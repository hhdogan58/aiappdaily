import json
import os
import glob
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from config import ONAY_ISTE, PAYLASILANLAR_DOSYASI
from kaynaklar import hf_makale_haberleri, github_trending_repo_cek
from ceviri import metin_isle
from carousel_generator import carousel_olustur
from sosyal_medya import gorsel_yukle, ig_carousel_paylas

CIKTI_KLASORU = "cikti"

def _link_normalize(url):
    if not url: return ""
    try:
        p = urlparse(url.strip())
        q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if not k.lower().startswith(("utm_", "fbclid", "gclid", "ref", "source", "mc_"))]
        p = p._replace(query=urlencode(q, doseq=True), fragment="")
        return urlunparse(p).rstrip("/")
    except Exception:
        return url.strip()

def eski_gorselleri_temizle():
    silinen = 0
    for dosya in glob.glob(os.path.join(CIKTI_KLASORU, "*.jpg")) + glob.glob("*.jpg"):
        try:
            os.remove(dosya)
            silinen += 1
        except Exception:
            pass
    if silinen > 0:
        print(f"🧹 {silinen} adet eski görsel temizlendi.")

def gecmis_oku():
    if not os.path.exists(PAYLASILANLAR_DOSYASI): return set()
    try:
        with open(PAYLASILANLAR_DOSYASI, "r", encoding="utf-8") as f:
            return {_link_normalize(x) for x in json.load(f) if x}
    except Exception: return set()

def gecmis_yaz(gecmis):
    with open(PAYLASILANLAR_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(sorted(gecmis), f, ensure_ascii=False, indent=0)

def zaten_paylasildi(haber, gecmis):
    adaylar = {_link_normalize(haber.get("id", "")), _link_normalize(haber.get("link", ""))}
    adaylar.discard("")
    return bool(adaylar & gecmis)

def gecmise_ekle(haber, gecmis):
    for anahtar in (_link_normalize(haber.get("id", "")), _link_normalize(haber.get("link", ""))):
        if anahtar: gecmis.add(anahtar)

def icerik_hazirla(haber, metin):
    genel_bilgi = f"{metin['ozet']} {metin['neden_onemli']}".strip()
    altbasliklar = metin.get("altbasliklar", [])
    
    caption = (f"📰 {metin['baslik']}\n\n{metin['ozet']}\n\n💡 {metin['neden_onemli']}\n\n"
               f"🔗 Kaynak: {haber['link']}\n\n#YapayZeka #AI #Teknoloji")
    return {
        "baslik_tr": metin["baslik"],
        "vurgu": metin.get("vurgu"),
        "kategori": "Günün Haberi",
        "chip": metin.get("chip"),
        "altbasliklar": altbasliklar,
        "metin": genel_bilgi,
        "kartlar": metin.get("kartlar"),
        "caption": caption,
    }

def main():
    print("-" * 50)
    print("appdaily.ai Botu Başlatılıyor (Karanlık Tema)...")
    print("-" * 50)

    eski_gorselleri_temizle()
    gecmis = gecmis_oku()
    print(f"📚 Geçmişte {len(gecmis)} kayıt var.")

    haberler = []
    print("🔍 Hugging Face Papers çekiliyor...")
    haberler.extend(hf_makale_haberleri(limit=30))
    
    print("🔍 GitHub Trending çekiliyor...")
    haberler.extend(github_trending_repo_cek(limit=30))

    yeni_haberler = [h for h in haberler if not zaten_paylasildi(h, gecmis)]
    print(f"🆕 {len(yeni_haberler)} yeni içerik bulundu.\n")

    if not yeni_haberler:
        print("✅ Tüm içerikler daha önce paylaşılmış. paylasilanlar.json'u sıfırlayın.")
        return

    for h in yeni_haberler:
        print("=" * 60)
        print(f"📌 İşleniyor: {h['baslik']}")
        print(f"   Kaynak: {h.get('kaynak')}")
        print("=" * 60)

        metin = metin_isle(h)
        if not metin:
            print("❌ LLM metni işleyemedi, atlanıyor.\n")
            continue
            
        icerik = icerik_hazirla(h, metin)

        print("\n" + "=" * 50)
        print("📝 OLUŞTURULACAK GÖRSELLERİN İÇERİĞİ")
        print("=" * 50)
        print(f"Kapak (TR): {icerik['baslik_tr']}")
        print(f"Alt başlıklar: {icerik['altbasliklar']}")
        print(f"Özet Metin: {icerik['metin'][:150]}...")
        print("\n" + "=" * 50)
        print("📝 INSTAGRAM AÇIKLAMASI (CAPTION)")
        print("=" * 50)
        print(icerik["caption"])
        print("=" * 50 + "\n")

        if ONAY_ISTE:
            onay = input("Paylaşılsın mı? (e/a): ")
            if onay.lower() == 'a':
                print("Atlandı.\n")
                continue
            elif onay.lower() != 'e':
                print("Çıkış yapılıyor.")
                break

        print("🎨 Görseller hazırlanıyor...")
        try:
            yollar = carousel_olustur(h, icerik, CIKTI_KLASORU)
        except Exception as e:
            print(f"[HATA] Görsel oluşturulamadı: {e}\n")
            continue

        print("☁️ Görseller ImgBB'ye yükleniyor...")
        urls = [gorsel_yukle(yol) for yol in yollar]
        if None in urls:
            print("[HATA] Görsellerden biri yüklenemedi, atlanıyor.\n")
            continue

        print("🚀 Instagram'a gönderiliyor...")
        basarili = ig_carousel_paylas(urls, icerik["caption"])
        if basarili:
            gecmise_ekle(h, gecmis)
            gecmis_yaz(gecmis)
            print(f"  ✓ Başarıyla paylaşıldı ve geçmişe eklendi.")
        print("-" * 50)

if __name__ == "__main__":
    main()
