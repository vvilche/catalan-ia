# Informes y memorias de cálculo — el patrón de referencia

Fuente: proyecto privado de automatización de ingeniería de estructuras y fundaciones de
equipos de patio. Mandante omitido a propósito en este documento público. El detalle completo
vive en el repo privado del proyecto.

Este documento **no** es una skill aparte: es el criterio que CatalanIA usa cuando tiene que
emitir un entregable técnico. La skill que lo implementa es `generating-technical-report`
(nombre interno: `informe-tecnico`), con `documento-docx-editable`,
`librerias-ingenieria-python` y `carta-gantt-msproject` como apoyo.

## Qué hace el proyecto de referencia, en una frase

De un archivo de entrada por equipo (TC, TP, DDCC, interruptor) genera la memoria de cálculo de
la estructura y la fundación, y el contenido de las láminas que Revit convierte en planos. Todo
automático: de la entrada al PDF y al DWG, sin intervención manual en el medio.

## Por qué este patrón importa para venta

1. **Es una muestra de capacidad, no un informe suelto.** Cuando una cuenta pregunta "¿pueden
   automatizar esto?", la respuesta no es una promesa: es un proyecto con motor de cálculo, casos
   patrón congelados y salida verificada.
2. **Tiene control de calidad medible.** Los casos patrón guardan casos congelados para verificar
   que el cálculo no cambió. Es la misma idea de la regla 5: verificar contra casos conocidos,
   no contra el número agregado.
3. **El estándar gráfico está escrito.** Tipografía, portada con control de revisiones
   (Elaboró, Revisó, Aprobó), encabezado de tres casillas. Un entregable que sale del agente
   tiene que verse como uno de CONECTA, no como el default de Word.

## La estructura del entregable (lo que CatalanIA debe replicar)

```
[PORTADA]
  Logo · título · proyecto · cliente · N° de informe · Revisión · fecha
  Preparado por / Revisado por / Aprobado por

[CONTROL DE REVISIONES]
  Rev. | Fecha | Descripción | Elaborado | Revisado | Aprobado

[TABLA DE CONTENIDOS]

1. Resumen ejecutivo            (máx. 1 página, legible por gerencia)
2. Introducción                 (antecedentes, objetivo, alcance)
3. Normativa y referencias      (citadas en texto como [COD-01])
4. Descripción del sistema
5. Desarrollo técnico           (cálculos, análisis, hallazgos)
6. Resultados y discusión
7. Conclusiones
8. Recomendaciones
9. Referencias
10. Anexos
```

Nomenclatura de documento: `CON-[ÁREA]-[AÑO]-[NNN]-[TIPO]`.
Ejemplos: `CON-ING-2025-001-MEM` (memoria de cálculo), `CON-CEN-2025-001-INF` (informe al CEN).
Revisiones: Rev. 0 / A = borrador; Rev. 1 = primera emisión oficial.

## Reglas duras al emitir un informe (heredan las del SOUL)

- **Cada afirmación técnica cita su fuente o su referencia normativa.** Sin fuente no se afirma
  (regla 6 del SOUL). En el texto: "según [COD-01], la corriente de cortocircuito...".
- **Unidades siempre.** kV, kA, MW, %, mm. Nunca "valores altos": "superiores a 25 kA".
- **Una cifra, un solo origen.** Si un número aparece en el resumen y en el capítulo 5, sale del
  mismo archivo de datos. Dos escrituras = dos verdades que se desfasan.
- **El informe es un entregable técnico, no marketing.** El resumen ejecutivo dice qué se
  concluyó, no cuánto conviene comprar.
- **Trazabilidad normativa requisito por requisito**, con la norma que lo respalda. Para la
  línea NORMATIVO, la matriz se arma contra NTSyCS, los ATS del CEN y las resoluciones SEC
  aplicables. El proyecto de referencia tiene la suya como archivo versionado del repo: ese es
  el modelo, no una tabla suelta en un informe.

## Herramientas

| Necesidad | Skill / herramienta |
|---|---|
| Estructura, numeración y checklist del informe | `generating-technical-report` |
| .docx editable para firma o para terceros | `documento-docx-editable` |
| Ecuaciones y cálculos de acero | `librerias-ingenieria-python` |
| Carta Gantt formato MS Project | `carta-gantt-msproject` |
| PDF final, unión, seguridad | `pdf` |
| Datos y tablas del informe | `xlsx` |

## Qué NO se copia a un repo público

El proyecto de referencia es privado y contiene material del mandante: nombre del proyecto,
datos de equipos, planos. Al repo público solo va **este criterio**, sin el nombre del mandante,
sin planos y sin datos de equipo. El detalle con nombre propio queda en el repo privado.
