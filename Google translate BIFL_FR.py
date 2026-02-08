import re
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from deep_translator import GoogleTranslator

# --- CONFIGURATION ---
SOURCE_FILE = "BIFL_FR.md"  # Se base sur ce fichier uniquement
TARGET_LANGS = {
    'en': 'English', 'ru': 'Russian', 'de': 'German', 'it': 'Italian',
    'es': 'Spanish', 'pl': 'Polish', 'uk': 'Ukrainian', 'ro': 'Romanian', 'nl': 'Dutch'
}
MAX_WORKERS = 10 

def draw_progress_bar(current, total, lang_name):
    width = 30
    percent = float(current) / total
    filled = int(width * percent)
    bar = "█" * filled + "-" * (width - filled)
    sys.stdout.write(f"\r🌍 {lang_name.ljust(10)} |{bar}| {int(percent*100)}% ({current}/{total})")
    sys.stdout.flush()

class MarkdownProtector:
    def __init__(self):
        self.placeholders = []
    def protect(self, text):
        self.placeholders = []
        def url_repl(m):
            idx = len(self.placeholders); self.placeholders.append(m.group(2))
            return f"{m.group(1)}([[{idx}]])"
        text = re.sub(r'(\[.*?\])\((.*?)\)', url_repl, text)
        def bold_repl(m):
            idx = len(self.placeholders); self.placeholders.append("**")
            return f"[[{idx}]]{m.group(1)}[[{idx}]]"
        text = re.sub(r'\*\*(.*?)\*\*', bold_repl, text)
        return text
    def restore(self, text):
        for i, val in enumerate(self.placeholders):
            text = re.sub(rf'\[\[\s*{i}\s*\]\]', val, text)
        return text

def translate_line_indexed(index, line, src, dest):
    if not line.strip() or line.strip() in ['---', '***']:
        return index, line
    protector = MarkdownProtector()
    protected = protector.protect(line)
    try:
        prefix = ""
        hashes = re.match(r'^(#+\s+)', protected)
        if hashes:
            prefix = hashes.group(1); protected = protected[len(prefix):]
        translated = GoogleTranslator(source=src, target=dest).translate(protected)
        return index, protector.restore(prefix + (translated if translated else protected))
    except:
        return index, line

def process_translation(content, src, dest, lang_name):
    lines = content.split('\n')
    total = len(lines)
    results = [None] * total
    completed = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(translate_line_indexed, i, line, src, dest): i for i, line in enumerate(lines)}
        for future in as_completed(futures):
            idx, translated_text = future.result()
            results[idx] = translated_text
            completed += 1
            draw_progress_bar(completed, total, lang_name)
    print()
    return '\n'.join(results)

def main():
    # Automatic detection of the source file
    if not os.path.exists(SOURCE_FILE):
        print(f"❌ Error: {SOURCE_FILE} not found in the current directory.")
        return
    
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        fr_content = f.read()
    
    # Create the output directory if it doesn't exist
    if not os.path.exists("content"):
        os.makedirs("content")

    print(f"--- BIFL Auto-Translator ---")
    
    # 1. English Pivot
    en_content = process_translation(fr_content, 'fr', 'en', "Pivot EN")
    with open("content/BIFL_EN.md", 'w', encoding='utf-8') as f:
        f.write(en_content)

    # 2. Others
    for code, name in TARGET_LANGS.items():
        if code == 'en': continue
        translated = process_translation(en_content, 'en', code, name)
        with open(f"content/BIFL_{code.upper()}.md", 'w', encoding='utf-8') as f:
            f.write(translated)
        time.sleep(1)

    print("\n🎉 DONE! Files are ready in the /content folder.")

if __name__ == "__main__":
    main()
