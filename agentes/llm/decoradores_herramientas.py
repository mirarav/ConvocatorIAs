"""
Módulo para implementar el decorador @tool.
"""

from smolagents import tool
from typing import List

from nucleo.base_datos.modelos import Database

from .procesadores.base import ProcessorContext
from .procesadores import convocatoria, documento

# Configuración compartida
db = Database()

@tool
def completar_titulo_documento(documento_id: int) -> bool:
    """
    Completa el título de un documento analizando su contenido.

    Args:
        documento_id: ID del documento a procesar.
    Returns:
        bool: True si se actualiza el título, False en caso contrario.
    """
    context = ProcessorContext(documento_id=documento_id)
    return documento.TituloDocumentoProcessor(context).process()

@tool
def clasificar_tipo_documento(documento_id: int) -> bool:
    """
    Clasifica el tipo de un documento analizando su contenido.
    
    Args:
        documento_id: ID del documento a procesar.
    Returns:
        bool: True si se actualiza el tipo, False en caso contrario
    """
    context = ProcessorContext(documento_id=documento_id)
    return documento.TipoDocumentoProcessor(context).process()

@tool 
def completar_nombre_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa el nombre de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza el nombre, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.NombreConvocatoriaProcessor(context).process()

@tool
def completar_linea_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa la línea de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza la línea, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.LineaConvocatoriaProcessor(context).process()

@tool
def completar_fecha_inicio_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa la fecha de inicio de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza la fecha, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.FechaInicioProcessor(context).process()

@tool
def completar_fecha_fin_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa la fecha de fin de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza la fecha, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.FechaFinProcessor(context).process()

@tool
def completar_objetivo_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa el objetivo de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza el objetivo, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.ObjetivoProcessor(context).process()

@tool
def completar_beneficiarios_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa los beneficiarios de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza los beneficiarios, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.BeneficiariosProcessor(context).process()
@tool
def completar_anio_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa el año de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.

    Returns:
        bool: True si se actualiza el año, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.AnioProcessor(context).process()

@tool
def completar_area_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa el área de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza el área, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.AreaProcessor(context).process()

@tool
def completar_presupuesto_minimo_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa el presupuesto mínimo de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza el presupuesto, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.PresupuestoMinimoProcessor(context).process()

@tool
def completar_presupuesto_maximo_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa el presupuesto máximo de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza el presupuesto, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.PresupuestoMaximoProcessor(context).process()

@tool
def completar_duracion_minima_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa la duración mínima de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza la duración, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.DuracionMinimaProcessor(context).process()

@tool
def completar_duracion_maxima_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa la duración máxima de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza la duración, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.DuracionMaximaProcessor(context).process()

@tool
def completar_intensidad_subvencion_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa la intensidad de subvención de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza la intensidad, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.IntensidadSubvencionProcessor(context).process()

@tool
def completar_intensidad_prestamo_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa la intensidad de préstamo de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.

    Returns:
        bool: True si se actualiza la intensidad, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.IntensidadPrestamoProcessor(context).process()

@tool
def completar_tipo_financiacion_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa el tipo de financiación de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza el tipo, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.TipoFinanciacionProcessor(context).process()

@tool
def completar_forma_plazo_cobro_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa la forma de plazo de cobro de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza la forma, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.FormaPlazoCobroProcessor(context).process()

@tool
def completar_minimis_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa la información de minimis de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza el minimis, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.MinimisProcessor(context).process()

@tool
def completar_region_aplicacion_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa la región de aplicación de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza la región, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.RegionAplicacionProcessor(context).process()

@tool
def completar_tipo_consorcio_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa el tipo de consorcio de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza el tipo, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.TipoConsorcioProcessor(context).process()

@tool
def completar_costes_elegibles_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa la información de costes elegibles de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza los costes, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.CostesElegiblesProcessor(context).process()

@tool
def completar_enlace_ficha_tecnica_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa el enlace a la ficha técnica de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar.
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza el enlace, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.EnlaceFichaTecnicaProcessor(context).process()

@tool
def completar_enlace_orden_bases_convocatoria(convocatoria_id: int, documento_ids: List[int]) -> bool:
    """
    Completa el enlace a la orden de bases de una convocatoria analizando documentos asociados.
    
    Args:
        convocatoria_id: ID de la convocatoria a procesar
        documento_ids: Lista de IDs de documentos asociados.
    Returns:
        bool: True si se actualiza el enlace, False en caso contrario.
    """
    documentos = db.obtener_documentos_por_ids(documento_ids)
    context = ProcessorContext(convocatoria_id=convocatoria_id, documentos=documentos)
    return convocatoria.EnlaceOrdenBasesProcessor(context).process()

def get_all_tools() -> List[callable]:
    """Devuelve todas las herramientas registradas."""
    return [
        completar_titulo_documento, clasificar_tipo_documento, completar_nombre_convocatoria,
        completar_linea_convocatoria, completar_fecha_inicio_convocatoria, completar_fecha_fin_convocatoria,
        completar_objetivo_convocatoria, completar_beneficiarios_convocatoria, completar_anio_convocatoria,
        completar_area_convocatoria, completar_presupuesto_minimo_convocatoria, completar_presupuesto_maximo_convocatoria,
        completar_duracion_minima_convocatoria, completar_duracion_maxima_convocatoria,
        completar_intensidad_subvencion_convocatoria, completar_intensidad_prestamo_convocatoria,
        completar_tipo_financiacion_convocatoria, completar_forma_plazo_cobro_convocatoria, completar_minimis_convocatoria,
        completar_region_aplicacion_convocatoria, completar_tipo_consorcio_convocatoria,
        completar_costes_elegibles_convocatoria, completar_enlace_ficha_tecnica_convocatoria,
        completar_enlace_orden_bases_convocatoria
    ]