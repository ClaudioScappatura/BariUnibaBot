import os, sys
import unicodedata
from bs4 import BeautifulSoup
import re
import requests
from flask import Flask, request

# URL Carta di identità elettronica
URL_CIE = "https://www.comune.bari.it/web/egov/-/carta-d-identita-elettronica-cie-"

# URL cambio di residenza
URL_CR = "https://www.comune.bari.it/web/egov/-/cambio-di-residenza-con-provenienza-da-altro-comune-o-stato-estero-e-cambio-di-abitazione-bari-su-bari-"

# URL Tari
URL_TARI = "https://www.comune.bari.it/web/egov/-/dichiarazione-tari"

# URL certificato di residenza
URL_CDR = "https://www.comune.bari.it/web/egov/-/certificato-di-residenza"


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
                                            elif len(z.findPreviousSiblings()) == 0 and len(z.findNextSiblings()) == 0:
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

    return fulfillmentText


# scraping sulle info inerenti alla TARI
def TARI_scraping(url, text, context):
    fulfillmentText = ""
    soup = parsing_html(url)
    printText = False

    # flag utile per la gestione degli allegati
    allegati = False
    if text is not None:
        # flag per la gestione delle stampe
        printText = False
        match text:
            case "ALLEGARE":
                text = "DOCUMENTI DA ALLEGARE"
    elif context is not None:
        match context:
            case "TARI_COSA":
                # COSA della Tari
                context = "accordion_descrizione_servizio_13941714"
            case "TARI_COME":
                # COME della TARI
                context = "accordion_come_13941714"
            case "TARI_DOVE":  # PROBLEMA testo dinamico
                # DOVE della tari
                context = "accordion_dove_13941714"
            case "TARI_COSTI":
                # COSTI della Tari
                context = "accordion_costi_13941714"
            case "TARI_TEMPI":  # da implementare poiche dinamico
                # TEMPI della Taro
                context = "accordion_tempi_13941714"
            case "TARI_ALLEGATI":
                allegati = True
    else:  # se text e context sono nulli, stampa tutte le informazioni in pagina
        printText = True

    if allegati is False:
        TARI_Soup = soup.findAll('div', class_="accordion-body collapse in")
        # se la variabile text è vuota, stampa tutte le info riguardo la CDI, altrimenti
        # ricerca tutti i DIV di quella classe
        for i in TARI_Soup:
            if context is not None:
                if i["id"] == context:
                    printText = True
                else:
                    printText = False
            try:
                # analizza il primo figlio di ogni DIV trovato (il primo figlio sarà un altro DIV
                for t in i.children:
                    try:
                        if len(t.findAll()) == 0 and printText is True:
                            fulfillmentText += t.text
                            fulfillmentText += "\n"
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
                                            elif len(z.findPreviousSiblings()) == 0 and len(z.findNextSiblings()) == 0:
                                                if printText is True:  # PROBLEMA di stampa quando il tag es.'p' possiede del testo senza tag, poi la presenza di un tag es.strong e poi nuovamente testo senza tag. Verrà stampato il testo con ordine invertito
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
        TARI_Soup = soup.findAll('a', class_="inverted-link")
        for links in TARI_Soup:
            print(links.text + ": \n - " + "https://www.comune.bari.it" + links["href"] + "\n")

    return fulfillmentText


# scraping sulle info inerenti al certificato di residenza
def CDR_scraping(url, text, context):
    fulfillmentText = ""
    soup = parsing_html(url)
    printText = False
    # flag utile per la gestione degli allegati
    allegati = False
    if text is not None:
        # flag per la gestione delle stampe
        printText = False
        match text:
            case "VALIDITA":
                text = "VALIDITA"
            case "EDICOLA":
                text = "CERTIFICATI IN EDICOLA"
            case "ESENZIONE":
                text = "CASI DI ESENZIONE"
    elif context is not None:
        match context:
            case "CDR_COSA":
                # COSA del certificato di residenza
                context = "accordion_descrizione_servizio_SCHEDA_SERVIZIO_IMPORTED_8868"
            case "CDR_COME":
                # COME del certificato di residenza
                context = "accordion_come_SCHEDA_SERVIZIO_IMPORTED_8868"
            case "CDR_DOVE":
                # DOVE del certificato di residenza
                context = "accordion_dove_SCHEDA_SERVIZIO_IMPORTED_8868"
            case "CDR_COSTI":
                # COSTI certificato di resistenza
                context = "accordion_costi_SCHEDA_SERVIZIO_IMPORTED_8868"
            case "CDR_TEMPI":  # da implementare poiche dinamico
                # TEMPI del certificato di residenza
                context = "accordion_tempi_SCHEDA_SERVIZIO_IMPORTED_8868"
            case "CDR_ALLEGATI":
                allegati = True
    else:  # se text e context sono nulli, stampa tutte le informazioni in pagina
        printText = True

    if allegati is False:
        CDR_Soup = soup.findAll('div', class_="accordion-body collapse in")
        # se la variabile text è vuota, stampa tutte le info riguardo la CDI, altrimenti
        # ricerca tutti i DIV di quella classe
        for i in CDR_Soup:
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

                                            elif z.name == "table" and printText is True:
                                                fulfillmentText += "ATTENZIONE: Per visualizzare la tabella riguardo le esenzioni, visita: "+URL_CDR+"\n"
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
        # stampa tutti i dati inerenti ai moduli per certificato di residenza
        CDR_Soup = soup.findAll('a', class_="inverted-link")
        for links in CDR_Soup:
            print(links.text + ": \n - " + "https://www.comune.bari.it" + links["href"] + "\n")

    # formattazione testo in eccesso
    fulfillmentText = re.sub("   MODALITA’ DI PAGAMENTO    Il pagamento", "\n\nMODALITA’ DI PAGAMENTO\nIl pagamento", fulfillmentText)
    fulfillmentText = re.sub("1. Attraverso i Servizi PagoPA", "\n\n1. Attraverso i Servizi PagoPA\n", fulfillmentText)
    fulfillmentText = re.sub("Certificati rilasciati con bollo    Inserire i", "\n   - Certificati rilasciati con bollo\n\nInserire i", fulfillmentText)
    fulfillmentText = re.sub(" Al termine della procedura sarà possibile pagare:" , "\n Al termine della procedura sarà possibile pagare:\n   -" , fulfillmentText)
    fulfillmentText = re.sub("oppure", "\n  oppure\n   -",fulfillmentText)
    fulfillmentText = re.sub("STAMPA.    In entrambi i casi" , "STAMPA.\n\n In entrambi i casi", fulfillmentText)
    fulfillmentText = re.sub("2. Direttamente presso", "\n\n2. Direttamente presso", fulfillmentText)
    if text == "CASI DI ESENZIONE":
        fulfillmentText = "CASI DI ESENZIONE\nIn caso di esenzione, spetta al soggetto richiedente dichiarare il relativo uso ed indicare la norma di riferimento che dispone il diritto di esenzione, in quanto l’esenzione non può essere presunta dall’operatore del servizio anagrafico.\nDi seguito, si riportano alcuni dei principali casi di esenzione, relativi ai certificati anagrafici, previsti dalle norme vigenti:\n\nATTENZIONE: Per visualizzare la tabella riguardo le esenzioni, visita: https://www.comune.bari.it/web/egov/-/certificato-di-residenza\n\nNOTA BENE: l’utilizzo di certificati rilasciati in esenzione da bolli, per fini diversi da quelli indicati sul certificato, equivale a evasione fiscale e comporta la responsabilità del richiedente, consistente nel pagamento dell’imposta e delle relative sanzioni previste dalle legge."

    return fulfillmentText


# print(cie_scraping(URL_CIE, None, "CDI_DOVE"))
print(cie_scraping(URL_CIE, None, "CDI_COME"))
