from fastapi import FastAPI

app = FastAPI(title="CLV + Uplift + Policy API")

@app.get("/health")
def health():
    return {"status": "ok"}
