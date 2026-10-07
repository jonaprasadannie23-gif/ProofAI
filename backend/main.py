from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

app = FastAPI(
    title="ProofAI",
    description="Proof-Carrying Data Analyst API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server (localhost)
        "http://127.0.0.1:5173",  # Vite dev server (127.0.0.1)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {"status": "ok", "service": "ProofAI"}


@app.get("/health")
def health():
    """Liveness check — returns 200 when the backend is up."""
    return {"status": "ok", "service": "ProofAI", "version": app.version}
