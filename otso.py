import asyncio
import logging
import os
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile

# Получаем токен из переменных окружения Railway
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("ОШИБКА: BOT_TOKEN не найден в переменных окружения!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Современный финский шаблон контракта
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Omaisuudenhoitosopimus</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        body {{ 
            font-family: 'Inter', sans-serif; 
            background-color: #f8fafc; 
            color: #0f172a; 
            line-height: 1.6; 
            margin: 0; 
            padding: 40px 20px; 
        }}
        .document-container {{
            max-width: 800px;
            margin: 0 auto;
            background: #ffffff;
            padding: 50px 60px;
            border-radius: 8px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
            border-top: 6px solid #1e293b;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .title-block h1 {{ 
            margin: 0; 
            color: #1e293b; 
            font-size: 24px; 
            font-weight: 700;
            letter-spacing: -0.5px;
        }}
        .title-block p {{
            margin: 5px 0 0;
            color: #64748b;
            font-size: 14px;
            font-weight: 600;
        }}
        .meta-info {{
            text-align: right;
            font-size: 14px;
            color: #475569;
        }}
        .meta-info p {{ margin: 4px 0; }}
        .meta-info strong {{ color: #0f172a; }}
        
        h2 {{ 
            color: #1e293b; 
            font-size: 16px; 
            font-weight: 700; 
            margin-top: 35px; 
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        p, li {{ 
            font-size: 15px; 
            color: #334155; 
            text-align: justify;
        }}
        .highlight {{
            background-color: #f1f5f9;
            padding: 15px 20px;
            border-left: 4px solid #3b82f6;
            border-radius: 4px;
            margin: 20px 0;
            font-weight: 600;
            color: #0f172a;
        }}
        .signatures {{ 
            margin-top: 60px; 
            display: flex; 
            justify-content: space-between; 
            gap: 40px;
        }}
        .sign-block {{ 
            flex: 1; 
            border-top: 1px solid #cbd5e1; 
            padding-top: 15px; 
        }}
        .sign-block p {{ margin: 5px 0; font-size: 14px; }}
        .sign-block .name {{ font-weight: 700; color: #0f172a; font-size: 16px; margin-top: 15px; }}
        
        .footer {{ 
            margin-top: 50px; 
            font-size: 12px; 
            color: #94a3b8; 
            text-align: center; 
            border-top: 1px solid #f1f5f9; 
            padding-top: 20px; 
        }}
    </style>
</head>
<body>
    <div class="document-container">
        <div class="header">
            <div class="title-block">
                <h1>OMAISUUDENHOITOSOPIMUS</h1>
                <p>Digitaalisten varojen hallinta (Intraday)</p>
            </div>
            <div class="meta-info">
                <p>Sopimusnumero: <strong>#2690497</strong></p>
                <p>Päivämäärä: <strong>{date}</strong></p>
                <p>Paikka: <strong>Helsinki, Suomi</strong></p>
            </div>
        </div>

        <div class="content">
            <p>Tämä omaisuudenhoitosopimus ("Sopimus") on solmittu <strong>{date}</strong>, ja sen osapuolina ovat Otso Laine (jäljempänä "Salkunhoitaja") ja <strong>{client_name}</strong> (jäljempänä "Asiakas").</p>

            <h2>1. Sopimuksen Tarkoitus</h2>
            <p>Asiakas valtuuttaa Salkunhoitajan tarjoamaan päiväkaupan (intraday) ja digitaalisten varojen hallintapalveluita. Salkunhoitaja hyödyntää patentoituja algoritmisia ja makrotaloudellisia strategioita Asiakkaan osoittaman pääoman hallinnoinnissa.</p>

            <h2>2. Alkupääoma ja Työaika</h2>
            <div class="highlight">
                Asiakas osoittaa kaupankäyntiistuntoon {amount} € (Sijoitussumma).
            </div>
            <p>Salkunhoitaja toteuttaa kaupat Asiakkaan puolesta korkean likviditeetin aikaikkunoissa. Istunnon arvioitu kesto on <strong>2–3 tuntia</strong>, jonka jälkeen positiot suljetaan ja varat palautetaan vakaavaluuttaan (stablecoin).</p>

            <h2>3. Tuottotavoite ja Palkkiorakenne</h2>
            <p>Salkunhoitaja soveltaa korkean tuoton intraday-strategioita merkittävän pääomankasvun saavuttamiseksi. Salkunhoitajan palkkio perustuu yksinomaan onnistuneeseen tulokseen:</p>
            <ul>
                <li>Palkkio (10–20 % valitusta palvelutasosta riippuen) lasketaan <strong>vain istunnon aikana kertyneestä nettovoitosta</strong>.</li>
                <li>Asiakas maksaa palkkion vasta sen jälkeen, kun alkupääoma ja kertyneet voitot on siirretty onnistuneesti ja turvallisesti Asiakkaan omaan lompakkoon.</li>
            </ul>

            <h2>4. Riskienhallinta ja Vastuut</h2>
            <p>Asiakas ymmärtää, että digitaalisten varojen kaupankäyntiin liittyy merkittävä markkinoiden volatiliteetti ja mahdollinen tappion riski. Vaikka Salkunhoitaja käyttää edistyksellisiä riskienhallintaprotokollia ja tiukkoja päiväkaupan irtautumisstrategioita riskien minimoimiseksi, aiempi kehitys ei ole tae tulevista tuotoista. Asiakas hyväksyy sijoitussummaan kohdistuvat markkinariskit.</p>

            <h2>5. Voimassaolo ja Päättyminen</h2>
            <p>Tämä Sopimus koskee vain osapuolten sopimaa yksittäistä kaupankäyntiistuntoa. Sopimus päättyy automaattisesti, kun istunnon varat on tilitetty ja mahdolliset tulosperusteiset palkkiot on maksettu.</p>
        </div>

        <div class="signatures">
            <div class="sign-block">
                <p><strong>Salkunhoitaja:</strong></p>
                <p class="name">Otso Laine</p>
                <p>Senior Analyst @ Kepler Cheuvreux<br>Digital Asset Management</p>
            </div>
            <div class="sign-block">
                <p><strong>Asiakas:</strong></p>
                <p class="name">{client_name}</p>
                <p>Yksityissijoittaja</p>
            </div>
        </div>

        <div class="footer">
            Ehdottoman luottamuksellinen. Asiakirja on laadittu digitaalisen varainhoidon läpinäkyvyyden periaatteita noudattaen.
        </div>
    </div>
</body>
</html>
"""

@dp.message(Command("contract"))
async def create_contract(message: types.Message, command: CommandObject):
    if command.args is None:
        await message.answer("Virhe. Käytä muotoa:\n/contract Nimi Summa\nEsimerkki: /contract Matti Virtanen 200")
        return

    args_list = command.args.split()
    if len(args_list) < 2:
        await message.answer("Anna asiakkaan nimi ja summa.")
        return

    try:
        amount = args_list[-1]
        client_name = " ".join(args_list[:-1])
        
        # Получаем точное время по Хельсинки
        helsinki_tz = pytz.timezone('Europe/Helsinki')
        current_date = datetime.now(helsinki_tz).strftime("%d.%m.%Y")

        # Подставляем данные в HTML
        final_html = HTML_TEMPLATE.format(
            date=current_date,
            client_name=client_name,
            amount=amount
        )

        file_bytes = final_html.encode('utf-8')
        file_name = f"Omaisuudenhoitosopimus_{client_name.replace(' ', '_')}_{current_date}.html"
        document = BufferedInputFile(file_bytes, filename=file_name)

        await message.answer_document(
            document, 
            caption=f"✅ Sopimus asiakkaalle {client_name} summalle {amount} € on luotu onnistuneesti. (ID: #2690497)"
        )

    except Exception as e:
        await message.answer(f"Virhe generoinnissa: {str(e)}")

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())