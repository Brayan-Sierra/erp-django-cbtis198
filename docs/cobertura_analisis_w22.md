# Análisis de Cobertura — W22
## Primera corrida: 19/11/2026
## Cobertura global: 88.7%

### Brechas identificadas

| Módulo | Cobertura | Líneas/ramas sin cubrir |
|---|---|---|
| productos/admin.py | 74.4% | 31-37, 42-48 (vistas previas de imagen en admin) |
| catalogo/views.py | 76.4% | 104, 135, 150-172, 210-223 (actualizar_cantidad, vaciar_carrito) |
| reportes/tasks.py | 78.6% | 16, 48-52, 89-96, 131-132 (ID inexistente / manejo de errores) |

### Plan de acción
→ Agregar tests de integración E2E (Parte 5)
→ Agregar tests dirigidos a las brechas (Parte 6)
→ Meta: mantener ≥ 80% global y subir módulos críticos en segunda corrida