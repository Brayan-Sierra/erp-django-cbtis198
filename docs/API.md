# API REST — Referencia Completa
## ERP Django · UTEC Celaya

Base URL: `https://erp-django-utec.onrender.com/api/`

---

## Autenticación

La API usa **Token Authentication**. Incluir en cada petición:

Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
### Obtener Token

POST /api/auth/token/
Content-Type: application/json{ "username": "admin", "password": "tu-password" }→ 200 OK
{ "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" }
---

## Permisos

| Método | Permiso requerido |
|---|---|
| `GET` (lectura) | Sin autenticación (público) |
| `POST`, `PUT`, `PATCH`, `DELETE` | Token válido |

---

## Endpoints

### Categorías

| Método | URL | Descripción |
|---|---|---|
| `GET` | `/api/categorias/` | Lista todas las categorías |
| `POST` | `/api/categorias/` | Crea una categoría |
| `GET` | `/api/categorias/{id}/` | Detalle de una categoría |
| `PUT` | `/api/categorias/{id}/` | Actualiza una categoría |
| `DELETE` | `/api/categorias/{id}/` | Elimina una categoría |

**Ejemplo de respuesta `GET /api/categorias/1/`:**
```json
{
  "id": 1,
  "nombre": "Electrónica",
  "descripcion": "Dispositivos electrónicos y accesorios"
}
ProductosMétodoURLDescripciónGET/api/productos/Lista productos activos (paginado, 20/página)POST/api/productos/Crea un producto (requiere token)GET/api/productos/{id}/Detalle de un productoPUT/api/productos/{id}/Actualización completaPATCH/api/productos/{id}/Actualización parcialDELETE/api/productos/{id}/Elimina un productoParámetros de paginación: ?page=2 → página 2 de resultados.Ejemplo de respuesta GET /api/productos/1/:JSON{
  "id": 1,
  "nombre": "Laptop HP ProBook",
  "precio": "12500.00",
  "stock": 5,
  "categoria": 1,
  "categoria_nombre": "Electrónica",
  "proveedor": 2,
  "proveedor_nombre": "Distribuidora Norte S.A.",
  "activo": true,
  "imagen": null,
  "imagen_url": "[https://erp-django-utec.onrender.com/media/productos/laptop.jpg](https://erp-django-utec.onrender.com/media/productos/laptop.jpg)",
  "creado": "2025-01-15T10:30:00Z"
}
Campos de solo lectura: id, creado, categoria_nombre,proveedor_nombre, imagen_url.ClientesMétodoURLDescripciónGET/api/clientes/Lista clientes activosPOST/api/clientes/Crea un clienteGET/api/clientes/{id}/Detalle de un clientePUT/api/clientes/{id}/Actualización completaPATCH/api/clientes/{id}/Actualización parcialDELETE/api/clientes/{id}/Elimina un clienteProveedoresMétodoURLDescripciónGET/api/proveedores/Lista proveedores activosPOST/api/proveedores/Crea un proveedorGET/api/proveedores/{id}/Detalle de un proveedorPUT/api/proveedores/{id}/Actualización completaDELETE/api/proveedores/{id}/Elimina un proveedorVentasMétodoURLDescripciónGET/api/ventas/Lista ventas (más recientes primero)POST/api/ventas/Crea el encabezado de una ventaGET/api/ventas/{id}/Detalle con líneas anidadas y totalDELETE/api/ventas/{id}/Elimina una venta y sus líneasEjemplo de respuesta GET /api/ventas/1/:JSON{
  "id": 1,
  "cliente": 3,
  "cliente_nombre": "Juan García",
  "fecha": "2025-01-15T18:30:00Z",
  "detalles": [
    {
      "id": 1,
      "producto": 5,
      "cantidad": 2,
      "precio_unitario": "12500.00",
      "subtotal": "25000.00"
    }
  ],
  "total": "25000.00"
}
Códigos de RespuestaCódigoSignificado200 OKPetición exitosa (GET, PUT, PATCH)201 CreatedRecurso creado exitosamente (POST)204 No ContentEliminado exitosamente (DELETE)400 Bad RequestDatos de entrada inválidos401 UnauthorizedToken faltante o inválido403 ForbiddenToken válido pero sin permiso404 Not FoundRecurso no encontradoBrowsable APILa API tiene una interfaz web navegable disponible en:https://erp-django-utec.onrender.com/api/Acceder desde el navegador para explorar todos los endpoints
con formularios interactivos.Fragmento de código
*(Si tu URL en Render tiene otro subdominio, reemplaza `[https://erp-django-utec.onrender.com](https://erp-django-utec.onrender.com)` por tu URL real antes de guardar).*

Cuando lo guardes, el siguiente paso es agregar `healthCheckPath: /` en `render.yaml` y crear 