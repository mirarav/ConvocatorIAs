"""
Módulo para rellenar los campos de documentos.
"""

from urllib.parse import urlparse

from .base import BaseFieldProcessor

class TituloDocumentoProcessor(BaseFieldProcessor):
    """Procesador para completar el título del documento."""
    
    @property
    def field_name(self) -> str:
        return "titulo"
    
    def process(self) -> bool:
        if not self.context.documento_id:
            return False
            
        chunks = self.db.obtener_chunks_por_documento(self.context.documento_id, limite=5)
        contexto = "\n".join([c['chunk_texto'] for c in chunks])
        
        system_prompt = (
            "Eres un experto en convocatorias públicas españolas. Tu tarea es extraer o generar el título "
            "más adecuado para documentos oficiales siguiendo estas reglas estrictas:\n\n"
            "PRIORIDAD: Extraer el título oficial si aparece claramente en la primera página "
            "del documento. Si no hay un título claro, crear uno descriptivo que capture la esencia.\n\n"
            "FORMATO REQUERIDO:\n"
            "   - Entre 3-10 palabras clave\n"
            "   - En español formal\n"
            "   - Sin años, fechas o referencias temporales\n"
            "   - Sin nombres de comunidades o regiones específicas\n"
            "   - Sin comillas, ni guiones, ni punto final, ni caracteres especiales\n\n"
            "EJEMPLOS CORRECTOS:\n"
            "   - Proyectos de I+D\n"
            "   - Proyectos de I+D de Transferencia Tecnológica Cervera\n"
            "   - Incentivos para el Desarrollo Industrial"
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO el título "
            f"cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )
        
        titulo = self._consultar_llm(system_prompt, user_prompt)
        return self.db.actualizar_campo_documento(self.context.documento_id, self.field_name, titulo)

class TipoDocumentoProcessor(BaseFieldProcessor):
    """Procesador para clasificar el tipo de documento."""
    
    @property
    def field_name(self) -> str:
        return "tipo_documento"

    def process(self) -> bool:
        if not self.context.documento_id:
            return False
            
        doc_info = self.db.documento_existe_por_id(self.context.documento_id)
        if not doc_info:
            return False
            
        chunks = self.db.obtener_chunks_por_documento(self.context.documento_id, limite=3)
        contexto = "\n".join([c['chunk_texto'] for c in chunks])
        
        nombre_archivo = ""
        if doc_info.get('enlace_documento'):
            nombre_archivo = urlparse(doc_info['enlace_documento']).path.split('/')[-1].lower()

        system_prompt = (
            "Eres un experto en convocatorias públicas españolas. Tu tarea es clasificar el tipo "
            "de documento en UNA de estas categorías:\n\n"
            "CATEGORÍAS:\n"
            "1. 'ficha_tecnica': Documento principal con detalles de la convocatoria.\n"
            "   - Contiene: objetivos, beneficiarios, presupuestos, plazos\n"
            "   - Suele llamarse: 'ficha_tecnica.pdf', 'convocatoria_2023.pdf', 'bases_ayudas.pdf'\n"
            "   - Ejemplo de contenido: 'La presente convocatoria tiene por objeto... requisitos...'\n\n"
            "2. 'orden_bases': Documento legal con la normativa y orden de bases.\n"
            "   - Contiene: artículos, disposiciones legales, anexos jurídicos\n"
            "   - Suele llamarse: 'orden_bases.pdf', 'disposicion_legal.pdf'\n"
            "   - Ejemplo de contenido: 'Artículo 1. Objeto... En virtud de la ley...'\n\n"
            "3. 'otro': Solo si no encaja en las categorías anteriores.\n"
            "   - Contiene: formulario, preguntas frecuentes, guía, información adicional\n"
            "   - Suele llamarse: 'faq.pdf', 'exencion_y_minoracion.pdf', 'obligaciones.pdf', 'guia.pdf'\n\n"
            "FORMATO REQUERIDO:\n"
            "   - Considera tanto el contenido como el nombre del archivo\n"
            "   - Responde EXACTAMENTE con una de estas palabras: ficha_tecnica, orden_bases, otro\n"
            "   - Sin explicaciones ni puntuación"
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y el nombre del archivo {nombre_archivo}"
            f"y devuelve SOLO el tipo de documento cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )
        
        tipo = self._consultar_llm(system_prompt, user_prompt, max_tokens=15).lower()
        tipos_validos = ['ficha_tecnica', 'orden_bases']
        tipo = tipo if tipo in tipos_validos else 'otro'
        
        return self.db.actualizar_campo_documento(self.context.documento_id, self.field_name, tipo)