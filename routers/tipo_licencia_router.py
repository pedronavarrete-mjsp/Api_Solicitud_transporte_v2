# routers/tipo_licencia_router.py
"""
Endpoints para TipoLicencia.
CRUD completo con validaciones y respuestas estandarizadas en español.
"""

from fastapi import APIRouter, Query
from typing import Optional

from models.tipo_licencia_model import TipoLicenciaCreate, TipoLicenciaUpdate
from services.tipo_licencia_service import TipoLicenciaService
from utils.response_handler import (
    success_response, created_response, error_response,
    not_found_response, conflict_response, internal_error_response,
)

router = APIRouter(
    prefix="/tipo-licencia",
    tags=["Tipo de Licencia"],
    responses={404: {"description": "No encontrado"}, 409: {"description": "Conflicto"}, 500: {"description": "Error interno"}}
)

service = TipoLicenciaService()


@router.post("/", summary="Crear tipo de licencia")
def crear_tipo_licencia(body: TipoLicenciaCreate):
    resultado = service.crear(body.model_dump())
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 409: return conflict_response(resultado["error"])
        if status == 500: return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)
    return created_response(data=resultado["data"], message="Tipo de licencia creado exitosamente")


@router.get("/todos/lista", summary="Listar todos los tipos de licencia (sin paginación)")
def listar_todos_tipos_licencia(
    codigo: Optional[str] = Query(None), nombre: Optional[str] = Query(None),
    busqueda: Optional[str] = Query(None)
):
    resultado = service.listar_todos(codigo=codigo, nombre=nombre, busqueda=busqueda)
    if "error" in resultado: return internal_error_response(detail=resultado["error"])
    return success_response(data=resultado["data"], message="Listado completo de tipos de licencia obtenido exitosamente")


@router.get("/{id_tipo_licencia}", summary="Obtener tipo de licencia por ID")
def obtener_tipo_licencia(id_tipo_licencia: int):
    resultado = service.obtener_por_id(id_tipo_licencia)
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404: return not_found_response(resultado["error"])
        return internal_error_response(detail=resultado["error"])
    return success_response(data=resultado["data"], message="Tipo de licencia obtenido exitosamente")


@router.get("/", summary="Listar tipos de licencia (paginado)")
def listar_tipos_licencia(
    pagina: int = Query(1, ge=1), por_pagina: int = Query(10, ge=1, le=100),
    codigo: Optional[str] = Query(None), nombre: Optional[str] = Query(None),
    busqueda: Optional[str] = Query(None)
):
    resultado = service.listar(pagina=pagina, por_pagina=por_pagina, codigo=codigo, nombre=nombre, busqueda=busqueda)
    if "error" in resultado: return internal_error_response(detail=resultado["error"])
    return success_response(data=resultado["data"], message="Listado de tipos de licencia obtenido exitosamente")


@router.put("/{id_tipo_licencia}", summary="Actualizar tipo de licencia")
def actualizar_tipo_licencia(id_tipo_licencia: int, body: TipoLicenciaUpdate):
    resultado = service.actualizar(id_tipo_licencia, body.model_dump(exclude_none=True))
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404: return not_found_response(resultado["error"])
        if status == 409: return conflict_response(resultado["error"])
        if status == 500: return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)
    return success_response(data=resultado["data"], message="Tipo de licencia actualizado exitosamente")


@router.delete("/{id_tipo_licencia}", summary="Eliminar tipo de licencia")
def eliminar_tipo_licencia(id_tipo_licencia: int):
    resultado = service.eliminar(id_tipo_licencia)
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404: return not_found_response(resultado["error"])
        if status == 409: return conflict_response(resultado["error"])
        if status == 500: return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)
    return success_response(data=resultado["data"], message="Tipo de licencia eliminado exitosamente")