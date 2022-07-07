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


def personal_scraping(url, query_text):
    fulfillmentText = ''
    soup = parsing_html(url)
    regex = None

    query_text = query_text.split()

    # se il cognome della persona ha spazi in mezzo

    if (len(query_text) == NAME_LEN):
        # riduco a 2 i token -> <nome> <cognome>
        el1 = query_text[0]
        el2 = query_text[1]
        del query_text[0:2]
        query_text.append(el1 + " " + el2)

    # cicla su ogni parola trovata alla ricerca del cognome del prof o collaboratore
    for surname in query_text:

        name = ""
        # se trova le informazioni richieste, non continua il ciclo
        if fulfillmentText != '':
            break

        # elimina apostrofi e spazi per l'email
        surname_no_apos = surname.replace("'", "").replace(" ", "")
        # elimina accenti per l'email
        surname_no_apos = ''.join(
            (c for c in unicodedata.normalize('NFD', surname_no_apos) if unicodedata.category(c) != 'Mn'))

        # estrae solo il testo della pagina HTML e cerca stringa iniziante per cognome del prof
        if url == URL_PROF or url == URL_SEGRET:
            if surname == "dimauro":
                regex = re.search("{0}.+giovanni\.{1}\@uniba\.it".format(surname, surname_no_apos), soup.get_text(),
                                  re.IGNORECASE)
            else:
                regex = re.search("{0}.+{1}\@uniba\.it".format(surname, surname_no_apos), soup.get_text(),
                                  re.IGNORECASE)
            # se le espressioni regolari hanno dato risultati
            if regex:
                fulfillmentText = regex.group(0)
                # elimino "interno <numero> dai contatti dei prof"
                if "interno" in fulfillmentText:
                    fulfillmentText = re.sub(".{0,1}interno.{0,1}\d*.{0,1}", " ", regex.group(0))


        # oppure cerca se nella stringa c'è il cognome del prof
        elif url == URL_SEGRET_FOREIGN:
            for i in soup.find_all("p"):
                if len(i.contents) > 1 and isinstance(i.contents[0], str):
                    if surname.lower() in i.contents[0].lower():
                        fulfillmentText = i.contents[0].string + i.contents[1].string

        # formattazione varia
        if url == URL_PROF:
            fulfillmentText = re.sub("- Tel", "\n- Tel", fulfillmentText, re.IGNORECASE)
            fulfillmentText = re.sub("- e-Mail", "\n- e-Mail", fulfillmentText, re.IGNORECASE)

        elif url == URL_SEGRET:
            fulfillmentText = re.sub("Tel", "\nTel", fulfillmentText, re.IGNORECASE)
            fulfillmentText = re.sub("E-mail", "\nE-mail", fulfillmentText, re.IGNORECASE)

        elif url == URL_SEGRET_FOREIGN:
            regex = re.search("-.tel:.\+[0-9]*.", fulfillmentText, re.IGNORECASE)
            if regex:
                n_tell = regex.group(0)
                fulfillmentText = re.sub("-.tel:.\+[0-9]*.", "\n{}\n".format(n_tell), fulfillmentText, re.IGNORECASE)

    return fulfillmentText


# craping sulle info inerenti alla CDI elettronica
def cie_scraping(url, text):
    fulfillmentText = ""
    soup = parsing_html(url)
    if text is "":
        text = None

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


def resources_scraping(url):
    fulfillmentText = ""
    soup = parsing_html(url)

    for i in soup.find_all(class_="portletWrapper"):

        if i[
            "id"] == "portletwrapper-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f756e696261342f726963657263612f646970617274696d656e74692f696e666f726d61746963612f646970617274696d656e746f2d64692d696e666f726d61746963610a7370617a696f2d73747564656e7469":

            for j in i.children:
                for k in j.children:
                    try:
                        if re.search("portletItem", k["class"][0], re.IGNORECASE):

                            for z in k.children:
                                try:
                                    fulfillmentText += z.text
                                    fulfillmentText += "\n "
                                    fulfillmentText += z.a["href"]
                                    fulfillmentText += "\n\n"
                                except:
                                    fulfillmentText += z.a["href"]
                                    fulfillmentText += "\n\n"
                    except:
                        continue
    return fulfillmentText


def foreign_stud_scraping(url):
    fulfillmentText = ""
    soup = parsing_html(url)

    for i in soup.find_all(class_="masiniEvidence"):

        if i is not None and i.text is not None and re.search("foreign students", i.text, re.IGNORECASE):

            for j in i.next_siblings:

                try:
                    if re.search("masiniEvidence", j["class"][0], re.IGNORECASE):
                        break
                    else:
                        if j.text is not None:
                            fulfillmentText += "\n" + j.text + "\n"
                except:
                    if j.text is not None:
                        fulfillmentText += "\n" + j.text + "\n"
            break
    return fulfillmentText


def degree_scraping(url, b_degree=None, m_degree=None):
    fulfillmentText = ''
    soup = parsing_html(url)

    if b_degree is not None:
        for i in soup.find_all(class_="masiniEvidence"):
            if i.string is None:
                continue
            if re.search("lauree triennali", i.string, re.IGNORECASE):
                fulfillmentText = i.string + ':\n'
                for j in i.next_siblings:
                    if j.a is None:
                        break
                    fulfillmentText += "\n" + j.a.text + ": "
                    fulfillmentText += "\n" + j.a["href"] + "\n"
                break

    elif m_degree is not None:
        for i in soup.find_all(class_="masiniEvidence"):
            if i.string is None:
                continue
            if re.search("laurea magistrale", i.string, re.IGNORECASE):
                fulfillmentText = i.string + ':\n'
                for j in i.next_siblings:
                    if j.a is None:
                        break
                    fulfillmentText += "\n" + j.a.text + ": "
                    fulfillmentText += "\n" + j.a["href"] + "\n"
                break

    elif b_degree is None and m_degree is None:
        for i in soup.find_all(class_="masiniEvidence"):
            if i.string is None:
                continue
            if "lauree triennali" in i.string.lower() or "laurea magistrale" in i.string.lower():
                fulfillmentText += '\n' + i.string + ':\n'
                for j in i.next_siblings:
                    if j.a is None:
                        break
                    fulfillmentText += "\n" + j.a.text + ": "
                    fulfillmentText += "\n" + j.a["href"] + "\n"

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


def lab_gradueting_scraping(url):
    fulfillmentText = ''
    soup = parsing_html(url)
    # conteggio del testo utile
    count = 0

    for i in soup.find_all("div"):

        try:
            if i["id"] == "content":
                for j in i.children:
                    try:
                        if j["id"] == "content-core":
                            for k in j.children:
                                try:
                                    if k["id"] == "parent-fieldname-text-d455f35fd63f4f92a619713c926d8282":
                                        for z in k.descendants:
                                            if (isinstance(z, str)):
                                                count += 1
                                                if re.search("accesso", z, re.IGNORECASE):
                                                    z = re.sub("Accesso", "\n\nAccesso\n\n", z)
                                                fulfillmentText += z
                                                if count == 9:
                                                    break
                                except:
                                    continue
                    except:
                        continue
        except:
            continue
    return fulfillmentText


def apprenticeship_scraping(url):
    fulfillmentText = ''
    soup = parsing_html(url)

    # quanti paragrafi scartare
    count_useless = 0

    # paragrafi da includere
    count_useful = 0

    for i in soup.find_all("div"):

        try:
            if i["id"] == "content":
                for j in i.children:
                    try:
                        if j["id"] == "content-core":
                            for k in j.children:
                                try:
                                    if k["id"] == "parent-fieldname-text-6af98676d13d43c88ab06b5a8342a1ac":
                                        for z in k.descendants:
                                            count_useless += 1
                                            if count_useless >= 9:
                                                if (isinstance(z, str)):
                                                    if re.search("tirocini interni", z, re.IGNORECASE):
                                                        z = re.sub("Tirocini interni", "\n\n**Tirocini interni**", z)
                                                    elif re.search("tirocini esterni", z, re.IGNORECASE):
                                                        z = re.sub("Tirocini esterni", "\n\n**Tirocini esterni**", z)
                                                    elif re.search("linee guida per", z, re.IGNORECASE):
                                                        z = re.sub("LINEE GUIDA PER CONVENZIONI E TIROCINI",
                                                                   "\nLINEE GUIDA PER CONVENZIONI E TIROCINI\n", z)
                                                    count_useful += 1
                                                    fulfillmentText += z + "\n"
                                                if count_useful == 27:
                                                    fulfillmentText += "\nPer i documenti di cui si parla consultare:" + URL_APPRENTICESHIP
                                                    break
                                except:
                                    continue
                    except:
                        continue
        except:
            continue

    return fulfillmentText


def secretary_scraping(url):
    fulfillmentText = ''
    soup = parsing_html(url)

    # paragrafi da scartare
    count_useless = 0
    for i in soup.find_all(class_="portletWrapper"):

        if i[
            "id"] == "portletwrapper-706c6f6e652e7269676874636f6c756d6e0a636f6e746578740a2f756e696261342f726963657263612f646970617274696d656e74692f696e666f726d61746963612f646970617274696d656e746f2d64692d696e666f726d61746963610a7370617a696f2d73747564656e7469":

            for j in i.children:

                for k in j.children:
                    try:
                        if re.search("portletItem", k["class"][0], re.IGNORECASE):

                            for z in k.descendants:

                                try:
                                    if (isinstance(z, str)):
                                        if count_useless >= 30:
                                            # formattazione varia
                                            if re.search("Segreteria Didattica sede di Taranto", z, re.IGNORECASE):
                                                z = re.sub("Segreteria Didattica sede di Taranto",
                                                           "\n**Segreteria Didattica sede di Taranto**", z)
                                            elif re.search("pratiche studenti stranieri", z, re.IGNORECASE):
                                                z = re.sub("Pratiche studenti stranieri",
                                                           "\n**Pratiche studenti stranieri**", z)
                                            elif re.search("Segreteria Orientamento, Tirocini e Job Placement", z,
                                                           re.IGNORECASE):
                                                z = re.sub("Segreteria Orientamento, Tirocini e Job Placement",
                                                           "\n**Segreteria Orientamento, Tirocini e Job Placement**", z)
                                            elif re.search("segreteria didattica", z, re.IGNORECASE):
                                                z = re.sub("Segreteria Didattica", "\n**Segreteria Didattica**", z)
                                            fulfillmentText += z
                                            fulfillmentText += "\n"
                                except:
                                    continue
                                finally:
                                    count_useless += 1
                    except:
                        continue

    return fulfillmentText


def erasmus_scraping(url):
    fulfillmentText = ''
    soup = parsing_html(url)

    for i in soup.find_all("div"):
        try:
            if i["id"] == "content":
                for j in i.children:
                    try:
                        if j["id"] == "content-core":
                            for k in j.children:
                                try:
                                    if k["id"] == "parent-fieldname-text-c4acaf658ef34dcc93f82abe3ae3be3d":
                                        for z in k.children:
                                            try:
                                                fulfillmentText += z.a.span.text + ":\n"
                                                fulfillmentText += z.a["href"] + "\n\n"
                                            except:
                                                fulfillmentText += z.a.text + ":\n"
                                                fulfillmentText += z.a["href"] + "\n\n"
                                                continue
                                except:
                                    continue
                    except:
                        continue
        except:
            continue
    return fulfillmentText


def news_scraping(url):
    fulfillmentText = "**ULTIME NOTIZIE DEL DIB**\n"
    soup = parsing_html(url)

    # tolgo span per evitare spaziature inutili
    for span_tag in soup.find_all('span'):
        span_tag.replace_with('')

    for i in soup.find_all(class_="portletWrapper"):

        if i[
            "id"] == "portletwrapper-436f6e74656e7457656c6c506f72746c6574732e42656c6f77506f72746c65744d616e61676572320a636f6e746578740a2f756e696261342f726963657263612f646970617274696d656e74692f696e666f726d61746963612f646970617274696d656e746f2d64692d696e666f726d61746963610a7a6f6e612d6e657773":
            for j in i.children:
                try:
                    if j["id"] == "portlet-newszona":
                        for z in j.children:
                            try:
                                if re.search("portletItem", z["class"][0], re.IGNORECASE):
                                    fulfillmentText += z.a.text
                                    fulfillmentText += z.a["href"] + "\n\n"
                                elif re.search("portletFooter", z["class"][0], re.IGNORECASE):
                                    fulfillmentText += z.a.text
                                    fulfillmentText += z.a["href"] + "\n"
                                    break
                            except:
                                continue
                except:
                    continue
    # formattazione varia
    fulfillmentText = re.sub("  +", "", fulfillmentText)
    return fulfillmentText


def events_scraping(url):
    fulfillmentText = '**ULTIMI EVENTI DEL DIB**\n'
    soup = parsing_html(url)

    # tolgo gli span per evitare troppe spaziature
    for span_tag in soup.find_all('span'):
        span_tag.replace_with('')

    for i in soup.find_all(class_="portletWrapper"):
        if i[
            "id"] == "portletwrapper-436f6e74656e7457656c6c506f72746c6574732e42656c6f77506f72746c65744d616e61676572310a636f6e746578740a2f756e696261342f726963657263612f646970617274696d656e74692f696e666f726d61746963612f646970617274696d656e746f2d64692d696e666f726d61746963610a7a6f6e612d6576656e7469":
            for j in i.children:
                try:
                    if j["id"] == "portlet-newszona":
                        for z in j.children:
                            try:
                                if re.search("portletItem", z["class"][0], re.IGNORECASE):
                                    fulfillmentText += z.a.text
                                    fulfillmentText += z.a["href"] + "\n\n"
                                elif re.search("portletFooter", z["class"][0], re.IGNORECASE):
                                    fulfillmentText += z.a.text
                                    fulfillmentText += z.a["href"] + "\n\n"
                                    break
                            except:
                                continue
                except:
                    continue
    fulfillmentText = re.sub("  +", "", fulfillmentText)
    return fulfillmentText


def uni_research_scraping(url):
    fulfillmentText = '**ORIENTAMENTO**\n'
    soup = parsing_html(url)
    # paragrafi utili
    count_useful = 0
    for i in soup.find_all('div'):
        try:
            if i["id"] == "parent-fieldname-description":
                fulfillmentText += i.text + "\n\n"
                fulfillmentText = re.sub("  +", "", fulfillmentText)
            elif i["id"] == "content-core":
                for j in i.children:
                    for k in j.descendants:
                        try:
                            if re.search("summary", k["class"][0], re.IGNORECASE):
                                fulfillmentText += "**** " + k.a.text + " ****" + "\n"
                                fulfillmentText += "link:\n" + k.a["href"] + "\n"
                            elif re.search("description", k["class"][0], re.IGNORECASE):
                                fulfillmentText += "riassunto:\n" + k.text + "\n\n\n"
                            count_useful += 1
                            # primi 17 sono i paragrafi utili
                            if count_useful == 16:
                                count_useful += 1
                                break
                        except:
                            continue
        except:
            continue
    return fulfillmentText


def job_placement_scraping(url):
    fulfillmentText = '**ULTIME SUL JOB PLACEMENT:**\n\n'
    soup = parsing_html(url)

    for i in soup.find_all(class_="portletWrapper"):
        if i[
            "id"] == "portletwrapper-436f6e74656e7457656c6c506f72746c6574732e42656c6f77506f72746c65744d616e61676572310a636f6e746578740a2f756e696261342f726963657263612f646970617274696d656e74692f696e666f726d61746963612f646970617274696d656e746f2d64692d696e666f726d61746963610a6a6f622d706c6163656d656e74":
            for j in i.children:
                try:
                    if re.search("portlet-static-job-placement", j["class"][2], re.IGNORECASE):
                        for z in j.children:
                            try:
                                if re.search("portletItem", z["class"][0], re.IGNORECASE):
                                    for k in z.descendants:
                                        try:
                                            text_to_add = k.a.text + ": "
                                            text_to_add += k.a["href"] + "\n\n"
                                            if text_to_add not in fulfillmentText:
                                                fulfillmentText += text_to_add
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

    # cerco tutti gli intent
    if query_result.get("intent").get("displayName") == "Ricerca personale":
        if "contact" in query_result["parameters"]:
            for i in URL_PROF, URL_SEGRET, URL_SEGRET_FOREIGN:
                if fulfillmentText != "":
                    break
                fulfillmentText = personal_scraping(i, query_result["parameters"]["contact"])


    elif query_result.get("intent").get("displayName") == "Biblioteca":
        fulfillmentText = library_scraping(URL_BIBLIO)


    elif query_result.get("intent").get("displayName") == "RisorseStudenti":
        fulfillmentText = resources_scraping(URL_RESOURCES)


    elif query_result.get("intent").get("displayName") == "Corsi di laurea":

        if query_result["parameters"]["LaureaTriennale"]:
            fulfillmentText = degree_scraping(URL_CDL, b_degree=query_result["parameters"]["LaureaTriennale"])
        elif query_result["parameters"]["LaureaMagistrale"]:
            fulfillmentText = degree_scraping(URL_CDL, m_degree=query_result["parameters"]["LaureaMagistrale"])
        else:
            fulfillmentText = degree_scraping(URL_CDL)


    elif query_result.get("intent").get("displayName") == "Studenti stranieri":
        fulfillmentText = foreign_stud_scraping(URL_STUD_FOREIGN)


    elif query_result.get("intent").get("displayName") == "ComeRaggiungerci":

        if query_result["parameters"]["SedeTaranto"] != "":
            fulfillmentText = "Sede di Taranto (ICD):\n\nex II facoltà di Scienze, piano terra  Via A. De Gasperi, Quartiere Paolo VI 74123 Taranto"
        else:
            fulfillmentText = dib_location_scraping(URL_DIB_LOCATION)

    elif query_result.get("intent").get("displayName") == "Laboratorio tesisti":
        fulfillmentText = lab_gradueting_scraping(URL_LAB_GRAD)


    elif query_result.get("intent").get("displayName") == "Tirocini":
        fulfillmentText = apprenticeship_scraping(URL_APPRENTICESHIP)


    elif query_result.get("intent").get("displayName") == "Segreteria studenti":
        fulfillmentText = secretary_scraping(URL_RESOURCES)

    elif query_result.get("intent").get("displayName") == "Erasmus+":
        fulfillmentText = erasmus_scraping(URL_ERASMUS)

    elif query_result.get("intent").get("displayName") == "Eventi":
        fulfillmentText = events_scraping(URL_RESOURCES)

    elif query_result.get("intent").get("displayName") == "News":
        fulfillmentText = news_scraping(URL_RESOURCES)

    elif query_result.get("intent").get("displayName") == "orientamento":
        fulfillmentText = uni_research_scraping(URL_UNI_RESEARCH)

    elif query_result.get("intent").get("displayName") == "JobPlacement":
        fulfillmentText = job_placement_scraping(URL_RESOURCES)

    elif query_result.get("intent").get("displayName") == "CDI":
        if query_result["parameters"]["caratteristicheCIE"] != "":
            fulfillmentText = cie_scraping(URL_CIE, "CARATTERISTICHE")
        elif query_result["parameters"]["RichiestaCDI"] != "":
            fulfillmentText = cie_scraping(URL_CIE, "QUANDO")
        else:
            fulfillmentText = cie_scraping(URL_CIE, "")

    # if fulfillmentText == "":
    #    fulfillmentText = "Ho ancora tanto da imparare, puoi ripetere?"

    # se c'è una risposta, la ritorno sempre in formato JSON
    return {
        "fulfillmentText": fulfillmentText,
        "displayText": '25',
        "source": "webhookdata"
    }

# app.run(debug=True, port=5000)
