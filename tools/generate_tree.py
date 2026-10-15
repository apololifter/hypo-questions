#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_tree.py - Genera el arbol de PREGUNTAS a partir del catalogo WPTA canonico.

Lee un checkout local del WPTA (por defecto third_party/wpta) y produce, por cada
nodo del arbol (area > familia > tecnica), un questions.yaml con preguntas derivadas
de los campos REALES de la ficha tecnica.json. No inventa: si un campo falta, lo
registra en missing_catalog_fields.

Salidas:
  areas/<area_dir>/questions.yaml
  areas/<area_dir>/<F-xxx_dir>/questions.yaml
  areas/<area_dir>/<F-xxx_dir>/<TEC-xxxx_dir>/questions.yaml
  indexes/questions.json
  indexes/technique-map.json
  indexes/areas.json
  indexes/families.json
  manifest.json
"""
import argparse
import glob
import json
import os
import subprocess
import sys

try:
    import yaml
except Exception:
    print("[!] PyYAML requerido:  pip install pyyaml", file=sys.stderr)
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WPTA_REPO = "https://github.com/apololifter/Web-Pentesting-Technique-Atlas-WPTA-"
SCHEMA_VERSION = "1.0"

TERMINALS = [
    "stop_not_applicable",
    "stop_not_relevant",
    "stop_precondition_unmet",
    "stop_false_positive",
    "request_missing_evidence",
    "request_scope_decision",
    "goto_technique_questions",
    "report",
    "done",
]


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def dump_yaml(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        yaml.safe_dump(obj, f, allow_unicode=True, sort_keys=False, default_flow_style=False, width=100)


def dump_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def clean(s):
    if not isinstance(s, str):
        return ""
    return " ".join(s.split()).strip()


def wpta_commit(wpta_dir):
    try:
        out = subprocess.check_output(
            ["git", "-C", wpta_dir, "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL, text=True,
        )
        return out.strip()
    except Exception:
        return "unknown"


def q(qid, qtype, question, purpose, req, answer_type, outcomes, nxt,
      depends_on=None, applicability=None, attacker_state=None, source_fields=None, notes=None):
    item = {
        "id": qid,
        "type": qtype,
        "question": clean(question),
        "purpose": clean(purpose),
        "required_evidence": req,
        "answer_type": answer_type,
        "possible_outcomes": outcomes,
        "next": nxt,
    }
    if depends_on:
        item["depends_on"] = depends_on
    if applicability:
        item["applicability_conditions"] = applicability
    if attacker_state:
        item["attacker_state_requirements"] = attacker_state
    if source_fields:
        item["source_fields"] = source_fields
    if notes:
        item["notes"] = clean(notes)
    return item


def area_questionset(code, title, subfamilies, families, commit):
    qs = []
    a1 = f"Q-AREA-{code}-01"
    a2 = f"Q-AREA-{code}-02"
    a3 = f"Q-AREA-{code}-03"
    subs = "; ".join(subfamilies) if subfamilies else "(el WPTA no declara subfamilias)"
    qs.append(q(
        a1, "context",
        f"¿Esta aplicacion expone o utiliza la dimension '{title}'? Subfamilias consideradas por el WPTA: {subs}.",
        "Determinar si el area debe explorarse para esta aplicacion antes de abrir sus familias.",
        ["app_surface", "tech_stack", "observed_flows"],
        "structured", ["relevant", "not_relevant", "unknown"],
        {"relevant": a2, "not_relevant": "stop_not_relevant", "unknown": "request_missing_evidence"},
        source_fields=["_meta/taxonomy.json:categories"],
    ))
    fams = ", ".join(f"{f['id']} ({f['name']})" for f in families) if families else "(sin familias)"
    qs.append(q(
        a2, "structure",
        f"¿Cuales de las familias del area {code} aplican al contexto observado y por que? Familias: {fams}.",
        "Priorizar familias aplicables en lugar de recorrer el area completa a ciegas.",
        ["module_or_function", "mechanism", "observed_signal"],
        "structured", ["some_apply", "none_apply", "unknown"],
        {"some_apply": a3, "none_apply": "stop_not_relevant", "unknown": "request_missing_evidence"},
        depends_on=[a1], source_fields=["_meta/checklist/families.json"],
    ))
    qs.append(q(
        a3, "next",
        "¿Qué familias quedaron sin evaluar (not_reviewed) y qué evidencia puntual las desbloquearia?",
        "Cerrar huecos de cobertura del area sin afirmar cobertura completa.",
        ["coverage_state", "missing_evidence"],
        "structured", ["covered", "gaps_remain"],
        {"covered": "done", "gaps_remain": "request_missing_evidence"},
        depends_on=[a2], source_fields=["coverage.json"],
    ))
    return {
        "schema_version": SCHEMA_VERSION,
        "node_type": "area",
        "id": code,
        "title": title,
        "description": f"Preguntas de encuadre para el area {code} ({title}).",
        "area": code,
        "area_title": title,
        "subfamilies": subfamilies,
        "attacker_state_requirements": [],
        "techniques": [t for f in families for t in f.get("techniques", [])],
        "wpta": {"repo": WPTA_REPO, "commit": commit, "source": f"atlas/{code}"},
        "generated": True,
        "questions": qs,
    }


def family_questionset(area_code, fam, techniques, commit):
    fid = fam["id"]
    name = fam.get("name", "")
    desc = fam.get("description", "")
    f1 = f"Q-{fid}-01"
    f2 = f"Q-{fid}-02"
    f3 = f"Q-{fid}-03"
    tlist = ", ".join(f"{t['id']} ({t['name']})" for t in techniques) if techniques else "(sin tecnicas)"
    qs = []
    qs.append(q(
        f1, "context",
        f"¿Qué funcionalidad, mecanismo o condicion de la aplicacion hace pertinente la familia '{name}'? {desc}",
        "Decidir si la familia aplica al sistema observado.",
        ["functionality", "mechanism", "precondition"],
        "structured", ["applicable", "not_applicable", "unknown"],
        {"applicable": f2, "not_applicable": "stop_not_applicable", "unknown": "request_missing_evidence"},
        source_fields=["_meta/checklist/families.json:description"],
    ))
    qs.append(q(
        f2, "structure",
        f"¿Cuales de las tecnicas de la familia aplican al contexto observado? Tecnicas: {tlist}.",
        "Abrir solo las tecnicas pertinentes; conservar trazabilidad de las descartadas.",
        ["endpoint_or_module", "observed_signal", "preconditions"],
        "structured", ["identified", "none", "unknown"],
        {"identified": "goto_technique_questions", "none": "stop_not_applicable", "unknown": "request_missing_evidence"},
        depends_on=[f1], source_fields=["_meta/checklist/families.json:techniques"],
    ))
    qs.append(q(
        f3, "differentiation",
        "¿Qué evidencia permitiria descartar la familia completa sin dejar huecos (precondicion ausente comprobada)?",
        "Evitar descartes por 'no vi senal': exigir evidencia positiva de no aplicabilidad.",
        ["positive_absence_evidence"],
        "structured", ["discardable", "keep"],
        {"discardable": "stop_not_applicable", "keep": "goto_technique_questions"},
        depends_on=[f1], source_fields=["objective.not_applicable"],
    ))
    return {
        "schema_version": SCHEMA_VERSION,
        "node_type": "family",
        "id": fid,
        "title": name,
        "description": desc,
        "area": area_code,
        "area_title": fam.get("area_title", ""),
        "family_id": fid,
        "family_name": name,
        "technique_id": None,
        "variant_of": None,
        "hypothesis": None,
        "behavior": None,
        "patterns": [],
        "attacker_state_requirements": [],
        "techniques": [t["id"] for t in techniques],
        "wpta": {"repo": WPTA_REPO, "commit": commit, "source": f"familia {fid}"},
        "generated": True,
        "questions": qs,
    }


def technique_questionset(tec, area_code, area_title, fam, commit, src_rel):
    tid = tec["id"]
    name = clean(tec.get("name", ""))
    o = tec.get("objective", {}) or {}
    pr = tec.get("procedure", {}) or {}
    rp = tec.get("replication", {}) or {}
    rel = tec.get("relations", {}) or {}
    ex = tec.get("example", {}) or {}

    def field(d, k):
        return clean(d.get(k, ""))

    behavior = field(o, "behavior")
    hypothesis = field(o, "hypothesis")
    contexts = field(o, "contexts")
    not_app = field(o, "not_applicable")
    action = field(pr, "action")
    var_change = field(pr, "variable_to_change")
    var_const = field(pr, "variables_to_hold_constant")
    secure = field(pr, "expected_secure_result")
    anomalous = field(pr, "anomalous_result")
    confirm = field(pr, "confirmation_criteria")
    reqs = field(rp, "requirements")
    signal = field(rp, "signal")
    patterns = rel.get("detects_pattern", []) or []
    related = sorted(set((rel.get("related_to", []) or []) + (rel.get("tests_same_invariant_as", []) or [])))

    watch = ["objective.behavior", "objective.hypothesis", "objective.contexts", "objective.not_applicable",
             "procedure.action", "procedure.variable_to_change", "procedure.variables_to_hold_constant",
             "procedure.expected_secure_result", "procedure.anomalous_result", "procedure.confirmation_criteria",
             "replication.requirements", "replication.signal", "example.normal", "example.modified"]
    values = {
        "objective.behavior": behavior, "objective.hypothesis": hypothesis, "objective.contexts": contexts,
        "objective.not_applicable": not_app, "procedure.action": action, "procedure.variable_to_change": var_change,
        "procedure.variables_to_hold_constant": var_const, "procedure.expected_secure_result": secure,
        "procedure.anomalous_result": anomalous, "procedure.confirmation_criteria": confirm,
        "replication.requirements": reqs, "replication.signal": signal,
        "example.normal": clean(ex.get("normal", "")), "example.modified": clean(ex.get("modified", "")),
    }
    missing = [k for k, v in values.items() if not v]

    def fb(text, field_name):
        return text if values.get(field_name) else f"[SIN DATO EN WPTA: {field_name}] " + text

    q1 = f"Q-{tid}-01"
    q2 = f"Q-{tid}-02"
    q3 = f"Q-{tid}-03"
    q4 = f"Q-{tid}-04"
    q5 = f"Q-{tid}-05"
    q6 = f"Q-{tid}-06"
    q7 = f"Q-{tid}-07"
    q8 = f"Q-{tid}-08"

    qs = []
    qs.append(q(
        q1, "context",
        fb(f"¿Esta aplicacion presenta el contexto que activa la tecnica '{name}'? Contexto canonico WPTA: {contexts}", "objective.contexts"),
        "Decidir si la tecnica es aplicable ANTES de disenar cualquier prueba. Sin contexto no hay hipotesis.",
        ["endpoint_or_route", "resource_model", "operation"],
        "structured", ["applicable", "not_applicable", "unknown"],
        {"applicable": q2, "not_applicable": "stop_not_applicable", "unknown": "request_missing_evidence"},
        applicability=[contexts] if contexts else [],
        source_fields=["objective.contexts", "objective.behavior"],
    ))
    cond = not_app if not_app else "(el WPTA no declara condicion de no aplicabilidad)"
    qs.append(q(
        q2, "preconditions",
        fb(f"¿Se cumplen las precondiciones de replicacion y NO se cumple la condicion de no aplicabilidad? Requisitos WPTA: {reqs.rstrip('.')}. No aplica si: {cond}", "replication.requirements"),
        "Verificar cuentas/roles/entorno antes de probar; comprobar la condicion que descartaria la tecnica.",
        ["accounts_or_roles", "environment", "concurrency_if_any"],
        "structured", ["satisfied", "not_satisfied", "unknown"],
        {"satisfied": q3, "not_satisfied": "stop_precondition_unmet", "unknown": "request_missing_evidence"},
        depends_on=[q1],
        attacker_state=[reqs] if reqs else [],
        source_fields=["replication.requirements", "objective.not_applicable"],
    ))
    qs.append(q(
        q3, "structure",
        fb(f"¿Qué rutas, funciones, estados o componentes intervienen en el comportamiento observado? Hipotesis a falsar: {hypothesis}", "objective.hypothesis"),
        "Reconstruir el flujo real (fuente -> transformacion -> efecto) que la tecnica pondria a prueba.",
        ["call_graph", "state_or_flow", "component_inventory"],
        "structured", ["identified", "partial", "unknown"],
        {"identified": q4, "partial": "request_missing_evidence", "unknown": "request_missing_evidence"},
        depends_on=[q2], source_fields=["objective.hypothesis", "procedure.steps"],
    ))
    qs.append(q(
        q4, "controls",
        fb(f"¿Dónde se valida la condicion de seguridad y en qué caminos/capas se aplica? Comportamiento a revisar: {behavior}", "objective.behavior"),
        "Localizar la guarda que DEBERIA impedir el fallo y comprobar si cubre todos los caminos.",
        ["middleware_or_policy", "alternative_routes", "effective_guard"],
        "structured", ["located", "not_located", "unknown"],
        {"located": q5, "not_located": q5, "unknown": "request_missing_evidence"},
        depends_on=[q3], source_fields=["objective.behavior"],
    ))
    qs.append(q(
        q5, "differentiation",
        fb(f"¿Qué observacion distingue una implementacion segura de una insegura? Seguro: {secure} Anomalo: {anomalous} Senal: {signal}", "procedure.expected_secure_result"),
        "Definir el discriminante observable ANTES de ejecutar; sin el, la prueba no es falsable.",
        ["expected_response", "anomalous_response", "signal_with_reference"],
        "structured", ["discriminates", "ambiguous", "unknown"],
        {"discriminates": q6, "ambiguous": q7, "unknown": "request_missing_evidence"},
        depends_on=[q4], source_fields=["procedure.expected_secure_result", "procedure.anomalous_result", "replication.signal"],
    ))
    qs.append(q(
        q6, "validation",
        fb(f"¿Qué prueba minima confirmaria o refutaria la hipotesis? Accion: {action} Cambia SOLO: {var_change} Constante: {var_const} Criterio: {confirm}", "procedure.confirmation_criteria"),
        "Producir evidencia reproducible con minima modificacion (una variable). Genera el instrumento minimo.",
        ["reproducible_request", "baseline", "differential_response"],
        "evidence_ref", ["confirmed", "refuted", "inconclusive", "blocked"],
        {"confirmed": q8, "refuted": q8, "inconclusive": q7, "blocked": "request_missing_evidence"},
        depends_on=[q5], source_fields=["procedure.action", "procedure.confirmation_criteria"],
        notes="La ejecucion requiere aprobacion del CEO por ser accion intrusiva.",
    ))
    qs.append(q(
        q7, "interpretation",
        "¿Qué otras explicaciones (cache, rol, tenant, entorno, dato preexistente) podrian producir el mismo resultado y como se descartan?",
        "Separar violacion real de falso positivo antes de concluir.",
        ["alternative_hypotheses", "control_comparison"],
        "structured", ["explained", "unresolved", "unknown"],
        {"explained": "stop_false_positive", "unresolved": q6, "unknown": "request_missing_evidence"},
        depends_on=[q5], source_fields=["relations.detects_pattern"],
    ))
    pats = ", ".join(patterns) if patterns else "(el WPTA no declara patrones)"
    rels = ", ".join(related) if related else "(sin tecnicas relacionadas)"
    qs.append(q(
        q8, "next",
        f"¿Qué pregunta o patron corresponde tras la evidencia? Patrones detectados: {pats}. Tecnicas relacionadas: {rels}.",
        "Decidir el siguiente paso (reportar, cerrar, o abrir una tecnica relacionada) preservando trazabilidad.",
        ["confirmed_or_refuted_evidence", "finding_ref"],
        "structured", ["confirmed_finding", "refuted_close", "follow_related"],
        {"confirmed_finding": "report", "refuted_close": "done", "follow_related": "goto_technique_questions"},
        depends_on=[q6], source_fields=["relations.detects_pattern", "relations.related_to"],
    ))

    return {
        "schema_version": SCHEMA_VERSION,
        "node_type": "technique",
        "id": tid,
        "title": name,
        "description": hypothesis if hypothesis else f"Tecnica {tid}: {name}",
        "area": area_code,
        "area_title": area_title,
        "family_id": fam.get("id", ""),
        "family_name": fam.get("name", ""),
        "technique_id": tid,
        "variant_of": tec.get("variant_of", None),
        "hypothesis": hypothesis or None,
        "behavior": behavior or None,
        "patterns": patterns,
        "related_techniques": related,
        "attacker_state_requirements": [reqs] if reqs else [],
        "missing_catalog_fields": missing,
        "wpta": {"repo": WPTA_REPO, "commit": commit, "source": src_rel},
        "generated": True,
        "questions": qs,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wpta", default=os.path.join(ROOT, "third_party", "wpta"))
    ap.add_argument("--out", default=os.path.join(ROOT, "areas"))
    ap.add_argument("--indexes", default=os.path.join(ROOT, "indexes"))
    args = ap.parse_args()

    wpta = os.path.abspath(args.wpta)
    if not os.path.isdir(wpta):
        print(f"[!] WPTA no encontrado en {wpta}. Clona el repo canonico.", file=sys.stderr)
        sys.exit(2)

    taxonomy = load_json(os.path.join(wpta, "_meta", "taxonomy.json"), {}) or {}
    titles = {c["code"]: c.get("title", "") for c in taxonomy.get("categories", [])}
    subs = {c["code"]: c.get("subfamilies", []) for c in taxonomy.get("categories", [])}
    families_json = load_json(os.path.join(wpta, "_meta", "checklist", "families.json"), []) or []
    fam_by_id = {f["id"]: f for f in families_json}
    commit = wpta_commit(wpta)

    tec_files = sorted(glob.glob(os.path.join(wpta, "atlas", "**", "tecnica.json"), recursive=True))
    if not tec_files:
        print("[!] No hay fichas tecnica.json en el WPTA.", file=sys.stderr)
        sys.exit(2)

    techniques = []
    for tf in tec_files:
        data = load_json(tf)
        if not isinstance(data, dict) or "id" not in data:
            continue
        rel = os.path.relpath(tf, wpta).replace("\\", "/")
        parts = rel.split("/")
        area_dir = parts[1]
        family_dir = parts[2]
        area_code = area_dir.split("_", 1)[0]
        family_id = family_dir.split("_", 1)[0]
        techniques.append({
            "json": data, "rel": rel, "area_dir": area_dir, "family_dir": family_dir,
            "area_code": area_code, "family_id": family_id,
        })

    fam_by_id_area = {}
    for f in families_json:
        fam_by_id_area[f["id"]] = f

    all_questions = []
    area_index = []
    family_index = []
    tech_index = {}

    area_dirs = {}
    for t in techniques:
        area_dirs.setdefault(t["area_code"], t["area_dir"])

    for area_code in sorted(area_dirs):
        area_dir = area_dirs[area_code]
        fams_here = [t for t in techniques if t["area_code"] == area_code]
        fam_ids = sorted({t["family_id"] for t in fams_here})
        fam_objs = []
        for fid in fam_ids:
            base = dict(fam_by_id.get(fid, {"id": fid, "name": "", "description": "", "techniques": []}))
            base["area_title"] = titles.get(area_code, "")
            fam_objs.append(base)

        aset = area_questionset(area_code, titles.get(area_code, ""), subs.get(area_code, []), fam_objs, commit)
        out_area = os.path.join(args.out, area_dir)
        dump_yaml(os.path.join(out_area, "questions.yaml"), aset)
        area_index.append({
            "area": area_code, "title": titles.get(area_code, ""), "dir": f"areas/{area_dir}",
            "questions_file": f"areas/{area_dir}/questions.yaml",
            "families": fam_ids, "techniques": [t["json"]["id"] for t in fams_here],
            "question_count": len(aset["questions"]),
        })
        for item in aset["questions"]:
            all_questions.append({**item, "node_type": "area", "node_id": area_code,
                                   "area": area_code, "file": f"areas/{area_dir}/questions.yaml"})

        for fid in fam_ids:
            fam = fam_by_id.get(fid, {"id": fid, "name": "", "description": "", "techniques": []})
            fam = dict(fam)
            fam["area_title"] = titles.get(area_code, "")
            fam_dir_name = next(t["family_dir"] for t in fams_here if t["family_id"] == fid)
            tecs_here = [t for t in fams_here if t["family_id"] == fid]
            tecs_sorted = sorted(tecs_here, key=lambda x: x["json"]["id"])
            fset = family_questionset(area_code, fam, [x["json"] for x in tecs_sorted], commit)
            out_fam = os.path.join(out_area, fam_dir_name)
            dump_yaml(os.path.join(out_fam, "questions.yaml"), fset)
            family_index.append({
                "family_id": fid, "name": fam.get("name", ""), "area": area_code,
                "questions_file": f"areas/{area_dir}/{fam_dir_name}/questions.yaml",
                "techniques": [x["json"]["id"] for x in tecs_sorted],
                "question_count": len(fset["questions"]),
            })
            for item in fset["questions"]:
                all_questions.append({**item, "node_type": "family", "node_id": fid,
                                       "area": area_code, "family_id": fid,
                                       "file": f"areas/{area_dir}/{fam_dir_name}/questions.yaml"})

            for t in tecs_sorted:
                tec = t["json"]
                tset = technique_questionset(tec, area_code, titles.get(area_code, ""), fam, commit, t["rel"])
                tec_dir_name = os.path.basename(os.path.dirname(t["rel"]))
                out_tec = os.path.join(out_fam, tec_dir_name)
                dump_yaml(os.path.join(out_tec, "questions.yaml"), tset)
                qfile = f"areas/{area_dir}/{fam_dir_name}/{tec_dir_name}/questions.yaml"
                tech_index[tec["id"]] = {
                    "technique_id": tec["id"], "name": clean(tec.get("name", "")),
                    "area": area_code, "family_id": fid, "variant_of": tec.get("variant_of", None),
                    "patterns": (tec.get("relations", {}) or {}).get("detects_pattern", []),
                    "questions_file": qfile, "question_count": len(tset["questions"]),
                    "missing_catalog_fields": tset["missing_catalog_fields"],
                    "wpta_source": t["rel"],
                }
                for item in tset["questions"]:
                    all_questions.append({**item, "node_type": "technique", "node_id": tec["id"],
                                           "area": area_code, "family_id": fid, "technique_id": tec["id"],
                                           "file": qfile})

    dump_json(os.path.join(args.indexes, "questions.json"), all_questions)
    dump_json(os.path.join(args.indexes, "technique-map.json"), tech_index)
    dump_json(os.path.join(args.indexes, "areas.json"), area_index)
    dump_json(os.path.join(args.indexes, "families.json"), family_index)

    variants = sum(1 for t in techniques if t["json"].get("variant_of"))
    manifest = {
        "name": "hypo-questions",
        "version": "0.1.0",
        "schema_version": SCHEMA_VERSION,
        "description": "Biblioteca de preguntas de investigacion ancladas al WPTA, consumible por agentes de pentesting.",
        "wpta": {
            "repo": WPTA_REPO, "commit": commit,
            "techniques": len(techniques), "variants": variants,
            "families": len(families_json), "areas": len(area_dirs),
        },
        "counts": {
            "areas": len(area_index), "families": len(family_index),
            "techniques": len(tech_index), "questions": len(all_questions),
        },
        "layout": {
            "areas": "areas/<area_dir>/[<family_dir>/[<tec_dir>/]]questions.yaml",
            "indexes": "indexes/{questions,technique-map,areas,families}.json",
            "schema": "schema/{question,questionset}.schema.json",
        },
        "terminals": TERMINALS,
    }
    dump_json(os.path.join(ROOT, "manifest.json"), manifest)

    print(f"[ok] areas={len(area_index)} families={len(family_index)} techniques={len(tech_index)} "
          f"questions={len(all_questions)} (wpta commit {commit[:10]})")


if __name__ == "__main__":
    main()
