# routers/departamento_router.py
"""Endpoints para Departamento. CRUD completo con jerarquía."""

from fastapi import APIRouter, Query
from typing import Optional

from models.departamento_model import DepartamentoCreate, DepartamentoUpdate
from services.departamento_service import DepartamentoService
from utils.response_handler import (
    success_response, created_response, error_response,
    not_found_response, conflict_response, internal_error_response,
)

router = APIRouter(
    prefix="/departamento",
    tags=["Departamento"],
    responses={404: {"description": "No encontrado"}, 409: {"description": "Conflicto"}, 500: {"description": "Error interno"}}
)

service = DepartamentoService()


@router.post("/", summary="Crear departamento")
def crear_departamento(body: DepartamentoCreate):
    """
    Crea un nuevo departamento.

    Validaciones:
    - **codigo**: Obligatorio, único, sin espacios, mayúsculas
    - **nombre**: Obligatorio
    - **departamentoPadreId**: Si se envía, debe existir y estar activo
    - **idPerfilJefe**: Si se envía, debe existir y estar activo
    """
    resultado = service.crear(body.model_dump())
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 409: return conflict_response(resultado["error"])
        if status == 500: return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)
    return created_response(data=resultado["data"], message="Departamento creado exitosamente")


@router.get("/todos/lista", summary="Listar todos los departamentos (sin paginación)")
def listar_todos_departamentos(
    codigo: Optional[str] = Query(None, description="Filtrar por código"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre"),
    nivel_jerarquico: Optional[int] = Query(None, alias="nivelJerarquico", description="Filtrar por nivel jerárquico"),
    id_padre: Optional[int] = Query(None, alias="departamentoPadreId", description="Filtrar por departamento padre"),
    busqueda: Optional[str] = Query(None, description="Búsqueda general")
):
    """Lista todos los departamentos activos sin paginación. Ordenado por nivel jerárquico."""
    resultado = service.listar_todos(
        codigo=codigo, nombre=nombre, nivel_jerarquico=nivel_jerarquico,
        id_padre=id_padre, busqueda=busqueda
    )
    if "error" in resultado: return internal_error_response(detail=resultado["error"])
    return success_response(data=resultado["data"], message="Listado completo de departamentos obtenido exitosamente")


@router.get("/{id_departamento}", summary="Obtener departamento por ID")
def obtener_departamento(id_departamento: int):
    """Obtiene un departamento específico con el nombre de su departamento padre."""
    resultado = service.obtener_por_id(id_departamento)
    if "error" in resultado:
        if resultado.get("status") == 404: return not_found_response(resultado["error"])
        return internal_error_response(detail=resultado["error"])
    return success_response(data=resultado["data"], message="Departamento obtenido exitosamente")


@router.get("/", summary="Listar departamentos (paginado)")
def listar_departamentos(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(10, ge=1, le=100, description="Registros por página"),
    codigo: Optional[str] = Query(None, description="Filtrar por código"),
    nombre: Optional[str] = Query(None, description="Filtrar por nombre"),
    nivel_jerarquico: Optional[int] = Query(None, alias="nivelJerarquico", description="Filtrar por nivel"),
    id_padre: Optional[int] = Query(None, alias="departamentoPadreId", description="Filtrar por padre"),
    busqueda: Optional[str] = Query(None, description="Búsqueda general")
):
    """
    Lista departamentos con paginación y filtros.

    Filtros disponibles:
    - **codigo**: Búsqueda parcial
    - **nombre**: Búsqueda parcial
    - **nivelJerarquico**: Filtro exacto por nivel
    - **departamentoPadreId**: Filtro por departamento padre
    - **busqueda**: Búsqueda en código, nombre, jefe y ubicación
    """
    resultado = service.listar(
        pagina=pagina, por_pagina=por_pagina, codigo=codigo, nombre=nombre,
        nivel_jerarquico=nivel_jerarquico, id_padre=id_padre, busqueda=busqueda
    )
    if "error" in resultado: return internal_error_response(detail=resultado["error"])
    return success_response(data=resultado["data"], message="Listado de departamentos obtenido exitosamente")


@router.put("/{id_departamento}", summary="Actualizar departamento")
def actualizar_departamento(id_departamento: int, body: DepartamentoUpdate):
    """
    Actualiza un departamento existente.

    Validaciones:
    - Registro debe existir y estar activo
    - Si se cambia el código, debe ser único
    - Si se cambia el padre, debe existir y no crear referencia circular
    - Si se cambia el jefe, el perfil debe existir
    """
    resultado = service.actualizar(id_departamento, body.model_dump(exclude_none=True))
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404: return not_found_response(resultado["error"])
        if status == 409: return conflict_response(resultado["error"])
        if status == 500: return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)
    return success_response(data=resultado["data"], message="Departamento actualizado exitosamente")


@router.delete("/{id_departamento}", summary="Eliminar departamento")
def eliminar_departamento(id_departamento: int):
    """
    Elimina lógicamente un departamento.

    Validaciones:
    - Registro debe existir y estar activo
    - No debe tener subdepartamentos activos
    - No debe tener solicitudes activas
    - No debe tener vehículos asignados activos
    - No debe tener motoristas asignados activos
    """
    resultado = service.eliminar(id_departamento)
    if "error" in resultado:
        status = resultado.get("status", 400)
        if status == 404: return not_found_response(resultado["error"])
        if status == 409: return conflict_response(resultado["error"])
        if status == 500: return internal_error_response(detail=resultado["error"])
        return error_response(resultado["error"], status_code=status)
    return success_response(data=resultado["data"], message="Departamento eliminado exitosamente")