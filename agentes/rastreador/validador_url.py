"""
Módulo para validar URLs y determinar el organismo responsable según el dominio.
"""

from urllib.parse import urlparse

class UrlValidator:
    """Valida URLs y determina organismos a partir del dominio."""

    ORGANISMOS = {
        'ader.es': 'ADER', 'aei.gob.es': 'AEI', 'cdti.es': 'CDTI', 
        'comunidad.madrid': 'Comunidad de Madrid', 'xunta.gal': 'GAIN',
        'aragon.es': 'Gobierno de Aragón', 'cantabria.es': 'Gobierno de Cantabria',
        'navarra.es': 'Gobierno de Navarra', 'ivace.es': 'IVACE', 
        'digital.gob.es': 'Gobierno de España', 'red.gob.es': 'Red',
        'sodercan.es': 'SODERCAN', 'spri.eus': 'SPRI', 'andaluciatrade.es': 'TRADE'
    }

    def es_valida(self, url: str) -> bool:
        """Verifica si es una URL válida."""
        try:
            parsed = urlparse(url)
            return all([parsed.scheme, parsed.netloc])
        except Exception:
            return False

    def determinar_organismo(self, url: str) -> str:
        """Determina el organismo correspondiente a partir del dominio de una URL."""
        dominio = urlparse(url).netloc.lower()
        for dominio_org, org in self.ORGANISMOS.items():
            if dominio_org in dominio:
                return org
        return 'OTRO'