# H2 — Corrección de modelos de influenza y operaciones FASTA

**Rama propuesta:** `codex/influenza-fasta` (desde `develop` con H1 integrado).  
**Dependencia:** H1 revisado.  
**Prioridad:** bloqueante para publicar utilidades de influenza.

## Objetivo

Asegurar que parsear, agrupar, resumir y exportar segmentos de influenza no genere excepciones inesperadas, pérdida silenciosa ni mezclas de muestras.

## Paquete de cambios

### 1. `FluGenome` y validación de datos

- Corregir la referencia a `self.A_TYPE` de `_get_subtype()` si sigue presente.
- Rechazar o representar explícitamente colecciones vacías; no usar `[0]` sobre conjuntos vacíos.
- Validar unicidad de ID y tipo A/B; comprobar segmentos duplicados antes de construir dicts que los sobrescriben.
- Definir un comportamiento explícito para HA/NA ausentes o sin subtipo; no producir `IndexError` ni inventar información.
- No inferir subtipos sin evidencia y no modificar secuencias originales.

### 2. Parseo de IDs de segmento

Revisar `FluSegment.parse_id()` y la expresión regular: exigir concordancia completa con un esquema documentado; conservar identificadores con `_`, validar tipo A/B y segmento admitido, y rechazar sufijos extraños. Comprobar específicamente la representación de segmento M: la constante actual usa `MP`; no cambiarla sin contrastar IDs reales de IRMA y compatibilidad.

### 3. Operaciones sobre colecciones

- Corregir `FluGenomeCollection.to_segment_dict()` donde se pasa un `FluSegment` individual a `extend(value)`.
- Verificar contrato de `Collection.append/extend` y sus llamadores, sin añadir jerarquías abstractas por sistema.
- Garantizar agregación correcta tanto por muestra (`samples`) como por segmento (`segments`).
- Evitar pérdida de segmentos al indexar y asegurar un orden determinista de exportación.

**Nota:** la llamada `return_collection.append(flu_genome)` en `return_genomes()` no constituye por sí sola un defecto: su retorno no se utiliza y luego se devuelve la colección. No «arreglarla» por una lectura errónea del análisis anterior.

### 4. Lectura y escritura FASTA

- Capturar FASTA vacío y IDs inválidos con errores informativos.
- Verificar FASTA monosecuencia/multisecuencia según contrato de cada operación.
- Validar rutas, crear directorios de forma segura y detectar colisiones/sobrescrituras.
- Conservar IDs de secuencia y contenido de nucleótidos durante la reorganización.
- Corregir parámetros de CLI `--mode` y `--out_dir` si el análisis revela valores `None` no gestionados.

## Pruebas obligatorias

- Influenza A H1N1/H3N2 e influenza B con IDs sintéticos compatibles.
- HA o NA ausentes; subtipo desconocido.
- FASTA vacío, mal formado, con múltiples registros y IDs con guiones bajos.
- Duplicado del mismo segmento en una muestra; mezcla de tipos o IDs.
- Agregación en ambos modos; conteo de registros y contenido exacto en salidas.
- Exportación a directorio nuevo y existente; nombres colisionantes.
- Idempotencia razonable de parseo → serialización para los formatos admitidos.

## Criterios de aceptación

- Ninguna muestra ni segmento se pierde o sustituye sin error.
- Ningún subtipo se infiere mediante datos insuficientes.
- Los dos modos producen archivos FASTA correctos y deterministas.
- No introducir dependencias ni conceptos biológicos nuevos sin aprobación.

## Entrega y stop

PR enfocado, fixtures sintéticos, pruebas y muestras de archivos esperados. Informar límites de formatos admitidos. **Detenerse:** esperar autorización de H3.
