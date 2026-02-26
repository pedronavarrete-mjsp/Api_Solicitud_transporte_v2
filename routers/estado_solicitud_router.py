# routers/estado_solicitud_router.py
"""
Endpoints para EstadoSolicitud.
CRUD completo con validaciones y respuestas estandarizadas en español.
Incluye filtro por EsEstadoFinal.
"""

from fastapi import APIRouter, Query
from typing import Optional

from models.estado_solicitud_model import (
    EstadoSolicitudCreate,
    EstadoSolicitudUpdate,
)
from services.estado_solicitud_service import EstadoSolicitudService
from utils.response_handler import (
    success_response,
    created_response,
    error_response,
    not_found_response,
    conflict_response,
    internal_error_response,
)

router = APIRouter(
    prefix="/estado-solicitud",
    tags=["Estado de Solicitud"],
    responses={
        404: {"description": "No encontrado"},
        409: {"description": "Conflicto - Registro duplicado"},
        500: {"description": "Error interno del servidor"},
    }
)

service = EstadoSolicitudService()


# ──────────────────────────────────────────────
# POST - Crear
# ──────────────────────────────────────────────

@router.post(
    "/",
    summary="Crear estado de solicitud",
    description="Crea un nuevo estado de solicitud. Código, nombre y orden deben ser únicos."
)
def crear_estado_solicitud(body: EstadoSolicitudCreate):
    """
    Crea un nuevo estado de solicitud.

    Validaciones:
    - **codigo**: Obligatorio, único, sin espacios, mayúsculas
    - **nombre**: Obligatorio, único
    - **esEstadoFinal**: Obligatorio, indica si es estado final del flujo
    - **orden**: Obligatorio, único entre activos, define posición en el flujo
    - **color**: Opcional, para representación visual
    - **descripcion**: Opcional, máximo 250 caracteres
    """
    resultado = service.crear(body.model_dump())

    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 409:
            return conflict_response(resultado["error"])
        if status == 500:
            return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)

    return created_response(
        data=resultado["data"],
        message="Estado de solicitud creado exitosamente"
    )


# ──────────────────────────────────────────────
# GET - Listar todos sin paginación
# ──────────────────────────────────────────────

@router.get(
    "/todos/lista",
    summary="Listar todos los estados de solicitud (sin paginación)",
    description="Lista todos los estados de solicitud activos. Ideal para dropdowns o selects. Ordenado por campo Orden."
)
def listar_todos_estados_solicitud(
    codigo: Optional[str] = Query(None, description="Filtrar por código"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre"),
    es_estado_final: Optional[bool] = Query(None, alias="esEstadoFinal", description="Filtrar por estado final (true/false)"),
    busqueda: Optional[str] = Query(None, description="Búsqueda general")
):
    """Lista todos los estados de solicitud activos sin paginación."""
    resultado = service.listar_todos(
        codigo=codigo,
        nombre=nombre,
        es_estado_final=es_estado_final,
        busqueda=busqueda
    )

    if "error" in resultado:
        return internal_error_response(detail=resultado["error"])

    return success_response(
        data=resultado["data"],
        message="Listado completo de estados de solicitud obtenido exitosamente"
    )


# ──────────────────────────────────────────────
# GET - Obtener por ID
# ──────────────────────────────────────────────

@router.get(
    "/{id_estado_solicitud}",
    summary="Obtener estado de solicitud por ID",
    description="Obtiene un estado de solicitud por su ID. Solo registros activos."
)
def obtener_estado_solicitud(id_estado_solicitud: int):
    """Obtiene un estado de solicitud específico por su ID."""
    resultado = service.obtener_por_id(id_estado_solicitud)

    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404:
            return not_found_response(resultado["error"])
        return internal_error_response(detail=resultado["error"])

    return success_response(
        data=resultado["data"],
        message="Estado de solicitud obtenido exitosamente"
    )


# ──────────────────────────────────────────────
# GET - Listar con paginación y filtros
# ──────────────────────────────────────────────

@router.get(
    "/",
    summary="Listar estados de solicitud (paginado)",
    description="Lista estados de solicitud con paginación y filtros opcionales. Ordenado por campo Orden."
)
def listar_estados_solicitud(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(10, ge=1, le=100, description="Registros por página"),
    codigo: Optional[str] = Query(None, description="Filtrar por código (búsqueda parcial)"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre (búsqueda parcial)"),
    es_estado_final: Optional[bool] = Query(None, alias="esEstadoFinal", description="Filtrar por estado final"),
    busqueda: Optional[str] = Query(None, description="Búsqueda general en código, nombre y descripción")
):
    """
    Lista estados de solicitud con paginación.

    Filtros disponibles:
    - **codigo**: Búsqueda parcial por código
    - **nombre**: Búsqueda parcial por nombre
    - **esEstadoFinal**: Filtrar por si es estado final (true/false)
    - **busqueda**: Búsqueda en código, nombre y descripción
    """
    resultado = service.listar(
        pagina=pagina,
        por_pagina=por_pagina,
        codigo=codigo,
        nombre=nombre,
        es_estado_final=es_estado_final,
        busqueda=busqueda
    )

    if "error" in resultado:
        return internal_error_response(detail=resultado["error"])

    return success_response(
        data=resultado["data"],
        message="Listado de estados de solicitud obtenido exitosamente"
    )


# ──────────────────────────────────────────────
# PUT - Actualizar
# ──────────────────────────────────────────────

@router.put(
    "/{id_estado_solicitud}",
    summary="Actualizar estado de solicitud",
    description="Actualiza un estado de solicitud existente. Solo se actualizan los campos enviados."
)
def actualizar_estado_solicitud(id_estado_solicitud: int, body: EstadoSolicitudUpdate):
    """
    Actualiza un estado de solicitud.

    Validaciones:
    - Registro debe existir y estar activo
    - Si se cambia el código, debe ser único
    - Si se cambia el nombre, debe ser único
    - Si se cambia el orden, debe ser único entre activos
    """
    resultado = service.actualizar(id_estado_solicitud, body.model_dump(exclude_none=True))

    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404:
            return not_found_response(resultado["error"])
        if status == 409:
            return conflict_response(resultado["error"])
        if status == 500:
            return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)

    return success_response(
        data=resultado["data"],
        message="Estado de solicitud actualizado exitosamente"
    )


# ──────────────────────────────────────────────
# DELETE - Eliminar (soft delete)
# ──────────────────────────────────────────────

@router.delete(
    "/{id_estado_solicitud}",
    summary="Eliminar estado de solicitud",
    description="Eliminación lógica. No se permite si tiene solicitudes activas asociadas."
)
def eliminar_estado_solicitud(id_estado_solicitud: int):
    """
    Elimina lógicamente un estado de solicitud.

    Validaciones:
    - Registro debe existir y estar activo
    - No debe tener solicitudes activas asociadas en el histórico
    """
    resultado = service.eliminar(id_estado_solicitud)

    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404:
            return not_found_response(resultado["error"])
        if status == 409:
            return conflict_response(resultado["error"])
        if status == 500:
            return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)

    return success_response(
        data=resultado["data"],
        message="Estado de solicitud eliminado exitosamente"
    )