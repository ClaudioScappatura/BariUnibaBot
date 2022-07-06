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
def cie_scraping(url):
    fulfillmentText = ""
    soup = parsing_html(url)

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
                                    fulfillmentText += "\n"
                                    fulfillmentText += z.text
                                    fulfillmentText += "\n"
                                    fulfillmentText += k.text.replace(str(z.text), "")
                                    fulfillmentText += "\n"

                                # se il tag è 'li' (elenco puntato), allora metti un a capo
                                elif z.name == "li":
                                    fulfillmentText += "- "
                                    fulfillmentText += z.text
                                    fulfillmentText += "\n"

                    # se il tag non ha figli, stampa il suo testo
                    else:
                        fulfillmentText += k.text
                        fulfillmentText += "\n"

        except:
            continue

    return fulfillmentText


cus = cie_scraping(URL_CIE)
print(cus)


