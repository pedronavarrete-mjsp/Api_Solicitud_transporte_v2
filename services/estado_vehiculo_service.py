# services/estado_vehiculo_service.py
"""
Servicio para EstadoVehiculo.
Lógica de negocio, validaciones y consultas SQL.
Incluye campo adicional: PermiteAsignacion.
"""

import logging
from typing import Optional, Dict
from datetime import datetime

from services.base_service import BaseService

logger = logging.getLogger(__name__)


class EstadoVehiculoService(BaseService):
    """Servicio CRUD completo para EstadoVehiculo"""

    TABLA = "EstadoVehiculo"

    # ──────────────────────────────────────────────
    # VALIDACIONES PRIVADAS
    # ──────────────────────────────────────────────

    def _validar_codigo_unico(self, codigo: str, excluir_id: Optional[int] = None) -> Dict:
        """
        Verifica que el código no esté duplicado.
        Revisa TODOS los registros (incluidos eliminados) por el constraint UNIQUE.
        """
        query = "SELECT Id, Eliminado FROM EstadoVehiculo WHERE Codigo = %s"
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
            return {"disponible": False, "error": f"Ya existe un estado de vehículo con el código '{codigo}'"}

    def _validar_nombre_unico(self, nombre: str, excluir_id: Optional[int] = None) -> Dict:
        """
        Verifica que el nombre no esté duplicado.
        Revisa TODOS los registros (incluidos eliminados).
        """
        query = "SELECT Id, Eliminado FROM EstadoVehiculo WHERE Nombre = %s"
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
            return {"disponible": False, "error": f"Ya existe un estado de vehículo con el nombre '{nombre}'"}

    def _validar_existencia(self, id_registro: int) -> Optional[Dict]:
        """Verifica que el registro exista y no esté eliminado"""
        query = """
            SELECT Id, Codigo, Nombre, Descripcion, PermiteAsignacion,
                   Eliminado, FechaHoraCreacion, FechaHoraActualizacion
            FROM EstadoVehiculo
            WHERE Id = %s AND Eliminado = 0
        """
        resultado = self.db.select(query, (id_registro,))
        return self._serializar_fila(resultado[0]) if resultado else None

    def _validar_tiene_vehiculos_asociados(self, id_registro: int) -> bool:
        """Verifica si hay vehículos activos con este estado"""
        query = """
            SELECT COUNT(*) AS Total
            FROM Vehiculo
            WHERE IdEstadoVehiculo = %s AND Eliminado = 0
        """
        resultado = self.db.select(query, (id_registro,))
        return resultado[0]["Total"] > 0 if resultado else False

    def _reactivar_registro(self, id_registro: int, datos: Dict) -> Dict:
        """Reactiva un registro previamente eliminado (soft delete) con datos nuevos"""
        ahora = datetime.now()

        query = """
            UPDATE EstadoVehiculo
            SET Codigo = %s,
                Nombre = %s,
                Descripcion = %s,
                PermiteAsignacion = %s,
                Eliminado = 0,
                FechaHoraEliminacion = NULL,
                FechaHoraActualizacion = %s
            WHERE Id = %s
        """
        params = (
            datos.get("codigo"),
            datos.get("nombre"),
            datos.get("descripcion"),
            datos.get("permiteAsignacion"),
            ahora,
            id_registro
        )

        self.db.ejecutar(query, params, fetch=False, as_dict=False)

        registro = self._validar_existencia(id_registro)
        return {"data": registro}

    # ──────────────────────────────────────────────
    # CREAR
    # ──────────────────────────────────────────────

    def crear(self, datos: Dict) -> Dict:
        """
        Crea un nuevo estado de vehículo.
        Si el código o nombre ya existían pero fueron eliminados, se reactiva el registro.

        Validaciones:
            - Código único
            - Nombre único
        """
        try:
            codigo = datos.get("codigo", "").strip().upper()
            nombre = datos.get("nombre", "").strip()
            descripcion = datos.get("descripcion")
            permite_asignacion = datos.get("permiteAsignacion")

            if descripcion:
                descripcion = descripcion.strip()

            datos_completos = {
                "codigo": codigo,
                "nombre": nombre,
                "descripcion": descripcion,
                "permiteAsignacion": permite_asignacion
            }

            # Validar código
            resultado_codigo = self._validar_codigo_unico(codigo)

            if not resultado_codigo.get("disponible"):
                if "error" in resultado_codigo:
                    return {"error": resultado_codigo["error"], "status": 409}

                if "eliminado_id" in resultado_codigo:
                    return self._reactivar_registro(
                        resultado_codigo["eliminado_id"], datos_completos
                    )

            # Validar nombre
            resultado_nombre = self._validar_nombre_unico(nombre)

            if not resultado_nombre.get("disponible"):
                if "error" in resultado_nombre:
                    return {"error": resultado_nombre["error"], "status": 409}

                if "eliminado_id" in resultado_nombre:
                    return self._reactivar_registro(
                        resultado_nombre["eliminado_id"], datos_completos
                    )

            # Crear nuevo registro
            ahora = datetime.now()

            query_insert = """
                INSERT INTO EstadoVehiculo
                    (Codigo, Nombre, Descripcion, PermiteAsignacion,
                     Eliminado, FechaHoraCreacion, FechaHoraActualizacion)
                VALUES (%s, %s, %s, %s, 0, %s, %s)
            """
            params = (codigo, nombre, descripcion, permite_asignacion, ahora, ahora)

            self.db.ejecutar(query_insert, params, fetch=False, as_dict=False)

            # Obtener ID del registro creado
            query_id = "SELECT MAX(Id) AS NuevoId FROM EstadoVehiculo WHERE Codigo = %s AND Eliminado = 0"
            resultado_id = self.db.select(query_id, (codigo,))

            if not resultado_id or not resultado_id[0].get("NuevoId"):
                return {"error": "No se pudo obtener el ID del registro creado", "status": 500}

            id_nuevo = int(resultado_id[0]["NuevoId"])

            registro = self._validar_existencia(id_nuevo)
            return {"data": registro}

        except Exception as e:
            logger.error(f"Error al crear EstadoVehiculo: {e}")
            return {"error": f"Error interno al crear el registro: {str(e)}", "status": 500}

    # ──────────────��───────────────────────────────
    # OBTENER POR ID
    # ──────────────────────────────────────────────

    def obtener_por_id(self, id_registro: int) -> Dict:
        """Obtiene un estado de vehículo por su ID"""
        try:
            registro = self._validar_existencia(id_registro)

            if not registro:
                return {"error": f"Estado de vehículo con Id {id_registro} no encontrado", "status": 404}

            return {"data": registro}

        except Exception as e:
            logger.error(f"Error al obtener EstadoVehiculo {id_registro}: {e}")
            return {"error": f"Error interno al obtener el registro: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # LISTAR CON PAGINACIÓN Y FILTROS
    # ──────────────────────────────────────────────

    def listar(
        self,
        pagina: int = 1,
        por_pagina: int = 10,
        codigo: Optional[str] = None,
        nombre: Optional[str] = None,
        permite_asignacion: Optional[bool] = None,
        busqueda: Optional[str] = None
    ) -> Dict:
        """
        Lista estados de vehículo con paginación y filtros.

        Args:
            pagina: Número de página
            por_pagina: Registros por página
            codigo: Filtrar por código (búsqueda parcial)
            nombre: Filtrar por nombre (búsqueda parcial)
            permite_asignacion: Filtrar por si permite asignación
            busqueda: Búsqueda general
        """
        try:
            if pagina < 1:
                pagina = 1
            if por_pagina < 1:
                por_pagina = 10
            if por_pagina > 100:
                por_pagina = 100

            where_clauses = ["Eliminado = 0"]
            params = []

            if codigo:
                where_clauses.append("Codigo LIKE %s")
                params.append(f"%{codigo}%")

            if nombre:
                where_clauses.append("Nombre LIKE %s")
                params.append(f"%{nombre}%")

            if permite_asignacion is not None:
                where_clauses.append("PermiteAsignacion = %s")
                params.append(permite_asignacion)

            if busqueda:
                where_clauses.append(
                    "(Codigo LIKE %s OR Nombre LIKE %s OR Descripcion LIKE %s)"
                )
                termino = f"%{busqueda}%"
                params.extend([termino, termino, termino])

            where_sql = " AND ".join(where_clauses)

            # Contar total
            count_query = f"SELECT COUNT(*) AS Total FROM EstadoVehiculo WHERE {where_sql}"
            total_result = self.db.select(count_query, tuple(params))
            total = total_result[0]["Total"] if total_result else 0

            # Obtener página
            offset = (pagina - 1) * por_pagina
            params_paginados = params + [offset, por_pagina]

            query = f"""
                SELECT Id, Codigo, Nombre, Descripcion, PermiteAsignacion,
                       Eliminado, FechaHoraCreacion, FechaHoraActualizacion
                FROM EstadoVehiculo
                WHERE {where_sql}
                ORDER BY Nombre ASC
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
            """

            registros = self.db.select(query, tuple(params_paginados))

            return {
                "data": {
                    "total": total,
                    "pagina": pagina,
                    "porPagina": por_pagina,
                    "registros": [self._serializar_fila(r) for r in registros] if registros else []
                }
            }

        except Exception as e:
            logger.error(f"Error al listar EstadoVehiculo: {e}")
            return {"error": f"Error interno al listar registros: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # LISTAR SIN PAGINACIÓN
    # ──────────────────────────────────────────────

    def listar_todos(
        self,
        codigo: Optional[str] = None,
        nombre: Optional[str] = None,
        permite_asignacion: Optional[bool] = None,
        busqueda: Optional[str] = None
    ) -> Dict:
        """Lista todos los estados de vehículo activos sin paginación"""
        try:
            where_clauses = ["Eliminado = 0"]
            params = []

            if codigo:
                where_clauses.append("Codigo LIKE %s")
                params.append(f"%{codigo}%")

            if nombre:
                where_clauses.append("Nombre LIKE %s")
                params.append(f"%{nombre}%")

            if permite_asignacion is not None:
                where_clauses.append("PermiteAsignacion = %s")
                params.append(permite_asignacion)

            if busqueda:
                where_clauses.append(
                    "(Codigo LIKE %s OR Nombre LIKE %s OR Descripcion LIKE %s)"
                )
                termino = f"%{busqueda}%"
                params.extend([termino, termino, termino])

            where_sql = " AND ".join(where_clauses)

            query = f"""
                SELECT Id, Codigo, Nombre, Descripcion, PermiteAsignacion,
                       Eliminado, FechaHoraCreacion, FechaHoraActualizacion
                FROM EstadoVehiculo
                WHERE {where_sql}
                ORDER BY Nombre ASC
            """

            registros = self.db.select(query, tuple(params))

            return {
                "data": [self._serializar_fila(r) for r in registros] if registros else []
            }

        except Exception as e:
            logger.error(f"Error al listar todos EstadoVehiculo: {e}")
            return {"error": f"Error interno al listar registros: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # ACTUALIZAR
    # ──────────────────────────────────────────────

    def actualizar(self, id_registro: int, datos: Dict) -> Dict:
        """
        Actualiza un estado de vehículo existente.

        Validaciones:
            - Registro existe
            - Código único (si se cambia)
            - Nombre único (si se cambia)
        """
        try:
            existente = self._validar_existencia(id_registro)
            if not existente:
                return {"error": f"Estado de vehículo con Id {id_registro} no encontrado", "status": 404}

            campos_actualizar = {k: v for k, v in datos.items() if v is not None}

            if not campos_actualizar:
                return {"error": "No se proporcionaron campos para actualizar", "status": 400}

            # Validar código único
            if "codigo" in campos_actualizar:
                nuevo_codigo = campos_actualizar["codigo"].strip().upper()
                campos_actualizar["codigo"] = nuevo_codigo

                resultado_codigo = self._validar_codigo_unico(nuevo_codigo, excluir_id=id_registro)
                if not resultado_codigo.get("disponible") and "error" in resultado_codigo:
                    return {"error": resultado_codigo["error"], "status": 409}

            # Validar nombre único
            if "nombre" in campos_actualizar:
                nuevo_nombre = campos_actualizar["nombre"].strip()
                campos_actualizar["nombre"] = nuevo_nombre

                resultado_nombre = self._validar_nombre_unico(nuevo_nombre, excluir_id=id_registro)
                if not resultado_nombre.get("disponible") and "error" in resultado_nombre:
                    return {"error": resultado_nombre["error"], "status": 409}

            ahora = datetime.now()

            mapeo = {
                "codigo": "Codigo",
                "nombre": "Nombre",
                "descripcion": "Descripcion",
                "permiteAsignacion": "PermiteAsignacion"
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

            query = f"""
                UPDATE EstadoVehiculo
                SET {', '.join(set_parts)}
                WHERE Id = %s AND Eliminado = 0
            """

            self.db.ejecutar(query, tuple(params), fetch=False, as_dict=False)

            registro = self._validar_existencia(id_registro)
            return {"data": registro}

        except Exception as e:
            logger.error(f"Error al actualizar EstadoVehiculo {id_registro}: {e}")
            return {"error": f"Error interno al actualizar el registro: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # ELIMINAR (soft delete)
    # ──────────────────────────────────────────────

    def eliminar(self, id_registro: int) -> Dict:
        """
        Eliminación lógica de un estado de vehículo.

        Validaciones:
            - Registro existe
            - No tiene vehículos activos asociados
        """
        try:
            existente = self._validar_existencia(id_registro)
            if not existente:
                return {"error": f"Estado de vehículo con Id {id_registro} no encontrado", "status": 404}

            if self._validar_tiene_vehiculos_asociados(id_registro):
                return {
                    "error": "No se puede eliminar este estado de vehículo porque tiene vehículos activos asociados",
                    "status": 409
                }

            ahora = datetime.now()

            query = """
                UPDATE EstadoVehiculo
                SET Eliminado = 1,
                    FechaHoraEliminacion = %s,
                    FechaHoraActualizacion = %s
                WHERE Id = %s AND Eliminado = 0
            """

            self.db.ejecutar(query, (ahora, ahora, id_registro), fetch=False, as_dict=False)

            return {"data": {"mensaje": f"Estado de vehículo '{existente['Nombre']}' eliminado exitosamente"}}

        except Exception as e:
            logger.error(f"Error al eliminar EstadoVehiculo {id_registro}: {e}")
            return {"error": f"Error interno al eliminar el registro: {str(e)}", "status": 500}