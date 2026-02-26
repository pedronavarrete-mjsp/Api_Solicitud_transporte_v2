# models/estado_mision_model.py
"""
Modelos Pydantic para EstadoMision.
Schemas de request (crear/actualizar) y response.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


# ──────────────────────────────────────────────
# Request: Crear
# ──────────────────────────────────────────────

class EstadoMisionCreate(BaseModel):
    """Schema para crear un nuevo estado de misión"""
    codigo: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Código único del estado de misión"
    )
    nombre: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre del estado de misión"
    )
    descripcion: Optional[str] = Field(
        None,
        max_length=250,
        description="Descripción del estado de misión"
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
                "codigo": "EN_ESPERA",
                "nombre": "En Espera",
                "descripcion": "La misión está en espera de recursos"
            }
        }


# ──────────────────────────────────────────────
# Request: Actualizar
# ──────────────────────────────────────────────

class EstadoMisionUpdate(BaseModel):
    """Schema para actualizar un estado de misión existente"""
    codigo: Optional[str] = Field(None, min_length=1, max_length=50)
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=250)

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

class EstadoMisionResponse(BaseModel):
    """Schema de respuesta de un estado de misión"""
    id: int
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    eliminado: bool
    fechaHoraCreacion: Optional[str] = None
    fechaHoraActualizacion: Optional[str] = None


# ──────────────────────────────────────────────
# Response: Lista paginada
# ──────────────────────────────────────────────

class EstadoMisionListResponse(BaseModel):
    """Schema para listado paginado de estados de misión"""
    total: int
    pagina: int
    porPagina: int
    registros: List[EstadoMisionResponse]