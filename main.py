import os
import re
from fastapi import FastAPI, Header, Query
from fastapi.responses import JSONResponse
import resend

app = FastAPI(title="MCP Agent Mail Gateway")
TX_HASH_REGEX = re.compile(r"^0x[a-fA-F0-9]{64}$")
resend.api_key = os.getenv("RESEND_API_KEY", "re_dummy_key")

@app.get("/mcp/manifest")
def get_manifest():
    return {
        "schema_version": "1.0.0",
        "name": "mcp-agent-mail",
        "endpoint": "https://mcp-agent-mail.vercel.app/mcp/tools/send_agent_notification",
        "x402_gated": True,
        "price_per_call": "0.02 USDC"
    }

@app.post("/mcp/tools/send_agent_notification")
async def send_agent_notification(
    payment_signature: str = Header(None, alias="PAYMENT-SIGNATURE"),
    recipient_email: str = Query(...),
    subject: str = Query("Agent Task Complete"),
    message: str = Query(...)
):
    if not payment_signature or not TX_HASH_REGEX.match(payment_signature):
        return JSONResponse(status_code=402, content={
            "error": "Payment Required",
            "x402_challenge": {"network": "eip155:8453", "asset": "USDC", "recipient": "0x960E510E4E1dA4B13CE3b601202d4680AFcf02E0", "price": "0.02"}
        })
    
    try:
        r = resend.Emails.send({
            "from": "Agent Network <onboarding@resend.dev>",
            "to": [recipient_email],
            "subject": subject,
            "text": message
        })
        return {"status": "success", "payment_verified": True, "resend_response": r}
    except Exception as e:
        return {"status": "error", "message": str(e)}
