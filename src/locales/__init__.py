import yaml
import os

LOCALES = {}

def load_all_locales():
    base_path = os.path.dirname(__file__)

    for file in os.listdir(base_path):
        if file.endswith(".yml"):
            lang = file.split(".")[0]
            with open(os.path.join(base_path, file), "r", encoding="utf-8") as f:
                LOCALES[lang] = yaml.safe_load(f)


load_all_locales()

def get_langs(lang: str):
    return LOCALES.get(lang, LOCALES.get("en"))