# models/lugar_model.py
"""
Modelos Pydantic para Lugares.
Tabla especial con coordenadas, tipo de lugar, contacto, etc.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


class LugarCreate(BaseModel):
    """Schema para crear un nuevo lugar"""
    codigo: Optional[str] = Field(None, max_length=50, description="Código único del lugar")
    nombre: str = Field(..., min_length=1, max_length=250, description="Nombre del lugar")
    direccion: Optional[str] = Field(None, max_length=500, description="Dirección del lugar")
    latitud: Optional[float] = Field(None, ge=-90, le=90, description="Latitud (-90 a 90)")
    longitud: Optional[float] = Field(None, ge=-180, le=180, description="Longitud (-180 a 180)")
    tipoLugar: Optional[str] = Field(None, max_length=50, description="Tipo de lugar (ej: OFICINA, TRIBUNAL, etc.)")
    esPuntoFrecuente: Optional[bool] = Field(None, description="Indica si es un punto frecuente de destino")
    referencia: Optional[str] = Field(None, max_length=500, description="Referencia de ubicación")
    telefonoContacto: Optional[str] = Field(None, max_length=20, description="Teléfono de contacto del lugar")
    observaciones: Optional[str] = Field(None, description="Observaciones adicionales")

    @field_validator("codigo")
    @classmethod
    def codigo_sin_espacios(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip().upper()
            if v and " " in v:
                raise ValueError("El código no debe contener espacios")
        return v if v else None

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
                "codigo": "TRIBUNAL_SS",
                "nombre": "Tribunal de San Salvador",
                "direccion": "Boulevard Constitución, San Salvador",
                "latitud": 13.6929,
                "longitud": -89.2182,
                "tipoLugar": "TRIBUNAL",
                "esPuntoFrecuente": True,
                "referencia": "Frente al parque central",
                "telefonoContacto": "2222-3333",
                "observaciones": "Acceso por portón lateral"
            }
        }


class LugarUpdate(BaseModel):
    """Schema para actualizar un lugar existente"""
    codigo: Optional[str] = Field(None, max_length=50)
    nombre: Optional[str] = Field(None, min_length=1, max_length=250)
    direccion: Optional[str] = Field(None, max_length=500)
    latitud: Optional[float] = Field(None, ge=-90, le=90)
    longitud: Optional[float] = Field(None, ge=-180, le=180)
    tipoLugar: Optional[str] = Field(None, max_length=50)
    esPuntoFrecuente: Optional[bool] = None
    referencia: Optional[str] = Field(None, max_length=500)
    telefonoContacto: Optional[str] = Field(None, max_length=20)
    observaciones: Optional[str] = None

    @field_validator("codigo")
    @classmethod
    def codigo_sin_espacios(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip().upper()
            if v and " " in v:
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


class LugarResponse(BaseModel):
    """Schema de respuesta de un lugar"""
    id: int
    codigo: Optional[str] = None
    nombre: str
    direccion: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    tipoLugar: Optional[str] = None
    esPuntoFrecuente: Optional[bool] = None
    referencia: Optional[str] = None
    telefonoContacto: Optional[str] = None
    observaciones: Optional[str] = None
    eliminado: bool
    fechaHoraCreacion: Optional[str] = None
    fechaHoraActualizacion: Optional[str] = None


class LugarListResponse(BaseModel):
    """Schema para listado paginado de lugares"""
    total: int
    pagina: int
    porPagina: int
    registros: List[LugarResponse]