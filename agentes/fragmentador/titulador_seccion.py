"""
Módulo para generar títulos de sección.
"""

import re

class SectionTitleGenerator:
    """Genera títulos representativos para cada fragmento de texto."""
    
    def generate(self, chunk: str, numero_pagina: int, chunk_num: int) -> str:
        """Genera un título de sección para un fragmento de texto."""
        # Usar marcado especial si es una tabla
        if re.match(r'--- TABLA \d+ PÁG \d+ ---', chunk):
            match = re.search(r'--- TABLA (\d+) PÁG (\d+) ---', chunk)
            tabla_num = match.group(1) if match else "?"
            return f"TABLA {tabla_num} (PÁG {numero_pagina})"
        
        # Usar numeración estándar si es texto
        return f"Página {numero_pagina} - Chunk {chunk_num}"