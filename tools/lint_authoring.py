#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lint_authoring.py - Aplica el estandar de autoria (AUTHORING.md) a cada questionset.

Distingue:
  - SEED      : generado automaticamente (authored != true). No se le exige el estandar completo.
  - AUTHORED  : authored: true. Debe cumplir los GATES T1-T7 y no incurrir en anti-patrones.

GATES (authored):
  T1 mechanism.invariant + >=1 control
  T2 discriminating_test completo (baseline, change, constant, expected_secure, anomalous)
  T3 hay pregunta de precondiciones + cada precondition tiene overlap lexico con alguna pregunta
  T4 cada alternative_paths[].question_id existe
  T5 existe una pregunta de tipo 'validation'
  T6 (delegado en validate_coverage.py: ramas resueltas)
  T7 sin preguntas redundantes (texto normalizado duplicado)
Anti-patrones: pregunta generica ("es vulnerable"), required_evidence vacio, <2 outcomes.
Separo conocimiento/ejecucion: prohibido guardar respuestas/observaciones.

Salida: exit 0 si ningun AUTHORED falla; 1 si hay fallos.
"""
import argparse
import glob
import json
import os
import re
import sys
import unicodedata

try:
    import yaml
except Exception:
    print("[!] PyYAML requerido:  pip install pyyaml", file=sys.stderr)
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

REQ_MECH = ["invariant", "preconditions", "controls"]
REQ_TEST = ["baseline", "change", "constant", "expected_secure", "anomalous"]
GENERIC_RE = re.compile(r"(es vulnerable|sea vulnerable|es vulnerable a|alguna vulnerabilidad|hay alguna vuln)", re.I)
FORBIDDEN_KEYS = {"answer", "answers", "observed", "observation", "result", "status", "response", "finding"}
STOP = {"para", "puede", "debe", "donde", "como", "cual", "cuales", "este", "esta", "tiene", "existe", "todos", "solo"}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


def tokens(s):
    return {t for t in re.split(r"[^a-z0-9]+", norm(s)) if len(t) >= 5 and t not in STOP}


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def lint_authored(node, rel):
    errs, warns = [], []
    if not node.get("standard_version"):
        errs.append("T0: falta standard_version")
    if node.get("node_type") != "technique":
        return errs, warns

    mech = node.get("mechanism") or {}
    for k in REQ_MECH:
        if not mech.get(k):
            errs.append(f"T1: mechanism.{k} ausente o vacio")
    for i, c in enumerate(mech.get("controls") or []):
        if not isinstance(c, dict) or not c.get("check"):
            errs.append(f"T1: mechanism.controls[{i}] sin 'check'")

    dt = node.get("discriminating_test") or {}
    for k in REQ_TEST:
        v = dt.get(k)
        if not v or (isinstance(v, list) and not v):
            errs.append(f"T2: discriminating_test.{k} ausente")

    qs = node.get("questions") or []
    types = [q.get("type") for q in qs if isinstance(q, dict)]
    if "preconditions" not in types:
        errs.append("T3: falta una pregunta tipo 'preconditions'")
    if "validation" not in types:
        errs.append("T5: falta una pregunta tipo 'validation'")

    qtext = " ".join((q.get("question", "") + " " + q.get("purpose", "")) for q in qs if isinstance(q, dict))
    qtok = tokens(qtext)
    for i, pre in enumerate(mech.get("preconditions") or []):
        pt = tokens(pre)
        if pt and not (pt & qtok):
            warns.append(f"T3: precondition[{i}] sin overlap lexico con ninguna pregunta (revisar cobertura)")

    ids = {q.get("id") for q in qs if isinstance(q, dict)}
    apaths = node.get("alternative_paths") or []
    if len(apaths) < 2:
        errs.append("T4: alternative_paths debe declarar >= 2 dimensiones de variacion")
    for i, ap in enumerate(apaths):
        qid = (ap or {}).get("question_id")
        if qid not in ids:
            errs.append(f"T4: alternative_paths[{i}].question_id='{qid}' no existe en el questionset")

    seen = {}
    for q in qs:
        if not isinstance(q, dict):
            continue
        qid = q.get("id", "?")
        if GENERIC_RE.search(q.get("question", "")):
            errs.append(f"anti-patron: pregunta generica en {qid}")
        if not q.get("required_evidence"):
            errs.append(f"G1: {qid} sin required_evidence")
        if len(q.get("possible_outcomes") or []) < 2:
            errs.append(f"G2: {qid} con <2 possible_outcomes")
        key = norm(q.get("question", ""))
        if key and key in seen:
            errs.append(f"T7: pregunta redundante {qid} (duplica {seen[key]})")
        else:
            seen[key] = qid

    for bad in FORBIDDEN_KEYS:
        if bad in node:
            errs.append(f"separa-conocimiento: contiene '{bad}' (el repo solo guarda preguntas)")
    return errs, warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--areas", default=os.path.join(ROOT, "areas"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--list-seeds", action="store_true")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.areas, "**", "questions.yaml"), recursive=True))
    authored_count = 0
    seed_count = 0
    failures = {}
    warnings = {}
    seeds = []

    for path in files:
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        try:
            node = load_yaml(path)
        except Exception as e:
            failures[rel] = [f"YAML invalido: {e}"]
            continue
        if not isinstance(node, dict):
            continue
        is_authored = node.get("authored") is True or node.get("generated") is False
        if not is_authored:
            seed_count += 1
            if args.list_seeds:
                seeds.append(rel)
            continue
        authored_count += 1
        errs, warns = lint_authored(node, rel)
        if errs:
            failures[rel] = errs
        if warns:
            warnings[rel] = warns

    report = {
        "ok": not failures,
        "authored": authored_count,
        "seeds": seed_count,
        "failures": failures,
        "warnings": warnings,
    }
    if args.list_seeds:
        report["seed_files"] = seeds

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"authored: {authored_count}  seeds: {seed_count}")
        for rel, errs in failures.items():
            print(f"  [FAIL] {rel}")
            for e in errs:
                print(f"         - {e}")
        for rel, warns in warnings.items():
            for w in warns:
                print(f"  [warn] {rel}: {w}")
        print("RESULTADO:", "OK" if not failures else f"{len(failures)} AUTHORED con fallos")

    sys.exit(0 if not failures else 1)


if __name__ == "__main__":
    main()
