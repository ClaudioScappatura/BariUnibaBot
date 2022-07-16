import os, sys
import unicodedata
import pickle
from bs4 import BeautifulSoup
import re
import requests
from flask import Flask, request

app = Flask(__name__)

# url intent carta di identità
URL_CIE = "https://www.comune.bari.it/web/egov/-/carta-d-identita-elettronica-cie-"

# URL cambio di residenza
URL_CR = "https://www.comune.bari.it/web/egov/-/cambio-di-residenza-con-provenienza-da-altro-comune-o-stato-estero-e-cambio-di-abitazione-bari-su-bari-"

# URL Tari
URL_TARI = "https://www.comune.bari.it/web/egov/-/dichiarazione-tari"

# URL certificato di residenza
URL_CDR = "https://www.comune.bari.it/web/egov/-/certificato-di-residenza"

# URL notizie
URL_NEWS = "https://www.comune.bari.it/web/guest/home"

# URL pagamento sanzioni
URL_SANZ = "https://www.comune.bari.it/web/egov/-/pagamento-delle-sanzioni-per-violazione-al-codice-della-strada-e-iscrizione-a-ruolo"

# URL eventi
URL_EVENT = "https://www.comune.bari.it"

# URL per APP comunali
URL_APPS = "https://www.comune.bari.it/web/egov"


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

    if text != "INFO" and text != "CIE_SANPASQUALE" and text != "CIE_CENTRALE":
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
                          "CIE per l'espatrio\n - Info su PIN e PUK\n - Esprimersi sulla donazione degli " \
                          "organi\n - " \
                          "Portale CIE\n - Costi della CIE\n - Come pagare la CIE\n - Tempi di arrivo CIE\n - Durata " \
                          "validità CIE "

    if text is not None:
        if text == "CIE_CENTRALE":
            fulfillmentText = "UFFICIO ANAGRAFE CENTRALE - CARTE D'IDENTITÀ\n\nNumero di telefono:\n080/5773357 - " \
                              "3304 - 3782\nNumero di Email PEC:\n " \
                              "ci.anagrafe.comunebari@pec.rupar.puglia.it\n\nORARI DI APERTURA AL " \
                              "PUBBLICO:\n\nLunedì: 9.00 - 12.00\nMartedì: 9.00 - 12.00\nMercoledì: 9.00 - " \
                              "12.00\nGiovedì: 9.00 - 12.00 e 15.30 - 17.00\nVenerdì: 9.00 - 12.00\nSabato: " \
                              "chiuso\n\nIndirizzo: Corso Vittorio Veneto,4 70122 Bari "
        elif text == "CIE_SANPASQUALE":
            fulfillmentText = "UFFICIO ANAGRAFE/STATO CIVILE DECENTRATO - DELEGAZIONE CARRASSI-SAN " \
                              "PASQUALE\n\nNumero di telefono :  \n080/5772491 080/5772493  080/5772496  " \
                              "080/5772497\nNumero di Email PEC " \
                              ":\ndelegazione.carrassi.comunebari@pec.rupar.puglia.it\n\nPosta elettronica :\n " \
                              "delegazione.oriente@comune.bari.it\n\nOrari di apertura al pubblico :\nLunedì : " \
                              "9.00 - 12.30\nMartedì : 9.00 - 12.30\nMercoledì : 9.00 - 12.30\nGiovedì : 9.00 - " \
                              "13.00 e 16.00 - 17.30\nVenerdì : 9.00 - 12.30\nSabato : chiuso\n\nIndirizzo : Via " \
                              "Luigi Pinto,3 70125 Bari "

    chat_id = 575403880
    token = '5430259949:AAFWM6G3Nma71fS8SkoeVOQ-Fw_XrSaaVRQ'
    msg = "Send text with photo 😉"
    img_uri = "https://www.ixbt.com/img/n1/news/2022/3/1/62342d1404eb2_large.jpg"
    telegram_msg = requests.get(
        f'https://api.telegram.org/bot{token}/sendPhoto?chat_id={chat_id}&caption={msg}&photo={img_uri}')
    print(telegram_msg)
    print(telegram_msg.content)

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
            case "DOCUMENTI":
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
            fulfillmentText += ("\n" + links.text + ": \n - " + "https://www.comune.bari.it" + links["href"] + "\n")

    if context == "accordion_descrizione_servizio_13941714":
        fulfillmentText += "- http://www.comune.bari.it/web/economia-tasse-e-tributi/tariffe-e-rapporti-con-gli" \
                           "-utenti-tari "

    if context == "accordion_dove_13941714":
        fulfillmentText = "SPORTELLO AL PUBBLICO TARI\n\nNumero di telefono:\n0809645690\n\nNumero di Email " \
                          "PEC:\nriscossionetributi.comunebari@pec.rupar.puglia.it\n\nPosta " \
                          "elettronica:\nrip.tributi@comune.bari.it\n\nORARI DI APERTURA:\nLunedì: 9.00 - " \
                          "12.00\nMartedì : 9.00 - 12.00 / 15.30 - 17.00\nMercoledì : 9.00 - 12.00\nGiovedì : 9.00 - " \
                          "12.00 / 15.30 - 17.00\nVenerdì : 9.00 - 12.00\nSabato : chiuso\n\nIndirizzo : Via Napoli," \
                          "245 70123 Bari "
    if context == "TARI_INFO":
        fulfillmentText = "Cosa ti interessa sapere sulla TARI?\n - Cos'è la TARI\n - Come denunciare/dichiarare la " \
                          "TARI\n - Quali documenti allegare per la TARI\n - Posizione/Orari uffici TARI\n - Costo " \
                          "per la denuncia TARI\n - Tempi per denunciare la TARI\n - Moduli per denuncia TARI\n "

    return fulfillmentText


# scraping sulle info sulle multe
def SANZ_scraping(url, text, context):
    fulfillmentText = ""
    soup = parsing_html(url)
    printText = False

    # flag utile per la gestione degli allegati
    allegati = False
    if text is not None:
        # flag per la gestione delle stampe
        printText = False
    elif context is not None:
        match context:
            case "SANZ_COSA":
                # COSA della Tari
                context = "accordion_descrizione_servizio_SCHEDA_SERVIZIO_IMPORTED_8838"
            case "SANZ_COME":
                # COME della TARI
                context = "accordion_come_SCHEDA_SERVIZIO_IMPORTED_8838"
            case "SANZ_COSTI":
                # COSTI della Tari
                context = "accordion_costi_SCHEDA_SERVIZIO_IMPORTED_8838"
            case "SANZ_TEMPI":  # da implementare poiche dinamico
                # TEMPI della Taro
                context = "accordion_tempi_SCHEDA_SERVIZIO_IMPORTED_8838"
            case "SANZ_ALLEGATI":
                allegati = True
    else:  # se text e context sono nulli, stampa tutte le informazioni in pagina
        printText = True

    if allegati is False:
        SANZ_Soup = soup.findAll('div', class_="accordion-body collapse in")
        # se la variabile text è vuota, stampa tutte le info riguardo la CDI, altrimenti
        # ricerca tutti i DIV di quella classe
        for i in SANZ_Soup:
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

                                            elif z.name == 'a':
                                                if printText is True:  # PROBLEMA di stampa quando il tag es.'p' possiede del testo senza tag, poi la presenza di un tag es.strong e poi nuovamente testo senza tag. Verrà stampato il testo con ordine invertito
                                                    fulfillmentText += k.text.replace(str(z.text), "")
                                                    fulfillmentText += z.text + " :\n"
                                                    fulfillmentText += z["href"]
                                                    fulfillmentText += "\n"

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
        SANZ_Soup = soup.findAll('a', class_="inverted-link")
        for links in SANZ_Soup:
            fulfillmentText += ("\n" + links.text + ": \n - " + "https://www.comune.bari.it" + links["href"] + "\n")

    # if context == "accordion_descrizione_servizio_13941714":
    #    fulfillmentText += "- http://www.comune.bari.it/web/economia-tasse-e-tributi/tariffe-e-rapporti-con-gli" \
    # "-utenti-tari "

    if context == "SANZ_DOVE":
        fulfillmentText = "CORPO DI POLIZIA MUNICIPALE\n\nNumero di telefono:\n080/5491331 Sala Operativa\n\nNumero di Email " \
                          "PEC:\npoliziamunicipale.comunebari@pec.rupar.puglia.it\n\nPosta " \
                          "elettronica:\nrip.poliziamunicipale@comune.bari.it\n\nORARI DI APERTURA:\nLunedì: 9.00 - " \
                          "12.00\nMartedì : 9.00 - 12.00\nMercoledì : 9.00 - 12.00\nGiovedì : 9.00 - " \
                          "12.00\nVenerdì : 9.00 - 12.00\nSabato : 9.00 - 12.00\n\nIndirizzo : Via Paolo Aquilino," \
                          "1 70126 Bari "
    if context == "SANZ_INFO":
        fulfillmentText = "Cosa ti interessa sapere sulle sanzioni/multe?\n - Cosa sono le sanzioni\n - Come " \
                          "pagare le sanzioni\n - Posizione/Orari uffici Polizia\n - Costo delle sanzioni\n" \
                          " - Tempi per pagamento delle sanzioni\n"

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

                                            elif context == "accordion_descrizione_servizio_11639056" and z.text.isupper() and len(
                                                    z.findPreviousSiblings()) == 0 and z.text == "N.B.":
                                                return fulfillmentText
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
        fulfillmentText = ""
        CR_Soup = soup.findAll('a', class_="inverted-link")
        for links in CR_Soup:
            fulfillmentText += ("\n" + links.text + ": \n - " + "https://www.comune.bari.it" + links["href"] + "\n")

    if context == "accordion_dove_11639056":
        fulfillmentText = "UFFICIO ANAGRAFE CENTRALE - DICHIARAZIONI DI RESIDENZA E CAMBI DI DOMICILIO\n\nNumero " \
                          "di telefono:\n080/5773332 - 3333 - 3355 - 3376 - 3344 - 3314 - 3729 - 6450 - 2489 - " \
                          "4636 - 4606\n\nNumero di fax:\n080/5773359\n\nNumero di Email " \
                          "PEC:\nanagrafe.comunebari@pec.rupar.puglia.it\n\nPosta elettronica " \
                          ":\nufficio.dichiarazioniresidenza@comune.bari.it\n\nIndirizzo : Corso Vittorio Veneto," \
                          "4 70122 Bari "

    if context == "accordion_come_11639056":
        fulfillmentText = CR_replace(fulfillmentText)

    if context == "accordion_costi_11639056":
        fulfillmentText = "COSTO CAMBIO DI RESIDENZA:\nGratuito"

    if context == "CR_INFO":
        fulfillmentText = "Cosa vuoi sapere nello specifico?\n - Cos'è il C.D.R.(cambio di residenza)\n - Entro quanto richiedere il C.D.R.\n - Come " \
                          "effettuare il C.D.R.\n - Documenti da allegare al C.D.R.\n - Cambio residenza cittadini " \
                          "stranieri\n - Costo del C.D.R.\n - Tempi necessari per il C.D.R.\n - " \
                          "Moduli per il C.D.R.\n - Orari di apertura ufficio anagrafe "

    return fulfillmentText


def CR_replace(fulfillmentText):
    fulfillmentText = fulfillmentText.replace("1) CITTADINI STRANIERI", "")
    fulfillmentText = fulfillmentText.replace("- Il cittadino di uno Stato non appartenente all'Unione Europea "
                                              "deve allegare la documentazione indicata nell' allegato A) del "
                                              "modulo ministeriale.", "")
    fulfillmentText = fulfillmentText.replace("- Il cittadino di uno Stato appartenente all'Unione Europea deve "
                                              "allegare la documentazione indicata nell' allegato B) del modulo "
                                              "ministeriale.", "")
    fulfillmentText = fulfillmentText.replace(
        "- presentandosi agli sportelli dedicati presso (N.B. questa modalità è temporaneamente sospesa) - l’Anagrafe Centrale, in corso Vittorio Veneto n. 4, attivo dal lunedì al venerdì dalle 9,00 alle 12,00 (nell’orario mattutino lo sportello accoglierà un massimo di 20 utenti) ed il giovedì anche di pomeriggio dalle ore 15,30 alle 17,00 (N.B. nell’orario pomeridiano lo sportello accoglierà un massimo di 10 utenti) - la Delegazione Oriente (Carrassi) in via Luigi Pinto n. 3, dal lunedì al venerdì dalle ore 9,00 alle 12,00, per un un massimo di 10 utenti.  Per usufruire di tale servizio non è richiesta la prenotazione. Il diretto interessato deve recarsi in loco con documentazione e modulistica necessaria, che varia in base alle caratteristiche del medesimo cambio di residenza (a che titolo si occupa il nuovo appartamento, quante persone si spostano, ecc). Per ulteriori informazioni è consigliabile contattare l’URP;\n",
        "")
    fulfillmentText = fulfillmentText.replace(
        "Nel caso di: iscrizione anagrafica in una convivenza (collegi, caserme, ecc) (consulta scheda dedicata) -  cittadino senza fissa dimora (scarica il modulo) – cambio di residenza con delega (scarica il modulo di delega)  è necessario presentarsi presso l'Anagrafe Centrale ed utilizzare la modulistica dedicata.\n",
        "")
    fulfillmentText = fulfillmentText.replace(
        "In ogni caso la persona interessata o un delegato deve presentarsi agli sportelli dell'anagrafe centrale o delle delegazioni di Oriente e Carbonara, con la modulistica compilata e sottoscritta da tutti i componenti del nucleo familiare maggiorenni, completo di tutti gli allegati. La modulistica è disponibile presso tutti gli uffici anagrafici (sede centrale e delegazioni), presso gli sportelli URP e scaricabile in fondo alla presente scheda.",
        "")
    fulfillmentText = fulfillmentText.replace(
        "In seguito all’approvazione del D.L. 47/2014 per la lotta all’occupazione abusiva, il richiedente deve dichiarare il titolo (proprietà, locazione, comodato, etc.) in base al quale occupa legittimamente l’abitazione (pagina 4 del modello ministeriale).  Qualora il dichiarante non fosse in possesso di un valido titolo di occupazione dell’alloggio o in caso di aggregazione a nuclei familiari già residenti, il proprietario dell’immobile deve compilare un’apposita dichiarazione in cui afferma di essere a conoscenza della richiesta di residenza (allegato 2). Il proprietario sottoscrive la dichiarazione, allegando copia del documento di riconoscimento.\n",
        "")
    fulfillmentText = fulfillmentText.replace(
        "Nel caso si tratti di , occorrerà presentare il titolo di assegnazione dell’alloggio o l’autorizzazione all’ampliamento del nucleo familiare rilasciati dall’Ente gestorealloggi di edilizia popolare",
        "")
    fulfillmentText = fulfillmentText.replace(
        "Nel caso si tratti di un fabbricato di nuova costruzione: \"Ai sensi degli artt. 42e 43 del D.P.R. 223/89 (Regolamento Anagrafico), non appena ultimata la costruzione di un fabbricato e comunque prima che il fabbricato possa essere occupato, il costruttore e/o il proprietario ha l'obbligo di chiedere l'attribuzione del numero civico. Pertanto, al momento dell'iscrizione anagrafica e/o del cambio di abitazione, il numero civico dichiarato deve essere presente nella banca dati toponomastica. Nel caso in cui il numero civico non risulti ufficialmente assegnato dall'Ufficio Toponomastica non si potrà dar corso all'istanza presentata che, quindi, verrà respinta.\"\n",
        "")

    match1 = re.search("(?sm)le comunicazioni per il cambio di residenza/indirizzo(.*?)(?=[\r\n]*\w*2\) "
                       "TRASFERIMENTO DI NUCLEO)",
                       fulfillmentText, re.IGNORECASE)
    fulfillmentText = match1.group(0)
    return fulfillmentText


# scraping sulle info inerenti al certificato di residenza
def CDR_scraping(url, text, context):
    cont = 0
    fulfillmentText = ""
    soup = parsing_html(url)
    printText = False
    pagamento = False
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
            case "PAGAMENTO":
                text = None
                pagamento = True
    elif context is not None:
        match context:
            case "CDR_COSA":
                # COSA del certificato di residenza
                stamp = "È il certificato che attesta l’iscrizione nell’Anagrafe della Popolazione del Comune di Bari.\nQuesto certificato può essere sostituito da una dichiarazione sostitutiva di certificazione o autocertificazione al link:\n - https://www.comune.bari.it/documents/25813/2500240/Dichiarazione+sostitutiva+di+certificazione+multipla.pdf/d9e5020e-d1b7-4acf-985e-f65d736441c3\n"
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
                                            elif "NOTA BENE:" in z.text and context == "accordion_costi_SCHEDA_SERVIZIO_IMPORTED_8868":
                                                return fulfillmentText
                                            elif z.name == "table" and printText is True:
                                                fulfillmentText += "ATTENZIONE: Per visualizzare la tabella riguardo le esenzioni, visita: " + URL_CDR + "\n"
                                            # se il tag è 'li' (elenco puntato), allora metti un a capo
                                            elif z.name == "li" and printText is True:
                                                fulfillmentText += "- "
                                                fulfillmentText += z.text
                                                fulfillmentText += "\n"
                                            # se il tag non ha fratelli precedenti e successivi, allora stampa prima il testo del padre e poi il proprio (ESCLUSIONE DUPLICATI)
                                            elif len(z.findPreviousSiblings()) == 0 and len(
                                                    z.findNextSiblings()) == 0 and len(
                                                k.text.replace(str(z.text), "")) < 3:
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
            fulfillmentText += ("\n" + links.text + ": \n - " + "https://www.comune.bari.it" + links["href"] + "\n")

    # formattazione testo in eccesso
    fulfillmentText = re.sub("   MODALITA’ DI PAGAMENTO    Il pagamento", "\n\nMODALITA’ DI PAGAMENTO\nIl pagamento",
                             fulfillmentText)
    fulfillmentText = re.sub("1. Attraverso i Servizi PagoPA", "\n\n1. Attraverso i Servizi PagoPA\n", fulfillmentText)
    fulfillmentText = re.sub("Certificati rilasciati con bollo    Inserire i",
                             "\n   - Certificati rilasciati con bollo\n\nInserire i", fulfillmentText)
    fulfillmentText = re.sub(" Al termine della procedura sarà possibile pagare:",
                             "\n Al termine della procedura sarà possibile pagare:\n   -", fulfillmentText)
    fulfillmentText = re.sub("oppure", "\n  oppure\n   -", fulfillmentText)
    fulfillmentText = re.sub("STAMPA.    In entrambi i casi", "STAMPA.\n\n In entrambi i casi", fulfillmentText)
    fulfillmentText = re.sub("2. Direttamente presso", "\n\n2. Direttamente presso", fulfillmentText)
    if text == "CASI DI ESENZIONE":
        fulfillmentText = "CASI DI ESENZIONE\nIn caso di esenzione, spetta al soggetto richiedente dichiarare il " \
                          "relativo uso ed indicare la norma di riferimento che dispone il diritto di esenzione, " \
                          "in quanto l’esenzione non può essere presunta dall’operatore del servizio anagrafico.\nDi " \
                          "seguito, si riportano alcuni dei principali casi di esenzione, relativi ai certificati " \
                          "anagrafici, previsti dalle norme vigenti:\n\nATTENZIONE: Per visualizzare la tabella " \
                          "riguardo le esenzioni, visita: " \
                          "https://www.comune.bari.it/web/egov/-/certificato-di-residenza\n\nNOTA BENE: l’utilizzo di " \
                          "certificati rilasciati in esenzione da bolli, per fini diversi da quelli indicati sul " \
                          "certificato, equivale a evasione fiscale e comporta la responsabilità del richiedente, " \
                          "consistente nel pagamento dell’imposta e delle relative sanzioni previste dalle legge. "

    if context == "accordion_come_SCHEDA_SERVIZIO_IMPORTED_8868":
        fulfillmentText = re.sub("(?s)NOTA BENE:.*?da presentare ad altre Pubbliche Amministrazioni.", "",
                                 fulfillmentText)

    if pagamento:
        match1 = re.search("(?s)MODALITA’ DI PAGAMENTO.*?dell'anagrafe con il POS", fulfillmentText)
        fulfillmentText = match1.group(0)

    if context == "accordion_dove_SCHEDA_SERVIZIO_IMPORTED_8868":
        fulfillmentText = "UFFICIO ANAGRAFE CENTRALE\n\nNumero di telefono :\n 080/5773387 080/5773392\n (chiamare " \
                          "dal lunedì al venerdì ore 8.30/ 9.00 e 13.00/13.45)\n\nNumero di Email PEC :\n " \
                          "anagrafe.comunebari@pec.rupar.puglia.it \n (tale indirizzo è abilitato a ricevere sia email " \
                          "che pec)\n\nOrari di apertura al pubblico :\n Lunedì : 9.00 - 12.00\n Martedì : 9.00 - " \
                          "12.00\n Mercoledì : 9.00 - 12.00\n Giovedì : 9.00 - 12.00 e 15.30 - 17.00\n Venerdì : 9.00 - " \
                          "12.00\n Sabato : chiuso\n\nIndirizzo : Corso Vittorio Veneto,4 70122 Bari "
    if context == "CDR_COSA":
        fulfillmentText = stamp

    if context == "CDR_INFO":
        fulfillmentText = "Cosa vuoi sapere sul certificato di residenza (C.R.)?\n - Cos'è il certificato di residenza\n - Come richiedere il C.R.\n - Richiedere il C.R. in edicola\n - Validita del C.R.\n - Posizione/orari uffici per il C.R.\n - Costi del C.R.\n - Casi di esenzione C.R.\n - Modalità di pagamento C.R.\n - Tempi di rilascio C.R.\n - Moduli per richiesta C.R.\n"

    return fulfillmentText


# ricerca delle news e stampa di titolo, link e data
def NEWS_scraping(url):
    fulfillmentText = "\nLE NOTIZIE:\n "
    soup = parsing_html(url)
    notices = soup.findAll('div', class_="notizia padding10")
    for news1 in notices:
        dataN = news1.find('div', class_="data")
        fulfillmentText += "\n" + news1.a["title"] + "\n" + dataN.text.replace("\n", "") + "\n" + news1.a["href"] + "\n"

    return fulfillmentText


def EVENT_scraping(category):
    url = URL_EVENT
    categoryStamp = ""
    if category is not None:
        match category:
            case "Musica":
                url += "/musica"
                categoryStamp = "MUSICA"
            case "Cinema":
                url += "/cinema"
                categoryStamp = "CINEMA"
            case "Teatro":
                url += "/teatro"
                categoryStamp = "TEATRO"
            case "Sport":
                url += "/sport"
                categoryStamp = "SPORT"
            case "SpettacoliDanza":
                url += "/spettacoli-e-danza"
                categoryStamp = "SPETTACOLI E DANZA"
            case "FieraConvegni":
                url += "/fiera-e-convegni"
                categoryStamp = "FIERA E CONVEGNI"
            case "ArteMostre":
                url += "/arte-e-mostre"
                categoryStamp = "ARTE E MOSTRE"
            case "Online":
                url += "/eventi-online"
                categoryStamp = "ONLINE"
    else:
        url += "/eventi"

    if category != "EVENT_INFO":

        soup = parsing_html(url)

        fulfillmentText = "\nTUTTI GLI EVENTI "
        if category is not None:
            fulfillmentText += "della categoria " + categoryStamp + ":\n"
        else:
            fulfillmentText += "di qualunque categoria:\n"

        events = soup.findAll('div', class_="evento marginbottom10")

        for event1 in events:
            fulfillmentText += "\n" + event1.a["title"] + "\n" + event1.a["href"] + "\n"
            for event2 in event1.findAll('span', class_="marginright5"):
                print(event2.text)
                if "2010" not in event2.text and "2011" not in event2.text and "2012" not in event2.text and "2013" not in event2.text and "2014" not in event2.text and "2015" not in event2.text and "2016" not in event2.text and "2017" not in event2.text and "2018" not in event2.text and "2019" not in event2.text and "2020" not in event2.text and "2021" not in event2.text and "2022" not in event2.text and "2023" not in event2.text:
                    fulfillmentText += " " + event2.text
                event3 = event2.find_next_sibling()
                if event3 is not None:
                    if len(event3.findAll()) == 0 and re.search(event2.text, event3.text) is None:
                        fulfillmentText += " " + event3.text

            fulfillmentText += "\n"

        fulfillmentText = re.sub("Presso ", "\nPresso ", fulfillmentText)
    else:
        fulfillmentText = "Cosa ti interessa sapere sugli EVENTI?\n\n - Quali sono gli eventi di/a Bari\n - Quali sono gli eventi di una determinata categoria (es: Sport)\n\n Le categorie disponibili sono:\n - Tutte le categorie\n - Cinema\n - Fiera e convegni\n - Musica\n - Spettacoli e danza\n - Sport\n - Teatro\n - Online\n"

    return fulfillmentText


"""
def APP_scraping(url, app_name):
    if app_name is not None:
        match app_name:
            case "MUVT":
                app_name = "MUVT"
                parsing = muvt
            case "BARIAIUTA":
                app_name = "BariAiuta"
                parsing = bariAiuta
            case "TUPASSI":
                app_name = "TuPassi"
                parsing = tuPassi
            case "INFOSMARTCITY":
                app_name = "InfoSmartCity"
                parsing = infoSmartCity
            case "BARISOLVE":
                app_name = "BaRisolve"
                parsing = baRisolve
            case "BARISOCIAL":
                app_name = "Bari Social"
                parsing = bariSocial
            case "BARINFORMA":
                app_name = "BARInforma"
                parsing = barInforma
            case "APP_INFO":
                app_name = "APP_INFO"

    fulfillmentText = ""
    # soupApps = parsing_html(url)
    # apps = soupApps.find('div', class_="span12 bg-f9f9f9 padding20")
    if app_name != "APP_INFO":
        for app2 in apps.findAll('a'):
            if app2["title"] not in fulfillmentText:
                if app_name is None:
                    printText = True
                else:
                    printText = False

                if app2["title"] == app_name or printText is True:
                    # fulfillmentText += "\n - "
                    fulfillmentText += " - " + app2["title"]
                    fulfillmentText += "\n"
                    fulfillmentText += app2["href"]
                    fulfillmentText += "\n"
                    if app_name is not None:
                        # prendo le descrizioni da pagina dedicata ad app
                        soupApps2 = parsing
                        app3 = soupApps2.find('div', class_="strutturacobari strutturaschedaapp")
                        app4 = app3.find('div', class_="span12")
                        app5 = app4.findAll('div', class_="span12")
                        for app6 in app5:
                            if len(app6.text) > 45:
                                fulfillmentText += app6.text
                                fulfillmentText += "\n"
                        links = soupApps2.findAll("div", class_="span12 marginbottom10 text-center")
                        for store in links:
                            for store2 in store.findAll('a'):
                                if store2["href"] is not None and "apple" in store2["href"]:
                                    fulfillmentText += "\nDownload app on the APP STORE (Iphone):\n"
                                    fulfillmentText += store2["href"]
                                elif store2["href"] is not None and "google" in store2["href"]:
                                    fulfillmentText += "\nDownload app on GOOGLE PLAY STORE (Android):\n"
                                    fulfillmentText += store2["href"]

                    fulfillmentText += "\n"
                    printText = False

        fulfillmentText = re.sub("\. ", ".\n", fulfillmentText)
    else:
        fulfillmentText = "\nCosa vuoi sapere riguardo le App?\n\n - Tutte le app di Bari\n - Una specifica app di Bari"

    return fulfillmentText
"""


@app.route("/webhooks", methods=["POST"])
def webhooks():
    webhooks.count = 1
    req = request.get_json(silent=True, force=True)
    fulfillmentText = ""
    # processo la query che arriva in JSON
    query_result = req.get('queryResult')

    # intent della carta di identità (CIE)
    if query_result.get("intent").get("displayName") == "CIE_INFO":
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
    elif query_result.get("intent").get("displayName") == "CIE_NON_COMUNITARI":
        fulfillmentText = cie_scraping(URL_CIE, "COMUNITARI", None)
    elif query_result.get("intent").get("displayName") == "CIE_PROCESSO":
        fulfillmentText = cie_scraping(URL_CIE, None, "CIE_COME")
    elif query_result.get("intent").get("displayName") == "CIE_TEMPI":
        fulfillmentText = cie_scraping(URL_CIE, None, "CIE_TEMPI")
    elif query_result.get("intent").get("displayName") == "CIE_COSTI":
        fulfillmentText = cie_scraping(URL_CIE, "COSTI", None)
    elif query_result.get("intent").get("displayName") == "CIE_PORTALE":
        fulfillmentText = cie_scraping(URL_CIE, "PORTALE CIE", None)
    elif query_result.get("intent").get("displayName") == "CIE_PAGAMENTO":
        fulfillmentText = cie_scraping(URL_CIE, "PAGAMENTO", None)
    elif query_result.get("intent").get("displayName") == "CIE_DOVE":
        if query_result["parameters"]["SanPasquale"] != "":
            fulfillmentText = cie_scraping(URL_CIE, "CIE_SANPASQUALE", None)
        elif query_result["parameters"]["Centrale"] != "":
            fulfillmentText = cie_scraping(URL_CIE, "CIE_CENTRALE", None)

    # intent del cambio di residenza (CR)
    elif query_result.get("intent").get("displayName") == "CR_INFO":
        fulfillmentText = CR_scraping(URL_CR, None, "CR_INFO")
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

    # intent della TARI
    elif query_result.get("intent").get("displayName") == "TARI_INFO":
        fulfillmentText = TARI_scraping(URL_TARI, None, "TARI_INFO")
    elif query_result.get("intent").get("displayName") == "TARI_COSA":
        fulfillmentText = TARI_scraping(URL_TARI, None, "TARI_COSA")
    elif query_result.get("intent").get("displayName") == "TARI_COME":
        fulfillmentText = TARI_scraping(URL_TARI, None, "TARI_COME")
    elif query_result.get("intent").get("displayName") == "TARI_COSTI":
        fulfillmentText = TARI_scraping(URL_TARI, None, "TARI_COSTI")
    elif query_result.get("intent").get("displayName") == "TARI_TEMPI":
        fulfillmentText = TARI_scraping(URL_TARI, None, "TARI_TEMPI")
    elif query_result.get("intent").get("displayName") == "TARI_ALLEGATI":
        fulfillmentText = TARI_scraping(URL_TARI, None, "TARI_ALLEGATI")
    elif query_result.get("intent").get("displayName") == "TARI_DOCUMENTI":
        fulfillmentText = TARI_scraping(URL_TARI, "DOCUMENTI", None)
    elif query_result.get("intent").get("displayName") == "TARI_DOVE":
        fulfillmentText = TARI_scraping(URL_TARI, None, "TARI_DOVE")

    # intent certificato di residenza
    elif query_result.get("intent").get("displayName") == "CDR_INFO":
        fulfillmentText = CDR_scraping(URL_CDR, None, "CDR_INFO")
    elif query_result.get("intent").get("displayName") == "CDR_COME":
        fulfillmentText = CDR_scraping(URL_CDR, None, "CDR_COME")
    elif query_result.get("intent").get("displayName") == "CDR_COSA":
        fulfillmentText = CDR_scraping(URL_CDR, None, "CDR_COSA")
    elif query_result.get("intent").get("displayName") == "CDR_DOVE":
        fulfillmentText = CDR_scraping(URL_CDR, None, "CDR_DOVE")
    elif query_result.get("intent").get("displayName") == "CDR_COSTI":
        fulfillmentText = CDR_scraping(URL_CDR, None, "CDR_COSTI")
    elif query_result.get("intent").get("displayName") == "CDR_TEMPI":
        fulfillmentText = CDR_scraping(URL_CDR, None, "CDR_TEMPI")
    elif query_result.get("intent").get("displayName") == "CDR_ALLEGATI":
        fulfillmentText = CDR_scraping(URL_CDR, None, "CDR_ALLEGATI")
    elif query_result.get("intent").get("displayName") == "CDR_VALIDITA":
        fulfillmentText = CDR_scraping(URL_CDR, "VALIDITA", None)
    elif query_result.get("intent").get("displayName") == "CDR_EDICOLA":
        fulfillmentText = CDR_scraping(URL_CDR, "EDICOLA", None)
    elif query_result.get("intent").get("displayName") == "CDR_ESENZIONE":
        fulfillmentText = CDR_scraping(URL_CDR, "ESENZIONE", None)
    elif query_result.get("intent").get("displayName") == "CDR_PAGAMENTO":
        fulfillmentText = CDR_scraping(URL_CDR, "PAGAMENTO", None)

    # intent sanzioni
    elif query_result.get("intent").get("displayName") == "SANZ_COSA":
        fulfillmentText = SANZ_scraping(URL_SANZ, None, "SANZ_COSA")
    elif query_result.get("intent").get("displayName") == "SANZ_COME":
        fulfillmentText = SANZ_scraping(URL_SANZ, None, "SANZ_COME")
    elif query_result.get("intent").get("displayName") == "SANZ_INFO":
        fulfillmentText = SANZ_scraping(URL_SANZ, None, "SANZ_INFO")
    elif query_result.get("intent").get("displayName") == "SANZ_COSTI":
        fulfillmentText = SANZ_scraping(URL_SANZ, None, "SANZ_COSTI")
    elif query_result.get("intent").get("displayName") == "SANZ_TEMPI":
        fulfillmentText = SANZ_scraping(URL_SANZ, None, "SANZ_TEMPI")
    elif query_result.get("intent").get("displayName") == "SANZ_DOVE":
        fulfillmentText = SANZ_scraping(URL_SANZ, None, "SANZ_DOVE")

    # intent news
    elif query_result.get("intent").get("displayName") == "NEWS":
        fulfillmentText = NEWS_scraping(URL_NEWS)

    # intent events
    elif query_result.get("intent").get("displayName") == "EVENT":
        if query_result["parameters"]["ArteMostre"] != "":
            fulfillmentText = EVENT_scraping("ArteMostre")
        elif query_result["parameters"]["Cinema"] != "":
            fulfillmentText = EVENT_scraping("Cinema")
        elif query_result["parameters"]["FieraConvegni"] != "":
            fulfillmentText = EVENT_scraping("FieraConvegni")
        elif query_result["parameters"]["Musica"] != "":
            fulfillmentText = EVENT_scraping("Musica")
        elif query_result["parameters"]["Musica"] != "":
            fulfillmentText = EVENT_scraping("Musica")
        elif query_result["parameters"]["SpettacoliDanza"] != "":
            fulfillmentText = EVENT_scraping("SpettacoliDanza")
        elif query_result["parameters"]["Sport"] != "":
            fulfillmentText = EVENT_scraping("Sport")
        elif query_result["parameters"]["Teatro"] != "":
            fulfillmentText = EVENT_scraping("Teatro")
        elif query_result["parameters"]["Online"] != "":
            fulfillmentText = EVENT_scraping("Online")
        else:
            fulfillmentText = EVENT_scraping(None)

    # intent info event
    elif query_result.get("intent").get("displayName") == "EVENT_INFO":
        fulfillmentText = EVENT_scraping("EVENT_INFO")
    """
    # intent APPS
    elif query_result.get("intent").get("displayName") == "APP":
        if query_result["parameters"]["MUVT"] != "":
            fulfillmentText = APP_scraping(URL_APPS, "MUVT")
        elif query_result["parameters"]["BARIAIUTA"] != "":
            fulfillmentText = APP_scraping(URL_APPS, "BARIAIUTA")
        elif query_result["parameters"]["TUPASSI"] != "":
            fulfillmentText = APP_scraping(URL_APPS, "TUPASSI")
        elif query_result["parameters"]["INFOSMARTCITY"] != "":
            fulfillmentText = APP_scraping(URL_APPS, "INFOSMARTCITY")
        elif query_result["parameters"]["BARISOCIAL"] != "":
            fulfillmentText = APP_scraping(URL_APPS, "BARISOCIAL")
        elif query_result["parameters"]["BARINFORMA"] != "":
            fulfillmentText = APP_scraping(URL_APPS, "BARINFORMA")
        elif query_result["parameters"]["BARISOLVE"] != "":
            fulfillmentText = APP_scraping(URL_APPS, "BARISOLVE")
        else:
            fulfillmentText = APP_scraping(URL_APPS, None)

    # intent info app
    elif query_result.get("intent").get("displayName") == "APP_INFO":
        fulfillmentText = APP_scraping(URL_APPS, "APP_INFO")
    """
    # if fulfillmentText == "":
    #    fulfillmentText = "Ho ancora tanto da imparare, puoi ripetere?"

    # se c'è una risposta, la ritorno sempre in formato JSON
    return {
        "fulfillmentText": fulfillmentText,
        "displayText": '25',
        "source": "webhookdata"
    }



# app.run(debug=True, port=8080)
