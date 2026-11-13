# H4 — Validación final, documentación y decisión de publicación

**Rama propuesta:** `codex/release-readiness` (desde `develop` actualizado).  
**Dependencia:** H3 revisado.  
**Objetivo:** entregar evidencia para que el mantenedor decida si se publica `0.1.0a1`.

## Alcance

### 1. Calidad automatizada

- Ejecutar todos los tests unitarios y de integración disponibles.
- Añadir CI mínima que ejecute tests sin requerir IRMA ni datos biológicos reales.
- Proponer, pero no introducir automáticamente, herramientas de lint/type-check no autorizadas.
- Registrar versiones de Python y dependencias compatibles verificadas.
- Distinguir claramente pruebas con IRMA simulado de pruebas con el ejecutable real.

### 2. Validación de instalación y funcionalidad

- Probar instalación en entorno limpio y ejecución de `irmagic --help`.
- Probar lote sintético single/paired con backend IRMA simulado y entradas mal formadas.
- Probar lectura, agrupación y escritura de FASTA de influenza con fixtures verificables.
- Si hay ejecutable IRMA real disponible y autorizado, añadir smoke test opcional; no bloquear el CI base por requerirlo.
- Revisar trazabilidad: entrada → muestra → comando → salida → error/estado.
- Ejecutar revisión de archivos que podrían contener secretos, rutas internas o datos sensibles, incluidos fixtures y logs.

### 3. Documentación mínima

Crear o actualizar, según exista:

- `README.md`: problema resuelto, alcance y limitaciones, instalación, dependencia externa CDC-IRMA, ejemplos CLI reproducibles, formatos de entrada, salidas y errores.
- `LICENSE`: **selección explícita por el mantenedor**; no elegirla por cuenta propia. Sin licencia, no presentar el repositorio como reutilizable bajo una licencia open source.
- `CHANGELOG.md`: cambios relevantes para primera versión candidata.
- Documentación de desarrollo: ejecutar tests, instalar editable y contribuir mediante `develop`/`codex/<feat>`.
- Nota sobre qué se ha probado con IRMA real, con mocks y qué queda sin verificar.

No crear un corpus extenso de ADRs, políticas o guías por un proyecto pequeño.

### 4. Validación de nombre y distribución

- Comprobar disponibilidad efectiva del nombre `irma-magic` en PyPI en el momento de publicar y conflictos de normalización.
- Verificar metadatos, wheel/sdist y CLI instalados.
- Preparar checklist de publicación; **no subir** a PyPI, crear tag ni fusionar a `main` sin aprobación.
- Si el nombre está ocupado, notificar y solicitar decisión; no cambiarlo unilateralmente.

## Criterios de aceptación

- Tests automatizados verdes en las plataformas/versiones declaradas.
- CLI instalable y funcional desde un entorno limpio.
- No hay bloqueos P0/P1 sin resolver; cualquier excepción documentada requiere aceptación explícita.
- Existe documentación suficiente para que otra persona ejecute un ejemplo sin consultar al autor.
- Dependencias y versiones conocidas, ausencia de secretos o datos reales.
- Reporte claro de validación funcional y límites de reproducibilidad.

## Informe de cierre solicitado

Entregar un **release-readiness report** con:

1. Commit SHA, rama y PR.
2. Lista de cambios y evidencias por requisito.
3. Matriz de pruebas: prueba, entorno, comando, resultado, ejecutado/no ejecutado.
4. Riesgos restantes ordenados por severidad.
5. Compatibilidades y posibles breaking changes.
6. Estado del empaquetado, licencia y disponibilidad de nombre.
7. Recomendación: `GO` / `GO con limitaciones` / `NO-GO`, con justificación.

**Stop final:** el mantenedor decide merge `develop` → `main`, tag `0.1.0a1` y publicación. Ninguna de esas acciones se ejecuta por defecto.
