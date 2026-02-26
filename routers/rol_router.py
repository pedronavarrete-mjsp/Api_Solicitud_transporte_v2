# routers/rol_router.py
"""Endpoints para Rol. CRUD completo."""

from fastapi import APIRouter, Query
from typing import Optional

from models.rol_model import RolCreate, RolUpdate
from services.rol_service import RolService
from utils.response_handler import (
    success_response, created_response, error_response,
    not_found_response, conflict_response, internal_error_response,
)

router = APIRouter(
    prefix="/rol",
    tags=["Rol"],
    responses={404: {"description": "No encontrado"}, 409: {"description": "Conflicto"}, 500: {"description": "Error interno"}}
)

service = RolService()


@router.post("/", summary="Crear rol")
def crear_rol(body: RolCreate):
    resultado = service.crear(body.model_dump())
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 409: return conflict_response(resultado["error"])
        if status == 500: return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)
    return created_response(data=resultado["data"], message="Rol creado exitosamente")


@router.get("/todos/lista", summary="Listar todos los roles (sin paginación)")
def listar_todos_roles(
    codigo: Optional[str] = Query(None), nombre: Optional[str] = Query(None),
    busqueda: Optional[str] = Query(None)
):
    resultado = service.listar_todos(codigo=codigo, nombre=nombre, busqueda=busqueda)
    if "error" in resultado: return internal_error_response(detail=resultado["error"])
    return success_response(data=resultado["data"], message="Listado completo de roles obtenido exitosamente")


@router.get("/{id_rol}", summary="Obtener rol por ID")
def obtener_rol(id_rol: int):
    resultado = service.obtener_por_id(id_rol)
    if "error" in resultado:
        if resultado.get("status") == 404: return not_found_response(resultado["error"])
        return internal_error_response(detail=resultado["error"])
    return success_response(data=resultado["data"], message="Rol obtenido exitosamente")


@router.get("/", summary="Listar roles (paginado)")
def listar_roles(
    pagina: int = Query(1, ge=1), por_pagina: int = Query(10, ge=1, le=100),
    codigo: Optional[str] = Query(None), nombre: Optional[str] = Query(None),
    busqueda: Optional[str] = Query(None)
):
    resultado = service.listar(pagina=pagina, por_pagina=por_pagina, codigo=codigo, nombre=nombre, busqueda=busqueda)
    if "error" in resultado: return internal_error_response(detail=resultado["error"])
    return success_response(data=resultado["data"], message="Listado de roles obtenido exitosamente")


@router.put("/{id_rol}", summary="Actualizar rol")
def actualizar_rol(id_rol: int, body: RolUpdate):
    resultado = service.actualizar(id_rol, body.model_dump(exclude_none=True))
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404: return not_found_response(resultado["error"])
        if status == 409: return conflict_response(resultado["error"])
        if status == 500: return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)
    return success_response(data=resultado["data"], message="Rol actualizado exitosamente")


@router.delete("/{id_rol}", summary="Eliminar rol")
def eliminar_rol(id_rol: int):
    resultado = service.eliminar(id_rol)
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404: return not_found_response(resultado["error"])
        if status == 409: return conflict_response(resultado["error"])
        if status == 500: return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)
    return success_response(data=resultado["data"], message="Rol eliminado exitosamente")