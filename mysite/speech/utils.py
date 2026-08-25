import hashlib

def normalize_text(text: str) -> str:
    return " ".join(text.strip().split())

def text_hash(text: str, model_name: str) -> str:
    n = normalize_text(text)
    key = f"{n}|{model_name}"
    return hashlib.sha256(key.encode('utf-8')).hexdigest()
