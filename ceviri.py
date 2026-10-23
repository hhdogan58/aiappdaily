from llm import sohbet_et, json_ayikla
import re

SISTEM = """Sen uzman bir Türkçe teknoloji editörüsün. Sana verilen İngilizce metni analiz edip,
Instagram carousel formatı için Türkçe metinler üreteceksin. 
SADECE istenen JSON formatında cevap ver. Başka hiçbir açıklama yazma."""

ISTEK = """Aşağıdaki haberi oku ve şu JSON formatında Türkçe çıktı ver:
{{
  "baslik": "Haberin çarpıcı ve akıcı Türkçe başlığı (max 90 karakter)",
  "ozet": "Ne olduğunu anlatan ÇOK KAPSAMLI ve DETAYLI bir metin yaz. En az 5-6 paragraf olsun. Konuyu güzelce açıkla, örnekler ver, okuyucunun ilgisini çekecek şekilde doldur.",
  "neden_onemli": "Bu haberin neden önemli olduğunu anlatan 2-3 cümlelik özet.",
  "altbasliklar": ["Slayt 2 için alt başlık", "Slayt 3 için alt başlık", "Slayt 4 için alt başlık", "Slayt 5 için alt başlık"]
}}

Haber Başlığı: {baslik}
Haber Metni: {metin}
"""

def metin_isle(haber):
    metin = haber.get("ozet", "") + " " + haber.get("aciklama", "")
    metin = re.sub(r"<[^>]+>", " ", metin).strip()[:3000]
    
    istek = ISTEK.format(baslik=haber["baslik"], metin=metin)
    cevap = sohbet_et(SISTEM, istek)
    veri = json_ayikla(cevap)
    
    if veri and "baslik" in veri and "ozet" in veri:
        return veri
    return None
