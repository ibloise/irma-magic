# H1 — Integridad de FASTQ y ejecución segura de CDC-IRMA

**Rama propuesta:** `codex/fastq-execution` (desde `develop` actualizado con H0).  
**Dependencia:** H0 aprobado.  
**Prioridad:** bloqueante.

## Objetivo

Impedir emparejamientos de muestras incorrectos, pérdidas silenciosas de entradas y falsos éxitos al ejecutar IRMA. No añadir orquestadores ni paralelización.

## Paquete de cambios

### 1. Emparejar por identidad, nunca por posición

Reemplazar el `zip(first_files, second_files)` de `_pair_files()` si continúa presente. Deducir una clave de muestra a partir de los patrones `_R1` y `_R2` (configurables) siguiendo una regla documentada. Construir un índice de R1/R2 por clave y comprobar:

- exactamente un R1 y un R2 por muestra en modo paired;
- detección de huérfanos, duplicados y coincidencias de patrón ambiguas;
- orden de entrada irrelevante y salida determinista;
- nombres con guiones bajos y rutas con espacios;
- no perder entradas por `zip`, filtrado o mensajes impresos.

**No** presupongas que se admiten todos los nombres Illumina imaginables. Delimita formatos soportados y casos rechazados; si hay una ambigüedad real que afecte compatibilidad, presenta opciones antes de cambiar semántica.

### 2. Normalizar la representación de archivo

- Transformar cada elemento una sola vez en `FastqCollection.append_files()`.
- Aceptar solo `.fastq`, `.fq`, `.fastq.gz`, `.fq.gz` (salvo evidencia y decisión explícita para otros formatos).
- Conservar coherentemente ruta, nombre base, extensión y estado de compresión.
- Corregir atributos no inicializados en `FastqFile` y evitar lógica duplicada entre setters.
- Los inválidos deben producir una excepción descriptiva; no descartarse silenciosamente.

### 3. Construir correctamente los comandos

- En `IrmaBulk._build_cmd()`, pasar rutas completas apropiadas, no solo `file.name`, salvo que se controle explícitamente `cwd`.
- Mantener `subprocess.run` con lista de argumentos y `shell=False` implícito.
- Respetar `irma_cmd` existente y preservar compatibilidad de la interfaz cuando sea posible.
- Validar identificador/destino y rechazar colisiones de nombres de salida.
- No inventar opciones de CDC-IRMA: verificar la sintaxis del ejecutable en documentación o evidencias del proyecto.

### 4. Gestionar las ejecuciones fallidas

- Comprobar fallo del proceso (`check=True` o control explícito del retorno).
- Traducir errores relevantes a mensajes utilizables: ejecutable ausente, permisos, fallo IRMA, entrada inválida.
- Política inicial: **fail-fast**; documentar cambio respecto del comportamiento anterior.
- Informar código de salida adecuado desde CLI una vez esté conectada.
- Registrar muestra/comando/estado con `logging` estándar si aporta trazabilidad; evitar registrar datos personales o sensibles.

## Tests obligatorios

1. Parejas correctas, incluso cuando las listas vienen desordenadas.
2. Huérfanos R1/R2, duplicados y ambigüedad.
3. Distintas extensiones válidas e inválidas.
4. Nombres de muestra con `_`, rutas relativas y absolutas, espacios en nombres.
5. Muestra simple single-end y varias muestras.
6. Comandos IRMA construidos con argumentos exactos y rutas correctas.
7. Mock de retorno 0, retorno no cero, `FileNotFoundError` y `PermissionError`.
8. Política fail-fast en lote y ausencia de sobrescritura silenciosa.

No requerir una instalación real de IRMA para las pruebas unitarias. Si se dispone de una, cualquier prueba real debe ser opt-in y con fixtures sintéticos.

## Criterios de aceptación

- Ningún emparejamiento erróneo o descarte silencioso.
- No hay pérdida de rutas; ejecuciones fallidas elevan error y detienen el lote según política.
- Tests de H0 relevantes pasan tras los cambios.
- Modificaciones acotadas; sin nuevas dependencias ni cambios de arquitectura superfluos.

## Entrega y stop

Informe con matriz antes/después, tests ejecutados, posibles incompatibilidades y PR hacia `develop` sin merge automático. **Detenerse:** esperar autorización de H2.
