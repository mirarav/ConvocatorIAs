"""
Agente que coordina el flujo completo de descarga, extracción, fragmentación,
vectorización y almacenamiento de documentos PDF.
"""

import time

from nucleo.configuracion.configuracion import Config
from nucleo.base_datos.modelos import Database
from servicios.monitoreo.recolector_metricas import MetricasManager

from .descargador_pdf import PdfDownloader
from .extractor_texto_pdf import PdfContentExtractor
from .fragmentador_texto import TextSplitter
from .generador_embedding import EmbeddingGenerator
from .titulador_seccion import SectionTitleGenerator

class ChunkingAgent:
    """Agente principal de procesamiento de documentos PDF."""

    def __init__(self):
        self.config = Config()
        self.db = Database()
        self.metricas = MetricasManager()
        self.downloader = PdfDownloader(self.config)
        self.extractor = PdfContentExtractor()
        self.splitter = TextSplitter()
        self.embedder = EmbeddingGenerator()
        self.title_generator = SectionTitleGenerator()

    def procesar_documento(self, documento_id: int, pdf_url: str) -> bool:
        """Procesa un documento completo desde la URL hasta su almacenamiento vectorial."""
        start_time = time.time()
        try:
            if self.db.documento_tiene_chunks(documento_id):
                return True
            
            # Descargar PDF
            pdf_stream = self.downloader.download(pdf_url)
            if not pdf_stream:
                print(f"No se pudo descargar el PDF de {pdf_url}")
                return False
            
            # Extraer texto estructurado con tablas
            paginas = self.extractor.extract_text(pdf_stream)
            if not paginas:
                print(f"No se pudo extraer texto del PDF {pdf_url}")
                return False
            
            # Dividir texto en chunks y generar embeddings
            total_chunks = 0
            for pagina in paginas:
                chunks = self.splitter.split(pagina['texto'])
                if not chunks:
                    continue
                
                embeddings = self.embedder.generate(chunks)
                if len(embeddings) != len(chunks):
                    print("No se pudo generar embeddings para todos los chunks")
                    continue
                
                # Almacenar en base de datos
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    titulo_seccion = self.title_generator.generate(chunk, pagina['numero_pagina'], i+1)
                    
                    if not self.db.insertar_chunk_documento(
                        documento_id=documento_id,
                        chunk_texto=chunk,
                        chunk_vector=embedding.tolist(),
                        titulo_seccion=titulo_seccion,
                        numero_pagina=pagina['numero_pagina']
                    ):
                        print(f"Error insertando chunk {i+1} de página {pagina['numero_pagina']}")
                    else:
                        total_chunks += 1

            tiempo_procesamiento = time.time() - start_time
            
            self.metricas.registrar_procesamiento_documento(
                tiene_texto=len(paginas) > 0,
                tiene_tablas=any(p['tiene_tablas'] for p in paginas),
                tiene_metadatos=True,
                num_chunks=total_chunks,
                caracteres_totales=sum(len(c['texto']) for c in paginas),
                tiempo_procesamiento=tiempo_procesamiento
            )
        
            return total_chunks > 0
            
        except Exception as e:
            tiempo_procesamiento = time.time() - start_time
            self.metricas.registrar_procesamiento_documento(
                tiene_texto=False,
                tiene_tablas=False,
                tiene_metadatos=False,
                num_chunks=0,
                caracteres_totales=0,
                tiempo_procesamiento=tiempo_procesamiento
            )
            return False