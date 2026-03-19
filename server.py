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

from agents.risk_agent import assess
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
    pnl = assess(address, chain)
    if "error" in pnl:
        return JSONResponse(content=pnl)

    # Fetch recent trades for personalized insight
    trades = get_recent_trades(address, chain)

    # Generate insight (Gemini if key set, static fallback otherwise)
    insight = deliver(
        mode=pnl["mode"],
        level=pnl["level"],
        pnl_usd=pnl["total_pnl_usd"],
        is_paid=paid,
        trades=trades,
        lang=lang,
    )
    return JSONResponse(content={**pnl, **insight})


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
    trades = get_recent_trades(wallet) if wallet else []
    content = deliver(mode=mode, level=level, pnl_usd=pnl_usd, is_paid=paid, trades=trades, lang=lang)
    return JSONResponse(content=content)


@app.get("/api/demo")
def demo(scenario: str = Query("profit_high", description="profit_low|profit_high|loss_low|loss_high"), lang: str = "cn"):
    """Returns mock assessment data for demo without a real wallet address."""
    scenarios = {
        "profit_low":  {"mode": "ZEN",          "level": 1, "total_pnl_usd": 45.00,   "orb_state": "MONITORING"},
        "profit_high": {"mode": "ZEN",          "level": 3, "total_pnl_usd": 820.00,  "orb_state": "MONITORING"},
        "loss_low":    {"mode": "INTERVENTION", "level": 1, "total_pnl_usd": -38.00,  "orb_state": "INTERVENTION"},
        "loss_high":   {"mode": "INTERVENTION", "level": 3, "total_pnl_usd": -490.00, "orb_state": "INTERVENTION"},
    }
    data = scenarios.get(scenario, scenarios["profit_high"])

    # Provide realistic mock trades based on scenario for Gemini to use
    if data["mode"] == "ZEN":
        mock_trades = [
            {"tokenSymbol": "WETH", "realizedPnlUsd": "850.00", "unrealizedPnlUsd": "400.00"},
            {"tokenSymbol": "OKB", "realizedPnlUsd": "0", "unrealizedPnlUsd": "50.00"},
            {"tokenSymbol": "MEME", "realizedPnlUsd": "-80.00", "unrealizedPnlUsd": "0"},
        ]
    else:
        mock_trades = [
            {"tokenSymbol": "DOGE", "realizedPnlUsd": "-500.00", "unrealizedPnlUsd": "-350.00"},
            {"tokenSymbol": "SHIB", "realizedPnlUsd": "0", "unrealizedPnlUsd": "-120.00"},
        ]

    # Auto-generate content (demo simulates a paid session to test TTS audio)
    content = deliver(
        mode=data["mode"],
        level=data["level"],
        pnl_usd=data["total_pnl_usd"],
        is_paid=True,  # Simulate paid unlock so user can hear the AI voice
        trades=mock_trades,
        lang=lang
    )
    return JSONResponse(content={**data, **content})


# ── x402 Payment Sessions (in-memory for demo) ────────────────────────────────
import subprocess, json, uuid, base64
from google import genai
from google.genai import types as genai_types

paid_sessions: dict[str, bool] = {}   # wallet_address -> True if paid

# x402 constants (change to real contract/address for production)
X402_NETWORK  = "eip155:196"          # X Layer mainnet
X402_ASSET    = os.getenv("X402_ASSET",    "0x4ae46a509f6b1d9056937ba4500cb143933d2dc8")  # USDG on X Layer
X402_PAY_TO   = os.getenv("X402_PAY_TO",  "0x0000000000000000000000000000000000000001")  # demo recipient
X402_AMOUNT   = os.getenv("X402_AMOUNT",  "100000")   # 0.10 USDG (6 decimals)


@app.post("/api/pay")
def pay_x402(wallet: str = Query(..., description="User wallet address")):
    """
    Initiate x402 payment to unlock audio meditation.
    Calls onchainos CLI to sign an EIP-3009 transferWithAuthorization.
    Returns payment proof or error.
    """
    try:
        result = subprocess.run(
            [
                "onchainos", "payment", "x402-pay",
                "--network",             X402_NETWORK,
                "--amount",              X402_AMOUNT,
                "--pay-to",              X402_PAY_TO,
                "--asset",               X402_ASSET,
                "--from",                wallet,
                "--max-timeout-seconds", "300",
            ],
            capture_output=True, text=True, timeout=60,
            env={**os.environ}
        )
        if result.returncode != 0:
            return JSONResponse(
                status_code=402,
                content={"error": "Payment failed", "detail": result.stderr.strip()}
            )
        # Mark wallet as paid
        paid_sessions[wallet.lower()] = True
        proof = json.loads(result.stdout) if result.stdout.strip().startswith("{") else {"raw": result.stdout}
        return JSONResponse(content={"paid": True, "proof": proof})
    except subprocess.TimeoutExpired:
        return JSONResponse(status_code=408, content={"error": "onchainos timed out"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


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
    from agents.sage_agent import CONTENT, generate_audio

    # Check payment — 'demo' wallet always considered paid
    is_paid = (wallet == "demo") or paid_sessions.get(wallet.lower(), False)
    if not is_paid:
        # Return x402 response so client knows what to pay
        payload = {
            "x402Version": 2,
            "accepts": [{
                "network": X402_NETWORK,
                "amount": X402_AMOUNT,
                "payTo": X402_PAY_TO,
                "asset": X402_ASSET,
                "maxTimeoutSeconds": 300,
            }]
        }
        encoded = base64.b64encode(json.dumps(payload).encode()).decode()
        return Response(content=encoded, status_code=402, media_type="text/plain")

    audio_bytes = generate_audio(mode, level)
    if audio_bytes is None:
        return JSONResponse(status_code=503, content={"error": "TTS generation failed. Check GEMINI_API_KEY."})
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
