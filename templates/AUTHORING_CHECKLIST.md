# Checklist de aceptación — authoring de una técnica

Copia esta lista por técnica (o por lote) y complétala antes de marcar `reviewed: true`.
Norma completa: [`../AUTHORING.md`](../AUTHORING.md).

## Paso 1 — Cómo se materializa la técnica
- [ ] `mechanism.invariant` es una **propiedad de seguridad**, no un síntoma.
- [ ] `mechanism.preconditions` enumeradas (y cada una cubierta por una pregunta).
- [ ] `mechanism.controls` con `applies_to` y `bypass_candidates`.
- [ ] `sources`, `transformations`, `components` presentes cuando apliquen.
- [ ] Queda claro **qué tendría que averiguar el pentester** para descubrir el mecanismo.

## Paso 2 — Ruta de investigación
- [ ] La ruta va del objetivo funcional a los detalles (funcionalidades → endpoints/estados/roles → procesamiento y controles → comportamiento → evidencia).
- [ ] Cada elemento del mecanismo tiene al menos una pregunta correspondiente.

## Paso 3 — Formular preguntas útiles
- [ ] Ninguna pregunta es «¿es vulnerable?» (ver anti-patrones §8).
- [ ] Cada pregunta nombra componente/operación/condición concreta y hace descubrir algo desconocido.
- [ ] Cada pregunta declara `required_evidence`.
- [ ] No se asumen endpoints, parámetros, tecnologías ni controles no identificados.

## Paso 4 — Paso a paso adaptativo
- [ ] `alternative_paths` cubre las dimensiones relevantes (ruta, método, estado, rol, entrada, capa, versión, concurrencia) con `question_id` existente.
- [ ] Todo outcome no-terminal apunta a una pregunta.
- [ ] Todo `unknown`/`partial` → `request_missing_evidence` nombrando la evidencia faltante.
- [ ] Toda rama termina en token terminal.
- [ ] Los caminos que exigen razonamientos/pruebas distintos van en ramas separadas.

## Paso 5 — Hipótesis concreta
- [ ] `hypothesis` es un **mecanismo causal** falsable (operación + precondiciones + atacante + propiedad incumplida + resultado observable).

## Paso 6 — Verificación del posible fallo
- [ ] `discriminating_test.baseline` = comportamiento normal de referencia.
- [ ] `change` = **una sola** variable.
- [ ] `constant` enumeradas.
- [ ] `expected_secure` y `anomalous` distinguibles.
- [ ] `signal`, `confirmation_criteria` y `falsation` definidos.
- [ ] Queda claro que la **ejecución** de la prueba es responsabilidad separada (fuera del árbol).

## Paso 7 — El árbol guía hacia la vulnerabilidad
- [ ] Toda precondición cubierta (matriz precondición × camino sin huecos).
- [ ] Ninguna rama abandonada sin salida definida.
- [ ] Sin preguntas redundantes ni que repitan el nombre de la técnica.
- [ ] Existe un recorrido comprensible hasta una hipótesis verificable.

## Cierre
- [ ] `wpta.source` / `wpta.commit` correctos.
- [ ] `missing_catalog_fields` declarados.
- [ ] `authored: true`, `reviewed: true`, `standard_version: "1.0"`.
- [ ] `python tools/validate_coverage.py` en verde.
- [ ] `python tools/lint_authoring.py` en verde para esta técnica.
