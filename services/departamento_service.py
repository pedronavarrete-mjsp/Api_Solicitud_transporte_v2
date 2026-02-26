# services/departamento_service.py
"""
Servicio para Departamento.
Tabla jerárquica con DepartamentoPadreId e IdPerfilJefe.
"""

import logging
from typing import Optional, Dict
from datetime import datetime

from services.base_service import BaseService

logger = logging.getLogger(__name__)


class DepartamentoService(BaseService):
    """Servicio CRUD completo para Departamento"""

    TABLA = "Departamento"

    COLUMNAS_SELECT = """
        d.Id, d.Codigo, d.Nombre, d.IdPerfilJefe,
        d.NombreJefe, d.EmailJefe, d.TelefonoJefe,
        d.UbicacionFisica, d.NivelJerarquico, d.DepartamentoPadreId,
        dp.Nombre AS NombreDepartamentoPadre,
        d.Eliminado, d.FechaHoraCreacion, d.FechaHoraActualizacion
    """

    # ──────────────────────────────────────────────
    # VALIDACIONES PRIVADAS
    # ──────────────────────────────────────────────

    def _validar_codigo_unico(self, codigo: str, excluir_id: Optional[int] = None) -> Dict:
        """Verifica que el código no esté duplicado (incluye eliminados)"""
        query = "SELECT Id, Eliminado FROM Departamento WHERE Codigo = %s"
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
            return {"disponible": False, "error": f"Ya existe un departamento con el código '{codigo}'"}

    def _validar_existencia(self, id_registro: int) -> Optional[Dict]:
        """Verifica que el registro exista y no esté eliminado"""
        query = f"""
            SELECT {self.COLUMNAS_SELECT}
            FROM Departamento d
            LEFT JOIN Departamento dp ON d.DepartamentoPadreId = dp.Id
            WHERE d.Id = %s AND d.Eliminado = 0
        """
        resultado = self.db.select(query, (id_registro,))
        return self._serializar_fila(resultado[0]) if resultado else None

    def _validar_departamento_padre_existe(self, id_padre: int) -> bool:
        """Verifica que el departamento padre exista y esté activo"""
        query = "SELECT Id FROM Departamento WHERE Id = %s AND Eliminado = 0"
        resultado = self.db.select(query, (id_padre,))
        return len(resultado) > 0 if resultado else False

    def _validar_perfil_jefe_existe(self, id_perfil: int) -> bool:
        """Verifica que el perfil del jefe exista y esté activo"""
        query = """
            SELECT p.Id FROM Perfil p
            INNER JOIN Usuario u ON p.IdUsuario = u.Id
            WHERE p.Id = %s AND p.Eliminado = 0 AND u.Eliminado = 0
        """
        resultado = self.db.select(query, (id_perfil,))
        return len(resultado) > 0 if resultado else False

    def _validar_referencia_circular(self, id_registro: int, id_padre: int) -> bool:
        """Verifica que no se cree una referencia circular en la jerarquía"""
        if id_registro == id_padre:
            return True

        actual = id_padre
        visitados = set()
        while actual is not None:
            if actual in visitados or actual == id_registro:
                return True
            visitados.add(actual)

            query = "SELECT DepartamentoPadreId FROM Departamento WHERE Id = %s AND Eliminado = 0"
            resultado = self.db.select(query, (actual,))
            if resultado and resultado[0].get("DepartamentoPadreId"):
                actual = resultado[0]["DepartamentoPadreId"]
            else:
                actual = None

        return False

    def _validar_tiene_dependencias(self, id_registro: int) -> Optional[str]:
        """Verifica si tiene subdepartamentos, solicitudes, vehículos o motoristas activos"""
        # Subdepartamentos
        query = "SELECT COUNT(*) AS Total FROM Departamento WHERE DepartamentoPadreId = %s AND Eliminado = 0"
        resultado = self.db.select(query, (id_registro,))
        if resultado and resultado[0]["Total"] > 0:
            return "tiene subdepartamentos activos"

        # Solicitudes
        query = "SELECT COUNT(*) AS Total FROM Solicitud WHERE IdDepartamentoSolicitante = %s AND Eliminado = 0"
        resultado = self.db.select(query, (id_registro,))
        if resultado and resultado[0]["Total"] > 0:
            return "tiene solicitudes activas asociadas"

        # Vehículos
        query = "SELECT COUNT(*) AS Total FROM Vehiculo WHERE IdDepartamentoAsignado = %s AND Eliminado = 0"
        resultado = self.db.select(query, (id_registro,))
        if resultado and resultado[0]["Total"] > 0:
            return "tiene vehículos activos asignados"

        # Motoristas
        query = "SELECT COUNT(*) AS Total FROM DetallePerfilMotorista WHERE IdDepartamentoAsignado = %s AND Eliminado = 0"
        resultado = self.db.select(query, (id_registro,))
        if resultado and resultado[0]["Total"] > 0:
            return "tiene motoristas activos asignados"

        return None

    def _reactivar_registro(self, id_registro: int, datos: Dict) -> Dict:
        """Reactiva un registro previamente eliminado con datos nuevos"""
        ahora = datetime.now()
        query = """
            UPDATE Departamento
            SET Codigo = %s, Nombre = %s, IdPerfilJefe = %s,
                NombreJefe = %s, EmailJefe = %s, TelefonoJefe = %s,
                UbicacionFisica = %s, NivelJerarquico = %s, DepartamentoPadreId = %s,
                Eliminado = 0, FechaHoraEliminacion = NULL,
                FechaHoraActualizacion = %s
            WHERE Id = %s
        """
        params = (
            datos.get("codigo"), datos.get("nombre"), datos.get("idPerfilJefe"),
            datos.get("nombreJefe"), datos.get("emailJefe"), datos.get("telefonoJefe"),
            datos.get("ubicacionFisica"), datos.get("nivelJerarquico"),
            datos.get("departamentoPadreId"), ahora, id_registro
        )
        self.db.ejecutar(query, params, fetch=False, as_dict=False)
        registro = self._validar_existencia(id_registro)
        return {"data": registro}

    # ──────────────────────────────────────────────
    # CREAR
    # ──────────────────────────────────────────────

    def crear(self, datos: Dict) -> Dict:
        """Crea un nuevo departamento"""
        try:
            codigo = datos.get("codigo", "").strip().upper()
            nombre = datos.get("nombre", "").strip()
            id_perfil_jefe = datos.get("idPerfilJefe")
            nombre_jefe = datos.get("nombreJefe")
            if nombre_jefe: nombre_jefe = nombre_jefe.strip()
            email_jefe = datos.get("emailJefe")
            if email_jefe: email_jefe = email_jefe.strip()
            telefono_jefe = datos.get("telefonoJefe")
            if telefono_jefe: telefono_jefe = telefono_jefe.strip()
            ubicacion = datos.get("ubicacionFisica")
            if ubicacion: ubicacion = ubicacion.strip()
            nivel = datos.get("nivelJerarquico")
            id_padre = datos.get("departamentoPadreId")

            datos_completos = {
                "codigo": codigo, "nombre": nombre, "idPerfilJefe": id_perfil_jefe,
                "nombreJefe": nombre_jefe, "emailJefe": email_jefe,
                "telefonoJefe": telefono_jefe, "ubicacionFisica": ubicacion,
                "nivelJerarquico": nivel, "departamentoPadreId": id_padre
            }

            # Validar código único
            resultado_codigo = self._validar_codigo_unico(codigo)
            if not resultado_codigo.get("disponible"):
                if "error" in resultado_codigo:
                    return {"error": resultado_codigo["error"], "status": 409}
                if "eliminado_id" in resultado_codigo:
                    return self._reactivar_registro(resultado_codigo["eliminado_id"], datos_completos)

            # Validar departamento padre
            if id_padre is not None:
                if not self._validar_departamento_padre_existe(id_padre):
                    return {"error": f"El departamento padre con Id {id_padre} no existe o está eliminado", "status": 400}

            # Validar perfil jefe
            if id_perfil_jefe is not None:
                if not self._validar_perfil_jefe_existe(id_perfil_jefe):
                    return {"error": f"El perfil del jefe con Id {id_perfil_jefe} no existe o está eliminado", "status": 400}

            ahora = datetime.now()
            query_insert = """
                INSERT INTO Departamento
                    (Codigo, Nombre, IdPerfilJefe, NombreJefe, EmailJefe, TelefonoJefe,
                     UbicacionFisica, NivelJerarquico, DepartamentoPadreId,
                     Eliminado, FechaHoraCreacion, FechaHoraActualizacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0, %s, %s)
            """
            params = (
                codigo, nombre, id_perfil_jefe, nombre_jefe, email_jefe,
                telefono_jefe, ubicacion, nivel, id_padre, ahora, ahora
            )
            self.db.ejecutar(query_insert, params, fetch=False, as_dict=False)

            query_id = "SELECT MAX(Id) AS NuevoId FROM Departamento WHERE Codigo = %s AND Eliminado = 0"
            resultado_id = self.db.select(query_id, (codigo,))
            if not resultado_id or not resultado_id[0].get("NuevoId"):
                return {"error": "No se pudo obtener el ID del registro creado", "status": 500}

            registro = self._validar_existencia(int(resultado_id[0]["NuevoId"]))
            return {"data": registro}
        except Exception as e:
            logger.error(f"Error al crear Departamento: {e}")
            return {"error": f"Error interno al crear el registro: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # OBTENER POR ID
    # ──────────────────────────────────────────────

    def obtener_por_id(self, id_registro: int) -> Dict:
        """Obtiene un departamento por su ID"""
        try:
            registro = self._validar_existencia(id_registro)
            if not registro:
                return {"error": f"Departamento con Id {id_registro} no encontrado", "status": 404}
            return {"data": registro}
        except Exception as e:
            logger.error(f"Error al obtener Departamento {id_registro}: {e}")
            return {"error": f"Error interno al obtener el registro: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # LISTAR CON PAGINACIÓN Y FILTROS
    # ──────────────────────────────────────────────

    def listar(self, pagina: int = 1, por_pagina: int = 10,
               codigo: Optional[str] = None, nombre: Optional[str] = None,
               nivel_jerarquico: Optional[int] = None,
               id_padre: Optional[int] = None,
               busqueda: Optional[str] = None) -> Dict:
        """Lista departamentos con paginación y filtros"""
        try:
            if pagina < 1: pagina = 1
            if por_pagina < 1: por_pagina = 10
            if por_pagina > 100: por_pagina = 100

            where_clauses = ["d.Eliminado = 0"]
            params = []

            if codigo:
                where_clauses.append("d.Codigo LIKE %s")
                params.append(f"%{codigo}%")
            if nombre:
                where_clauses.append("d.Nombre LIKE %s")
                params.append(f"%{nombre}%")
            if nivel_jerarquico is not None:
                where_clauses.append("d.NivelJerarquico = %s")
                params.append(nivel_jerarquico)
            if id_padre is not None:
                where_clauses.append("d.DepartamentoPadreId = %s")
                params.append(id_padre)
            if busqueda:
                where_clauses.append(
                    "(d.Codigo LIKE %s OR d.Nombre LIKE %s OR d.NombreJefe LIKE %s OR d.UbicacionFisica LIKE %s)"
                )
                termino = f"%{busqueda}%"
                params.extend([termino, termino, termino, termino])

            where_sql = " AND ".join(where_clauses)

            count_query = f"""
                SELECT COUNT(*) AS Total FROM Departamento d
                LEFT JOIN Departamento dp ON d.DepartamentoPadreId = dp.Id
                WHERE {where_sql}
            """
            total_result = self.db.select(count_query, tuple(params))
            total = total_result[0]["Total"] if total_result else 0

            offset = (pagina - 1) * por_pagina
            params_paginados = params + [offset, por_pagina]

            query = f"""
                SELECT {self.COLUMNAS_SELECT}
                FROM Departamento d
                LEFT JOIN Departamento dp ON d.DepartamentoPadreId = dp.Id
                WHERE {where_sql}
                ORDER BY d.NivelJerarquico ASC, d.Nombre ASC
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
            logger.error(f"Error al listar Departamento: {e}")
            return {"error": f"Error interno al listar registros: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # LISTAR SIN PAGINACIÓN
    # ──────────────────────────────────────────────

    def listar_todos(self, codigo: Optional[str] = None, nombre: Optional[str] = None,
                     nivel_jerarquico: Optional[int] = None,
                     id_padre: Optional[int] = None,
                     busqueda: Optional[str] = None) -> Dict:
        """Lista todos los departamentos activos sin paginación"""
        try:
            where_clauses = ["d.Eliminado = 0"]
            params = []

            if codigo:
                where_clauses.append("d.Codigo LIKE %s")
                params.append(f"%{codigo}%")
            if nombre:
                where_clauses.append("d.Nombre LIKE %s")
                params.append(f"%{nombre}%")
            if nivel_jerarquico is not None:
                where_clauses.append("d.NivelJerarquico = %s")
                params.append(nivel_jerarquico)
            if id_padre is not None:
                where_clauses.append("d.DepartamentoPadreId = %s")
                params.append(id_padre)
            if busqueda:
                where_clauses.append(
                    "(d.Codigo LIKE %s OR d.Nombre LIKE %s OR d.NombreJefe LIKE %s OR d.UbicacionFisica LIKE %s)"
                )
                termino = f"%{busqueda}%"
                params.extend([termino, termino, termino, termino])

            where_sql = " AND ".join(where_clauses)

            query = f"""
                SELECT {self.COLUMNAS_SELECT}
                FROM Departamento d
                LEFT JOIN Departamento dp ON d.DepartamentoPadreId = dp.Id
                WHERE {where_sql}
                ORDER BY d.NivelJerarquico ASC, d.Nombre ASC
            """
            registros = self.db.select(query, tuple(params))
            return {"data": [self._serializar_fila(r) for r in registros] if registros else []}
        except Exception as e:
            logger.error(f"Error al listar todos Departamento: {e}")
            return {"error": f"Error interno al listar registros: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # ACTUALIZAR
    # ──────────────────────────────────────────────

    def actualizar(self, id_registro: int, datos: Dict) -> Dict:
        """Actualiza un departamento existente"""
        try:
            existente = self._validar_existencia(id_registro)
            if not existente:
                return {"error": f"Departamento con Id {id_registro} no encontrado", "status": 404}

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

            # Validar departamento padre
            if "departamentoPadreId" in campos_actualizar:
                id_padre = campos_actualizar["departamentoPadreId"]
                if not self._validar_departamento_padre_existe(id_padre):
                    return {"error": f"El departamento padre con Id {id_padre} no existe o está eliminado", "status": 400}
                if self._validar_referencia_circular(id_registro, id_padre):
                    return {"error": "No se puede asignar este departamento padre porque crearía una referencia circular", "status": 400}

            # Validar perfil jefe
            if "idPerfilJefe" in campos_actualizar:
                id_perfil = campos_actualizar["idPerfilJefe"]
                if not self._validar_perfil_jefe_existe(id_perfil):
                    return {"error": f"El perfil del jefe con Id {id_perfil} no existe o está eliminado", "status": 400}

            ahora = datetime.now()
            mapeo = {
                "codigo": "Codigo", "nombre": "Nombre", "idPerfilJefe": "IdPerfilJefe",
                "nombreJefe": "NombreJefe", "emailJefe": "EmailJefe",
                "telefonoJefe": "TelefonoJefe", "ubicacionFisica": "UbicacionFisica",
                "nivelJerarquico": "NivelJerarquico", "departamentoPadreId": "DepartamentoPadreId"
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

            query = f"UPDATE Departamento SET {', '.join(set_parts)} WHERE Id = %s AND Eliminado = 0"
            self.db.ejecutar(query, tuple(params), fetch=False, as_dict=False)

            registro = self._validar_existencia(id_registro)
            return {"data": registro}
        except Exception as e:
            logger.error(f"Error al actualizar Departamento {id_registro}: {e}")
            return {"error": f"Error interno al actualizar el registro: {str(e)}", "status": 500}

    # ──────────────────────────────────────────────
    # ELIMINAR (soft delete)
    # ──────────────────────────────────────────────

    def eliminar(self, id_registro: int) -> Dict:
        """Eliminación lógica de un departamento"""
        try:
            existente = self._validar_existencia(id_registro)
            if not existente:
                return {"error": f"Departamento con Id {id_registro} no encontrado", "status": 404}

            dependencia = self._validar_tiene_dependencias(id_registro)
            if dependencia:
                return {
                    "error": f"No se puede eliminar este departamento porque {dependencia}",
                    "status": 409
                }

            ahora = datetime.now()
            query = """
                UPDATE Departamento SET Eliminado = 1,
                    FechaHoraEliminacion = %s, FechaHoraActualizacion = %s
                WHERE Id = %s AND Eliminado = 0
            """
            self.db.ejecutar(query, (ahora, ahora, id_registro), fetch=False, as_dict=False)
            return {"data": {"mensaje": f"Departamento '{existente['Nombre']}' eliminado exitosamente"}}
        except Exception as e:
            logger.error(f"Error al eliminar Departamento {id_registro}: {e}")
            return {"error": f"Error interno al eliminar el registro: {str(e)}", "status": 500}