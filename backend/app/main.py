"""API minima B0."""
from fastapi import FastAPI
app = FastAPI(title="Enterprise AI OS", version="0.1.0-b0")

@app.get("/health")
def health():
    return {"status": "ok", "app": "Enterprise AI OS", "version": "0.1.0-b0", "phase": "B0"}

@app.get("/")
def root():
    return {"message": "EMPLEADOS_IA API", "docs": "/docs", "health": "/health"}
