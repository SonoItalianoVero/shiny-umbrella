import asyncio
import logging
import os
import io
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile
from xhtml2pdf import pisa

# Получаем токен из Railway
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("ОШИБКА: BOT_TOKEN не найден в переменных окружения!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Шаблон, адаптированный специально для конвертации в PDF
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fi">
<head>
    <meta charset="UTF-8">
    <style>
        @page {{
            size: A4;
            margin: 2cm;
        }}
        body {{ 
            font-family: Helvetica, Arial, sans-serif; 
            color: #1e293b; 
            line-height: 1.5; 
            font-size: 13px; 
        }}
        h1 {{ 
            color: #0f172a; 
            font-size: 20px; 
            margin-bottom: 5px;
        }}
        h2 {{ 
            color: #1e293b;
            font-size: 14px; 
            margin-top: 25px; 
            margin-bottom: 10px;
            text-transform: uppercase;
        }}
        h3 {{
            color: #334155;
            font-size: 13px;
            margin-top: 15px;
            margin-bottom: 5px;
        }}
        p, li {{ 
            text-align: justify;
            margin-bottom: 8px;
        }}
        .highlight {{
            background-color: #f1f5f9;
            padding: 12px;
            border-left: 3px solid #3b82f6;
            margin: 15px 0;
            font-weight: bold;
        }}
        table.header {{
            width: 100%;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }}
        table.pricing {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 11px;
        }}
        table.pricing th, table.pricing td {{
            border: 1px solid #cbd5e1;
            padding: 8px;
            text-align: center;
        }}
        table.pricing th {{
            background-color: #f8fafc;
            font-weight: bold;
            color: #334155;
        }}
        table.signatures {{
            width: 100%;
            margin-top: 50px;
        }}
        td {{ vertical-align: top;
        }}
        .signature-line {{
            border-bottom: 1px solid #000;
            width: 80%;
            margin-top: 5px;
            margin-bottom: 5px;
        }}
        .footer {{ 
            margin-top: 50px;
            font-size: 10px; 
            color: #94a3b8; 
            text-align: center; 
            border-top: 1px solid #e2e8f0; 
            padding-top: 15px;
        }}
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
        <p>Salkunhoitaja toteuttaa kaupat Asiakkaan puolesta korkean likviditeetin aikaikkunoissa. Istunnon arvioitu kesto on <strong>2–3 tuntia</strong>, jonka jälkeen positiot suljetaan. Salkunhoitaja on velvollinen suorittamaan kaikki varojen palautukset ja voitonmaksut Asiakkaalle yksinomaan fiat-valuutassa.</p>

        <h2>3. Tuottotavoite ja Palkkiorakenne</h2>
        <p>Salkunhoitaja soveltaa korkean tuoton intraday-strategioita merkittävän pääomankasvun saavuttamiseksi. Salkunhoitajan palkkio perustuu yksinomaan onnistuneeseen tulokseen:</p>
        <ul>
            <li>Palkkio lasketaan <strong>vain istunnon aikana kertyneestä nettovoitosta</strong>.</li>
            <li>Asiakas maksaa palkkion vasta sen jälkeen, kun alkupääoma ja kertyneet voitot on siirretty onnistuneesti Asiakkaan omaan lompakkoon tai pankkitilille fiat-valuutassa.</li>
        </ul>

        <h3>Tariffisuunnitelmat: Crypto Intraday (Helsinki Edition)</h3>
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

        <h2>4. Riskienhallinta ja Vastuut</h2>
        <p>Asiakas ymmärtää, että digitaalisten varojen kaupankäyntiin liittyy merkittävä markkinoiden volatiliteetti ja mahdollinen tappion riski. Vaikka Salkunhoitaja käyttää edistyksellisiä riskienhallintaprotokollia, aiempi kehitys ei ole tae tulevista tuotoista. Asiakas hyväksyy sijoitussummaan kohdistuvat markkinariskit.</p>
        <p><strong>Pääomaturva ja kompensaatio:</strong> Mikäli kaupankäynti epäonnistuu tai johtaa tappioon, Salkunhoitaja sitoutuu palauttamaan Asiakkaalle tämän sijoittaman alkupääoman täysimääräisenä. Lisäksi Salkunhoitaja on velvollinen maksamaan Asiakkaalle kiinteän 150 euron suuruisen korvauksen kaupankäynnin tuloksesta riippumatta, korvauksena Asiakkaan käyttämästä ajasta ja vaivasta.</p>

        <h2>5. Kertaluonteinen Talletus ja Lisämaksujen Kielto</h2>
        <p>Tämän sopimuksen mukainen sijoitus on ehdottomasti kertaluonteinen. Asiakas sitoutuu tekemään vain yhden (1) talletuksen valitun tariffisuunnitelman puitteissa, eikä Salkunhoitaja vaadi tai hyväksy mitään lisämaksuja käynnissä olevan kaupankäyntiistunnon aikana. Kaikki kaupankäynti toteutetaan yksinomaan alun perin siirretyn pääoman rajoissa. Mahdolliset uudet sijoitukset tai kaupankäyntiistunnot edellyttävät aina uuden, erillisen omaisuudenhoitosopimuksen laatimista.</p>

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
                <div style="margin-top: 25px;"></div>
                <strong>Asiakas:</strong>
                <div class="signature-line" style="margin-top: 40px;"></div>
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

# Вспомогательная функция для генерации PDF
def generate_pdf(html_content: str) -> bytes:
    pdf_buffer = io.BytesIO()
    # Конвертируем HTML в PDF
    pisa_status = pisa.CreatePDF(io.StringIO(html_content), dest=pdf_buffer)
    if pisa_status.err:
        raise Exception("Ошибка при компиляции PDF файла")
    return pdf_buffer.getvalue()

# Инструкция и приветствие на русском
@dp.message(Command("start", "help"))
async def send_welcome(message: types.Message):
    await message.answer(
        "👋 <b>Добро пожаловать в панель генерации контрактов!</b>\n\n"
        "Для создания нового PDF-контракта используйте команду в формате:\n"
        "<code>/contract Имя_Клиента Сумма</code>\n\n"
        "<b>Пример:</b>\n"
        "<code>/contract Matti Virtanen 200</code>",
        parse_mode="HTML"
    )

# Основная команда генерации
@dp.message(Command("contract"))
async def create_contract(message: types.Message, command: CommandObject):
    if command.args is None:
        await message.answer("❌ <b>Ошибка ввода.</b>\nПожалуйста, используйте формат: <code>/contract Имя Фамилия Сумма</code>", parse_mode="HTML")
        return

    args_list = command.args.split()
    if len(args_list) < 2:
        await message.answer("❌ <b>Ошибка ввода.</b>\nУкажите ФИО клиента и сумму вложений.", parse_mode="HTML")
        return

    # Отправляем сообщение об ожидании
    processing_msg = await message.answer("⏳ Генерирую PDF-контракт, пожалуйста подождите...")

    try:
        amount = args_list[-1]
        client_name = " ".join(args_list[:-1])
        
        # Получаем время по Хельсинки
        helsinki_tz = pytz.timezone('Europe/Helsinki')
        current_date = datetime.now(helsinki_tz).strftime("%d.%m.%Y")

        # Формируем HTML
        final_html = HTML_TEMPLATE.format(
            date=current_date,
            client_name=client_name,
            amount=amount
        )

        # Создаем PDF
        pdf_bytes = generate_pdf(final_html)
        
        # Называем файл: ФИО_номер.pdf
        file_name = f"{client_name}_2690497.pdf"
        document = BufferedInputFile(pdf_bytes, filename=file_name)

        # Отправляем PDF
        await message.answer_document(
            document, 
            caption=f"✅ <b>Контракт готов!</b>\n\n👤 Клиент: {client_name}\n💶 Сумма: €{amount}\n📄 Номер заявки: #2690497",
            parse_mode="HTML"
        )
        
        # Удаляем сообщение "Ожидайте..."
        await processing_msg.delete()

    except Exception as e:
        await processing_msg.edit_text(f"❌ <b>Произошла системная ошибка:</b>\n{str(e)}", parse_mode="HTML")

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
