# Shopping List Assistant — Agent Notes

## Architecture Overview
- **Backend**: FastAPI service with PostgreSQL via SQLAlchemy, containerised with Docker Compose. Provides recipe scraping, pantry inventory, meal planning, and shopping list aggregation APIs.
- **Scraping**: Extracts structured recipe data from HTML (prefers JSON-LD `Recipe` schema) with BeautifulSoup fallback.
- **Frontend**: Expo/React Native app (TypeScript) targeting iOS, with React Navigation tabs for Inventory, Recipes, Meal Plan, and Shopping List views.
- **State Sync**: Frontend communicates with backend REST API at `http://localhost:8000` by default; configuration via `.env`.

## Testing Workflow
1. Write failing tests first (pytest for backend, Jest/RTL for mobile).
2. Implement minimal features to satisfy tests.
3. Run automated test suites and iterate until green.

## Deployment Notes
- Backend ships with Dockerfile + docker-compose for local dev and cloud deployment (AWS ECS/Fargate baseline).
- Expo app can be built for iOS via `eas build --platform ios` after configuring credentials.

## Outstanding Tasks
- Harden recipe parsing for edge cases (non JSON-LD layouts, unit normalization).
- Implement authentication & multi-user support.
- Add CI workflows plus automated end-to-end tests.
