# routers/estado_vehiculo_router.py
"""
Endpoints para EstadoVehiculo.
CRUD completo con validaciones y respuestas estandarizadas en español.
Incluye filtro por PermiteAsignacion.
"""

from fastapi import APIRouter, Query
from typing import Optional

from models.estado_vehiculo_model import (
    EstadoVehiculoCreate,
    EstadoVehiculoUpdate,
)
from services.estado_vehiculo_service import EstadoVehiculoService
from utils.response_handler import (
    success_response,
    created_response,
    error_response,
    not_found_response,
    conflict_response,
    internal_error_response,
)

router = APIRouter(
    prefix="/estado-vehiculo",
    tags=["Estado de Vehículo"],
    responses={
        404: {"description": "No encontrado"},
        409: {"description": "Conflicto - Registro duplicado"},
        500: {"description": "Error interno del servidor"},
    }
)

service = EstadoVehiculoService()


# ──────────────────────────────────────────────
# POST - Crear
# ──────────────────────────────────────────────

@router.post(
    "/",
    summary="Crear estado de vehículo",
    description="Crea un nuevo estado de vehículo. El código y nombre deben ser únicos."
)
def crear_estado_vehiculo(body: EstadoVehiculoCreate):
    """
    Crea un nuevo estado de vehículo.

    Validaciones:
    - **codigo**: Obligatorio, único, sin espacios, mayúsculas
    - **nombre**: Obligatorio, único
    - **permiteAsignacion**: Obligatorio, define si permite asignar vehículos en este estado
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
        message="Estado de vehículo creado exitosamente"
    )


# ──────────────────────────────────────────────
# GET - Listar todos sin paginación
# ──────────────────────────────────────────────

@router.get(
    "/todos/lista",
    summary="Listar todos los estados de vehículo (sin paginación)",
    description="Lista todos los estados de vehículo activos. Ideal para dropdowns o selects."
)
def listar_todos_estados_vehiculo(
    codigo: Optional[str] = Query(None, description="Filtrar por código"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre"),
    permite_asignacion: Optional[bool] = Query(None, alias="permiteAsignacion", description="Filtrar por si permite asignación"),
    busqueda: Optional[str] = Query(None, description="Búsqueda general")
):
    """Lista todos los estados de vehículo activos sin paginación."""
    resultado = service.listar_todos(
        codigo=codigo,
        nombre=nombre,
        permite_asignacion=permite_asignacion,
        busqueda=busqueda
    )

    if "error" in resultado:
        return internal_error_response(detail=resultado["error"])

    return success_response(
        data=resultado["data"],
        message="Listado completo de estados de vehículo obtenido exitosamente"
    )


# ──────────────────────────────────────────────
# GET - Obtener por ID
# ──────────────────────────────────────────────

@router.get(
    "/{id_estado_vehiculo}",
    summary="Obtener estado de vehículo por ID",
    description="Obtiene un estado de vehículo por su ID. Solo registros activos."
)
def obtener_estado_vehiculo(id_estado_vehiculo: int):
    """Obtiene un estado de vehículo específico por su ID."""
    resultado = service.obtener_por_id(id_estado_vehiculo)

    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404:
            return not_found_response(resultado["error"])
        return internal_error_response(detail=resultado["error"])

    return success_response(
        data=resultado["data"],
        message="Estado de vehículo obtenido exitosamente"
    )


# ──────────────────────────────────────────────
# GET - Listar con paginación y filtros
# ──────────────────────────────────────────────

@router.get(
    "/",
    summary="Listar estados de vehículo (paginado)",
    description="Lista estados de vehículo con paginación y filtros opcionales."
)
def listar_estados_vehiculo(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(10, ge=1, le=100, description="Registros por página"),
    codigo: Optional[str] = Query(None, description="Filtrar por código (búsqueda parcial)"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre (búsqueda parcial)"),
    permite_asignacion: Optional[bool] = Query(None, alias="permiteAsignacion", description="Filtrar por si permite asignación"),
    busqueda: Optional[str] = Query(None, description="Búsqueda general en código, nombre y descripción")
):
    """
    Lista estados de vehículo con paginaci��n.

    Filtros disponibles:
    - **codigo**: Búsqueda parcial por código
    - **nombre**: Búsqueda parcial por nombre
    - **permiteAsignacion**: Filtrar por si permite asignación (true/false)
    - **busqueda**: Búsqueda en código, nombre y descripción
    """
    resultado = service.listar(
        pagina=pagina,
        por_pagina=por_pagina,
        codigo=codigo,
        nombre=nombre,
        permite_asignacion=permite_asignacion,
        busqueda=busqueda
    )

    if "error" in resultado:
        return internal_error_response(detail=resultado["error"])

    return success_response(
        data=resultado["data"],
        message="Listado de estados de vehículo obtenido exitosamente"
    )


# ──────────────────────────────────────────────
# PUT - Actualizar
# ──────────────────────────────────────────────

@router.put(
    "/{id_estado_vehiculo}",
    summary="Actualizar estado de vehículo",
    description="Actualiza un estado de vehículo existente. Solo se actualizan los campos enviados."
)
def actualizar_estado_vehiculo(id_estado_vehiculo: int, body: EstadoVehiculoUpdate):
    """
    Actualiza un estado de vehículo.

    Validaciones:
    - Registro debe existir y estar activo
    - Si se cambia el código, debe ser único
    - Si se cambia el nombre, debe ser único
    """
    resultado = service.actualizar(id_estado_vehiculo, body.model_dump(exclude_none=True))

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
        message="Estado de vehículo actualizado exitosamente"
    )


# ──────────────────────────────────────────────
# DELETE - Eliminar (soft delete)
# ──────────────────────────────────────────────

@router.delete(
    "/{id_estado_vehiculo}",
    summary="Eliminar estado de vehículo",
    description="Eliminación lógica. No se permite si tiene vehículos activos asociados."
)
def eliminar_estado_vehiculo(id_estado_vehiculo: int):
    """
    Elimina lógicamente un estado de vehículo.

    Validaciones:
    - Registro debe existir y estar activo
    - No debe tener vehículos activos asociados
    """
    resultado = service.eliminar(id_estado_vehiculo)

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
        message="Estado de vehículo eliminado exitosamente"
    )