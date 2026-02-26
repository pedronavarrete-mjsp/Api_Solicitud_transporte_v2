# routers/tipo_combustible_router.py
"""
Endpoints para TipoCombustible.
CRUD completo con validaciones y respuestas estandarizadas en español.
"""

from fastapi import APIRouter, Query
from typing import Optional

from models.tipo_combustible_model import (
    TipoCombustibleCreate,
    TipoCombustibleUpdate,
)
from services.tipo_combustible_service import TipoCombustibleService
from utils.response_handler import (
    success_response,
    created_response,
    error_response,
    not_found_response,
    conflict_response,
    internal_error_response,
)

router = APIRouter(
    prefix="/tipo-combustible",
    tags=["Tipo de Combustible"],
    responses={
        404: {"description": "No encontrado"},
        409: {"description": "Conflicto - Registro duplicado"},
        500: {"description": "Error interno del servidor"},
    }
)

service = TipoCombustibleService()


# ──────────────────────────────────────────────
# POST - Crear
# ──────────────────────────────────────────────

@router.post(
    "/",
    summary="Crear tipo de combustible",
    description="Crea un nuevo tipo de combustible. El código y nombre deben ser únicos."
)
def crear_tipo_combustible(body: TipoCombustibleCreate):
    """
    Crea un nuevo tipo de combustible.

    Validaciones:
    - **codigo**: Obligatorio, único, sin espacios, mayúsculas
    - **nombre**: Obligatorio, único
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
        message="Tipo de combustible creado exitosamente"
    )


# ──────────────────────────────────────────────
# GET - Listar todos sin paginación
# ──────────────────────────────────────────────

@router.get(
    "/todos/lista",
    summary="Listar todos los tipos de combustible (sin paginación)",
    description="Lista todos los tipos de combustible activos. Ideal para dropdowns o selects."
)
def listar_todos_tipos_combustible(
    codigo: Optional[str] = Query(None, description="Filtrar por código"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre"),
    busqueda: Optional[str] = Query(None, description="Búsqueda general")
):
    """Lista todos los tipos de combustible activos sin paginación."""
    resultado = service.listar_todos(
        codigo=codigo,
        nombre=nombre,
        busqueda=busqueda
    )

    if "error" in resultado:
        return internal_error_response(detail=resultado["error"])

    return success_response(
        data=resultado["data"],
        message="Listado completo de tipos de combustible obtenido exitosamente"
    )


# ──────────────────────────────────────────────
# GET - Obtener por ID
# ──────────────────────────────────────────────

@router.get(
    "/{id_tipo_combustible}",
    summary="Obtener tipo de combustible por ID",
    description="Obtiene un tipo de combustible por su ID. Solo registros activos."
)
def obtener_tipo_combustible(id_tipo_combustible: int):
    """Obtiene un tipo de combustible específico por su ID."""
    resultado = service.obtener_por_id(id_tipo_combustible)

    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404:
            return not_found_response(resultado["error"])
        return internal_error_response(detail=resultado["error"])

    return success_response(
        data=resultado["data"],
        message="Tipo de combustible obtenido exitosamente"
    )


# ──────────────────────────────────────────────
# GET - Listar con paginación y filtros
# ──────────────────────────────────────────────

@router.get(
    "/",
    summary="Listar tipos de combustible (paginado)",
    description="Lista tipos de combustible con paginación y filtros opcionales."
)
def listar_tipos_combustible(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(10, ge=1, le=100, description="Registros por página"),
    codigo: Optional[str] = Query(None, description="Filtrar por código (búsqueda parcial)"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre (búsqueda parcial)"),
    busqueda: Optional[str] = Query(None, description="Búsqueda general en código y nombre")
):
    """
    Lista tipos de combustible con paginación.

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
        message="Listado de tipos de combustible obtenido exitosamente"
    )


# ──────────────────────────────────────────────
# PUT - Actualizar
# ──────────────────────────────────────────────

@router.put(
    "/{id_tipo_combustible}",
    summary="Actualizar tipo de combustible",
    description="Actualiza un tipo de combustible existente. Solo se actualizan los campos enviados."
)
def actualizar_tipo_combustible(id_tipo_combustible: int, body: TipoCombustibleUpdate):
    """
    Actualiza un tipo de combustible.

    Validaciones:
    - Registro debe existir y estar activo
    - Si se cambia el código, debe ser único
    - Si se cambia el nombre, debe ser único
    """
    resultado = service.actualizar(id_tipo_combustible, body.model_dump(exclude_none=True))

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
        message="Tipo de combustible actualizado exitosamente"
    )


# ──────────────────────────────────────────────
# DELETE - Eliminar (soft delete)
# ──────────────────────────────────────────────

@router.delete(
    "/{id_tipo_combustible}",
    summary="Eliminar tipo de combustible",
    description="Eliminación lógica. No se permite si tiene vehículos activos asociados."
)
def eliminar_tipo_combustible(id_tipo_combustible: int):
    """
    Elimina lógicamente un tipo de combustible.

    Validaciones:
    - Registro debe existir y estar activo
    - No debe tener vehículos activos asociados
    """
    resultado = service.eliminar(id_tipo_combustible)

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
        message="Tipo de combustible eliminado exitosamente"
    )