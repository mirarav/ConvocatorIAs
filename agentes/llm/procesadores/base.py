"""
Módulo para definir las clases base y abstracciones para el procesamiento de campos.
"""

import time
from openai import AzureOpenAI
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer

from nucleo.configuracion.configuracion import Config
from nucleo.base_datos.modelos import Database
from servicios.monitoreo.recolector_metricas import MetricasManager

@dataclass
class ProcessorContext:
    documento_id: Optional[int] = None
    convocatoria_id: Optional[int] = None
    documentos: Optional[List[Dict]] = None

class BaseFieldProcessor(ABC):
    """Establece la interfaz abstracta para procesadores de campos."""
    
    def __init__(self, context: ProcessorContext):
        self.context = context
        self.db = Database()
        self.metricas = MetricasManager()
        self.embedder = self._get_embedder()
    
    def _get_embedder(self):
        """Inicializa y cachea el modelo de embeddings."""
        return SentenceTransformer('all-MiniLM-L6-v2')
    
    @abstractmethod
    def process(self) -> bool:
        """Procesa el campo y actualiza la base de datos."""
        pass
    
    @property
    @abstractmethod
    def field_name(self) -> str:
        """Nombre del campo que procesa esta clase."""
        pass
    
    def _buscar_chunks_relevantes(self, terminos: List[str], documento_id: Optional[int] = None, limite: int = 3) -> List[Dict]:
        """Busca chunks similares a los términos dados usando embeddings."""
        chunks_encontrados = []
        doc_id = documento_id or self.context.documento_id
        
        if doc_id:
            for termino in terminos:
                try:
                    embedding = self.embedder.encode(termino)
                    chunks = self.db.buscar_chunks_por_similitud(
                        documento_id=doc_id, 
                        vector_consulta=embedding.tolist(), 
                        limite=limite
                    )
                    chunks_encontrados.extend(chunks)
                except Exception:
                    continue
        return chunks_encontrados
    
    def _consultar_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = 100) -> str:
        """Consulta al LLM con los prompts dados."""
        
        config = Config()
        client = AzureOpenAI(
            api_key=config.LLM_CONFIG['api_key'],
            api_version=config.LLM_CONFIG['api_version'],
            azure_endpoint=config.LLM_CONFIG['endpoint'],
            max_retries=3
        )
        
        start_time = time.time()
        try:
            response = client.chat.completions.create(
                model=config.LLM_CONFIG['deployment_name'],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=max_tokens
            )
            tiempo = time.time() - start_time
            self.metricas.registrar_llamada_llm('general', tiempo)
            return response.choices[0].message.content.strip()
        except Exception as e:
            tiempo = time.time() - start_time
            self.metricas.registrar_llamada_llm('error', tiempo)
            raise e