# database/sql_connection.py
import re
import logging
from typing import Any, Optional, Union, List, Dict
from contextlib import contextmanager
import pymssql
from config import get_settings

# Obtener settings perezosamente
settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# Utilidades
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _safe_ident(name: str) -> str:
    """Valida nombres de tablas y columnas"""
    if not name or not _IDENT_RE.match(name):
        raise ValueError(f"Identificador SQL inválido: {name!r}")
    return name



# Gestor SQL Server
class SQLServerManager:
    """
    Gestor mejorado para SQL Server usando pymssql.
    Ejecuta cualquier tipo de consulta con manejo automático de commits.
    Configuración cargada desde config.py (settings.sqlserver).
    """

    def __init__(self):
        """
        Inicializa el gestor con configuración desde settings.sqlserver
        """
        self.server = settings.sqlserver.HOST
        self.port = settings.sqlserver.PORT
        self.database = settings.sqlserver.NAME
        self.username = settings.sqlserver.USER
        self.password = settings.sqlserver.PASSWORD

        self._validar_configuracion()

    def _validar_configuracion(self):
        """Valida que todas las configuraciones necesarias estén presentes"""
        missing = []

        if not self.server:
            missing.append("SQL_HOST")
        if not self.database:
            missing.append("SQL_NAME")
        if not self.username:
            missing.append("SQL_USER")
        if not self.password:
            missing.append("SQL_PASSWORD")

        if missing:
            raise EnvironmentError(
                f"Faltan configuraciones de SQL Server en .env: {', '.join(missing)}\n"
                f"Asegúrate de definir: SQL_HOST, SQL_PORT, SQL_NAME, SQL_USER, SQL_PASSWORD"
            )

    
    # Gestión de Conexión
    @contextmanager
    def conexion(self):
        """
        Context manager para manejar conexiones a SQL Server.
        Yields:
            pymssql.Connection: Conexión activa a la base de datos
        Raises:
            Exception: Si hay algun error en la conexión
        """
        conn = None
        try:
            conn = pymssql.connect(
                server=self.server,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.database,
                timeout=30,
                login_timeout=15,
                as_dict=False  # Lo manejamos en el cursor
            )
            logging.info(
                f"✓ Conectado a SQL Server [{self.database}] en {self.server}:{self.port}"
            )
            yield conn

        except pymssql.Error as e:
            logging.error(f"✗ Error de conexión SQL Server: {e}")
            raise
        except Exception as e:
            logging.error(f"✗ Error inesperado en conexión: {e}")
            raise
        finally:
            if conn:
                conn.close()
                logging.info(f"✓ Conexión cerrada [{self.database}]")

    
    # Metodo Principal de Ejecución de Consultas
    def ejecutar(
            self,
            query: str,
            params: Optional[Union[tuple, list]] = None,
            fetch: bool = None,
            as_dict: bool = True
    ) -> Union[List[Dict], List[tuple], int]:
        """
        Ejecuta cualquier consulta SQL con manejo automático de commits.

        Args:
            query: Consulta SQL a ejecutar
            params: Parámetros para la consulta (previene SQL injection)
            fetch: True para SELECT, False para DML, None para auto-detectar
            as_dict: Si True, devuelve diccionarios; si False, devuelve tuplas

        Returns:
            - Para SELECT: Lista de filas (dict o tuplas según as_dict)
            - Para INSERT/UPDATE/DELETE: Número de filas afectadas
            - Para consultas con SCOPE_IDENTITY(): El ID generado

        Raises:
            Exception: Si hay algun error en la ejecución de la consulta
        """
        if not query or not isinstance(query, str):
            raise ValueError("La consulta debe ser una cadena no vacía")

        # Normalizar parámetros
        if params is None:
            params = ()
        elif isinstance(params, list):
            params = tuple(params)
        elif not isinstance(params, tuple):
            params = (params,)

        # Auto-detectar tipo de consulta
        query_upper = query.strip().upper()
        es_select = query_upper.startswith('SELECT') or query_upper.startswith('WITH')

        if fetch is None:
            fetch = es_select

        conn = None
        try:
            with self.conexion() as conn:
                cursor = conn.cursor(as_dict=as_dict)

                # Ejecutar query
                logging.info(f"Ejecutando query: {query[:100]}...")
                cursor.execute(query, params)

                # Manejar SELECT
                if fetch:
                    resultados = cursor.fetchall()
                    logging.info(f"✓ SELECT completado: {len(resultados)} fila(s)")
                    return resultados

                # Manejar INSERT/UPDATE/DELETE
                filas_afectadas = cursor.rowcount

                # Intentar obtener SCOPE_IDENTITY() o OUTPUT
                id_generado = None
                try:
                    resultado = cursor.fetchone()
                    if resultado:
                        # Si as_dict=True, resultado es un dict; si False, es tupla
                        if as_dict and isinstance(resultado, dict):
                            id_generado = list(resultado.values())[0]
                        elif isinstance(resultado, tuple):
                            id_generado = resultado[0]
                        else:
                            id_generado = resultado
                except Exception:
                    pass

                # Commit automático para DML
                conn.commit()

                tipo_query = "INSERT" if "INSERT" in query_upper else \
                    "UPDATE" if "UPDATE" in query_upper else \
                        "DELETE" if "DELETE" in query_upper else "DML"

                logging.info(
                    f"✓ {tipo_query} completado: {filas_afectadas} fila(s) afectada(s)"
                )

                # Devolver ID generado si existe, sino filas afectadas
                if id_generado is not None:
                    try:
                        return int(id_generado)
                    except (ValueError, TypeError):
                        return id_generado

                return filas_afectadas

        except pymssql.Error as e:
            logging.error(f"✗ Error SQL: {e}")
            if conn:
                conn.rollback()
                logging.info("✓ Rollback ejecutado")

            # Devolver resultado vacío según el tipo
            return [] if fetch else 0

        except Exception as e:
            logging.error(f"✗ Error inesperado: {e}")
            if conn:
                conn.rollback()
                logging.info("✓ Rollback ejecutado")

            return [] if fetch else 0

    
    # Métodos de Conveniencia
    
    def select(
            self,
            query: str,
            params: Optional[Union[tuple, list]] = None,
            as_dict: bool = True
        ) -> List[Dict]:
        """
    ) -> List[Dict]:

        Args:
            query: Consulta SELECT
            params: Parámetros opcionales
            as_dict: Si True devuelve dicts, si False tuplas

        Returns:
            Lista de filas como diccionarios o tuplas
        """
        return self.ejecutar(query, params, fetch=True, as_dict=as_dict)

    def insert(
            self,
            query: str,
            params: Optional[Union[tuple, list]] = None,
            return_id: bool = False
        ) -> Union[int, Any]:
        """
    ) -> Union[int, Any]:

        Args:
            query: Consulta INSERT
            params: Parámetros opcionales
            return_id: Si True, intenta devolver el ID generado

        Returns:
            ID generado (si return_id=True y existe) o filas afectadas
        """
        if return_id and "SCOPE_IDENTITY()" not in query.upper():
            query = query.rstrip(';') + "; SELECT SCOPE_IDENTITY();"

        return self.ejecutar(query, params, fetch=False)

    def update(
            self,
            query: str,
            params: Optional[Union[tuple, list]] = None
        ) -> int:
        """
    ) -> int:

        Args:
            query: Consulta UPDATE
            params: Parámetros opcionales

        Returns:
            Número de filas afectadas
        """
        return self.ejecutar(query, params, fetch=False)

    def delete(
            self,
            query: str,
            params: Optional[Union[tuple, list]] = None
        ) -> int:
        """
    ) -> int:

        Args:
            query: Consulta DELETE
            params: Parámetros opcionales

        Returns:
            Número de filas afectadas
        """
        return self.ejecutar(query, params, fetch=False)

    def execute_many(
            self,
            query: str,
            params_list: List[tuple]
        ) -> int:
        """
    ) -> int:
        Útil para inserts o updates masivos.

        Args:
            query: Consulta SQL a ejecutar
            params_list: Lista de tuplas con parámetros

        Returns:
            Total de filas afectadas
        """
        if not params_list:
            raise ValueError("params_list no puede estar vacío")

        conn = None
        total_afectadas = 0

        try:
            with self.conexion() as conn:
                cursor = conn.cursor()

                for params in params_list:
                    cursor.execute(query, params)
                    total_afectadas += cursor.rowcount

                conn.commit()
                logging.info(
                    f"✓ Ejecución múltiple completada: {total_afectadas} fila(s) "
                    f"afectada(s) en {len(params_list)} operación(es)"
                )

                return total_afectadas

        except Exception as e:
            logging.error(f"✗ Error en execute_many: {e}")
            if conn:
                conn.rollback()
                logging.info("✓ Rollback ejecutado")
            return 0

    
    # Helpers CRUD con validación
    
    def insert_dict(
            self,
            table_name: str,
            data: Dict[str, Any],
            return_id: bool = True
    ) -> Union[int, Any]:
        """
        Inserta un diccionario como nueva fila.

        Args:
            table_name: Nombre de la tabla
            data: Diccionario con columna: valor
            return_id: Si True, devuelve el ID generado

        Returns:
            ID generado o filas afectadas
        """
        table = _safe_ident(table_name)
        if not data:
            raise ValueError("data no puede estar vacío")

        cols = [_safe_ident(c) for c in data.keys()]
        values = tuple(data.values())

        columns_sql = ", ".join(cols)
        placeholders = ", ".join(["%s"] * len(values))

        query = f"INSERT INTO {table} ({columns_sql}) VALUES ({placeholders})"

        return self.insert(query, values, return_id=return_id)

    def update_dict(
            self,
            table_name: str,
            data: Dict[str, Any],
            where: str,
            where_params: Union[tuple, list]
    ) -> int:
        """
        Actualiza filas usando un diccionario.

        Args:
            table_name: Nombre de la tabla
            data: Diccionario con columna: nuevo_valor
            where: Cláusula WHERE (ej: "id = %s")
            where_params: Parámetros para WHERE

        Returns:
            Número de filas actualizadas
        """
        table = _safe_ident(table_name)
        if not data:
            raise ValueError("data no puede estar vacío")
        if not where or not where_params:
            raise ValueError("WHERE es obligatorio para evitar UPDATE masivo")

        cols = [_safe_ident(c) for c in data.keys()]
        set_sql = ", ".join([f"{c} = %s" for c in cols])

        values = tuple(data.values())
        if isinstance(where_params, list):
            where_params = tuple(where_params)

        all_params = values + where_params

        query = f"UPDATE {table} SET {set_sql} WHERE {where}"
        return self.update(query, all_params)

    def delete_where(
            self,
            table_name: str,
            where: str,
            where_params: Union[tuple, list]
    ) -> int:
        """
        Elimina filas con una cláusula WHERE.

        Args:
            table_name: Nombre de la tabla
            where: Cláusula WHERE (ej: "id = %s")
            where_params: Parámetros para WHERE

        Returns:
            Número de filas eliminadas
        """
        table = _safe_ident(table_name)
        if not where or not where_params:
            raise ValueError("WHERE es obligatorio para evitar DELETE masivo")

        query = f"DELETE FROM {table} WHERE {where}"
        return self.delete(query, where_params)

    
    # Utilidades de Información
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión a la base de datos.

        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        try:
            resultado = self.select("SELECT 1 AS test")
            return len(resultado) > 0
        except Exception as e:
            logging.error(f"✗ Test de conexión fallido: {e}")
            return False

    def get_tables(self) -> List[str]:
        """
        Obtiene la lista de tablas en la base de datos.

        Returns:
            Lista de nombres de tablas
        """
        query = """
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME \
                """
        resultados = self.select(query)
        return [r['TABLE_NAME'] for r in resultados] if resultados else []

    def get_table_info(self, table_name: str) -> List[Dict]:
        """
        Obtiene información de las columnas de una tabla.

        Args:
            table_name: Nombre de la tabla

        Returns:
            Lista de diccionarios con información de columnas
        """
        table = _safe_ident(table_name)
        query = """
                SELECT COLUMN_NAME, \
                       DATA_TYPE, \
                       CHARACTER_MAXIMUM_LENGTH, \
                       IS_NULLABLE, \
                       COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION \
                """
        return self.select(query, (table,))



# Instancia global (Singleton)

_sql_manager_instance = None


def get_sql_manager() -> SQLServerManager:
    """
    Retorna la instancia global de SQLServerManager (Singleton).

    Returns:
        Instancia de SQLServerManager
    """
    global _sql_manager_instance
    if _sql_manager_instance is None:
        _sql_manager_instance = SQLServerManager()
    return _sql_manager_instance