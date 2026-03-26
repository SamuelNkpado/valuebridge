# ValueBridge — Business Valuation & Marketplace Platform

ValueBridge is a full-stack platform that helps Nigerian SME owners get professional business valuations and connect with verified investors through a secure marketplace and deal room.

## Tech Stack
- **Backend:** Python FastAPI + PostgreSQL
- **Frontend:** React + Vite
- **Auth:** JWT tokens

## Live Demo
- Frontend: [your Vercel URL]
- API Docs: [your Render URL]/docs

## Local Setup — Backend

### Prerequisites
- Python 3.10+
- PostgreSQL 14+

### Steps

1. Clone the repository
```bash
git clone https://github.com/SamuelNkpado/valuebridge.git
cd valuebridge
```

2. Create and activate virtual environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create `.env` file in the root directory
```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/valuebridge_db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

5. Create PostgreSQL database
```sql
CREATE DATABASE valuebridge_db;
```

6. Run the server
```bash
uvicorn app.main:app --reload
```

7. Open API docs at `http://127.0.0.1:8000/docs`

## Local Setup — Frontend

1. Clone the frontend repository
```bash
git clone https://github.com/SamuelNkpado/valuebridge-frontend.git
cd valuebridge-frontend
```

2. Install dependencies
```bash
npm install
```

3. Create `.env.local` file
```
VITE_API_URL=http://127.0.0.1:8000
```

4. Run the dev server
```bash
npm run dev
```

5. Open `http://localhost:5173`

## Test Accounts
| Role | Email | Password |
|------|-------|----------|
| SME Owner | john@example.com | password123 |
| Investor | jane@test.com | password123 |
| Admin | admin@valuebridge.com | admin123 |

## Features
- JWT Authentication with role-based access
- Business profile management
- 3-method valuation engine (Asset, DCF, Market Multiples)
- Marketplace with listings, offers and deal rooms
- NDA-gated due diligence process
- Term sheet with mutual approval
- Real-time messaging
- Admin dashboard with advisor verification