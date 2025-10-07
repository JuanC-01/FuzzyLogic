import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from rules_loader import load_rules_from_file  


# 1. Universos y Constantes
X_COLOR = np.arange(0, 256, 1)
X_OUTPUT = np.arange(0, 101, 1)

KEY_POINTS = {
    'Bajo': [0, 0, 85],
    'MedioBajo': [0, 85, 170],
    'MedioAlto': [85, 170, 255],
    'Alto': [170, 255, 255],
}

MF_TYPES = ['Triangular (trimf)', 'Trapezoidal (trapmf)']
LEVELS = list(KEY_POINTS.keys())
COLORS_OUT = ['Rojo', 'Naranja', 'Amarillo', 'VerdeLima', 'Verde', 'Cian', 'Azul', 'Magenta']


def create_mf(mf_type, points, universe):
    """Crea una función de pertenencia según el tipo y los puntos dados."""
    a, b, c = points[0], points[1], points[2]

    if 'Triangular' in mf_type:
        return fuzz.trimf(universe, [a, b, c])

    elif 'Trapezoidal' in mf_type:
        p1 = a
        p2 = b - 20 if b > 20 else b
        p3 = b + 20 if b < 235 else b
        p4 = c

        if p2 < p1: p2 = p1
        if p3 > p4: p3 = p4

        return fuzz.trapmf(universe, [p1, p2, p3, p4])

    return fuzz.trimf(universe, [a, b, c])


def get_output_functions(mf_type_selected="Triangular (trimf)"):
    """Genera las funciones de salida (consequents) para todos los colores del sistema RGB difuso."""
    
    def make_mf(a, b, c):
        if "Trapezoidal" in mf_type_selected:
            p1, p2, p3, p4 = a, b - 5, b + 5, c 
            if p2 < p1: p2 = p1
            if p3 > p4: p3 = p4
            return fuzz.trapmf(X_OUTPUT, [p1, p2, p3, p4])
        else:
            return fuzz.trimf(X_OUTPUT, [a, b, c])

    # DEFINICIÓN COMPLETA CON TODAS TUS ETIQUETAS
    color_definitions = {
        # Tonos Oscuros/Bajos
        'Negro': (0, 0, 5),
        'AzulOscuro': (5, 10, 20),
        'VerdeOscuro': (15, 20, 30),
        'RojoOscuro': (25, 30, 40),
        'NaranjaOscuro': (30, 35, 45),
        'AmarilloOscuro': (35, 40, 50),
        'CianOscuro': (40, 45, 55),
        'MagentaOscuro': (45, 50, 60),
        
        # Colores Base/Medios
        'Azul': (50, 55, 65),
        'Cian': (55, 60, 70),
        'Verde': (60, 65, 75),
        'Amarillo': (65, 70, 80),
        'Naranja': (70, 75, 85),
        'Rojo': (75, 80, 90),
        'Magenta': (80, 85, 95),
        
        # Tonos Claros/Brillantes
        'AmarilloClaro': (70, 75, 85),
        'NaranjaClaro': (75, 80, 90),
        'CianClaro': (78, 83, 93),
        'MagentaClaro': (82, 87, 97),
        'Rosa': (70, 80, 90),
        'BlancoApagado': (65, 75, 85),
        'Blanco': (85, 90, 98),
        
        'AzulBrillante': (85, 90, 95),
        'CianBrillante': (88, 93, 98),
        'VerdeBrillante': (88, 93, 98),
        'AmarilloBrillante': (90, 95, 100),
        'RojoBrillante': (90, 95, 100),
        'MagentaBrillante': (92, 97, 100),
        'BlancoBrillante': (95, 100, 100),
        
        # Colores personalizados de tus reglas
        'VerdeAzulado': (55, 65, 75),
        'VerdeAzuladoBrillante': (75, 85, 95),
        'Gris': (40, 50, 60),
        'Lavanda': (65, 75, 85),
        'AmarilloVerde': (60, 70, 80),
        'AmarilloVerdeClaro': (70, 80, 90),
        'RojoMagenta': (70, 80, 90),
        'Salmon': (75, 85, 95),
        'LavandaClaro': (75, 85, 95),
        'RosaClaro': (80, 90, 100),
        'RosaBrillante': (85, 95, 100),
        'BlancoAzulado': (85, 92, 100),
        'AmarilloVerdeBrillante': (85, 95, 100),
        'BlancoVerde': (88, 95, 100),
        'RojoMagentaBrillante': (90, 97, 100),
        'Melon': (80, 90, 100),
        'AmarilloClaroBrillante': (85, 95, 100),
        'BlancoAmarillento': (90, 97, 100),
        'BlancoPuro': (98, 100, 100),
        'NaranjaBrillante': (85, 92, 100),  # <-- ESTA FALTABA
    }
    
    # Crear las funciones de pertenencia
    output_funcs = {}
    for color_name, (a, b, c) in color_definitions.items():
        output_funcs[color_name] = make_mf(a, b, c)
    
    return output_funcs
# --- FUNCIÓN PRINCIPAL DEL SISTEMA FUZZY ---
def create_system_from_json(rules_filename, R_val, G_val, B_val, mf_type_selected):
    """
    Crea y ejecuta el sistema de control Fuzzy basado en un archivo JSON de reglas.
    """

    # 1. Variables de Entrada y Salida
    Rojo = ctrl.Antecedent(X_COLOR, 'Rojo')
    Verde = ctrl.Antecedent(X_COLOR, 'Verde')
    Azul = ctrl.Antecedent(X_COLOR, 'Azul')
    Clasificacion = ctrl.Consequent(X_OUTPUT, 'ColorOutput')

    # Funciones de entrada (MF)
    selected_mf = {
        name: create_mf(mf_type_selected, points, X_COLOR)
        for name, points in KEY_POINTS.items()
    }
    for var in [Rojo, Verde, Azul]:
        for name, func in selected_mf.items():
            var[name] = func

    # Funciones de salida
    for label, mf in get_output_functions(mf_type_selected).items():
        Clasificacion[label] = mf

    # 2. Cargar reglas desde archivo usando rules_loader
    rules = load_rules_from_file(rules_filename, Rojo, Verde, Azul, Clasificacion)

    if not rules:
        # Regla de emergencia si no hay reglas válidas
        rules = [ctrl.Rule(Rojo['Bajo'] | Verde['Bajo'] | Azul['Bajo'], Clasificacion['Azul'])]

    # 3. Crear y ejecutar sistema de control
    control_system = ctrl.ControlSystem(rules)
    color_simulador = ctrl.ControlSystemSimulation(control_system)

    color_simulador.input['Rojo'] = R_val
    color_simulador.input['Verde'] = G_val
    color_simulador.input['Azul'] = B_val

    try:
        color_simulador.compute()
    except Exception as e:
        print(f"Error en computación fuzzy: {e}")
        return None, None

    return color_simulador.output.get('ColorOutput'), color_simulador
