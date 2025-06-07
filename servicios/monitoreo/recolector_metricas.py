"""
Módulo para seguir y calcular las métricas del sistema.
"""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict

from nucleo.base_datos.modelos import Database

@dataclass
class MetricasExtraccion:
    total_urls_procesadas: int = 0
    urls_exitosas: int = 0
    urls_fallidas: int = 0
    tiempo_total: float = 0.0
    documentos_detectados: int = 0
    paginas_analizadas: int = 0

@dataclass
class MetricasProcesamiento:
    total_documentos: int = 0
    texto_principal: int = 0
    tablas: int = 0
    metadatos: int = 0
    total_chunks: int = 0
    caracteres_totales: int = 0
    tiempo_total: float = 0.0

@dataclass
class MetricasLLM:
    llamadas_totales: int = 0
    texto_corto: Dict[str, float] = None  # {'count': 0, 'total_time': 0.0}
    texto_medio: Dict[str, float] = None
    texto_largo: Dict[str, float] = None
    tablas: Dict[str, float] = None

@dataclass
class MetricasBusqueda:
    busquedas_vectoriales: int = 0
    tiempo_vectorial: float = 0.0
    busquedas_hibridas: int = 0
    tiempo_hibrido: float = 0.0

class MetricasManager:
    """Gestiona el registro y cálculo de todas las métricas del sistema."""
    
    def __init__(self):
        self.db = Database()
        self.extraccion = MetricasExtraccion()
        self.procesamiento = MetricasProcesamiento()
        self.llm = MetricasLLM(
            texto_corto={'count': 0, 'total_time': 0.0},
            texto_medio={'count': 0, 'total_time': 0.0},
            texto_largo={'count': 0, 'total_time': 0.0},
            tablas={'count': 0, 'total_time': 0.0}
        )
        self.busqueda = MetricasBusqueda()
        
    def registrar_inicio_extraccion(self):
        """Registra el inicio de un proceso de extracción."""
        self.current_extraction_start = time.time()
        
    def registrar_fin_extraccion(self, exitoso: bool, num_documentos: int, num_paginas: int):
        """Registra el fin de un proceso de extracción."""
        tiempo = time.time() - self.current_extraction_start
        
        self.extraccion.total_urls_procesadas += 1
        self.extraccion.tiempo_total += tiempo
        self.extraccion.documentos_detectados += num_documentos
        self.extraccion.paginas_analizadas += num_paginas
        
        if exitoso:
            self.extraccion.urls_exitosas += 1
        else:
            self.extraccion.urls_fallidas += 1
            
        # Guardar en base de datos
        self._guardar_metricas_extraccion()
        
    def registrar_procesamiento_documento(self, tiene_texto: bool, tiene_tablas: bool, 
                                         tiene_metadatos: bool, num_chunks: int, 
                                         caracteres_totales: int, tiempo_procesamiento: float):
        """Registra el procesamiento de un documento."""
        self.procesamiento.total_documentos += 1
        self.procesamiento.tiempo_total += tiempo_procesamiento
        self.procesamiento.total_chunks += num_chunks
        self.procesamiento.caracteres_totales += caracteres_totales
        
        if tiene_texto:
            self.procesamiento.texto_principal += 1
        if tiene_tablas:
            self.procesamiento.tablas += 1
        if tiene_metadatos:
            self.procesamiento.metadatos += 1
            
        # Guardar en base de datos
        self._guardar_metricas_procesamiento()
        
    def registrar_llamada_llm(self, tipo: str, tiempo_ejecucion: float):
        """Registra una llamada al LLM."""
        self.llm.llamadas_totales += 1
        
        if tipo == 'corto':
            self.llm.texto_corto['count'] += 1
            self.llm.texto_corto['total_time'] += tiempo_ejecucion
        elif tipo == 'medio':
            self.llm.texto_medio['count'] += 1
            self.llm.texto_medio['total_time'] += tiempo_ejecucion
        elif tipo == 'largo':
            self.llm.texto_largo['count'] += 1
            self.llm.texto_largo['total_time'] += tiempo_ejecucion
        elif tipo == 'tabla':
            self.llm.tablas['count'] += 1
            self.llm.tablas['total_time'] += tiempo_ejecucion
            
        # Guardar en base de datos
        self._guardar_metricas_llm()
        
    def registrar_busqueda(self, tipo: str, tiempo_ejecucion: float):
        """Registra una búsqueda semántica."""
        if tipo == 'vectorial':
            self.busqueda.busquedas_vectoriales += 1
            self.busqueda.tiempo_vectorial += tiempo_ejecucion
        elif tipo == 'hibrida':
            self.busqueda.busquedas_hibridas += 1
            self.busqueda.tiempo_hibrido += tiempo_ejecucion
            
        # Guardar en base de datos
        self._guardar_metricas_busqueda()
        
    def obtener_metricas_extraccion(self) -> Dict:
        """Calcula y devuelve las métricas de extracción."""
        return {
            'cobertura_organismos': self._calcular_cobertura_organismos(),
            'tasa_exito': self._calcular_tasa_exito(),
            'tiempo_promedio': self._calcular_tiempo_promedio(),
            'tasa_deteccion_pdf': self._calcular_tasa_deteccion_pdf(),
            'urls_procesadas': self.extraccion.total_urls_procesadas,
            'urls_exitosas': self.extraccion.urls_exitosas,
            'urls_fallidas': self.extraccion.urls_fallidas,
            'documentos_detectados': self.extraccion.documentos_detectados,
            'paginas_analizadas': self.extraccion.paginas_analizadas
        }
        
    def obtener_metricas_procesamiento(self) -> Dict:
        """Calcula y devuelve las métricas de procesamiento."""
        return {
            'tasa_texto_principal': self._calcular_tasa_texto_principal(),
            'tasa_tablas': self._calcular_tasa_tablas(),
            'tasa_metadatos': self._calcular_tasa_metadatos(),
            'tamano_promedio_chunks': self._calcular_tamano_promedio_chunks(),
            'solapamiento_optimo': 'N/A',  # Se calcularía basado en configuración
            'tiempo_promedio_procesamiento': self._calcular_tiempo_promedio_procesamiento(),
            'total_documentos': self.procesamiento.total_documentos,
            'total_chunks': self.procesamiento.total_chunks
        }
        
    def obtener_metricas_llm(self) -> Dict:
        """Calcula y devuelve las métricas del LLM."""
        return {
            'tiempo_respuesta_texto_corto': self._calcular_tiempo_promedio_llm('texto_corto'),
            'tiempo_respuesta_texto_medio': self._calcular_tiempo_promedio_llm('texto_medio'),
            'tiempo_respuesta_texto_largo': self._calcular_tiempo_promedio_llm('texto_largo'),
            'tiempo_respuesta_tablas': self._calcular_tiempo_promedio_llm('tablas'),
            'llamadas_totales': self.llm.llamadas_totales
        }
        
    def obtener_metricas_busqueda(self) -> Dict:
        """Calcula y devuelve las métricas de búsqueda."""
        return {
            'tiempo_respuesta_vectorial': self._calcular_tiempo_promedio_busqueda('vectorial'),
            'tiempo_respuesta_hibrida': self._calcular_tiempo_promedio_busqueda('hibrida'),
            'busquedas_vectoriales': self.busqueda.busquedas_vectoriales,
            'busquedas_hibridas': self.busqueda.busquedas_hibridas
        }
        
    def _calcular_cobertura_organismos(self) -> float:
        """Calcula el % de organismos objetivo procesados."""
        organismos = ['ADER', 'CDTI', 'Comunidad de Madrid', 'TRADE']
        conteo = self.db._execute_query(
            "SELECT COUNT(DISTINCT organismo) FROM convocatorias WHERE organismo IN %s",
            (tuple(organismos),),
            fetch=True
        )
        if conteo.success and conteo.data:
            return (conteo.data['count'] / len(organismos)) * 100
        return 0.0
        
    def _calcular_tasa_exito(self) -> float:
        """Calcula el % de URLs procesadas correctamente."""
        if self.extraccion.total_urls_procesadas == 0:
            return 0.0
        return (self.extraccion.urls_exitosas / self.extraccion.total_urls_procesadas) * 100
        
    def _calcular_tiempo_promedio(self) -> float:
        """Calcula el tiempo promedio por convocatoria en segundos."""
        if self.extraccion.total_urls_procesadas == 0:
            return 0.0
        return self.extraccion.tiempo_total / self.extraccion.total_urls_procesadas
        
    def _calcular_tasa_deteccion_pdf(self) -> float:
        """Calcula el % de páginas analizadas que contienen PDFs."""
        if self.extraccion.paginas_analizadas == 0:
            return 0.0
        return (self.extraccion.documentos_detectados / self.extraccion.paginas_analizadas) * 100
        
    def _calcular_tasa_texto_principal(self) -> float:
        """Calcula el % de documentos con texto principal."""
        if self.procesamiento.total_documentos == 0:
            return 0.0
        return (self.procesamiento.texto_principal / self.procesamiento.total_documentos) * 100
        
    def _calcular_tasa_tablas(self) -> float:
        """Calcula el % de documentos con tablas."""
        if self.procesamiento.total_documentos == 0:
            return 0.0
        return (self.procesamiento.tablas / self.procesamiento.total_documentos) * 100
        
    def _calcular_tasa_metadatos(self) -> float:
        """Calcula el % de documentos con metadatos."""
        if self.procesamiento.total_documentos == 0:
            return 0.0
        return (self.procesamiento.metadatos / self.procesamiento.total_documentos) * 100
        
    def _calcular_tamano_promedio_chunks(self) -> float:
        """Calcula el tamaño promedio de los chunks en caracteres."""
        if self.procesamiento.total_chunks == 0:
            return 0.0
        return self.procesamiento.caracteres_totales / self.procesamiento.total_chunks
        
    def _calcular_tiempo_promedio_procesamiento(self) -> float:
        """Calcula el tiempo promedio de procesamiento por documento."""
        if self.procesamiento.total_documentos == 0:
            return 0.0
        return self.procesamiento.tiempo_total / self.procesamiento.total_documentos
        
    def _calcular_tiempo_promedio_llm(self, tipo: str) -> float:
        """Calcula el tiempo promedio de respuesta del LLM para un tipo."""
        datos = getattr(self.llm, tipo)
        if datos['count'] == 0:
            return 0.0
        return datos['total_time'] / datos['count']
        
    def _calcular_tiempo_promedio_busqueda(self, tipo: str) -> float:
        """Calcula el tiempo promedio de búsqueda."""
        if tipo == 'vectorial':
            if self.busqueda.busquedas_vectoriales == 0:
                return 0.0
            return self.busqueda.tiempo_vectorial / self.busqueda.busquedas_vectoriales
        else:
            if self.busqueda.busquedas_hibridas == 0:
                return 0.0
            return self.busqueda.tiempo_hibrido / self.busqueda.busquedas_hibridas
            
    def _guardar_metricas_extraccion(self):
        """Guarda las métricas de extracción en la base de datos."""
        metricas = self.obtener_metricas_extraccion()
        self.db._execute_query(
            """INSERT INTO metricas_extraccion 
               (fecha, cobertura_organismos, tasa_exito, tiempo_promedio, 
                tasa_deteccion_pdf, urls_procesadas, urls_exitosas, urls_fallidas,
                documentos_detectados, paginas_analizadas)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (datetime.now(), metricas['cobertura_organismos'], metricas['tasa_exito'], 
             metricas['tiempo_promedio'], metricas['tasa_deteccion_pdf'], 
             metricas['urls_procesadas'], metricas['urls_exitosas'], metricas['urls_fallidas'],
             metricas['documentos_detectados'], metricas['paginas_analizadas'])
        )
        
    def _guardar_metricas_procesamiento(self):
        """Guarda las métricas de procesamiento en la base de datos."""
        metricas = self.obtener_metricas_procesamiento()
        self.db._execute_query(
            """INSERT INTO metricas_procesamiento 
               (fecha, tasa_texto_principal, tasa_tablas, tasa_metadatos, 
                tamano_promedio_chunks, tiempo_promedio_procesamiento, 
                total_documentos, total_chunks)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (datetime.now(), metricas['tasa_texto_principal'], metricas['tasa_tablas'], 
             metricas['tasa_metadatos'], metricas['tamano_promedio_chunks'], 
             metricas['tiempo_promedio_procesamiento'], metricas['total_documentos'], 
             metricas['total_chunks'])
        )
        
    def _guardar_metricas_llm(self):
        """Guarda las métricas del LLM en la base de datos."""
        metricas = self.obtener_metricas_llm()
        self.db._execute_query(
            """INSERT INTO metricas_llm 
               (fecha, tiempo_respuesta_texto_corto, tiempo_respuesta_texto_medio,
                tiempo_respuesta_texto_largo, tiempo_respuesta_tablas, llamadas_totales)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (datetime.now(), metricas['tiempo_respuesta_texto_corto'], 
             metricas['tiempo_respuesta_texto_medio'], metricas['tiempo_respuesta_texto_largo'],
             metricas['tiempo_respuesta_tablas'], metricas['llamadas_totales'])
        )
        
    def _guardar_metricas_busqueda(self):
        """Guarda las métricas de búsqueda en la base de datos."""
        metricas = self.obtener_metricas_busqueda()
        self.db._execute_query(
            """INSERT INTO metricas_busqueda 
               (fecha, tiempo_respuesta_vectorial, tiempo_respuesta_hibrida,
                busquedas_vectoriales, busquedas_hibridas)
               VALUES (%s, %s, %s, %s, %s)""",
            (datetime.now(), metricas['tiempo_respuesta_vectorial'], 
             metricas['tiempo_respuesta_hibrida'], metricas['busquedas_vectoriales'],
             metricas['busquedas_hibridas'])
        )