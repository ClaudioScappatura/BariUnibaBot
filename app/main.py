import os, sys
import unicodedata
from bs4 import BeautifulSoup
import re
import requests
from flask import Flask, request

app = Flask(__name__)

# intent ricerca personale:
# url professori
URL_PROF = "https://www.uniba.it/ricerca/dipartimenti/informatica/dipartimento/personale/docenti-2"
# url tecnici
URL_SEGRET = "https://www.uniba.it/ricerca/dipartimenti/informatica/dipartimento/personale/tecniciamministrativi"
# url tecnici studenti stranieri
URL_SEGRET_FOREIGN = "https://www.uniba.it/ricerca/dipartimenti/informatica/instructions-for-the-eligibility-for-the-master-degree-in-computer-science"
# parsing per le informazioni del personale (docenti + segretari)

# url intent biblioteca
URL_BIBLIO = "https://www.uniba.it/bibliotechecentri/informatica/biblioteca-di-informatica"

# url intent Convenzioni
URL_RESOURCES = "https://www.uniba.it/ricerca/dipartimenti/informatica"

# url intent Corsi di laurea
URL_CDL = "https://www.uniba.it/ricerca/dipartimenti/informatica/didattica/corsi-di-laurea/corsi-di-laurea"

# url intent studenti stranieri
URL_STUD_FOREIGN = "https://www.uniba.it/ricerca/dipartimenti/informatica/instructions-for-the-eligibility-for-the-master-degree-in-computer-science"

# url intent raggiungimento
URL_DIB_LOCATION = "https://www.uniba.it/ricerca/dipartimenti/informatica/dipartimento/come-raggiungerci"

# url intent Laboratorio tesisti
URL_LAB_GRAD = "https://www.uniba.it/ricerca/dipartimenti/informatica/manuzio/laboratorio-manuzio"

# url intent Tirocinio
URL_APPRENTICESHIP = "https://www.uniba.it/ricerca/dipartimenti/informatica/didattica/tirocini/tirocini-informatica"

# url intent Erasmus+
URL_ERASMUS = "https://www.uniba.it/ricerca/dipartimenti/informatica/didattica/erasmus/erasmus"

# url intent Orientamento
URL_UNI_RESEARCH = "https://www.uniba.it/ricerca/dipartimenti/informatica/tutorato/orientamento-e-tutorato-1"

# url intent carta di identità
URL_CIE = "https://www.comune.bari.it/web/egov/-/carta-d-identita-elettronica-cie-"


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

    elif query_result.get("intent").get("displayName") == "CIE_INFO":
        fulfillmentText = cie_scraping(URL_CIE, "INFO", None)
    elif query_result.get("intent").get("displayName") == "CIE1_CHI_RICHIEDERE":
        fulfillmentText = cie_scraping(URL_CIE, "CHI", None)
    elif query_result.get("intent").get("displayName") == "CIE1_QUANDO_RICHIEDERE":
        fulfillmentText = cie_scraping(URL_CIE, "QUANDO", None)
    elif query_result.get("intent").get("displayName") == "CIE2_DOCUMENTI":
        fulfillmentText = cie_scraping(URL_CIE, "DOCUMENTI", None)
    elif query_result.get("intent").get("displayName") == "CIE2_DUPLICATO":
        fulfillmentText = cie_scraping(URL_CIE, "DUPLICATO", None)
    elif query_result.get("intent").get("displayName") == "CIE2_ESPATRIO":
        fulfillmentText = cie_scraping(URL_CIE, "ESPATRIO", None)
    elif query_result.get("intent").get("displayName") == "CIE2_PIN":
        fulfillmentText = cie_scraping(URL_CIE, "PIN/PUK", None)
    elif query_result.get("intent").get("displayName") == "CIE2_ORGANI":
        fulfillmentText = cie_scraping(URL_CIE, "DONAZIONE", None)
    elif query_result.get("intent").get("displayName") == "CIE2_NON_COMUNITARI":
        fulfillmentText = cie_scraping(URL_CIE, "COMUNITARI", None)
    elif query_result.get("intent").get("displayName") == "CIE2_PROCESSO":
        fulfillmentText = cie_scraping(URL_CIE, None, "CIE_COME")
    elif query_result.get("intent").get("displayName") == "CIE_TEMPI":
        fulfillmentText = cie_scraping(URL_CIE, None, "CIE_TEMPI")
    elif query_result.get("intent").get("displayName") == "CIE_COSTI":
        fulfillmentText = cie_scraping(URL_CIE, "COSTI", None)
    elif query_result.get("intent").get("displayName") == "CIE_PAGAMENTO":
        fulfillmentText = cie_scraping(URL_CIE, "PAGAMENTO", None)


    # if fulfillmentText == "":
    #    fulfillmentText = "Ho ancora tanto da imparare, puoi ripetere?"

    # se c'è una risposta, la ritorno sempre in formato JSON
    return {
        "fulfillmentText": fulfillmentText,
        "displayText": '25',
        "source": "webhookdata"
    }

# app.run(debug=True, port=5000)
