# H1 — Integridad de FASTQ y ejecución IRMA

## Resultado

H1 implementa validación explícita de nombres FASTQ, emparejamiento por identidad y ejecución fail-fast. El trabajo continúa en `codex/audit-regression`, que contiene los commits anteriores de esta cadena. No se ejecutó ni instaló CDC-IRMA.

## Regla de nombres y compatibilidad

- Se aceptan únicamente `.fastq`, `.fq`, `.fastq.gz` y `.fq.gz`, en minúsculas.
- En modo paired, cada nombre base sin extensión debe contener exactamente una vez el marcador R1 o R2 configurado. Se elimina ese marcador literal para obtener el ID de muestra; se admiten guiones bajos y el marcador puede aparecer en cualquier posición del nombre base.
- Un nombre con ambos marcadores, con un marcador repetido o sin marcador es ambiguo/ inválido y produce `ValueError`. Los patrones deben ser distintos y no vacíos.
- La pareja se identifica además por su directorio de origen absoluto. Por tanto, un R1 y un R2 con el mismo ID pero en directorios distintos no se emparejan: se informan como huérfanos. Esta regla evita unir por accidente archivos homónimos de rutas diferentes.
- Se requiere exactamente un R1 y un R2 por clave (directorio, muestra). La salida se ordena determinísticamente por esa clave. IDs de salida duplicados en el lote se rechazan para evitar sobrescrituras.
- En single-end, el ID de salida es el nombre base sin extensión. Se rechazan IDs repetidos, vacíos y nombres de salida `.`/`..` o que contengan separadores de ruta.

## Cambios

- `FastqFile` inicializa nombre, extensión completa, compresión, ruta y ruta completa; las entradas inválidas ya no se convierten en `None` ni se imprimen para luego omitirse.
- `FastqCollection` transforma cada ruta una vez, rechaza listas vacías, huérfanos, duplicados y marcadores ambiguos, y deja intacta la colección si la validación del lote falla.
- `IrmaBulk` conserva rutas completas como argumentos individuales, mantiene la forma posicional de comando que ya construía el proyecto (`irma_cmd`, módulo, archivos y nombre de salida), y rechaza colisiones al agregar ejecuciones.
- La ejecución usa `subprocess.run(..., check=True)`. Un fallo de IRMA, un ejecutable inexistente o permisos insuficientes generan `IrmaExecutionError`; se detiene el lote en el primer error. La CLI muestra el error y devuelve estado 1. Los errores de validación se reportan mediante `argparse` con estado 2.
- Las pruebas de regresión de H0 se actualizaron para verificar el comportamiento corregido en lugar de marcar esos defectos como fallos esperados.

| Caso | Antes | Ahora |
| --- | --- | --- |
| Emparejamiento | R1 y R2 por posición con `zip`; huérfanos desaparecían. | Índice por directorio y clave de muestra; huérfanos, duplicados y nombres ambiguos fallan. |
| FASTQ | Cualquier `.gz`; metadatos incompletos; archivos inválidos impresos y omitidos. | Solo cuatro sufijos admitidos; metadatos completos; inválidos elevan `ValueError`. |
| Comando | Se perdía el directorio al usar `file.name`. | Cada argumento conserva la ruta completa, incluso con espacios. |
| Proceso | Se ignoraba el código de salida. | `check=True`, error utilizable y lote detenido en el primer fallo. |
| Destino | IDs duplicados podían competir por la misma salida. | Colisiones dentro de la colección/lote se rechazan antes de ejecutar. |

## Comprobaciones

Comandos:

```text
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src tests
git diff --check
```

Resultado: **34 tests pasaron**, incluyendo todos los casos H0 relevantes, parser FASTA, pairing y ejecución simulada. `compileall` y `git diff --check` finalizaron correctamente. Los casos de ejecución usan mocks para retornos 0/no cero, `FileNotFoundError` y `PermissionError`; no llaman a un IRMA instalado.

## Evidencia y límites

La sintaxis externa de CDC-IRMA no se verificó contra documentación externa ni un ejecutable disponible. Se preservó solamente la forma posicional observada en la implementación previa de `_build_cmd()`; las pruebas verifican los argumentos construidos, no que una versión concreta de IRMA los acepte.

No se comprueba que cada ruta exista antes de invocar IRMA. Los sufijos y el esquema de nombres se validan localmente; el tratamiento de archivos ausentes queda en manos del proceso IRMA y su código de salida. No se valida el contenido interno FASTQ.

La regla de directorio puede rechazar pares que deliberadamente estén repartidos entre carpetas, y la exigencia de un único marcador rechaza nombres donde el mismo token también forma parte del ID de muestra. Estos casos ambiguos requieren adaptar el patrón o normalizar los nombres antes de ejecutar.

H1 no modifica módulos de CDC-IRMA, no añade dependencias y no afirma validación biológica. La siguiente puerta del plan es revisión de H1 y autorización de H2.
