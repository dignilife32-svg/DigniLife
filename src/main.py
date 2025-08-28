from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title=os.getenv("APP_NAME", "DigniLife API"))

@app.get("/")
def root():
    return {"msg": "Hello DigniLife"}

@app.get("/health")
def health():
    return {"status": "ok"}
