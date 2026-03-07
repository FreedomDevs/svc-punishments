from fastapi import FastAPI, Request
from app.enums import Codes
from app.responses import success_response

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