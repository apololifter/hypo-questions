# hypo-questions

**Biblioteca de preguntas de investigación** anclada al [Web Pentesting Technique Atlas (WPTA)](https://github.com/apololifter/Web-Pentesting-Technique-Atlas-WPTA-).

Este repositorio **no contiene vulnerabilidades ni checklist**: contiene **preguntas** organizadas en el
mismo árbol que el WPTA (área → familia → técnica). Cada técnica tiene una secuencia de preguntas que lleva
de una observación a una **decisión técnica** o a un **experimento discriminante**, y que un agente
(por ejemplo `generador-instrumentos`) puede recorrer para saber **qué preguntar, qué evidencia falta y
qué prueba mínima la resuelve**.

> Es una **base de conocimiento interrogativa**, no un catálogo de ataques. Documentar una pregunta no
> autoriza a ejecutarla. Solo pruebas autorizadas / lab / bug bounty en scope.

---

## Prompt principal — cómo construir las preguntas

> Este es el **prompt principal** del repositorio: la metodología que gobierna a quien autora las
> preguntas, técnica por técnica. El desarrollo operativo (GATES T1-T7, taxonomía de preguntas, checklist)
> está en [`AUTHORING.md`](AUTHORING.md).

Tu tarea es construir una metodología para las preguntas de `hypo-questions` que permita a un agente
investigar una **aplicación web real**, técnica por técnica del WPTA, y llegar a **hipótesis de
vulnerabilidad con pruebas formuladas**. No otra lista de dimensiones genéricas.

Para **cada técnica del WPTA** debes:

1. **Descomponer el mecanismo.** Identificar qué condiciones, componentes, controles y comportamientos
   deben existir para que pueda producirse el fallo.
2. **Derivar las preguntas necesarias.** Determinar qué necesita averiguar el agente sobre la aplicación
   para saber si cada condición se cumple. Las preguntas deben ser específicas del mecanismo, no variantes
   de «¿es vulnerable?».
3. **Cubrir caminos alternativos.** Investigar las distintas rutas, estados, roles, entradas, validaciones
   y operaciones que pueden cambiar el resultado de seguridad.
4. **Construir ramas de investigación.** Cada respuesta debe determinar qué pregunta corresponde después,
   qué evidencia falta o si una línea de investigación puede descartarse justificadamente.
5. **Llegar a una hipótesis comprobable.** Las respuestas deben permitir establecer un mecanismo causal
   concreto, sus precondiciones y el comportamiento de seguridad que podría incumplirse.
6. **Derivar una prueba discriminante.** Definir la modificación mínima, el estado inicial, las variables
   constantes, los resultados esperados y los criterios para confirmar, refutar o dejar inconclusa la
   hipótesis.
7. **Validar la cobertura.** Comprobar que las preguntas contemplan las condiciones relevantes de la
   técnica —incluidas variantes de implementación— y que no son redundantes ni dejan ramas sin resolver.

**Ejemplo — elusión de workflows.** No basta con preguntar si se puede saltar un paso. Hay que identificar
las precondiciones de cada transición, dónde se aplican, qué caminos alcanzan la operación final, cuáles
evitan esas comprobaciones, y qué prueba permite distinguir una ruta legítima de una que viola las reglas
del proceso.

**El entregable es el estándar de autoría**: un documento que indica cómo analizar cada técnica del WPTA,
cómo derivar sus preguntas, cómo organizarlas en ramas y cómo verificar que permiten llegar a hipótesis y
pruebas. Ese estándar es el que debes usar para construir `hypo-questions` de forma sistemática.

---

## Por qué existe

Sin esto, un agente parte de cero cada vez e improvisa las preguntas. Aquí cada pregunta está **derivada de
los campos reales** de la ficha `tecnica.json` del WPTA (`objective.contexts`, `objective.hypothesis`,
`procedure.action`, `replication.signal`, `relations.detects_pattern`, …), de modo que las preguntas son
**específicas de esa técnica** y no genéricas.

## Principios

1. **Separación conocimiento / ejecución.** El repo guarda *preguntas, dependencias, condiciones de
   aplicabilidad y reglas de navegación*. Las **respuestas, observaciones y resultados viven en la memoria
   del engagement** (nunca aquí). El validador rechaza cualquier nodo que contenga campos de respuesta.
2. **Trazabilidad al WPTA.** Cada nodo enlaza al `TEC-xxxx` / `F-…` real y al **commit fijado** del WPTA del
   que se generó. Si el WPTA cambia, el validador lo detecta.
3. **No se inventa.** Si un campo del WPTA falta, la pregunta lo declara (`[SIN DATO EN WPTA: …]`) y se
   registra en `missing_catalog_fields`. Nada de suposiciones.
4. **Cada pregunta falsa algo.** Toda pregunta tiene `possible_outcomes` y reglas `next` que conducen a
   continuar, a pedir evidencia o a un token terminal (`stop_*`, `request_missing_evidence`, `report`, `done`).

## Estructura

```
hypo-questions/
├── README.md
├── AUTHORING.md                   # ESTANDAR de autoria (como se construyen las preguntas)
├── manifest.json                  # commit WPTA fijado + conteos + tokens terminales
├── schema/
│   ├── question.schema.json       # una pregunta
│   └── questionset.schema.json    # un questions.yaml (nodo area/familia/tecnica)
├── templates/
│   ├── technique.questions.template.yaml   # plantilla de una tecnica
│   └── AUTHORING_CHECKLIST.md              # checklist de aceptacion
├── tools/
│   ├── generate_tree.py           # WPTA -> arbol de preguntas (preserva lo autorado)
│   ├── validate_coverage.py       # trazabilidad + cobertura + reglas de navegacion
│   └── lint_authoring.py          # GATES de autoria (T1-T7) + anti-patrones
├── indexes/                       # GENERADO: lookup rapido por agente
│   ├── questions.json             # todas las preguntas (plano)
│   ├── technique-map.json         # TEC -> {area, familia, patrones, archivo, #preguntas}
│   ├── areas.json
│   └── families.json
├── areas/<area_dir>/
│   ├── questions.yaml             # preguntas de encuadre del area
│   └── <F-xxx_dir>/
│       ├── questions.yaml         # preguntas de la familia
│       └── <TEC-xxxx_dir>/
│           └── questions.yaml     # preguntas de la tecnica
└── .github/workflows/validate.yml
```

`<area_dir>` / `<family_dir>` / `<TEC-xxxx_dir>` replican **exactamente** los nombres de carpeta del
`atlas/` del WPTA (p. ej. `D_autorizacion-y/F-D01_control-de-acceso-a/TEC-0003_sustitucion-de-referencia-de/`).

## Autoría: seed vs. authored

Cada `questions.yaml` nace como **seed** (borrador generado del WPTA: `generated: true`, `authored: false`).
Un nodo se promueve a **authored** cuando se reescribe siguiendo [`AUTHORING.md`](AUTHORING.md):
`generated: false`, `authored: true`, con `mechanism`, `discriminating_test` y `alternative_paths`.
**La regeneración preserva los nodos autorados**; los seeds son el backlog visible.

El estándar exige 7 pasos por técnica: (1) descomponer el mecanismo, (2) derivar preguntas, (3) cubrir
caminos alternativos, (4) construir ramas, (5) llegar a hipótesis comprobable, (6) derivar la prueba
discriminante, (7) validar cobertura. Ejemplo completo y autorado:
[`TEC-0033` (workflow bypass)](areas/G_logica-de-negocio-y/F-G01_logica-de-negocio/TEC-0033_salto-de-pasos-en-un-flujo-de/questions.yaml).

## El modelo de pregunta

Cada técnica despliega preguntas de estos `type` (la secuencia base, ampliable por ramas):

| # | `type` | Qué reduce |
|---|--------|-----------|
| 01 | `context` | ¿La app presenta el contexto que activa la técnica? |
| 02 | `preconditions` | ¿Se cumplen cuentas/roles/entorno y **no** la condición de no-aplicabilidad? |
| 03 | `structure` | ¿Qué rutas, funciones, estados o componentes intervienen? |
| 04 | `paths` | ¿Qué caminos alternativos alcanzan la operación evitando el control? |
| 05 | `controls` | ¿Dónde se valida la condición y cubre **todos** los caminos? |
| 06 | `differentiation` | ¿Qué observación distingue implementación segura de insegura? |
| 07 | `validation` | ¿Qué prueba **mínima** (una variable) confirma/refuta? |
| 08 | `interpretation` | ¿Qué otras explicaciones producen el mismo resultado? |
| 09 | `next` | ¿Qué corresponde después: reportar, cerrar, o abrir una técnica relacionada? |

Ejemplo (`TEC-0003`, IDOR horizontal):

```yaml
- id: Q-TEC-0003-05
  type: differentiation
  question: '¿Qué observacion distingue una implementacion segura de una insegura? Seguro: La respuesta
    deniega el acceso al objeto ajeno (403/404) con independencia del ID. Anomalo: Se obtienen datos de B...'
  required_evidence: [expected_response, anomalous_response, signal_with_reference]
  possible_outcomes: [discriminates, ambiguous, unknown]
  next: {discriminates: Q-TEC-0003-06, ambiguous: Q-TEC-0003-07, unknown: request_missing_evidence}
```

Campos de una pregunta: `id`, `type`, `question`, `purpose`, `required_evidence`, `answer_type`,
`possible_outcomes`, `next`, `depends_on`, `applicability_conditions`, `attacker_state_requirements`,
`source_fields` (trazabilidad al WPTA). Esquema completo en [`schema/question.schema.json`](schema/question.schema.json).

## Cómo lo consume un agente

```
1. Lee el contexto real de la app (evidence.json, api_map, infra_model.md).
2. indexa: indexes/technique-map.json  +  indexes/questions.json
3. Selecciona nodos aplicables (area -> familia -> tecnica).
4. Recorre questions.yaml: responde con evidencia las que puede; marca 'unknown' las que no.
5. Elige la pregunta pendiente de mayor valor informativo y genera el instrumento minimo
   (agente generador-instrumentos).
6. Registra respuestas/observaciones/experimentos en la MEMORIA DEL ENGAGEMENT, no aqui.
7. Sigue las reglas 'next' para la siguiente pregunta.
```

Contrato estable para el integrador (`bin/route_techniques.py`, agentes `atlas-tecnicas` /
`generador-instrumentos`): el campo clave es `technique_id` (une con el WPTA) y `indexes/questions.json`
da el lookup plano. Los `next` que valen `goto_technique_questions` se resuelven abriendo el
`questions.yaml` de la técnica destino y entrando por su pregunta `Q-<TEC>-01`.

## Regenerar

Requiere un checkout del WPTA (build input, **no** se versiona aquí):

```bash
git clone --depth 1 --branch main \
  https://github.com/apololifter/Web-Pentesting-Technique-Atlas-WPTA-.git third_party/wpta

python tools/generate_tree.py          # regenera areas/ + indexes/ + manifest.json (preserva authored)
python tools/validate_coverage.py      # estructura + trazabilidad + cobertura + ramas
python tools/lint_authoring.py         # GATES de autoria sobre los nodos authored
python tools/lint_authoring.py --list-seeds   # backlog de tecnicas pendientes de autoria
```

`manifest.json` registra el commit exacto del WPTA usado. Para actualizar el catálogo: `git -C third_party/wpta pull`
y volver a generar; el diff del árbol es la revisión.

## Estado actual

- **23** áreas · **61** familias · **439** técnicas (310 base + 129 variantes) · **3765** preguntas.
- Cobertura de técnicas: **100%**.
- Autoría: **1** técnica `authored` (TEC-0033) · **522** seeds pendientes de autoría según `AUTHORING.md`.

## Uso responsable

Catálogo para pruebas **autorizadas**, laboratorios e investigación. Documentar una pregunta **no**
autoriza a ejecutarla sobre un objetivo. La ejecución de la pregunta `validation` es una acción intrusiva y
requiere aprobación explícita (GATE del CEO).

## Licencia / atribución

El conocimiento se deriva del WPTA (ver su repositorio y licencia). Este repositorio solo aporta la
**capa de preguntas** y las herramientas de generación/validación.
