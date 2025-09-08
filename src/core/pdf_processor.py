import PyPDF2
import re

def clean_text(text: str) -> str:


    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned

def extract_text_from_pdf(pdf_path: str) -> str:

    raw_text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            print(f"Lecture de {len(reader.pages)} pages du PDF...")
            for page in reader.pages:
                raw_text += page.extract_text() or ""

        print("Nettoyage du texte extrait...")

        cleaned_text = clean_text(raw_text)

        print("Extraction du texte terminée.")
        return cleaned_text
    except Exception as e:
        print(f"Erreur lors de la lecture du PDF : {e}")
        return ""