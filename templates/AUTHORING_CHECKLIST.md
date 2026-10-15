# Checklist de aceptación — authoring de una técnica

Copia esta lista por técnica (o por lote) y complétala antes de marcar `reviewed: true`.
Norma completa: [`../AUTHORING.md`](../AUTHORING.md).

## Paso 1 — Mecanismo
- [ ] `mechanism.invariant` es una **propiedad de seguridad**, no un síntoma.
- [ ] `mechanism.preconditions` enumeradas (y cada una cubierta por una pregunta).
- [ ] `mechanism.controls` con `applies_to` y `bypass_candidates`.
- [ ] `sources`, `transformations`, `components` presentes cuando apliquen.

## Paso 2 — Preguntas derivadas
- [ ] Ninguna pregunta es «¿es vulnerable?» (ver anti-patrones §8).
- [ ] Cada pregunta nombra componente/operación/condición concreta.
- [ ] Cada pregunta declara `required_evidence`.

## Paso 3 — Caminos alternativos
- [ ] `alternative_paths` cubre las dimensiones relevantes (ruta, método, estado, rol, entrada, capa, versión, concurrencia).
- [ ] Cada dimensión declara `question_id` existente.

## Paso 4 — Ramas
- [ ] Todo outcome no-terminal apunta a una pregunta.
- [ ] Todo `unknown`/`partial` → `request_missing_evidence` nombrando la evidencia faltante.
- [ ] Toda rama termina en token terminal.

## Paso 5 — Hipótesis
- [ ] `hypothesis` es un **mecanismo causal** falsable.

## Paso 6 — Prueba discriminante
- [ ] `discriminating_test.baseline` = flujo legítimo de referencia.
- [ ] `change` = **una sola** variable.
- [ ] `constant` enumeradas.
- [ ] `expected_secure` y `anomalous` distinguibles.
- [ ] `signal`, `confirmation_criteria` y `falsation` definidos.

## Paso 7 — Cobertura
- [ ] Toda precondición cubierta (matriz precondición × camino sin huecos).
- [ ] Sin preguntas redundantes.

## Cierre
- [ ] `wpta.source` / `wpta.commit` correctos.
- [ ] `missing_catalog_fields` declarados.
- [ ] `authored: true`, `reviewed: true`, `standard_version: "1.0"`.
- [ ] `python tools/validate_coverage.py` en verde.
- [ ] `python tools/lint_authoring.py` en verde para esta técnica.
