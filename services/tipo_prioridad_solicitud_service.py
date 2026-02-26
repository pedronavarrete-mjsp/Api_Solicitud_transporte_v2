# services/tipo_prioridad_solicitud_service.py
"""
Servicio para TipoPrioridadSolicitud.
Nota: Esta tabla solo tiene Nombre (sin Codigo).
"""

import logging
from typing import Optional, Dict
from datetime import datetime

from services.base_service import BaseService

logger = logging.getLogger(__name__)


class TipoPrioridadSolicitudService(BaseService):
    """Servicio CRUD completo para TipoPrioridadSolicitud"""

    TABLA = "TipoPrioridadSolicitud"

    # ──────────────────────────────────────────────
    # VALIDACIONES PRIVADAS
    # ──────────────────────────────────────────────

    def _validar_nombre_unico(self, nombre: str, excluir_id: Optional[int] = None) -> Dict:
        """Verifica que el nombre no esté duplicado (incluye eliminados por UNIQUE constraint)"""
        query = "SELECT Id, Eliminado FROM TipoPrioridadSolicitud WHERE Nombre = %s"
        params = [nombre]

        if excluir_id:
            query += " AND Id != %s"
            params.append(excluir_id)

        resultado = self.db.select(query, tuple(params))

        if not resultado:
            return {"disponible": True}

        registro = resultado[0]
        if registro["Eliminado"]:
            return {"disponible": False, "eliminado_id": registro["Id"]}
        else:
            return {"disponible": False, "error": f"Ya existe un tipo de prioridad con el nombre '{nombre}'"}

    def _validar_existencia(self, id_registro: int) -> Optional[Dict]:
        """Verifica que el registro exista y no esté eliminado"""
        query = """
            SELECT Id, Nombre, Eliminado,
                   FechaHoraCreacion, FechaHoraActualizacion
            FROM TipoPrioridadSolicitud
            WHERE Id = %s AND Eliminado = 0
        """
        resultado = self.db.select(query, (id_registro,))
        return self._serializar_fila(resultado[0]) if resultado else None

    def _validar_tiene_solicitudes_asociadas(self, id_registro: int) -> bool:
        """Verifica si hay solicitudes activas con este tipo de prioridad"""
        query = """
            SELECT COUNT(*) AS Total
            FROM Solicitud
            WHERE IdTipoPrioridadSolicitud = %s AND Eliminado = 0
        """
        resultado = self.db.select(query, (id_registro,))
        return resultado[0]["Total"] > 0 if resultado else False

    def _reactivar_registro(self, id_registro: int, datos: Dict) -> Dict:
        """Reactiva un registro previamente eliminado con datos nuevos"""
        ahora = datetime.now()
        query = """
            UPDATE TipoPrioridadSolicitud
            SET Nombre = %s, Eliminado = 0,
                FechaHoraEliminacion = NULL, FechaHoraActualizacion = %s
            WHERE Id = %s
        """
        self.db.ejecutar(query, (datos["nombre"], ahora, id_registro), fetch=False, as_dict=False)
        registro = self._validar_existencia(id_registro)
        return {"data": registro}

    # ──────────────────────────────────────────────
    # CREAR
    # ──────────────────────────────────────────────

    def crear(self, datos: Dict) -> Dict:
        """Crea un nuevo tipo de prioridad de solicitud"""
        try:
            nombre = datos.get("nombre", "").strip()
            datos_completos = {"nombre": nombre}

            resultado_nombre = self._validar_nombre_unico(nombre)
            if not resultado_nombre.get("disponible"):
                if "error" in resultado_nombre:
                    return {"error": resultado_nombre["error"], "status": 409}
                if "eliminado_id" in resultado_nombre:
                    return self._reactivar_registro(resultado_nombre["eliminado_id"], datos_completos)

            ahora = datetime.now()
            query_insert = """
                INSERT INTO TipoPrioridadSolicitud
                    (Nombre, Eliminado, FechaHoraCreacion, FechaHoraActualizacion)
                VALUES (%s, 0, %s, %s)
            """
            self.db.ejecutar(query_insert, (nombre, ahora, ahora), fetch=False, as_dict=False)

            query_id = "SELECT MAX(Id) AS NuevoId FROM TipoPrioridadSolicitud WHERE Nombre = %s AND Eliminado = 0"
            resultado_id = self.db.select(query_id, (nombre,))

            if not resultado_id or not resultado_id[0].get("NuevoId"):
                return {"error": "No se pudo obtener el ID del registro creado", "status": 500}

            registro = self._validar_existencia(int(resultado_id[0]["NuevoId"]))
            return {"data": registro}
        except Exception as e:
            logger.error(f"Error al crear TipoPrioridadSolicitud: {e}")
            return {"error": f"Error interno al crear el registro: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # OBTENER POR ID
    # ──────────────────────────────────────────────

    def obtener_por_id(self, id_registro: int) -> Dict:
        """Obtiene un tipo de prioridad por su ID"""
        try:
            registro = self._validar_existencia(id_registro)
            if not registro:
                return {"error": f"Tipo de prioridad con Id {id_registro} no encontrado", "status": 404}
            return {"data": registro}
        except Exception as e:
            logger.error(f"Error al obtener TipoPrioridadSolicitud {id_registro}: {e}")
            return {"error": f"Error interno al obtener el registro: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # LISTAR CON PAGINACIÓN Y FILTROS
    # ──────────────────────────────────────────────

    def listar(self, pagina: int = 1, por_pagina: int = 10,
               nombre: Optional[str] = None, busqueda: Optional[str] = None) -> Dict:
        """Lista tipos de prioridad con paginación y filtros"""
        try:
            if pagina < 1: pagina = 1
            if por_pagina < 1: por_pagina = 10
            if por_pagina > 100: por_pagina = 100

            where_clauses = ["Eliminado = 0"]
            params = []

            if nombre:
                where_clauses.append("Nombre LIKE %s")
                params.append(f"%{nombre}%")
            if busqueda:
                where_clauses.append("Nombre LIKE %s")
                params.append(f"%{busqueda}%")

            where_sql = " AND ".join(where_clauses)

            count_query = f"SELECT COUNT(*) AS Total FROM TipoPrioridadSolicitud WHERE {where_sql}"
            total_result = self.db.select(count_query, tuple(params))
            total = total_result[0]["Total"] if total_result else 0

            offset = (pagina - 1) * por_pagina
            params_paginados = params + [offset, por_pagina]

            query = f"""
                SELECT Id, Nombre, Eliminado, FechaHoraCreacion, FechaHoraActualizacion
                FROM TipoPrioridadSolicitud
                WHERE {where_sql}
                ORDER BY Nombre ASC
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
            """
            registros = self.db.select(query, tuple(params_paginados))

            return {
                "data": {
                    "total": total, "pagina": pagina, "porPagina": por_pagina,
                    "registros": [self._serializar_fila(r) for r in registros] if registros else []
                }
            }
        except Exception as e:
            logger.error(f"Error al listar TipoPrioridadSolicitud: {e}")
            return {"error": f"Error interno al listar registros: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # LISTAR SIN PAGINACIÓN
    # ──────────────────────────────────────────────

    def listar_todos(self, nombre: Optional[str] = None, busqueda: Optional[str] = None) -> Dict:
        """Lista todos los tipos de prioridad activos sin paginación"""
        try:
            where_clauses = ["Eliminado = 0"]
            params = []

            if nombre:
                where_clauses.append("Nombre LIKE %s")
                params.append(f"%{nombre}%")
            if busqueda:
                where_clauses.append("Nombre LIKE %s")
                params.append(f"%{busqueda}%")

            where_sql = " AND ".join(where_clauses)

            query = f"""
                SELECT Id, Nombre, Eliminado, FechaHoraCreacion, FechaHoraActualizacion
                FROM TipoPrioridadSolicitud
                WHERE {where_sql}
                ORDER BY Nombre ASC
            """
            registros = self.db.select(query, tuple(params))
            return {"data": [self._serializar_fila(r) for r in registros] if registros else []}
        except Exception as e:
            logger.error(f"Error al listar todos TipoPrioridadSolicitud: {e}")
            return {"error": f"Error interno al listar registros: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # ACTUALIZAR
    # ──────────────────────────────────────────────

    def actualizar(self, id_registro: int, datos: Dict) -> Dict:
        """Actualiza un tipo de prioridad existente"""
        try:
            existente = self._validar_existencia(id_registro)
            if not existente:
                return {"error": f"Tipo de prioridad con Id {id_registro} no encontrado", "status": 404}

            campos_actualizar = {k: v for k, v in datos.items() if v is not None}
            if not campos_actualizar:
                return {"error": "No se proporcionaron campos para actualizar", "status": 400}

            if "nombre" in campos_actualizar:
                nuevo_nombre = campos_actualizar["nombre"].strip()
                campos_actualizar["nombre"] = nuevo_nombre
                resultado_nombre = self._validar_nombre_unico(nuevo_nombre, excluir_id=id_registro)
                if not resultado_nombre.get("disponible") and "error" in resultado_nombre:
                    return {"error": resultado_nombre["error"], "status": 409}

            ahora = datetime.now()
            set_parts = []
            params = []

            if "nombre" in campos_actualizar:
                set_parts.append("Nombre = %s")
                params.append(campos_actualizar["nombre"])

            if not set_parts:
                return {"error": "No se reconocieron campos válidos para actualizar", "status": 400}

            set_parts.append("FechaHoraActualizacion = %s")
            params.append(ahora)
            params.append(id_registro)

            query = f"UPDATE TipoPrioridadSolicitud SET {', '.join(set_parts)} WHERE Id = %s AND Eliminado = 0"
            self.db.ejecutar(query, tuple(params), fetch=False, as_dict=False)

            registro = self._validar_existencia(id_registro)
            return {"data": registro}
        except Exception as e:
            logger.error(f"Error al actualizar TipoPrioridadSolicitud {id_registro}: {e}")
            return {"error": f"Error interno al actualizar el registro: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # ELIMINAR (soft delete)
    # ──────────────────────────────────────────────

    def eliminar(self, id_registro: int) -> Dict:
        """Eliminación lógica de un tipo de prioridad"""
        try:
            existente = self._validar_existencia(id_registro)
            if not existente:
                return {"error": f"Tipo de prioridad con Id {id_registro} no encontrado", "status": 404}

            if self._validar_tiene_solicitudes_asociadas(id_registro):
                return {
                    "error": "No se puede eliminar este tipo de prioridad porque tiene solicitudes activas asociadas",
                    "status": 409
                }

            ahora = datetime.now()
            query = """
                UPDATE TipoPrioridadSolicitud
                SET Eliminado = 1, FechaHoraEliminacion = %s, FechaHoraActualizacion = %s
                WHERE Id = %s AND Eliminado = 0
            """
            self.db.ejecutar(query, (ahora, ahora, id_registro), fetch=False, as_dict=False)
            return {"data": {"mensaje": f"Tipo de prioridad '{existente['Nombre']}' eliminado exitosamente"}}
        except Exception as e:
            logger.error(f"Error al eliminar TipoPrioridadSolicitud {id_registro}: {e}")
            return {"error": f"Error interno al eliminar el registro: {str(e)}", "status": 500}