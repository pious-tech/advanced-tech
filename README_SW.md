# Smart Commune DSM - Maelekezo ya arifa (USSD + SMS)

Faili la `index.html` ni website. Faili la `app.py` ni "seva" inayopokea usajili, inajibu USSD/SMS na kutuma arifa kiotomatiki.

## Hatua 1: Jaribu kwenye kompyuta yako (bure, bila kulipa)

1. Weka Python kutoka python.org. Wakati wa kuweka, tia tiki "Add Python to PATH".
2. Fungua folda `backend` kwenye VS Code. Fungua Terminal (Terminal > New Terminal).
3. Andika amri hizi moja moja:
   ```
   pip install -r requirements.txt
   python app.py
   ```
4. Fungua browser: `http://localhost:5000/admin`
5. Fungua `index.html`, jisajili kwenye fomu ya "Pata arifa". Rudi kwenye terminal, utaona `[SMS ya majaribio]`. Hizo ndizo SMS zitakazotumwa baadaye kwa watu halisi.
6. Kwenye `/admin`, weka password (ya mwanzo ni `badilisha-hii`, ibadilishe), chagua barabara na hali, kisha bonyeza kitufe. Arifa inatumwa kwa wote waliojisajili kwa barabara hiyo.

## Hatua 2: Unganisha na SMS na USSD halisi

Seva yenyewe haiwezi kutuma SMS au kupokea USSD. Unahitaji mtoa huduma (aggregator) aliyeunganishwa na mitandao ya simu. Mfano: **Africa's Talking**, Beem Africa, NextSMS. Thibitisha na kila mmoja kama anatoa USSD na SMS Tanzania, na gharama zake, kabla ya kulipa.

Kwa Africa's Talking (njia ya majaribio ni bure kwenye "sandbox"):

1. Fungua akaunti, tengeneza App, chukua **API Key**.
2. Weka funguo kwenye terminal kabla ya kuendesha (Windows PowerShell):
   ```
   $env:AT_USERNAME="sandbox"
   $env:AT_API_KEY="funguo-yako"
   $env:ADMIN_PASSWORD="password-yako-ngumu"
   python app.py
   ```
3. Seva yako lazima ionekane mtandaoni. Kwa majaribio tumia `ngrok` (ngrok http 5000) kupata anwani kama `https://xxxx.ngrok-free.app`.
4. Kwenye dashibodi ya Africa's Talking:
   - USSD > Create Channel > Callback URL: `https://xxxx.ngrok-free.app/ussd`
   - SMS > Callback URL ya ujumbe unaoingia: `https://xxxx.ngrok-free.app/sms`
5. Jaribu kwa "Simulator" iliyomo kwenye dashibodi yao.

## Hatua 3: Kuanza kutumika kwa watu halisi

- **Namba ya USSD** (mfano `*XXX#`) na **namba ya SMS** (mfano `15XXX`) kwa umma zinahitaji kusajiliwa na kulipiwa kupitia mtoa huduma na mitandao ya simu. Hii huchukua muda na ina gharama, kwa hiyo anza na majaribio.
- Weka seva mtandaoni kwa huduma kama Render, Railway au PythonAnywhere, na utumie HTTPS. Baadhi ya huduma za bure hufuta faili la database (`commune.db`) zikizimwa, kwa hiyo hakikisha una hifadhi ya kudumu.
- Kwenye `index.html`: badilisha `*XXX#` na `15XXX` kuwa namba halisi. Anwani ya seva (`const API = ...` kwenye sehemu ya `<script>`, na `action` ya fomu ya arifa) badilisha kutoka `http://localhost:5000` kuwa anwani yako ya mtandaoni.
- Weka `ALLOWED_ORIGIN` kuwa anwani ya website yako ili seva ikubali maombi kutoka huko tu.
- Taarifa zinazotumwa ukiwa offline huhifadhiwa kwenye simu na hutumwa utakapofungua ukurasa tena ukiwa na mtandao.

## Tahadhari muhimu

- **Usahihi:** taarifa za wananchi hazijathibitishwa na zinaweza kuwa za uongo. Arifa zinaandikwa "haijathibitishwa". Mtu mmoja au zaidi wanapaswa kuhakiki kabla ya kutuma arifa kubwa kwa wote kupitia `/admin`.
- **Faragha:** namba za simu ni taarifa binafsi. Zilinde, usizishiriki, na jifunze mahitaji ya sheria ya ulinzi wa taarifa binafsi ya Tanzania (PDPA 2022).
- **Gharama:** kila SMS na kila kipindi cha USSD kina bei. Watumiaji wengi maana yake bili kubwa.
- **Ongeza baadaye:** njia nyingine nyepesi ni Telegram bot au kikundi/channel ya WhatsApp.
