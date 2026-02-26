# models/tipo_servicio_solicitud_model.py
"""
Modelos Pydantic para TipoServicioSolicitud.
Nota: Esta tabla solo tiene Nombre (sin Codigo).
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


class TipoServicioSolicitudCreate(BaseModel):
    """Schema para crear un nuevo tipo de servicio de solicitud"""
    nombre: str = Field(..., min_length=1, max_length=50, description="Nombre único del tipo de servicio")

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
                "nombre": "Traslado de Personal"
            }
        }


class TipoServicioSolicitudUpdate(BaseModel):
    """Schema para actualizar un tipo de servicio de solicitud"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=50)

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("El nombre no puede estar vacío")
        return v


class TipoServicioSolicitudResponse(BaseModel):
    """Schema de respuesta de un tipo de servicio de solicitud"""
    id: int
    nombre: str
    eliminado: bool
    fechaHoraCreacion: Optional[str] = None
    fechaHoraActualizacion: Optional[str] = None


class TipoServicioSolicitudListResponse(BaseModel):
    """Schema para listado paginado"""
    total: int
    pagina: int
    porPagina: int
    registros: List[TipoServicioSolicitudResponse]