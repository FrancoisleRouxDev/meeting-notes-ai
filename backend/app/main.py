from fastapi import FastAPI

app = FastAPI(title="Meeting Notes AI")

@app.get("/health")
def health():
    return {"status": "ok"}
