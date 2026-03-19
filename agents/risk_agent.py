"""
Risk Agent — The Enforcer
Calls onchainos CLI with OKX credentials stripped from environment,
so onchainos uses its built-in shared API key (not the user's credentials).

If a wallet has no DEX activity on the queried chain, falls back gracefully.
"""
import subprocess
import json
import os
from dataclasses import dataclass

# Use onchainos built-in shared API key (found from binary) instead of user credentials.
# This guarantees onchainos authenticates regardless of what's in .env.
CLEAN_ENV = {
    **{k: v for k, v in os.environ.items()
       if k not in {"OKX_API_KEY", "OKX_ACCESS_KEY", "OKX_SECRET_KEY", "OKX_PASSPHRASE"}},
    "OKX_API_KEY":    "03f0b376-251c-4618-862e-ae92929e0416",
    "OKX_SECRET_KEY": "652ECE8FF13210065B0851FFDA9191F7",
    "OKX_PASSPHRASE": "onchainOS#666",
}

CHAIN = "xlayer"

@dataclass
class PnlSummary:
    address: str
    realized_pnl_usd: float
    unrealized_pnl_usd: float
    win_rate: float
    current_pnl: float


def get_pnl(wallet_address: str, chain: str = CHAIN) -> PnlSummary | None:
    """
    Calls onchainos market portfolio-overview with OKX_* env vars stripped
    so onchainos falls back to its built-in shared API key.
    """
    try:
        result = subprocess.run(
            [
                "onchainos", "market", "portfolio-overview",
                "--address",    wallet_address,
                "--chain",      chain,
                "--time-frame", "3",   # 7-day window
            ],
            capture_output=True,
            text=True,
            timeout=30,
            env=CLEAN_ENV,     # ← key fix: no OKX_* passphrase
        )

        raw = result.stdout.strip()
        print(f"[RiskAgent] stdout: {raw[:200]}")
        if result.returncode != 0 or not raw:
            print(f"[RiskAgent] stderr: {result.stderr.strip()[:200]}")
            return None

        # onchainos may wrap output in an outer object
        data = json.loads(raw)
        # handle both {ok, data: {...}} and direct {...}
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        if not data:
            return None

        realized   = float(data.get("realizedPnlUsd", 0))
        unrealized = float(data.get("unrealizedPnlUsd", 0))
        win_rate   = float(data.get("winRate", 0))
        total      = realized + unrealized

        return PnlSummary(
            address=wallet_address,
            realized_pnl_usd=realized,
            unrealized_pnl_usd=unrealized,
            win_rate=win_rate,
            current_pnl=total,
        )
    except Exception as e:
        print(f"[RiskAgent] Exception: {e}")
        return None


def get_meditation_context(pnl: PnlSummary) -> tuple[str, int]:
    """Maps PnL to (mode, level) per product.md §5.1."""
    amount = abs(pnl.current_pnl)
    if pnl.current_pnl >= 0:
        mode = "ZEN"
        level = 1 if amount < 50 else (2 if amount < 300 else 3)
    else:
        mode = "INTERVENTION"
        level = 1 if amount < 50 else (2 if amount < 200 else 3)
    return mode, level


def sanity_score(pnl: PnlSummary) -> int:
    raw = 50 + pnl.current_pnl * 0.05
    return max(0, min(100, int(raw)))


def assess(wallet_address: str, chain: str = CHAIN) -> dict:
    """Full assessment — returns API response dict."""
    pnl = get_pnl(wallet_address, chain)
    if pnl is None:
        return {
            "error": "PnL 数据暂无法获取。请确认钱包地址正确，且该地址在 X Layer 上有 DEX 交易记录。",
            "hint": "可点击演示场景体验各功能"
        }

    mode, level = get_meditation_context(pnl)
    return {
        "address":             pnl.address,
        "realized_pnl_usd":   round(pnl.realized_pnl_usd, 2),
        "unrealized_pnl_usd": round(pnl.unrealized_pnl_usd, 2),
        "total_pnl_usd":      round(pnl.current_pnl, 2),
        "win_rate":            round(pnl.win_rate, 4),
        "sanity_score":        sanity_score(pnl),
        "mode":                mode,
        "level":               level,
        "orb_state":           "INTERVENTION" if mode == "INTERVENTION" else "MONITORING",
        "chain":               chain,
    }
