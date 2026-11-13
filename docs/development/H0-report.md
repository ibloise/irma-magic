# H0 — Informe de auditoría y regresión

## Estado examinado

- Rama de trabajo: `codex/audit-regression`, creada desde `develop`.
- `develop` examinado en: `6b40202ce3a8e54a7bfe8b654cd90d6855321373`.
- Commit inicial de los cambios ya presentes en el árbol: `79dac04` (`chore: prepare package migration and development plan`).
- No se realizaron arreglos funcionales durante H0.

## CLI e interfaces observadas

- `irmagic` está configurado como entry point a `irma_magic.cli:main` en `pyproject.toml`. La CLI expone el subcomando `bulker`, opciones de archivos, módulo, tipo de lecturas y patrones; `main()` tiene invocación directa en `src/irma_magic/cli.py`.
- Las interfaces de Python actuales están en `src/irma_magic`: `FastqFile`, `FastqSet`, `FastqCollection`, `IrmaBulk`; herramientas de influenza (`FluSegment`, colecciones, genomas, resumen y escritura FASTA); y renombradores (`IrmaRenamer`, `FastaRenamer`, `IrmaDirRenamer`). `src/irma_magic/__init__.py` no reexporta nombres.
- En la revisión del árbol no había suite de tests, README de usuario, licencia ni workflows de CI. Sí existe `AGENTS.md`, documentación del plan y `pyproject.toml`. El inventario se refiere al árbol de trabajo al inicio de H0.
- `pyproject.toml` declara el backend `setuptools>=61` y Python `>=3.8`, pero no declara las importaciones de runtime `pandas` y Biopython que usa `flu_tools.py`/`renamer.py`. Biopython no está instalado en el entorno de revisión, así que no fue posible importar ni ejecutar esos módulos.

## Matriz de hipótesis

| # | Resultado | Evidencia y severidad | Prueba / alcance |
| --- | --- | --- | --- |
| 1 | **Confirmado** | `files.py:128-137`: separa por patrón y hace `zip`, asociando por posición; los sobrantes no aparecen. Alto: puede mezclar muestras o perder lecturas. | `test_pairs_by_sample_not_list_position` y `test_orphan_read_is_not_silently_dropped` reproducen ambos casos. |
| 2 | **Confirmado** | `files.py:100-103` transforma cada ruta en el filtro y de nuevo en la expresión; `120-126` imprime y devuelve `None` ante extensión inválida. Medio: trabajo duplicado y entrada descartada sin fallo explícito. | `test_transform_file_runs_once_per_input`; inspección confirma impresión para inválidos. |
| 3 | **Confirmado** | `files.py:40-46` permite cualquier nombre terminado en `.gz`; `48-50` no inicializa `ext` ni `full_name` en `FastqFile`. Medio. | `test_rejects_non_fastq_gzip` y `test_fastq_file_exposes_full_name`. Se comprobaron las cuatro extensiones FASTQ previstas en H0. |
| 4 | **Confirmado** | `bulk.py:50-59` construye argumentos usando `file.name`, perdiendo el directorio de origen. Alto si hay nombres repetidos o la ejecución ocurre desde otra ruta. | `test_command_preserves_source_path_with_spaces`. |
| 5 | **Confirmado** | `bulk.py:66-68` no inspecciona el resultado de `subprocess.run`. Alto: el llamador puede continuar como si IRMA hubiera terminado bien. | `test_nonzero_irma_exit_is_reported` con un resultado simulado de código 2. |
| 6 | **Confirmado** | `flu_tools.py:185-192` usa `self.A_TYPE`, pero `A_TYPE` está definido en `FluSegment` (líneas 23-24), no en `FluGenome`. Alto: construir genomas tipo A falla con `AttributeError`. | Reproducible por lectura; ejecución bloqueada por falta de Biopython. |
| 7 | **Descartado** | `flu_tools.py:112-115` define `extend(*elements)` e itera cada argumento; `to_segment_dict()` le pasa un `FluSegment` como un argumento en `flu_tools.py:279-283`. No requiere un iterable de segmentos y no se observó el fallo alegado. | Contrato contrastado estáticamente; ejecución bloqueada por falta de Biopython. |
| 8 | **Confirmado parcialmente** | `flu_tools.py:93-98` indexa `records[0]` sin manejar FASTA vacío (`IndexError`). `FluGenome._get_id()` hace lo mismo con un conjunto vacío (`175-177`). `_get_segment_type()` indexa `segment_type[1]` cuando el segmento existe (`193-201`), lo que falla si falta subtipo. Alto para entradas que llegan a esas rutas. | Casos identificados por inspección; pruebas de ejecución bloqueadas por Biopython. |
| 9 | **Confirmado** | `renamer.py:37-45` guarda `out_dir`; `12-17` construye y copia al nombre relativo `dest_file`, sin usarlo. `copyfile` sobrescribe destinos existentes. Alto por salida inesperada y riesgo de sobrescritura. | Inspección estática; Biopython ausente impide importar el módulo para prueba dinámica. |
| 10 | **Descartado para la estructura equivalente actual** | `src/irma_magic/cli.py:45-46` invoca `main()` al ejecutarse directamente y usa importaciones relativas (`2-3`). | Contraste directo del CLI equivalente actual; los ficheros antiguos `scripts/irmagic.py` y `magic_irma` ya no están en `develop`. |
| 11 | **Confirmado con matices** | La búsqueda de todo el árbol inicial no encontró README, licencia, configuración de tests ni workflows. `pyproject.toml` sí existe en el árbol actual y no declara dependencias runtime. | Inventario de archivos; no implica que esos recursos nunca hayan existido fuera de este checkout. |

## Regresión y comandos

Suite añadida: `tests/test_h0_regressions.py`. Usa únicamente `unittest`, rutas sintéticas y un mock de `subprocess.run`; no instala dependencias ni llama a CDC-IRMA.

Comando ejecutado:

```text
PYTHONPATH=src python -m unittest discover -s tests -v
```

Resultado: **8 tests ejecutados; 1 pasó y 7 quedaron como `expected failure`**, que registra los defectos FASTQ/ejecución sin introducir arreglos en H0. No hubo fallos inesperados. Los casos de influenza y renombrado quedan pendientes de ejecución dinámica por falta de Biopython.

## Riesgos, límites y siguiente puerta

- La suite no cubre aún influenza, escritura FASTA, colisiones ni directorio de salida en ejecución; esos hallazgos son estáticos y necesitan entorno con dependencias disponibles/autorizadas.
- El `expected failure` de códigos de retorno simula un `CompletedProcess`; no lanza procesos ni valida la sintaxis externa de CDC-IRMA.
- Las observaciones no validan comportamiento biológico o clínico.
- H0 no cambia código funcional. La puerta indicada por el plan es revisión/acuerdo de este inventario antes de iniciar H1.
