import logging
from fastapi import FastAPI, BackgroundTasks, status
from schemas import WebhookPayload
from agents import run_multi_agent_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("webhook-gateway")

app = FastAPI(title="Zero Trust Edge Multi-Agent AI")


@app.post("/alert", status_code=status.HTTP_202_ACCEPTED)
async def receive_alert(payload: WebhookPayload, background_tasks: BackgroundTasks):
    logger.info(f"Webhook received ({len(payload.alerts)} alerts). Offloading to background agents...")

    for alert in payload.alerts:
        if alert.status == "firing":
            background_tasks.add_task(run_multi_agent_pipeline, alert)

    return {
        "status": "accepted",
        "queued_alerts": len(payload.alerts),
        "message": "Alerts queued for asynchronous multi-agent evaluation."
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "mode": "asynchronous-multi-agent"}
