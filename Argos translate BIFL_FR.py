import os
import re
import sys
import argostranslate.package
import argostranslate.translate

# --- CONFIGURATION ---
SOURCE_FILE = "BIFL_FR.md"
# Argos passe par l'anglais pour la plupart des langues
TARGET_LANGS = {
    'en': 'EN', # Pivot
    'de': 'DE', 'es': 'ES', 'it': 'IT', 'nl': 'NL', 
    'pl': 'PL', 'ro': 'RO', 'ru': 'RU' 
    # Note: L'Ukrainien (UK) est parfois mal supporté par Argos basique, 
    # je l'ai retiré pour la stabilité, mais on peut tester 'uk'.
}

def install_languages():
    """Télécharge les modèles de langue nécessaires."""
    print("📦 Mise à jour de l'index Argos...")
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()

    # Liste des paires à installer (FR->EN, puis EN->Autres)
    pairs_to_install = [('fr', 'en')]
    for code in TARGET_LANGS.keys():
        if code != 'en':
            pairs_to_install.append(('en', code))

    for from_code, to_code in pairs_to_install:
        # Vérifie si déjà installé
        installed = argostranslate.package.get_installed_packages()
        if any(p.from_code == from_code and p.to_code == to_code for p in installed):
            print(f"  - {from_code}->{to_code} déjà installé.")
            continue

        # Sinon on installe
        try:
            package = next(filter(
                lambda x: x.from_code == from_code and x.to_code == to_code, 
                available_packages
            ))
            print(f"  - Téléchargement {from_code}->{to_code}...")
            argostranslate.package.install_from_path(package.download())
        except StopIteration:
            print(f"⚠️  Pas de modèle trouvé pour {from_code}->{to_code}")

# --- PROTECTION DU MARKDOWN ---
class MarkdownProtector:
    def __init__(self):
        self.placeholders = []

    def protect(self, text):
        self.placeholders = []
        
        # 1. Protéger les liens complets [texte](url) -> préserver l'URL
        # On ne traduit que le texte entre crochets, on cache l'URL
        def link_repl(m):
            # m.group(1) = texte, m.group(2) = url
            # On ne protège que l'URL pour l'instant pour laisser le texte être traduit
            idx = len(self.placeholders)
            self.placeholders.append(m.group(2))
            return f"[{m.group(1)}]([[URL_{idx}]])"
        
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link_repl, text)

        # 2. Protéger les indicateurs spéciaux BIFL ($$ | ★★★)
        # On remplace tout ce qui est entre pipes par des tokens si c'est des symboles
        def symbol_repl(m):
            idx = len(self.placeholders)
            self.placeholders.append(m.group(0))
            return f" [[SYM_{idx}]] "
        
        # Protège les séquences d'étoiles ou dollars
        text = re.sub(r'(\$\+|★+|☆+|⚠️)', symbol_repl, text)

        return text

    def restore(self, text):
        # Restauration inverse
        for i, val in enumerate(self.placeholders):
            # Restauration URL
            text = re.sub(rf'\[\[URL_{i}\]\]', val, text)
            # Restauration Symboles (avec tolérance sur les espaces ajoutés par l'IA)
            text = re.sub(rf'\[\[\s*SYM_{i}\s*\]\]', val, text)
        return text

def translate_file(content, from_code, to_code):
    protector = MarkdownProtector()
    
    # On découpe par ligne pour éviter que l'IA ne mélange tout le document
    lines = content.split('\n')
    translated_lines = []

    # Chargement du modèle
    try:
        t = argostranslate.translate.get_translation_from_codes(from_code, to_code)
    except Exception as e:
        print(f"❌ Erreur chargement modèle {from_code}->{to_code}: {e}")
        return content # On renvoie l'original si échec

    print(f"🚀 Traduction {from_code} -> {to_code} en cours...")
    
    for line in lines:
        if not line.strip() or line.startswith('---') or line.startswith('|'):
            # On ne traduit pas les séparateurs ou les lignes vides
            # ATTENTION : On garde les lignes de tableau (|) brutes pour ne pas casser la structure
            # Si tu veux traduire le contenu des tableaux, retire "line.startswith('|')"
            translated_lines.append(line)
            continue

        # Protection
        protected_line = protector.protect(line)
        
        # Traduction
        try:
            trans = t.translate(protected_line)
            # Restauration
            final = protector.restore(trans)
            translated_lines.append(final)
        except:
            translated_lines.append(line)

    return '\n'.join(translated_lines)

def main():
    if not os.path.exists(SOURCE_FILE):
        print(f"❌ {SOURCE_FILE} introuvable.")
        sys.exit(1)

    # 1. Installation des langues
    install_languages()

    # 2. Lecture source
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        fr_content = f.read()

    # 3. Pivot : FR -> EN
    print("\n--- Génération du Pivot (Anglais) ---")
    en_content = translate_file(fr_content, 'fr', 'en')
    
    if not os.path.exists("content"):
        os.makedirs("content")
        
    with open("content/BIFL_EN.md", "w", encoding="utf-8") as f:
        f.write(en_content)

    # 4. Traduction des autres langues depuis l'Anglais
    for code, suffix in TARGET_LANGS.items():
        if code == 'en': continue
        
        print(f"\n--- Génération {suffix} ({code}) ---")
        # On utilise le contenu anglais comme source
        translated_content = translate_file(en_content, 'en', code)
        
        filename = f"content/BIFL_{suffix}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(translated_content)
            
    print("\n✅ Terminé ! Tous les fichiers sont générés.")

if __name__ == "__main__":
    main()
