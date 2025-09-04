import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import requests
import os
from concurrent.futures import ThreadPoolExecutor

TOKEN = "8271499993:AAHP8Ji5NbXNnqv52EXyie8jFWXZSTNn5iQ"
bot = telebot.TeleBot(TOKEN)

KANAL_ID = -1002448652443
GRUP_ID = -1002283497071

otp = 1907

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI5MDUzMjI2MDA1NDUiLCJsaW5lVHlwZSI6IklORElWSURVQUxfUE9TVFBBSUQiLCJvc1R5cGUiOiJVTktOT1dOIiwibXNpc2RuIjoiOTA1MzIyNjAwNTQ1IiwidHlwZSI6IlBFRVIiLCJleHAiOjE3ODg1NDU3MzUsIm9wZXJhdG9yIjoiVk9EQUZPTkUifQ.w5MH1VxIMuD2786czYc-_cCsz2J-R7tHhBERxQPVyCrqX2hNt0j4KQ-FyAce57oO-2md1GvfSwcXVSMGIdjTHvqgEhF58avyEB3Xpi5K84QMSRNkA4qHNPAC0b0Ehiiagr6XMV_yZgr988cMWRrW9jkYjA3jfms_OD7drmuJUCDpG7ig1bue04uMl_-7_VTrcx5K2iDxd6wYxsSRVnbQsM23diPB8JOGTo-a3mVHToiE7ATt5T_BzgDI7BDZLQZOsC2GbTfCtKZekU0V1fgY7b8h-zfOXGsD6LZeNIVKnSBUmrAAlVHStVqaLGkLUIHbPSZe4PW7-CDHAFc8dpn48g"

KANAL_LINK = "https://t.me/+Z1dFrv0CPilmOWZk"
GRUP_LINK = "https://t.me/+Nz8aUaZeF-E2ZmM0"

ADMIN_ID = 7927763999

USER_DATA_FILE = "users.json"

# Thread havuzu oluştur
# Maksimum 10 eşzamanlı görev çalıştırabilir. Bu değeri ihtiyaca göre ayarlayabilirsiniz.
executor = ThreadPoolExecutor(max_workers=10)

def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

kullanicilar = load_user_data()

def kullanici_kontrol(user_id):
    try:
        kanal = bot.get_chat_member(KANAL_ID, user_id)
        grup = bot.get_chat_member(GRUP_ID, user_id)

        if kanal.status in ["member", "administrator", "creator"] and \
           grup.status in ["member", "administrator", "creator"]:
            return True
        else:
            return False
    except Exception as e:
        print(f"Kanal/Grup kontrol hatası: {e}")
        return False

@bot.message_handler(commands=["start"])
def start_mesaj(m):
    user_id_str = str(m.from_user.id)
    if user_id_str in kullanicilar and kullanicilar[user_id_str].get("status") == "SENT":
        bot.reply_to(m, "❌ Zaten FreeByte hakkınızı kullandınız.")
        return

    if kullanici_kontrol(m.from_user.id):
        msg = bot.reply_to(m, "📱 Telefon numaranı gir (örnek: 5451234567):")
        bot.register_next_step_handler(msg, telefon_al)
    else:
        kontrol_butonu_gonder(m.chat.id)

def kontrol_butonu_gonder(chat_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 Kanala Katıl", url=KANAL_LINK))
    markup.add(InlineKeyboardButton("💬 Gruba Katıl", url=GRUP_LINK))
    markup.add(InlineKeyboardButton("🔄 Kontrol Et", callback_data="kontrol"))
    bot.send_message(
        chat_id,
        "❌ Botu kullanmak için hem **kanala** hem **gruba** katılmalısın!",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "kontrol")
def kontrol_buton(call):
    if kullanici_kontrol(call.from_user.id):
        msg = bot.send_message(call.message.chat.id, "📱 Telefon numaranı gir (örnek: 5451234567):")
        bot.register_next_step_handler(msg, telefon_al)
    else:
        kontrol_butonu_gonder(call.message.chat.id)

def _freebytegonder_task(user_id, no, geciciotpp):
    url = "https://utxk52xqxk.execute-api.eu-west-1.amazonaws.com/beta/transactions"
    
    payload = {
      "amount": "500",
      "toMsisdn": f"90{no}",
      "pinOtp": geciciotpp
    }
    
    headers = {
      'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
      'Accept': "application/json, text/plain, */*",
      'Content-Type': "application/json",
      'sec-ch-ua': "\"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
      'sec-ch-ua-mobile': "?1",
      'authorization': "Bearer " + token,
      'sec-ch-ua-platform': "\"Android\"",
      'origin': "https://www.1gb.app",
      'sec-fetch-site': "cross-site",
      'sec-fetch-mode': "cors",
      'sec-fetch-dest': "empty",
      'referer': "https://www.1gb.app/",
      'accept-language': "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    user_id_str = str(user_id)
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers).json()
        print(f"FreeByte Gönderim Yanıtı: {response}")

        if "transactionId" in response:
            bot.send_message(user_id, "✅ FreeByte başarıyla hattınıza 500 FreeByte gönderildi!\nSahip: @EbediTaht")
            bot.send_message(ADMIN_ID, f"🎉 Kullanıcı {user_id} ({no}) FreeByte gönderimi başarılı! Transaction ID: {response['transactionId']}")
            kullanicilar[user_id_str]["status"] = "SENT"
            save_user_data(kullanicilar)
        elif response.get("code") == "insufficient-balance":
            bot.send_message(user_id, "❌ Maalesef, botun FreeByte gönderme limiti dolmuş. Lütfen daha sonra tekrar deneyin.")
            bot.send_message(ADMIN_ID, f"⚠️ Kullanıcı {user_id} ({no}) için FreeByte gönderme başarısız. Neden: Botun limiti dolmuş.")
        else:
            bot.send_message(user_id, "❌ FreeByte gönderilirken beklenmedik bir hata oluştu. Lütfen tekrar deneyin veya admin ile iletişime geçin.")
            bot.send_message(ADMIN_ID, f"🚨 Kullanıcı {user_id} ({no}) için FreeByte gönderiminde ciddi bir hata oluştu: {response}")
    except requests.exceptions.RequestException as e:
        bot.send_message(user_id, "❌ Sunucuya bağlanırken bir sorun oluştu. Lütfen daha sonra tekrar deneyin.")
        bot.send_message(ADMIN_ID, f"🚨 FreeByte gönderme isteği sırasında ağ hatası oluştu: {e} - Kullanıcı: {user_id} ({no})")
    except json.JSONDecodeError:
        bot.send_message(user_id, "❌ Sunucudan geçersiz bir yanıt alındı. Lütfen daha sonra tekrar deneyin.")
        bot.send_message(ADMIN_ID, f"🚨 FreeByte gönderme isteği sonrası JSON çözümleme hatası: Kullanıcı: {user_id} ({no})")
    except Exception as e:
        bot.send_message(user_id, "❌ Beklenmedik bir hata oluştu. Lütfen daha sonra tekrar deneyin veya admin ile iletişime geçin.")
        bot.send_message(ADMIN_ID, f"🚨 FreeByte gönderme işleminde genel hata: {e} - Kullanıcı: {user_id} ({no})")

def freebytegonder(user_id, no, geciciotpp):
    # İşlemi bir thread havuzuna gönder
    executor.submit(_freebytegonder_task, user_id, no, geciciotpp)

def _geciciotp_task(user_id, no):
    url = "https://3uptzlakwi.execute-api.eu-west-1.amazonaws.com/api/user/pin/get-otp"
    
    payload = {
      "pin": otp
    }
    
    headers = {
      'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
      'Accept': "application/json, text/plain, */*",
      'Content-Type': "application/json",
      'sec-ch-ua': "\"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
      'sec-ch-ua-mobile': "?1",
      'authorization': "Bearer " + token,
      'sec-ch-ua-platform': "\"Android\"",
      'origin': "https://www.1gb.app",
      'sec-fetch-site': "cross-site",
      'sec-fetch-mode': "cors",
      'sec-fetch-dest': "empty",
      'referer': "https://www.1gb.app/",
      'accept-language': "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    user_id_str = str(user_id)
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers).json()
        print(f"OTP Alım Yanıtı: {response}")
        
        if response.get("otp"):
            geciciotpsi = response["otp"]
            print(geciciotpsi)
            # FreeByte gönderme işlemini de ayrı bir thread'de başlat
            freebytegonder(user_id, no, geciciotpsi)
        else:
            print(f"MALESEF FARKLI HATA (OTP): {response}")
            bot.send_message(user_id, "❌ FreeByte gönderilirken bir sorun oluştu. Lütfen tekrar deneyin.")
            bot.send_message(ADMIN_ID, f"🚨 Kullanıcı {user_id} ({no}) için OTP alımında hata oluştu: {response}")
            if user_id_str in kullanicilar:
                del kullanicilar[user_id_str]
                save_user_data(kullanicilar)
            
    except requests.exceptions.RequestException as e:
        bot.send_message(user_id, "❌ Sunucuya bağlanırken bir sorun oluştu. Lütfen daha sonra tekrar deneyin.")
        bot.send_message(ADMIN_ID, f"🚨 OTP alım isteği sırasında ağ hatası oluştu: {e} - Kullanıcı: {user_id} ({no})")
        if user_id_str in kullanicilar:
            del kullanicilar[user_id_str]
            save_user_data(kullanicilar)
    except json.JSONDecodeError:
        bot.send_message(user_id, "❌ Sunucudan geçersiz bir yanıt alındı. Lütfen daha sonra tekrar deneyin.")
        bot.send_message(ADMIN_ID, f"🚨 OTP alım isteği sonrası JSON çözümleme hatası: Kullanıcı: {user_id} ({no})")
        if user_id_str in kullanicilar:
            del kullanicilar[user_id_str]
            save_user_data(kullanicilar)
    except Exception as e:
        bot.send_message(user_id, "❌ Beklenmedik bir hata oluştu. Lütfen daha sonra tekrar deneyin.")
        bot.send_message(ADMIN_ID, f"🚨 OTP alım işleminde genel hata: {e} - Kullanıcı: {user_id} ({no})")
        if user_id_str in kullanicilar:
            del kullanicilar[user_id_str]
            save_user_data(kullanicilar)

def geciciotp(user_id, no):
    # İşlemi bir thread havuzuna gönder
    executor.submit(_geciciotp_task, user_id, no)


def telefon_al(m):
    user_id = m.from_user.id
    tel = m.text.strip()
    user_id_str = str(user_id)

    if not tel.isdigit() or len(tel) != 10 or tel.startswith("90") or tel.startswith("+"):
        msg = bot.reply_to(m, "❌ Geçersiz numara! Sadece 10 haneli gir (örnek: 5451234567):")
        bot.register_next_step_handler(msg, telefon_al)
        return

    # Kullanıcıyı PENDING statüsünde kaydet ve kaydet
    kullanicilar[user_id_str] = {"telefon": tel, "status": "PENDING"}
    save_user_data(kullanicilar)
    bot.reply_to(m, f"✅ Numaran kaydedildi: {tel}. FreeByte gönderiliyor...")

    # Uzun sürebilecek OTP alma işlemini ayrı bir thread'de başlat
    geciciotp(user_id, tel)

@bot.message_handler(commands=["panel"])
def admin_panel(m):
    if m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "❌ Bu komutu sadece admin kullanabilir!")
        return

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("👥 Kayıtlı Kullanıcı Sayısı", callback_data="say"))
    markup.add(InlineKeyboardButton("📂 Kullanıcı Listesi", callback_data="liste"))

    bot.send_message(m.chat.id, "🔐 Admin Paneli:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["say", "liste"])
def admin_islemleri(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Yetkin yok!")
        return

    if call.data == "say":
        sent_users_count = sum(1 for user_data in kullanicilar.values() if user_data.get("status") == "SENT")
        bot.send_message(call.message.chat.id, f"👥 Toplam FreeByte alan kullanıcı: {sent_users_count}")
    elif call.data == "liste":
        if kullanicilar:
            text = "📂 Kayıtlı Kullanıcılar:\n"
            for uid_str, user_data in kullanicilar.items():
                telefon = user_data.get("telefon", "Bilinmiyor")
                status = user_data.get("status", "Bilinmiyor")
                text += f"• ID: {uid_str} | Tel: {telefon} | Durum: {status}\n"
            bot.send_message(call.message.chat.id, text)
        else:
            bot.send_message(call.message.chat.id, "📂 Henüz kullanıcı yok.")

print("Bot çalışıyor...")
bot.infinity_polling()
