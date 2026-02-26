# models/tipo_licencia_model.py
"""
Modelos Pydantic para TipoLicencia.
Schemas de request (crear/actualizar) y response.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


class TipoLicenciaCreate(BaseModel):
    """Schema para crear un nuevo tipo de licencia"""
    codigo: str = Field(..., min_length=1, max_length=50, description="Código único del tipo de licencia")
    nombre: str = Field(..., min_length=1, max_length=20, description="Nombre del tipo de licencia")

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
                "codigo": "LIVIANA",
                "nombre": "Liviana"
            }
        }


class TipoLicenciaUpdate(BaseModel):
    """Schema para actualizar un tipo de licencia existente"""
    codigo: Optional[str] = Field(None, min_length=1, max_length=50)
    nombre: Optional[str] = Field(None, min_length=1, max_length=20)

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


class TipoLicenciaResponse(BaseModel):
    """Schema de respuesta de un tipo de licencia"""
    id: int
    codigo: str
    nombre: str
    eliminado: bool
    fechaHoraCreacion: Optional[str] = None
    fechaHoraActualizacion: Optional[str] = None


class TipoLicenciaListResponse(BaseModel):
    """Schema para listado paginado de tipos de licencia"""
    total: int
    pagina: int
    porPagina: int
    registros: List[TipoLicenciaResponse]