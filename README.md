# IppolitoPisaniApp

Applicazione web Flask pensata per la gestione del patrimonio informativo dell'Istituto Ippolito Pisani. Questa versione iniziale fornisce:

- struttura base del progetto in Flask con Blueprint principale (`main`)
- pagina di login con gestione sessione e logout
- dashboard di esempio post-login
- autenticazione collegata alla tabella `dbo.Utenti` su SQL Server tramite `pyodbc`

## Requisiti

- Python 3.11 (raccomandato). Versioni oltre la 3.13 non sono ancora supportate da `pyodbc`.
- [ODBC Driver per SQL Server](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server) installato sulla macchina

## Setup

Esegui i seguenti comandi dal terminale (PowerShell su Windows, bash su macOS/Linux):

```powershell
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configurazione ambiente

Compila il file `.env` con valori reali di produzione/sviluppo. Esempio di struttura:

```env
SECRET_KEY=change-me-in-production

DB_SERVER=YOUR_SQL_SERVER_HOST
DB_PORT=1433
DB_NAME=YOUR_DATABASE_NAME
DB_USER=YOUR_DB_USERNAME
DB_PASSWORD=YOUR_DB_PASSWORD
DB_DRIVER=  # opzionale: verrà scelto automaticamente se lasciato vuoto
```

- `SECRET_KEY` viene utilizzata da Flask per firmare le sessioni.
- Le variabili `DB_*` vengono utilizzate da `pyodbc` per aprire la connessione a SQL Server.
- Se `DB_DRIVER` non è valorizzata l'app cercherà automaticamente tra i driver disponibili (`ODBC Driver 18/17`, `SQL Server`).
- Per accedere è necessario che l'utente esista nella tabella `dbo.Utenti` del database configurato.

## Avvio dell'applicazione

```powershell
python run.py
```

Per modificare host, porta o debug puoi esportare le variabili `FLASK_RUN_HOST`, `FLASK_RUN_PORT` e `FLASK_DEBUG` prima di lanciare il comando.

## Struttura del progetto

```
IppolitoPisaniApp/
├── app/
│   ├── __init__.py       # Application factory e registrazione blueprint
│   ├── db.py             # Helper per connessioni SQL Server via pyodbc
│   ├── routes.py         # Blueprint principale con login/logout/dashboard
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   └── dashboard.html
│   └── static/
│       ├── css/
│       │   ├── style.css
│       │   └── login.css
│       ├── js/
│       │   └── main.js
│       └── images/
├── config.py             # Configurazione centralizzata caricata da .env
├── requirements.txt
├── run.py
└── .env
```

## Prossimi sviluppi suggeriti

- Collegare il login alle tabelle utenti presenti sul database.
- Gestire ruoli e permessi differenziati.
- Integrare componenti front-end per dashboard dinamiche.
- Implementare test automatici (unit test e integrazione DB).
