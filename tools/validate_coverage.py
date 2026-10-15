#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""validate_coverage.py - Valida el arbol de preguntas contra el WPTA canonico.

Comprueba:
  1. Estructura: cada questions.yaml tiene los campos requeridos y las preguntas
     cumplen el patron de id/tipo/answer_type y reglas de navegacion.
  2. Trazabilidad: cada nodo tecnica/familia/area existe en el WPTA (o en el indice).
  3. Cobertura: toda tecnica del WPTA tiene su questions.yaml (sin huecos).
  4. Sin huerfanos ni ids duplicados; nav 'next' resuelve a una pregunta o token terminal.
  5. Separacion conocimiento/ejecucion: ningun nodo guarda respuestas/observaciones.

Uso:
  python tools/validate_coverage.py                 # usa third_party/wpta si existe
  python tools/validate_coverage.py --wpta DIR
  python tools/validate_coverage.py --json          # reporte machine-readable
Salida: exit 0 si OK; 1 si hay errores.
"""
import argparse
import glob
import json
import os
import re
import sys

try:
    import yaml
except Exception:
    print("[!] PyYAML requerido:  pip install pyyaml", file=sys.stderr)
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

REQ_NODE = ["schema_version", "node_type", "id", "questions"]
REQ_Q = ["id", "type", "question", "purpose", "required_evidence", "answer_type", "possible_outcomes", "next"]
ID_RE = re.compile(r"^Q-(AREA-[A-Z]|F-[A-Z][0-9]{2}|TEC-[0-9]{4})-[0-9]{2}$")
TYPES = {"context", "preconditions", "structure", "paths", "controls", "differentiation", "validation", "interpretation", "next"}
ANSWER_TYPES = {"structured", "boolean", "enum", "free_text", "evidence_ref"}
FORBIDDEN_KEYS = {"answer", "answers", "observed", "observation", "result", "status", "response", "finding"}


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def catalog_techniques(wpta):
    """Devuelve dict tec_id -> family_id, y dict family_id -> set(tec)."""
    tec_fam = {}
    fam_tec = {}
    if wpta and os.path.isdir(wpta):
        for tf in glob.glob(os.path.join(wpta, "atlas", "**", "tecnica.json"), recursive=True):
            data = load_json(tf)
            if not isinstance(data, dict) or "id" not in data:
                continue
            rel = os.path.relpath(tf, wpta).replace("\\", "/")
            parts = rel.split("/")
            fam = parts[2].split("_", 1)[0] if len(parts) > 2 else ""
            tec_fam[data["id"]] = fam
            fam_tec.setdefault(fam, set()).add(data["id"])
    else:
        tmap = load_json(os.path.join(ROOT, "indexes", "technique-map.json"), {}) or {}
        for tid, meta in tmap.items():
            tec_fam[tid] = meta.get("family_id", "")
            fam_tec.setdefault(meta.get("family_id", ""), set()).add(tid)
    return tec_fam, fam_tec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wpta", default=os.path.join(ROOT, "third_party", "wpta"))
    ap.add_argument("--areas", default=os.path.join(ROOT, "areas"))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    manifest = load_json(os.path.join(ROOT, "manifest.json"), {}) or {}
    terminals = set(manifest.get("terminals", []))

    errors = []
    warnings = []
    seen_ids = {}
    covered_techs = set()
    covered_fams = set()
    covered_areas = set()
    node_count = {"area": 0, "family": 0, "technique": 0}
    q_count = 0

    files = sorted(glob.glob(os.path.join(args.areas, "**", "questions.yaml"), recursive=True))
    if not files:
        print("[!] No hay questions.yaml en", args.areas, file=sys.stderr)
        sys.exit(2)

    for path in files:
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        try:
            node = load_yaml(path)
        except Exception as e:
            errors.append(f"{rel}: YAML invalido: {e}")
            continue
        if not isinstance(node, dict):
            errors.append(f"{rel}: no es un objeto")
            continue
        for k in REQ_NODE:
            if k not in node:
                errors.append(f"{rel}: falta campo requerido '{k}'")
        ntype = node.get("node_type")
        if ntype not in node_count:
            errors.append(f"{rel}: node_type invalido '{ntype}'")
            continue
        node_count[ntype] += 1

        if ntype == "technique":
            tid = node.get("technique_id")
            covered_techs.add(tid)
            if tid != node.get("id"):
                errors.append(f"{rel}: id ({node.get('id')}) != technique_id ({tid})")
        elif ntype == "family":
            covered_fams.add(node.get("family_id"))
        elif ntype == "area":
            covered_areas.add(node.get("id"))

        for bad in FORBIDDEN_KEYS:
            if bad in node:
                errors.append(f"{rel}: contiene '{bad}' (el repo solo guarda preguntas, no respuestas)")

        qs = node.get("questions")
        if not isinstance(qs, list) or not qs:
            errors.append(f"{rel}: 'questions' vacio o invalido")
            continue
        for item in qs:
            q_count += 1
            if not isinstance(item, dict):
                errors.append(f"{rel}: pregunta no-objeto")
                continue
            for k in REQ_Q:
                if k not in item:
                    errors.append(f"{rel}: pregunta {item.get('id','?')} falta '{k}'")
            qid = item.get("id", "")
            if not ID_RE.match(qid):
                errors.append(f"{rel}: id de pregunta invalido '{qid}'")
            if qid in seen_ids:
                errors.append(f"{rel}: id duplicado '{qid}' (ya en {seen_ids[qid]})")
            else:
                seen_ids[qid] = rel
            if item.get("type") not in TYPES:
                errors.append(f"{rel}: tipo invalido '{item.get('type')}' en {qid}")
            if item.get("answer_type") not in ANSWER_TYPES:
                errors.append(f"{rel}: answer_type invalido en {qid}")
            if not isinstance(item.get("required_evidence"), list):
                errors.append(f"{rel}: required_evidence no-lista en {qid}")

    global_ids = set(seen_ids)
    for path in files:
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        node = load_yaml(path)
        if not isinstance(node, dict):
            continue
        for item in node.get("questions", []) or []:
            if not isinstance(item, dict):
                continue
            qid = item.get("id", "?")
            for outcome, target in (item.get("next") or {}).items():
                if target is None:
                    continue
                if target in terminals:
                    continue
                if not isinstance(target, str) or not ID_RE.match(target):
                    errors.append(f"{rel}: {qid} next['{outcome}']='{target}' no es token terminal ni id de pregunta")
                elif target not in global_ids:
                    errors.append(f"{rel}: {qid} next['{outcome}'] apunta a '{target}' inexistente")

    tec_fam, fam_tec = catalog_techniques(args.wpta)
    if tec_fam:
        missing = sorted(set(tec_fam) - covered_techs)
        orphan = sorted(covered_techs - set(tec_fam))
        if missing:
            errors.append(f"cobertura: {len(missing)} tecnicas del WPTA sin questions.yaml: {missing[:10]}...")
        if orphan:
            errors.append(f"huerfanos: {len(orphan)} tecnicas sin correspondencia en el WPTA: {orphan[:10]}")
        missing_fam = sorted(set(fam_tec) - {f for f in covered_fams if f})
        if missing_fam:
            warnings.append(f"familias del WPTA sin questions.yaml: {missing_fam}")
    else:
        warnings.append("WPTA no disponible: cobertura verificada solo contra indexes/technique-map.json")

    report = {
        "ok": not errors,
        "nodes": node_count,
        "questions": q_count,
        "covered_techniques": len(covered_techs),
        "catalog_techniques": len(tec_fam),
        "coverage_pct": round(100.0 * len(covered_techs) / len(tec_fam), 2) if tec_fam else None,
        "errors": errors,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"nodos: area={node_count['area']} familia={node_count['family']} tecnica={node_count['technique']}")
        print(f"preguntas: {q_count}")
        print(f"cobertura: {len(covered_techs)}/{len(tec_fam)} tecnicas ({report['coverage_pct']}%)")
        for w in warnings:
            print("  [warn]", w)
        for e in errors:
            print("  [ERROR]", e)
        print("RESULTADO:", "OK" if not errors else f"{len(errors)} ERRORES")

    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
