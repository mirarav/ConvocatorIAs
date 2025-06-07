"""
Módulo para centralizar la configuración de todos los componentes.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Accede a las variables de entorno."""

    @property
    def SCRAPING_CONFIG(self) -> Dict[str, Any]:
        """Configuración para el servicio de scraping."""
        return {
            'user_agent': os.getenv('SCRAPING_USER_AGENT'),
            'timeout': int(os.getenv('SCRAPING_TIMEOUT')),
            'max_intentos': int(os.getenv('SCRAPING_MAX_RETRIES')),
            'headless': os.getenv('PLAYWRIGHT_HEADLESS').lower() == 'true',
            'slow_mo': int(os.getenv('PLAYWRIGHT_SLOW_MO'))
        }

    @property
    def DB_CONFIG(self) -> Dict[str, Any]:
        """Configuración para la conexión a PostgreSQL."""
        return {
            'host': os.getenv('POSTGRES_HOST'),
            'port': os.getenv('POSTGRES_PORT'),
            'dbname': os.getenv('POSTGRES_DB'),
            'user': os.getenv('POSTGRES_USER'),
            'password': os.getenv('POSTGRES_PASSWORD')
        }

    @property
    def LLM_CONFIG(self) -> Dict[str, Any]:
        """Configuración para el servicio de Azure OpenAI."""
        return {
            'api_key': os.getenv('AZURE_OPENAI_API_KEY'),
            'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
            'api_version': os.getenv('AZURE_OPENAI_API_VERSION'),
            'deployment_name': os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
        }