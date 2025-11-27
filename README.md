# Capvero Backend

Backend-API für die Capvero SaaS-Plattform – eine moderne FastAPI-Anwendung für Unternehmensbewertungen und Unternehmensnachfolgen.

## Tech-Stack

- **Framework:** FastAPI
- **Sprache:** Python 3.11+
- **Datenbank:** PostgreSQL mit SQLAlchemy 2.0 (async)
- **Migrationen:** Alembic
- **Authentifizierung:** JWT (python-jose)
- **Validierung:** Pydantic
- **KI/ML:** Prophet, ARIMA (statsmodels), scikit-learn
- **Testing:** Pytest

## Projektstruktur

```
capvero-backend/
├── .github/                    # CI/CD Workflows
├── alembic/                    # Datenbank-Migrationen
│   └── versions/               # Migration-Versionen
├── src/
│   ├── api/                    # API-Endpunkte
│   │   └── v1/
│   │       ├── endpoints/      # Einzelne Endpoint-Dateien
│   │       └── router.py       # Haupt-Router für v1
│   ├── core/                   # Konfiguration, Security, DB-Session
│   ├── crud/                   # Datenbank-Operationen (CRUD)
│   ├── models/                 # SQLAlchemy-Datenbankmodelle
│   ├── schemas/                # Pydantic-Validierungsmodelle
│   ├── services/               # Geschäftslogik (Bewertungsengine, etc.)
│   └── main.py                 # Hauptanwendung
├── tests/                      # Unit- & Integrationstests
├── .env.example
├── requirements.txt
└── Dockerfile
```

## Erste Schritte

### Voraussetzungen

- Python 3.11+ installiert
- PostgreSQL-Datenbank verfügbar

### Installation

```bash
# Virtuelle Umgebung erstellen
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt
```

### Konfiguration

Erstellen Sie eine `.env`-Datei basierend auf `.env.example`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/capvero
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Datenbank-Migrationen

```bash
# Initiale Migration ausführen
alembic upgrade head

# Neue Migration erstellen
alembic revision --autogenerate -m "Description"
```

### Entwicklung

```bash
# Server starten
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Die API läuft unter [http://localhost:8000](http://localhost:8000).
API-Dokumentation: [http://localhost:8000/docs](http://localhost:8000/docs)

### Tests

```bash
pytest
pytest --cov=src tests/
```

## API-Endpunkte

### Authentifizierung
- `POST /api/v1/auth/register` - Benutzerregistrierung
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Token erneuern

### Unternehmen
- `GET /api/v1/companies` - Liste aller Unternehmen
- `POST /api/v1/companies` - Neues Unternehmen erstellen
- `GET /api/v1/companies/{id}` - Unternehmensdetails
- `PUT /api/v1/companies/{id}` - Unternehmen aktualisieren
- `DELETE /api/v1/companies/{id}` - Unternehmen löschen

### Bewertungen
- `POST /api/v1/valuations` - Neue Bewertung erstellen
- `GET /api/v1/valuations/{id}` - Bewertungsdetails
- `POST /api/v1/valuations/{id}/calculate` - Bewertung berechnen

### Prognosen
- `POST /api/v1/forecasts` - KI-Prognose erstellen
- `GET /api/v1/forecasts/{id}` - Prognosedetails

### Exporte
- `GET /api/v1/exports/excel/{valuation_id}` - Excel-Export
- `GET /api/v1/exports/pdf/{valuation_id}` - PDF-Export

## Deployment

Das Backend wird über GitHub Actions automatisch auf Google Cloud Run deployed:

- **DEV:** Automatisch bei Push auf `develop`
- **STAGE:** Automatisch bei Push auf `stage`
- **PROD:** Automatisch bei Push auf `main`

## Lizenz

Proprietary - Capvero © 2025
