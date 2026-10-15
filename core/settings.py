# core/settings.py
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Variables de entorno ──────────────────────────────────────────────────
env = environ.Env(DEBUG=(bool, True))
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY  = env('SECRET_KEY', default='dev-key-insegura-solo-para-desarrollo')
DEBUG       = env('DEBUG', default=True)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# ── Apps instaladas ───────────────────────────────────────────────────────
INSTALLED_APPS = [
    # Jazzmin PRIMERO — antes de django.contrib.admin
    'jazzmin',                          # ← nueva línea, primera posición
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Terceros
    'rest_framework',
    'whitenoise.runserver_nostatic',
    # Apps del ERP
    'clientes',
    'proveedores',
    'productos',
    'ventas',
    'reportes',
    'configuracion',   # ← nueva app W05
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

# ── Templates ─────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],       # carpeta global de templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ── Base de datos ─────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ── Internacionalización ──────────────────────────────────────────────────
LANGUAGE_CODE = 'es-mx'
TIME_ZONE     = 'America/Mexico_City'
USE_I18N      = True
USE_TZ        = True

# ── Archivos estáticos ────────────────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ── Archivos media ────────────────────────────────────────────────────────
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Autenticación ─────────────────────────────────────────────────────────
LOGIN_URL           = '/accounts/login/'
LOGIN_REDIRECT_URL  = '/productos/'
LOGOUT_REDIRECT_URL = '/'

# ── DRF ──────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# core/settings.py — agregar al final del archivo

# ── JAZZMIN — Personalización del admin con Fable 5 AzulERP ───────────────
JAZZMIN_SETTINGS = {
    # Identidad
    'site_title':       'ERP Django',
    'site_header':      'ERP CBTis198',
    'site_brand':       '𝄢 ERP Django',  # Clave de Fa reemplazando la caja
    'welcome_sign':     '𝄢 bienvenido al Sistema ERP · CBTis198 Celaya',
    'copyright':        'Brayan Enrique Sierra Rivera · CBTis198 Celaya',

    # Icono del sitio / Pestaña del navegador
    'site_icon':        None,
    'site_logo':        None,

    # Búsqueda global en el admin
    'search_model':     ['clientes.Cliente', 'productos.Producto'],

    # Menú superior (top navigation)
    'topmenu_links': [
        {'name': 'Inicio ERP',   'url': '/', 'new_window': False, 'icon': 'fas fa-home'},
        {'name': 'Productos',    'url': '/productos/', 'icon': 'fas fa-box-open'},
        {'name': 'Clientes',     'url': '/clientes/', 'icon': 'fas fa-users'},
        {'name': 'Ventas',       'url': '/ventas/', 'icon': 'fas fa-cash-register'},
    ],

    # Menú de usuario (avatar)
    'usermenu_links': [
        {'name': 'Ver ERP', 'url': '/', 'new_window': False, 'icon': 'fas fa-globe'},
    ],

    # Menú lateral: orden de apps y modelos
    'order_with_respect_to': [
        'clientes', 'proveedores', 'productos',
        'ventas', 'configuracion', 'auth',
    ],

    # Iconos de Font Awesome con colores y variedad
    'icons': {
        'auth':                       'fas fa-user-shield',
        'auth.user':                  'fas fa-user-astronaut',
        'auth.Group':                 'fas fa-users-cog',
        'clientes.Cliente':           'fas fa-id-card',
        'proveedores.Proveedor':      'fas fa-shipping-fast',
        'productos.Categoria':        'fas fa-layer-group',
        'productos.Producto':         'fas fa-cubes',
        'ventas.Venta':               'fas fa-file-invoice-dollar',
        'ventas.DetalleVenta':        'fas fa-receipt',
        'ventas.Pedido':              'fas fa-shopping-basket',
        'configuracion.ConfiguracionERP': 'fas fa-sliders-h',
    },
    'default_icon_parents': 'fas fa-folder-open',
    'default_icon_children': 'fas fa-dot-circle',

    # Apariencia
    'related_modal_active':     True,
    'custom_css':               'erp_custom.css',   # Personalización de estilos
    'show_sidebar':             True,
    'navigation_expanded':      True,
    'hide_apps':                [],
    'hide_models':              [],

    # UI tweaks
    'changeform_format':        'horizontal_tabs',
    'language_chooser':         False,
}

JAZZMIN_UI_TWEAKS = {
    'navbar_small_text':        False,
    'footer_small_text':        True,
    'body_small_text':          False,
    'brand_small_text':         False,
    'brand_colour':             'navbar-navy',
    'accent':                   'accent-warning',    # Acentos en dorado/amarillo brillante
    'navbar':                   'navbar-dark navbar-navy',
    'no_navbar_border':         True,
    'navbar_fixed':             True,
    'layout_boxed':             False,
    'footer_fixed':             False,
    'sidebar_fixed':            True,
    'sidebar':                  'sidebar-dark-warning', # Destaca opciones seleccionadas
    'sidebar_nav_small_text':   False,
    'sidebar_disable_expand':   False,
    'sidebar_nav_child_indent': True,
    'sidebar_nav_compact_style': False,
    'sidebar_nav_legacy_style': False,
    'sidebar_nav_flat_style':   False,
    'theme':                    'darkly',           # Tema moderno de alto contraste
    'default_theme_mode':       'dark',
    'button_classes': {
        'primary':   'btn-outline-primary',
        'secondary': 'btn-outline-secondary',
        'info':      'btn-info',
        'warning':   'btn-warning',
        'danger':    'btn-danger',
        'success':   'btn-success',
    },
}