# routers/lugar_router.py
"""Endpoints para Lugares. CRUD completo con filtros especiales."""

from fastapi import APIRouter, Query
from typing import Optional

from models.lugar_model import LugarCreate, LugarUpdate
from services.lugar_service import LugarService
from utils.response_handler import (
    success_response, created_response, error_response,
    not_found_response, conflict_response, internal_error_response,
)

router = APIRouter(
    prefix="/lugar",
    tags=["Lugares"],
    responses={404: {"description": "No encontrado"}, 409: {"description": "Conflicto"}, 500: {"description": "Error interno"}}
)

service = LugarService()


@router.post("/", summary="Crear lugar")
def crear_lugar(body: LugarCreate):
    resultado = service.crear(body.model_dump())
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 409: return conflict_response(resultado["error"])
        if status == 500: return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)
    return created_response(data=resultado["data"], message="Lugar creado exitosamente")


@router.get("/todos/lista", summary="Listar todos los lugares (sin paginación)")
def listar_todos_lugares(
    codigo: Optional[str] = Query(None), nombre: Optional[str] = Query(None),
    tipo_lugar: Optional[str] = Query(None, alias="tipoLugar"),
    es_punto_frecuente: Optional[bool] = Query(None, alias="esPuntoFrecuente"),
    busqueda: Optional[str] = Query(None)
):
    resultado = service.listar_todos(codigo=codigo, nombre=nombre, tipo_lugar=tipo_lugar,
                                     es_punto_frecuente=es_punto_frecuente, busqueda=busqueda)
    if "error" in resultado: return internal_error_response(detail=resultado["error"])
    return success_response(data=resultado["data"], message="Listado completo de lugares obtenido exitosamente")


@router.get("/{id_lugar}", summary="Obtener lugar por ID")
def obtener_lugar(id_lugar: int):
    resultado = service.obtener_por_id(id_lugar)
    if "error" in resultado:
        if resultado.get("status") == 404: return not_found_response(resultado["error"])
        return internal_error_response(detail=resultado["error"])
    return success_response(data=resultado["data"], message="Lugar obtenido exitosamente")


@router.get("/", summary="Listar lugares (paginado)")
def listar_lugares(
    pagina: int = Query(1, ge=1), por_pagina: int = Query(10, ge=1, le=100),
    codigo: Optional[str] = Query(None), nombre: Optional[str] = Query(None),
    tipo_lugar: Optional[str] = Query(None, alias="tipoLugar"),
    es_punto_frecuente: Optional[bool] = Query(None, alias="esPuntoFrecuente"),
    busqueda: Optional[str] = Query(None)
):
    resultado = service.listar(pagina=pagina, por_pagina=por_pagina, codigo=codigo, nombre=nombre,
                               tipo_lugar=tipo_lugar, es_punto_frecuente=es_punto_frecuente, busqueda=busqueda)
    if "error" in resultado: return internal_error_response(detail=resultado["error"])
    return success_response(data=resultado["data"], message="Listado de lugares obtenido exitosamente")


@router.put("/{id_lugar}", summary="Actualizar lugar")
def actualizar_lugar(id_lugar: int, body: LugarUpdate):
    resultado = service.actualizar(id_lugar, body.model_dump(exclude_none=True))
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404: return not_found_response(resultado["error"])
        if status == 409: return conflict_response(resultado["error"])
        if status == 500: return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)
    return success_response(data=resultado["data"], message="Lugar actualizado exitosamente")


@router.delete("/{id_lugar}", summary="Eliminar lugar")
def eliminar_lugar(id_lugar: int):
    resultado = service.eliminar(id_lugar)
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404: return not_found_response(resultado["error"])
        if status == 409: return conflict_response(resultado["error"])
        if status == 500: return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)
    return success_response(data=resultado["data"], message="Lugar eliminado exitosamente")