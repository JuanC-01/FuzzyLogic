from dash import dcc
from dash import html
from fuzzy_core import LEVELS, COLORS_OUT, MF_TYPES 
from fuzzy_core import X_COLOR, KEY_POINTS 

# --- DATA NECESARIA PARA EL SELECTOR DE ARCHIVOS ---
RULE_FILES = [
    {'label': '100% Reglas Posibles (64)', 'value': 'rules_100.json'},
    {'label': '60% Reglas de Prueba (38)', 'value': 'rules_60.json'},
    {'label': '30% Reglas Mínimas (19)', 'value': 'rules_30.json'},
]
# --- FIN DATA ---


# --- Helpers  ---
def create_color_slider(id_name, label_text, color):
    custom_marks = {
        0: {'label': '0 (Bajo)', 'style': {'color': 'black'}},
        85: {'label': '85 (Cruce)', 'style': {'color': 'gray'}},
        170: {'label': '170 (Cruce)', 'style': {'color': 'gray'}},
        255: {'label': '255 (Alto)', 'style': {'color': 'black'}},
    }
    return html.Div([
        html.Label(label_text, style={'color': color, 'fontWeight': 'bold'}),
        dcc.Slider(id=id_name, min=0, max=255, step=1, value=128,
                   marks=custom_marks)
    ], style={'padding': '10px 0', 'width': '90%', 'margin': 'auto'})
    
    
# ----------------------------------------------------
# MÓDULOS DEL LAYOUT
# ----------------------------------------------------

def build_tab_io_with_selector():
    """
    Pestaña 1 (FUSIONADA): Entradas, Salidas y Selector de Modelo.
    """
    return dcc.Tab(label='1. Entrada, Salida y Modelo', children=[
        html.Div([
            html.H3("Modelo de Reglas", style={'textAlign': 'center', 'marginTop': '15px'}),
            
            # --- SELECTOR DE MODELO (Movido de la Pestaña 3) ---
            html.Div([
                html.Label('Selecciona el Set de Reglas a Probar:', style={'fontWeight': 'bold', 'marginRight': '10px'}),
                dcc.Dropdown(
                    id='ruleset-selector',
                    options=RULE_FILES,
                    value=RULE_FILES[0]['value'], # 100% por defecto
                    style={'width': '350px', 'margin': 'auto'}
                ),
            ], style={'textAlign': 'center', 'maxWidth': '500px', 'margin': '20px auto'}),
            
            html.P(id='active-rules-info', style={'textAlign': 'center', 'fontWeight': 'bold', 'color': 'darkgreen'}),
            
            html.Hr(),
            
            # --- ENTRADAS RGB ---
            html.H3("Entradas RGB", style={'textAlign': 'center'}),
            create_color_slider('R-slider', 'Rojo (R)', '#FF0000'),
            create_color_slider('G-slider', 'Verde (G)', '#00FF00'),
            create_color_slider('B-slider', 'Azul (B)', '#0000FF'),

            html.Div(id='color-sample', style={
                'width': '100px', 'height': '100px', 'margin': '20px auto', 
                'border': '2px solid black'
            }),
            
            html.Hr(),
            
            # --- RESULTADO Y GRÁFICO ---
            html.H3("Resultado", style={'textAlign': 'center'}),
            html.H3(id='output-text', style={'textAlign': 'center'}),
            dcc.Graph(id='defuzz-graph', style={'height': '350px'}),
            
        ], style={'maxWidth': '900px', 'margin': 'auto', 'padding': '20px'})
    ])


def build_tab_mf_config():
    """Pestaña 2: Configuración de MF (SIN CAMBIOS)"""
    return dcc.Tab(label='2. Configuración de MF', children=[
        # ... (Contenido de la configuración de MF)
        html.Div([
            html.H3("Seleccionar Tipo de Función de Pertenencia", style={'textAlign': 'center'}),
            
            html.Div([
                html.Label('Tipo de Función (MF) para Entradas:', style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='mf-type-selector',
                    options=[{'label': t, 'value': t} for t in MF_TYPES],
                    value=MF_TYPES[0], 
                    style={'width': '300px', 'margin': '10px auto'}
                ),
            ], style={'textAlign': 'center', 'margin': '20px 0'}),

            html.Hr(),
            html.H4("Visualización de las Funciones de Pertenencia Generadas"),
            dcc.Graph(id='mf-graph', style={'height': '400px'}), 

        ], style={'maxWidth': '900px', 'margin': 'auto', 'padding': '20px'})
    ])

def build_tab_rules_viewer():
    """Pestaña 3: Visualización de Reglas"""
    return dcc.Tab(label='3. Visualizador de Reglas', children=[
        html.Div([
            html.H3("Visualización de Reglas Difusas", style={'textAlign': 'center'}),
            html.Div(id='rules-graphs-container')
        ], style={'maxWidth': '900px', 'margin': 'auto', 'padding': '20px'})
    ])



def create_layout():
    """Ensambla todos los módulos en una estructura de pestañas (solo 2 ahora)."""
    return html.Div([
        html.H1("Clasificador Fuzzy Interactivo (Probador de Modelos)", style={'textAlign': 'center', 'padding': '10px'}),
        dcc.Tabs(id="tabs", value='tab-1', children=[
            build_tab_io_with_selector(),      # NUEVA PESTAÑA 1 (Fusionada)
            build_tab_mf_config(),             # PESTAÑA 2 (MF)
            build_tab_rules_viewer() # PESTAÑA 3 (Visor de Reglas)
        ]),
        
        # Almacenamiento invisible necesario para el flujo de datos
        dcc.Store(id='rules-data', data=[]),
    ])