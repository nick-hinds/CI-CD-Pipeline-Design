from fastapi import FastAPI
import os
app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello from Kubernetes!"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api/status")
def status():
    return {"status": "ok"}
