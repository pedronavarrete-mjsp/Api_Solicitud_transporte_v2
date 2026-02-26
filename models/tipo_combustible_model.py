# models/tipo_combustible_model.py
"""
Modelos Pydantic para TipoCombustible.
Schemas de request (crear/actualizar) y response.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


# ──────────────────────────────────────────────
# Request: Crear
# ──────────────────────────────────────────────

class TipoCombustibleCreate(BaseModel):
    """Schema para crear un nuevo tipo de combustible"""
    codigo: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Código único del tipo de combustible"
    )
    nombre: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre del tipo de combustible"
    )

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
                "codigo": "GASOLINA",
                "nombre": "Gasolina Regular"
            }
        }


# ──────────────────────────────────────────────
# Request: Actualizar
# ──────────────────────────────────────────────

class TipoCombustibleUpdate(BaseModel):
    """Schema para actualizar un tipo de combustible existente"""
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


# ──────────────────────────────────────────────
# Response
# ──────────────────────────────────────────────

class TipoCombustibleResponse(BaseModel):
    """Schema de respuesta de un tipo de combustible"""
    id: int
    codigo: str
    nombre: str
    eliminado: bool
    fechaHoraCreacion: Optional[str] = None
    fechaHoraActualizacion: Optional[str] = None


# ──────────────────────────────────────────────
# Response: Lista paginada
# ──────────────────────────────────────────────

class TipoCombustibleListResponse(BaseModel):
    """Schema para listado paginado de tipos de combustible"""
    total: int
    pagina: int
    porPagina: int
    registros: List[TipoCombustibleResponse]