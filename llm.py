import json
import re
import requests
from config import LLM_URL, LLM_MODEL

def sohbet_et(sistem_mesaji, kullanici_mesaji, sicaklik=0.2, max_token=1500):
    url = f"{LLM_URL}/chat/completions"
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": sistem_mesaji},
            {"role": "user", "content": kullanici_mesaji}
        ],
        "temperature": sicaklik,
        "max_tokens": max_token
    }
    try:
        r = requests.post(url, json=payload, timeout=120)
        r.raise_for_status()
        icerik = r.json()["choices"][0]["message"]["content"]
        # Qwen bazen <think> etiketi basabilir, temizleyelim
        icerik = re.sub(r"<think>.*?</think>", "", icerik, flags=re.S)
        icerik = re.sub(r"<think>.*", "", icerik, flags=re.S)
        return icerik.strip()
    except Exception as e:
        print(f"[HATA] LLM bağlantısı başarısız: {e}")
        return ""

def json_ayikla(metin):
    """LLM'in döndürdüğü metinden JSON objesini cımbızla çeker."""
    bas, son = metin.find("{"), metin.rfind("}")
    if bas != -1 and son > bas:
        try:
            return json.loads(metin[bas:son+1])
        except json.JSONDecodeError:
            pass
    return None