# ERP Django — UTEC Celaya
## Sistema de Planificación de Recursos Empresariales

<!-- Badges -->
![Python](https://img.shields.io/badge/python-3.11-blue)
![Django](https://img.shields.io/badge/django-4.2_LTS-green)
![Tests](https://img.shields.io/badge/tests-219_passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-90.2%25-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Sistema ERP académico desarrollado durante 24 semanas en el
**Técnico en Programación (SEP 3061300006-23)** de UTEC Celaya.

**URL Pública:** https://erp-django-utec.onrender.com

---

## Tabla de Contenidos

- [Características](#características)
- [Stack Tecnológico](#stack-tecnológico)
- [Instalación Rápida con Docker](#instalación-rápida-con-docker)
- [Instalación Manual (sin Docker)](#instalación-manual-sin-docker)
- [Variables de Entorno](#variables-de-entorno)
- [Comandos Útiles](#comandos-útiles)
- [API REST](#api-rest)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Tests y Cobertura](#tests-y-cobertura)
- [Despliegue en Render.com](#despliegue-en-rendercom)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Autor](#autor)

---

## Características

| Módulo | Funcionalidad | Semana |
|---|---|---|
| 🏢 **Gestión de inventario** | Productos, categorías, proveedores con historial de precios | W05, W21 |
| 👥 **Clientes** | CRUD completo con validaciones | W05–W08 |
| 💰 **Ventas** | Registro, líneas de detalle, cálculo automático de totales | W05–W08 |
| 🔐 **Autenticación y roles** | Login/logout allauth + 3 grupos RBAC | W09 |
| 🌐 **API REST** | Endpoints DRF con autenticación por token | W10 |
| 🖼️ **Gestión de imágenes** | Subida con validación MIME, almacenamiento S3 | W11 |
| 📄 **Documentos** | Facturas PDF (WeasyPrint/xhtml2pdf) + exportación Excel | W12 |
| 🛒 **E-commerce** | Catálogo público, carrito de sesión, filtros | W13 |
| 💳 **Pagos Stripe** | Checkout sandbox, webhooks, descuento de stock | W14–W15 |
| ⚡ **Tareas asíncronas** | Celery + Redis: correos, alertas, reportes automáticos | W16–W18 |
| 📊 **Dashboard** | 5 KPIs + 3 gráficas Chart.js + caché Redis | W19 |
| 📋 **Reportes** | Filtros por fecha/cliente/producto + exportación adaptativa | W20 |
| 📜 **Auditoría** | Historial de cambios de precio (django-simple-history) | W21 |

---

## Stack Tecnológico

Backend:        Python 3.11 · Django 4.2 LTS · Django REST Framework
Base de datos:  PostgreSQL 15 (producción) · SQLite (desarrollo)
Caché/Cola:     Redis 7 (broker Celery + caché Django)
Tareas:         Celery 5.3 · Celery Beat · Flower
Email:          django-anymail + SendGrid
Pagos:          Stripe (sandbox)
Almacenamiento: django-storages + S3 (producción)
Frontend:       Bootstrap 5 · Chart.js 4.4 · Fable 5 AzulERP
PDF:            WeasyPrint 60 (Docker/Linux) · xhtml2pdf (Windows/USB)
Historial:      django-simple-history 3.5
Despliegue:     Render.com (Docker) · GitHub Actions (CI opcional)
---

## Instalación Rápida con Docker

### Prerrequisitos

- Docker Desktop ≥ 25.x instalado y corriendo
- Git instalado
- Cuenta en Stripe (modo sandbox, gratuita)
- Cuenta en SendGrid (plan gratuito: 100 correos/día)

### Pasos

```bash
# 1. Clonar el repositorio
git clone [https://github.com/TU_USUARIO/erp-django-utec.git](https://github.com/TU_USUARIO/erp-django-utec.git)
cd erp-django-utec

# 2. Copiar y configurar las variables de entorno
cp .env.example .env
# → Editar .env con tus claves (ver sección Variables de Entorno)

# 3. Construir y arrancar todos los servicios
docker-compose build
docker-compose up -d

# 4. Crear el superusuario
docker-compose exec web python manage.py createsuperuser

# 5. Configurar los grupos de roles
docker-compose exec web python manage.py crear_grupos

# 6. Abrir en el navegador
# → http://localhost:8000           (ERP)
# → http://localhost:8000/admin/    (Panel Admin con Jazzmin)
# → http://localhost:8000/catalogo/ (Tienda pública)
# → http://localhost:5555           (Flower — monitor Celery)
Instalación Manual (sin Docker)Para el entorno portable USB en Windows (sin permisos de administrador):DOS:: Prerrequisito: Python 3.11 + Git

:: 1. Clonar
git clone [https://github.com/TU_USUARIO/erp-django-utec.git](https://github.com/TU_USUARIO/erp-django-utec.git)
cd erp-django-utec

:: 2. Crear entorno virtual y activar
python -m venv env_erp
call env_erp\Scripts\activate

:: 3. Instalar dependencias
pip install -r requirements.txt

:: 4. Configurar variables de entorno
copy .env.example .env
:: Editar .env con tus valores

:: 5. Migrar y arrancar
python manage.py migrate
python manage.py createsuperuser
python manage.py crear_grupos
python manage.py runserver

:: Nota: En este entorno, la generación de PDF usa xhtml2pdf (no WeasyPrint)
:: y no se dispone de Celery (las tareas se ejecutan síncronamente con CELERY_TASK_ALWAYS_EAGER=True)
Variables de EntornoCopiar .env.example como .env y completar:Bash# ── Django ─────────────────────────────────────────────────────────
SECRET_KEY=genera-una-clave-aleatoria-de-50-caracteres
DEBUG=True                         # False en producción
ALLOWED_HOSTS=localhost,127.0.0.1  # dominio Render en producción

# ── Base de datos ──────────────────────────────────────────────────
DATABASE_URL=postgresql://erp_user:erp_pass@localhost:5432/erp_db
# En desarrollo con SQLite (más simple):
# DATABASE_URL=sqlite:///db.sqlite3

# ── Redis ──────────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0        # broker Celery
REDIS_CACHE_URL=redis://localhost:6379/1  # caché Django

# ── Stripe ─────────────────────────────────────────────────────────
STRIPE_SECRET_KEY=sk_test_...             # clave secreta sandbox
STRIPE_PUBLISHABLE_KEY=pk_test_...       # clave publicable sandbox
STRIPE_WEBHOOK_SECRET=whsec_...          # obtener con: stripe listen

# ── SendGrid ───────────────────────────────────────────────────────
SENDGRID_API_KEY=SG....
DEFAULT_FROM_EMAIL=ERP Django <noreply@tudominio.com>
ADMIN_EMAIL=admin@tudominio.com

# ── Almacenamiento S3 (opcional, para producción) ──────────────────
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=

# ── Dominio del sitio (para tareas Celery) ─────────────────────────
SITE_DOMAIN=[https://erp-django-utec.onrender.com](https://erp-django-utec.onrender.com)
Comandos ÚtilesBash# ── Tests y Cobertura ──────────────────────────────────────────────
python manage.py test tests                            # todos los tests
python manage.py test tests.test_w24_smoke             # smoke tests
python manage.py test tests.test_w09_auth_rbac         # un módulo específico
coverage run manage.py test tests && coverage report   # con cobertura
coverage html && start htmlcov/index.html              # reporte visual

# ── Administración ─────────────────────────────────────────────────
python manage.py createsuperuser         # crear admin
python manage.py crear_grupos            # configurar Gerente/Vendedor/Almacén
python manage.py migrate                 # aplicar migraciones
python manage.py collectstatic           # recolectar estáticos

# ── Celery (en terminales separadas) ──────────────────────────────
celery -A core worker -l info -Q erp_django    # procesar tareas
celery -A core beat   -l info                  # tareas programadas
celery -A core flower --port=5555              # monitorear

# ── Docker ─────────────────────────────────────────────────────────
docker-compose up -d                           # arrancar todo
docker-compose logs -f web                     # ver logs del servidor
docker-compose exec web python manage.py shell # shell interactivo
docker-compose down                            # detener todo

# ── Stripe CLI (para probar webhooks) ─────────────────────────────
stripe listen --forward-to http://localhost:8000/catalogo/webhook/
API RESTLa API expone endpoints RESTful bajo /api/ con autenticación por Token (Authorization: Token <key>). Consulta la referencia completa con ejemplos JSON en docs/API.md.Arquitectura del Sistema┌─────────────────────────────────────────────────────────────────────┐
│  CLIENTE (Navegador / App móvil / Stripe / SendGrid)                │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTP/HTTPS
┌───────────────────────────▼─────────────────────────────────────────┐
│  RENDER.COM / DOCKER LOCAL                                          │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Django 4.2 + Gunicorn                                       │  │
│  │  ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐  │  │
│  │  │ Interface  │ │ API REST │ │ Catálogo │ │  Reportes   │  │  │
│  │  │   Web      │ │  (DRF)   │ │ Carrito  │ │ Dashboard   │  │  │
│  │  │ (Jazzmin)  │ │ Token    │ │ Checkout │ │ Exportar    │  │  │
│  │  └────────────┘ └──────────┘ └──────────┘ └─────────────┘  │  │
│  └───────────────────────┬──────────────────────────────────────┘  │
│                          │                                          │
│  ┌────────────┐  ┌───────▼──────┐  ┌──────────────────────────┐  │
│  │ PostgreSQL │  │   Redis 7    │  │  Celery Worker + Beat    │  │
│  │    15      │  │  DB/0 broker │  │  · enviar_confirmacion   │  │
│  │ (datos)    │  │  DB/1 caché  │  │  · verificar_stock_bajo  │  │
│  │            │  │              │  │  · reporte_ventas_diario │  │
│  └────────────┘  └──────────────┘  │  · generar_exportacion   │  │
│                                    └──────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  Servicios Externos                                         │  │
│  │  · Stripe (pagos sandbox)  · SendGrid (correo transaccional)│  │
│  │  · Amazon S3 (imágenes)    · Flower (monitor Celery :5555)  │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
Tests y CoberturaBashpython manage.py test tests   # Ran 227 tests — OK (219 base + 8 smoke tests W24)
coverage report               # TOTAL: 90.2%
Suite de tests por espiral:EspiralSemanasTests agregadosAcumuladoE1 — Entorno y TemplatesW01–W033333E2 — Modelado y ORMW04–W063366E3 — CRUD y AuthW07–W0934100E4 — API REST y MediaW10–W1223123E5 — E-commerceW13–W1524147E6 — Celery e IntegracionesW16–W1824171E7 — Dashboard y ReportesW19–W2124195E8 — Calidad y EntregaW22–W2432227Despliegue en Render.comBash# 1. Fork del repositorio en GitHub
# 2. Conectar Render con GitHub
# 3. Crear Blueprint desde render.yaml (incluido en el repo)
# 4. Configurar las variables de entorno secretas en el dashboard
# 5. Deploy automático al hacer git push origin main

# Comandos post-deploy (desde la Shell de Render):
python manage.py crear_grupos
python manage.py check --deploy
Estructura del Proyectoerp-django-utec/
├── core/                    # Configuración central de Django
│   ├── settings.py          # Dev (SQLite, console email, debug-toolbar)
│   ├── settings_prod.py     # Producción (PostgreSQL, SendGrid, S3)
│   ├── celery.py            # Configuración de Celery
│   └── urls.py              # Enrutador principal
├── clientes/                # App: gestión de clientes
├── proveedores/             # App: gestión de proveedores
├── productos/               # App: inventario (con historial django-simple-history)
├── ventas/                  # App: ventas, detalles y pedidos
├── reportes/                # App: dashboard, reportes filtrables, exportación
├── configuracion/           # App: singleton ConfiguracionERP
├── catalogo/                # App: tienda pública, carrito, checkout, webhooks
├── templates/               # Templates base + emails
├── static/                  # CSS, JS (Fable 5 AzulERP)
├── tests/                   # Suite de tests (unit + integración + rendimiento + smoke)
│   └── factories.py         # factory_boy para datos de prueba
├── docs/                    # Documentación técnica
│   ├── API.md               # Referencia completa de la API REST
│   ├── auditoria_rendimiento_w23.md
│   └── cobertura_analisis_w22.md
├── Dockerfile               # Multi-stage con WeasyPrint
├── docker-compose.yml       # Stack local: web + db + redis + celery + flower
├── render.yaml              # Blueprint de despliegue en Render.com
├── requirements.txt         # Dependencias Python
└── README.md                # Este archivo
AutorMC. Román Fernando López González
Asesor de Programación · UTEC Celaya
SEP 3061300006-23 · Técnico en ProgramaciónFragmento de código
Cuando guardes `README.md`, avísame si quieres que te pase también `docs/API.md` y los 8 smok