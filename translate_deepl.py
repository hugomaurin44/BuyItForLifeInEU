import os
import deepl # pip install deepl

# --- CONFIGURATION ---
# On récupère la clé soit depuis les variables d'environnement (GitHub), soit en dur (Test local)
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "TON_API_KEY_DEEPL_ICI")
SOURCE_FILE = "BIFL_EN.md"
TARGET_LANGS = {
    'RU': 'ru', 'DE': 'de', 'FR': 'fr', 'IT': 'it', 
    'ES': 'es', 'PL': 'pl', 'UK': 'uk', 'RO': 'ro', 'NL': 'nl'
}

def translate_guide():
    if not os.path.exists(SOURCE_FILE):
        print(f"❌ Erreur : {SOURCE_FILE} introuvable.")
        return

    translator = deepl.Translator(DEEPL_API_KEY)

    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        source_text = f.read()

    for lang_code, lang_suffix in TARGET_LANGS.items():
        print(f"🚀 Traduction vers {lang_code}...")
        try:
            # L'option magique : tag_handling="markdown"
            result = translator.translate_text(
                source_text, 
                target_lang=lang_code, 
                tag_handling="markdown"
            )
            
            output_path = f"content/BIFL_{lang_code}.md"
            os.makedirs("content", exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result.text)
            print(f"✅ Terminé : {output_path}")
            
        except Exception as e:
            print(f"❌ Erreur pour {lang_code} : {e}")

if __name__ == "__main__":
    translate_guide()
