# services/base_service.py
"""
Servicio base con utilidades de serialización comunes.
Todos los services heredan de aquí.
"""

from typing import Any, Dict
from datetime import datetime, date, time
from decimal import Decimal

from database.sql_connection import get_sql_manager


class BaseService:
    """Clase base para todos los servicios"""

    def __init__(self):
        self.db = get_sql_manager()

    def _serializar_valor(self, valor: Any) -> Any:
        """Convierte tipos de datos Python a formatos serializables JSON"""
        if valor is None:
            return None
        if isinstance(valor, datetime):
            return valor.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(valor, date):
            return valor.strftime("%Y-%m-%d")
        if isinstance(valor, time):
            return valor.strftime("%H:%M:%S")
        if isinstance(valor, Decimal):
            return float(valor)
        if isinstance(valor, bytes):
            return valor.hex()
        return valor

    def _serializar_fila(self, fila: Dict) -> Dict:
        """Serializa todos los valores de una fila de resultado SQL"""
        return {k: self._serializar_valor(v) for k, v in fila.items()}