import os
import argostranslate.package
import argostranslate.translate

# Nom exact du fichier (attention à l'espace entre BIFL et FR)
SOURCE_FILE = "BIFL FR.md"
# Correspondance des langues (Code Argos : Suffixe fichier)
LANGS = {
    'en': 'EN', 'ru': 'RU', 'de': 'DE', 'it': 'IT', 
    'es': 'ES', 'pl': 'PL', 'uk': 'UK', 'ro': 'RO', 'nl': 'NL'
}

def setup_translator(from_code, to_code):
    """Télécharge les packs de langue sur le serveur GitHub"""
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    package_to_install = next(
        filter(lambda x: x.from_code == from_code and x.to_code == to_code, available_packages)
    )
    argostranslate.package.install_from_path(package_to_install.download())

def main():
    if not os.path.exists(SOURCE_FILE):
        print(f"Erreur : {SOURCE_FILE} introuvable.")
        return

    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    if not os.path.exists("content"):
        os.makedirs("content")

    # On traduit tout depuis le Français vers l'Anglais d'abord
    print("--- Installation FR -> EN ---")
    setup_translator("fr", "en")
    en_content = argostranslate.translate.translate(content, "fr", "en")
    
    with open("content/BIFL_EN.md", "w", encoding="utf-8") as f:
        f.write(en_content)
    print("Fichier Anglais OK.")

    # Puis on fait les autres depuis l'Anglais
    for code, suffix in LANGS.items():
        if code == 'en': continue
        print(f"--- Traduction vers {suffix} ---")
        setup_translator("en", code)
        translated = argostranslate.translate.translate(en_content, "en", code)
        
        with open(f"content/BIFL_{suffix}.md", "w", encoding="utf-8") as f:
            f.write(translated)
        print(f"Fichier {suffix} OK.")

if __name__ == "__main__":
    main()
