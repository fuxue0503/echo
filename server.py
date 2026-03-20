"""
Echo Sentinel — FastAPI Server
Ties together the Risk Agent and Philosophy Agent.
"""
import os
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, Response
from dotenv import load_dotenv

load_dotenv()

from agents.risk_agent import (
    assess, setup_user, load_users, save_users, 
    verify_usdt_transfer, is_tx_processed, log_payment
)
from agents.sage_agent import deliver, get_recent_trades

app = FastAPI(title="Echo Sentinel API", version="1.0.0")

# ── Health Check ───────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "product": "Echo Sentinel - The Orb"}


# ── PnL Assessment + Personalized Insight (one-shot) ─────────────────────────
@app.get("/api/pnl")
def get_pnl(
    address: str  = Query(..., description="Wallet address on X Layer"),
    chain:   str  = Query("xlayer", description="Chain name"),
    paid:    bool = Query(False),
    lang:    str  = Query("cn"),
):
    """
    Assess wallet PnL and immediately generate a Gemini-powered
    personalized philosophical insight from real trade history.
    Returns everything the widget needs in one call.
    """
    address = address.lower()
    # Init user in store if not exists
    user_data = setup_user(address)
    
    # Check if user has active sub or credits
    # For demo transition purpose, if paid=True is passed manually we simulate they are paid via front-end override,
    # otherwise we check DB.
    has_credit = user_data.get("credits", 0) > 0
    is_actively_paid = paid or user_data.get("subscription_active") or has_credit
    
    pnl = assess(address, chain)
    if not pnl or "error" in pnl:
        return JSONResponse(content=pnl or {"error": "Failed to fetch PnL"})

    # Fetch recent trades for personalized insight
    trades = get_recent_trades(address, chain)

    # Generate insight (Gemini if key set, static fallback otherwise)
    insight = deliver(
        mode=pnl["mode"],
        level=pnl["level"],
        pnl_usd=pnl["total_pnl_usd"],
        is_paid=is_actively_paid,
        trades=trades,
        lang=lang,
    )
    
    # Decrement credit if they used one
    if is_actively_paid and not user_data.get("subscription_active") and has_credit:
        users = load_users()
        users[address]["credits"] -= 1
        save_users(users)
        
    return JSONResponse(content={**pnl, **insight})

# ── User Status & Persistence ──────────────────────────────────────────────────
@app.post("/api/watch")
def watch_wallet(wallet: str = Query(...)):
    """Save the wallet to the watch list (users.json)."""
    wallet = wallet.lower()
    user_data = setup_user(wallet)
    return JSONResponse(content={"status": "watching", "wallet": wallet, "user": user_data})

@app.get("/api/user/status")
def user_status(wallet: str = Query(...)):
    """Return user subscription and credit info."""
    wallet = wallet.lower()
    users = load_users()
    user = users.get(wallet, setup_user(wallet))
    return JSONResponse(content=user)

# ── Generate Meditation Content (standalone, for re-generation) ───────────────
@app.post("/api/meditate")
def meditate(
    mode:    str   = Query(...),
    level:   int   = Query(...),
    pnl_usd: float = Query(0.0),
    wallet:  str   = Query("", description="Wallet address for trade context"),
    paid:    bool  = Query(False),
    lang:    str   = Query("cn"),
):
    """Re-generate philosophical content on demand (widget 'Refresh' button)."""
    wallet = wallet.lower()
    trades = get_recent_trades(wallet) if wallet else []
    content = deliver(mode=mode, level=level, pnl_usd=pnl_usd, is_paid=paid, trades=trades, lang=lang)
    return JSONResponse(content=content)



# ── x402 Payment Sessions (in-memory for demo) ────────────────────────────────
import subprocess, json, uuid, base64

X402_ASSET    = os.getenv("X402_ASSET",    "0x1e4a5963abfd975d8c9021ce480b42188849d41d")  # USDT on X Layer
X402_PAY_TO   = os.getenv("X402_PAY_TO",   "0x0000000000000000000000000000000000000001")  # real recipient

@app.get("/api/config")
def get_config():
    """Returns public X Layer config for the frontend."""
    return {
        "xLayerChainId": 196,
        "usdtAddress":   X402_ASSET,
        "treasury":      X402_PAY_TO
    }

@app.post("/api/pay/subscribe")
def pay_subscribe(wallet: str = Query(...), txHash: str = Query(...)):
    """Handle 10 USDT subscription."""
    import time
    wallet = wallet.lower()
    # 1. Prevent Double Spending
    if is_tx_processed(txHash):
        return JSONResponse(status_code=400, content={"error": "Transaction already processed"})

    # 2. Verify On-Chain
    if not verify_usdt_transfer(txHash, wallet, X402_PAY_TO, 10.0):
        return JSONResponse(status_code=400, content={"error": "Invalid or unconfirmed transaction"})

    # 3. Log Payment & Update Credits
    log_payment(txHash, wallet, 10.0, "subscription")
    users = load_users()
    user = users.get(wallet, setup_user(wallet))
    user["subscription_active"] = True
    user["subscription_expires"] = int(time.time() + 30 * 86400) # 30 days
    user["credits"] += 100
    users[wallet] = user
    save_users(users)
    return JSONResponse(content={"status": "success", "user": user})

@app.post("/api/pay/once")
def pay_once(wallet: str = Query(...), txHash: str = Query(...)):
    """Handle 1 USDT single experience."""
    wallet = wallet.lower()
    # 1. Prevent Double Spending
    if is_tx_processed(txHash):
        return JSONResponse(status_code=400, content={"error": "Transaction already processed"})

    # 2. Verify On-Chain
    if not verify_usdt_transfer(txHash, wallet, X402_PAY_TO, 1.0):
        return JSONResponse(status_code=400, content={"error": "Invalid or unconfirmed transaction"})

    # 3. Log Payment & Update Credits
    log_payment(txHash, wallet, 1.0, "once")
    users = load_users()
    user = users.get(wallet, setup_user(wallet))
    user["credits"] += 1
    users[wallet] = user
    save_users(users)
    return JSONResponse(content={"status": "success", "user": user})

@app.get("/api/audio")
def get_audio(
    mode:   str   = Query(...),
    level:  int   = Query(...),
    wallet: str   = Query("demo", description="Wallet address to check payment status"),
):
    """
    Generate Gemini TTS audio for paid users.
    Returns 402 if not paid, audio/wav bytes if paid.
    """
    from agents.sage_agent import generate_audio
    
    wallet = wallet.lower()

    # Check payment
    is_paid = False
    users = load_users()
    user = users.get(wallet, {})
    is_paid = user.get("subscription_active") or user.get("credits", 0) > 0

    if not is_paid:
        # Return simplified payload
        payload = {"error": "Payment required", "tiers": ["subscribe", "once"]}
        encoded = base64.b64encode(json.dumps(payload).encode()).decode()
        return Response(content=encoded, status_code=402, media_type="text/plain")

    audio_bytes = generate_audio(mode, level)
    if audio_bytes is None:
        return JSONResponse(status_code=503, content={"error": "TTS generation failed."})
    return Response(content=audio_bytes, media_type="audio/wav")


@app.get("/widget", response_class=HTMLResponse)
def widget():
    """Serves the compact floating desktop widget (loaded by Electron)."""
    widget_path = static_dir / "widget.html"
    if widget_path.exists():
        return HTMLResponse(content=widget_path.read_text())
    return HTMLResponse(content="<h1>widget.html not found</h1>", status_code=404)


# ── Serve static frontend ──────────────────────────────────────────────────────
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8888, reload=True)
