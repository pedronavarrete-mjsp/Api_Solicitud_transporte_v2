# main.py
"""
Punto de entrada principal de la API Backend ONI Justicia.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.responses import HTMLResponse

from config import get_settings
from routers.estado_mision_router import router as estado_mision_router
from routers.clase_vehiculo_router import router as clase_vehiculo_router
from routers.estado_solicitud_router import router as estado_solicitud_router
from routers.estado_vehiculo_router import router as estado_vehiculo_router
from routers.tipo_combustible_router import router as tipo_combustible_router
from routers.tipo_disponibilidad_router import router as tipo_disponibilidad_router
from routers.tipo_licencia_router import router as tipo_licencia_router
from routers.tipo_prioridad_solicitud_router import router as tipo_prioridad_solicitud_router
from routers.tipo_servicio_solicitud_router import router as tipo_servicio_solicitud_router
from routers.rol_router import router as rol_router
from routers.lugar_router import router as lugar_router
from routers.departamento_router import router as departamento_router


settings = get_settings()

app = FastAPI(
    title=settings.app.TITLE,
    version=settings.app.VERSION,
    description="API para gestión de solicitudes y misiones de transporte - ONI Justicia",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ──────────────────────────────────────────────
# CORS
# ──────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Manejo global de errores de validación Pydantic (en español)
# ──────────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Captura errores de validación de Pydantic y los devuelve en español"""
    errores = []

    for error in exc.errors():
        campo = " → ".join(str(loc) for loc in error["loc"] if loc != "body")
        tipo = error["type"]
        msg_original = error["msg"]

        # Traducir mensajes comunes
        mensaje = _traducir_error_validacion(campo, tipo, msg_original, error)
        errores.append(mensaje)

    return JSONResponse(
        status_code=422,
        content={
            "exito": False,
            "mensaje": "Error de validación en los datos enviados",
            "detalle": errores
        }
    )


def _traducir_error_validacion(campo: str, tipo: str, msg: str, error: dict) -> str:
    """Traduce los mensajes de error de Pydantic al español"""

    traducciones = {
        "missing": f"El campo '{campo}' es obligatorio",
        "string_too_short": f"El campo '{campo}' es demasiado corto",
        "string_too_long": f"El campo '{campo}' excede la longitud máxima permitida",
        "value_error": f"El campo '{campo}' tiene un valor inválido: {msg}",
        "int_parsing": f"El campo '{campo}' debe ser un número entero",
        "string_type": f"El campo '{campo}' debe ser texto",
        "bool_parsing": f"El campo '{campo}' debe ser verdadero o falso",
        "date_parsing": f"El campo '{campo}' debe ser una fecha válida (YYYY-MM-DD)",
        "time_parsing": f"El campo '{campo}' debe ser una hora válida (HH:MM:SS)",
        "datetime_parsing": f"El campo '{campo}' debe ser una fecha y hora válida",
        "greater_than_equal": f"El campo '{campo}' debe ser mayor o igual al mínimo permitido",
        "less_than_equal": f"El campo '{campo}' debe ser menor o igual al máximo permitido",
        "too_short": f"El campo '{campo}' debe tener al menos los elementos mínimos requeridos",
        "json_invalid": f"El cuerpo de la petición no es un JSON válido",
    }

    # Buscar traducción exacta o parcial
    for key, traduccion in traducciones.items():
        if key in tipo:
            return traduccion

    # Si no hay traducción, devolver el original con contexto
    return f"Error en '{campo}': {msg}"


# ──────────────────────────────────────────────
# Manejo global de excepciones no controladas
# ──────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Captura cualquier excepción no controlada"""
    return JSONResponse(
        status_code=500,
        content={
            "exito": False,
            "mensaje": "Error interno del servidor",
            "detalle": str(exc) if settings.app.DEBUG else None
        }
    )


# ─────────────────────────────────────────────��
# Health check
# ──────────────────────────────────────────────

@app.get("/root", tags=["Health"])
def health_check():
    return {
        "exito": True,
        "mensaje": "API funcionando correctamente",
        "datos": {
            "servicio": settings.app.TITLE,
            "version": settings.app.VERSION
        }
    }


# ──────────────────────────────────────────────
# Registrar Routers
# ──────────────────────────────────────────────

# Catálogos
app.include_router(clase_vehiculo_router)
# Aquí se irán agregando los demás routers:
app.include_router(estado_mision_router)
app.include_router(estado_solicitud_router)
app.include_router(estado_vehiculo_router)
app.include_router(tipo_combustible_router)
app.include_router(tipo_disponibilidad_router)
app.include_router(tipo_licencia_router)
app.include_router(tipo_prioridad_solicitud_router)
app.include_router(tipo_servicio_solicitud_router)
app.include_router(lugar_router)
app.include_router(rol_router)
app.include_router(departamento_router)
# app.include_router(usuario_router)
# app.include_router(perfil_router)
# app.include_router(vehiculo_router)
# app.include_router(solicitud_router)
# app.include_router(mision_router)


@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html>
    <head>
        <title>Oni Transporte</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #fdfdfd;
                color: #111;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .container {
                text-align: center;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                background-color: #ffffff;
                max-width: 500px;
            }
            h2 {
                margin-bottom: 20px;
                font-size: 28px;
            }
            p {
                margin-bottom: 15px;
                font-size: 16px;
            }
            a {
                text-decoration: none;
                color: #ffffff;
                background-color: #111;
                padding: 8px 16px;
                border-radius: 6px;
                transition: background-color 0.3s;
            }
            a:hover {
                background-color: #333;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Bienvenido al backend de Oni transporte(Solicitud)</h2>
            <p>Documentación disponible en:</p>
            <p><a href='/docs'>Swagger UI</a></p>
            <p>Alternativa Redoc:</p>
            <p><a href='/redoc'>Redoc</a></p>
        </div>
    </body>
    </html>
    """
