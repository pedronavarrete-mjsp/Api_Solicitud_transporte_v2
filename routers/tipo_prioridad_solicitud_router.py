# routers/tipo_prioridad_solicitud_router.py
"""
Endpoints para TipoPrioridadSolicitud.
CRUD completo. Nota: solo tiene campo Nombre (sin Codigo).
"""

from fastapi import APIRouter, Query
from typing import Optional

from models.tipo_prioridad_solicitud_model import TipoPrioridadSolicitudCreate, TipoPrioridadSolicitudUpdate
from services.tipo_prioridad_solicitud_service import TipoPrioridadSolicitudService
from utils.response_handler import (
    success_response, created_response, error_response,
    not_found_response, conflict_response, internal_error_response,
)

router = APIRouter(
    prefix="/tipo-prioridad-solicitud",
    tags=["Tipo de Prioridad de Solicitud"],
    responses={404: {"description": "No encontrado"}, 409: {"description": "Conflicto"}, 500: {"description": "Error interno"}}
)

service = TipoPrioridadSolicitudService()


@router.post("/", summary="Crear tipo de prioridad de solicitud")
def crear_tipo_prioridad(body: TipoPrioridadSolicitudCreate):
    resultado = service.crear(body.model_dump())
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 409: return conflict_response(resultado["error"])
        if status == 500: return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)
    return created_response(data=resultado["data"], message="Tipo de prioridad creado exitosamente")


@router.get("/todos/lista", summary="Listar todos los tipos de prioridad (sin paginación)")
def listar_todos_tipos_prioridad(
    nombre: Optional[str] = Query(None), busqueda: Optional[str] = Query(None)
):
    resultado = service.listar_todos(nombre=nombre, busqueda=busqueda)
    if "error" in resultado: return internal_error_response(detail=resultado["error"])
    return success_response(data=resultado["data"], message="Listado completo de tipos de prioridad obtenido exitosamente")


@router.get("/{id_tipo_prioridad}", summary="Obtener tipo de prioridad por ID")
def obtener_tipo_prioridad(id_tipo_prioridad: int):
    resultado = service.obtener_por_id(id_tipo_prioridad)
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404: return not_found_response(resultado["error"])
        return internal_error_response(detail=resultado["error"])
    return success_response(data=resultado["data"], message="Tipo de prioridad obtenido exitosamente")


@router.get("/", summary="Listar tipos de prioridad (paginado)")
def listar_tipos_prioridad(
    pagina: int = Query(1, ge=1), por_pagina: int = Query(10, ge=1, le=100),
    nombre: Optional[str] = Query(None), busqueda: Optional[str] = Query(None)
):
    resultado = service.listar(pagina=pagina, por_pagina=por_pagina, nombre=nombre, busqueda=busqueda)
    if "error" in resultado: return internal_error_response(detail=resultado["error"])
    return success_response(data=resultado["data"], message="Listado de tipos de prioridad obtenido exitosamente")


@router.put("/{id_tipo_prioridad}", summary="Actualizar tipo de prioridad")
def actualizar_tipo_prioridad(id_tipo_prioridad: int, body: TipoPrioridadSolicitudUpdate):
    resultado = service.actualizar(id_tipo_prioridad, body.model_dump(exclude_none=True))
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404: return not_found_response(resultado["error"])
        if status == 409: return conflict_response(resultado["error"])
        if status == 500: return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)
    return success_response(data=resultado["data"], message="Tipo de prioridad actualizado exitosamente")


@router.delete("/{id_tipo_prioridad}", summary="Eliminar tipo de prioridad")
def eliminar_tipo_prioridad(id_tipo_prioridad: int):
    resultado = service.eliminar(id_tipo_prioridad)
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404: return not_found_response(resultado["error"])
        if status == 409: return conflict_response(resultado["error"])
        if status == 500: return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)
    return success_response(data=resultado["data"], message="Tipo de prioridad eliminado exitosamente")