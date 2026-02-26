# models/estado_solicitud_model.py
"""
Modelos Pydantic para EstadoSolicitud.
Schemas de request (crear/actualizar) y response.
Incluye campos adicionales: Color, EsEstadoFinal, Orden.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


# ──────────────────────────────────────────────
# Request: Crear
# ──────────────────────────────────────────────

class EstadoSolicitudCreate(BaseModel):
    """Schema para crear un nuevo estado de solicitud"""
    codigo: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Código único del estado de solicitud"
    )
    nombre: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre del estado de solicitud"
    )
    descripcion: Optional[str] = Field(
        None,
        max_length=250,
        description="Descripción del estado de solicitud"
    )
    color: Optional[str] = Field(
        None,
        max_length=20,
        description="Color representativo del estado (ej: #FF5733, rojo, etc.)"
    )
    esEstadoFinal: bool = Field(
        ...,
        description="Indica si este estado es un estado final del flujo"
    )
    orden: int = Field(
        ...,
        ge=0,
        description="Orden de visualización del estado en el flujo"
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

    @field_validator("color")
    @classmethod
    def color_formato(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "codigo": "PENDIENTE",
                "nombre": "Pendiente",
                "descripcion": "La solicitud está pendiente de aprobación",
                "color": "#FFA500",
                "esEstadoFinal": False,
                "orden": 1
            }
        }


# ──────────────────────────────────────────────
# Request: Actualizar
# ──────────────────────────────────────────────

class EstadoSolicitudUpdate(BaseModel):
    """Schema para actualizar un estado de solicitud existente"""
    codigo: Optional[str] = Field(None, min_length=1, max_length=50)
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=250)
    color: Optional[str] = Field(None, max_length=20)
    esEstadoFinal: Optional[bool] = None
    orden: Optional[int] = Field(None, ge=0)

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

    @field_validator("color")
    @classmethod
    def color_formato(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
        return v


# ──────────────────────────────────────────────
# Response
# ──────────────────────────────────────────────

class EstadoSolicitudResponse(BaseModel):
    """Schema de respuesta de un estado de solicitud"""
    id: int
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    color: Optional[str] = None
    esEstadoFinal: bool
    orden: int
    eliminado: bool
    fechaHoraCreacion: Optional[str] = None
    fechaHoraActualizacion: Optional[str] = None


# ──────────────────────────────────────────────
# Response: Lista paginada
# ──────────────────────────────────────────────

class EstadoSolicitudListResponse(BaseModel):
    """Schema para listado paginado de estados de solicitud"""
    total: int
    pagina: int
    porPagina: int
    registros: List[EstadoSolicitudResponse]