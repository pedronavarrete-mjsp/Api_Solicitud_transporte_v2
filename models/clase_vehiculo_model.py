# models/clase_vehiculo_model.py
"""
Modelos Pydantic para ClaseVehiculo.
Schemas de request (crear/actualizar) y response.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


# ──────────────────────────────────────────────
# Request: Crear
# ──────────────────────────────────────────────

class ClaseVehiculoCreate(BaseModel):
    """Schema para crear una nueva clase de vehículo"""
    codigo: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Código único de la clase de vehículo"
    )
    nombre: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre de la clase de vehículo"
    )
    descripcion: Optional[str] = Field(
        None,
        max_length=250,
        description="Descripción de la clase de vehículo"
    )

    @field_validator("codigo")
    @classmethod
    def codigo_sin_espacios(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("El código no puede estar vacío")
        if " " in v:
            raise ValueError("El código no debe contener espacios")
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
                "codigo": "SEDAN",
                "nombre": "Sedán",
                "descripcion": "Vehículo tipo sedán de 4 puertas"
            }
        }


# ──────────────────────────────────────────────
# Request: Actualizar
# ──────────────────────────────────────────────

class ClaseVehiculoUpdate(BaseModel):
    """Schema para actualizar una clase de vehículo existente"""
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
                raise ValueError("El código no debe contener espacios")
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

class ClaseVehiculoResponse(BaseModel):
    """Schema de respuesta de una clase de vehículo"""
    id: int
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    eliminado: bool
    fechaHoraCreacion: Optional[str] = None
    fechaHoraActualizacion: Optional[str] = None


# ──────────────────────────────────────────────
# Response: Lista paginada
# ────────────��─────────────────────────────────

class ClaseVehiculoListResponse(BaseModel):
    """Schema para listado paginado de clases de vehículo"""
    total: int
    pagina: int
    porPagina: int
    registros: List[ClaseVehiculoResponse]