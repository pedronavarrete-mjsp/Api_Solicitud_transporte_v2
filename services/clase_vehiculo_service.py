# services/clase_vehiculo_service.py
"""
Servicio para ClaseVehiculo.
Lógica de negocio, validaciones y consultas SQL.
"""

import logging
from typing import Optional, Dict
from datetime import datetime

from services.base_service import BaseService

logger = logging.getLogger(__name__)


class ClaseVehiculoService(BaseService):
    """Servicio CRUD completo para ClaseVehiculo"""

    TABLA = "ClaseVehiculo"

    # ──────────────────────────────────────────────
    # VALIDACIONES PRIVADAS
    # ──────────────────────────────────────────────

    def _validar_codigo_unico(self, codigo: str, excluir_id: Optional[int] = None) -> Dict:
        """
        Verifica que el código no esté duplicado.
        Revisa TODOS los registros (incluidos eliminados) por el constraint UNIQUE.

        Returns:
            Dict con:
            - "disponible": True si se puede usar
            - "eliminado_id": ID del registro eliminado si existe (para reactivar)
            - "error": Mensaje si está duplicado y activo
        """
        query = "SELECT Id, Eliminado FROM ClaseVehiculo WHERE Codigo = %s"
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
            return {"disponible": False, "error": f"Ya existe una clase de vehículo con el código '{codigo}'"}

    def _validar_nombre_unico(self, nombre: str, excluir_id: Optional[int] = None) -> Dict:
        """
        Verifica que el nombre no esté duplicado.
        Revisa TODOS los registros (incluidos eliminados) por el constraint UNIQUE.

        Returns:
            Dict similar a _validar_codigo_unico
        """
        query = "SELECT Id, Eliminado FROM ClaseVehiculo WHERE Nombre = %s"
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
            return {"disponible": False, "error": f"Ya existe una clase de vehículo con el nombre '{nombre}'"}

    def _validar_existencia(self, id_registro: int) -> Optional[Dict]:
        """
        Verifica que el registro exista y no esté eliminado.

        Args:
            id_registro: ID del registro

        Returns:
            Registro encontrado o None
        """
        query = """
            SELECT Id, Codigo, Nombre, Descripcion, Eliminado,
                   FechaHoraCreacion, FechaHoraActualizacion
            FROM ClaseVehiculo
            WHERE Id = %s AND Eliminado = 0
        """
        resultado = self.db.select(query, (id_registro,))
        return self._serializar_fila(resultado[0]) if resultado else None

    def _validar_tiene_vehiculos_asociados(self, id_registro: int) -> bool:
        """
        Verifica si hay vehículos asociados a esta clase (para soft delete).

        Args:
            id_registro: ID de la clase de vehículo

        Returns:
            True si tiene vehículos asociados activos
        """
        query = """
            SELECT COUNT(*) AS Total
            FROM Vehiculo
            WHERE IdClaseVehiculo = %s AND Eliminado = 0
        """
        resultado = self.db.select(query, (id_registro,))
        return resultado[0]["Total"] > 0 if resultado else False

    def _reactivar_registro(self, id_registro: int, datos: Dict) -> Dict:
        """
        Reactiva un registro previamente eliminado (soft delete) con datos nuevos.

        Args:
            id_registro: ID del registro eliminado
            datos: Nuevos datos para el registro

        Returns:
            Dict con "data" del registro reactivado
        """
        ahora = datetime.now()

        query = """
            UPDATE ClaseVehiculo
            SET Codigo = %s,
                Nombre = %s,
                Descripcion = %s,
                Eliminado = 0,
                FechaHoraEliminacion = NULL,
                FechaHoraActualizacion = %s
            WHERE Id = %s
        """
        params = (
            datos.get("codigo"),
            datos.get("nombre"),
            datos.get("descripcion"),
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
        Crea una nueva clase de vehículo.
        Si el código o nombre ya existían pero fueron eliminados, se reactiva el registro.

        Args:
            datos: Diccionario con codigo, nombre, descripcion

        Returns:
            Dict con clave "error" si hubo error, o "data" con el registro creado

        Validaciones:
            - Código único (entre activos)
            - Nombre único (entre activos)
            - Si existe eliminado, se reactiva
        """
        try:
            codigo = datos.get("codigo", "").strip().upper()
            nombre = datos.get("nombre", "").strip()
            descripcion = datos.get("descripcion")

            if descripcion:
                descripcion = descripcion.strip()

            # Validar código
            resultado_codigo = self._validar_codigo_unico(codigo)

            if not resultado_codigo.get("disponible"):
                # Si tiene error = está activo y duplicado
                if "error" in resultado_codigo:
                    return {"error": resultado_codigo["error"], "status": 409}

                # Si tiene eliminado_id = existe pero eliminado → reactivar
                if "eliminado_id" in resultado_codigo:
                    return self._reactivar_registro(
                        resultado_codigo["eliminado_id"],
                        {"codigo": codigo, "nombre": nombre, "descripcion": descripcion}
                    )

            # Validar nombre
            resultado_nombre = self._validar_nombre_unico(nombre)

            if not resultado_nombre.get("disponible"):
                if "error" in resultado_nombre:
                    return {"error": resultado_nombre["error"], "status": 409}

                if "eliminado_id" in resultado_nombre:
                    return self._reactivar_registro(
                        resultado_nombre["eliminado_id"],
                        {"codigo": codigo, "nombre": nombre, "descripcion": descripcion}
                    )

            # No existe en ninguna forma → crear nuevo
            ahora = datetime.now()

            query_insert = """
                INSERT INTO ClaseVehiculo
                    (Codigo, Nombre, Descripcion, Eliminado,
                     FechaHoraCreacion, FechaHoraActualizacion)
                VALUES (%s, %s, %s, 0, %s, %s)
            """
            params = (codigo, nombre, descripcion, ahora, ahora)

            self.db.ejecutar(query_insert, params, fetch=False, as_dict=False)

            # Obtener el ID del registro recién insertado
            query_id = "SELECT MAX(Id) AS NuevoId FROM ClaseVehiculo WHERE Codigo = %s AND Eliminado = 0"
            resultado_id = self.db.select(query_id, (codigo,))

            if not resultado_id or not resultado_id[0].get("NuevoId"):
                return {"error": "No se pudo obtener el ID del registro creado", "status": 500}

            id_nuevo = int(resultado_id[0]["NuevoId"])

            registro = self._validar_existencia(id_nuevo)
            return {"data": registro}

        except Exception as e:
            logger.error(f"Error al crear ClaseVehiculo: {e}")
            return {"error": f"Error interno al crear el registro: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # OBTENER POR ID
    # ──────────────────────────────────────────────

    def obtener_por_id(self, id_registro: int) -> Dict:
        """
        Obtiene una clase de vehículo por su ID.

        Args:
            id_registro: ID del registro

        Returns:
            Dict con "data" o "error"
        """
        try:
            registro = self._validar_existencia(id_registro)

            if not registro:
                return {"error": f"Clase de vehículo con Id {id_registro} no encontrada", "status": 404}

            return {"data": registro}

        except Exception as e:
            logger.error(f"Error al obtener ClaseVehiculo {id_registro}: {e}")
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
        busqueda: Optional[str] = None
    ) -> Dict:
        """
        Lista clases de vehículo con paginación y filtros.

        Args:
            pagina: Número de página (mínimo 1)
            por_pagina: Registros por página (máximo 100)
            codigo: Filtrar por código (búsqueda parcial)
            nombre: Filtrar por nombre (búsqueda parcial)
            busqueda: Búsqueda general en código, nombre y descripción

        Returns:
            Dict con total, pagina, porPagina y registros
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

            if busqueda:
                where_clauses.append(
                    "(Codigo LIKE %s OR Nombre LIKE %s OR Descripcion LIKE %s)"
                )
                termino = f"%{busqueda}%"
                params.extend([termino, termino, termino])

            where_sql = " AND ".join(where_clauses)

            # Contar total
            count_query = f"SELECT COUNT(*) AS Total FROM ClaseVehiculo WHERE {where_sql}"
            total_result = self.db.select(count_query, tuple(params))
            total = total_result[0]["Total"] if total_result else 0

            # Obtener página
            offset = (pagina - 1) * por_pagina
            params_paginados = params + [offset, por_pagina]

            query = f"""
                SELECT Id, Codigo, Nombre, Descripcion, Eliminado,
                       FechaHoraCreacion, FechaHoraActualizacion
                FROM ClaseVehiculo
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
            logger.error(f"Error al listar ClaseVehiculo: {e}")
            return {"error": f"Error interno al listar registros: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # LISTAR SIN PAGINACIÓN (solo filtros)
    # ──────────────────────────────────────────────

    def listar_todos(
        self,
        codigo: Optional[str] = None,
        nombre: Optional[str] = None,
        busqueda: Optional[str] = None
    ) -> Dict:
        """
        Lista todas las clases de vehículo sin paginación (para dropdowns/selects).
        Solo registros activos.

        Args:
            codigo: Filtrar por código
            nombre: Filtrar por nombre
            busqueda: Búsqueda general

        Returns:
            Dict con lista de registros
        """
        try:
            where_clauses = ["Eliminado = 0"]
            params = []

            if codigo:
                where_clauses.append("Codigo LIKE %s")
                params.append(f"%{codigo}%")

            if nombre:
                where_clauses.append("Nombre LIKE %s")
                params.append(f"%{nombre}%")

            if busqueda:
                where_clauses.append(
                    "(Codigo LIKE %s OR Nombre LIKE %s OR Descripcion LIKE %s)"
                )
                termino = f"%{busqueda}%"
                params.extend([termino, termino, termino])

            where_sql = " AND ".join(where_clauses)

            query = f"""
                SELECT Id, Codigo, Nombre, Descripcion, Eliminado,
                       FechaHoraCreacion, FechaHoraActualizacion
                FROM ClaseVehiculo
                WHERE {where_sql}
                ORDER BY Nombre ASC
            """

            registros = self.db.select(query, tuple(params))

            return {
                "data": [self._serializar_fila(r) for r in registros] if registros else []
            }

        except Exception as e:
            logger.error(f"Error al listar todos ClaseVehiculo: {e}")
            return {"error": f"Error interno al listar registros: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # ACTUALIZAR
    # ──────────────────────────────────────────────

    def actualizar(self, id_registro: int, datos: Dict) -> Dict:
        """
        Actualiza una clase de vehículo existente.

        Args:
            id_registro: ID del registro
            datos: Campos a actualizar

        Returns:
            Dict con "data" o "error"

        Validaciones:
            - Registro existe
            - Código único (si se cambia)
            - Nombre único (si se cambia)
        """
        try:
            existente = self._validar_existencia(id_registro)
            if not existente:
                return {"error": f"Clase de vehículo con Id {id_registro} no encontrada", "status": 404}

            campos_actualizar = {k: v for k, v in datos.items() if v is not None}

            if not campos_actualizar:
                return {"error": "No se proporcionaron campos para actualizar", "status": 400}

            # Validar código único si se está cambiando
            if "codigo" in campos_actualizar:
                nuevo_codigo = campos_actualizar["codigo"].strip().upper()
                campos_actualizar["codigo"] = nuevo_codigo

                resultado_codigo = self._validar_codigo_unico(nuevo_codigo, excluir_id=id_registro)
                if not resultado_codigo.get("disponible") and "error" in resultado_codigo:
                    return {"error": resultado_codigo["error"], "status": 409}

            # Validar nombre único si se está cambiando
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
                "descripcion": "Descripcion"
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
                UPDATE ClaseVehiculo
                SET {', '.join(set_parts)}
                WHERE Id = %s AND Eliminado = 0
            """

            self.db.ejecutar(query, tuple(params), fetch=False, as_dict=False)

            registro = self._validar_existencia(id_registro)
            return {"data": registro}

        except Exception as e:
            logger.error(f"Error al actualizar ClaseVehiculo {id_registro}: {e}")
            return {"error": f"Error interno al actualizar el registro: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # ELIMINAR (soft delete)
    # ──────────────────────────────────────────────

    def eliminar(self, id_registro: int) -> Dict:
        """
        Eliminación lógica de una clase de vehículo.

        Args:
            id_registro: ID del registro

        Returns:
            Dict con "data" (mensaje éxito) o "error"

        Validaciones:
            - Registro existe
            - No tiene vehículos asociados activos
        """
        try:
            existente = self._validar_existencia(id_registro)
            if not existente:
                return {"error": f"Clase de vehículo con Id {id_registro} no encontrada", "status": 404}

            if self._validar_tiene_vehiculos_asociados(id_registro):
                return {
                    "error": "No se puede eliminar esta clase de vehículo porque tiene vehículos asociados activos",
                    "status": 409
                }

            ahora = datetime.now()

            query = """
                UPDATE ClaseVehiculo
                SET Eliminado = 1,
                    FechaHoraEliminacion = %s,
                    FechaHoraActualizacion = %s
                WHERE Id = %s AND Eliminado = 0
            """

            self.db.ejecutar(query, (ahora, ahora, id_registro), fetch=False, as_dict=False)

            return {"data": {"mensaje": f"Clase de vehículo '{existente['Nombre']}' eliminada exitosamente"}}

        except Exception as e:
            logger.error(f"Error al eliminar ClaseVehiculo {id_registro}: {e}")
            return {"error": f"Error interno al eliminar el registro: {str(e)}", "status": 500}