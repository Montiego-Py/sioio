import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import requests
import os
from concurrent.futures import ThreadPoolExecutor
import threading
import traceback

# ---------------- CONFIG ----------------
TOKEN = "8271499993:AAHP8Ji5NbXNnqv52EXyie8jFWXZSTNn5iQ"
bot = telebot.TeleBot(TOKEN, parse_mode=None)

KANAL_ID = -1002448652443
GRUP_ID = -1002283497071

# API / OTP
otp = 1907
token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI5MDUzODg0MDQ1MjAiLCJsaW5lVHlwZSI6IklORElWSURVQUxfUE9TVFBBSUQiLCJvc1R5cGUiOiJVTktOT1dOIiwibXNpc2RuIjoiOTA1Mzg4NDA0NTIwIiwidHlwZSI6IlBFRVIiLCJleHAiOjE3ODkzMTczODQsIm9wZXJhdG9yIjoiVFVSS0NFTEwifQ.XPGXhU1rSk9MDaXWIRDxloeWaWjxiBnOH1HKAhO8VfSLlpSD3x6KDdwuvgTrw2SVoCcNQAWqSurP9ipVl4EwhUrUZRFOgUCg4B_CwCOkgQCdq_5i94sRJOdK_Yh0axZoMkdciL9HFp4Dr_nyHaBnhVedFNo_ZGUBo-QZfRZ8qERNSKLkhYrUAdngrNSfK4qSLBQ0caDKQM0g9Iw2MJcaLZWHnRxOio3H5ZhzxCCT5pPgu4j2O1zlvh8SnbBPGaQW75X2peCXdhILKto_3i79_H18ZIIohBZJdD3oWKA_tI0wVvP3hbwWSFVQGu6IwbbuQDiVceSZ-xp8zKSwQi9w8g"

KANAL_LINK = "https://t.me/+Z1dFrv0CPilmOWZk"
GRUP_LINK = "https://t.me/+Nz8aUaZeF-E2ZmM0"

ADMIN_ID = 7927763999

USER_DATA_FILE = "userrs.json"

executor = ThreadPoolExecutor(max_workers=10)

# ---------- concurrency helpers ----------
user_locks = {}
user_locks_lock = threading.Lock()


def get_user_lock(user_id_str):
    with user_locks_lock:
        if user_id_str not in user_locks:
            user_locks[user_id_str] = threading.Lock()
        return user_locks[user_id_str]


# ---------- persist helpers ----------
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_user_data(data):
    try:
        with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print("Kullanıcı verisi kaydedilemedi:", e)


kullanicilar = load_user_data()  # keys are strings


# ---------- membership check ----------
def kullanici_kontrol(user_id):
    try:
        # bot.get_chat_member accepts numeric chat id or username
        kanal = bot.get_chat_member(KANAL_ID, user_id)
        grup = bot.get_chat_member(GRUP_ID, user_id)
        kanal_ok = kanal.status in ["member", "administrator", "creator"]
        grup_ok = grup.status in ["member", "administrator", "creator"]
        return kanal_ok and grup_ok
    except Exception as e:
        # Hata: örn. bot admin değil, veya kullanıcı yoksa
        print("kullanici_kontrol hata:", e)
        return False


# ---------- UI: kontrol butonu ----------
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


# ---------- /start ----------
@bot.message_handler(commands=["start"], chat_types=['private'])
def start_mesaj(m):
    user_id = m.from_user.id
    user_id_str = str(user_id)
    lock = get_user_lock(user_id_str)

    with lock:
        current = kullanicilar.get(user_id_str, {})
        status = current.get("status")

        if status == "SENT":
            bot.reply_to(m, "❌ Kullanım limitin doldu. Tekrar kullanamazsın.")
            return
        if status == "PENDING":
            bot.reply_to(m, "⏳ İşleminiz sürüyor. Lütfen bekleyin.")
            return
        if status == "AWAITING_PHONE":
            bot.reply_to(m, "📱 Önceki isteğiniz tamamlanmadı. Lütfen telefon numaranızı gönderin.")
            return

        # membership kontrol
        if kullanici_kontrol(user_id):
            kullanicilar[user_id_str] = {"status": "AWAITING_PHONE"}
            save_user_data(kullanicilar)
            bot.send_message(user_id, "📱 Telefon numaranı gir (örnek: 5451234567):")
            # artık mesajları global handler ile yakalayacağız
        else:
            kontrol_butonu_gonder(m.chat.id)


# ---------- callback (kontrol butonu) ----------
@bot.callback_query_handler(func=lambda call: call.data == "kontrol")
def kontrol_buton(call):
    user_id = call.from_user.id
    user_id_str = str(user_id)
    lock = get_user_lock(user_id_str)

    with lock:
        current = kullanicilar.get(user_id_str, {})
        status = current.get("status")

        if status == "SENT":
            bot.answer_callback_query(call.id, "❌ Kullanım limitin doldu.")
            return
        if status == "PENDING":
            bot.answer_callback_query(call.id, "⏳ İşleminiz sürüyor.")
            return
        if status == "AWAITING_PHONE":
            bot.answer_callback_query(call.id, "📱 Telefon numaranızı giriniz.")
            return

        # tekrar kontrol
        if kullanici_kontrol(user_id):
            kullanicilar[user_id_str] = {"status": "AWAITING_PHONE"}
            save_user_data(kullanicilar)
            bot.answer_callback_query(call.id, "✅ Üyelik gözüküyor. Lütfen telefon numaranızı gönderin.")
            bot.send_message(call.message.chat.id, "📱 Telefon numaranı gir (örnek: 5451234567):")
        else:
            bot.answer_callback_query(call.id, "❌ Hala katılmadığınız gözüküyor. Kanala/gruba katılın ve tekrar kontrol edin.")
            kontrol_butonu_gonder(call.message.chat.id)


# ---------- GLOBAL PRIVATE MESSAGE HANDLER ----------
# Burada özel sohbette gelen tüm metinleri yakalayıp duruma göre işliyoruz.
@bot.message_handler(func=lambda m: m.chat.type == 'private' and m.text is not None, content_types=['text'])
def private_text_handler(m):
    user_id = m.from_user.id
    user_id_str = str(user_id)
    text = m.text.strip()

    lock = get_user_lock(user_id_str)
    with lock:
        status = kullanicilar.get(user_id_str, {}).get("status")

        # Eğer kullanıcı telefon beklemede ise -> işle
        if status == "AWAITING_PHONE":
            telefon_al(m)  # telefon_al, gelen mesaj objesini kullanır
            return

        # Eğer kullanıcı hiç /start yapmamışsa veya başka metin atmışsa
        # cevap ver (opsiyonel)
        if text.startswith("/"):
            # komut zaten handled ediliyor (/start vb.)
            return
        else:
            bot.reply_to(m, "👋 FreeByte almak için önce /start yazın ve yönergeleri izleyin.")


# ---------- telefon_al (doğrulayıcı) ----------
def telefon_al(m):
    try:
        user_id = m.from_user.id
        user_id_str = str(user_id)
        no = m.text.strip()

        # Basit numara doğrulama: 10 hane (başında 0/5 kabul etmiyoruz; örnek: 5451234567)
        if not no.isdigit() or len(no) != 10:
            bot.reply_to(m, "❌ Geçersiz numara. Lütfen 10 haneli numara gir (örnek: 5451234567).")
            # durum AWATING_PHONE kalır, kullanıcı tekrar girebilir
            kullanicilar[user_id_str] = {"status": "AWAITING_PHONE"}
            save_user_data(kullanicilar)
            return

        # Kullaniciyi PENDING yap ve işlemi başlat
        kullanicilar[user_id_str] = {"status": "PENDING", "phone": no}
        save_user_data(kullanicilar)

        bot.reply_to(m, "⏳ İşleminiz başlatıldı, lütfen bekleyiniz...")
        executor.submit(freebytegonder_task, m.chat.id, no, user_id_str)
    except Exception as e:
        print("telefon_al hata:", e)
        traceback.print_exc()
        bot.reply_to(m, "⚠️ Bir hata oluştu. Lütfen tekrar deneyin.")
        # Güvenli duruma al
        kullanicilar[user_id_str] = {"status": "AWAITING_PHONE"}
        save_user_data(kullanicilar)


# ---------- gecici OTP alma (güvenli) ----------
def geciciotp():
    try:
        url = "https://3uptzlakwi.execute-api.eu-west-1.amazonaws.com/api/user/pin/get-otp"
        payload = {"pin": otp}
        headers = {
            'Authorization': "Bearer " + token,
            'Content-Type': "application/json"
        }
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        resp = r.json()
        if resp.get("otp"):
            return resp["otp"]
        else:
            print("geciciotp: otp yok, cevap:", resp)
            return None
    except Exception as e:
        print("geciciotp hata:", e)
        return None


# ---------- freebyte gönderme işlemi ----------
def freebytegonder_task(chat_id, no, user_id_str):
    try:
        # önce OTP al
        otp_code = geciciotp()
        if not otp_code:
            #bot.send_message(chat_id, "❌ OTP alınamadı. Lütfen tekrar deneyin veya daha sonra tekrar deneyin.")
            # kullanıcıyı tekrar telefon bekleme durumuna al (izin ver tekrar denesin)
            bot.send_message(chat_id, "Ciddi sorun var Admine Bildirildi. tekrar dene belki sorun Çözülür")
            bot.send_message(ADMIN_ID, "Ciddi sorun var hesap pın.")
            kullanicilar[user_id_str] = {"status": "AWAITING_PHONE", "phone": no}
            save_user_data(kullanicilar)
            return

        url = "https://utxk52xqxk.execute-api.eu-west-1.amazonaws.com/beta/transactions"
        payload = {
      "amount": "500",
      "toMsisdn": f"90{no}",
      "pinOtp": otp_code
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

        r = requests.post(url, json=payload, headers=headers, timeout=20)
        try:
            resp_json = r.json()
        except Exception:
            resp_json = {}

        # API limiti bitti
        if resp_json.get("code") == "insufficient-balance":
            bot.send_message(chat_id, "❌ Maalesef, botun FreeByte gönderme limiti dolmuş. Lütfen daha sonra tekrar deneyin.")
            kullanicilar[user_id_str] = {"status": "AWAITING_PHONE", "phone": no}
            save_user_data(kullanicilar)
            # opsiyonel: admin'e bildir
            try:
                bot.send_message(ADMIN_ID, f"⚠️ insufficient-balance uyarısı: kullanıcı {user_id_str} numara {no}")
            except Exception:
                pass
            return

        # pin-required gibi hata
        if resp_json.get("code") == "pin-required":
            bot.send_message(chat_id, "⚠️ Şifre/OTP ile ilgili bir sorun oluştu. Tekrar deneyin.")
            kullanicilar[user_id_str] = {"status": "AWAITING_PHONE", "phone": no}
            save_user_data(kullanicilar)
            return

        # başarılı mı?
        if resp_json.get("code") == "wrong_pin":
        	bot.send_message(chat_id, "Ciddi sorun var Admine Bildirildi. tekrar dene belki sorun Çözülür")
        	bot.send_message(ADMIN_ID, "Ciddi sorun var hesap pın.")
        if r.status_code == 200 and (resp_json.get("transactionId") or resp_json.get("status") == "success"):
            bot.send_message(chat_id, "✅ İşlem başarılı! 500 FreeByte gönderildi.")
            kullanicilar[user_id_str] = {"status": "SENT", "phone": no}
            save_user_data(kullanicilar)
            try:
                bot.send_message(ADMIN_ID, f"🎉 FreeByte gönderildi: kullanıcı {user_id_str} numara {no} -> {resp_json}")
            except Exception:
                pass
            return
        else:
            # başarısız detayını kullanıcıya gösterme (güvenlik), ama debugte konsola bas
            print("freebyte başarısız:", r.status_code, resp_json)
            bot.send_message(chat_id, "❌ İşlem başarısız oldu. Lütfen daha sonra tekrar deneyin.")
            kullanicilar[user_id_str] = {"status": "AWAITING_PHONE", "phone": no}
            save_user_data(kullanicilar)
            try:
                bot.send_message(ADMIN_ID, f"🚨 FreeByte başarısız: kullanıcı {user_id_str} numara {no} -> {resp_json}")
            except Exception:
                pass
            return

    except Exception as e:
        print("freebytegonder_task exception:", e)
        traceback.print_exc()
        bot.send_message(chat_id, "⚠️ Beklenmedik bir hata oluştu. Lütfen daha sonra tekrar deneyin.")
        kullanicilar[user_id_str] = {"status": "AWAITING_PHONE", "phone": no}
        save_user_data(kullanicilar)


# ---------- startup ----------
if __name__ == "__main__":
    print("🤖 Bot çalışıyor...")
    bot.infinity_polling(timeout=20, long_polling_timeout = 10)
