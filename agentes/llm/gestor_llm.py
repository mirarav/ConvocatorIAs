"""
Agente que coordina el flujo completo de relleno de información de documentos y convocatorias.
"""

import time
from typing import List, Dict, Callable
from openai import AzureOpenAI
from smolagents import CodeAgent

from nucleo.configuracion.configuracion import Config
from nucleo.base_datos.modelos import Database

from .factoria_procesadores import LLMProcessorFactory
from .procesadores.base import ProcessorContext
from .decoradores_herramientas import get_all_tools

class LLMAgent:
    """Agente principal de completitud de información en documentos y convocatorias."""
    
    def __init__(self):
        self.config = Config()
        self.db = Database()
        self.client = AzureOpenAI(
            api_key=self.config.LLM_CONFIG['api_key'],
            api_version=self.config.LLM_CONFIG['api_version'],
            azure_endpoint=self.config.LLM_CONFIG['endpoint'],
            max_retries=3
        )
        self.agent = CodeAgent(
            tools=get_all_tools(),
            model=self.modelo_llm()
        )
     
    def modelo_llm(self) -> Callable:
        """Crea una función de modelo que usa el cliente configurado."""
        def model(messages):
            return self.client.chat.completions.create(
                model=self.config.LLM_CONFIG['deployment_name'],
                messages=messages
            ).choices[0].message.content
        
        return model
    
    def completar_informacion_documentos(self, documento_ids: List[int]) -> Dict:
        """Completa información faltante en documentos."""
        resultados = {'documentos_procesados': 0, 'campos_completados': 0, 'detalle': {}}
        
        for doc_id in documento_ids:
            try:
                time.sleep(1)  # Evita superar el límite de tasa
                context = ProcessorContext(documento_id=doc_id)
                
                for campo in ['titulo', 'tipo_documento']:
                    processor = LLMProcessorFactory.create_processor(campo, context)
                    if processor.process():
                        resultados['campos_completados'] += 1
                        resultados['detalle'].setdefault(campo, 0)
                        resultados['detalle'][campo] += 1
                
                # Actualizar convocatorias relacionadas
                self._actualizar_enlaces_convocatorias(doc_id)
                resultados['documentos_procesados'] += 1
                        
            except Exception as e:
                print(f"Error procesando documento {doc_id}: {str(e)}")
        
        return resultados
    
    def _actualizar_enlaces_convocatorias(self, documento_id: int) -> None:
        """Actualiza enlaces en las convocatorias asociados a un documento."""
        documento = self.db.documento_existe_por_id(documento_id)
        if not documento or not documento.get('tipo_documento'):
            return
            
        convocatorias = self.db.obtener_convocatorias_por_documento(documento_id)
        for conv in convocatorias:
            if documento['tipo_documento'] == 'ficha_tecnica':
                self.db.actualizar_enlace_ficha_tecnica_convocatoria(conv['id'], documento['enlace_documento'])
            elif documento['tipo_documento'] == 'orden_bases':
                self.db.actualizar_enlace_orden_bases_convocatoria(conv['id'], documento['enlace_documento'])
    
    def completar_informacion_convocatorias(self, convocatoria_ids: List[int]) -> Dict:
        """Completa información faltante en convocatorias."""
        resultados = {'convocatorias_procesadas': 0, 'campos_completados': 0, 'detalle': {}}
        
        for conv_id in convocatoria_ids:
            try:
                time.sleep(1)  # Evita superar el límite de tasa
                documentos = self.db.obtener_documentos_por_convocatoria(conv_id)
                if not documentos:
                    continue
                    
                context = ProcessorContext(
                    convocatoria_id=conv_id,
                    documentos=documentos
                )
                
                for field_name in LLMProcessorFactory.get_available_fields():
                    if field_name in ['titulo', 'tipo_documento']:
                        continue
                        
                    try:
                        processor = LLMProcessorFactory.create_processor(field_name, context)
                        if processor.process():
                            resultados['campos_completados'] += 1
                            resultados['detalle'].setdefault(field_name, 0)
                            resultados['detalle'][field_name] += 1
                    except Exception as e:
                        print(f"Error campo {field_name}: {e}")
                
                resultados['convocatorias_procesadas'] += 1
                        
            except Exception as e:
                print(f"Error procesando convocatoria {conv_id}: {e}")
                
        return resultados