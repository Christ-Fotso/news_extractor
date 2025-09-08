import google.generativeai as genai
import os
import json
import re

from src.config.config import API_KEYS, PROMPT_FILES

SRC_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class AIExtractor:
    def __init__(self):

        self.valid_api_keys = [key for key in API_KEYS.values() if key]


        if not self.valid_api_keys:
            raise ValueError("Aucune clé API Google valide n'a été trouvée dans le fichier .env. Veuillez vérifier la configuration.")

        print(f"{len(self.valid_api_keys)} clé(s) API valide(s) ont été chargées.")


        self.current_key_index = 0

        self.model = None
        self._configure_genai()

    def _configure_genai(self):

        current_api_key = self.valid_api_keys[self.current_key_index]
        genai.configure(api_key=current_api_key)

        generation_config = {
            "temperature": 0.1,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 500000,
        }
        safety_settings = [
        ]
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        print(f"Modèle GenAI configuré avec la clé n°{self.current_key_index + 1}.")

    def _rotate_key(self):

        self.current_key_index = (self.current_key_index + 1) % len(self.valid_api_keys)
        print(f"Passage à la clé API n°{self.current_key_index + 1}...")
        self._configure_genai()


    def _load_prompt(self, prompt_type: str) -> str:
        prompt_path = os.path.join(SRC_ROOT, PROMPT_FILES[prompt_type])
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _repair_json(self, faulty_json: str) -> str:
        print("Tentative de réparation du JSON...")
        repaired = faulty_json.strip()
        if repaired.startswith("```json"):
            repaired = repaired[7:]
        if repaired.endswith("```"):
            repaired = repaired[:-3]
        repaired = repaired.strip()
        last_brace = repaired.rfind('}')
        last_bracket = repaired.rfind(']')

        if last_bracket > last_brace:
            repaired = repaired[:last_bracket+1] + ']}'
        elif last_brace > -1:
            repaired = repaired[:last_brace+1] + ']}'
        repaired = re.sub(r'(?<!\\)(?<![,\{\[\s:])"(?![:,\]\}\s])', r'\"', repaired)
        repaired = re.sub(r'[\x00-\x1f]', lambda m: '\\n' if m.group(0) == '\n' else '', repaired)

        return repaired

    def extract(self, text_content: str, extraction_type: str) -> str:
        if hasattr(self, '_call_count'):
            self._rotate_key()
        else:
            self._call_count = 1

        prompt = self._load_prompt(extraction_type)
        full_prompt = f"{prompt}\n\n### CONTENU DU DOCUMENT À ANALYSER ###\n\n{text_content}"

        print(f"Envoi de la requête à l'IA pour l'extraction '{extraction_type}'...")
        try:
            response = self.model.generate_content(full_prompt)
            print("Réponse de l'IA reçue.")
            raw_response = response.text

            return raw_response

        except Exception as e:
            print(f"Erreur lors de l'appel à l'API Google AI : {e}")
            return f'{{"error": "Une erreur est survenue lors de la communication avec l\'API AI: {e}"}}'