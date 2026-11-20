# Documentar la arquitectura con el modelo C4 y diagramas como código en PlantUML

- Fecha: 2026-11-20
- Estado: Aceptado

## Contexto

El MVP necesita una documentación de arquitectura que:

- Describa el sistema a varios niveles de detalle: su entorno (usuarios y sistemas externos), sus contenedores (aplicaciones, servicios y almacenes de datos) y sus componentes internos.
- Use una notación común para todo el equipo.
- Viva en el mismo repositorio que el código, se versione con Git y se revise en los mismos pull requests.

Los diagramas hechos en herramientas de dibujo se guardan como archivos binarios o exportados. Sus cambios no se pueden revisar línea por línea y tienden a quedar desactualizados respecto del código.

## Decisión

1. Documentar la arquitectura con el modelo C4 de Simon Brown (https://c4model.com) en tres niveles:
   - C1 Contexto: `docs/arquitectura/c4/c1-contexto.puml`
   - C2 Contenedores: `docs/arquitectura/c4/c2-contenedores.puml`
   - C3 Componentes: `docs/arquitectura/c4/c3-componentes.puml`
2. No elaborar el nivel 4 (código). En un MVP, los diagramas de clases mantenidos a mano cambian con cada refactorización y su costo de mantenimiento es alto. Si hacen falta, se generan desde el código o el IDE.
3. Escribir los diagramas como código en PlantUML con la librería C4-PlantUML (https://github.com/plantuml-stdlib/C4-PlantUML).

## Atributos que gana

- Mantenibilidad de la documentación: archivos de texto plano con diffs legibles.
- Trazabilidad: el historial de la arquitectura queda en Git junto al código.
- Comprensibilidad: cada nivel se dirige a una audiencia. C1 es legible también para interlocutores no técnicos; C2 y C3 se dirigen al equipo técnico.
- Consistencia: una sola notación para todos los diagramas.

## Atributos que sacrifica

- Control del diseño visual: PlantUML calcula la disposición de los elementos y el ajuste fino es limitado.
- Accesibilidad para personas no técnicas: editar los diagramas requiere conocer la sintaxis de PlantUML y C4-PlantUML.
- Detalle a nivel de código: sin el nivel 4, la correspondencia entre componentes y clases no queda documentada en diagramas.

## Consecuencias

- Para renderizar los diagramas se necesita PlantUML (instalación local, servidor PlantUML o extensión del editor).
- Los archivos incluyen C4-PlantUML desde su URL en GitHub (rama `master`). Renderizar requiere acceso a internet, y un cambio en la librería puede alterar los diagramas. Si se necesita estabilidad, se fija una versión publicada (tag) en la URL del `!include`.
- Todo cambio de arquitectura actualiza el diagrama del nivel que corresponda. Si el cambio implica una decisión, se registra un ADR.
- Los diagramas no se generan desde el código: su vigencia depende de revisarlos en cada pull request que cambie la arquitectura.
