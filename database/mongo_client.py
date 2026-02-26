# database/mongo_client.py
import logging
from pymongo import MongoClient, errors
from config import get_settings

# Obtener settings perezosamente
settings = get_settings()

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# ---------------------------- Variables globales ----------------------------
_client = None
_db = None


def init_mongo():
    """Inicializa la conexión global a MongoDB si no existe."""
    global _client, _db

    if _client is not None:
        return  # Ya está inicializado

    try:
        # Obtener la URL de conexión desde settings
        connection_url = settings.mongodb.get_connection_string()

        logging.info(f"Conectando a MongoDB en {settings.mongodb.HOST}:{settings.mongodb.PORT}...")

        _client = MongoClient(
            connection_url,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=50,
            minPoolSize=1,
            retryWrites=True
        )

        # Verificar conexión con ping
        _client.admin.command('ping')

        # Asignar base de datos activa
        _db = _client[settings.mongodb.NAME]

        logging.info(f"✓ Conexión persistente establecida con la base de datos '{settings.mongodb.NAME}'")

    except errors.ConnectionFailure as e:
        logging.error(f"✗ No se pudo conectar a MongoDB: {e}")
        raise
    except Exception as e:
        logging.error(f"✗ Error conectando a MongoDB: {e}")
        raise


def get_db():
    """Devuelve la base de datos inicializada."""
    if _db is None:
        init_mongo()
    return _db


def close_connection():
    """Cierra la conexión global a MongoDB."""
    global _client, _db

    if _client is not None:
        _client.close()
        _client = None
        _db = None
        logging.info("✓ Conexión a MongoDB cerrada")


# ---------------------------- Operaciones CRUD ----------------------------

def ejecutar_query(collection_name: str, filtro: dict = None) -> list[dict]:
    """
    Ejecuta una consulta básica en una colección.

    Args:
        collection_name: Nombre de la colección
        filtro: Filtro para la búsqueda

    Returns:
        Lista de documentos encontrados
    """
    filtro = filtro or {}
    try:
        resultados = list(get_db()[collection_name].find(filtro))
        logging.info(
            f"✓ Consulta ejecutada en '{collection_name}', "
            f"documentos obtenidos: {len(resultados)}"
        )
        return resultados
    except Exception as e:
        logging.error(f"✗ Error ejecutando consulta en '{collection_name}': {e}")
        return []


def ejecutar_query_V2(
        collection_name: str,
        filtro: dict = None,
        projection: dict = None
) -> list[dict]:
    """
    Ejecuta una consulta con proyección personalizada.

    Args:
        collection_name: Nombre de la colección
        filtro: Filtro para la búsqueda
        projection: Campos a incluir/excluir en el resultado

    Returns:
        Lista de documentos encontrados
    """
    filtro = filtro or {}
    if projection is None:
        projection = {"_id": 0}

    try:
        resultados = list(get_db()[collection_name].find(filtro, projection))
        logging.info(
            f"✓ Consulta ejecutada en '{collection_name}', "
            f"documentos obtenidos: {len(resultados)}"
        )
        return resultados
    except Exception as e:
        logging.error(f"✗ Error ejecutando consulta en '{collection_name}': {e}")
        return []


def ejecutar_query_V3(
        collection_name: str,
        filtro: dict = None,
        projection: dict = None,
        skip: int = 0,
        limit: int = 20,
        sort: list[tuple] = None
) -> list[dict]:
    """
    Ejecuta una consulta con paginación, proyección y ordenamiento.

    Args:
        collection_name: Nombre de la colección
        filtro: Filtro para la búsqueda
        projection: Campos a incluir/excluir
        skip: Número de documentos a saltar (para paginación)
        limit: Número máximo de documentos a retornar
        sort: Lista de tuplas (campo, dirección) para ordenamiento

    Returns:
        Lista de documentos encontrados
    """
    filtro = filtro or {}
    projection = projection or {"_id": 0}

    try:
        cursor = get_db()[collection_name].find(filtro, projection)

        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)

        resultados = list(cursor)

        logging.info(
            f"✓ Consulta ejecutada en '{collection_name}', "
            f"documentos obtenidos: {len(resultados)} (skip={skip}, limit={limit})"
        )
        return resultados
    except Exception as e:
        logging.error(f"✗ Error ejecutando consulta en '{collection_name}': {e}")
        return []


def insert_document(collection_name: str, data: dict) -> str | None:
    """
    Inserta un documento en una colección.

    Args:
        collection_name: Nombre de la colección
        data: Documento a insertar

    Returns:
        ID del documento insertado o None si falló
    """
    try:
        result = get_db()[collection_name].insert_one(data)
        logging.info(
            f"✓ Documento insertado en '{collection_name}' con _id: {result.inserted_id}"
        )
        return str(result.inserted_id)
    except Exception as e:
        logging.error(f"✗ Error insertando documento en '{collection_name}': {e}")
        return None


def insert_many_documents(collection_name: str, data_list: list[dict]) -> list[str]:
    """
    Inserta múltiples documentos en una colección.

    Args:
        collection_name: Nombre de la colección
        data_list: Lista de documentos a insertar

    Returns:
        Lista de IDs de los documentos insertados
    """
    try:
        result = get_db()[collection_name].insert_many(data_list)
        logging.info(
            f"✓ {len(result.inserted_ids)} documentos insertados en '{collection_name}'"
        )
        return [str(_id) for _id in result.inserted_ids]
    except Exception as e:
        logging.error(f"✗ Error insertando documentos en '{collection_name}': {e}")
        return []


def update_document(
        collection_name: str,
        filtro: dict,
        update: dict,
        multiple: bool = False
) -> int:
    """
    Actualiza uno o varios documentos en una colección.

    Args:
        collection_name: Nombre de la colección
        filtro: Filtro para identificar documentos
        update: Operaciones de actualización
        multiple: Si True, actualiza todos los documentos que coincidan

    Returns:
        Número de documentos modificados
    """
    try:
        result = (
            get_db()[collection_name].update_many(filtro, update)
            if multiple else
            get_db()[collection_name].update_one(filtro, update)
        )
        logging.info(
            f"✓ {result.modified_count} documento(s) actualizados en '{collection_name}'"
        )
        return result.modified_count
    except Exception as e:
        logging.error(f"✗ Error actualizando documentos en '{collection_name}': {e}")
        return 0


def update_document2(
        collection_name: str,
        filtro: dict,
        update: dict,
        multiple: bool = False,
        upsert: bool = False
) -> int:
    """
    Actualiza documentos con opción de upsert.

    Args:
        collection_name: Nombre de la colección
        filtro: Filtro para identificar documentos
        update: Operaciones de actualización
        multiple: Si True, actualiza todos los documentos que coincidan
        upsert: Si True, inserta el documento si no existe

    Returns:
        Número de documentos modificados
    """
    try:
        if multiple:
            result = get_db()[collection_name].update_many(filtro, update, upsert=upsert)
        else:
            result = get_db()[collection_name].update_one(filtro, update, upsert=upsert)

        logging.info(
            f"✓ {result.modified_count} documento(s) actualizados en '{collection_name}'"
        )
        return result.modified_count
    except Exception as e:
        logging.error(f"✗ Error actualizando documentos en '{collection_name}': {e}")
        return 0


def delete_document(
        collection_name: str,
        filtro: dict,
        multiple: bool = False
) -> int:
    """
    Elimina uno o varios documentos de una colección.

    Args:
        collection_name: Nombre de la colección
        filtro: Filtro para identificar documentos
        multiple: Si True, elimina todos los documentos que coincidan

    Returns:
        Número de documentos eliminados
    """
    try:
        result = (
            get_db()[collection_name].delete_many(filtro)
            if multiple else
            get_db()[collection_name].delete_one(filtro)
        )
        logging.info(
            f"✓ {result.deleted_count} documento(s) eliminados de '{collection_name}'"
        )
        return result.deleted_count
    except Exception as e:
        logging.error(f"✗ Error eliminando documentos de '{collection_name}': {e}")
        return 0


def aggregate(collection_name: str, pipeline: list[dict]) -> list[dict]:
    """
    Ejecuta un pipeline de agregación en una colección.

    Args:
        collection_name: Nombre de la colección
        pipeline: Pipeline de agregación

    Returns:
        Lista de documentos resultantes
    """
    try:
        resultados = list(get_db()[collection_name].aggregate(pipeline))
        logging.info(
            f"✓ Agregación ejecutada en '{collection_name}', "
            f"documentos obtenidos: {len(resultados)}"
        )
        return resultados
    except Exception as e:
        logging.error(f"✗ Error ejecutando agregación en '{collection_name}': {e}")
        return []


def count_documents(collection_name: str, filtro: dict = None) -> int:
    """
    Cuenta el número de documentos que coinciden con un filtro.

    Args:
        collection_name: Nombre de la colección
        filtro: Filtro para la búsqueda

    Returns:
        Número de documentos encontrados
    """
    filtro = filtro or {}
    try:
        count = get_db()[collection_name].count_documents(filtro)
        logging.info(
            f"✓ Conteo en '{collection_name}': {count} documento(s) encontrados"
        )
        return count
    except Exception as e:
        logging.error(f"✗ Error contando documentos en '{collection_name}': {e}")
        return 0


def test_connection() -> bool:
    """
    Prueba la conexión a MongoDB.

    Returns:
        True si la conexión es exitosa, False en caso contrario
    """
    try:
        init_mongo()
        return True
    except Exception as e:
        logging.error(f"✗ Test de conexión a MongoDB fallido: {e}")
        return False