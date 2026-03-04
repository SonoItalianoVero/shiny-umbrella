import asyncio
import logging
import os
import io
import sqlite3
import uuid
from datetime import datetime
import pytz

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile
from aiohttp import web
from xhtml2pdf import pisa

# ================= НАСТРОЙКИ И ПЕРЕМЕННЫЕ =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
# Railway автоматически выдает порт для веб-сервера
PORT = int(os.getenv("PORT", 8080))
# Домен вашего сайта (зададим переменную в Railway, или Railway сам её подставит)
DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN", "your-app-domain.railway.app")

if not BOT_TOKEN:
    raise ValueError("ОШИБКА: BOT_TOKEN не найден в переменных окружения!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ================= БАЗА ДАННЫХ (SQLite) =================

def init_db():
    conn = sqlite3.connect('contracts.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS contracts
                 (id TEXT PRIMARY KEY, client_name TEXT, amount TEXT, date TEXT, 
                  admin_chat_id INTEGER, status TEXT)''')
    conn.commit()
    conn.close()

# Инициализируем базу при запуске
init_db()

# ================= ШАБЛОНЫ =================

# 1. Текст для веб-страницы (то, что клиент читает перед подписью)

WWEB_CONTRACT_TEXT = """
<table class="header">
    <tr>
        <td width="60%">
            <h2>OMAISUUDENHOITOSOPIMUS</h2>
            <p style="color: #64748b; font-size: 12px; margin-top: 0;">Digitaalisten varojen hallinta (Intraday)</p>
        </td>
        <td width="40%" style="text-align: right; font-size: 12px; color: #475569;">
            <p style="margin: 2px 0;">Sopimusnumero: <strong style="color: #000;">#2690497</strong></p>
            <p style="margin: 2px 0;">Päivämäärä: <strong style="color: #000;">{date}</strong></p>
            <p style="margin: 2px 0;">Paikka: <strong style="color: #000;">Helsinki, Suomi</strong></p>
        </td>
    </tr>
</table>

<div class="content">
    <p>Tämä omaisuudenhoitosopimus ("Sopimus") on solmittu <strong>{date}</strong>, ja sen osapuolina ovat Otso Laine (jäljempänä "Salkunhoitaja") ja <strong>{client_name}</strong> (jäljempänä "Asiakas").</p>

    <h3>1. Sopimuksen Tarkoitus</h3>
    <p>Asiakas valtuuttaa Salkunhoitajan tarjoamaan päiväkaupan (intraday) ja digitaalisten varojen hallintapalveluita. Salkunhoitaja hyödyntää patentoituja algoritmisia ja makrotaloudellisia strategioita Asiakkaan osoittaman pääoman hallinnoinnissa.</p>

    <h3>2. Alkupääoma ja Työaika</h3>
    <div class="highlight">
        Asiakas osoittaa kaupankäyntiistuntoon {amount} € (Sijoitussumma). Talletus suoritetaan yksinomaan fiat-valuutassa.
    </div>
    <p>Salkunhoitaja toteuttaa kaupat Asiakkaan puolesta korkean likviditeetin aikaikkunoissa. Istunnon arvioitu kesto on <strong>2–3 tuntia</strong>, jonka jälkeen positiot suljetaan. Salkunhoitaja on velvollinen suorittamaan kaikki varojen palautukset ja voitonmaksut Asiakkaalle yksinomaan fiat-valuutassa.</p>

    <h3>3. Tuottotavoite ja Palkkiorakenne</h3>
    <p>Salkunhoitaja soveltaa korkean tuoton intraday-strategioita merkittävän pääomankasvun saavuttamiseksi. Salkunhoitajan palkkio perustuu yksinomaan onnistuneeseen tulokseen:</p>
    <ul>
        <li>Palkkio lasketaan <strong>vain istunnon aikana kertyneestä nettovoitosta</strong>.</li>
        <li>Asiakas maksaa palkkion vasta sen jälkeen, kun alkupääoma ja kertyneet voitot on siirretty onnistuneesti Asiakkaan omaan lompakkoon tai pankkitilille fiat-valuutassa.</li>
    </ul>

    <h4>Tariffisuunnitelmat: Crypto Intraday (Helsinki Edition)</h4>
    <table class="pricing">
        <tr>
            <th>Paketti</th>
            <th>Talletus</th>
            <th>Työaika</th>
            <th>Minimituotto (Brutto)</th>
            <th>Palkkio</th>
            <th>Asiakkaan nettovoitto</th>
        </tr>
        <tr>
            <td>Fast Impulse</td>
            <td>100 €</td>
            <td>2 tuntia</td>
            <td>1 300 €</td>
            <td>20% (260 €)</td>
            <td>1 040 €</td>
        </tr>
        <tr>
            <td>Nordic Strategy</td>
            <td>135 €</td>
            <td>2,5 tuntia</td>
            <td>2 000 €</td>
            <td>15% (300 €)</td>
            <td>1 700 €</td>
        </tr>
        <tr>
            <td>Kepler High-Yield</td>
            <td>200 €</td>
            <td>3 tuntia</td>
            <td>3 200 €</td>
            <td>10% (320 €)</td>
            <td>2 880 €</td>
        </tr>
    </table>
    <p style="font-size: 11px; color: #475569;"><em>Salkunhoitaja sitoutuu saavuttamaan vähintään yllä mainitun minimituoton. Mahdollisen ylituoton tavoittelu ja tuloutus on yksinomaan Salkunhoitajan harkinnassa.</em></p>

    <h3>4. Riskienhallinta ja Vastuut</h3>
    <p>Asiakas ymmärtää, että digitaalisten varojen kaupankäyntiin liittyy merkittävä markkinoiden volatiliteetti ja mahdollinen tappion riski. Vaikka Salkunhoitaja käyttää edistyksellisiä riskienhallintaprotokollia, aiempi kehitys ei ole tae tulevista tuotoista. Asiakas hyväksyy sijoitussummaan kohdistuvat markkinariskit.</p>
    <p><strong>Pääomaturva ja kompensaatio:</strong> Mikäli kaupankäynti epäonnistuu tai johtaa tappioon, Salkunhoitaja sitoutuu palauttamaan Asiakkaalle tämän sijoittaman alkupääoman täysimääräisenä. Lisäksi Salkunhoitaja on velvollinen maksamaan Asiakkaalle kiinteän 150 euron suuruisen korvauksen kaupankäynnin tuloksesta riippumatta, korvauksena Asiakkaan käyttämästä ajasta ja vaivasta.</p>

    <h3>5. Kertaluonteinen Talletus ja Lisämaksujen Kielto</h3>
    <p>Tämän sopimuksen mukainen sijoitus on ehdottomasti kertaluonteinen. Asiakas sitoutuu tekemään vain yhden (1) talletuksen valitun tariffisuunnitelman puitteissa, eikä Salkunhoitaja vaadi tai hyväksy mitään lisämaksuja käynnissä olevan kaupankäyntiistunnon aikana. Kaikki kaupankäynti toteutetaan yksinomaan alun perin siirretyn pääoman rajoissa. Mahdolliset uudet sijoitukset tai kaupankäyntiistunnot edellyttävät aina uuden, erillisen omaisuudenhoitosopimuksen laatimista.</p>

    <h3>6. Voimassaolo ja Päättyminen</h3>
    <p>Sopimus koskee yksittäistä kaupankäyntiistuntoa. Sopimus päättyy, kun varat on tilitetty ja mahdolliset palkkiot maksettu.</p>
</div>
"""

# 2. Шаблон для финального PDF (с обеими подписями)
PDF_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fi">
<head>
    <meta charset="UTF-8">
    <style>
        @page {{ size: A4; margin: 2cm; }}
        body {{ font-family: Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.5; font-size: 13px; }}
        h1 {{ color: #0f172a; font-size: 20px; margin-bottom: 5px; }}
        h2 {{ color: #1e293b; font-size: 14px; margin-top: 25px; margin-bottom: 10px; text-transform: uppercase; }}
        h3 {{ color: #334155; font-size: 13px; margin-top: 15px; margin-bottom: 5px; }}
        p, li {{ text-align: justify; margin-bottom: 8px; }}
        .highlight {{ background-color: #f1f5f9; padding: 12px; border-left: 3px solid #3b82f6; margin: 15px 0; font-weight: bold; }}
        table.header {{ width: 100%; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; margin-bottom: 25px; }}
        table.pricing {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 11px; }}
        table.pricing th, table.pricing td {{ border: 1px solid #cbd5e1; padding: 8px; text-align: center; }}
        table.pricing th {{ background-color: #f8fafc; font-weight: bold; color: #334155; }}
        table.signatures {{ width: 100%; margin-top: 50px; }}
        td {{ vertical-align: top; }}
        .signature-line {{ border-bottom: 1px solid #000; width: 80%; margin-top: 5px; margin-bottom: 5px; }}
        .footer {{ margin-top: 50px; font-size: 10px; color: #94a3b8; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 15px; }}
    </style>
</head>
<body>
    <table class="header">
        <tr>
            <td width="60%">
                <h1>OMAISUUDENHOITOSOPIMUS</h1>
                <p style="color: #64748b; font-size: 12px; margin-top: 0;">Digitaalisten varojen hallinta (Intraday)</p>
            </td>
            <td width="40%" style="text-align: right; font-size: 12px; color: #475569;">
                <p style="margin: 2px 0;">Sopimusnumero: <strong style="color: #000;">#2690497</strong></p>
                <p style="margin: 2px 0;">Päivämäärä: <strong style="color: #000;">{date}</strong></p>
                <p style="margin: 2px 0;">Paikka: <strong style="color: #000;">Helsinki, Suomi</strong></p>
            </td>
        </tr>
    </table>

    <div class="content">
        <p>Tämä omaisuudenhoitosopimus ("Sopimus") on solmittu <strong>{date}</strong>, ja sen osapuolina ovat Otso Laine (jäljempänä "Salkunhoitaja") ja <strong>{client_name}</strong> (jäljempänä "Asiakas").</p>
        <h2>1. Sopimuksen Tarkoitus</h2>
        <p>Asiakas valtuuttaa Salkunhoitajan tarjoamaan päiväkaupan (intraday) ja digitaalisten varojen hallintapalveluita. Salkunhoitaja hyödyntää patentoituja algoritmisia ja makrotaloudellisia strategioita Asiakkaan osoittaman pääoman hallinnoinnissa.</p>
        <h2>2. Alkupääoma ja Työaika</h2>
        <div class="highlight">
            Asiakas osoittaa kaupankäyntiistuntoon {amount} € (Sijoitussumma). Talletus suoritetaan yksinomaan fiat-valuutassa.
        </div>
        <p>Salkunhoitaja toteuttaa kaupat Asiakkaan puolesta korkean likviditeetin aikaikkunoissa. Istunnon arvioitu kesto on <strong>2–3 tuntia</strong>.</p>
        <h2>3. Tuottotavoite ja Palkkiorakenne</h2>
        <p>Salkunhoitajan palkkio perustuu yksinomaan onnistuneeseen tulokseen vain istunnon aikana kertyneestä nettovoitosta.</p>
        <h2>4. Riskienhallinta ja Vastuut</h2>
        <p>Pääomaturva ja kompensaatio: Mikäli kaupankäynti epäonnistuu tai johtaa tappioon, Salkunhoitaja sitoutuu palauttamaan Asiakkaalle tämän sijoittaman alkupääoman täysimääräisenä. Lisäksi Salkunhoitaja on velvollinen maksamaan Asiakkaalle kiinteän 150 euron suuruisen korvauksen.</p>
        <h2>5. Kertaluonteinen Talletus ja Lisämaksujen Kielto</h2>
        <p>Tämän sopimuksen mukainen sijoitus on ehdottomasti kertaluonteinen. Asiakas sitoutuu tekemään vain yhden (1) talletuksen valitun tariffisuunnitelman puitteissa, eikä Salkunhoitaja vaadi tai hyväksy mitään lisämaksuja käynnissä olevan kaupankäyntiistunnon aikana. Kaikki kaupankäynti toteutetaan yksinomaan alun perin siirretyn pääoman rajoissa.</p>
        <h2>6. Voimassaolo ja Päättyminen</h2>
        <p>Sopimus koskee yksittäistä kaupankäyntiistuntoa. Sopimus päättyy, kun varat on tilitetty ja mahdolliset palkkiot maksettu.</p>
    </div>

    <table class="signatures">
        <tr>
            <td width="50%">
                <strong>Salkunhoitaja:</strong>
                <div style="margin-top: 15px; margin-bottom: -10px; height: 50px;">
                    <img src="sign.png" height="50" />
                </div>
                <div class="signature-line"></div>
                <strong>Otso Laine</strong><br>
                <span style="font-size: 11px; color: #475569;">Senior Analyst @ Kepler Cheuvreux<br>Digital Asset Management</span>
            </td>
            <td width="50%">
                <strong>Asiakas:</strong>
                <div style="margin-top: 15px; margin-bottom: -10px; height: 50px;">
                    <img src="{client_signature}" height="50" />
                </div>
                <div class="signature-line"></div>
                <strong>{client_name}</strong><br>
                <span style="font-size: 11px; color: #475569;">Yksityissijoittaja</span>
            </td>
        </tr>
    </table>

    <div class="footer">
        Ehdottoman luottamuksellinen. Asiakirja on laadittu digitaalisen varainhoidon läpinäkyvyyden periaatteita noudattaen.
    </div>
</body>
</html>
"""

def generate_pdf(html_content: str) -> bytes:
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(html_content), dest=pdf_buffer)
    if pisa_status.err:
        raise Exception("Ошибка при компиляции PDF файла")
    return pdf_buffer.getvalue()

# ================= TELEGRAM БОТ =================

@dp.message(Command("start", "help"))
async def send_welcome(message: types.Message):
    await message.answer(
        "👋 <b>Панель генерации контрактов</b>\n\n"
        "Формат команды:\n<code>/contract Имя_Клиента Сумма</code>\n\n"
        "Бот сгенерирует уникальную ссылку для подписи клиентом.",
        parse_mode="HTML"
    )

@dp.message(Command("contract"))
async def create_contract(message: types.Message, command: CommandObject):
    if command.args is None or len(command.args.split()) < 2:
        await message.answer("❌ Формат: <code>/contract Имя Фамилия Сумма</code>", parse_mode="HTML")
        return

    args_list = command.args.split()
    amount = args_list[-1]
    client_name = " ".join(args_list[:-1])
    
    helsinki_tz = pytz.timezone('Europe/Helsinki')
    current_date = datetime.now(helsinki_tz).strftime("%d.%m.%Y")
    contract_id = str(uuid.uuid4().hex)[:10] # Создаем короткий уникальный ID

    # Сохраняем в БД
    conn = sqlite3.connect('contracts.db')
    c = conn.cursor()
    c.execute("INSERT INTO contracts VALUES (?, ?, ?, ?, ?, ?)", 
              (contract_id, client_name, amount, current_date, message.chat.id, "pending"))
    conn.commit()
    conn.close()

    # Формируем ссылку для клиента
    link = f"https://{DOMAIN}/sign/{contract_id}"
    
    await message.answer(
        f"✅ <b>Договор сформирован!</b>\n\n👤 Клиент: {client_name}\n💶 Сумма: €{amount}\n\n"
        f"🔗 <b>Отправьте эту ссылку клиенту для подписи:</b>\n{link}",
        parse_mode="HTML"
    )

# ================= ВЕБ-СЕРВЕР (aiohttp) =================

async def handle_sign_page(request):
    contract_id = request.match_info.get('id', '')
    
    conn = sqlite3.connect('contracts.db')
    c = conn.cursor()
    c.execute("SELECT client_name, amount, date, status FROM contracts WHERE id=?", (contract_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return web.Response(text="Sopimusta ei löydy / Контракт не найден", status=404)
    
    client_name, amount, date, status = row
    if status == 'signed':
        return web.Response(text="Tämä sopimus on jo allekirjoitettu / Этот контракт уже подписан", status=403)

    # Читаем HTML шаблон страницы (которую мы создали на шаге 1)
    with open('templates/sign_page.html', 'r', encoding='utf-8') as f:
        html_template = f.read()

    # Подставляем переменные в текстовый блок контракта
    contract_text = WEB_CONTRACT_TEXT.format(date=date, client_name=client_name, amount=amount)
    
    # Вставляем текст в веб-страницу
    final_html = html_template.replace("{{ contract_content | safe }}", contract_text)
    
    return web.Response(text=final_html, content_type='text/html')

async def handle_submit_signature(request):
    contract_id = request.match_info.get('id', '')
    data = await request.json()
    signature_base64 = data.get('image') # Получаем картинку с подписью
    
    conn = sqlite3.connect('contracts.db')
    c = conn.cursor()
    c.execute("SELECT client_name, amount, date, admin_chat_id, status FROM contracts WHERE id=?", (contract_id,))
    row = c.fetchone()

    if not row or row[4] == 'signed':
        conn.close()
        return web.Response(status=400)

    client_name, amount, date, admin_chat_id, _ = row
    
    # Обновляем статус в БД
    c.execute("UPDATE contracts SET status='signed' WHERE id=?", (contract_id,))
    conn.commit()
    conn.close()

    # Формируем финальный PDF!
    final_html = PDF_HTML_TEMPLATE.format(
        date=date,
        client_name=client_name,
        amount=amount,
        client_signature=signature_base64 # Вставляем подпись клиента (base64) напрямую
    )

    pdf_bytes = generate_pdf(final_html)
    file_name = f"{client_name}_signed.pdf"
    document = BufferedInputFile(pdf_bytes, filename=file_name)

    # Отправляем PDF администратору в Telegram
    try:
        await bot.send_document(
            admin_chat_id, 
            document, 
            caption=f"🚨 <b>Новый подписанный контракт!</b>\n\n👤 Клиент: {client_name}\n💶 Сумма: €{amount}\n✅ Статус: Успешно подписан клиентом.",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка отправки в Telegram: {e}")

    return web.Response(text="Success")

# ================= ЗАПУСК СИСТЕМЫ =================

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Настраиваем веб-сервер
    app = web.Application()
    app.router.add_get('/sign/{id}', handle_sign_page)
    app.router.add_post('/submit-signature/{id}', handle_submit_signature)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logging.info(f"Веб-сервер запущен на порту {PORT}")

    # Запускаем бота параллельно
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
