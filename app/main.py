from fastapi import FastAPI, Request
from sqlalchemy import text

from app.enums import Codes
from app.responses import success_response
from app.db import engine
from app.db import SessionLocal


app = FastAPI(title="svc-punishments")

@app.get("/live")
def live(request: Request):
    trace_id = request.headers.get("X-Trace-Id")

    return success_response(
        data={"alive": True},
        message="svc-punishments alive",
        code=Codes.LIVE_OK,
        trace_id=trace_id
    )

@app.get("/health")
def health(request: Request):
    trace_id = request.headers.get("X-Trace-Id")

    details: dict[str, str] = {}
    ready = True

    # мемори
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        details["memory"] = "OK"
    except Exception as e:
        details["memory"] = f"ERROR: {str(e)}"
        ready = False

    # датабаза
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        details["database"] = "OK"
    except Exception as e:
        details["database"] = f"ERROR: {str(e)}"
        ready = False


    return success_response(
        data={
            "status": "UP" if ready else "ERROR",
            "ready": ready,
            "details": details
        },
        message="Service is healthy",
        code=Codes.HEALTH_OK,
        trace_id=trace_id
    )
