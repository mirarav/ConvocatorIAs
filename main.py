"""
Punto de entrada principal del sistema ConvocatorIAs.
"""

import time

from nucleo.base_datos.modelos import Database
from agentes.orquestador.gestor_cli import Orquestador

def inicializar_sistema(max_intentos=10, espera=2) -> bool:
    """Intenta inicializar la base de datos con reintentos."""
    db = Database()
    for intento in range(max_intentos):
        try:
            if db.verificar_crear_tablas():
                return True
            print(f"Intento {intento+1}/{max_intentos}. Base de datos no disponible...")
            time.sleep(espera)
        except Exception as e:
            print(f"Error en intento {intento+1}: {str(e)}")
            time.sleep(espera)
    return False

def main():
    """Función principal que inicia el sistema."""
    if not inicializar_sistema():
        print("Error al inicializar. Verifique:\n- Servicio DB\n- Credenciales (.env)\n- Conexión de red")
        return
    
    try:
        Orquestador().main()
    except Exception as e:
        print(f"\nError crítico: {str(e)}\nReporte este error al administrador\n")

if __name__ == '__main__':
    main()