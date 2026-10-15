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

## Prompt principal — metodología para crear árboles de preguntas por técnica WPTA

> Este es el **prompt principal** del repositorio: la metodología que gobierna a quien autora las
> preguntas. El desarrollo operativo (GATES T1-T7, taxonomía de preguntas, checklist) está en
> [`AUTHORING.md`](AUTHORING.md).

### Objetivo

Para cada técnica del Web Pentesting Technique Atlas (WPTA), construir un **árbol de preguntas** que guíe
al agente, paso a paso, durante la investigación de una aplicación hasta descubrir si existe una
vulnerabilidad compatible con el mecanismo de esa técnica.

Las preguntas deben funcionar como una **ruta de investigación**: cada una indica qué necesita averiguar el
agente, qué evidencia debe buscar y cómo utilizar la respuesta para decidir el siguiente paso.

El resultado no es una descripción de la técnica, una lista de comprobaciones independientes ni un
cuestionario genérico. Es una **guía de razonamiento** que permite avanzar desde el objetivo funcional de
la técnica hasta localizar un posible punto de materialización, comprender su mecanismo y llegar a una
hipótesis verificable.

### Procedimiento obligatorio

**1. Comprender cómo se materializa la técnica.** Analizar la ficha de la técnica WPTA para identificar el
mecanismo que produce la vulnerabilidad, las condiciones necesarias, las propiedades de seguridad afectadas
y los comportamientos de la aplicación que podrían permitirla. Determinar qué tendría que averiguar un
pentester para descubrir si ese mecanismo existe en una aplicación concreta.

**2. Convertir el mecanismo en una ruta de investigación.** Traducir el mecanismo en una secuencia lógica
de preguntas que lleve al agente desde el contexto general hasta los detalles necesarios para identificar
la vulnerabilidad. La ruta debe investigar progresivamente:

- Qué objetivo funcional puede verse afectado.
- Qué funcionalidades y operaciones podrían permitir alcanzar ese objetivo.
- Qué endpoints, entradas, estados, roles, identidades o relaciones intervienen.
- Cómo procesa la aplicación esas operaciones y qué controles aplica.
- Qué comportamiento permitiría que el mecanismo de la técnica se materializara.
- Qué evidencia permitiría confirmar o descartar esa posibilidad.

Esta secuencia es orientativa. Las preguntas concretas deben derivarse del mecanismo de cada técnica, no de
una plantilla universal.

**3. Formular preguntas que hagan avanzar la investigación.** Cada pregunta debe ayudar a descubrir algo
que el agente todavía no conoce y que necesita averiguar para avanzar hacia la vulnerabilidad. Una pregunta
bien formulada debe:

- Investigar un aspecto específico del mecanismo de la técnica.
- Indicar qué información o evidencia debe obtenerse.
- Permitir distinguir entre explicaciones relevantes.
- Conducir a una nueva pregunta o a una decisión de investigación.
- Evitar asumir endpoints, parámetros, tecnologías, modelos de datos o controles que todavía no se han
  identificado.

No formular preguntas como «¿existe esta vulnerabilidad?» cuando el agente todavía no ha investigado las
condiciones que permitirían responderla.

**4. Construir un paso a paso adaptativo.** Las preguntas deben estar conectadas mediante ramas
condicionales; la siguiente pregunta dependerá de lo que el agente descubra en la anterior.

- Si encuentra una funcionalidad relevante, debe profundizar en sus operaciones, entradas, estados y
  controles.
- Si encuentra un parámetro o mecanismo prometedor, debe investigar cómo lo procesa el sistema y qué efecto
  tiene.
- Si descubre que el mecanismo esperado no existe, debe determinar si la técnica realmente no aplica o si
  todavía falta localizar otra ruta de materialización.
- Si la evidencia es insuficiente, debe preguntar qué necesita averiguar a continuación, en lugar de saltar
  a una conclusión.
- Si aparecen varios caminos posibles, debe investigarlos por ramas separadas cuando requieran
  razonamientos o pruebas diferentes.

Cada rama debe indicar la siguiente pregunta, la evidencia pendiente o una condición justificada para
cerrar esa línea de investigación.

**5. Conducir las preguntas hasta una hipótesis concreta.** La secuencia debe permitir que el agente reúna
progresivamente las piezas necesarias para formular una hipótesis causal:

- Qué operación o funcionalidad interviene.
- Qué precondiciones y estado de atacante se requieren.
- Qué entrada, secuencia o capacidad puede controlar el atacante.
- Qué comportamiento de implementación hace posible el fallo.
- Qué propiedad de seguridad podría incumplirse.
- Qué resultado observable permitiría comprobarlo.

No es obligatorio que una sola pregunta descubra todos estos elementos; la finalidad del árbol es guiar al
agente para que los descubra mediante preguntas sucesivas.

**6. Llegar a la verificación del posible fallo.** Cuando las respuestas identifiquen un mecanismo
plausible, el árbol debe conducir a las preguntas necesarias para establecer cómo comprobarlo. Debe quedar
claro qué comportamiento normal sirve como referencia, qué variable tendría que modificarse, qué
condiciones deben mantenerse constantes y qué observación permitiría distinguir entre una ejecución
legítima y una vulneración de la propiedad de seguridad.

El árbol de preguntas guía la investigación y determina qué se debería comprobar. La ejecución de las
pruebas, su autorización y el registro de resultados son responsabilidades separadas.

**7. Validar que el árbol realmente guía hacia la vulnerabilidad.** Revisar el recorrido completo y
comprobar que:

- Cada pregunta contribuye a descubrir o descartar una condición relevante de la técnica.
- El orden de las preguntas tiene sentido investigativo.
- Las respuestas determinan cómo continuar.
- Se consideran rutas alternativas y variantes pertinentes del mecanismo.
- Las ramas no quedan abandonadas sin una salida definida.
- No se presupone información que el agente aún necesita descubrir.
- Las preguntas evitan redundancias y no se limitan a repetir el nombre de la técnica.
- Existe un recorrido comprensible desde el inicio de la investigación hasta una hipótesis verificable.
- Si la evidencia no permite continuar, el árbol identifica qué información falta en lugar de inventar una
  conclusión.

### Resultado esperado

Cada técnica WPTA debe disponer de un **árbol de preguntas** que el agente pueda recorrer durante una
investigación real. El árbol debe indicarle qué averiguar primero, qué buscar según lo descubierto, qué
condiciones investigar después y cómo avanzar hasta identificar un mecanismo de vulnerabilidad y establecer
cómo verificarlo.

No se exige una cantidad fija de preguntas ni una estructura idéntica para todas las técnicas. Se exige que
cada árbol constituya una guía paso a paso, específica para el mecanismo de la técnica y capaz de adaptarse
a la evidencia encontrada en la aplicación.

**Criterio fundamental:** si un agente sigue las preguntas y sus ramificaciones, debe poder avanzar
sistemáticamente en la investigación de la técnica, en lugar de recibir una lista de temas que debe analizar
por su cuenta.

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
