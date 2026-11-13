# H3 — CLI, renombrado de archivos e instalación

**Rama propuesta:** `codex/cli-packaging` (desde `develop` actualizado).  
**Dependencia:** H2 revisado.  
**Prioridad:** bloqueante para distribución.

## Objetivo

Tener una CLI `irmagic` funcional y una distribución Python candidata `irma-magic`, conservando utilidades de renombrado y evitando sobrescrituras accidentales.

## Convenciones acordadas

- Nombre de proyecto: **IRMagic**.
- Distribución: **`irma-magic`** (verificar disponibilidad y normalización de nombres PyPI antes de liberar).
- Módulo Python objetivo: **`irma_magic`**.
- Comando console script: **`irmagic`**.
- Repo GitHub: puede permanecer `magic_irma`.

El nombre de distribución no determina el del módulo ni el ejecutable; configurar cada uno explícitamente.

## Paquete de cambios

### 1. CLI

- Corregir el punto de entrada de `scripts/irmagic.py` si no se llama `main()` cuando se ejecuta directamente.
- Definir un `console_scripts`/`[project.scripts]` que invoque una función `main` verificable.
- Mantener los argumentos actuales de `bulker` o documentar cambios inevitables.
- Mostrar ayuda clara, errores de argumentos y códigos de salida coherentes.
- Evitar que lanzar el comando sin subcomando termine aparentemente bien sin mostrar ayuda.
- No incorporar subcomandos nuevos que no tengan un contrato existente aprobado.

### 2. Renombrado

Revisar `IrmaRenamer`, `FastaRenamer` e `IrmaDirRenamer`:

- Respetar de verdad `out_dir` en los destinos.
- Utilizar rutas completas y crear directorios según contrato.
- Evitar sobrescribir archivos existentes o que distintas entradas colisionen; fallo explícito por defecto.
- No modificar los archivos fuente salvo operación explícita y documentada; preferir copia/transformación segura.
- En FASTA, preservar todas las secuencias, asegurar IDs resultantes inequívocos y no alterar nucleótidos.
- Revisar la regla `if record.id in name` por riesgo de coincidencias parciales.
- Comprobar el tratamiento de extensiones, incluyendo nombres con varios puntos.

### 3. Empaquetado

- Crear/actualizar `pyproject.toml` con metadatos mínimos, versión candidata y entrada `irmagic`.
- Declarar dependencias que el proyecto ya usa (Biopython, pandas, si siguen siendo necesarias), **sin añadir ni actualizar dependencias sin autorización**.
- Resolver importaciones del estilo `import constants` y `from files import ...` para que funcionen desde instalación limpia.
- Renombrar `magic_irma` → `irma_magic` con cambios enfocados, comprobando imports y scripts. Si la compatibilidad externa está en uso, proponer estrategia antes de romperla.
- Especificar que CDC-IRMA es dependencia **externa**; no pretender instalarlo con pip sin un mecanismo real.
- Utilizar herramientas de construcción estándar, pero solicitar autorización si hay que incorporar dependencias de build no presentes.

## Tests obligatorios

- CLI `--help` y `bulker --help`.
- Invocación del entrypoint `irmagic` mediante instalación local limpia.
- Instalación editable y, si existen herramientas autorizadas, build e instalación de wheel en entorno temporal.
- Imports desde un directorio ajeno al checkout del repositorio.
- Errores de argumentos y código de salida no cero.
- Renombrado: salida alternativa, colisiones, origen intacto, múltiples FASTA y nombres ambiguos.

## Criterios de aceptación

- Un usuario puede instalar el proyecto y ejecutar `irmagic --help` sin alterar PYTHONPATH manualmente.
- `irma_magic` es importable desde otra ubicación.
- No hay sobrescrituras silenciosas ni pérdida de rutas.
- La integración con IRMA se documenta como requisito externo real.
- Ningún release enviado a PyPI.

## Entrega y stop

Proporcionar comandos de instalación probados, salida de `--help`, tests y listado de cambios potencialmente incompatibles. **Detenerse:** esperar autorización de H4.
