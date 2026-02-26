# utils/validaciones.py
"""
Validaciones reutilizables para toda la API.
"""

from typing import Any, Dict, List, Optional


def validar_campos_requeridos(datos: Dict[str, Any], campos: List[str]) -> Optional[str]:
    """
    Valida que los campos requeridos estén presentes y no vacíos.

    Args:
        datos: Diccionario con los datos a validar
        campos: Lista de nombres de campos requeridos

    Returns:
        Mensaje de error si falta algún campo, None si todo está bien
    """
    faltantes = []
    for campo in campos:
        valor = datos.get(campo)
        if valor is None:
            faltantes.append(campo)
        elif isinstance(valor, str) and not valor.strip():
            faltantes.append(campo)

    if faltantes:
        campos_str = ", ".join(faltantes)
        return f"Los siguientes campos son obligatorios: {campos_str}"

    return None


def validar_longitud_maxima(valor: str, campo: str, max_length: int) -> Optional[str]:
    """
    Valida que un string no exceda la longitud máxima.

    Returns:
        Mensaje de error si excede, None si está bien
    """
    if valor and len(valor) > max_length:
        return f"El campo '{campo}' no debe exceder {max_length} caracteres (tiene {len(valor)})"
    return None


def validar_longitud_minima(valor: str, campo: str, min_length: int) -> Optional[str]:
    """
    Valida que un string tenga al menos la longitud mínima.

    Returns:
        Mensaje de error si es menor, None si está bien
    """
    if valor and len(valor) < min_length:
        return f"El campo '{campo}' debe tener al menos {min_length} caracteres"
    return None