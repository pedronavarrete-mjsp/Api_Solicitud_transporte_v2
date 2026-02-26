# routers/tipo_disponibilidad_router.py
"""
Endpoints para TipoDisponibilidad.
CRUD completo con validaciones y respuestas estandarizadas en español.
"""

from fastapi import APIRouter, Query
from typing import Optional

from models.tipo_disponibilidad_model import (
    TipoDisponibilidadCreate,
    TipoDisponibilidadUpdate,
)
from services.tipo_disponibilidad_service import TipoDisponibilidadService
from utils.response_handler import (
    success_response,
    created_response,
    error_response,
    not_found_response,
    conflict_response,
    internal_error_response,
)

router = APIRouter(
    prefix="/tipo-disponibilidad",
    tags=["Tipo de Disponibilidad"],
    responses={
        404: {"description": "No encontrado"},
        409: {"description": "Conflicto - Registro duplicado"},
        500: {"description": "Error interno del servidor"},
    }
)

service = TipoDisponibilidadService()


# ──────────────────────────────────────────────
# POST - Crear
# ──────────────────────────────────────────────

@router.post(
    "/",
    summary="Crear tipo de disponibilidad",
    description="Crea un nuevo tipo de disponibilidad. El código y nombre deben ser únicos."
)
def crear_tipo_disponibilidad(body: TipoDisponibilidadCreate):
    """
    Crea un nuevo tipo de disponibilidad.

    Validaciones:
    - **codigo**: Obligatorio, único, sin espacios, mayúsculas
    - **nombre**: Obligatorio, único, máximo 20 caracteres
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
        message="Tipo de disponibilidad creado exitosamente"
    )


# ──────────────────────────────────────────────
# GET - Listar todos sin paginación
# ──────────────────────────────────────────────

@router.get(
    "/todos/lista",
    summary="Listar todos los tipos de disponibilidad (sin paginación)",
    description="Lista todos los tipos de disponibilidad activos. Ideal para dropdowns o selects."
)
def listar_todos_tipos_disponibilidad(
    codigo: Optional[str] = Query(None, description="Filtrar por código"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre"),
    busqueda: Optional[str] = Query(None, description="Búsqueda general")
):
    """Lista todos los tipos de disponibilidad activos sin paginación."""
    resultado = service.listar_todos(
        codigo=codigo,
        nombre=nombre,
        busqueda=busqueda
    )

    if "error" in resultado:
        return internal_error_response(detail=resultado["error"])

    return success_response(
        data=resultado["data"],
        message="Listado completo de tipos de disponibilidad obtenido exitosamente"
    )


# ──────────────────────────────────────────────
# GET - Obtener por ID
# ──────────────────────────────────────────────

@router.get(
    "/{id_tipo_disponibilidad}",
    summary="Obtener tipo de disponibilidad por ID",
    description="Obtiene un tipo de disponibilidad por su ID. Solo registros activos."
)
def obtener_tipo_disponibilidad(id_tipo_disponibilidad: int):
    """Obtiene un tipo de disponibilidad específico por su ID."""
    resultado = service.obtener_por_id(id_tipo_disponibilidad)

    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404:
            return not_found_response(resultado["error"])
        return internal_error_response(detail=resultado["error"])

    return success_response(
        data=resultado["data"],
        message="Tipo de disponibilidad obtenido exitosamente"
    )


# ──────────────────────────────────────────────
# GET - Listar con paginación y filtros
# ──────────────────────────────────────────────

@router.get(
    "/",
    summary="Listar tipos de disponibilidad (paginado)",
    description="Lista tipos de disponibilidad con paginación y filtros opcionales."
)
def listar_tipos_disponibilidad(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(10, ge=1, le=100, description="Registros por página"),
    codigo: Optional[str] = Query(None, description="Filtrar por código (búsqueda parcial)"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre (búsqueda parcial)"),
    busqueda: Optional[str] = Query(None, description="Búsqueda general en código y nombre")
):
    """
    Lista tipos de disponibilidad con paginación.

    Filtros disponibles:
    - **codigo**: Búsqueda parcial por código
    - **nombre**: Búsqueda parcial por nombre
    - **busqueda**: Búsqueda en código y nombre
    """
    resultado = service.listar(
        pagina=pagina,
        por_pagina=por_pagina,
        codigo=codigo,
        nombre=nombre,
        busqueda=busqueda
    )

    if "error" in resultado:
        return internal_error_response(detail=resultado["error"])

    return success_response(
        data=resultado["data"],
        message="Listado de tipos de disponibilidad obtenido exitosamente"
    )


# ──────────────────────────────────────────────
# PUT - Actualizar
# ──────────────────────────────────────────────

@router.put(
    "/{id_tipo_disponibilidad}",
    summary="Actualizar tipo de disponibilidad",
    description="Actualiza un tipo de disponibilidad existente. Solo se actualizan los campos enviados."
)
def actualizar_tipo_disponibilidad(id_tipo_disponibilidad: int, body: TipoDisponibilidadUpdate):
    """
    Actualiza un tipo de disponibilidad.

    Validaciones:
    - Registro debe existir y estar activo
    - Si se cambia el código, debe ser único
    - Si se cambia el nombre, debe ser único
    """
    resultado = service.actualizar(id_tipo_disponibilidad, body.model_dump(exclude_none=True))

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
        message="Tipo de disponibilidad actualizado exitosamente"
    )


# ──────────────────────────────────────────────
# DELETE - Eliminar (soft delete)
# ──────────────────────────────────────────────

@router.delete(
    "/{id_tipo_disponibilidad}",
    summary="Eliminar tipo de disponibilidad",
    description="Eliminación lógica. No se permite si tiene motoristas activos asociados."
)
def eliminar_tipo_disponibilidad(id_tipo_disponibilidad: int):
    """
    Elimina lógicamente un tipo de disponibilidad.

    Validaciones:
    - Registro debe existir y estar activo
    - No debe tener motoristas activos asociados
    """
    resultado = service.eliminar(id_tipo_disponibilidad)

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
        message="Tipo de disponibilidad eliminado exitosamente"
    )