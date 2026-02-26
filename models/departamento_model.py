# models/departamento_model.py
"""
Modelos Pydantic para Departamento.
Tabla jerárquica con DepartamentoPadreId e IdPerfilJefe.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


class DepartamentoCreate(BaseModel):
    """Schema para crear un nuevo departamento"""
    codigo: str = Field(..., min_length=1, max_length=20, description="Código único del departamento")
    nombre: str = Field(..., min_length=1, max_length=250, description="Nombre del departamento")
    idPerfilJefe: Optional[int] = Field(None, description="ID del perfil del jefe del departamento")
    nombreJefe: Optional[str] = Field(None, max_length=250, description="Nombre del jefe")
    emailJefe: Optional[str] = Field(None, max_length=250, description="Email del jefe")
    telefonoJefe: Optional[str] = Field(None, max_length=20, description="Teléfono del jefe")
    ubicacionFisica: Optional[str] = Field(None, max_length=500, description="Ubicación física del departamento")
    nivelJerarquico: Optional[int] = Field(None, ge=0, description="Nivel jerárquico (0 = raíz)")
    departamentoPadreId: Optional[int] = Field(None, description="ID del departamento padre")

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
                "codigo": "TI",
                "nombre": "Tecnologías de la Información",
                "nombreJefe": "Juan Pérez",
                "emailJefe": "jperez@ejemplo.com",
                "telefonoJefe": "2222-1111",
                "ubicacionFisica": "Edificio A, Piso 3",
                "nivelJerarquico": 2,
                "departamentoPadreId": 1
            }
        }


class DepartamentoUpdate(BaseModel):
    """Schema para actualizar un departamento existente"""
    codigo: Optional[str] = Field(None, min_length=1, max_length=20)
    nombre: Optional[str] = Field(None, min_length=1, max_length=250)
    idPerfilJefe: Optional[int] = None
    nombreJefe: Optional[str] = Field(None, max_length=250)
    emailJefe: Optional[str] = Field(None, max_length=250)
    telefonoJefe: Optional[str] = Field(None, max_length=20)
    ubicacionFisica: Optional[str] = Field(None, max_length=500)
    nivelJerarquico: Optional[int] = Field(None, ge=0)
    departamentoPadreId: Optional[int] = None

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


class DepartamentoResponse(BaseModel):
    """Schema de respuesta de un departamento"""
    id: int
    codigo: str
    nombre: str
    idPerfilJefe: Optional[int] = None
    nombreJefe: Optional[str] = None
    emailJefe: Optional[str] = None
    telefonoJefe: Optional[str] = None
    ubicacionFisica: Optional[str] = None
    nivelJerarquico: Optional[int] = None
    departamentoPadreId: Optional[int] = None
    nombreDepartamentoPadre: Optional[str] = None
    eliminado: bool
    fechaHoraCreacion: Optional[str] = None
    fechaHoraActualizacion: Optional[str] = None


class DepartamentoListResponse(BaseModel):
    """Schema para listado paginado"""
    total: int
    pagina: int
    porPagina: int
    registros: List[DepartamentoResponse]