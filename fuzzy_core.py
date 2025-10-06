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
            p1, p2, p3, p4 = a, b - 3, b + 3, c
            if p2 < p1: p2 = p1
            if p3 > p4: p3 = p4
            return fuzz.trapmf(X_OUTPUT, [p1, p2, p3, p4])
        else:
            return fuzz.trimf(X_OUTPUT, [a, b, c])

    return {
        # Tonos oscuros
        'Negro': fuzz.trimf(X_OUTPUT, [0, 0, 5]),
        'AzulOscuro': fuzz.trimf(X_OUTPUT, [5, 10, 20]),
        'VerdeOscuro': fuzz.trimf(X_OUTPUT, [10, 15, 25]),
        'RojoOscuro': fuzz.trimf(X_OUTPUT, [15, 20, 30]),
        'NaranjaOscuro': fuzz.trimf(X_OUTPUT, [20, 25, 35]),
        'AmarilloOscuro': fuzz.trimf(X_OUTPUT, [25, 30, 40]),
        'CianOscuro': fuzz.trimf(X_OUTPUT, [30, 35, 45]),
        'MagentaOscuro': fuzz.trimf(X_OUTPUT, [35, 40, 50]),
        
        # Colores base
        'Azul': fuzz.trimf(X_OUTPUT, [40, 45, 55]),
        'Cian': fuzz.trimf(X_OUTPUT, [50, 55, 65]),
        'Verde': fuzz.trimf(X_OUTPUT, [55, 60, 70]),
        'Amarillo': fuzz.trimf(X_OUTPUT, [60, 65, 75]),
        'Naranja': fuzz.trimf(X_OUTPUT, [65, 70, 80]),
        'Rojo': fuzz.trimf(X_OUTPUT, [70, 75, 85]),
        'Magenta': fuzz.trimf(X_OUTPUT, [75, 80, 90]),
        'Blanco': fuzz.trimf(X_OUTPUT, [80, 85, 95]),

        # Tonos claros y brillantes
        'AzulBrillante': fuzz.trimf(X_OUTPUT, [85, 90, 95]),
        'CianBrillante': fuzz.trimf(X_OUTPUT, [85, 90, 100]),
        'VerdeBrillante': fuzz.trimf(X_OUTPUT, [85, 90, 100]),
        'AmarilloBrillante': fuzz.trimf(X_OUTPUT, [85, 95, 100]),
        'RojoBrillante': fuzz.trimf(X_OUTPUT, [85, 95, 100]),
        'MagentaBrillante': fuzz.trimf(X_OUTPUT, [85, 95, 100]),
        'BlancoBrillante': fuzz.trimf(X_OUTPUT, [90, 100, 100]),
        
        # Tonos intermedios y especiales
        'AmarilloClaro': fuzz.trimf(X_OUTPUT, [70, 80, 90]),
        'NaranjaClaro': fuzz.trimf(X_OUTPUT, [70, 80, 90]),
        'MagentaClaro': fuzz.trimf(X_OUTPUT, [70, 80, 90]),
        'CianClaro': fuzz.trimf(X_OUTPUT, [70, 80, 90]),
        'Rosa': fuzz.trimf(X_OUTPUT, [75, 85, 95]),
        'VerdeLima': fuzz.trimf(X_OUTPUT, [65, 75, 85]),
        'BlancoApagado': fuzz.trimf(X_OUTPUT, [60, 70, 80]),
    }


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
    for label, mf in get_output_functions().items():
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
    except Exception:
        return None, None

    return color_simulador.output.get('ColorOutput'), color_simulador

