# Sprint 7 Planning — ERP Django
## Semanas W22–W24 · Espiral 8: Calidad y Entrega

**Sprint Goal:**
Al finalizar el Sprint 7, el ERP tendrá cobertura ≥ 80%, tests
de integración para los flujos críticos, rendimiento optimizado
y documentación completa para la entrega académica final.

## HUs seleccionadas

| ID | Historia | Puntos | Semana |
|---|---|---|---|
| HU-E8-01 | Como dev, quiero cobertura de código ≥ 80% | 5 | W22 |
| HU-E8-02 | Como dev, quiero tests de integración E2E | 5 | W22 |
| HU-E8-03 | Como dev, quiero factories con datos realistas | 3 | W22 |
| HU-E8-04 | Como admin, quiero el N+1 identificado y corregido | 3 | W23 |
| HU-E8-05 | Como admin, quiero django-debug-toolbar en desarrollo | 2 | W23 |
| HU-E8-06 | Como evaluador, quiero documentación técnica completa | 3 | W24 |
| HU-E8-07 | Como evaluador, quiero el sistema desplegado y funcional | 5 | W24 |

**Total Sprint 7:** 26 puntos

## DoD — Sprint 7
- coverage report → TOTAL ≥ 80%
- 3 tests E2E pasan sin errores
- django-debug-toolbar instalado en development
- 0 queries N+1 detectadas en las vistas críticas
- README.md actualizado con instrucciones de instalación
- URL pública en Render funcionando con todos los hitos
- python manage.py test → ≥ 203 tests OK