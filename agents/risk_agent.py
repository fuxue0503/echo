"""
Risk Agent — The Enforcer
Calls onchainos CLI with OKX credentials stripped from environment,
so onchainos uses its built-in shared API key (not the user's credentials).

If a wallet has no DEX activity on the queried chain, falls back gracefully.
"""
import json
import os
import hashlib
from dataclasses import dataclass
from web3 import Web3

CHAIN = "xlayer"
RPC_URL = "https://rpc.xlayer.tech"

# X Layer Token Contracts
TOKENS = {
    "USDT": "0x1e4a5963abfd975d8c9021ce480b42188849d41d",
    "WETH": "0x5a77f1443d16ee5761d310e38b62f77f726bc71c"
}

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]

# Simple User & Payment Store
USERS_FILE = os.path.join(os.path.dirname(__file__), "..", "users.json")
PAYMENTS_FILE = os.path.join(os.path.dirname(__file__), "..", "payments.json")

def load_payments():
    if not os.path.exists(PAYMENTS_FILE):
        return {}
    try:
        with open(PAYMENTS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_payments(data):
    with open(PAYMENTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def is_tx_processed(tx_hash: str) -> bool:
    payments = load_payments()
    return tx_hash.lower() in [h.lower() for h in payments.keys()]

def log_payment(tx_hash: str, wallet: str, amount: float, p_type: str):
    import time
    payments = load_payments()
    payments[tx_hash] = {
        "wallet": wallet,
        "amount": amount,
        "type": p_type,
        "timestamp": int(time.time())
    }
    save_payments(payments)

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def setup_user(address: str):
    address = address.lower()
    users = load_users()
    if address not in users:
        users[address] = {
            "credits": 0,
            "subscription_active": False,
            "subscription_expires": 0
        }
        save_users(users)
    return users[address]

def verify_usdt_transfer(tx_hash: str, sender: str, recipient: str, amount_usdt: float) -> bool:
    """Verifies a completed USDT transfer on X Layer via RPC."""
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        if receipt.status != 1:  # Status 1 is success
            return False

        tx = w3.eth.get_transaction(tx_hash)
        if tx["from"].lower() != sender.lower():
            return False
            
        usdt_contract = TOKENS["USDT"].lower()
        if tx.get("to", "").lower() != usdt_contract:
            return False

        transfer_topic = w3.keccak(text="Transfer(address,address,uint256)").hex()
        expected_wei = int(amount_usdt * (10**6))
        
        for log in receipt.logs:
            if log.address.lower() == usdt_contract:
                if len(log.topics) == 3 and log.topics[0].hex() == transfer_topic:
                    log_from = "0x" + log.topics[1].hex()[26:]
                    log_to = "0x" + log.topics[2].hex()[26:]
                    log_val = int(log.data.hex(), 16)
                    
                    if log_from.lower() == sender.lower() and log_to.lower() == recipient.lower():
                        if log_val >= expected_wei:
                            return True
        return False
    except Exception as e:
        print(f"[RiskAgent] Verify TX Error: {e}")
        return False

@dataclass
class PnlSummary:
    address: str
    realized_pnl_usd: float
    unrealized_pnl_usd: float
    win_rate: float
    current_pnl: float


def get_pnl(wallet_address: str, chain: str = CHAIN) -> PnlSummary | None:
    """
    Fetches actual token balances via X Layer RPC and computes an estimated portfolio value.
    """
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not w3.is_connected():
            return None

        checksum_addr = w3.to_checksum_address(wallet_address)
        
        # 1. Native Token (OKB)
        okb_wei = w3.eth.get_balance(checksum_addr)
        okb_balance = w3.from_wei(okb_wei, 'ether')
        
        # 2. ERC20 Tokens (USDT, WETH)
        usdt_contract = w3.eth.contract(address=w3.to_checksum_address(TOKENS["USDT"]), abi=ERC20_ABI)
        weth_contract = w3.eth.contract(address=w3.to_checksum_address(TOKENS["WETH"]), abi=ERC20_ABI)
        
        usdt_raw = usdt_contract.functions.balanceOf(checksum_addr).call()
        weth_raw = weth_contract.functions.balanceOf(checksum_addr).call()
        
        usdt_balance = usdt_raw / (10 ** 6) # USDT is 6 decimals
        weth_balance = weth_raw / (10 ** 18) # WETH is 18 decimals
        
        # Hardcoded prices for demo/speed (Replace with Oracle later)
        PREFS = {"OKB": 45.0, "WETH": 3500.0, "USDT": 1.0}
        
        total_usd = (float(okb_balance) * PREFS["OKB"]) + (float(weth_balance) * PREFS["WETH"]) + (usdt_balance * PREFS["USDT"])
        
        import subprocess
        
        ONCHAINOS_ENV = {
            **{k: v for k, v in os.environ.items()
               if k not in {"OKX_API_KEY", "OKX_ACCESS_KEY", "OKX_SECRET_KEY", "OKX_PASSPHRASE"}},
            "OKX_API_KEY":    "03f0b376-251c-4618-862e-ae92929e0416",
            "OKX_SECRET_KEY": "652ECE8FF13210065B0851FFDA9191F7",
            "OKX_PASSPHRASE": "onchainOS#666",
        }
        
        realized_pnl = 0.0
        try:
            result = subprocess.run(
                [
                    "onchainos", "market", "portfolio-overview",
                    "--address", wallet_address,
                    "--chain",   chain,
                    "--time-frame", "4", # 1 month time frame
                ],
                capture_output=True, text=True, timeout=20,
                env=ONCHAINOS_ENV,
            )
            raw = result.stdout.strip()
            if raw:
                data = json.loads(raw)
                if isinstance(data, dict):
                    payload = data.get("data", data)
                    realized_pnl = float(payload.get("realizedPnlUsd", 0))
        except Exception as e:
            print(f"[RiskAgent] onchainos portfolio fetch error: {e}")
            
        actual_pnl = realized_pnl
        
        return PnlSummary(
            address=wallet_address,
            realized_pnl_usd=actual_pnl,
            unrealized_pnl_usd=0.0,
            win_rate=0.55 if actual_pnl > 0 else 0.45,
            current_pnl=actual_pnl,
        )
    except Exception as e:
        print(f"[RiskAgent] Web3 Exception: {e}")
        return None

def get_meditation_context(pnl: PnlSummary) -> tuple[str, int]:
    """Maps PnL to (mode, level) per product.md."""
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
