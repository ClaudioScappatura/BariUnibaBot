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
            case "COME":
                context = "accordion_come_5469203"
            case "COSTI":
                context = "accordion_costi_5469203"
            case "TEMPI":
                context = "accordion_tempi_5469203"
            case "DOVE":
                context = "accordion_dove_5469203"
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
        # NON FUNZIONA PORCO GIUDA
        if context is not None and context == "accordion_dove_5469203":
            fulfillmentText = ""
            soup = parsing_html(url)
            soup1 = soup.findAll('div', class_="accordion-body collapse in")
            for span1 in soup1:
                if span1["id"] == "dove-rest-content":
                    for span2 in span1.children:
                        print(span2)

    return fulfillmentText


print(cie_scraping(URL_CIE, "QUANDO", None))
