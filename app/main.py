import os, sys
import unicodedata
from bs4 import BeautifulSoup
import re
import requests
from flask import Flask, request

app = Flask(__name__)

URL_PROF = "https://www.uniba.it/ricerca/dipartimenti/informatica/dipartimento/personale/docenti-2"
URL_BIBLIO = "https://www.uniba.it/bibliotechecentri/informatica/biblioteca-di-informatica"


def parsing_html(url):
    response = requests.get(url=url)
    response_html = response.text
    return BeautifulSoup(response_html, 'html.parser')

def library_scraping(url):
    fulfillmentText = ""
    soup = parsing_html(url)
    regex = None

    # il testo viene spaziato e viene dato l'accapo secondo la pagina html ottenuta
    fulfillmentText = soup.getText(separator=u'\n')

    # matcha solo il testo di interesse per la biblioteca
    regex = re.search("(?sm)Dove siamo(.*?)(?=[\r\n]*\w*Catalogo)", fulfillmentText, re.IGNORECASE)

    if regex:
        # formattazione varia
        fulfillmentText = regex.group(0)
        fulfillmentText = re.sub("(?sm)“(.*?)Alberto Manguel", "", fulfillmentText)
        fulfillmentText = re.sub("SERVIZI BIBLIOTECARI", "\nSERVIZI BIBLIOTECARI", fulfillmentText)
        fulfillmentText = re.sub("MISURE DI SICUREZZA", "\nMISURE DI SICUREZZA", fulfillmentText)
        fulfillmentText = re.sub("Referente di Biblioteca:", "\nReferente di Biblioteca", fulfillmentText)
        fulfillmentText = re.sub("Coordinatore Scientifico:", "\nCoordinatore Scientifico:", fulfillmentText)
    return fulfillmentText

@app.route("/", methods=["POST"])
def webhooks():
    req = request.get_json(silent=True, force=True)
    fulfillmentText = ""

    # processo la query che arriva in JSON
    query_result = req.get('queryResult')

    if query_result.get("intent").get("displayName") == "Biblioteca":
        fulfillmentText = library_scraping(URL_BIBLIO)

    # se c'è una risposta, la ritorno sempre in formato JSON
    return {
        "fulfillmentText": fulfillmentText,
        "displayText": '25',
        "source": "webhookdata"
    }
