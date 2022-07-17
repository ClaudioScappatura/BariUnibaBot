# Documentazione tecnica Progetto SysAg BariBot

### Organizzazione File
- Scraper: app -> main.py<br />
- File "wsgi.py" da cui si avvia l'applicazione (utile per la compatibilità con l'applicazione corrispondente di Heroku)<br />
- Presentazione progetto
- Copia dell'agente di DialogFlow: BariBot.zip

### Descrizione dell'applicazione collegata a BariBot
#### L'applicazione usata dal Webhook Service costruito in Python sono una serie di funzioni di scraping che estraggono testo direttamente dal sito del comune di Bari.<br />
- Il codice dell'applicazione è scritto nel "main.py", mentre il modulo "wsgi.py" serve solo per eseguirla.<br />
- L'app è stata deployata su Heroku e risponde solo alle richieste "POST".<br />
- In particolare gestisce tutta la parte di fullfilment prevista dal chatbot, gestendo le richieste POST e scambiando messaggi in formato Json con DialogFlow, piattaforma utilizzata per gestire il flusso conversazionale con l'utente, ovvero per rispondere all'utente tramite risposte predefinite o ricavate da attraverso webhook.<br />
Per testare il bot su Telegram digitare @Bari_Uniba_bot<br />

### Riferimenti

- Librerie utilizzate per realizzare lo screaping: BeautifulSoup per l'estrazione della pagina HTML<br />
- Server su cui è stata deployata l'applicazione: Heroku<br />
- Piattaforma per la gestione del flusso della conversazione con l'utente: DialogFlow

### ATTENZIONE

La versione del chatbot in esecuzione su Heroku presenta il servizio "APP" disabilitato poichè la versione gratuita di Heroku pone dei limiti all'esecuzione del codice quindi quest ultimo sarà abilitato solamente durante l'esecuzione in locale (dimostrazione durante la prova di esame).
