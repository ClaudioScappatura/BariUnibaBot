import os, sys
import unicodedata
from bs4 import BeautifulSoup
import re
import requests
from flask import Flask, request

app = Flask(__name__)

# lunghezza di nome e cognome di prof e collaboratori previsti
NAME_LEN = 3
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
            case "PROCEDURA":
                text = "PROCEDURA DI RILASCIO"
            case "QUANDO":
                text = "QUANDO SI PUO’ RICHIEDERE LA CIE"
            case "CHI":
                text = "CHI PUO’ RICHIEDERE LA CIE"
            case "CARATTERISTICHE":
                text = "CARATTERISTICHE DEL DOCUMENTO"
    elif context is not None:
        match context:
            case "CDI_COME":
                context = "accordion_come_5469203"
            case "CDI_COSTI":
                context = "accordion_costi_5469203"
            case "CDI_TEMPI":
                context = "accordion_tempi_5469203"
            case "CDI_DOVE":
                context = "accordion_dove_5469203"
            case "CDI_INFO":
                context = "accordion_descrizione_servizio_5469203"
    else:
        printText = True

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

        # STAMPA SEZIONE ORARI
        # NON FUNZIONA PERCHE PRENDE DATI DA UN DOCUMENTO/DATABASE
        if context is not None and context == "accordion_dove_5469203":
            fulfillmentText = ""
            soup = parsing_html(url)
            res1 = soup.find_all()
            for cus1 in res1:
                print(cus1)

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

    elif query_result.get("intent").get("displayName") == "infoCIE":
        fulfillmentText = cie_scraping(URL_CIE, None, None)

    # if fulfillmentText == "":
    #    fulfillmentText = "Ho ancora tanto da imparare, puoi ripetere?"

    # se c'è una risposta, la ritorno sempre in formato JSON
    return {
        "fulfillmentText": fulfillmentText,
        "displayText": '25',
        "source": "webhookdata"
    }

# app.run(debug=True, port=5000)
