import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance, ImageChops

W, H = 1080, 1350
KENAR = 80
BEYAZ = (255, 255, 255)
METIN = (210, 210, 210) 
GRI = (130, 130, 130)
TURUNCU = (247, 135, 10) 
HESAP = "@appdaily.ai"
FONT_DIR = os.path.dirname(os.path.abspath(__file__))

PANEL_X, PANEL_W = KENAR, W - 2 * KENAR
RADIUS = 24

def font_yukle(boyut, stil="bold"):
    adaylar = {
        "bold": ["Poppins-Bold.ttf", "DejaVuSans-Bold.ttf"],
        "regular": ["Poppins-Regular.ttf", "DejaVuSans.ttf"],
    }[stil]
    for ad in adaylar:
        for yol in (os.path.join(FONT_DIR, ad), ad):
            try:
                return ImageFont.truetype(yol, boyut)
            except OSError:
                pass
    try:
        return ImageFont.load_default(boyut)
    except TypeError:
        return ImageFont.load_default()

def tr_lower(s):
    return s.replace("İ", "i").replace("I", "ı").lower()

def vurgu_sec(baslik):
    kel = baslik.split()
    for k in kel:
        if any(c.isdigit() for c in k) or "$" in k:
            return [k]
    return [max(kel, key=len)] if kel else []

def gradyan(w, h, c1, c2):
    # Zifiri siyah tema
    return Image.new("RGB", (w, h), (5, 5, 5))

def isik(img, cx, cy, r, renk, alpha):
    # Siyah temada arkada hafif ışıklandırma
    kap = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(kap).ellipse([cx - r, cy - r, cx + r, cy + r], fill=renk + (alpha,))
    kap = kap.filter(ImageFilter.GaussianBlur(r // 2))
    return Image.alpha_composite(img.convert("RGBA"), kap).convert("RGB")

def cam(img, kutu, radius=20, alpha=15, cizgi=40):
    kap = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(kap).rounded_rectangle(
        kutu, radius=radius, fill=(255, 255, 255, alpha), outline=(255, 255, 255, cizgi), width=1)
    return Image.alpha_composite(img.convert("RGBA"), kap).convert("RGB")

def arka_kapak():
    img = gradyan(W, H, (0, 0, 0), (0, 0, 0))
    return isik(img, 900, 200, 400, (50, 50, 50), 20)

def arka_ic():
    img = gradyan(W, H, (0, 0, 0), (0, 0, 0))
    return isik(img, 800, 300, 500, (40, 40, 40), 15)

def satirlara_bol(draw, metin, font, max_genislik):
    satirlar, satir = [], ""
    for kelime in metin.split():
        deneme = f"{satir} {kelime}".strip()
        if draw.textlength(deneme, font=font) <= max_genislik:
            satir = deneme
        else:
            if satir:
                satirlar.append(satir)
            satir = kelime
    if satir:
        satirlar.append(satir)
    return satirlar

def metin_sigdir(draw, metin, boyutlar, max_w, max_h, kat=1.4, stil="regular"):
    for b in boyutlar:
        f = font_yukle(b, stil)
        sat = satirlara_bol(draw, metin, f, max_w)
        if len(sat) * int(b * kat) <= max_h:
            return f, sat, int(b * kat)
    lh = int(b * kat)
    mx = max(1, max_h // lh)
    sat = sat[:mx]
    sat[-1] = sat[-1].rstrip(" .,;") + "…"
    return f, sat, lh

def baslik_ciz(draw, metin, vurgu, x, y, max_w, max_h, boyutlar=range(88, 43, -2), max_satir=4, kat=1.16):
    kelimeler = metin.split()
    vset = {tr_lower(p) for v in vurgu for p in v.split()}
    for b in boyutlar:
        f = font_yukle(b, "bold")
        satirlar, sat = [], []
        for k in kelimeler:
            if sat and draw.textlength(" ".join(sat + [k]), font=f) > max_w:
                satirlar.append(sat)
                sat = [k]
            else:
                sat.append(k)
        if sat:
            satirlar.append(sat)
        if len(satirlar) <= max_satir and len(satirlar) * int(b * kat) <= max_h:
            break
    lh = int(b * kat)
    for s in satirlar:
        cx = x
        for k in s:
            temiz = tr_lower(k.strip(".,:;!?\"'()“”’"))
            draw.text((cx, y), k, font=f, fill=TURUNCU if temiz in vset else BEYAZ)
            cx += draw.textlength(k + " ", font=f)
        y += lh
    return y

def panel_hazirla(kaynak, w, h):
    img = kaynak.convert("RGB")
    oran_p, oran_g = w / h, img.width / img.height
    if abs(oran_g / oran_p - 1) < 0.18:
        return ImageOps.fit(img, (w, h), Image.LANCZOS)
    arka = ImageOps.fit(img, (w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(35))
    arka = ImageEnhance.Brightness(arka).enhance(0.3) 
    on = ImageOps.contain(img, (w - 40, h - 40), Image.LANCZOS)
    arka.paste(on, ((w - on.width) // 2, (h - on.height) // 2))
    return arka

def yedek_panel(w, h, seed=11):
    rnd = random.Random(seed)
    # Zifiri siyah yedek panel
    img = gradyan(w, h, (0, 0, 0), (0, 0, 0))
    d = ImageDraw.Draw(img)
    for x in range(0, w, 60):
        d.line([(x, 0), (x, h)], fill=(20, 20, 20), width=1)
    for y in range(0, h, 60):
        d.line([(0, y), (w, y)], fill=(20, 20, 20), width=1)

    n = 12
    bw = int((w - 100) / n * 0.62)
    adim = (w - 100) / n
    tepe = []
    for i in range(n):
        yuk = int(h * (0.12 + 0.62 * (i / (n - 1))) + rnd.randint(-18, 18))
        x0 = int(50 + i * adim)
        d.rounded_rectangle([x0, h - 30 - yuk, x0 + bw, h - 30], radius=4, fill=(50, 50, 50))
        tepe.append((x0 + bw // 2, h - 30 - yuk - 14))
    
    d.line(tepe, fill=TURUNCU, width=4, joint="curve")
    ex, ey = tepe[-1]
    d.ellipse([ex - 8, ey - 8, ex + 8, ey + 8], fill=TURUNCU, outline=BEYAZ, width=2)
    return img

def panel_koy(image, gorsel, y, h, chip=None, seed=None):
    if gorsel is not None:
        ic = panel_hazirla(gorsel, PANEL_W, h)
    else:
        if seed is None: seed = random.randint(0, 99999)
        ic = yedek_panel(PANEL_W, h, seed)

    maske = Image.new("L", (PANEL_W, h), 0)
    ImageDraw.Draw(maske).rounded_rectangle([0, 0, PANEL_W - 1, h - 1], radius=RADIUS, fill=255)
    image.paste(ic, (PANEL_X, y), maske)
    ImageDraw.Draw(image).rounded_rectangle(
        [PANEL_X, y, PANEL_X + PANEL_W, y + h], radius=RADIUS, outline=(40, 40, 40), width=1)
    
    if chip:
        f = font_yukle(34, "bold")
        tw = ImageDraw.Draw(image).textlength(chip, font=f)
        kutu = [PANEL_X + 30, y + h - 100, PANEL_X + 30 + tw + 60, y + h - 30]
        image = cam(image, kutu, radius=15, alpha=30, cizgi=60)
        ImageDraw.Draw(image).text((kutu[0] + 30, kutu[1] + 14), chip, font=f, fill=BEYAZ)
    return image

def alt_bar(image, sira, toplam, kredi=None):
    d = ImageDraw.Draw(image)
    d.text((KENAR, 1250), HESAP, font=font_yukle(34, "bold"), fill=BEYAZ)
    if kredi:
        f = font_yukle(24, "regular")
        d.text((W - KENAR - d.textlength(kredi, font=f), 1258), kredi, font=f, fill=GRI)
        return
    pill_w, r, bosluk = 46, 5, 12
    toplam_w = pill_w + (toplam - 1) * (2 * r + bosluk) + bosluk
    x = W - KENAR - toplam_w
    cy = 1274
    for i in range(toplam):
        if i == sira - 1:
            d.rounded_rectangle([x, cy - r, x + pill_w, cy + r], radius=r, fill=TURUNCU)
            x += pill_w + bosluk
        else:
            d.ellipse([x, cy - r, x + 2 * r, cy + r], fill=(60, 60, 60))
            x += 2 * r + bosluk

def ust_bar(image, kategori, sira, toplam):
    d = ImageDraw.Draw(image)
    f = font_yukle(24, "bold")
    tw = d.textlength(kategori.upper(), font=f)
    
    image = cam(image, [KENAR, 80, KENAR + 52 + tw + 30, 132], radius=15, alpha=20, cizgi=50)
    d = ImageDraw.Draw(image)
    d.ellipse([KENAR + 22, 98, KENAR + 36, 112], fill=TURUNCU)
    d.text((KENAR + 52, 94), kategori.upper(), font=f, fill=BEYAZ)
    
    if sira:
        s = f"{sira}/{toplam}"
        fs = font_yukle(24, "bold")
        sw = d.textlength(s, font=fs)
        image = cam(image, [W - KENAR - sw - 50, 80, W - KENAR, 132], radius=15, alpha=20, cizgi=50)
        ImageDraw.Draw(image).text((W - KENAR - sw - 25, 94), s, font=fs, fill=BEYAZ)
    return image

def kaydet(image, yol):
    image.convert("RGB").save(yol, quality=95)
    return yol

def kapak_b(baslik_tr, vurgu, kategori, chip, sira, toplam, gorsel, yol, seed=11):
    image = arka_kapak()
    image = ust_bar(image, kategori, None, toplam)
    d = ImageDraw.Draw(image)
    baslik_ciz(d, baslik_tr, vurgu or vurgu_sec(baslik_tr), KENAR, 200, W - 2 * KENAR, 400, max_satir=3)
    image = panel_koy(image, gorsel, 620, 520, chip=chip, seed=seed)
    alt_bar(image, sira, toplam)
    return kaydet(image, yol)

def icerik_slayti_gorselli(altbaslik, metin, kategori, gorsel, kredi, sira, toplam, yol, chip=None, seed=22):
    image = arka_ic()
    image = ust_bar(image, kategori, sira, toplam)
    d = ImageDraw.Draw(image)
    
    y = baslik_ciz(d, altbaslik, [], KENAR, 180, W - 2 * KENAR, 200, boyutlar=range(64, 43, -2), max_satir=2, kat=1.18)
    d.line([(KENAR, y + 15), (KENAR + 60, y + 15)], fill=TURUNCU, width=4)
    
    govde_y = y + 50
    
    if gorsel is not None:
        f, satirlar, lh = metin_sigdir(d, metin, range(38, 28, -2), W - 2 * KENAR, 600 - govde_y)
        for s in satirlar:
            d.text((KENAR, govde_y), s, font=f, fill=METIN)
            govde_y += lh
        image = panel_koy(image, gorsel, 700, 460, chip=chip, seed=seed)
    else:
        f, satirlar, lh = metin_sigdir(d, metin, range(48, 32, -2), W - 2 * KENAR, 1050 - govde_y, kat=1.5)
        for s in satirlar:
            d.text((KENAR, govde_y), s, font=f, fill=METIN)
            govde_y += lh
            
    alt_bar(image, sira, toplam, kredi=kredi)
    return kaydet(image, yol)

def bilgi_slayti(baslik, kartlar, kategori, sira, toplam, yol):
    image = arka_ic()
    image = ust_bar(image, kategori, sira, toplam)
    d = ImageDraw.Draw(image)
    
    y = baslik_ciz(d, baslik, [], KENAR, 180, W - 2 * KENAR, 200, boyutlar=range(60, 39, -2), max_satir=2, kat=1.18)
    
    kartlar = kartlar[:3]
    ust, bosluk = max(y + 40, 320), 24
    kh = int((1190 - ust - bosluk * (len(kartlar) - 1)) / max(1, len(kartlar)))
    kh = min(kh, 260)
    
    for i, (buyuk, kucuk) in enumerate(kartlar):
        ky = ust + i * (kh + bosluk)
        image = cam(image, [KENAR, ky, W - KENAR, ky + kh], radius=20, alpha=15, cizgi=50)
        d = ImageDraw.Draw(image)
        for b in range(90, 39, -4):
            fb = font_yukle(b, "bold")
            if d.textlength(buyuk, font=fb) <= W - 2 * KENAR - 80: break
        d.text((KENAR + 40, ky + 25), buyuk, font=fb, fill=TURUNCU)
        fk, sat, lh = metin_sigdir(d, kucuk, range(30, 23, -2), W - 2 * KENAR - 80, kh - 28 - int(b * 1.25) - 20, kat=1.35)
        yy = ky + 25 + int(b * 1.25)
        for s in sat:
            d.text((KENAR + 40, yy), s, font=fk, fill=METIN)
            yy += lh
            
    alt_bar(image, sira, toplam)
    return kaydet(image, yol)

def kapanis_slayti(baslik_en, kredi, sira, toplam, yol):
    image = arka_ic()
    image = ust_bar(image, "Kaynak", sira, toplam)
    d = ImageDraw.Draw(image)
    
    f, sat, lh = metin_sigdir(d, baslik_en, range(40, 29, -2), W - 2 * KENAR - 80, 300, kat=1.28, stil="bold")
    kh = 100 + len(sat) * lh
    image = cam(image, [KENAR, 200, W - KENAR, 200 + kh], radius=20, alpha=20, cizgi=50)
    d = ImageDraw.Draw(image)
    d.text((KENAR + 40, 230), "ORİJİNAL BAŞLIK", font=font_yukle(20, "bold"), fill=GRI)
    yy = 270
    for s in sat:
        d.text((KENAR + 40, yy), s, font=f, fill=BEYAZ)
        yy += lh
    d.text((KENAR, 200 + kh + 30), kredi, font=font_yukle(28, "regular"), fill=GRI)

    d.text((KENAR, 750), "Her gün yapay zekâ", font=font_yukle(64, "bold"), fill=BEYAZ)
    d.text((KENAR, 830), "haberleri için", font=font_yukle(64, "bold"), fill=BEYAZ)
    d.text((KENAR, 910), "takip et", font=font_yukle(64, "bold"), fill=TURUNCU)
    
    d.line([(KENAR, 1020), (KENAR + 60, 1020)], fill=TURUNCU, width=4)
    d.text((KENAR, 1060), "Kaydet  •  Paylaş  •  Takip et", font=font_yukle(30, "regular"), fill=METIN)
    
    alt_bar(image, sira, toplam)
    return kaydet(image, yol)
