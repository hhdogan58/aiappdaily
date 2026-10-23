@echo off
title appdaily.ai - Otonom Instagram Botu
color 0B

:: ===== BEKLEME SURESI (saniye) =====
:: 3600 = 1 saat, 1800 = 30 dakika, 7200 = 2 saat
set BEKLE=30

:: Bu dosyanin bulundugu klasore git
cd /d "%~dp0"

:dongu
echo ====================================================
echo Bot baslatiliyor: %DATE% - %TIME%
echo ====================================================

:: Sanal ortam (venv) kontrolu. Eger proje klasorunde venv varsa aktif eder.
:: (Senin klasorunde venv yoksa sistem Python'unu kullanir, sorun cikmaz)
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    if exist ..\Scripts\activate.bat (
        call ..\Scripts\activate.bat
    )
)

:: Ana Python dosyasini calistir
python main.py

echo.
echo ====================================================
echo Islem tamamlandi. Sonraki calisma %BEKLE% saniye sonra.
echo CMD penceresini kapatmayin. Kapatmak icin X tusuna basabilirsiniz.
echo ====================================================

:: Belirtilen saniye kadar bekle ve basa don
timeout /t %BEKLE% /nobreak >nul

goto dongu