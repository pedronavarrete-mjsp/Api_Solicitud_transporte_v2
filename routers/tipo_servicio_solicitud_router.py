# routers/tipo_servicio_solicitud_router.py
"""
Endpoints para TipoServicioSolicitud.
CRUD completo. Nota: solo tiene campo Nombre (sin Codigo).
"""

from fastapi import APIRouter, Query
from typing import Optional

from models.tipo_servicio_solicitud_model import TipoServicioSolicitudCreate, TipoServicioSolicitudUpdate
from services.tipo_servicio_solicitud_service import TipoServicioSolicitudService
from utils.response_handler import (
    success_response, created_response, error_response,
    not_found_response, conflict_response, internal_error_response,
)

router = APIRouter(
    prefix="/tipo-servicio-solicitud",
    tags=["Tipo de Servicio de Solicitud"],
    responses={404: {"description": "No encontrado"}, 409: {"description": "Conflicto"}, 500: {"description": "Error interno"}}
)

service = TipoServicioSolicitudService()


@router.post("/", summary="Crear tipo de servicio de solicitud")
def crear_tipo_servicio(body: TipoServicioSolicitudCreate):
    """
    Crea un nuevo tipo de servicio de solicitud.

    Validaciones:
    - **nombre**: Obligatorio, único, máximo 50 caracteres
    """
    resultado = service.crear(body.model_dump())
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 409: return conflict_response(resultado["error"])
        if status == 500: return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)
    return created_response(data=resultado["data"], message="Tipo de servicio creado exitosamente")


@router.get("/todos/lista", summary="Listar todos los tipos de servicio (sin paginación)")
def listar_todos_tipos_servicio(
    nombre: Optional[str] = Query(None, description="Filtrar por nombre"),
    busqueda: Optional[str] = Query(None, description="Búsqueda general")
):
    """Lista todos los tipos de servicio activos sin paginación. Ideal para dropdowns."""
    resultado = service.listar_todos(nombre=nombre, busqueda=busqueda)
    if "error" in resultado: return internal_error_response(detail=resultado["error"])
    return success_response(data=resultado["data"], message="Listado completo de tipos de servicio obtenido exitosamente")


@router.get("/{id_tipo_servicio}", summary="Obtener tipo de servicio por ID")
def obtener_tipo_servicio(id_tipo_servicio: int):
    """Obtiene un tipo de servicio específico por su ID."""
    resultado = service.obtener_por_id(id_tipo_servicio)
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404: return not_found_response(resultado["error"])
        return internal_error_response(detail=resultado["error"])
    return success_response(data=resultado["data"], message="Tipo de servicio obtenido exitosamente")


@router.get("/", summary="Listar tipos de servicio (paginado)")
def listar_tipos_servicio(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(10, ge=1, le=100, description="Registros por página"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre (búsqueda parcial)"),
    busqueda: Optional[str] = Query(None, description="Búsqueda general en nombre")
):
    """Lista tipos de servicio con paginación y filtros."""
    resultado = service.listar(pagina=pagina, por_pagina=por_pagina, nombre=nombre, busqueda=busqueda)
    if "error" in resultado: return internal_error_response(detail=resultado["error"])
    return success_response(data=resultado["data"], message="Listado de tipos de servicio obtenido exitosamente")


@router.put("/{id_tipo_servicio}", summary="Actualizar tipo de servicio")
def actualizar_tipo_servicio(id_tipo_servicio: int, body: TipoServicioSolicitudUpdate):
    """
    Actualiza un tipo de servicio existente.

    Validaciones:
    - Registro debe existir y estar activo
    - Si se cambia el nombre, debe ser único
    """
    resultado = service.actualizar(id_tipo_servicio, body.model_dump(exclude_none=True))
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404: return not_found_response(resultado["error"])
        if status == 409: return conflict_response(resultado["error"])
        if status == 500: return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)
    return success_response(data=resultado["data"], message="Tipo de servicio actualizado exitosamente")


@router.delete("/{id_tipo_servicio}", summary="Eliminar tipo de servicio")
def eliminar_tipo_servicio(id_tipo_servicio: int):
    """
    Elimina lógicamente un tipo de servicio.

    Validaciones:
    - Registro debe existir y estar activo
    - No debe tener solicitudes activas asociadas
    """
    resultado = service.eliminar(id_tipo_servicio)
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404: return not_found_response(resultado["error"])
        if status == 409: return conflict_response(resultado["error"])
        if status == 500: return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)
    return success_response(data=resultado["data"], message="Tipo de servicio eliminado exitosamente")