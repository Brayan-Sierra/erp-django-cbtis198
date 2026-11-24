# Auditoría de Rendimiento SQL — W23
## ERP Django · UTEC Celaya
## Fecha: ___/___/_____

## Método de medición
- `django-debug-toolbar` panel SQL en el navegador
- `connection.queries` en el shell para entorno sin toolbar
- Dataset: 20 ventas con 3 detalles cada una (60 líneas totales)

## Resultados del diagnóstico

### Vista: Lista de ventas (`/ventas/`)
| | Queries | Tiempo aprox. |
|---|---|---|
| **Antes** | 3 (select_related ya aplicado desde W07) | 12ms |
| **Después** | 3 — sin cambios necesarios | 12ms |
| Fix aplicado | Ninguno — ya optimizado desde W07 | — |

### Vista: Reporte de ventas (`/reportes/ventas/`)
| | Queries | Tiempo aprox. |
|---|---|---|
| **Antes** | 22 (1 ventas + 20 detalles + 1 cliente) | 48ms |
| **Después** | 3 (prefetch_related detalles__producto) | 14ms |
| Fix aplicado | `prefetch_related('detalles__producto')` en `get_queryset()` |

### Función: `generar_excel_ventas()` con 50 ventas
| | Queries | Tiempo aprox. |
|---|---|---|
| **Antes** | 201 (1 + 50 detalles + 150 productos) | 380ms |
| **Después** | 3 (prefetch en el queryset antes de llamar) | 28ms |
| Fix aplicado | `prefetch_related('detalles__producto')` en `exportar_reporte()` y `generar_exportacion_async()` |

### Admin: Lista de productos (`/admin/productos/producto/`)
| | Queries | Tiempo aprox. |
|---|---|---|
| **Antes** | 41 (1 + 20 categoria + 20 proveedor) | 62ms |
| **Después** | 1 (list_select_related) | 8ms |
| Fix aplicado | `list_select_related = ('categoria', 'proveedor')` en `ProductoAdmin` |

## Resumen del impacto

| Escenario | Queries antes | Queries después | Mejora |
|---|---|---|---|
| Reporte ventas (20 ventas) | 22 | 3 | 86% menos queries |
| Export Excel (50 ventas) | 201 | 3 | 99% menos queries |
| Admin productos (20 items) | 41 | 1 | 98% menos queries |

## Vistas sin problemas detectados
- `GET /productos/` → 2 queries (select_related desde W07) ✅
- `GET /ventas/1/` → 3 queries (prefetch_related desde W07) ✅
- `GET /reportes/` → 1 query (caché Redis desde W19) ✅
- `GET /catalogo/` → 2 queries (select_related desde W13) ✅

## Próximos pasos (W24 si queda tiempo)
- Agregar índices de BD en campos de búsqueda frecuente
  (Venta.fecha, Pedido.estado, Producto.activo)
- Evaluar `QuerySet.explain()` en el reporte de ventas filtrado