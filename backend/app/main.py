from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import r

app = FastAPI(
    title="Yammic demo backend",
    version="0.1.0",
    description="Local demo platform slice. All data is synthetic — prototype, not for clinical use. "
                "Auth: POST /auth/login, then `Authorization: Bearer <token>`. JSON is camelCase.")
# ponytail: wide-open CORS, fine for a local-only demo (Flutter web dev server)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(r)
