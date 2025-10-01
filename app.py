from dash import Dash, dcc, html
from dash.dependencies import Input, Output

import plotly.graph_objects as go
import plotly.subplots as sp
import numpy as np
import json, os

# Usamos funciones y constantes desde fuzzy_core
from fuzzy_core import (
    create_system_from_json as run_system, 
    create_mf, X_COLOR, KEY_POINTS, X_OUTPUT, get_output_functions
)
from app_layout import create_layout


# Inicialización de la App Dash
app = Dash(__name__)
app.title = "Clasificador Fuzzy Interactivo (Probador de Modelos)"
app.layout = create_layout()


# --- CALLBACK 1: Actualizar la Gráfica de MF ---
@app.callback(
    Output('mf-graph', 'figure'),
    [Input('mf-type-selector', 'value')]
)
def update_mf_graph(mf_type_selected):
    fig = go.Figure()

    for name, points in KEY_POINTS.items():
        mf_values = create_mf(mf_type_selected, points, X_COLOR)
        fig.add_trace(go.Scatter(x=X_COLOR, y=mf_values, mode='lines', name=name))

    fig.update_layout(
        title=f'Funciones de Pertenencia de Entrada: {mf_type_selected}',
        xaxis_title='Intensidad de Color (0-255)',
        yaxis_title='Grado de Pertenencia (0-1)',
        yaxis_range=[0, 1.1]
    )
    return fig


# --- CALLBACK 2: Actualizar Información del Archivo Seleccionado ---
@app.callback(
    Output('active-rules-info', 'children'),
    [Input('ruleset-selector', 'value')]
)
def update_rules_info(rules_filename):
    return f"Set de reglas activo: {rules_filename} (3 variables, 4 conjuntos)"


# --- CALLBACK 3: Simulación principal (Defuzzificación Final) ---
@app.callback(
    [Output('output-text', 'children'),
     Output('color-sample', 'style'),
     Output('defuzz-graph', 'figure')],
    [Input('R-slider', 'value'),
     Input('G-slider', 'value'),
     Input('B-slider', 'value'),
     Input('ruleset-selector', 'value'), 
     Input('mf-type-selector', 'value')] 
)
def run_simulation_and_update_ui(R, G, B, rules_filename, mf_type_selected):

    final_output_val, color_simulador = run_system(
        rules_filename, R, G, B, mf_type_selected 
    )

    hex_color = f'rgb({R},{G},{B})'
    style = {
        'backgroundColor': hex_color,
        'width': '100px',
        'height': '100px',
        'margin': '20px auto',
        'border': '2px solid black'
    }
    
    fig = go.Figure()
    text_output = f"Modelo: {rules_filename} | Clasificación no generada. Revise el archivo JSON."

    if final_output_val is not None and color_simulador is not None:
        text_output = f"Clasificación Fuzzy: {float(final_output_val):.2f} / 100"

        # ✅ Tomar el conjunto agregado (la unión de todas las salidas activadas)
        try:
            agregado_np = color_simulador.aggregate['ColorOutput']
        except Exception:
            agregado_np = np.zeros_like(X_OUTPUT)

        # --- Área del conjunto agregado ---
        fig.add_trace(go.Scatter(
            x=X_OUTPUT, y=agregado_np,
            mode='lines', fill='tozeroy', 
            name='Conjunto Agregado',
            line=dict(color='blue', width=2),
            fillcolor='rgba(0,0,255,0.5)'
        ))

        # --- Línea del centroide (valor defuzzificado) ---
        max_height = np.max(agregado_np) if agregado_np.size > 0 else 1.0
        fig.add_trace(go.Scatter(
            x=[float(final_output_val), float(final_output_val)], 
            y=[0.0, float(max_height)], 
            mode='lines', 
            name='Centroide (Defuzzificación)',
            line=dict(color='red', dash='solid', width=3)
        ))

    fig.update_layout(
        title='Resultado de Defuzzificación', 
        xaxis_range=[0, 100],
        yaxis_range=[0, 1.1],
        xaxis_title="Salida (0-100)",
        yaxis_title="Grado de pertenencia"
    )

    return text_output, style, fig



# --- FUNCIÓN AUXILIAR: Gráfica de regla estilo Toolbox ---
def plot_rule_toolbox(rule, R_val, G_val, B_val, mf_type_selected):
    fig = sp.make_subplots(rows=1, cols=4,
                           subplot_titles=("Rojo", "Verde", "Azul", "Salida"))

    selected_mf = {
        name: create_mf(mf_type_selected, points, X_COLOR)
        for name, points in KEY_POINTS.items()
    }
    crisp_vals = {"Rojo": R_val, "Verde": G_val, "Azul": B_val}

    # Entradas (Rojo, Verde, Azul)
    for j, var in enumerate(["Rojo", "Verde", "Azul"], start=1):
        mf_vals = selected_mf[rule[var]]
        crisp = crisp_vals[var]

        fig.add_trace(go.Scatter(x=X_COLOR, y=mf_vals,
                                 mode="lines", line=dict(color="black")),
                      row=1, col=j)
        fig.add_trace(go.Scatter(x=[crisp, crisp], y=[0, 1],
                                 mode="lines", line=dict(color="red")),
                      row=1, col=j)
        fig.add_trace(go.Scatter(x=X_COLOR, y=mf_vals,
                                 mode="lines", fill="tozeroy",
                                 line=dict(color="yellow", width=0)),
                      row=1, col=j)

    # Salida (recorte por activación)
    salida = get_output_functions()[rule["OUTPUT"]]
    activacion = min(
        np.interp(R_val, X_COLOR, selected_mf[rule["Rojo"]]),
        np.interp(G_val, X_COLOR, selected_mf[rule["Verde"]]),
        np.interp(B_val, X_COLOR, selected_mf[rule["Azul"]])
    )
    salida_recortada = np.minimum(activacion, salida)

    fig.add_trace(go.Scatter(x=X_OUTPUT, y=salida,
                             mode="lines", line=dict(color="black")),
                  row=1, col=4)
    fig.add_trace(go.Scatter(x=X_OUTPUT, y=salida_recortada,
                             mode="lines", fill="tozeroy",
                             line=dict(color="blue", width=0)),
                  row=1, col=4)

    fig.update_layout(height=250, showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
    return fig


# --- CALLBACK 4: Visualizador estilo Toolbox ---
@app.callback(
    Output('rules-graphs-container', 'children'),
    [Input('ruleset-selector', 'value'),
     Input('mf-type-selector', 'value'),
     Input('R-slider', 'value'),
     Input('G-slider', 'value'),
     Input('B-slider', 'value')]
)
def update_rules_graphs(rules_filename, mf_type_selected, R_val, G_val, B_val):
    figs = []
    filepath = os.path.join("rules_data", rules_filename)
    try:
        with open(filepath, 'r') as f:
            rules_data = json.load(f)
    except Exception:
        return [html.Div("⚠️ No se pudo cargar el archivo de reglas.", 
                         style={'color': 'red', 'textAlign': 'center'})]

    for i, rule in enumerate(rules_data, start=1):
        fig = plot_rule_toolbox(rule, R_val, G_val, B_val, mf_type_selected)
        figs.append(html.Div([
            html.H5(f"Regla {i}: IF R={rule['Rojo']} AND G={rule['Verde']} AND B={rule['Azul']} → {rule['OUTPUT']}",
                    style={'textAlign': 'center'}),
            dcc.Graph(figure=fig, style={'height': '260px'})
        ], style={'marginBottom': '20px'}))

    return figs


if __name__ == '__main__':
    print("Iniciando la aplicación Dash. Abre tu navegador en http://127.0.0.1:8050/")
    app.run(debug=True)
