"""
Módulo para dividir texto en fragmentos.
"""

import re
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter

class TextSplitter:
    """Divide el texto en fragmentos más pequeños."""
    
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            add_start_index=True,
            separators=["\n\n", "\n", "  ", " ", ""]
        )

    def split(self, texto: str) -> List[str]:
        """Divide el texto en fragmentos, preservando estructura de tablas."""
        try:
            partes = re.split(r'(--- TABLA \d+ PÁG \d+ ---)', texto)
            chunks = []
            i = 0

            while i < len(partes):
                parte = partes[i].strip()
                if not parte:
                    i += 1
                    continue

                if re.match(r'--- TABLA \d+ PÁG \d+ ---', parte):
                    # Combinar marcador de tabla y contenido siguiente
                    if i + 1 < len(partes):
                        contenido_tabla = partes[i + 1].strip()
                        chunk_tabla = f"{parte}\n{contenido_tabla}"
                        chunks.append(chunk_tabla)
                        i += 2
                    else:
                        chunks.append(parte)
                        i += 1
                else:
                    chunks.extend(self.text_splitter.split_text(parte))
                    i += 1

            return chunks
        
        except Exception as e:
            print(f"Error dividiendo texto en chunks: {str(e)}")
            return []