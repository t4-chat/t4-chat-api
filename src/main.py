from fastapi import FastAPI
from datetime import datetime, timezone

app = FastAPI(
    title="Agg AI API",
    description="API for aggregating multiple AI providers",
    version="0.1.0",
)

@app.get("/ping")
def ping():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }