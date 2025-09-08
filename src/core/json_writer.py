# /src/core/json_writer.py (Version finale avec réparation)

import json
import os
import re

def _repair_json(faulty_json: str) -> str:

    print("Tentative de réparation du JSON...")
    repaired = faulty_json.strip()


    if repaired.startswith("```json"):
        repaired = repaired[7:]
    if repaired.endswith("```"):
        repaired = repaired[:-3]
    repaired = repaired.strip()
    repaired = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', repaired)

    if not repaired.endswith('"}') and not repaired.endswith('"} ]}'):
        last_valid_char_index = max(repaired.rfind('}'), repaired.rfind(']'))
        if last_valid_char_index != -1:

            repaired = repaired[:last_valid_char_index + 1]

            if repaired.count('[') > repaired.count(']'):
                repaired += ']}'
            elif repaired.count('{') > repaired.count('}'):
                repaired += ']}'

    return repaired


def save_json(data: str, output_path: str):

    try:
        json_data = json.loads(data)
    except json.JSONDecodeError as e:
        print(f"Avertissement : La réponse de l'IA n'est pas un JSON valide. Tentative de réparation. Erreur initiale: {e}")
        repaired_data = _repair_json(data)

        try:
            json_data = json.loads(repaired_data)
            print("Réparation du JSON réussie.")
        except json.JSONDecodeError as final_e:
            print(f"Erreur : La réparation du JSON a échoué. Erreur finale: {final_e}")
            error_path = output_path.replace(".json", "_error.txt")
            with open(error_path, 'w', encoding='utf-8') as f:
                f.write(data) # On sauvegarde la donnée BRUTE originale
            print(f"La réponse brute a été sauvegardée dans : {error_path}")
            return False

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"Fichier JSON sauvegardé avec succès : {output_path}")
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du fichier JSON : {e}")
        return False