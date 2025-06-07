"""
Módulo para descargar con seguridad los documentos PDF.
"""

import io
import requests
from typing import Optional

from nucleo.configuracion.configuracion import Config
from servicios.utilidades.adaptador_ssl import CustomSSLAdapter

class PdfDownloader:
    """Descarga documentos PDF a partir de URLs."""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = self._configurar_sesion()

    def _configurar_sesion(self):
        """Configura una sesión HTTP segura para descargas."""
        session = requests.Session()
        session.mount('https://', CustomSSLAdapter(max_retries=3))
        session.mount('http://', CustomSSLAdapter(max_retries=3))
        session.headers.update({'User-Agent': self.config.SCRAPING_CONFIG['user_agent']})
        session.verify = False # Desactiva verificación SSL
        session.trust_env = False
        return session
    
    def download(self, url: str) -> Optional[io.BytesIO]:
        """Descarga un documento PDF desde la URL proporcionada y lo guarda en memoria."""
        try:
            response = self.session.get(
                url,
                timeout=self.config.SCRAPING_CONFIG['timeout'],
                stream=True
            )
            response.raise_for_status()
            
            # Verificar que el contenido sea realmente un PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'application/pdf' not in content_type:
                print(f"El contenido no es un PDF válido (Content-Type: {content_type})")
                return None
            
            # Descargar todo el contenido en memoria
            pdf_content = io.BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                pdf_content.write(chunk)
            
            # Verificar que el PDF no esté vacío
            if pdf_content.getbuffer().nbytes == 0:
                print("El PDF descargado está vacío")
                return None

            # Verificar estructura básica del PDF
            pdf_content.seek(0)
            magic_number = pdf_content.read(4)
            if magic_number != b'%PDF':
                print("El archivo no comienza con la firma PDF (%PDF)")
                return None

            pdf_content.seek(0)
            return pdf_content

        except requests.exceptions.RequestException as e:
            print(f"Error de red al descargar PDF: {str(e)}")
            return None
        except Exception as e:
            print(f"Error inesperado al descargar PDF: {str(e)}")
            return None