"""
Módulo para rellenar los campos de convocatorias.
"""

from .base import BaseFieldProcessor

class NombreConvocatoriaProcessor(BaseFieldProcessor):
    """Procesador para completar el nombre de la convocatoria."""

    @property
    def field_name(self) -> str:
        return "nombre"
    
    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False
        
        # Seleccionar documento más relevante
        documentos_ordenados = sorted(
            self.context.documentos,
            key=lambda x: (
                0 if x.get('tipo_documento') == 'ficha_tecnica' else 
                1 if x.get('tipo_documento') == 'orden_bases' else 2,
                -x.get('numero_paginas', 0)
            )
        )
        doc_relevante = documentos_ordenados[0]

        # Obtener contenido
        chunks = self.db.obtener_chunks_por_documento(doc_relevante['id'], limite=3)
        contexto = "\n".join(c['chunk_texto'] for c in chunks if c.get('chunk_texto', '').strip())
        
        if not contexto:
            return False
        
        system_prompt = (
            "Eres un experto de convocatorias públicas españolas. Tu tarea es identificar el nombre "
            "más adecuado de la convocatoria siguiendo estas reglas estrictas:\n\n "
            "PRIORIDAD: Extraer el nombre oficial de la convocatoria. Es el título que identifica la ayuda "
            "o subvención.\n\n "
            "FORMATO REQUERIDO:\n "
            "   - Conciso, entre 3-12 palabras\n "
            "   - En español formal\n "
            "   - Sin años, fechas o referencias temporales\n "
            "   - Sin nombres de comunidades o regiones específicas\n "
            "   - Sin comillas, ni guiones, ni punto final, ni caracteres especiales\n\n "
            "EJEMPLOS CORRECTOS:\n "
            "   - Incentivos para el Desarrollo Industrial\n "
            "   - Proyectos de I+D\n "
            "   - Programa Cheque de Innovación Digitalización "
            "   - Proyectos de I+D de Transferencia Tecnológica Cervera\n "
            "   - Incentivos para el Desarrollo Industrial "
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO el nombre oficial"
            f"cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )
        
        try:
            nombre = self._consultar_llm(system_prompt, user_prompt, max_tokens=100).strip()
            nombre = ' '.join(nombre.split()).strip('"\'. ')
            return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, nombre)
        except Exception:
            return False
        
class LineaConvocatoriaProcessor(BaseFieldProcessor):
    """Procesador para completar la línea de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "linea"
    
    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False

        chunks_lineas = []
        for doc in self.context.documentos[:3]: # Limitar a 3 documentos principales
            chunks = self._buscar_chunks_relevantes(
                ["tipología de proyectos", "líneas de subvención", "programa", "modalidad", 
                 "tipo de ayuda", "línea de actuación", "tipos de proyectos"],
                documento_id=doc['id'],
                limite=3
            )
            chunks_lineas.extend(chunks)
        
        if not chunks_lineas:
            return False
            
        contexto = "\n".join([c['chunk_texto'] for c in chunks_lineas])
        
        system_prompt = (
            "Eres un experto de convocatorias públicas españolas. Tu tarea es identificar las LÍNEAS "
            "PRINCIPALES para convocatorias oficiales siguiendo estas reglas estrictas:\n\n"
            "PRIORIDAD: Extraer SOLO las líneas de la convocatoria (máximo 3).\n\n "
            "FORMATO REQUERIDO:\n"
            "   - Entre 3-12 palabras clave\n"
            "   - En español formal\n"
            "   - Sin comillas, ni guiones, ni punto final, ni caracteres especiales\n"
            "   - Si hay varias líneas, sepáralas con saltos de línea ('\\n')\n"
            "   - Si no hay líneas, responde 'Individual'\n\n"
            "EJEMPLOS CORRECTOS:\n"
            "   - Proyectos de I+D Individuales\n"
            "   - Proyectos de I+D de Cooperación Nacional\n"
            "   - Proyectos de I+D de Cooperación Tecnológica Internacional\n"
            "   - Proyectos de I+D de Cooperación Tecnológica Europea\n"
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO las líneas de ayuda"
            f"cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )

        lineas = self._consultar_llm(system_prompt, user_prompt, max_tokens=150)
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, lineas)

class FechaInicioProcessor(BaseFieldProcessor):
    """Procesador para completar la fecha de inicio de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "fecha_inicio"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False

        chunks_fechas = []
        for doc in self.context.documentos[:3]:  # Limitar a 3 documentos principales
            chunks = self._buscar_chunks_relevantes(
                ["presentación de solicitudes", "plazo de solicitud", "fecha de inicio", "periodo de solicitud", 
                 "abierto desde", "convocatoria abierta", "plazo de presentación", "permanentemente abierta",
                 "presentación de solicitudes"],
                documento_id=doc['id'],
                limite=3
            )
            chunks_fechas.extend(chunks)
        
        if not chunks_fechas:
            return False
            
        contexto = "\n".join([c['chunk_texto'] for c in chunks_fechas])
        
        system_prompt = (
            "Eres un experto de convocatorias públicas españolas. Tu tarea es identificar la fecha "
            "de INICIO para convocatorias oficiales siguiendo estas reglas estrictas:\n\n "
            "PRIORIDAD: Extraer la fecha de INICIO de la convocatoria. Es la fecha en la que se abre "
            "el plazo de ayuda. SIEMPRE es anterior a la fecha de fin.\n\n "
            "FORMATO REQUERIDO:\n "
            "   - En formato textual si no se encuentra la fecha exacta "
            "   - En formato de fecha si se encuentra la fecha exacta\n "
            "   - En formato de fecha SOLO puede ser 'YYYY-MM-DD' o 'YYYY'\n "
            "   - Sin comillas, ni guiones, ni punto final, ni caracteres especiales\n "
            "   - Si se menciona 'permanente', 'continuo' o similar, devuelve 'Permanentemente'\n "
            "   - Si no se especifica o no tiene, devuelve 'No'\n\n "
            "EJEMPLOS CORRECTOS:\n "
            "   - Todo el año\n "
            "   - Permanentemente\n "
            "   - 2023-03-03\n "
            "   - 2024 "
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO la fecha de inicio"
            f"cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )

        fecha = self._consultar_llm(system_prompt, user_prompt, max_tokens=150)
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, fecha)
    
class FechaFinProcessor(BaseFieldProcessor):
    """Procesador para completar la fecha de fin de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "fecha_fin"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False
        
        chunks_fechas = []
        for doc in self.context.documentos[:3]:  # Limitar a 3 documentos principales
            chunks = self._buscar_chunks_relevantes(
                ["cierre de convocatoria", "fecha límite", "finalización plazo", "presentación de solicitudes"
                 "fecha de fin", "hasta", "convocatoria hasta", "plazo finaliza", "permanentemente abierta"],
                documento_id=doc['id'],
                limite=3
            )
            chunks_fechas.extend(chunks)
        
        if not chunks_fechas:
            return False
            
        contexto = "\n".join([c['chunk_texto'] for c in chunks_fechas])
        
        system_prompt = (
            "Eres un experto de convocatorias públicas españolas. Tu tarea es identificar la fecha "
            "de FIN para convocatorias oficiales siguiendo estas reglas estrictas:\n\n "
            "PRIORIDAD: Extraer la fecha de FIN de la convocatoria. Es la fecha límite para presentar "
            "solicitudes. SIEMPRE es posterior a la fecha de inicio.\n\n "
            "FORMATO REQUERIDO:\n"
            "   - En formato textual si no se encuentra la fecha exacta "
            "   - En formato de fecha si se encuentra la fecha exacta\n "
            "   - En formato de fecha SOLO puede ser 'YYYY-MM-DD' o 'YYYY'\n "
            "   - Sin comillas, ni guiones, ni punto final, ni caracteres especiales\n "
            "   - Si se menciona 'permanente', 'continuo' o similar, devuelve 'Permanentemente'\n "
            "   - Si no se especifica o no tiene, devuelve 'No'\n\n "
            "EJEMPLOS CORRECTOS:\n "
            "   - Todo el año\n "
            "   - Permanentemente\n "
            "   - 2024-05-01\n "
            "   - 2025 "
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO la fecha de fin"
            f"cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )

        fecha = self._consultar_llm(system_prompt, user_prompt, max_tokens=150)
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, fecha)
    
class ObjetivoProcessor(BaseFieldProcessor):
    """Procesador para completar el objetivo de la convocatoria."""

    @property
    def field_name(self) -> str:
        return "objetivo"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False

        chunks_objetivos = []
        for doc in self.context.documentos[:3]:  # Limitar a 3 documentos principales
            chunks = self._buscar_chunks_relevantes(
                ["objetivo", "finalidad", "propósito", "definición", "objeto",
                 "resuelve", "objetivos de la convocatoria", "fin de la ayuda"],
                documento_id=doc['id'],
                limite=3
            )
            chunks_objetivos.extend(chunks)
        
        if not chunks_objetivos:
            return False
            
        contexto = "\n".join([c['chunk_texto'] for c in chunks_objetivos])
        
        system_prompt = (
            "Eres un experto de convocatorias públicas españolas. Tu tarea es identificar el objetivo "
            "para convocatorias oficiales siguiendo estas reglas estrictas:\n\n"
            "PRIORIDAD: Extraer el objetivo general de la convocatoria. Es el propósito principal que "
            "se busca alcanzar con la ayuda, qué se pretende conseguir.\n\n"
            "FORMATO REQUERIDO:\n"
            "   - Preciso\n"                        
            "   - Máximo 50 palabras\n"
            "   - En español formal\n"
            "   - Sin comillas, ni guiones, ni punto final, ni caracteres especiales\n\n"
            "EJEMPLOS CORRECTOS:\n"
            "   - Fomentar la innovación tecnológica en pymes mediante ayudas a proyectos de I+D que "
            "incorporen nuevas tecnologías digitales\n"
            "   - Apoyar las inversiones en el sector industrial encaminadas a incrementar "
            "la productividad y competitividad de las microempresas"
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO el objetivo"
            f"cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )

        objetivo = self._consultar_llm(system_prompt, user_prompt, max_tokens=200)
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, objetivo)
    
class BeneficiariosProcessor(BaseFieldProcessor):
    """Procesador para completar los beneficiarios de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "beneficiarios"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False
        
        chunks_beneficiarios = []
        for doc in self.context.documentos[:3]:  # Limitar a 3 documentos principales
            chunks = self._buscar_chunks_relevantes(
                ["entidades beneficiarias", "beneficiarios", "destinatarios"],
                documento_id=doc['id'],
                limite=3
            )
            chunks_beneficiarios.extend(chunks)

        if not chunks_beneficiarios:
            return False            
        
        contexto = "\n".join([c['chunk_texto'] for c in chunks_beneficiarios])
        
        system_prompt = (
            "Eres un experto de convocatorias públicas españolas. Tu tarea es identificar los beneficiarios "
            "para convocatorias oficiales siguiendo estas reglas estrictas:\n\n"
            "PRIORIDAD: Extraer los beneficiarios de la convocatoria. Son los destinatarios de la ayuda. "
            "Suelen estar en el apartado de 'Beneficiarios' o 'Destinatarios'.\n\n"
            "FORMATO REQUERIDO:\n"
            "   - Preciso\n"
            "   - Máximo 50 palabras\n"
            "   - En español formal\n"
            "   - Sin comillas, ni guiones, ni punto final, ni caracteres especiales\n\n"
            "EJEMPLOS CORRECTOS:\n"
            "   - Microempresas, PYMES y autónomos\n"
            "   - Empresas y autónomos\n"
            "   - Empresas de cualquier tamaño "
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO los beneficiarios "
            f"cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )
        
        beneficiarios = self._consultar_llm(system_prompt, user_prompt, max_tokens=100)
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, beneficiarios)
    
class AnioProcessor(BaseFieldProcessor):
    """Procesador para completar el año de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "anio"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False
        
        chunks_fechas = []
        for doc in self.context.documentos[:3]: # Limitar a 3 documentos principales
            chunks = self._buscar_chunks_relevantes(
                ["periodo", "año", "publicación", "plazo"],
                documento_id=doc['id'],
                limite=3
            )
            chunks_fechas.extend(chunks)

        if not chunks_fechas:
            return False            
        
        contexto = "\n".join([c['chunk_texto'] for c in chunks_fechas])
        
        system_prompt = (
            "Eres un experto de convocatorias públicas españolas. Tu tarea es identificar el año de "
            "publicación para convocatorias oficiales siguiendo estas reglas estrictas:\n\n"
            "PRIORIDAD: Extraer el año de la convocatoria. Es el año (o años) en el que la convocatoria "
            "está abierta para presentar solicitudes. Es el año (o años) que aparece en la fecha de inicio "
            "y la fecha de fin. NO puede ser anterior al año de la fecha de inicio. Busca números de 4 "
            "dígitos entre 2000 y el año actual. Prioriza números cerca de palabras como 'año', 'periodo', "
            "'convocatoria'. Si hay varios años, elige el más reciente.\n\n"
            "FORMATO REQUERIDO:\n"
            "   - En formato SOLO 'YYYY' o 'YYYY-YYYY'\n"
            "   - Sin comillas, punto final o caracteres especiales\n\n"
            "EJEMPLOS CORRECTOS:\n"
            "   - 2023\n"
            "   - 2024\n"
            "   - 2025\n"
            "   - 2025-2027 "
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO el año "
            f"cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )
        
        anio = self._consultar_llm(system_prompt, user_prompt, max_tokens=10)
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, anio)
    
class AreaProcessor(BaseFieldProcessor):
    """Procesador para clasificar el área de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "area"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False
        
        chunks_area = []
        for doc in self.context.documentos[:3]: # Limitar a 3 documentos principales
            chunks = self._buscar_chunks_relevantes(
                ["área", "sector", "temática", "objetivo"],
                documento_id=doc['id'],
                limite=3
            )
            chunks_area.extend(chunks)

        if not chunks_area:
            return False            
        
        contexto = "\n".join([c['chunk_texto'] for c in chunks_area])
        
        system_prompt = (
            "Eres un experto en convocatorias públicas españolas. Tu tarea es clasificar el área temática "
            "de convocatoria en UNA de estas categorías:\n\n"
            "CATEGORÍAS:\n"
            "1. 'I+D': Proyectos de investigación y desarrollo\n"
            "2. 'Innovación': Proyectos de innovación tecnológica\n"
            "3. 'Inversión': Proyectos de inversión en activos fijos\n"
            "4. 'Ciberseguridad': Proyectos relacionados con la seguridad digital\n"
            "5. 'Contratación': Proyectos relacionados con la contratación\n"
            "6. 'Otro': Si no encaja en las anteriores\n\n"
            "FORMATO REQUERIDO:\n"
            "   - Responde EXACTAMENTE con una de estas palabras: I+D, Innovación, Inversión, "
            "Ciberseguridad, Contratación, Otro\n"
            "   - Sin explicaciones ni puntuación "
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO el área temática "
            f"cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )
        
        area = self._consultar_llm(system_prompt, user_prompt, max_tokens=20)
        
        # Validar áreas temáticas
        areas_validas = ['I+D', 'Innovación', 'Inversión', 'Ciberseguridad', 'Contratación']
        area = area if area in areas_validas else 'Otro'
        
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, area)
    
class PresupuestoMinimoProcessor(BaseFieldProcessor):
    """Procesador para completar el presupuesto mínimo de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "presupuesto_minimo"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False

        chunks_presupuesto = []
        for doc in self.context.documentos[:3]: # Limitar a 3 documentos principales
            chunks = self._buscar_chunks_relevantes(
                ["presupuesto mínimo", "importe mínimo", "inversión mínima", "mínimo de euros",
                 "cantidad mínima", "mínimo presupuestario", "mínimo a solicitar", "presupuesto inferior",
                 "mínimo elegible", "menor cuantía", "euros", "importe"],
                documento_id=doc['id'],
                limite=3
            )
            chunks_presupuesto.extend(chunks)

        if not chunks_presupuesto:
            return False
        
        contexto = "\n".join([c['chunk_texto'] for c in chunks_presupuesto])
        
        system_prompt = (
            "Eres un experto en convocatorias públicas españolas. Tu tarea es identificar el presupuesto "
            "MÍNIMO para convocatorias oficiales siguiendo estas reglas estrictas:\n\n"
            "PRIORIDAD: Extraer el presupuesto MÍNIMO (en euros) que se debe solicitar "
            "para la convocatoria. Es un campo OBLIGATORIO, por lo que se ha de buscar un presupuesto "
            "MÍNIMO para cada convocatoria.\n\n"
            "FORMATO REQUERIDO:\n"
            "   - En formato SOLO 'XXXXX' (número entero)\n"
            "   - Sin símbolos de euro, puntos o comas\n"
            "   - Sin comillas, punto final o caracteres especiales\n"
            "   - Si no se especifica o no tiene, devuelve 'No' "
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO el presupuesto mínimo "
            f"cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )
        
        presupuesto = self._consultar_llm(system_prompt, user_prompt, max_tokens=100)
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, presupuesto)
    
class PresupuestoMaximoProcessor(BaseFieldProcessor):
    """Procesador para completar el presupuesto máximo de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "presupuesto_maximo"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False
        
        chunks_presupuesto = []
        for doc in self.context.documentos[:3]: # Limitar a 3 documentos principales
            chunks = self._buscar_chunks_relevantes(
                ["presupuesto máximo", "importe máximo", "inversión máxima", "máximo de euros", 
                 "cantidad máxima", "máximo presupuestario", "máximo a solicitar", "presupuesto superior", 
                 "límite máximo", "máximo elegible", "mayor cuantía", "euros", "importe"],
                documento_id=doc['id'],
                limite=3
            )
            chunks_presupuesto.extend(chunks)

        if not chunks_presupuesto:
            return False            
        
        contexto = "\n".join([c['chunk_texto'] for c in chunks_presupuesto])
        
        system_prompt = (
            "Eres un experto en convocatorias públicas españolas. Tu tarea es identificar el presupuesto "
            "MÁXIMO para convocatorias oficiales siguiendo estas reglas estrictas:\n\n"
            "PRIORIDAD: Extraer el presupuesto MÁXIMO (en euros) que se debe solicitar "
            "para la convocatoria. Es un campo OBLIGATORIO, por lo que se ha de buscar un presupuesto "
            "MÁXIMO para cada convocatoria.\n\n"
            "FORMATO REQUERIDO:\n"
            "   - En formato SOLO 'XXXXX' (número entero)\n"
            "   - Sin símbolos de euro, puntos o comas\n"
            "   - Sin comillas, punto final o caracteres especiales\n"
            "   - Si no se especifica o no tiene, devuelve 'No' "
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO el presupuesto máximo "
            f"cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )
        
        presupuesto = self._consultar_llm(system_prompt, user_prompt, max_tokens=100)
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, presupuesto)
    
class DuracionMinimaProcessor(BaseFieldProcessor):
    """Procesador para completar la duración mínima de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "duracion_minima"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False
        
        chunks_duracion = []
        for doc in self.context.documentos[:3]: # Limitar a 3 documentos principales
            chunks = self._buscar_chunks_relevantes(
                ["duración mínima", "meses", "años", "plazo", "tiempo mínimo", "plazo mínimo", "mínimo de meses", 
                 "periodo mínimo", "ejecución mínima", "mínimo temporal", "menor duración", "mínimo requerido", 
                 "dura al menos", "mínimo vigencia", "mínimo temporalidad", "como mínimo", "no menos de"],
                documento_id=doc['id'],
                limite=3
            )
            chunks_duracion.extend(chunks)

        if not chunks_duracion:
            return False
        
        contexto = "\n".join([c['chunk_texto'] for c in chunks_duracion])
        
        system_prompt = (
            "Eres un experto de convocatorias públicas españolas. Tu tarea es identificar la duración "
            "MÍNIMA para convocatorias oficiales siguiendo estas reglas estrictas:\n\n"
            "PRIORIDAD: Extraer la duración MÍNIMA de la convocatoria. Es el tiempo mínimo "
            "que se debe cumplir. Suele estar en el apartado de duración mínima o plazos. SIEMPRE es "
            "menor a la duración máxima. Muchas veces es la misma duración que la duración máxima."
            "Es un campo OBLIGATORIO, por lo que se ha de buscar una duración MÍNIMA para cada "
            "convocatoria.\n\n"
            "FORMATO REQUERIDO:\n"
            "   - En número entero con unidad (meses, año, etc.)\n"
            "   - Sin comillas, ni guiones, ni punto final, ni caracteres especiales\n"
            "   - Si no se especifica o no tiene, devuelve 'No' "
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO la duración mínima "
            f"cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )
        
        duracion = self._consultar_llm(system_prompt, user_prompt, max_tokens=100)
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, duracion)
    
class DuracionMaximaProcessor(BaseFieldProcessor):
    """Procesador para completar la duración máxima de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "duracion_maxima"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False
        
        chunks_duracion = []
        for doc in self.context.documentos[:3]: # Limitar a 3 documentos principales
            chunks = self._buscar_chunks_relevantes(
                ["duración máxima", "meses", "años", "plazo", "tiempo máximo", "plazo máximo", 
                 "máximo de meses", "periodo máximo", "ejecución máxima", "máximo temporal", "mayor duración", 
                 "máximo permitido", "dura como máximo", "máximo vigencia", "máximo temporalidad", "como máximo"],
                documento_id=doc['id'],
                limite=3
            )
            chunks_duracion.extend(chunks)

        if not chunks_duracion:
            return False            
        
        contexto = "\n".join([c['chunk_texto'] for c in chunks_duracion])
        
        system_prompt = (
            "Eres un experto de convocatorias públicas españolas. Tu tarea es identificar la duración "
            "MÁXIMA para convocatorias oficiales siguiendo estas reglas estrictas:\n\n"
            "PRIORIDAD: Extraer la duración MÁXIMA de la convocatoria. Es el tiempo máximo "
            "que se debe cumplir. Suele estar en el apartado de duración máxima o plazos. SIEMPRE es "
            "igual o mayor a la duración mínima. Muchas veces es la misma duración que la duración "
            "mínima. Es un campo OBLIGATORIO, por lo que se ha de buscar una duración MÁXIMA para cada "
            "convocatoria.\n\n"
            "FORMATO REQUERIDO:\n"
            "   - En número entero con unidad (meses, año, etc.)\n"
            "   - Sin comillas, ni guiones, ni punto final, ni caracteres especiales\n"
            "   - Si no se especifica o no tiene, devuelve 'No' "
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO la duración máxima "
            f"cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )
        
        duracion = self._consultar_llm(system_prompt, user_prompt, max_tokens=100)
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, duracion)
    
class IntensidadSubvencionProcessor(BaseFieldProcessor):
    """Procesador para completar la intensidad de subvención de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "intensidad_subvencion"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False
        
        # Buscar en tablas
        chunks_con_tablas = []
        for doc in self.context.documentos[:3]:  # Limitar a 3 documentos principales
            chunks = self.db.obtener_chunks_con_tablas(doc['id'], limite=5)
            if chunks:
                chunks_con_tablas.extend(chunks)
        
        terminos_busqueda = [
            "intensidad subvención", "porcentaje ayuda", "tasa financiación", "cuantía máxima",
            "% subvencionable", "ayuda máxima", "porcentaje máximo", "cuantía de las subvenciones",
            "límite financiación no reembolsable", "costes subvencionables",
            "bonificación pyme", "incremento cooperativas", "proyectos colaboración"
        ]

        # Buscar en texto si no se encontró nada en tablas
        if not chunks_con_tablas:
            for doc in self.context.documentos[:3]: # Limitar a 3 documentos principales
                for termino in terminos_busqueda:
                    chunks = self._buscar_chunks_relevantes([termino], limite=5)
                    if chunks:
                        chunks_con_tablas.extend(chunks)

        if not chunks_con_tablas:
            return False
        
        # Preparar el contexto
        contexto = "INFORMACIÓN RELEVANTE:\n"
        if chunks_con_tablas and 'titulo_seccion' in chunks_con_tablas[0] and 'TABLA' in chunks_con_tablas[0]['titulo_seccion']:
            contexto = "INFORMACIÓN DE TABLAS:\n"
        
        contexto += "\n---\n".join([
            c['chunk_texto'] for c in chunks_con_tablas[:5] 
            if 'chunk_texto' in c
        ])

        system_prompt = (
            "Eres un experto de convocatorias públicas españolas. Tu tarea es identificar TODOS los porcentajes "
            "de subvención relevantes para convocatorias oficiales siguiendo estas reglas estrictas:\n\n "
            "PRIORIDAD: Extraer la intensidad de subvención. Es el porcentaje de financiación "
            "que se puede solicitar. Buscar primero en secciones marcadas como TABLA. Hay diferencias "
            "según el tamaño de empresa y el tipo de ayuda. Mencionar SOLO los límites máximos de ayuda.\n\n "
            "FORMATO REQUERIDO:\n "
            "   - Preciso\n "
            "   - Máximo 150 palabras\n "
            "   - En español formal\n "
            "   - Sin comillas, ni guiones, ni punto final, ni caracteres especiales\n "
            "   - Si hay varias intensidades de subvención, sepáralas con saltos de línea ('\\n')\n "
            "   - Si no se especifica o no tiene, devuelve 'No'\n\n "
            "EJEMPLOS CORRECTOS:\n"
            "   - Gran empresa: 15%\n "
            "   - Mediana empresa: 25%\n "
            "   - Pequeña empresa: 35%\n "
            "   - Investigación industrial: hasta el 40%\n "
            "   - Desarrollo experimental: hasta el 25% "
        )

        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO las intensidades de subvención "
            f"cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )
        
        resultado = self._consultar_llm(system_prompt, user_prompt, max_tokens=300)
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, resultado)

class IntensidadPrestamoProcessor(BaseFieldProcessor):
    """Procesador para completar la intensidad de préstamo de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "intensidad_prestamo"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False
        
        chunks_prestamos = []
        for doc in self.context.documentos[:3]: # Limitar a 3 documentos principales
            chunks = self._buscar_chunks_relevantes(
                ["préstamo", "financiación reembolsable", "crédito", "tipo de interés",
                "tramo no reembolsable", "carencia", "amortización", "amortización del préstamo",
                "euribor", "intereses", "garantías", "condiciones préstamo"],
                documento_id=doc['id'],
                limite=3
            )
            chunks_prestamos.extend(chunks)
        
        if not chunks_prestamos:
            return False
        
        contexto = "\n".join([c['chunk_texto'] for c in chunks_prestamos])
        
        system_prompt = (
            "Eres un asistente especializado en extraer información de intensidades de préstamo. "
            "Identifica el porcentaje MÁXIMO de préstamo que se puede solicitar. "
            "Responde SOLO con el porcentaje (ej: '50%' o '70 por ciento'), en un máximo 25 palabras si hay "
            "una explicación adicional. "
            "Si no se especifica o no tiene, devuelve 'No' "
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO las intensidades de préstamo "
            f"cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )
        
        prestamo = self._consultar_llm(system_prompt, user_prompt, max_tokens=200)
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, prestamo)
    
class TipoFinanciacionProcessor(BaseFieldProcessor):
    """Procesador para completar el tipo de financiación de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "tipo_financiacion"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False
        
        chunks_financiacion = []
        for doc in self.context.documentos[:3]: # Limitar a 3 documentos principales
            chunks = self._buscar_chunks_relevantes(
                ["tipo financiación", "subvención a fondo perdido", "ayuda no reembolsable", "financiación sin retorno",
                 "tipo de interés preferente", "subvención reembolsable", "préstamo reembolsable", "aval público",	
                 "capital riesgo", "financiación combinada", "ayuda a fondo perdido", "crédito participativo"],
                documento_id=doc['id'],
                limite=3
            )
            chunks_financiacion.extend(chunks)

        if not chunks_financiacion:
            return False
        
        contexto = "\n".join([c['chunk_texto'] for c in chunks_financiacion])
        
        system_prompt = (
            "Eres un experto de convocatorias públicas españolas. Tu tarea es identificar el tipo "
            "de financiación más adecuado para convocatorias oficiales siguiendo estas reglas estrictas:\n\n "
            "PRIORIDAD: Extraer el tipo de financiación de la convocatoria. Es la forma en que se otorga la ayuda, "
            "pública (subvención, préstamo, aval, etc.) y sus condiciones específicas (reembolsable, "
            "no reembolsable, porcentaje de cofinanciación, etc.). "
            "FORMATO REQUERIDO:\n "
            "   - Entre 3-5 palabras clave\n "
            "   - En español formal\n "
            "   - Sin comillas, ni guiones, ni punto final, ni caracteres especiales\n "
            "   - Si no se especifica o no tiene, devuelve 'No'\n\n "
            "EJEMPLOS CORRECTOS:\n "
            "   - Subvención\n "
            "   - Préstamo\n "
            "   - Mixta (Subvención + Préstamo) "
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO el tipo de financiación "
            f"cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )
        
        financiacion = self._consultar_llm(system_prompt, user_prompt, max_tokens=50)
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, financiacion)
    
class FormaPlazoCobroProcessor(BaseFieldProcessor):
    """Procesador para completar la forma y plazo de cobro de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "forma_plazo_cobro"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False
        
        chunks_plazos = []
        for doc in self.context.documentos[:3]:  # Limitar a 3 documentos principales
            chunks = self._buscar_chunks_relevantes(
                ["forma de pago", "modalidad de abono", "plazo de cobro", "pago único", "anticipo",
                 "liquidación", "justificación previa al pago", "desembolsos", "calendario de pagos",
                 "condiciones de financiación", "requisitos para el cobro", "anticipo de la ayuda"],
                documento_id=doc['id'],
                limite=3
            )
            chunks_plazos.extend(chunks)

        if not chunks_plazos:
            return False
        
        contexto = "\n".join([c['chunk_texto'] for c in chunks_plazos])
        
        system_prompt = (
            "Eres un experto de convocatorias públicas españolas. Tu tarea es identificar la forma y plazo "
            "de cobro más adecuado para convocatorias oficiales siguiendo estas reglas estrictas:\n\n "
            "PRIORIDAD: Extraer la forma y plazo de cobro de la convocatoria. Es cómo y cuándo se abonan" \
            "las ayudas (pagon único, fraccionado, anticipos, justificación previa, etc.).\n\n "
            "FORMATO REQUERIDO:\n "
            "   - Entre 10-40 palabras\n "
            "   - En español formal\n "
            "   - Sin comillas, ni guiones, ni punto final, ni caracteres especiales\n\n "
            "   - Si no se especifica o no tiene, devuelve 'No'\n\n "
            "EJEMPLOS CORRECTOS:\n "
            "   - Pago a la justificación de la ayuda\n "
            "   - Al finalizar cada anualidad más un anticipo inicial "
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO la forma y plazo "
            f"de cobro cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )
        
        forma = self._consultar_llm(system_prompt, user_prompt, max_tokens=150).strip()
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, forma)
    
class MinimisProcessor(BaseFieldProcessor):
    """Procesador para completar el régimen de minimis de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "minimis"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False
        
        chunks_minimis = []
        for doc in self.context.documentos[:3]: # Limitar a 3 documentos principales
            chunks = self._buscar_chunks_relevantes(
                ["ayudas de minimis", "reglamento (UE) 1407/2013", "límite minimis", 
                 "acumulación de ayudas", "declaración responsable de minimis"],
                documento_id=doc['id'],
                limite=3
            )
            chunks_minimis.extend(chunks)

        if not chunks_minimis:
            return False
        
        contexto = "\n".join([c['chunk_texto'] for c in chunks_minimis])
        
        system_prompt = (
            "Eres un experto de convocatorias públicas españolas. Tu tarea es identificar el régimen de "
            "minimis más adecuado para convocatorias oficiales siguiendo estas reglas estrictas:\n\n "
            "PRIORIDAD: Extraer el régimen de minimis de la convocatoria. Son ayudas de pequeño importe "
            "que no requieren notificación previa a la Comisión Europea.\n\n "
            "FORMATO REQUERIDO:\n "
            "   - Si hay régimen de minimis, responde 'Sí'\n "
            "   - Si no hay régimen de minimis, responde 'No'\n "
            "   - Sin comillas, ni guiones, ni punto final, ni caracteres especiales "
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO el régimen de minimis "
            f"cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )
        
        minimis = self._consultar_llm(system_prompt, user_prompt, max_tokens=10)
        minimis = 'Sí' if minimis.lower().startswith('sí') or minimis.lower().startswith('si') else 'No'

        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, minimis)
    
class RegionAplicacionProcessor(BaseFieldProcessor):
    """Procesador para completar la región de aplicación de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "region_aplicacion"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False
        
        chunks_region = []
        for doc in self.context.documentos[:3]: # Limitar a 3 documentos principales
            chunks = self._buscar_chunks_relevantes(
                ["región aplicación", "ámbito geográfico", "comunidad autónoma", "territorio de actuación",
                 "empresas radicadas en", "proyectos desarrollados en", "ubicación"],
                documento_id=doc['id'],
                limite=3
            )
            chunks_region.extend(chunks)

        if not chunks_region:
            return False

        contexto = "\n".join([c['chunk_texto'] for c in chunks_region])
        
        system_prompt = (
            "Eres un experto de convocatorias públicas españolas. Tu tarea es identificar la región de "
            "aplicación más adecuada para convocatorias oficiales siguiendo estas reglas estrictas:\n\n "
            "PRIORIDAD: Extraer la región de aplicación de la convocatoria. Es el territorio donde se ejecuta"
            "el proyecto o donde debe ubicarse el beneficiario.\n\n "
            "FORMATO REQUERIDO:\n "
            "   - En 1 frase\n "
            "   - En español formal\n "
            "   - Es el nombre de una región, comunidad autónoma o 'Estatal'\n "
            "   - Sin comillas, ni guiones, ni punto final, ni caracteres especiales\n\n "
            "   - Si no se especifica o no tiene, devuelve 'No'\n\n "
            "EJEMPLOS CORRECTOS:\n "
            "   - Andalucía\n "
            "   - Empresas con centro de trabajo en el País Vasco "
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO la región de "
            f"aplicación cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )
        
        region = self._consultar_llm(system_prompt, user_prompt, max_tokens=30).strip()
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, region)
    
class TipoConsorcioProcessor(BaseFieldProcessor):
    """Procesador para completar el tipo de consorcio de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "tipo_consorcio"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False
        
        chunks_consorcio = []
        for doc in self.context.documentos[:3]:  # Limitar a 3 documentos principales
            chunks = self._buscar_chunks_relevantes(
                ["consorcio", "agrupación de entidades", "colaboración público-privada", "empresas", 
                 "participantes", "socios", "colaboradores", "proyectos de cooperación", "consorcio de empresas"],
                documento_id=doc['id'],
                limite=3
            )
            chunks_consorcio.extend(chunks)

        if not chunks_consorcio:
            return False
        
        contexto = "\n".join([c['chunk_texto'] for c in chunks_consorcio])
        
        system_prompt = (
            "Eres un experto en convocatorias públicas españolas. Tu tarea es identificar el tipo de "
            "consorcio requerido para convocatorias oficiales siguiendo estas reglas estrictas:\n\n "
            "PRIORIDAD: Extraer el tipo de consorcio de la convocatoria. Es si la ayuda requiere o permite " \
            "agrupaciones (empresa y universidad, pymes, consorcios internacionales, etc.).\n\n "
            "FORMATO REQUERIDO:\n "
            "   - Entre 10-50 palabras\n "
            "   - En español formal\n "
            "   - Sin comillas, ni guiones, ni punto final, ni caracteres especiales\n\n "
            "   - Identifica si se requiere participación individual o en consorcio\n "
            "   - Extrae los requisitos de composición (mínimo/máximo de empresas)\n "
            "   - Especifica si hay requisitos especiales (p.ej. pymes, centros investigación)\n "
            "   - Si no se especifica o no tiene, devuelve 'No'\n\n "
            "EJEMPLOS CORRECTOS:\n "
            "- Individual o en cooperación con una o varias entidades\n "
            "- Mínimo 2 empresas, máximo 6 empresas\n "
            "- Consorcio con al menos 1 pyme y 1 centro de investigación "
        )
        
        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO los requisitos de consorcio "
            f"cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )

        consorcio = self._consultar_llm(system_prompt, user_prompt, max_tokens=150)
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, consorcio)
    
class CostesElegiblesProcessor(BaseFieldProcessor):
    """Procesador para completar los costes elegibles de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "costes_elegibles"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False
        
        chunks_costes = []
        for doc in self.context.documentos[:3]:  # Limitar a 3 documentos principales
            chunks = self._buscar_chunks_relevantes(
                ["costes elegibles", "gastos subvencionables", "costes subvencionables",
                 "gastos elegibles", "partidas elegibles", "costes financiables", "personal investigador", 
                 "materiales", "equipamiento", "gastos indirectos", "amortizaciones"],
                documento_id=doc['id'],
                limite=3
            )
            chunks_costes.extend(chunks)

        if not chunks_costes:
            return False

        contexto = "\n".join([c['chunk_texto'] for c in chunks_costes])        
        
        system_prompt = (
            "Eres un experto de convocatorias públicas. españolas. Tu tarea es identificar los costes "
            "elegibles más adecuados para convocatorias oficiales siguiendo estas reglas estrictas:\n\n "
            "PRIORIDAD: Extraer los costes elegibles de la convocatoria. Son los gastos que se pueden "
            "financiar con la ayuda. Deben ser gastos directos relacionados con el proyecto.\n\n "
            "FORMATO REQUERIDO:\n "
            "   - Máximo 50 palabras\n "
            "   - En español formal\n "
            "   - Sin comillas, ni guiones, ni punto final, ni caracteres especiales\n "
            "   - Si hay varios tipos de costes elegibles, sepáralos con saltos de línea ('\\n')\n "
            "   - Si no se especifica o no tiene, devuelve 'No'\n\n "
            "EJEMPLOS CORRECTOS:\n"
            "- Personal cualificado\n "
            "- Equipamiento tecnológico nuevo\n "
            "- Consultoría externa especializada "
        )

        user_prompt = (
            f"Analiza el siguiente texto de convocatoria pública y devuelve SOLO los costes elegibles "
            f"cumpliendo estrictamente las reglas indicadas:\n{contexto}"
        )

        costes = self._consultar_llm(system_prompt, user_prompt, max_tokens=150)
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, costes)
    
class EnlaceFichaTecnicaProcessor(BaseFieldProcessor):
    """Procesador para gestionar el enlace a la ficha técnica de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "enlace_ficha_tecnica"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False
        
        # Filtrar documentos marcados como fichas técnicas
        fichas_tecnicas = [doc for doc in self.context.documentos if doc.get('tipo_documento') == 'ficha_tecnica']
        
        if not fichas_tecnicas:
            return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, "No")
        
        # Seleccionar el documento más largo (mayor número de páginas)
        ficha_seleccionada = max(fichas_tecnicas, key=lambda x: x.get('numero_paginas', 0))
        
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, 
                                                ficha_seleccionada['enlace_documento'])
    
class EnlaceOrdenBasesProcessor(BaseFieldProcessor):
    """Procesador para gestionar el enlace a la orden de bases de la convocatoria."""
    
    @property
    def field_name(self) -> str:
        return "enlace_orden_bases"

    def process(self) -> bool:
        if not self.context.convocatoria_id or not self.context.documentos:
            return False
        
        # Filtrar documentos marcados como órdenes de bases
        ordenes_bases = [doc for doc in self.context.documentos if doc.get('tipo_documento') == 'orden_bases']
        
        if not ordenes_bases:
            return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name, "No")
        
        # Concatenar todos los enlaces de órdenes de bases
        enlaces = "\n".join({doc['enlace_documento'] for doc in ordenes_bases})
        return self.db.actualizar_campo_convocatoria(self.context.convocatoria_id, self.field_name,
                                                enlaces if enlaces else "No")