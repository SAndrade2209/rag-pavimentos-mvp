# rag-pavimentos-mvp

## Objetivo

MVP de una aplicación RAG (generación aumentada por recuperación) que responde preguntas en lenguaje natural sobre datos tabulares de pavimentos. Los datos incluyen los campos:

- Sección
- Coordenadas
- PCI (Pavement Condition Index)
- Año

## Alcance

### Incluido en el MVP

- Preguntas y respuestas sobre los datos tabulares de pavimentos (sección, coordenadas, PCI, año).

### Fuera del MVP

- Documentos PDF.
- Mapa.
- Especificaciones.

## Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| `docs/casos-de-uso/` | Los 3 o 4 casos de uso principales del MVP, orientados al negocio. |
| `docs/arquitectura/` | Documentación de arquitectura. `atributos-calidad.md` contiene los atributos de calidad priorizados. |
| `docs/arquitectura/c4/` | Diagramas del modelo C4 como código (PlantUML con la librería C4-PlantUML): C1 contexto, C2 contenedores y C3 componentes. |
| `docs/arquitectura/adr/` | Registros de decisiones de arquitectura (ADR). `0000-plantilla.md` es la plantilla; cada ADR se nombra `YYYY-MM-DD-titulo-corto.md`. |
| `docs/estimaciones/` | Estimaciones del MVP (esfuerzo, plazo y costo). |
| `demo/` | Código y material de la demostración del MVP. |
