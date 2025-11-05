from fastapi import FastAPI
from app.check import Check
app = FastAPI()

@app.get("/")
def main():
    return {"message": "Hello, World!"}

@app.get("/health")
def health_check():
    checker = Check()
    return {"status": checker.checking()}