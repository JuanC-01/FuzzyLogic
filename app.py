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
app.title = "Clasificador Fuzzy"
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
        xaxis_title='Intensidad de Color (0–255)',
        yaxis_title='Grado de Pertenencia (0–1)',
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


# --- CALLBACK 3: Ejecutar el sistema Fuzzy ---
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
    """
    Ejecuta el sistema difuso y actualiza los elementos visuales del dashboard.
    """
    final_output_val, color_simulador = run_system(rules_filename, R, G, B, mf_type_selected)

    # --- Cuadro de color RGB ---
    hex_color = f'rgb({R},{G},{B})'
    style = {
        'backgroundColor': hex_color,
        'width': '100px',
        'height': '100px',
        'margin': '20px auto',
        'border': '2px solid black',
        'boxShadow': '0 0 10px rgba(0,0,0,0.3)'
    }

    fig = go.Figure()
    text_output = f"Modelo: {rules_filename} | Clasificación no generada."

    if final_output_val is not None and color_simulador is not None:
        text_output = f"Clasificación Fuzzy: {float(final_output_val):.2f} / 100"

        try:
            output_funcs = get_output_functions(mf_type_selected)
            agregado_np = np.zeros_like(X_OUTPUT)

            # Método ALTERNATIVO: Usar el conjunto agregado interno de skfuzzy si está disponible
            if hasattr(color_simulador, 'aggregate') and color_simulador.aggregate is not None:
                # Si skfuzzy ya calculó el agregado, usarlo directamente
                agregado_np = color_simulador.aggregate
            else:
                # Método de respaldo: reconstruir manualmente
                for i, rule in enumerate(color_simulador.ctrl.rules):
                    try:
                        # Calcular activación de forma más robusta
                        activacion_regla = 1.0
                        
                        # Método alternativo para acceder a los términos del antecedente
                        if hasattr(rule.antecedent, '_terms'):
                            terms_dict = rule.antecedent._terms
                        elif hasattr(rule.antecedent, 'terms'):
                            terms_dict = rule.antecedent.terms
                        else:
                            continue
                            
                        for (var_obj, term_obj) in terms_dict.items():
                            var_name = var_obj.label
                            term_label = term_obj.label
                            
                            # Obtener valor crisp
                            if var_name == 'Rojo':
                                crisp_val = R
                            elif var_name == 'Verde':
                                crisp_val = G  
                            elif var_name == 'Azul':
                                crisp_val = B
                            else:
                                continue
                                
                            # Calcular grado de pertenencia
                            mf_vals = create_mf(mf_type_selected, KEY_POINTS[term_label], X_COLOR)
                            grado = np.interp(crisp_val, X_COLOR, mf_vals)
                            activacion_regla = min(activacion_regla, grado)
                        
                        # Obtener etiqueta de salida
                        salida_label = None
                        consequent_str = str(rule.consequent)
                        # Buscar patrones como "ColorOutput IS Verde" o "ColorOutput_is_Verde"
                        if 'IS' in consequent_str:
                            parts = consequent_str.split('IS')
                            if len(parts) > 1:
                                salida_label = parts[1].strip()
                        elif '_is_' in consequent_str:
                            parts = consequent_str.split('_is_')
                            if len(parts) > 1:
                                salida_label = parts[1].strip()
                        
                        if salida_label and salida_label in output_funcs:
                            mf_salida = output_funcs[salida_label]
                            implicacion = np.minimum(mf_salida, activacion_regla)
                            agregado_np = np.maximum(agregado_np, implicacion)
                            
                    except Exception as e:
                        # Si falla, continuar con la siguiente regla
                        continue

            # Si no hay activación, crear forma suave alrededor del centroide
            if np.max(agregado_np) == 0 and final_output_val is not None:
                centroide = final_output_val
                x_vals = X_OUTPUT
                y_vals = np.exp(-0.05 * (x_vals - centroide)**2)
                agregado_np = y_vals * 0.3

            # --- Gráfica del conjunto agregado ---
            fig.add_trace(go.Scatter(
                x=X_OUTPUT, y=agregado_np,
                mode='lines', fill='tozeroy',
                name='Conjunto Agregado',
                line=dict(color='blue', width=2),
                fillcolor='rgba(0,0,255,0.4)'
            ))

            # --- Línea del centroide ---
            max_height = np.max(agregado_np) if agregado_np.size > 0 else 1.0
            fig.add_trace(go.Scatter(
                x=[float(final_output_val), float(final_output_val)],
                y=[0.0, float(max_height)],
                mode='lines',
                name=f'Centroide: {final_output_val:.2f}',
                line=dict(color='red', dash='solid', width=3)
            ))

        except Exception as e:
            print(f"⚠️ Error en gráfica de defuzzificación: {e}") 
            # Gráfica vacía como fallback
            fig.add_trace(go.Scatter(x=[], y=[], name='Error'))

    else:
        # Si no hay resultado, gráfica vacía
        fig.add_trace(go.Scatter(x=[], y=[], name='Sin datos'))

    # --- Ajustes visuales ---
    fig.update_layout(
        title='Defuzzificación: Conjunto Agregado y Centroide',
        xaxis=dict(title="Salida (0–100)", range=[0, 100]),
        yaxis=dict(title="Grado de pertenencia", range=[0, 1.1]),
        height=400,
        margin=dict(l=40, r=40, t=50, b=40),
        showlegend=True,
        legend=dict(orientation='h', y=-0.3)
    )

    return text_output, style, fig

# --- FUNCIÓN AUXILIAR: Gráfica estilo Toolbox ---
def plot_rule_toolbox(rule, R_val, G_val, B_val, mf_type_selected):
    """Visualización de reglas individuales - CORREGIDA para evitar el amarillo"""
    fig = sp.make_subplots(rows=1, cols=4, subplot_titles=("Rojo", "Verde", "Azul", "Salida"))

    selected_mf = {name: create_mf(mf_type_selected, points, X_COLOR) for name, points in KEY_POINTS.items()}
    crisp_vals = {"Rojo": R_val, "Verde": G_val, "Azul": B_val}

    # Calcular activación
    activacion = min(
        np.interp(R_val, X_COLOR, selected_mf[rule["Rojo"]]),
        np.interp(G_val, X_COLOR, selected_mf[rule["Verde"]]),
        np.interp(B_val, X_COLOR, selected_mf[rule["Azul"]])
    )

    # Colores más apropiados
    color_activation = 'orange'  # En lugar de amarillo brillante
    color_mf = 'blue'
    color_crisp = 'red'
    
    for j, var in enumerate(["Rojo", "Verde", "Azul"], start=1):
        mf_vals = selected_mf[rule[var]]
        crisp = crisp_vals[var]
        
        # MF original
        fig.add_trace(go.Scatter(x=X_COLOR, y=mf_vals, mode="lines", 
                               line=dict(color=color_mf, width=2)), row=1, col=j)
        
        # Línea del valor crisp
        fig.add_trace(go.Scatter(x=[crisp, crisp], y=[0, 1], mode="lines", 
                               line=dict(color=color_crisp, width=2)), row=1, col=j)
        
        # Área de activación (con color más suave)
        mf_recortada = np.minimum(activacion, mf_vals)
        fig.add_trace(go.Scatter(x=X_COLOR, y=mf_recortada, mode="lines", 
                               fill="tozeroy", 
                               line=dict(color=color_activation, width=1),
                               fillcolor='rgba(255,165,0,0.4)'),  # Naranja semitransparente
                     row=1, col=j)

    # Salida
    salida_funcs = get_output_functions(mf_type_selected)
    salida = salida_funcs[rule["OUTPUT"]]
    salida_recortada = np.minimum(activacion, salida)
    
    # MF de salida original
    fig.add_trace(go.Scatter(x=X_OUTPUT, y=salida, mode="lines", 
                           line=dict(color=color_mf, width=2)), row=1, col=4)
    
    # Área de salida activada
    fig.add_trace(go.Scatter(x=X_OUTPUT, y=salida_recortada, mode="lines", 
                           fill="tozeroy", 
                           line=dict(color=color_activation, width=1),
                           fillcolor='rgba(255,165,0,0.4)'), row=1, col=4)

    fig.update_layout(
        height=250, 
        showlegend=False, 
        margin=dict(l=10, r=10, t=30, b=10),
        title_text=f"Regla: R={rule['Rojo']}, G={rule['Verde']}, B={rule['Azul']} → {rule['OUTPUT']}"
    )
    
    return fig

# --- CALLBACK 4: Visualizador de Reglas Estilo Toolbox ---
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
        return [html.Div("⚠️ No se pudo cargar el archivo de reglas.", style={'color': 'red', 'textAlign': 'center'})]

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
