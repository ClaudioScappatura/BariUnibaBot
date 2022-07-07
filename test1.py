import os, sys
import unicodedata
from bs4 import BeautifulSoup
import re
import requests
from flask import Flask, request

URL_CIE = "https://www.comune.bari.it/web/egov/-/carta-d-identita-elettronica-cie-"


def parsing_html(url):
    response = requests.get(url=url)
    response_html = response.text
    return BeautifulSoup(response_html, 'html.parser')


# craping sulle info inerenti alla CDI elettronica
def cie_scraping(url, text):
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
            case "PROCEDURA":
                text = "PROCEDURA DI RILASCIO"
            case "CARATTERISTICHE":
                text = "CARATTERISTICHE DEL DOCUMENTO"
    else:
        printText = True

    # se la variabile text è vuota, stampa tutte le info riguardo la CDI, altrimenti
    for i in soup.find('div', class_="accordion-body collapse in"):
        try:
            # è la lista dei figli del primo DIV
            for k in i.children:
                if k.name is not None:
                    # verifica sul numero di figli
                    has_child = len(k.findAll()) != 0
                    # se il tag ha figli allora cerca e stampa i figli
                    if has_child:
                        # è la lista di figli di ogni TAG all'interno di DIV
                        for z in k.children:
                            if z.name is not None:
                                # se è una scritta in stampatello, la stampo, la tolgo dal tago superiore, stampo il testo del tag padre e vado a capo
                                if z.text.isupper():
                                    if text is not None:
                                        printText = False
                                    else:
                                        printText = True
                                    if text is not None and text in z.text:
                                        printText = True
                                    if printText is True:
                                        fulfillmentText += "\n"
                                        fulfillmentText += z.text
                                        fulfillmentText += "\n"
                                        fulfillmentText += k.text.replace(str(z.text), "")
                                        fulfillmentText += "\n"

                                # se il tag è 'li' (elenco puntato), allora metti un a capo
                                elif z.name == "li" and printText is True:
                                    fulfillmentText += "- "
                                    fulfillmentText += z.text
                                    fulfillmentText += "\n"

                    # se il tag non ha figli, stampa il suo testo
                    else:
                        if printText is True:
                            fulfillmentText += k.text
                            fulfillmentText += "\n"
        except:
            continue

    return fulfillmentText


cus = cie_scraping(URL_CIE, None)
print(cus)
