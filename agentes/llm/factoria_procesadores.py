"""
Módulo para instanciar los procesadores de campos de convocatorias y documentos.
"""

from typing import Dict, List, Type

from .procesadores import convocatoria, documento

class LLMProcessorFactory:
    """Establece la factoría de procesadores de campos de convocatorias."""

    # Crear un diccionario de clases de procesadores
    _processor_classes: Dict[str, Type] = {
        # Establecer procesadores de campos de documentos
        'titulo': documento.TituloDocumentoProcessor,
        'tipo_documento': documento.TipoDocumentoProcessor,
        # Extablecer procesadores de campos de convocatorias
        'nombre': convocatoria.NombreConvocatoriaProcessor,
        'linea': convocatoria.LineaConvocatoriaProcessor,
        'fecha_inicio': convocatoria.FechaInicioProcessor,
        'fecha_fin': convocatoria.FechaFinProcessor,
        'objetivo': convocatoria.ObjetivoProcessor,
        'beneficiarios': convocatoria.BeneficiariosProcessor,
        'anio': convocatoria.AnioProcessor,
        'area': convocatoria.AreaProcessor,
        'presupuesto_minimo': convocatoria.PresupuestoMinimoProcessor,
        'presupuesto_maximo': convocatoria.PresupuestoMaximoProcessor,
        'duracion_minima': convocatoria.DuracionMinimaProcessor,
        'duracion_maxima': convocatoria.DuracionMaximaProcessor,
        'intensidad_subvencion': convocatoria.IntensidadSubvencionProcessor,
        'intensidad_prestamo': convocatoria.IntensidadPrestamoProcessor,
        'tipo_financiacion': convocatoria.TipoFinanciacionProcessor, 
        'forma_plazo_cobro': convocatoria.FormaPlazoCobroProcessor,
        'minimis': convocatoria.MinimisProcessor,
        'region_aplicacion': convocatoria.RegionAplicacionProcessor,
        'tipo_consorcio': convocatoria.TipoConsorcioProcessor,
        'costes_elegibles': convocatoria.CostesElegiblesProcessor,
        'enlace_ficha_tecnica': convocatoria.EnlaceFichaTecnicaProcessor,
        'enlace_orden_bases': convocatoria.EnlaceOrdenBasesProcessor
    }
    
    @classmethod
    def create_processor(cls, field_name: str, *args, **kwargs):
        """Crea una instancia del procesador adecuado según el campo."""
        processor_class = cls._processor_classes.get(field_name)
        if not processor_class:
            raise ValueError(f"No se encontró procesador para el campo: {field_name}")
        return processor_class(*args, **kwargs)

    @classmethod
    def get_available_fields(cls) -> List[str]:
        """Devuelve la lista de campos que pueden ser procesados."""
        return list(cls._processor_classes.keys())