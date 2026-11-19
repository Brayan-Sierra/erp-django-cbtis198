# Ficha de Sistematización — Espiral 7
## ERP Django · Espiral E7: Dashboard y Reportes

| Campo | Contenido |
|---|---|
| **Número de espiral** | 7 |
| **Nombre del ciclo** | Dashboard y Reportes |
| **Semanas** | W19 – W21 |
| **Fecha de inicio** | ___/___/_____ |
| **Fecha de cierre** | ___/___/_____ |
| **Responsable** | [Nombre del estudiante] |
| **Asesor** | MC. Román Fernando López González |

## 1. Objetivo del ciclo
Implementar un módulo de inteligencia de negocio con dashboard de KPIs
cacheados, reportes filtrables con exportación adaptativa, e histórico
completo de cambios de precio.

## 2. Tareas realizadas

| # | Tarea | Estado | Semana |
|---|---|---|---|
| 1 | CACHES con Redis (DB separada del broker) | ✅ | W19 |
| 2 | _calcular_kpis(): 5 KPIs + 3 datasets | ✅ | W19 |
| 3 | DashboardView con cache.get_or_set() | ✅ | W19 |
| 4 | Template dashboard.html + 3 gráficas Chart.js | ✅ | W19 |
| 5 | reportes/filters.py: VentaReporteFilter | ✅ | W20 |
| 6 | reportes/models.py: ExportacionReporte | ✅ | W20 |
| 7 | ReporteVentasView + exportación síncrona | ✅ | W20 |
| 8 | reportes/exports.py (funciones reutilizables) | ✅ | W20 |
| 9 | Exportación asíncrona > UMBRAL_ASYNC | ✅ | W20 |
| 10 | django-simple-history instalado | ✅ | W21 |
| 11 | HistoricalRecords en Producto, Venta, Pedido | ✅ | W21 |
| 12 | HistoricoProductoView + template timeline | ✅ | W21 |
| 13 | Migraciones históricas aplicadas | ✅ | W21 |

## 3. Evidencias
- Dashboard: /reportes/ → 5 KPIs + 3 gráficas
- Caché: segunda carga < 100ms (verificar con DevTools)
- Exportación: /reportes/exportar/?formato=excel → descarga inmediata
- Histórico: /productos/<id>/historico/ → timeline de cambios
- Admin: botón "History" en cada producto
- Tests: Ran 195 tests → OK

## 4. Criterios de aceptación

| Criterio | Estado |
|---|---|
| GET /reportes/ → 5 KPIs cacheados | ✅ |
| 3 gráficas Chart.js renderizadas | ✅ |
| Reporte filtrado por fecha/cliente/producto | ✅ |
| Exportación Excel síncrona | ✅ |
| Exportación asíncrona > 1000 filas | ✅ |
| Histórico de precios en timeline | ✅ |
| history_type '+' en creación, '~' en edición | ✅ |
| diff_against() detecta campo precio | ✅ |
| 195 tests OK | ✅ |

## 5. Problemas encontrados
(completar durante la sesión)

## 6. Lecciones aprendidas
1.
2.
3.

## 7. Tiempo total invertido

| Categoría | Horas |
|---|---|
| Diseño | |
| Implementación | |
| Pruebas | |
| Documentación | |
| **Total Espiral 7** | |