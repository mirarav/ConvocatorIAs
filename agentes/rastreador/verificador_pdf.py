"""
Módulo para verificar y obtener metadatos de documentos PDF desde una URL.
"""

import io
import hashlib
import requests
import pdfplumber
from typing import Dict, Optional

class PdfVerifier:
    """Verifica que URL corresponde a un PDF y obtiene sus metadatos."""

    def verificar_es_pdf(self, url: str, session: requests.Session, timeout: int) -> bool:
        """Verifica si la URL apunta a un archivo PDF basado en el tipo MIME"""
        try:
            # Verificar inicial con HEAD para minimizar transferencia
            head_response = session.head(url, timeout=timeout, allow_redirects=True)
            content_type = head_response.headers.get('content-type', '').lower()
            return 'application/pdf' in content_type and 'html' not in content_type
        except Exception:
            return False

    def obtener_metadatos_pdf(self, pdf_url: str, session: requests.Session, timeout: int) -> Optional[Dict]:
        """Descarga parcialmente un PDF para calcular su hash y obtener metadatos."""
        try:
            # Realizar HEAD request para obtener metadatos
            head_response = session.head(pdf_url, timeout=timeout, allow_redirects=True)
            head_response.raise_for_status()
            
            content_length = int(head_response.headers.get('content-length', 0))
            last_modified = head_response.headers.get('last-modified')
            
            # Descargar solo lo necesario para contar páginas
            get_response = session.get(
                pdf_url,
                stream=True,
                headers={'Range': 'bytes=0-999999'},
                timeout=timeout
            )
            get_response.raise_for_status()
            
            # Calcular hash SHA256
            sha256 = hashlib.sha256()
            pdf_content = io.BytesIO()

            for chunk in get_response.iter_content(chunk_size=8192):
                pdf_content.write(chunk)
                sha256.update(chunk)
                if pdf_content.tell() > 1000000: break
            
            # Contar páginas
            num_paginas = 0
            pdf_content.seek(0)
            try:
                with pdfplumber.open(pdf_content) as pdf:
                    num_paginas = len(pdf.pages)
            except Exception: pass

            return {
                'tipo_mime': 'application/pdf',
                'tamano_bytes': content_length,
                'numero_paginas': num_paginas,
                'hash_sha256': sha256.hexdigest(),
                'enlace_documento': pdf_url,
                'ultima_modificacion': last_modified
            }
        except Exception as e:
            print(f"Error metadatos PDF {pdf_url}: {str(e)}")
            return None