# H0 — Auditoría del estado real y pruebas de regresión

**Rama propuesta:** `codex/audit-regression` (desde `develop`).  
**Tipo:** diagnóstico + tests; no refactorización funcional.  
**Dependencias:** ninguna.

## Objetivo

Verificar el estado de la rama `develop` y convertir los hallazgos preliminares en casos reproducibles antes de modificar el código. El commit de referencia es `0f5dfb2` de `main`, no necesariamente el estado actual.

## Alcance

Examinar `magic_irma/files.py`, `bulk.py`, `flu_tools.py`, `renamer.py`, `constants.py`, `scripts/irmagic.py`, y cualquier estructura equivalente actual. Revisar además `AGENTS.md`, configuración, dependencias, documentación, scripts, tests y CI disponibles.

### Hipótesis a comprobar

1. `_pair_files()` empareja por posición usando `zip`, pudiendo asociar muestras equivocadas y perder huérfanos.
2. `FastqCollection.append_files()` invoca `_transform_file()` dos veces y descarta archivos inválidos imprimiendo mensajes.
3. `FastqFile` admite cualquier extensión `.gz`; la clase puede quedar sin algunos atributos esperados (`full_name`).
4. `IrmaBulk._build_cmd()` elimina la ruta de origen al usar `file.name`.
5. `IrmaBulk.run()` invoca `subprocess.run()` sin comprobar el código de retorno.
6. `FluGenome._get_subtype()` emplea `self.A_TYPE` no declarado en esa clase.
7. `FluGenomeCollection.to_segment_dict()` pasa un objeto `FluSegment` a `extend()` en vez de un iterable/varargs válido.
8. `FluSegment.read_file()` no controla FASTA vacío; `FluGenome` no controla una colección vacía; subtipos ausentes pueden fallar.
9. `IrmaDirRenamer` admite `out_dir` pero los destinos construidos por `IrmaRenamer` no lo respetan; posibilidad de sobrescribir.
10. `scripts/irmagic.py` declara `main()` sin invocación directa visible; importaciones absolutas internas afectan empaquetado.
11. README, licencia, `pyproject.toml`, tests o workflows no estaban verificables en las rutas consultadas. **Buscar en todo el árbol** antes de concluir ausencia.

**Corrección de revisión anterior:** `FluSegmentCollection.return_genomes()` *sí* devuelve `return_collection` después de ejecutar `append`; no debe registrarse como fallo que use el retorno de `append()` sin nueva evidencia. En cambio, sí revisar el contrato general de colecciones.

## Trabajo solicitado

- Registrar SHA y rama examinados.
- Crear inventario de CLI e interfaces de importación.
- Elaborar matriz de cada hipótesis: `confirmado / descartado / no reproducido`, evidencia concreta (archivo y líneas), severidad, alcance y test propuesto.
- Crear una suite mínima de regresión con datos sintéticos; usar `unittest` si no hay framework de pruebas autorizado. No instalar pytest por iniciativa propia.
- Para IRMA externo, usar mocks o un ejecutable simulado; no depender de bases de datos o muestras reales.
- Ejecutar los tests base y preservar resultados de fallo esperados (no falsear estado verde).

## Matriz de casos mínimos

| Caso | Comportamiento a demostrar |
| --- | --- |
| R1/R2 desordenados | Identidad de pareja coherente |
| R1 o R2 ausente | El caso no desaparece sin aviso |
| Duplicados y nombres ambiguos | Se detectan |
| FASTQ `.fastq`, `.fq`, `.fastq.gz`, `.fq.gz` | Extensiones tratadas correctamente |
| Archivo `.txt.gz` | No se acepta como FASTQ |
| FASTQ en ruta externa / con espacios | Se preserva la ruta |
| IRMA devuelve código no cero o no existe | El error no se comunica como éxito |
| FASTA vacío / IDs erróneos / duplicados | Se identifican fallos de parseo |
| Agrupación por muestra y por segmento | No se pierden ni mezclan registros |
| Directorio de salida y colisiones | Se observa el comportamiento real |

## Criterios de aceptación

- Matriz con evidencia enlazable a código actual y sin atribuciones basadas solo en el análisis previo.
- Tests reproducibles, identificados por intención; fallos previos registrados con claridad.
- Ninguna instalación ni dependencia no autorizada.
- Sin arreglos funcionales de alcance amplio realizados en H0.

## Entrega y stop

Entregar `H0-report.md` o resumen de PR con inventario, matriz, comandos/tests y riesgos. **Detenerse:** esperar aprobación de H1.
