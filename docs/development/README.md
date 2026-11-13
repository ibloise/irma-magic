# IRMagic — Plan de estabilización previo a publicación

**Estado:** propuesto, pendiente de autorización por hito.  
**Referencia examinada:** `ibloise/magic_irma`, `main`, commit `0f5dfb2be13ffb0804e90fc0581bde381bbf89bf` (revisión estática).  
**Objetivo:** preparar una primera distribución `irma-magic` con CLI `irmagic`, sin ampliar innecesariamente el alcance.

## Cómo usar este paquete

Este directorio es un **plan de trabajo**, no una orden de implementar todos los hitos de una vez. Proporcionar a Codex `AGENTS.md` del repositorio y **solo** el documento del hito autorizado. Trabajar desde `develop` en una rama `codex/<feat>`. Cada hito termina en informe de evidencias y revisión humana; no realizar merge, tag ni publicación sin aprobación explícita.

| Documento | Hito | Resultado esperado | Dependencia |
| --- | --- | --- | --- |
| `H0-auditoria-y-regresion.md` | H0 | Diagnóstico contrastado, pruebas que reproducen fallos | Ninguna |
| `H1-fastq-y-ejecucion.md` | H1 | Emparejamiento seguro y ejecución IRMA con fallos visibles | H0 |
| `H2-influenza-y-fasta.md` | H2 | Parseo, agrupación y salida FASTA fiables | H1 (para la secuencia de integración) |
| `H3-cli-archivos-empaquetado.md` | H3 | CLI instalable, renombrado seguro y paquete preparado | H2 |
| `H4-validacion-release.md` | H4 | Documentación, CI, validación y decisión de release | H3 |

## Reglas generales

- Aplicar el `AGENTS.md` real del repositorio; prevalece en convenciones generales compatibles con este plan.
- **Revisar primero `develop`:** las observaciones están basadas en un commit anterior y pueden haber cambiado. No implementar cambios obsoletos.
- Usar Python estándar y dependencias ya autorizadas; ninguna dependencia nueva, actualización de versión, framework, contenedor o servicio sin aprobación. Si una herramienta de build exige instalar algo, documentarlo y pedir autorización antes.
- No inventar sintaxis, formatos, módulos o garantías de CDC-IRMA. Contrastar con documentación real y ejemplos existentes. Se permiten mocks para tests unitarios.
- No usar material clínico real ni datos sensibles. Tests con fixtures sintéticos.
- Mantener interfaces existentes salvo cambio deliberado documentado. No introducir patrones de diseño por anticipación.
- No silenciar entradas inválidas, errores de procesos ni sobrescrituras. Los cambios de semántica deben explicarse.
- Separar **observaciones confirmadas por lectura del código** de **hipótesis que requieren reproducirse**.
- Salida de cada hito: resumen, rutas modificadas, casos probados, comandos ejecutados, resultados, limitaciones, riesgos y PR hacia `develop` sin fusionar.

## Nomenclatura de publicación prevista

- Marca: **IRMagic**
- Distribución candidata de PyPI: `irma-magic` (**disponibilidad por verificar justo antes de publicar**)
- Comando CLI: `irmagic`
- Módulo Python objetivo: `irma_magic`
- Repositorio: puede seguir siendo `magic_irma`
- Primera versión candidata: `0.1.0a1` (no asignar ni publicar hasta H4).

## Fuera de alcance

Nuevas funciones de IRMA, paralelización, orquestación, UI, contenedores, bases de datos, pipelines genéricos, validación clínica y publicación automática. Estas decisiones requieren propuestas independientes.

## Puertas de control

**H0 → H1:** inventario y reproducción de fallos acordados.  
**H1 → H2:** pruebas de emparejamiento y ejecución aprobadas.  
**H2 → H3:** parseo, agrupación y exportación validados.  
**H3 → H4:** instalación y CLI probadas en entorno limpio.  
**H4 → release:** aprobación humana del informe final, licencia, nombre de distribución, CI y comportamiento de ejecución.
