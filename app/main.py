import os, sys
import unicodedata
from bs4 import BeautifulSoup
import re
import requests
from flask import Flask, request

app = Flask(__name__)

# url intent raggiungimento
URL_DIB_LOCATION = "https://www.uniba.it/ricerca/dipartimenti/informatica/dipartimento/come-raggiungerci"

# url intent carta di identità
URL_CIE = "https://www.comune.bari.it/web/egov/-/carta-d-identita-elettronica-cie-"

# URL cambio di residenza
URL_CR = "https://www.comune.bari.it/web/egov/-/cambio-di-residenza-con-provenienza-da-altro-comune-o-stato-estero-e-cambio-di-abitazione-bari-su-bari-"


def parsing_html(url):
    response = requests.get(url=url)
    response_html = response.text
    return BeautifulSoup(response_html, 'html.parser')


# scraping sulle info inerenti alla CDI elettronica
def cie_scraping(url, text, context):
    fulfillmentText = ""
    soup = parsing_html(url)

    if text is not None:
        # flag per la gestione delle stampe
        printText = False
        match text:
            case "DONAZIONE":
                text = "POSSIBILITÀ DI ESPRIMERSI SULLA DONAZIONE DI ORGANI E TESSUTI"
            case "PROCEDURA":
                text = "PROCEDURA DI RILASCIO"
            case "QUANDO":
                text = "QUANDO SI PUO’ RICHIEDERE LA CIE"
            case "CHI":
                text = "CHI PUO’ RICHIEDERE LA CIE"
            case "CARATTERISTICHE":
                text = "CARATTERISTICHE DEL DOCUMENTO"
            case "COSTI":
                text = "EMISSIONE|ESENZIONE"
            case "PAGAMENTO":
                text = "MODALITA' DI PAGAMENTO"
            case "COMUNITARI":
                text = "CITTADINI NON COMUNITARI"
            case "ESPATRIO":
                text = "VALIDITA’ PER L’ESPATRIO"
            case "INFO":
                text = "INFO"
    elif context is not None:
        match context:
            case "CIE_COME":
                context = "accordion_come_5469203"
                text = "DOCUMENTI DA ALLEGARE|CITTADINI NON COMUNITARI|PIN/PUK|PORTALE CIE"
            case "CIE_COSTI":
                context = "accordion_costi_5469203"
            case "CIE_TEMPI":
                context = "accordion_tempi_5469203"
            case "CIE_DOVE":
                context = "accordion_dove_5469203"
            case "CIE_INFO":
                context = "accordion_descrizione_servizio_5469203"
    else:
        printText = False

    if text != "INFO":
        Cie_Soup = soup.findAll('div', class_="accordion-body collapse in")
        # se la variabile text è vuota, stampa tutte le info riguardo la CDI, altrimenti
        # ricerca tutti i DIV di quella classe
        for i in Cie_Soup:
            if context is not None:
                if i["id"] == context:
                    printText = True
                else:
                    printText = False
            try:
                # analizza il primo figlio di ogni DIV trovato (il primo figlio sarà un altro DIV
                for t in i.children:
                    try:
                        # è la lista dei figli del secondo DIV
                        for k in t.children:
                            if k.name is not None:
                                # verifica sul numero di figli
                                has_child = len(k.findAll()) != 0
                                # se il tag ha figli allora cerca e stampa i figli
                                if has_child:
                                    # è la lista di figli di ogni TAG all'interno di DIV
                                    for z in k.children:
                                        if z.name is not None:
                                            # se è una scritta in stampatello senza tag che la precedono allora la stampo, la tolgo dal tag superiore, stampo il testo del tag padre e vado a capo
                                            if z.text.isupper() and len(z.findPreviousSiblings()) == 0:
                                                if context is None or context == "accordion_come_5469203":
                                                    if text is not None:
                                                        if re.match(text, z.text):
                                                            printText = True
                                                        else:
                                                            printText = False
                                                    else:
                                                        printText = True
                                                if printText is True:
                                                    fulfillmentText += "\n"
                                                    fulfillmentText += z.text
                                                    fulfillmentText += "\n"
                                                    fulfillmentText += k.text.replace(str(z.text), "")
                                                    fulfillmentText += "\n"
                                                    break  # esco per evitare duplicati

                                            # se il tag è 'li' (elenco puntato), allora metti un a capo
                                            elif z.name == "li" and printText is True:
                                                fulfillmentText += "\n"
                                                fulfillmentText += "- "
                                                fulfillmentText += z.text
                                                fulfillmentText += "\n"
                                            # se il tag non ha fratelli precedenti e successivi, allora stampa prima il testo del padre e poi il proprio (ESCLUSIONE DUPLICATI)
                                            elif len(z.findPreviousSiblings()) == 0 and len(z.findNextSiblings()) == 0:
                                                if printText is True:
                                                    fulfillmentText += k.text.replace(str(z.text), "")
                                                    fulfillmentText += z.text
                                            else:
                                                if printText is True:
                                                    fulfillmentText += z.text
                                                    break  # evita duplicati


                                # se il tag non ha figli, stampa il suo testo
                                else:
                                    if printText is True:
                                        fulfillmentText += k.text
                                        fulfillmentText += "\n"
                    except:
                        continue
            except:
                continue
    else:
        fulfillmentText = "Cosa ti interessa sapere riguardo la CIE (carta di identità " \
                          "elettronica)?:\n\n - Chi può richiedere la CIE\n - Quando poter richiedere la CIE\n - Come " \
                          "richiedere la CIE (procedimento)\n - Documenti necessari per richiesta CIE\n - " \
                          "Richiedere un duplicato della CIE\n - CIE per cittadini NON comunitari\n - Validità della " \
                          "CIE per l'espartrio\n - Info su PIN e PUK\n - Esperimersi sulla donazione degli    " \
                          "organi\n - " \
                          "Portale CIE\n - Costi della CIE\n - Come pagare la CIE\n - Tempi di arrivo CIE\n - Durata " \
                          "validità CIE "

    if text is not None:
        if text == "UFFICIO ANAGRAFE CENTRALE":
            fulfillmentText = "UFFICIO ANAGRAFE CENTRALE - CARTE D'IDENTITÀ\n\nNumero di telefono:\n080/5773357 - " \
                              "3304 - 3782\nNumero di Email PEC:\n " \
                              "ci.anagrafe.comunebari@pec.rupar.puglia.it\n\nORARI DI APERTURA AL " \
                              "PUBBLICO:\n\nLunedì: 9.00 - 12.00\nMartedì: 9.00 - 12.00\nMercoledì: 9.00 - " \
                              "12.00\nGiovedì: 9.00 - 12.00 e 15.30 - 17.00\nVenerdì: 9.00 - 12.00\nSabato: " \
                              "chiuso\n\nIndirizzo: Corso Vittorio Veneto,4 70122 Bari "
        elif text == "UFFICIO ANAGRAFE SAN PASQUALE":
            fulfillmentText = "UFFICIO ANAGRAFE/STATO CIVILE DECENTRATO - DELEGAZIONE CARRASSI-SAN " \
                              "PASQUALE\n\nNumero di telefono :  \n080/5772491 080/5772493  080/5772496  " \
                              "080/5772497\nNumero di Email PEC " \
                              ":\ndelegazione.carrassi.comunebari@pec.rupar.puglia.it\n\nPosta elettronica :\n " \
                              "delegazione.oriente@comune.bari.it\n\nOrari di apertura al pubblico :\nLunedì : " \
                              "9.00 - 12.30\nMartedì : 9.00 - 12.30\nMercoledì : 9.00 - 12.30\nGiovedì : 9.00 - " \
                              "13.00 e 16.00 - 17.30\nVenerdì : 9.00 - 12.30\nSabato : chiuso\n\nIndirizzo : Via " \
                              "Luigi Pinto,3 70125 Bari "

    return fulfillmentText


# scraping sulle info inerenti al cambio di residenza
def CR_scraping(url, text, context):
    fulfillmentText = ""
    soup = parsing_html(url)

    # flag utile per la gestione degli allegati
    allegati = False
    if text is not None:
        # flag per la gestione delle stampe
        printText = False
        match text:
            case "ALLEGARE":
                text = "DOCUMENTI DA ALLEGARE"
            case "STRANIERI":
                text = "CITTADINI STRANIERI"
            case "MINORI":
                text = "MINOR"
    elif context is not None:
        match context:
            case "CR_COSA":
                # COSA del cambio di residenza
                context = "accordion_descrizione_servizio_11639056"
            case "CR_COME":
                # COME del cambio di residenza
                context = "accordion_come_11639056"
                printText = True
            case "CR_DOVE":
                # DOVE del cambio di residenza
                context = "accordion_dove_11639056"
            case "CR_COSTI":
                # COSTI cambio di resistenza
                context = "accordion_costi_11639056"
            case "CR_TEMPI":  # da implementare poiche dinamico
                # TEMPI del cambio di residenza
                context = "accordion_tempi_11639056"
            case "CR_ALLEGATI":
                allegati = True
    else:  # se text e context sono nulli, stampa tutte le informazioni in pagina
        printText = True

    if allegati is False:
        CR_Soup = soup.findAll('div', class_="accordion-body collapse in")
        # se la variabile text è vuota, stampa tutte le info riguardo la CDI, altrimenti
        # ricerca tutti i DIV di quella classe
        for i in CR_Soup:
            if context is not None:
                if i["id"] == context:
                    printText = True
                else:
                    printText = False
            try:
                # analizza il primo figlio di ogni DIV trovato (il primo figlio sarà un altro DIV
                for t in i.children:
                    try:
                        # è la lista dei figli del secondo DIV
                        for k in t.children:
                            if k.name is not None:
                                # verifica sul numero di figli
                                has_child = len(k.findAll()) != 0
                                # se il tag ha figli allora cerca e stampa i figli
                                if has_child:
                                    # è la lista di figli di ogni TAG all'interno di DIV
                                    for z in k.children:
                                        if z.name is not None:
                                            # se è una scritta in stampatello senza tag che la precedono allora la stampo, la tolgo dal tag superiore, stampo il testo del tag padre e vado a capo
                                            if z.text.isupper() and len(
                                                    z.findPreviousSiblings()) == 0 and z.text != "N.B.":
                                                if context is None:
                                                    if text is not None:
                                                        if text in z.text:
                                                            printText = True
                                                        else:
                                                            printText = False
                                                    else:
                                                        printText = True
                                                if printText is True:
                                                    fulfillmentText += "\n"
                                                    fulfillmentText += z.text
                                                    # se il titolo in maiuscolo contiene fratelli all'interno dello stesso TAG, allora mette uno spazio per andare a capo
                                                    if len(z.findNextSiblings()) != 0:
                                                        fulfillmentText += "\n"
                                                    fulfillmentText += k.text.replace(str(z.text), "")
                                                    fulfillmentText += "\n"
                                                    break  # esco per evitare duplicati

                                            # se il tag è 'li' (elenco puntato), allora metti un a capo
                                            elif z.name == "li" and printText is True:
                                                fulfillmentText += "- "
                                                fulfillmentText += z.text
                                                fulfillmentText += "\n"
                                            # se il tag non ha fratelli precedenti e successivi, allora stampa prima il testo del padre e poi il proprio (ESCLUSIONE DUPLICATI)
                                            elif (len(z.findPreviousSiblings()) == 0 and len(
                                                    z.findNextSiblings()) == 0):
                                                if printText is True:
                                                    fulfillmentText += k.text.replace(str(z.text), "")
                                                    fulfillmentText += z.text
                                                    fulfillmentText += "\n"
                                            else:  # se il tag ha più figli che però non rientrano in uno dei casi particolari precedenti, allora stampa il padre
                                                if printText is True:
                                                    fulfillmentText += k.text
                                                    fulfillmentText += "\n"
                                                    break  # evita duplicati


                                # se il tag non ha figli, stampa il suo testo
                                else:
                                    if printText is True:
                                        fulfillmentText += k.text
                                        fulfillmentText += "\n"
                    except:
                        continue
            except:
                continue
    else:
        # stampa tutti i dati inerenti ai moduli per cambio di residenza
        CR_Soup = soup.findAll('a', class_="inverted-link")
        for links in CR_Soup:
            print(links.text + ": \n - " + "https://www.comune.bari.it" + links["href"] + "\n")

    if text is not None:
        if text == "UFFICIO ANAGRAFE CENTRALE":
            fulfillmentText = "UFFICIO ANAGRAFE CENTRALE - DICHIARAZIONI DI RESIDENZA E CAMBI DI DOMICILIO\n\nNumero " \
                              "di telefono:\n080/5773332 - 3333 - 3355 - 3376 - 3344 - 3314 - 3729 - 6450 - 2489 - " \
                              "4636 - 4606\nNumero di fax:\n080/5773359\nNumero di Email " \
                              "PEC:\nanagrafe.comunebari@pec.rupar.puglia.it\nPosta elettronica " \
                              ":\nufficio.dichiarazioniresidenza@comune.bari.it\n\nIndirizzo : Corso Vittorio Veneto," \
                              "4 70122 Bari "

    if context == "accordion_come_11639056":
        match1 = re.search("(?sm)al fine di (.*?)(?=[\r\n]*\w*2\) TRASFERIMENTO DI NUCLEO)",
                           fulfillmentText, re.IGNORECASE)
        fulfillmentText = match1.group(0)

    if context == "accordion_costi_11639056":
        fulfillmentText = "COSTO CAMBIO DI RESIDENZA:\nGratuito"

    if context == "INFO":
        fulfillmentText = "Cosa vuoi sapere nello specifico?\n - Cos'è il C.D.R.(cambio di residenza)\n - Come " \
                          "cambiare residenza\n - Documenti da allegare al C.D.R.\n - Cambio residenza cittadini " \
                          "stranieri\n - Costo del C.D.R.\n - Costo del C.D.R.\n - Tempi necessari per il C.D.R.\n - " \
                          "Moduli per il C.D.R.\n - Orari di apertura ufficio anagrafe "

    return fulfillmentText


def dib_location_scraping(url):
    fulfillmentText = ''
    soup = parsing_html(url)

    # conteggio paragrafi utili
    count = 0

    for i in soup.find_all("div"):
        try:
            if i["id"] == "content":
                for j in i.children:
                    try:
                        if j["id"] == "content-core":
                            for k in j.children:
                                try:
                                    if k["id"] == "parent-fieldname-text-4b73d87057334c6b977eb1588e14a4fd":
                                        for z in k.descendants:
                                            try:
                                                if (isinstance(z, str)):
                                                    fulfillmentText += z
                                                    fulfillmentText = re.sub("\. ", ".\n", fulfillmentText)
                                                    count += 1
                                                    # mi basta fino a via Orabona, quindi i primi 4 paragrafi
                                                if count >= 3:
                                                    break
                                            except:
                                                continue
                                except:
                                    continue
                    except:
                        continue
        except:
            continue
    return fulfillmentText


@app.route("/webhooks", methods=["POST"])
def webhooks():
    req = request.get_json(silent=True, force=True)
    fulfillmentText = ""

    # processo la query che arriva in JSON
    query_result = req.get('queryResult')

    if query_result.get("intent").get("displayName") == "ComeRaggiungerci":

        if query_result["parameters"]["SedeTaranto"] != "":
            fulfillmentText = "Sede di Taranto (ICD):\n\nex II facoltà di Scienze, piano terra  Via A. De Gasperi, Quartiere Paolo VI 74123 Taranto"
        else:
            fulfillmentText = dib_location_scraping(URL_DIB_LOCATION)
    # intent della carta di identità (CIE)
    elif query_result.get("intent").get("displayName") == "CIE_INFO":
        fulfillmentText = cie_scraping(URL_CIE, "INFO", None)
    elif query_result.get("intent").get("displayName") == "CIE_CHI_RICHIEDERE":
        fulfillmentText = cie_scraping(URL_CIE, "CHI", None)
    elif query_result.get("intent").get("displayName") == "CIE_QUANDO_RICHIEDERE":
        fulfillmentText = cie_scraping(URL_CIE, "QUANDO", None)
    elif query_result.get("intent").get("displayName") == "CIE_DOCUMENTI":
        fulfillmentText = cie_scraping(URL_CIE, "DOCUMENTI", None)
    elif query_result.get("intent").get("displayName") == "CIE_DUPLICATO":
        fulfillmentText = cie_scraping(URL_CIE, "DUPLICATO", None)
    elif query_result.get("intent").get("displayName") == "CIE_ESPATRIO":
        fulfillmentText = cie_scraping(URL_CIE, "ESPATRIO", None)
    elif query_result.get("intent").get("displayName") == "CIE_PIN":
        fulfillmentText = cie_scraping(URL_CIE, "PIN/PUK", None)
    elif query_result.get("intent").get("displayName") == "CIE_ORGANI":
        fulfillmentText = cie_scraping(URL_CIE, "DONAZIONE", None)
    elif query_result.get("intent").get("displayName") == "CIE2_NON_COMUNITARI":
        fulfillmentText = cie_scraping(URL_CIE, "COMUNITARI", None)
    elif query_result.get("intent").get("displayName") == "CIE_PROCESSO":
        fulfillmentText = cie_scraping(URL_CIE, None, "CIE_COME")
    elif query_result.get("intent").get("displayName") == "CIE_TEMPI":
        fulfillmentText = cie_scraping(URL_CIE, None, "CIE_TEMPI")
    elif query_result.get("intent").get("displayName") == "CIE_COSTI":
        fulfillmentText = cie_scraping(URL_CIE, "COSTI", None)
    elif query_result.get("intent").get("displayName") == "CIE_PAGAMENTO":
        fulfillmentText = cie_scraping(URL_CIE, "PAGAMENTO", None)

    # intent del cambio di residenza (CR)
    elif query_result.get("intent").get("displayName") == "CR_INFO":
        fulfillmentText = CR_scraping(URL_CR, "INFO", None)
    elif query_result.get("intent").get("displayName") == "CR_COSA":
        fulfillmentText = CR_scraping(URL_CR, None, "CR_COSA")
    elif query_result.get("intent").get("displayName") == "CR_COME":
        fulfillmentText = CR_scraping(URL_CR, None, "CR_COME")
    elif query_result.get("intent").get("displayName") == "CR_DOCUMENTI":
        fulfillmentText = CR_scraping(URL_CR, "ALLEGARE", None)
    elif query_result.get("intent").get("displayName") == "CR_STRANIERI":
        fulfillmentText = CR_scraping(URL_CR, "STRANIERI", None)
    elif query_result.get("intent").get("displayName") == "CR_MINORI":
        fulfillmentText = CR_scraping(URL_CR, "MINORI", None)
    elif query_result.get("intent").get("displayName") == "CR_DOVE":
        fulfillmentText = CR_scraping(URL_CR, None, "CR_DOVE")
    elif query_result.get("intent").get("displayName") == "CR_COSTI":
        fulfillmentText = CR_scraping(URL_CR, None, "CR_COSTI")
    elif query_result.get("intent").get("displayName") == "CR_TEMPI":
        fulfillmentText = CR_scraping(URL_CR, None, "CR_TEMPI")
    elif query_result.get("intent").get("displayName") == "CR_ALLEGATI":
        fulfillmentText = CR_scraping(URL_CR, None, "CR_ALLEGATI")
    # if fulfillmentText == "":
    #    fulfillmentText = "Ho ancora tanto da imparare, puoi ripetere?"

    # se c'è una risposta, la ritorno sempre in formato JSON
    return {
        "fulfillmentText": fulfillmentText,
        "displayText": '25',
        "source": "webhookdata"
    }

# app.run(debug=True, port=5000)
