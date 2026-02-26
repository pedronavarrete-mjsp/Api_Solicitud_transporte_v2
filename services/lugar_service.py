# services/lugar_service.py
"""
Servicio para Lugares.
Tabla especial con coordenadas, tipo, contacto, observaciones.
"""

import logging
from typing import Optional, Dict
from datetime import datetime

from services.base_service import BaseService

logger = logging.getLogger(__name__)


class LugarService(BaseService):
    """Servicio CRUD completo para Lugares"""

    TABLA = "Lugares"

    COLUMNAS_SELECT = """
        Id, Codigo, Nombre, Direccion, Latitud, Longitud,
        TipoLugar, EsPuntoFrecuente, Referencia, TelefonoContacto,
        Observaciones, Eliminado, FechaHoraCreacion, FechaHoraActualizacion
    """

    # ──────────────────────────────────────────────
    # VALIDACIONES PRIVADAS
    # ──────────────────────────────────────────────

    def _validar_codigo_unico(self, codigo: str, excluir_id: Optional[int] = None) -> Dict:
        """Verifica que el código no esté duplicado (incluye eliminados)"""
        if not codigo:
            return {"disponible": True}

        query = "SELECT Id, Eliminado FROM Lugares WHERE Codigo = %s"
        params = [codigo]
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
            return {"disponible": False, "error": f"Ya existe un lugar con el código '{codigo}'"}

    def _validar_existencia(self, id_registro: int) -> Optional[Dict]:
        """Verifica que el registro exista y no esté eliminado"""
        query = f"SELECT {self.COLUMNAS_SELECT} FROM Lugares WHERE Id = %s AND Eliminado = 0"
        resultado = self.db.select(query, (id_registro,))
        return self._serializar_fila(resultado[0]) if resultado else None

    def _validar_tiene_misiones_asociadas(self, id_registro: int) -> bool:
        """Verifica si hay misiones activas que usen este lugar como origen o destino"""
        query = """
            SELECT COUNT(*) AS Total
            FROM Mision
            WHERE (IdLugarOrigen = %s OR IdLugarDestino = %s) AND Eliminado = 0
        """
        resultado = self.db.select(query, (id_registro, id_registro))
        return resultado[0]["Total"] > 0 if resultado else False

    def _reactivar_registro(self, id_registro: int, datos: Dict) -> Dict:
        """Reactiva un registro previamente eliminado con datos nuevos"""
        ahora = datetime.now()
        query = """
            UPDATE Lugares
            SET Codigo = %s, Nombre = %s, Direccion = %s,
                Latitud = %s, Longitud = %s, TipoLugar = %s,
                EsPuntoFrecuente = %s, Referencia = %s,
                TelefonoContacto = %s, Observaciones = %s,
                Eliminado = 0, FechaHoraEliminacion = NULL,
                FechaHoraActualizacion = %s
            WHERE Id = %s
        """
        params = (
            datos.get("codigo"), datos.get("nombre"), datos.get("direccion"),
            datos.get("latitud"), datos.get("longitud"), datos.get("tipoLugar"),
            datos.get("esPuntoFrecuente"), datos.get("referencia"),
            datos.get("telefonoContacto"), datos.get("observaciones"),
            ahora, id_registro
        )
        self.db.ejecutar(query, params, fetch=False, as_dict=False)
        registro = self._validar_existencia(id_registro)
        return {"data": registro}

    # ──────────────────────────────────────────────
    # CREAR
    # ──────────────────────────────────────────────

    def crear(self, datos: Dict) -> Dict:
        """Crea un nuevo lugar"""
        try:
            codigo = datos.get("codigo")
            if codigo:
                codigo = codigo.strip().upper() or None
            nombre = datos.get("nombre", "").strip()
            direccion = datos.get("direccion")
            if direccion: direccion = direccion.strip()
            latitud = datos.get("latitud")
            longitud = datos.get("longitud")
            tipo_lugar = datos.get("tipoLugar")
            if tipo_lugar: tipo_lugar = tipo_lugar.strip().upper()
            es_punto_frecuente = datos.get("esPuntoFrecuente")
            referencia = datos.get("referencia")
            if referencia: referencia = referencia.strip()
            telefono = datos.get("telefonoContacto")
            if telefono: telefono = telefono.strip()
            observaciones = datos.get("observaciones")
            if observaciones: observaciones = observaciones.strip()

            datos_completos = {
                "codigo": codigo, "nombre": nombre, "direccion": direccion,
                "latitud": latitud, "longitud": longitud, "tipoLugar": tipo_lugar,
                "esPuntoFrecuente": es_punto_frecuente, "referencia": referencia,
                "telefonoContacto": telefono, "observaciones": observaciones
            }

            # Validar código único (si se proporcionó)
            if codigo:
                resultado_codigo = self._validar_codigo_unico(codigo)
                if not resultado_codigo.get("disponible"):
                    if "error" in resultado_codigo:
                        return {"error": resultado_codigo["error"], "status": 409}
                    if "eliminado_id" in resultado_codigo:
                        return self._reactivar_registro(resultado_codigo["eliminado_id"], datos_completos)

            ahora = datetime.now()
            query_insert = """
                INSERT INTO Lugares
                    (Codigo, Nombre, Direccion, Latitud, Longitud, TipoLugar,
                     EsPuntoFrecuente, Referencia, TelefonoContacto, Observaciones,
                     Eliminado, FechaHoraCreacion, FechaHoraActualizacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, %s, %s)
            """
            params = (
                codigo, nombre, direccion, latitud, longitud, tipo_lugar,
                es_punto_frecuente, referencia, telefono, observaciones,
                ahora, ahora
            )
            self.db.ejecutar(query_insert, params, fetch=False, as_dict=False)

            # Obtener ID
            if codigo:
                query_id = "SELECT MAX(Id) AS NuevoId FROM Lugares WHERE Codigo = %s AND Eliminado = 0"
                resultado_id = self.db.select(query_id, (codigo,))
            else:
                query_id = "SELECT MAX(Id) AS NuevoId FROM Lugares WHERE Nombre = %s AND Eliminado = 0"
                resultado_id = self.db.select(query_id, (nombre,))

            if not resultado_id or not resultado_id[0].get("NuevoId"):
                return {"error": "No se pudo obtener el ID del registro creado", "status": 500}

            registro = self._validar_existencia(int(resultado_id[0]["NuevoId"]))
            return {"data": registro}
        except Exception as e:
            logger.error(f"Error al crear Lugar: {e}")
            return {"error": f"Error interno al crear el registro: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # OBTENER POR ID
    # ──────────────────────────────────────────────

    def obtener_por_id(self, id_registro: int) -> Dict:
        """Obtiene un lugar por su ID"""
        try:
            registro = self._validar_existencia(id_registro)
            if not registro:
                return {"error": f"Lugar con Id {id_registro} no encontrado", "status": 404}
            return {"data": registro}
        except Exception as e:
            logger.error(f"Error al obtener Lugar {id_registro}: {e}")
            return {"error": f"Error interno al obtener el registro: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # LISTAR CON PAGINACIÓN Y FILTROS
    # ──────────────────────────────────────────────

    def listar(self, pagina: int = 1, por_pagina: int = 10,
               codigo: Optional[str] = None, nombre: Optional[str] = None,
               tipo_lugar: Optional[str] = None, es_punto_frecuente: Optional[bool] = None,
               busqueda: Optional[str] = None) -> Dict:
        """Lista lugares con paginación y filtros"""
        try:
            if pagina < 1: pagina = 1
            if por_pagina < 1: por_pagina = 10
            if por_pagina > 100: por_pagina = 100

            where_clauses = ["Eliminado = 0"]
            params = []

            if codigo:
                where_clauses.append("Codigo LIKE %s")
                params.append(f"%{codigo}%")
            if nombre:
                where_clauses.append("Nombre LIKE %s")
                params.append(f"%{nombre}%")
            if tipo_lugar:
                where_clauses.append("TipoLugar = %s")
                params.append(tipo_lugar.upper())
            if es_punto_frecuente is not None:
                where_clauses.append("EsPuntoFrecuente = %s")
                params.append(es_punto_frecuente)
            if busqueda:
                where_clauses.append(
                    "(Codigo LIKE %s OR Nombre LIKE %s OR Direccion LIKE %s OR Referencia LIKE %s)"
                )
                termino = f"%{busqueda}%"
                params.extend([termino, termino, termino, termino])

            where_sql = " AND ".join(where_clauses)

            count_query = f"SELECT COUNT(*) AS Total FROM Lugares WHERE {where_sql}"
            total_result = self.db.select(count_query, tuple(params))
            total = total_result[0]["Total"] if total_result else 0

            offset = (pagina - 1) * por_pagina
            params_paginados = params + [offset, por_pagina]

            query = f"""
                SELECT {self.COLUMNAS_SELECT}
                FROM Lugares WHERE {where_sql}
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
            logger.error(f"Error al listar Lugares: {e}")
            return {"error": f"Error interno al listar registros: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # LISTAR SIN PAGINACIÓN
    # ──────────────────────────────────────────────

    def listar_todos(self, codigo: Optional[str] = None, nombre: Optional[str] = None,
                     tipo_lugar: Optional[str] = None, es_punto_frecuente: Optional[bool] = None,
                     busqueda: Optional[str] = None) -> Dict:
        """Lista todos los lugares activos sin paginación"""
        try:
            where_clauses = ["Eliminado = 0"]
            params = []

            if codigo:
                where_clauses.append("Codigo LIKE %s")
                params.append(f"%{codigo}%")
            if nombre:
                where_clauses.append("Nombre LIKE %s")
                params.append(f"%{nombre}%")
            if tipo_lugar:
                where_clauses.append("TipoLugar = %s")
                params.append(tipo_lugar.upper())
            if es_punto_frecuente is not None:
                where_clauses.append("EsPuntoFrecuente = %s")
                params.append(es_punto_frecuente)
            if busqueda:
                where_clauses.append(
                    "(Codigo LIKE %s OR Nombre LIKE %s OR Direccion LIKE %s OR Referencia LIKE %s)"
                )
                termino = f"%{busqueda}%"
                params.extend([termino, termino, termino, termino])

            where_sql = " AND ".join(where_clauses)
            query = f"SELECT {self.COLUMNAS_SELECT} FROM Lugares WHERE {where_sql} ORDER BY Nombre ASC"
            registros = self.db.select(query, tuple(params))
            return {"data": [self._serializar_fila(r) for r in registros] if registros else []}
        except Exception as e:
            logger.error(f"Error al listar todos Lugares: {e}")
            return {"error": f"Error interno al listar registros: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # ACTUALIZAR
    # ──────────────────────────────────────────────

    def actualizar(self, id_registro: int, datos: Dict) -> Dict:
        """Actualiza un lugar existente"""
        try:
            existente = self._validar_existencia(id_registro)
            if not existente:
                return {"error": f"Lugar con Id {id_registro} no encontrado", "status": 404}

            campos_actualizar = {k: v for k, v in datos.items() if v is not None}
            if not campos_actualizar:
                return {"error": "No se proporcionaron campos para actualizar", "status": 400}

            if "codigo" in campos_actualizar:
                nuevo_codigo = campos_actualizar["codigo"].strip().upper()
                campos_actualizar["codigo"] = nuevo_codigo
                resultado_codigo = self._validar_codigo_unico(nuevo_codigo, excluir_id=id_registro)
                if not resultado_codigo.get("disponible") and "error" in resultado_codigo:
                    return {"error": resultado_codigo["error"], "status": 409}

            ahora = datetime.now()
            mapeo = {
                "codigo": "Codigo", "nombre": "Nombre", "direccion": "Direccion",
                "latitud": "Latitud", "longitud": "Longitud", "tipoLugar": "TipoLugar",
                "esPuntoFrecuente": "EsPuntoFrecuente", "referencia": "Referencia",
                "telefonoContacto": "TelefonoContacto", "observaciones": "Observaciones"
            }

            set_parts = []
            params = []

            for campo, valor in campos_actualizar.items():
                columna = mapeo.get(campo)
                if columna:
                    set_parts.append(f"{columna} = %s")
                    params.append(valor.strip() if isinstance(valor, str) else valor)

            if not set_parts:
                return {"error": "No se reconocieron campos válidos para actualizar", "status": 400}

            set_parts.append("FechaHoraActualizacion = %s")
            params.append(ahora)
            params.append(id_registro)

            query = f"UPDATE Lugares SET {', '.join(set_parts)} WHERE Id = %s AND Eliminado = 0"
            self.db.ejecutar(query, tuple(params), fetch=False, as_dict=False)

            registro = self._validar_existencia(id_registro)
            return {"data": registro}
        except Exception as e:
            logger.error(f"Error al actualizar Lugar {id_registro}: {e}")
            return {"error": f"Error interno al actualizar el registro: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # ELIMINAR (soft delete)
    # ──────────────────────────────────────────────

    def eliminar(self, id_registro: int) -> Dict:
        """Eliminación lógica de un lugar"""
        try:
            existente = self._validar_existencia(id_registro)
            if not existente:
                return {"error": f"Lugar con Id {id_registro} no encontrado", "status": 404}

            if self._validar_tiene_misiones_asociadas(id_registro):
                return {
                    "error": "No se puede eliminar este lugar porque tiene misiones activas asociadas como origen o destino",
                    "status": 409
                }

            ahora = datetime.now()
            query = """
                UPDATE Lugares SET Eliminado = 1, FechaHoraEliminacion = %s, FechaHoraActualizacion = %s
                WHERE Id = %s AND Eliminado = 0
            """
            self.db.ejecutar(query, (ahora, ahora, id_registro), fetch=False, as_dict=False)
            return {"data": {"mensaje": f"Lugar '{existente['Nombre']}' eliminado exitosamente"}}
        except Exception as e:
            logger.error(f"Error al eliminar Lugar {id_registro}: {e}")
            return {"error": f"Error interno al eliminar el registro: {str(e)}", "status": 500}