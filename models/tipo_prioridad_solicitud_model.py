# models/tipo_prioridad_solicitud_model.py
"""
Modelos Pydantic para TipoPrioridadSolicitud.
Nota: Esta tabla solo tiene Nombre (sin Codigo).
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


class TipoPrioridadSolicitudCreate(BaseModel):
    """Schema para crear un nuevo tipo de prioridad de solicitud"""
    nombre: str = Field(..., min_length=1, max_length=20, description="Nombre único del tipo de prioridad")

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
                "nombre": "Alta"
            }
        }


class TipoPrioridadSolicitudUpdate(BaseModel):
    """Schema para actualizar un tipo de prioridad de solicitud"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=20)

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("El nombre no puede estar vacío")
        return v


class TipoPrioridadSolicitudResponse(BaseModel):
    """Schema de respuesta de un tipo de prioridad de solicitud"""
    id: int
    nombre: str
    eliminado: bool
    fechaHoraCreacion: Optional[str] = None
    fechaHoraActualizacion: Optional[str] = None


class TipoPrioridadSolicitudListResponse(BaseModel):
    """Schema para listado paginado"""
    total: int
    pagina: int
    porPagina: int
    registros: List[TipoPrioridadSolicitudResponse]