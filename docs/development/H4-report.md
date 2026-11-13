# H4 — Informe de preparación para release

## Decisión

**NO-GO por ahora para publicar.** Tras la revisión del mantenedor, el requisito
de Python es `>=3.12` y la matriz actual prueba Python 3.12–3.14. En la
ejecución anterior pasaron Python 3.12 y 3.13; Python 3.8 y 3.9 fallaron en
`setup-python` porque Ubuntu 26.04 ya no ofrecía esas versiones. Esos
intérpretes ya no forman parte del rango admitido. La matriz actualizada queda
pendiente de ejecución en GitHub. No se abrió PR, no se hizo merge, no se creó
tag y no se publicó nada.

## Identificación

- Rama: `codex/audit-regression`.
- Base H4 revisada: `6a6b5b2` (`feat: complete CLI packaging and safe renaming`).
- Commit de implementación H4: `57a661e` (`release: prepare 0.1.0a1 candidate`).
- Commit posterior que retiró la guía de contribución: `e0fbd1d`; está publicado
  en `origin/codex/audit-regression`.
- PR: ninguno; el trabajo se mantiene local según la instrucción del mantenedor.
- Distribución candidata: `irma-magic==0.1.0a1`.
- Licencia: MIT, seleccionada explícitamente por el mantenedor; texto en
  `LICENSE` y metadatos de paquete configurados.

## Cambios y evidencias

- `.github/workflows/tests.yml` ejecuta `unittest` con Python 3.12, 3.13 y
  3.14 en Ubuntu 22.04, sin instalar CDC-IRMA ni dependencias Python de
  runtime.
- `tests/test_h4_validation.py` prueba lotes FASTQ single y paired con un
  backend de subprocess simulado. Verifica los argumentos completos, las rutas
  y el ID de salida. Un par mal formado falla con estado 2 antes de invocar el
  backend.
- Tras la indicación del mantenedor de recuperar la CLI histórica, `irmagic`
  expone ahora `bulker`, `renamer` y `flu`. El modo `flu` conserva `--summary`
  y escribe `summary.csv` con el módulo `csv` estándar. README usa estos tres
  subcomandos; `python -m irma_magic.flu_tools` también ejecuta el mismo parser.
- README documenta instalación, Python 3.12+, comandos de ejemplo, sufijos
  FASTQ, esquema de IDs FASTA, agrupación/salidas, errores, códigos de estado y
  límites. Se añadieron `CHANGELOG.md` y `docs/development/CONTRIBUTING.md`; el
  mantenedor pidió retirar después la guía de contribución.
- `pyproject.toml` identifica MIT, declara `0.1.0a1` y requiere Python `>=3.12`,
  según la decisión del mantenedor.
  El paquete no declara dependencias Python de runtime; CDC-IRMA es externo.
- `IrmaBulk.run()` devuelve 0 después de un lote correcto, manteniendo el
  contrato de salida del entrypoint CLI.
- Revisión de texto de archivos del repositorio: no se encontraron claves,
  tokens, claves privadas, contraseñas ni rutas locales personales en el
  escaneo de patrones ejecutado. La revisión no sustituye un escáner dedicado
  ni confirma secretos históricos fuera del árbol revisado.

## Matriz de validación

| Prueba | Entorno/comando | Resultado |
| --- | --- | --- |
| Suite unitaria e integración | Python 3.13.5; `PYTHONPATH=src python -m unittest discover -s tests -v` | **76 tests pasaron**. Los casos de ejecución IRMA usan mocks; no ejecutan IRMA real. |
| Compilación de fuentes | Python 3.13.5; `python -m compileall -q src tests` | Pasó. |
| Espacios y formato del diff | `git diff --check` | Pasó. |
| Wheel | `python -m pip wheel --no-deps --no-build-isolation --wheel-dir <directorio-temporal> .` | Construido como `irma_magic-0.1.0a1-py3-none-any.whl`. SHA-256: `d190648a464c76ebae3a3f472ca4580710eb675ae96cdffcde68c78cb75eb0ce`. |
| Source distribution | `setuptools.build_meta.build_sdist(<directorio-temporal>)` | Construido como `irma_magic-0.1.0a1.tar.gz`. SHA-256: `a2a7bbc6f12ae79c6740287a8855adb0da012613b6ef10801dcf15ac6ea6cc76`. El sdist incluye README y LICENSE. |
| Instalación limpia de wheel | Entorno virtual temporal; `pip install --no-deps <wheel>` | Pasó desde fuera del checkout. Metadatos: versión `0.1.0a1`, MIT, sin `Requires-Dist`. |
| CLI instalada e imports | Desde un directorio externo: `irmagic --help`, `irmagic {bulker,renamer,flu} --help`, imports de los módulos del paquete | Pasó. Los tres comandos aparecen en ayuda; `irmagic` sin subcomando termina con estado 2. |
| Backend CDC-IRMA real | No disponible/ejecutado | No ejecutado; la suite simula el subprocess. |
| Matriz CI remota en `e0fbd1d` | GitHub Actions, Ubuntu 26.04 | 3.10–3.13 pasaron; 3.8 y 3.9 fallaron en `setup-python` antes de los tests porque no están disponibles para esa imagen. |
| Matriz CI actual (Python 3.12–3.14) | Aún no ejecutada | Pendiente de push del rango actualizado. |
| Python 3.12 y 3.14 local | Solo Python 3.13.5 instalado en el entorno de trabajo | No ejecutado localmente. |
| Instalación editable | No ejecutada en H4 | No verificada. |

Entorno de build local: pip 25.1 y setuptools 78.1.1. El build del sdist
terminó correctamente, aunque setuptools emitió una advertencia deprecando la
tabla `project.license`; se mantuvo el formato compatible con el mínimo
existente `setuptools>=61`, sin elevar ese requisito en este hito.

## Nombre de distribución

El endpoint público de PyPI
[`/pypi/irma-magic/json`](https://pypi.org/pypi/irma-magic/json) devolvió HTTP
404 el 13 de noviembre de 2026. Esto indica que no había un proyecto publicado
con ese nombre en el momento de la consulta. No garantiza que PyPI permita el
registro: puede reservar nombres no publicados o rechazar similitudes, y la
disponibilidad puede cambiar. PyPI normaliza separadores y aplica controles de
similitud según su [política de nombres](https://docs.pypi.org/project-management/choosing-a-name/).
Repetir la comprobación inmediatamente antes de publicar.

## Riesgos y compatibilidad

1. **Bloqueante para GO — CI pendiente:** la matriz previa pasó en Python 3.12
   y 3.13. Los jobs de 3.8 y 3.9 fallaron durante setup; el mantenedor elevó el
   mínimo a 3.12 y la matriz se actualizó a 3.12–3.14. Falta ejecutar esa
   matriz actualizada en GitHub.
2. **Limitación funcional:** no se probó con una instalación real de CDC-IRMA.
   El backend y las entradas se simularon. Una smoke test real sigue siendo
   opcional según el plan, pero no se hace afirmación de compatibilidad real.
3. **Aviso de empaquetado:** setuptools 78.1.1 depreca la tabla TOML usada para
   adjuntar `LICENSE`. El build actual funciona; actualizar la sintaxis puede
   requerir subir el mínimo de setuptools y debe revisarse como cambio
   explícito.
4. **API modificada en H3:** `summary_to_df()` y `bulk_df_summarize()` fueron
   reemplazados por escritores CSV; pandas ya no es dependencia. El cambio se
   documentó en H3.

No se identificaron bloqueos de sobrescritura, pérdida de FASTQ/FASTA o
dependencias de runtime pendientes en las pruebas realizadas. No se afirma
validación biológica o clínica.

## Checklist de publicación pendiente

- Esperar workflow verde en Python 3.12–3.14.
- Repetir la consulta de disponibilidad y similitud del nombre en PyPI.
- Revisar cuenta/propietarios de PyPI y generar artefactos finales desde el
  commit aprobado.
- Confirmar que la advertencia de licencia del backend es aceptable o actualizar
  explícitamente el requisito/sintaxis de build.
- Revisión humana final y autorización explícita antes de merge, tag
  `0.1.0a1` o publicación.
