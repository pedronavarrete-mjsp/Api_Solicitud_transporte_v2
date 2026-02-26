# config.py
"""
Módulo de configuración para Backend ONI Justicia.
Carga variables de entorno desde archivo .env y las expone como objetos de configuración.
"""

import os
from typing import Optional, Literal
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno desde .env
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class MongoDBConfig:
    """Configuración de MongoDB"""

    def __init__(self):
        # Opción 1: URL directa (tiene prioridad)
        self.URL: Optional[str] = os.getenv('DB_URL')

        # Opción 2: Variables individuales
        self.HOST: str = os.getenv('DB_HOST', 'localhost')
        self.PORT: int = int(os.getenv('DB_PORT', '27017'))
        self.NAME: str = os.getenv('DB_NAME', 'dev_oni_justicia')
        self.USER: str = os.getenv('DB_USER', 'admin')
        self.PASSWORD: str = os.getenv('DB_PASSWORD', '')
        self.AUTH_DB: str = os.getenv('DB_AUTH_DB', 'admin')

    def get_connection_string(self) -> str:
        """Retorna la cadena de conexión de MongoDB"""
        if self.URL:
            return self.URL

        # Construir URL desde variables individuales
        auth = f"{self.USER}:{self.PASSWORD}@" if self.USER and self.PASSWORD else ""
        auth_source = f"?authSource={self.AUTH_DB}" if self.AUTH_DB else ""

        return f"mongodb://{auth}{self.HOST}:{self.PORT}/{self.NAME}{auth_source}"


class SQLServerConfig:
    """Configuración de SQL Server"""

    def __init__(self):
        self.ENGINE: str = os.getenv('SQL_ENGINE', 'mssql')
        self.HOST: str = os.getenv('SQL_HOST', 'localhost')
        self.PORT: int = int(os.getenv('SQL_PORT', '1433'))
        self.NAME: str = os.getenv('SQL_NAME', '')
        self.USER: str = os.getenv('SQL_USER', '')
        self.PASSWORD: str = os.getenv('SQL_PASSWORD', '')

    def get_connection_string(self) -> str:
        """Retorna la cadena de conexión de SQL Server usando pymssql (no requiere ODBC)"""
        return (
            f"mssql+pymssql://{self.USER}:{self.PASSWORD}@"
            f"{self.HOST}:{self.PORT}/{self.NAME}"
        )


class AppConfig:
    """Configuración general de la aplicación"""

    def __init__(self):
        self.TITLE: str = os.getenv('API_TITLE', 'Backend ONI Justicia')
        self.VERSION: str = os.getenv('API_VERSION', '1.0.0')
        self.DEBUG: bool = os.getenv('API_DEBUG', 'false').lower() == 'true'
        self.LOG_LEVEL: str = os.getenv('API_LOG_LEVEL', 'INFO')
        self.LOG_FORMAT: str = os.getenv('API_LOG_FORMAT', 'text')
        self.TIMEZONE: str = os.getenv('TIMEZONE', 'America/El_Salvador')


class APICredentials:
    """Credenciales de la API"""

    def __init__(self):
        self.USER: str = os.getenv('API_USER', 'api_user')
        self.PASSWORD: str = os.getenv('API_PASSWORD', '')


class JWTConfig:
    """Configuración de JWT"""

    def __init__(self):
        self.SECRET: str = os.getenv('JWT_SECRET', '')
        self.ALGORITHM: str = os.getenv('JWT_ALGORITHM', 'HS256')
        self.ACCESS_TOKEN_EXP_VALUE: int = int(os.getenv('JWT_ACCESS_TOKEN_EXP_VALUE', '60'))
        self.ACCESS_TOKEN_EXP_UNIT: Literal['minutes', 'hours'] = os.getenv('JWT_ACCESS_TOKEN_EXP_UNIT', 'minutes')
        self.REFRESH_TOKEN_EXP_VALUE: int = int(os.getenv('JWT_REFRESH_TOKEN_EXP_VALUE', '24'))
        self.REFRESH_TOKEN_EXP_UNIT: Literal['minutes', 'hours'] = os.getenv('JWT_REFRESH_TOKEN_EXP_UNIT', 'hours')


class MFAConfig:
    """Configuración de MFA (Multi-Factor Authentication)"""

    def __init__(self):
        self.ISSUER_NAME: str = os.getenv('MFA_ISSUER_NAME', 'ONI_Justicia')
        self.VALID_WINDOW: int = int(os.getenv('MFA_VALID_WINDOW', '1'))


class EmailConfig:
    """Configuración de Email"""

    def __init__(self):
        self.USER: str = os.getenv('EMAIL_USER', '')
        self.PASSWORD: str = os.getenv('EMAIL_PASSWORD', '')
        self.SMTP_HOST: str = os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com')
        self.SMTP_PORT: int = int(os.getenv('EMAIL_SMTP_PORT', '587'))
        self.USE_TLS: bool = os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true'


class SOTIConfig:
    """Configuración de SOTI MDM"""

    def __init__(self):
        self.TENANT: str = os.getenv('SOTI_TENANT', '')
        self.TOKEN_URL: str = os.getenv('SOTI_TOKEN_URL', '')
        self.CLIENT_ID: str = os.getenv('SOTI_CLIENT_ID', '')
        self.CLIENT_SECRET: str = os.getenv('SOTI_CLIENT_SECRET', '')
        self.USERNAME: str = os.getenv('SOTI_USERNAME', '')
        self.PASSWORD: str = os.getenv('SOTI_PASSWORD', '')


class Settings:
    """Clase principal de configuración que agrupa todas las configuraciones"""

    def __init__(self):
        self.mongodb = MongoDBConfig()
        self.sqlserver = SQLServerConfig()
        self.app = AppConfig()
        self.api_credentials = APICredentials()
        self.jwt = JWTConfig()
        self.mfa = MFAConfig()
        self.email = EmailConfig()
        self.soti = SOTIConfig()

    def validate(self) -> list[str]:
        """Valida que las configuraciones críticas estén presentes"""
        errors = []

        # Validar JWT
        if not self.jwt.SECRET:
            errors.append("JWT_SECRET no está configurado")

        # Validar credenciales de API
        if not self.api_credentials.PASSWORD:
            errors.append("API_PASSWORD no está configurado")

        # Validar MongoDB
        if not self.mongodb.URL and not self.mongodb.PASSWORD:
            errors.append("DB_PASSWORD o DB_URL deben estar configurados")

        # Validar SQL Server
        if not self.sqlserver.PASSWORD:
            errors.append("SQL_PASSWORD no está configurado")

        return errors


# Instancia global de configuración
settings = Settings()

# Validar configuración al importar (opcional, comentar si no se desea)
validation_errors = settings.validate()
if validation_errors:
    import warnings

    for error in validation_errors:
        warnings.warn(f"Configuración incompleta: {error}")


# Función de utilidad para obtener configuraciones
def get_settings() -> Settings:
    """Retorna la instancia de configuración global"""
    return settings


# Exportar para facilitar importaciones
__all__ = [
    'settings',
    'get_settings',
    'MongoDBConfig',
    'SQLServerConfig',
    'AppConfig',
    'APICredentials',
    'JWTConfig',
    'MFAConfig',
    'EmailConfig',
    'SOTIConfig',
    'Settings'
]