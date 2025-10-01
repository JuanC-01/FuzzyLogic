import json
import os
from skfuzzy import control as ctrl

# El path base es donde se encuentra este script
RULES_DIR = os.path.join(os.path.dirname(__file__), "rules_data")

def build_rules(json_rules, Rojo, Verde, Azul, Clasificacion):
    """Convierte un diccionario JSON de reglas en objetos ctrl.Rule."""
    rules = []
    
    for rule_data in json_rules:
        # 1. Construir Antecedente (IF)
        try:
            R = Rojo[rule_data['Rojo']]
            G = Verde[rule_data['Verde']]
            B = Azul[rule_data['Azul']]
            antecedent = R & G & B
            
            # 2. Construir Consecuente (THEN)
            consequent = Clasificacion[rule_data['OUTPUT']]
            
            rules.append(ctrl.Rule(antecedent, consequent))
        except KeyError as e:
            # Esto ayuda a depurar si una etiqueta está mal escrita en el JSON
            print(f"⚠️ Error en clave de regla: {e} en la regla {rule_data}")
            continue
            
    return rules

def load_rules_from_file(filename, Rojo, Verde, Azul, Clasificacion):
    """Carga y parsea las reglas de un archivo JSON específico."""
    filepath = os.path.join(RULES_DIR, filename)
    
    if not os.path.exists(filepath):
        print(f"⚠️ Archivo de reglas no encontrado: {filepath}")
        return []

    try:
        with open(filepath, 'r') as f:
            rules_data = json.load(f)
        
        return build_rules(rules_data, Rojo, Verde, Azul, Clasificacion)
        
    except Exception as e:
        print(f"⚠️ Error al cargar o parsear el JSON {filename}: {e}")
        return []