# routers/clase_vehiculo_router.py
"""
Endpoints para ClaseVehiculo.
CRUD completo con validaciones y respuestas estandarizadas en español.
"""

from fastapi import APIRouter, Query
from typing import Optional

from models.clase_vehiculo_model import (
    ClaseVehiculoCreate,
    ClaseVehiculoUpdate,
)
from services.clase_vehiculo_service import ClaseVehiculoService
from utils.response_handler import (
    success_response,
    created_response,
    error_response,
    not_found_response,
    conflict_response,
    internal_error_response,
)

router = APIRouter(
    prefix="/clase-vehiculo",
    tags=["Clase de Vehículo"],
    responses={
        404: {"description": "No encontrado"},
        409: {"description": "Conflicto - Registro duplicado"},
        500: {"description": "Error interno del servidor"},
    }
)

service = ClaseVehiculoService()


# ──────────────────────────────────────────────
# POST - Crear
# ──────────────────────────────────────────────

@router.post(
    "/",
    summary="Crear clase de vehículo",
    description="Crea una nueva clase de vehículo. El código y nombre deben ser únicos."
)
def crear_clase_vehiculo(body: ClaseVehiculoCreate):
    """
    Crea una nueva clase de vehículo.

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
        message="Clase de vehículo creada exitosamente"
    )


# ──────────────────────────────────────────────
# GET - Obtener por ID
# ──────────────────────────────────────────────

@router.get(
    "/{id_clase_vehiculo}",
    summary="Obtener clase de vehículo por ID",
    description="Obtiene una clase de vehículo por su ID. Solo registros activos."
)
def obtener_clase_vehiculo(id_clase_vehiculo: int):
    """Obtiene una clase de vehículo específica por su ID."""
    resultado = service.obtener_por_id(id_clase_vehiculo)

    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404:
            return not_found_response(resultado["error"])
        return internal_error_response(detail=resultado["error"])

    return success_response(
        data=resultado["data"],
        message="Clase de vehículo obtenida exitosamente"
    )


# ──────────────────────────────────────────────
# GET - Listar con paginación y filtros
# ──────────────────────────────────────────────

@router.get(
    "/",
    summary="Listar clases de vehículo (paginado)",
    description="Lista clases de vehículo con paginación y filtros opcionales."
)
def listar_clases_vehiculo(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(10, ge=1, le=100, description="Registros por página"),
    codigo: Optional[str] = Query(None, description="Filtrar por código (búsqueda parcial)"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre (búsqueda parcial)"),
    busqueda: Optional[str] = Query(None, description="Búsqueda general en código, nombre y descripción")
):
    """
    Lista clases de vehículo con paginación.

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
        message="Listado de clases de vehículo obtenido exitosamente"
    )


# ──────────────────────────────────────────────
# GET - Listar todos sin paginación (para selects/dropdowns)
# ──────────────────────────────────────────────

@router.get(
    "/todos/lista",
    summary="Listar todas las clases de vehículo (sin paginación)",
    description="Lista todas las clases de vehículo activas. Ideal para dropdowns o selects."
)
def listar_todas_clases_vehiculo(
    codigo: Optional[str] = Query(None, description="Filtrar por código"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre"),
    busqueda: Optional[str] = Query(None, description="Búsqueda general")
):
    """Lista todas las clases de vehículo activas sin paginación."""
    resultado = service.listar_todos(
        codigo=codigo,
        nombre=nombre,
        busqueda=busqueda
    )

    if "error" in resultado:
        return internal_error_response(detail=resultado["error"])

    return success_response(
        data=resultado["data"],
        message="Listado completo de clases de vehículo obtenido exitosamente"
    )


# ──────────────────────────────────────────────
# PUT - Actualizar
# ──────────────────────────────────────────────

@router.put(
    "/{id_clase_vehiculo}",
    summary="Actualizar clase de vehículo",
    description="Actualiza una clase de vehículo existente. Solo se actualizan los campos enviados."
)
def actualizar_clase_vehiculo(id_clase_vehiculo: int, body: ClaseVehiculoUpdate):
    """
    Actualiza una clase de vehículo.

    Validaciones:
    - Registro debe existir y estar activo
    - Si se cambia el código, debe ser único
    - Si se cambia el nombre, debe ser único
    """
    resultado = service.actualizar(id_clase_vehiculo, body.model_dump(exclude_none=True))

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
        message="Clase de vehículo actualizada exitosamente"
    )


# ──────────────────────────────────────────────
# DELETE - Eliminar (soft delete)
# ──────────────────────────────────────────────

@router.delete(
    "/{id_clase_vehiculo}",
    summary="Eliminar clase de vehículo",
    description="Eliminación lógica. No se permite si tiene vehículos asociados activos."
)
def eliminar_clase_vehiculo(id_clase_vehiculo: int):
    """
    Elimina lógicamente una clase de vehículo.

    Validaciones:
    - Registro debe existir y estar activo
    - No debe tener vehículos asociados activos
    """
    resultado = service.eliminar(id_clase_vehiculo)

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
        message="Clase de vehículo eliminada exitosamente"
    )