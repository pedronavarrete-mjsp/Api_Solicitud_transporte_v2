# models/rol_model.py
"""
Modelos Pydantic para Rol.
Schemas de request (crear/actualizar) y response.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


class RolCreate(BaseModel):
    """Schema para crear un nuevo rol"""
    codigo: str = Field(..., min_length=1, max_length=50, description="Código único del rol")
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre del rol")

    @field_validator("codigo")
    @classmethod
    def codigo_sin_espacios(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("El código no puede estar vacío")
        if " " in v:
            raise ValueError("El código no debe contener espacios, use guion bajo (_) como separador")
        return v

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El nombre no puede estar vacío")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "codigo": "ADMIN",
                "nombre": "Administrador"
            }
        }


class RolUpdate(BaseModel):
    """Schema para actualizar un rol existente"""
    codigo: Optional[str] = Field(None, min_length=1, max_length=50)
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)

    @field_validator("codigo")
    @classmethod
    def codigo_sin_espacios(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip().upper()
            if not v:
                raise ValueError("El código no puede estar vacío")
            if " " in v:
                raise ValueError("El código no debe contener espacios, use guion bajo (_) como separador")
        return v

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("El nombre no puede estar vacío")
        return v


class RolResponse(BaseModel):
    """Schema de respuesta de un rol"""
    id: int
    codigo: str
    nombre: str
    eliminado: bool
    fechaHoraCreacion: Optional[str] = None
    fechaHoraActualizacion: Optional[str] = None


class RolListResponse(BaseModel):
    """Schema para listado paginado de roles"""
    total: int
    pagina: int
    porPagina: int
    registros: List[RolResponse]