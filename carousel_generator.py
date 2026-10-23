import os
from gorsel_uret import kapak_b, icerik_slayti_gorselli, bilgi_slayti, kapanis_slayti, vurgu_sec
from media_finder import gorselleri_bul, gorsel_indir

def _seed_uret(haber):
    anahtar = str(haber.get("id") or haber.get("baslik") or "x")
    return abs(hash(anahtar)) % 10000

def _gecerli_mi(url, img):
    """Gereksiz logoları ve çok küçük görselleri eler."""
    if not url: return False
    u = url.lower()
    if any(k in u for k in ["logo", "simons", "foundation", "banner", "header", "avatar"]):
        return False
    # Çok küçük görselleri (ikon vb.) ele
    if img.width < 400 or img.height < 250:
        return False
    return True

def _gorselleri_hazirla(haber, adet=8):
    sonuc = []
    gorulen = set()

    # 1. Hugging Face Thumbnail'i (Eğer gerçekten konuyla alakalıysa)
    thumb_url = haber.get("thumbnail")
    if thumb_url:
        img = gorsel_indir(thumb_url)
        if img is not None and _gecerli_mi(thumb_url, img):
            sonuc.append({"img": img, "kaynak": haber.get("kaynak", ""), "url": thumb_url})
            gorulen.add(thumb_url)

    # 2. GitHub Görselleri
    if haber.get("kaynak") == "GitHub Trending" and haber.get("gorseller"):
        for url in haber["gorseller"]:
            if url not in gorulen and len(sonuc) < adet:
                img = gorsel_indir(url)
                if img is not None and _gecerli_mi(url, img):
                    sonuc.append({"img": img, "kaynak": "GitHub", "url": url})
                    gorulen.add(url)

    # 3. Hala eksik varsa MediaFinder ile ara
    if len(sonuc) < adet:
        ek = gorselleri_bul(haber, adet=adet - len(sonuc))
        for g in ek:
            if g["url"] not in gorulen and _gecerli_mi(g["url"], g["img"]):
                sonuc.append(g)
                gorulen.add(g["url"])
                if len(sonuc) >= adet: break

    return sonuc[:adet]

def _metni_parcala(metin, parca_sayisi):
    cumleler = [c.strip() + "." for c in metin.split(".") if c.strip()]
    if not cumleler:
        return [metin] * parca_sayisi
    
    parcalar = []
    parca_basi = 0
    cumle_sayisi = len(cumleler)
    adim = max(1, cumle_sayisi // parca_sayisi)
    
    for i in range(parca_sayisi):
        if i == parca_sayisi - 1:
            parca = " ".join(cumleler[parca_basi:])
        else:
            parca = " ".join(cumleler[parca_basi:parca_basi + adim])
        parcalar.append(parca)
        parca_basi += adim
    return parcalar

def carousel_olustur(haber, icerik, klasor="cikti"):
    os.makedirs(klasor, exist_ok=True)
    
    hedef_slayt = 7 
    icerik_slayt_sayisi = hedef_slayt - 2

    gorseller = _gorselleri_hazirla(haber, adet=icerik_slayt_sayisi)
    
    if not gorseller:
        gorseller = [{"img": None, "kaynak": "Yapay Zeka", "url": ""}]
        
    g1 = gorseller[0]["img"] if len(gorseller) > 0 else None
    kredi = "Kaynak: " + (gorseller[0]["kaynak"] if gorseller else haber.get("kaynak", ""))
    
    seed = _seed_uret(haber)
    kategori = icerik.get("kategori", "Yapay Zeka Haberleri")
    baslik_tr = icerik["baslik_tr"]
    vurgu = icerik.get("vurgu") or vurgu_sec(baslik_tr)
    chip = icerik.get("chip")
    yol = lambda n: os.path.join(klasor, f"slayt_{n}.jpg")

    parcalanmis_metin = _metni_parcala(icerik.get("metin", ""), icerik_slayt_sayisi)
    altbasliklar = icerik.get("altbasliklar", [])
    
    yollar = []
    
    yollar.append(kapak_b(baslik_tr, vurgu, kategori, chip, 1, hedef_slayt, g1, yol(1), seed=seed))
    n = 2

    for i in range(icerik_slayt_sayisi):
        img = gorseller[i+1]["img"] if (i+1) < len(gorseller) else None
        altb = altbasliklar[i] if i < len(altbasliklar) else "Detaylar"
        metin_parcasi = parcalanmis_metin[i] if i < len(parcalanmis_metin) else ""
        
        yollar.append(icerik_slayti_gorselli(
            altb, metin_parcasi, kategori, 
            img, kredi, n, hedef_slayt, yol(n),
            chip=None, seed=seed + i))
        n += 1

    yollar.append(kapanis_slayti(haber.get("baslik", ""), kredi, n, hedef_slayt, yol(n)))
    return yollar

def carousel_paylas(haber, icerik, klasor="cikti"):
    from sosyal_medya import gorsel_yukle, ig_carousel_paylas
    yollar = carousel_olustur(haber, icerik, klasor)
    urller = [gorsel_yukle(y) for y in yollar]
    if not all(urller): return False
    caption = icerik.get("caption") or f"{icerik['baslik_tr']}\n\n{haber.get('link', '')}\n\n#yapayzeka #ai"
    return ig_carousel_paylas(urller, caption)
