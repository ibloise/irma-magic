# H2 — Modelos de influenza y operaciones FASTA

## Resultado

Se validan estrictamente los modelos, las agrupaciones y las exportaciones FASTA con fixtures sintéticos. El trabajo permanece en la rama local `codex/audit-regression`; no se ha abierto PR ni se ha publicado esta continuación.

## Esquema de IDs admitido

El parser exige concordancia completa con:

```text
<sample>_<A|B>_<segment>[_<Hn|Nn>]
```

- `<sample>` puede contener guiones bajos, pero no espacios en blanco. El parser conserva el ID de muestra completo hasta los separadores finales reconocidos.
- `<segment>` debe ser uno de los valores actuales de `SEGMENTS`: `PB2`, `PB1`, `PA`, `NP`, `HA`, `NA`, `MP` o `NS`.
- Se conserva la constante vigente `M = "MP"`; no se cambió por falta de evidencia adicional de IDs reales de IRMA.
- El sufijo de subtipo solo se admite para influenza A: `Hn` en HA y `Nn` en NA. IDs de influenza B con ese sufijo y sufijos en otros segmentos se rechazan.
- No se valida el alfabeto de la secuencia ni se altera su contenido.

## Matriz de cambios

| Área | Antes | Ahora |
| --- | --- | --- |
| ID de segmento | Regex parcial; podía aceptar prefijos/sufijos no consumidos y segmentos desconocidos. | `fullmatch` del esquema anterior, tipo A/B y segmento conocido; IDs inválidos fallan con detalle. |
| `FluGenome` | Acceso a `self.A_TYPE`, conjuntos vacíos indexados, segmentos duplicados sobrescritos en dict. | Tipo contrastado con constantes, genoma vacío rechazado, ID/tipo únicos y duplicados detectados antes del índice. |
| Subtipo | Podía fallar con HA/NA ausentes o sin subtipo, y construía valores parciales con `x`. | Subtipo solo si A tiene HA y NA con ambos sufijos; en otro caso `None`. No se infiere información. |
| Colecciones | `append` descartaba objetos de tipo incorrecto; el orden dependía de la entrada y mapas podían sobrescribir IDs. | Tipo incorrecto produce `TypeError`; agrupación ordenada y IDs de genoma duplicados rechazados. `to_segment_dict()` usa `append(segment)` explícitamente. |
| Lectura FASTA | Archivo vacío acababa en `IndexError`; `read_file` no distinguía vacío de múltiples registros. | Vacío produce `ValueError` informativo; `read_file` exige exactamente un registro y `from_fasta` acepta varios. |
| Escritura FASTA | `out_dir=None` podía romper `mkdir`; sobrescribía destinos y generaba archivos vacíos para segmentos ausentes. | Directorio predeterminado seguro (`.`), creación recursiva, validación de nombres/grupos, preflight de colisiones y rechazo de sobrescritura. No se crean FASTA vacíos para segmentos sin registros. |
| CLI del módulo | `--mode` podía quedar en `None`; salida podía llegar como `None`. | `--mode` es obligatorio y `--out_dir` usa `.` por defecto; la API de escritura también acepta `None`. |

### Aclaración sobre `to_segment_dict()`

La hipótesis previa de que `extend(value)` fallaba era incorrecta: `Collection.extend(*elements)` recibe el `FluSegment` como un argumento válido y lo añade mediante `append`. Se cambió a `append(segment)` para hacer explícito el contrato y ordenar la agregación; no se atribuye el cambio a un fallo reproducido de `extend`.

## Pruebas y comandos

Se añadió `tests/test_flu_tools.py` con IDs y secuencias sintéticos, incluyendo A H1N1/H3N2, B, muestra con guiones bajos, FASTA vacío/mal formado/multirregistro, segmentos duplicados, agrupaciones, salidas y colisiones. No se usan muestras clínicas ni CDC-IRMA.

```text
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src tests
git diff --check
```

Resultado: **56 tests pasaron**; `compileall` y `git diff --check` finalizaron correctamente. Se validó el contenido exacto de las salidas y su relectura para comprobar IDs y secuencias.

## Límites

- La aceptación del esquema de IDs se contrastó con el formato que el código previo generaba (`id_type_segment[_segment_type]`), no con una instalación real de IRMA ni con fixtures reales. El uso de `MP` se mantiene sin reinterpretación.
- Los grupos de muestra se exportan con el ID de muestra como nombre de archivo; IDs que incluyan separadores de ruta se rechazan en escritura.
- Los segmentos ausentes se omiten en modo `segments`; no se crean archivos FASTA vacíos.
- `pandas` sigue utilizándose para resúmenes y no está declarado en `pyproject.toml`; H2 no añadió ni instaló dependencias.
- No se afirma validación biológica o clínica.

H2 queda listo para revisión. No se abrió PR según la instrucción del usuario; la siguiente puerta es autorización de H3.
