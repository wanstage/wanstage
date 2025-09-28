#!/usr/bin/env zsh
from fastapi import FastAPI

app = FastAPI(title="WANSTAGE API", version="0.1.0")

@app.get("/")
def root():
    return {"WANSTAGE": "API alive"}

@app.get("/health")
def health():
    return {"status": "ok"}
