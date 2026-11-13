# H3 — CLI, renombrado y empaquetado

## Resultado

H3 está implementado en la rama local `codex/audit-regression`. No se ha hecho
push, PR, merge ni publicación. CDC-IRMA sigue siendo un programa externo.

## Cambios

- `irmagic` conserva el subcomando `bulker`; ejecutar sin subcomando ahora da
  error de argumentos (código 2). La ayuda raíz y la de `bulker` están
  disponibles. No se añadieron subcomandos.
- `IrmaRenamer`, `FastaRenamer` e `IrmaDirRenamer` escriben en `out_dir`, crean
  el directorio si hace falta, usan destinos completos y rechazan destinos
  existentes o colisiones entre entradas antes de copiar. Los originales se
  mantienen intactos. La selección por extensión tolera nombres con varios
  puntos.
- `FastaRenamer` procesa todos los registros, conserva IDs ya prefijados solo
  cuando coinciden con el prefijo completo y su separador, conserva secuencias
  y descripciones y rechaza IDs de salida duplicados.
- Se retiró pandas: `FluGenomeSummarizer.summary_to_csv()` y
  `bulk_summary_to_csv()` escriben cabecera y filas mediante `csv.DictWriter`
  en un handle de texto abierto. `summary()` y `bulk_summarize()` siguen
  devolviendo diccionarios/listas. Los métodos DataFrame anteriores se
  sustituyeron; esto cambia deliberadamente esa API.
- `pyproject.toml` incluye el README en los metadatos y mantiene el entrypoint
  `irmagic`. El paquete no necesita dependencias Python de runtime. README
  explica instalación local y que CDC-IRMA se instala aparte.

## Validación ejecutada

- `PYTHONPATH=src python -m unittest discover -s tests`: **71 tests pasaron**.
- `python -m compileall -q src tests`: correcto.
- `git diff --check`: correcto.
- `python -m pip wheel --no-deps --no-build-isolation --wheel-dir <directorio-temporal> .`:
  wheel `irma_magic-0.1.0-py3-none-any.whl` construido con el backend ya
  instalado, sin instalar dependencias.
- Wheel instalado con `--no-deps` en un entorno temporal; desde otro directorio,
  `irmagic --help`, `irmagic bulker --help` e imports de `irma_magic`,
  `irma_magic.cli` y `irma_magic.flu_tools` funcionaron. Sin subcomando,
  `irmagic` termina con código 2.

## Límites y compatibilidad

- La API previa `summary_to_df()`/`bulk_df_summarize()` devolvía objetos pandas;
  se reemplaza por escritura CSV a un handle estándar. No se encontró uso
  interno de esos métodos aparte de su definición.
- No se instaló ni ejecutó CDC-IRMA real. No se probó instalación editable; el
  wheel local y su console script se probaron desde un entorno temporal.
- La prueba de wheel no instala dependencias adicionales. No hay dependencias
  Python de runtime declaradas ni importadas en el código actual.
- No se afirma validación biológica o clínica.

H3 queda listo para revisión. Según el plan, el siguiente hito es H4; no se ha
iniciado.
