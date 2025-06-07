"""
Módulo para generar reportes de métricas de rendimiento.
"""

from datetime import datetime, timedelta
from typing import Dict, List

from nucleo.base_datos.modelos import Database

class ReportGenerator:
    """Genera reportes basados en las métricas almacenadas."""
    
    def __init__(self):
        self.db = Database()
        
    def generar_reporte_rendimiento(self, dias: int = 7) -> Dict:
        """Genera un reporte consolidado de rendimiento."""
        fecha_inicio = datetime.now() - timedelta(days=dias)
        # Obtener métricas de los últimos N días
        extraccion = self._obtener_metricas('metricas_extraccion', fecha_inicio)
        procesamiento = self._obtener_metricas('metricas_procesamiento', fecha_inicio)
        llm = self._obtener_metricas('metricas_llm', fecha_inicio)
        busqueda = self._obtener_metricas('metricas_busqueda', fecha_inicio)
        # Procesar cada conjunto de métricas
        resultado = {
            'periodo': f"Últimos {dias} días",
            'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
            'fecha_fin': datetime.now().strftime('%Y-%m-%d'),
            'resumen': self._generar_resumen(extraccion, procesamiento, llm, busqueda)
        }
        # Solo incluir áreas con datos
        if extraccion:
            resultado['extraccion'] = self._procesar_metricas(extraccion)
        if procesamiento:
            resultado['procesamiento'] = self._procesar_metricas(procesamiento)
        if llm:
            resultado['llm'] = self._procesar_metricas(llm)
        if busqueda:
            resultado['busqueda'] = self._procesar_metricas(busqueda)
        return resultado
        
    def _obtener_metricas(self, tabla: str, fecha_inicio: datetime) -> List[Dict]:
        """Obtiene métricas de una tabla específica desde una fecha."""
        result = self.db._execute_query(
            f"SELECT * FROM {tabla} WHERE fecha >= %s ORDER BY fecha",
            (fecha_inicio,),
            fetch=True,
            many=True
        )
        return result.data if result.success else []
        
    def _procesar_metricas(self, metricas: List[Dict]) -> Dict:
        """Procesa una lista de métricas para calcular promedios."""
        if not metricas:
            return {}
        # Calcular promedios para todas las columnas numéricas
        promedios = {}
        for key in metricas[0].keys():
            if key in ['id', 'fecha']:
                continue
            valores = [m[key] for m in metricas if m[key] is not None]
            if valores:
                promedios[key] = sum(valores) / len(valores)   
        return {
            'total_registros': len(metricas),
            'promedios': promedios,
            'ultimo_registro': metricas[-1] if metricas else {}
        }
        
    def _generar_resumen(self, extraccion: List[Dict], procesamiento: List[Dict], 
                         llm: List[Dict], busqueda: List[Dict]) -> Dict:
        """Genera un resumen ejecutivo del rendimiento."""
        resumen = {
            'convocatorias_procesadas': sum(e.get('urls_procesadas', 0) for e in extraccion),
            'documentos_procesados': sum(p.get('total_documentos', 0) for p in procesamiento),
            'chunks_generados': sum(p.get('total_chunks', 0) for p in procesamiento),
            'llamadas_llm': sum(l.get('llamadas_totales', 0) for l in llm),
            'busquedas_realizadas': sum(b.get('busquedas_vectoriales', 0) + b.get('busquedas_hibridas', 0) for b in busqueda),
            'tasa_exito_promedio': self._calcular_promedio(extraccion, 'tasa_exito'),
            'tiempo_respuesta_llm_promedio': self._calcular_promedio_llm(llm)
        }
        return resumen
        
    def _calcular_promedio(self, metricas: List[Dict], campo: str) -> float:
        """Calcula el promedio de un campo específico."""
        valores = [m[campo] for m in metricas if campo in m and m[campo] is not None]
        return (sum(valores) / len(valores)) if valores else 0.0
        
    def _calcular_promedio_llm(self, metricas: List[Dict]) -> float:
        """Calcula el promedio de tiempo de respuesta del LLM."""
        tiempos = []
        totales = []
        for tipo in ['texto_corto', 'texto_medio', 'texto_largo', 'tablas']:
            campo = f'tiempo_respuesta_{tipo}'
            valores = [m[campo] for m in metricas if campo in m and m[campo] is not None]
            tiempos.extend(valores)
            totales.append(len(valores))
        return (sum(tiempos) / sum(totales)) if sum(totales) > 0 else 0.0