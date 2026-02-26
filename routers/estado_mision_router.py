# routers/estado_mision_router.py
"""
Endpoints para EstadoMision.
CRUD completo con validaciones y respuestas estandarizadas en español.
"""

from fastapi import APIRouter, Query
from typing import Optional

from models.estado_mision_model import (
    EstadoMisionCreate,
    EstadoMisionUpdate,
)
from services.estado_mision_service import EstadoMisionService
from utils.response_handler import (
    success_response,
    created_response,
    error_response,
    not_found_response,
    conflict_response,
    internal_error_response,
)

router = APIRouter(
    prefix="/estado-mision",
    tags=["Estado de Misión"],
    responses={
        404: {"description": "No encontrado"},
        409: {"description": "Conflicto - Registro duplicado"},
        500: {"description": "Error interno del servidor"},
    }
)

service = EstadoMisionService()


# ──────────────────────────────────────────────
# POST - Crear
# ──────────────────────────────────────────────

@router.post(
    "/",
    summary="Crear estado de misión",
    description="Crea un nuevo estado de misión. El código y nombre deben ser únicos."
)
def crear_estado_mision(body: EstadoMisionCreate):
    """
    Crea un nuevo estado de misión.

    Validaciones:
    - **codigo**: Obligatorio, único, sin espacios, se guarda en mayúsculas
    - **nombre**: Obligatorio, único
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
        message="Estado de misión creado exitosamente"
    )


# ──────────────────────────────────────────────
# GET - Listar todos sin paginación (ANTES de la ruta con parámetro)
# ──────────────────────────────────────────────

@router.get(
    "/todos/lista",
    summary="Listar todos los estados de misión (sin paginación)",
    description="Lista todos los estados de misión activos. Ideal para dropdowns o selects."
)
def listar_todos_estados_mision(
    codigo: Optional[str] = Query(None, description="Filtrar por código"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre"),
    busqueda: Optional[str] = Query(None, description="Búsqueda general")
):
    """Lista todos los estados de misión activos sin paginación."""
    resultado = service.listar_todos(
        codigo=codigo,
        nombre=nombre,
        busqueda=busqueda
    )

    if "error" in resultado:
        return internal_error_response(detail=resultado["error"])

    return success_response(
        data=resultado["data"],
        message="Listado completo de estados de misión obtenido exitosamente"
    )


# ──────────────────────────────────────────────
# GET - Obtener por ID
# ──────────────────────────────────────────────

@router.get(
    "/{id_estado_mision}",
    summary="Obtener estado de misión por ID",
    description="Obtiene un estado de misión por su ID. Solo registros activos."
)
def obtener_estado_mision(id_estado_mision: int):
    """Obtiene un estado de misión específico por su ID."""
    resultado = service.obtener_por_id(id_estado_mision)

    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404:
            return not_found_response(resultado["error"])
        return internal_error_response(detail=resultado["error"])

    return success_response(
        data=resultado["data"],
        message="Estado de misión obtenido exitosamente"
    )


# ──────────────────────────────────────────────
# GET - Listar con paginación y filtros
# ──────────────────────────────────────────────

@router.get(
    "/",
    summary="Listar estados de misión (paginado)",
    description="Lista estados de misión con paginación y filtros opcionales."
)
def listar_estados_mision(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(10, ge=1, le=100, description="Registros por página"),
    codigo: Optional[str] = Query(None, description="Filtrar por código (búsqueda parcial)"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre (búsqueda parcial)"),
    busqueda: Optional[str] = Query(None, description="Búsqueda general en código, nombre y descripción")
):
    """
    Lista estados de misión con paginación.

    Filtros disponibles:
    - **codigo**: Búsqueda parcial por código
    - **nombre**: Búsqueda parcial por nombre
    - **busqueda**: Búsqueda en código, nombre y descripción
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
        message="Listado de estados de misión obtenido exitosamente"
    )


# ──────────────────────────────────────────────
# PUT - Actualizar
# ──────────────────────────────────────────────

@router.put(
    "/{id_estado_mision}",
    summary="Actualizar estado de misión",
    description="Actualiza un estado de misión existente. Solo se actualizan los campos enviados."
)
def actualizar_estado_mision(id_estado_mision: int, body: EstadoMisionUpdate):
    """
    Actualiza un estado de misión.

    Validaciones:
    - Registro debe existir y estar activo
    - Si se cambia el código, debe ser único
    - Si se cambia el nombre, debe ser único
    """
    resultado = service.actualizar(id_estado_mision, body.model_dump(exclude_none=True))

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
        message="Estado de misión actualizado exitosamente"
    )


# ──────────────────────────────────────────────
# DELETE - Eliminar (soft delete)
# ──────────────────────────────────────────────

@router.delete(
    "/{id_estado_mision}",
    summary="Eliminar estado de misión",
    description="Eliminación lógica. No se permite si tiene misiones activas asociadas."
)
def eliminar_estado_mision(id_estado_mision: int):
    """
    Elimina lógicamente un estado de misión.

    Validaciones:
    - Registro debe existir y estar activo
    - No debe tener misiones activas asociadas
    """
    resultado = service.eliminar(id_estado_mision)

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
        message="Estado de misión eliminado exitosamente"
    )