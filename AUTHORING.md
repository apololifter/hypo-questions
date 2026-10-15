# Estándar de autoría de preguntas — hypo-questions

> Norma `standard_version: "1.0"`. Define **cómo se analiza una técnica del WPTA, cómo se derivan
> sus preguntas, cómo se organizan en ramas y cómo se verifica** que permiten llegar a una
> hipótesis comprobable y a una prueba discriminante.
>
> Se aplica técnica por técnica. Una técnica cuyas preguntas cumplen esta norma se marca
> `authored: true` y pasa el linter (`tools/lint_authoring.py`).

---

## 0. Qué problema resuelve

Una lista de dimensiones genéricas ("¿hay IDOR?", "¿hay XSS?") no sirve para investigar una
aplicación real: no dice **qué mirar primero, qué evidencia falta, ni cómo distinguir una
implementación segura de una insegura**. Este estándar obliga a que cada pregunta nazca del
**mecanismo** de la técnica y conduzca a una **decisión** o a un **experimento**.

Regla de oro: **la pregunta correcta se deriva del mecanismo, no del nombre de la vulnerabilidad.**

## 1. Principios (no negociables)

1. **Mecanismo primero.** No se escribe ninguna pregunta hasta descomponer la técnica (§3, Paso 1).
2. **Falsabilidad.** Toda línea de investigación debe poder terminar en confirmado, refutado o
   inconcluso, con evidencia. Una pregunta que no puede falsarse no es una pregunta: es una opinión.
3. **Una variable.** Toda prueba cambia **una sola** cosa respecto de un baseline válido (§3, Paso 6).
4. **Evidencia, no supuestos.** Cada pregunta declara `required_evidence`. Lo que no se observó es
   `unknown` → `request_missing_evidence`, nunca una conclusión.
5. **Trazabilidad.** Cada nodo enlaza al `TEC-xxxx` real y al commit del WPTA (`wpta.commit`).
6. **Separación conocimiento / ejecución.** Aquí viven preguntas, dependencias y ramas. Las
   respuestas, observaciones y resultados viven **fuera del repo** (en el registro de cada análisis),
   nunca aquí.
7. **Cobertura explícita.** Los caminos alternativos (§3, Paso 4) y las precondiciones (§3, Paso 1)
   deben estar cubiertos por preguntas o marcados como fuera de alcance con razón.

## 2. Material de entrada (leer, no inventar)

Para cada técnica, la fuente canónica es la ficha `tecnica.json` del WPTA (y su `README.md`).
De ella se extraen, cuando existan, los campos:

`objective.{behavior,hypothesis,contexts,not_applicable}` · `procedure.{action,variable_to_change,
variables_to_hold_constant,steps,expected_secure_result,anomalous_result,evidence_to_record,
confirmation_criteria}` · `example.{normal,modified,what_changed,look_for}` ·
`replication.{requirements,variables,signal}` · `relations.detects_pattern` · `evidence.references`.

**Si un campo falta**, la firma del estándar es *enriquecer el mecanismo con razonamiento propio y
marcar el hueco*, no copiar la ausencia. Ejemplo: `TEC-0033` no trae `procedure.action` ni
`variable_to_change`; el autor del questionset los reconstruye desde el mecanismo y lo documenta.

## 3. El procedimiento obligatorio (7 pasos)

Para cada técnica, la ruta se construye con estos pasos; cada paso produce una parte del `questions.yaml`.

### Paso 1 — Comprender cómo se materializa la técnica
Produce el bloque `mechanism` del questionset:

```yaml
mechanism:
  invariant: >-            # la PROPIEDAD de seguridad que debe cumplirse
    Una operación con efectos solo se ejecuta si se completaron y verificaron
    los pasos previos obligatorios del flujo.
  preconditions: [ ... ]   # qué debe ser true para que el fallo sea posible
  components: [ ... ]      # piezas implicadas (auth, router, servicio, cola, caché, BD)
  sources: [ ... ]         # entradas controladas por el atacante
  transformations: [ ... ] # procesamiento entre fuente y sink
  controls:                # las comprobaciones que DEBERÍAN impedir el fallo
    - check: "..."
      applies_to: [ ... ]         # dónde se aplica
      bypass_candidates: [ ... ]  # formas plausibles de esquivarla (alimentan el Paso 3)
```

Regla: si no puedes nombrar el `invariant` y al menos un `control`, no entiendes la técnica
todavía. Vuelve a la ficha. Determina además **qué tendría que averiguar un pentester** para
descubrir si ese mecanismo existe en una aplicación concreta.

### Paso 2 — Convertir el mecanismo en una ruta de investigación

Traduce el mecanismo en una secuencia lógica que lleve del contexto general a los detalles que
revelan la vulnerabilidad. La ruta investiga progresivamente:

- qué objetivo funcional puede verse afectado;
- qué funcionalidades y operaciones podrían alcanzarlo;
- qué endpoints, entradas, estados, roles, identidades o relaciones intervienen;
- cómo procesa la aplicación esas operaciones y qué controles aplica;
- qué comportamiento materializaría el mecanismo de la técnica;
- qué evidencia confirmaría o descartaría esa posibilidad.

Correspondencia base entre el mecanismo y el tipo de pregunta (§5):

| Elemento del mecanismo | Tipo de pregunta |
|---|---|
| `preconditions` | `context` / `preconditions` |
| `sources`, `transformations`, `components` | `structure` |
| `controls` | `controls` |
| caminos alternativos | `paths` |
| `invariant` | `differentiation` |
| (verificación) | `validation` |
| (falsos positivos) | `interpretation` |
| (continuación) | `next` |

La secuencia es orientativa; las preguntas concretas se derivan del mecanismo de cada técnica, no de
una plantilla universal.

### Paso 3 — Formular preguntas que hagan avanzar la investigación

Cada pregunta debe descubrir algo que el agente **todavía no conoce** y necesita averiguar:

- investigar un aspecto específico del mecanismo de la técnica;
- indicar qué información o evidencia obtener (`required_evidence`);
- permitir distinguir entre explicaciones relevantes;
- conducir a una nueva pregunta o a una decisión de investigación;
- **no asumir** endpoints, parámetros, tecnologías, modelos de datos o controles que aún no se han
  identificado.

Prohibido: preguntas como «¿existe esta vulnerabilidad?» antes de haber investigado las condiciones que
permitirían responderlas (ver anti-patrones, §8).

### Paso 4 — Construir un paso a paso adaptativo

Cada pregunta es un nodo con `possible_outcomes` y aristas `next`; la siguiente depende de lo descubierto.
Ramifica cuando el hallazgo cambia el razonamiento:

- funcionalidad relevante → profundizar en operaciones, entradas, estados y controles;
- parámetro o mecanismo prometedor → investigar cómo lo procesa el sistema y qué efecto tiene;
- el mecanismo esperado no existe → decidir si la técnica no aplica o falta localizar otra ruta;
- evidencia insuficiente → preguntar qué falta (`request_missing_evidence`), nunca concluir;
- varios caminos → ramas separadas cuando requieran razonamientos o pruebas distintas.

Formula las ramas alternativas como preguntas tipo `paths` y declara cada dimensión en `alternative_paths`:

```yaml
alternative_paths:
  - { dimension: "ruta",   variation: "endpoint equivalente que ejecuta el mismo efecto", question_id: Q-TEC-0033-05 }
  - { dimension: "estado", variation: "reutilizar un flujo propio ya completado",          question_id: Q-TEC-0033-05 }
  - { dimension: "rol",    variation: "otro rol/tenant con menos privilegios",             question_id: Q-TEC-0033-04 }
```

Dimensiones mínimas: `ruta/endpoint`, `metodo/transporte`, `estado del flujo`, `rol/identidad/tenant`,
`entrada/encoding/parser`, `capa que valida` (cliente/servidor/proxy), `version/entorno`,
`concurrencia/orden temporal`.

Gramática de ramas (§6):
- todo outcome no terminal apunta a **otra pregunta** (no dejar cabos);
- todo `unknown`/`partial` apunta a `request_missing_evidence` y nombra la evidencia que falta;
- toda rama termina en un token terminal (`stop_*`, `report`, `done`).

### Paso 5 — Conducir las preguntas hasta una hipótesis concreta

La secuencia debe reunir progresivamente las piezas de una **hipótesis causal**:

- qué operación o funcionalidad interviene;
- qué precondiciones y estado de atacante se requieren (`attacker_state_requirements`);
- qué entrada, secuencia o capacidad controla el atacante;
- qué comportamiento de implementación hace posible el fallo;
- qué propiedad de seguridad podría incumplirse (`invariant`);
- qué resultado observable permitiría comprobarlo.

No es obligatorio que una sola pregunta lo descubra todo; el árbol guía para que se descubra por pasos.
El campo `hypothesis` debe expresar el mecanismo causal, no una sospecha, y poder refutarse con una
observación.

### Paso 6 — Llegar a la verificación del posible fallo

Cuando las respuestas identifiquen un mecanismo plausible, produce el bloque `discriminating_test` (y la
pregunta `validation` que lo materializa): qué comportamiento normal sirve de referencia, qué variable se
modifica, qué se mantiene constante y qué observación distingue una ejecución legítima de una vulneración.

```yaml
discriminating_test:
  baseline: "recorrer el flujo completo y capturar la petición del paso final"
  change: "invocar SOLO el paso final, sin los previos"
  constant: ["sesión", "cabeceras", "identificador del recurso"]
  expected_secure: "el backend rechaza o redirige al paso pendiente (409/422/redirección)"
  anomalous: "el efecto persiste (p. ej. el pedido queda confirmado)"
  signal: "estado persistido tras la petición fuera de orden"
  confirmation_criteria: "confirmada si el efecto final ocurre sin los pasos previos"
  falsation: "el backend exige el orden (rechazo explícito) => refutada"
```

El árbol **guía** la investigación y determina qué comprobar. La **ejecución** de las pruebas, su
autorización y el registro de resultados son responsabilidades separadas.

### Paso 7 — Validar que el árbol realmente guía hacia la vulnerabilidad

Revisa el recorrido completo y comprueba que:

- cada pregunta contribuye a descubrir o descartar una condición relevante de la técnica;
- el orden tiene sentido investigativo y las respuestas determinan cómo continuar;
- se cubren rutas alternativas y variantes pertinentes del mecanismo;
- ninguna rama queda abandonada sin una salida definida;
- no se presupone información que el agente aún necesita descubrir;
- no hay redundancias ni preguntas que solo repiten el nombre de la técnica;
- existe un recorrido comprensible hasta una hipótesis verificable;
- si la evidencia no permite continuar, el árbol identifica qué falta en vez de inventar una conclusión.

La matriz de cobertura es `precondición/control × camino` → `question_id`. Los huecos se resuelven o se
declaran fuera de alcance con razón. `tools/lint_authoring.py` verifica esto automáticamente (§10).

## 4. Modelo de datos

Un `questions.yaml` (por área, familia o técnica) = un **QuestionSet**
(`schema/questionset.schema.json`). Campos de autoría que añade este estándar:
`standard_version`, `authored`, `reviewed`, `mechanism`, `discriminating_test`, `alternative_paths`.
Cada pregunta sigue `schema/question.schema.json`.

## 5. Taxonomía de preguntas (9 tipos)

| `type` | Pregunta que responde |
|---|---|
| `context` | ¿La app presenta el contexto que activa la técnica? |
| `preconditions` | ¿Se cumplen las precondiciones y **no** la condición de no-aplicabilidad? |
| `structure` | ¿Qué rutas, funciones, estados o componentes intervienen? |
| `paths` | ¿Qué caminos alternativos alcanzan la operación evitando el control? |
| `controls` | ¿Dónde se valida la condición y cubre **todos** los caminos? |
| `differentiation` | ¿Qué observación distingue seguro de inseguro (el invariante)? |
| `validation` | ¿Qué prueba **mínima** (una variable) confirma/refuta? |
| `interpretation` | ¿Qué otras explicaciones producen el mismo resultado? |
| `next` | ¿Qué corresponde después: reportar, cerrar o abrir una técnica relacionada? |

## 6. Gramática de ramas y tokens terminales

- `id`: `Q-AREA-<code>-NN` · `Q-F-<FAM>-NN` · `Q-TEC-xxxx-NN`.
- `next`: mapa `outcome -> (id de pregunta | token terminal | null)`.
- Tokens terminales (en `manifest.json:terminals`):
  `stop_not_applicable`, `stop_not_relevant`, `stop_precondition_unmet`, `stop_false_positive`,
  `request_missing_evidence`, `request_scope_decision`, `goto_technique_questions`, `report`, `done`.
- `depends_on`: preguntas que deben resolverse antes (trazabilidad del orden mental).
- `attacker_state_requirements`: cuentas/roles/entorno necesarios (posición del atacante).
- `source_fields`: campos del WPTA de los que se derivó la pregunta.

## 7. Reglas de calidad (GATES)

**Gate por pregunta** (una pregunta se rechaza si…):
- G1 no declara `required_evidence`, o
- G2 no tiene ≥2 `possible_outcomes` con aristas definidas, o
- G3 es genérica («¿es vulnerable?») sin nombrar componente/condición (§8), o
- G4 deja un outcome no-terminal sin destino, o
- G5 mezcla dos incertidumbres en una sola pregunta (viola "una variable").

**Gate por técnica** (una técnica es `authored: true` solo si…):
- T1 tiene `mechanism.invariant` y ≥1 `mechanism.controls`, y
- T2 tiene `discriminating_test` completo (baseline, change, constant, expected_secure, anomalous), y
- T3 toda `mechanism.preconditions[i]` está cubierta por al menos una pregunta, y
- T4 cada `alternative_paths[j]` tiene `question_id` que existe, y
- T5 existe una pregunta `validation` con la modificación mínima, y
- T6 todas las ramas resuelven (terminal o pregunta existente) — lo comprueba `validate_coverage.py`, y
- T7 no hay preguntas redundantes (texto/incertidumbre repetida sin cambiar condición).

## 8. Anti-patrones (prohibido)

- ❌ «¿La aplicación es vulnerable a X?» — no es falsable ni accionable.
- ❌ Preguntas de encuesta («¿usa JWT?») sin conectarlas a un control o invariante.
- ❌ Dos cambios en la prueba (`change` que altera más de una variable).
- ❌ `unknown` como callejón sin salida: debe pedir la evidencia faltante.
- ❌ Guardar respuestas/observaciones en el questionset (el repo es solo preguntas).
- ❌ Inventar IDs `TEC-xxxx` o campos que el WPTA no declara (se marcan como `missing_catalog_fields`).

## 9. Flujo sistemático de construcción del repo

1. **Seed generado.** `tools/generate_tree.py` convierte cada ficha en un questionset borrador
   (`generated: true`, `authored: false`).
2. **Priorizar lotes.** Se eligen familias/áreas de mayor valor (p. ej. control de acceso `D`,
   lógica de negocio `G`) y se recorren por lotes.
3. **Autoría.** Para cada técnica, aplicar los 7 pasos, partir de la plantilla
   (`templates/technique.questions.template.yaml`) y marcar `generated: false`, `authored: true`,
   `reviewed: true`. La regeneración **preserva** estos archivos.
4. **Lint.** `python tools/lint_authoring.py` exige GATES T1-T7 a lo autorado y reporta los seeds.
5. **Validar.** `python tools/validate_coverage.py` (estructura, trazabilidad, cobertura, ramas).
6. **Repetir** hasta cubrir el objetivo; los seeds restantes son el backlog visible.

## 10. Verificación automática

| Herramienta | Qué garantiza |
|---|---|
| `tools/validate_coverage.py` | estructura, IDs, cobertura WPTA 100%, ramas `next` resueltas, sin respuestas |
| `tools/lint_authoring.py` | GATES de autoría (T1-T7), anti-patrones, redundancia, cobertura precondición×camino |
| CI (`.github/workflows/validate.yml`) | regeneración determinista contra el commit WPTA fijado |

## 11. Plantilla y ejemplo trabajado

- Plantilla: `templates/technique.questions.template.yaml`
- Checklist: `templates/AUTHORING_CHECKLIST.md`
- Ejemplo completo (workflow bypass, el caso del enunciado):
  `areas/G_logica-de-negocio-y/F-G01_logica-de-negocio/TEC-0033_salto-de-pasos-en-un-flujo-de/questions.yaml`

## 12. Checklist de aceptación de una técnica

- [ ] `mechanism.invariant` redactado como propiedad de seguridad.
- [ ] `mechanism.preconditions` enumeradas y cada una cubierta por una pregunta.
- [ ] `mechanism.controls` con `applies_to` y `bypass_candidates`.
- [ ] `alternative_paths` con las dimensiones relevantes y su `question_id`.
- [ ] Preguntas de los 9 tipos presentes cuando apliquen; ninguna genérica.
- [ ] `discriminating_test` con baseline, una variable, constantes, esperado y anómalo.
- [ ] Todas las ramas resuelven; `unknown` pide evidencia.
- [ ] `wpta.source` y `wpta.commit` correctos; `missing_catalog_fields` declarados.
- [ ] `authored: true`, `reviewed: true`, `standard_version: "1.0"`.
- [ ] `validate_coverage.py` y `lint_authoring.py` en verde para esta técnica.
