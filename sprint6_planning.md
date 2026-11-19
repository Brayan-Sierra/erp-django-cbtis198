# Sprint 6 Planning — ERP Django
## Semanas W19–W21 · Espiral 7: Dashboard y Reportes

**Sprint Goal:**
Al finalizar el Sprint 6, el ERP mostrará un dashboard con 5 KPIs,
3 gráficas interactivas, exportación de reportes y filtros
parametrizables, optimizado con caché Redis.

## HUs seleccionadas

| ID | Historia | Puntos | Semana |
|---|---|---|---|
| HU-E7-01 | Como gerente, quiero ver 5 KPIs clave del negocio | 3 | W19 |
| HU-E7-02 | Como gerente, quiero ver ventas de los últimos 7 días en gráfica | 3 | W19 |
| HU-E7-03 | Como gerente, quiero ver el top 5 de productos más vendidos | 2 | W19 |
| HU-E7-04 | Como admin, quiero exportar reportes filtrados por fecha | 3 | W20 |
| HU-E7-05 | Como admin, quiero filtrar reportes por producto y cliente | 2 | W20 |
| HU-E7-06 | Como admin, quiero ver histórico de cambios de precio | 3 | W21 |
| HU-E7-07 | Como dev, quiero que el dashboard cargue en menos de 1 segundo | 2 | W19 |

**Total Sprint 6:** 18 puntos

## DoD — Sprint 6
- GET /reportes/ con login → 5 KPIs visibles
- 3 gráficas Chart.js renderizadas con datos reales
- Segunda carga del dashboard < 100ms (caché Redis activo)
- Exportación de reportes filtrados a Excel/PDF (W20)
- Histórico de precios visible con django-simple-history (W21)
- python manage.py test → ≥ 179 tests OK

## Sprint Backlog — actualización W19

| Tarea | Estado |
|---|---|
| CACHES con Redis (DB separada) | ✅ W19 |
| _calcular_kpis(): 5 KPIs + 3 datasets | ✅ W19 |
| DashboardView con cache.get_or_set() | ✅ W19 |
| Template dashboard.html con 3 gráficas Chart.js | ✅ W19 |
| reportes/urls.py actualizado | ✅ W19 |
| 9 tests de dashboard y caché | ✅ W19 |
| Exportación reportes filtrados Excel/PDF | ⏳ W20 |
| django-filter en reportes | ⏳ W20 |
| Histórico de precios (simple-history) | ⏳ W21 |

## Sprint Backlog — actualización W20

| Tarea | Estado |
|---|---|
| Dashboard + KPIs + Chart.js + caché | ✅ W19 |
| reportes/filters.py: VentaReporteFilter | ✅ W20 |
| reportes/models.py: ExportacionReporte + migración 0001 | ✅ W20 |
| ReporteVentasView filtrable | ✅ W20 |
| reportes/exports.py: funciones reutilizables Excel/PDF | ✅ W20 |
| Exportación adaptativa (síncrona/asíncrona) | ✅ W20 |
| reportes/tasks.py: generar_exportacion_async | ✅ W20 |
| Correo con link de descarga | ✅ W20 |
| 8 tests de reportes y exportación | ✅ W20 |
| Histórico de precios (simple-history) | ⏳ W21 |
| Sprint 6 Review + Retrospectiva + Hito M7 | ⏳ W21 |