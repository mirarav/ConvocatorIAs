"""
Módulo para establecer conexiones HTTP/HTTPS con adaptadores SSL.
"""

import ssl
import urllib3
from typing import Optional
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# Desactivar advertencias de SSL no verificado
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CustomSSLAdapter(HTTPAdapter):
    """Maneja las conexiones SSL con configuración flexible."""
    
    def __init__(self, ssl_context: Optional[ssl.SSLContext] = None, max_retries: int = 3, **kwargs):
        self.ssl_context = ssl_context or self._create_ssl_context()
        super().__init__(max_retries=max_retries, **kwargs)

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Crea y configura un contexto SSL seguro pero flexible."""

        # Crear contexto con configuración moderna
        context = create_urllib3_context()
        
        # Optimizar configuración SSL
        context.options |= ssl.OP_NO_SSLv2  # Deshabilitar SSLv2 (inseguro)
        context.options |= ssl.OP_NO_SSLv3  # Deshabilitar SSLv3 (inseguro)
        context.options |= ssl.OP_NO_TLSv1  # Deshabilitar TLSv1 (obsoleto)
        
        # Configurar verificación de certificados
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Usar cifrados seguros por defecto
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        
        return context

    def init_poolmanager(self, *args, **kwargs):
        """Inicializa el pool de conexiones con el contexto SSL configurado."""
        kwargs['ssl_context'] = self.ssl_context
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        """Configura el manejador de proxies con el contexto SSL."""
        kwargs['ssl_context'] = self.ssl_context
        return super().proxy_manager_for(*args, **kwargs)