"""
Agente que coordina el flujo completo de scraping, validación y procesamiento
de convocatorias y sus documentos PDF asociados.
"""

import requests
from typing import Dict, List

from nucleo.configuracion.configuracion import Config
from nucleo.base_datos.modelos import Database
from servicios.utilidades.adaptador_ssl import CustomSSLAdapter
from agentes.fragmentador.gestor_fragmentacion import ChunkingAgent
from agentes.llm.gestor_llm import LLMAgent
from servicios.monitoreo.recolector_metricas import MetricasManager

from .validador_url import UrlValidator
from .extractor_url_pdf import PdfUrlExtractor
from .verificador_pdf import PdfVerifier

class CrawlerAgent:
    """Agente principial de scraping y procesamiento de convocatorias."""

    def __init__(self):
        self.max_retries = 3
        self.base_wait_time = 2
        self.silent = False

        self.config = Config()
        self.db = Database()
        self.pdf_processor = ChunkingAgent()
        self.llm = LLMAgent()
        self.metricas = MetricasManager()
        self.session = self._configurar_sesion()
        self.url_procesadas = set()
        self.url_validator = UrlValidator()
        self.pdf_extractor = PdfUrlExtractor(self.config)
        self.pdf_verifier = PdfVerifier()

    def set_silent(self, silent: bool):
        """Activa o desactiva el modo silencioso."""        
        self.silent = silent

    def _configurar_sesion(self):
        """Configura una sesión HTTP con headers y adaptador SSL personalizado."""        
        session = requests.Session()
        adapter = CustomSSLAdapter(max_retries=self.max_retries)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        
        session.headers.update({
            'User-Agent': self.config.SCRAPING_CONFIG['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        session.verify = False # Verificación SSL desactivada
        session.trust_env = False
        return session

    def procesar_convocatoria(self, url: str) -> Dict:
        """Procesa una convocatoria desde su URL."""        
        try:
            self.metricas.registrar_inicio_extraccion()

            if not self.url_validator.es_valida(url):
                return {'error': 'url_invalida', 'detalle': 'URL no válida'}

            if (conv_existente := self.db.obtener_convocatoria_por_url(url)):
                return {'error': 'duplicada', 'detalle': 'Convocatoria ya registrada'}

            organismo = self.url_validator.determinar_organismo(url)
            exito, mensaje, id_convocatoria = self.db.insertar_convocatoria({
                'organismo': organismo,
                'enlace_convocatoria': url
            })
            
            if not exito:
                return {'error': 'bd_error', 'detalle': f'Error BD: {mensaje}'}
            
            resultado_documentos = self.procesar_documentos_convocatoria(id_convocatoria, url)

            if not resultado_documentos['exito']:
                return {
                    'error': 'documentos_error',
                    'detalle': resultado_documentos['mensaje'],
                    'convocatoria_id': id_convocatoria
                }
            
            self.completar_informacion_con_llm(id_convocatoria, resultado_documentos['documentos'])

            convocatoria_actualizada = self.db.obtener_convocatorias_por_ids([id_convocatoria])[0]

            self.metricas.registrar_fin_extraccion(
                exitoso=True,
                num_documentos=len(resultado_documentos['documentos']),
                num_paginas=sum(doc.get('numero_paginas', 0) for doc in resultado_documentos['documentos'])
            )
            
            return {
                'estado': 'éxito',
                'convocatoria': convocatoria_actualizada,
                'documentos': resultado_documentos['documentos'],
                'total_documentos': len(resultado_documentos['documentos'])
            }

        except Exception as e:
            return {
                'error': 'error_general',
                'detalle': f'Error inesperado: {str(e)}'
                }

    def procesar_documentos_convocatoria(self, id_convocatoria: int, url_convocatoria: str) -> Dict:
        """Extrae y procesa los PDFs asociados a una convocatoria."""
        resultado = {'exito': False, 'mensaje': '', 'documentos': []}
        
        if not url_convocatoria or url_convocatoria in self.url_procesadas:
            resultado['mensaje'] = "URL inválida o ya procesada"
            return resultado
            
        self.url_procesadas.add(url_convocatoria)

        try:
            pdf_urls = self.pdf_extractor.extraer_pdfs(
                url_convocatoria,
                max_retries=self.max_retries,
                base_wait_time=self.base_wait_time,
                silent=self.silent
            )
            
            pdfs_validos = [
                url for url in pdf_urls 
                if self.pdf_verifier.verificar_es_pdf(url, self.session, self.config.SCRAPING_CONFIG['timeout'])
            ]
            
            if not pdfs_validos:
                resultado['mensaje'] = "No se encontraron PDFs válidos"
                return resultado
            
            documentos_procesados = []

            for pdf_url in pdfs_validos:
                try:
                    metadatos = self.pdf_verifier.obtener_metadatos_pdf(
                        pdf_url, 
                        self.session, 
                        self.config.SCRAPING_CONFIG['timeout']
                    )

                    if not metadatos: 
                        continue

                    exito, _, doc_id = self.db.insertar_documento(metadatos)
                    if not exito: 
                        continue

                    if not self.db.asociar_documento_convocatoria(id_convocatoria, doc_id): 
                        continue
                    
                    num_chunks = self.pdf_processor.procesar_documento(doc_id, pdf_url)
                    
                    if num_chunks <= 0: 
                        continue

                    if (doc_actualizado := self.db.documento_existe_por_id(doc_id)):
                        documentos_procesados.append(doc_actualizado)

                except Exception: 
                    continue
                        
            if documentos_procesados:
                resultado.update({
                    'exito': True,
                    'mensaje': f"Procesados {len(documentos_procesados)} documentos",
                    'documentos': documentos_procesados
                })
            else:
                resultado['mensaje'] = "No se pudieron procesar documentos"
            
            return resultado
            
        except Exception as e:
            resultado['mensaje'] = f"Error procesando documentos: {str(e)}"
            return resultado
        
    def completar_informacion_con_llm(self, convocatoria_id: int, documentos: List[Dict]) -> None:
        """Enriquece los documentos y la convocatoria usando un modelo LLM."""
        try:
            doc_ids = [doc['id'] for doc in documentos]
            self.llm.completar_informacion_documentos(doc_ids)
            self.llm.completar_informacion_convocatorias([convocatoria_id])
        except Exception as e:
            print(f"Error LLM: {str(e)}")