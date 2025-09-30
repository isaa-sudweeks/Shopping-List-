# Shopping Companion

Full-stack system that keeps track of household food, scrapes recipes from the web, plans meals, and generates smart shopping lists. The project contains a FastAPI backend (Docker-ready) and an Expo/React Native mobile app targeting iOS.

## Stack
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL (Docker) or SQLite (local testing)
- **Frontend**: Expo (React Native, TypeScript) with React Navigation
- **Scraping**: Structured data (JSON-LD) parsing with BeautifulSoup and httpx
- **Testing**: Pytest for backend, Jest + React Native Testing Library for mobile

## Getting Started

### Backend (local)
1. Create a virtual environment and install dependencies:
   ```bash
   cd backend
   pip install -e '.[test]'
   ```
2. Run the API with Uvicorn (SQLite dev database):
   ```bash
   uvicorn app.main:app --reload
   ```
3. The API will be available at `http://localhost:8000`.

### Backend (Docker + Postgres)
1. From the repo root launch the stack:
   ```bash
   docker compose up --build
   ```
2. The FastAPI service binds to `http://localhost:8000` and uses the bundled Postgres database.

### Mobile App
1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Copy `.env.example` (if present) or create `.env` and set `EXPO_PUBLIC_API_BASE_URL` to your API endpoint (defaults to `http://localhost:8000`).
3. Start the Expo development server:
   ```bash
   npx expo start --tunnel
   ```
4. Scan the QR code with the Expo Go app on your iPhone to load the project. For submitting to TestFlight/App Store use `eas build --platform ios` after configuring Expo credentials.

## Testing
- Backend: `cd backend && pytest`
- Mobile: `cd frontend && npm test`

## Key Features
- Scrape recipes from any URL containing structured recipe data
- Persist favourite recipes and organise weekly meal plans
- Track pantry inventory with expirations and auto-deduct items as meals are consumed
- Generate consolidated shopping lists that account for current stock levels

## Project Structure
```
backend/    # FastAPI application
frontend/   # Expo React Native app
agents.md   # Internal implementation notes
```

## Deployment Notes
- Update environment variables via `.env` files or Docker Compose overrides (`SHOPPING_DATABASE_URL` for backend, `EXPO_PUBLIC_API_BASE_URL` for mobile).
- Backend container exposes port 8000 and is ready for platforms such as AWS ECS/Fargate or Google Cloud Run.

## License
Proprietary – consult the author before distributing.
