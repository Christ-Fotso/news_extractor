import os
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DOTENV_PATH = os.path.join(PROJECT_ROOT, '.env')

load_dotenv(dotenv_path=DOTENV_PATH)

API_KEYS = {}
for i in range(2, 32):
    key_name = f"GOOGLE_API_KEY_{i}"
    API_KEYS[key_name] = os.getenv(key_name)
SOURCES_CONFIG = {
    "JORF": {
        "label": "Journal Officiel (JORF)",
        "types": ["paie", "ccn"]
    },
    "BOCC": {
        "label": "Bulletin Officiel (BOCC)",
        "types": ["ccn"]
    }
}

PROMPT_FILES = {
    "paie": "prompts/paie_prompt.txt",
    "ccn": "prompts/ccn_prompt.txt"
}

if __name__ == '__main__':
    print(f"Chemin racine du projet détecté : {PROJECT_ROOT}")
    print(f"Chemin du fichier .env utilisé : {DOTENV_PATH}")

    print("\n--- Clés API Google chargées (1 à 31) ---")
    keys_found = 0
    keys_missing = 0
    for key_name, key_value in API_KEYS.items():
        if key_value:
            print(f" - {key_name} : Oui (valeur commence par '{key_value[:4]}...')")
            keys_found += 1
        else:
            print(f" - {key_name} : Non (non trouvée dans le fichier .env ou vide)")
            keys_missing += 1

    print(f"\nRésumé : {keys_found} clé(s) trouvée(s), {keys_missing} clé(s) manquante(s).")

    print("\n--- Configuration des sources ---")
    for source, config in SOURCES_CONFIG.items():
        print(f" - {source}: Label='{config['label']}', Types autorisés={config['types']}")

    print("\n--- Configuration des prompts ---")
    for p_type, p_file in PROMPT_FILES.items():
        print(f" - Type '{p_type}': Fichier='{p_file}'")