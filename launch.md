# 🌌 Launch Echo Sentinel Demo Locally

Follow these steps to run the Echo Sentinel production-ready demo on your machine and allow external users (like hackathon judges) to access the dashboard.

## 1. Prerequisites
- **Python**: 3.9 or higher.
- **Node.js**: 16.x or higher (required for the Electron Desktop App).
- **Wallet**: OKX Wallet (recommended) or MetaMask connected to **X Layer Mainnet** (Chain ID: 196).
- **Assets**: Small amount of **OKB** for gas & **USDT** for testing the payment flow.

## 2. Quick Start (One-Click Launch)
We provide a unified launcher that handles environment setup and starts both the backend and the desktop app.

```bash
# Clone the repository and enter the directory
chmod +x launch.sh
./launch.sh
```

**What this script does:**
1.  Creates a Python virtual environment (`venv`) and installs `requirements.txt`.
2.  Installs Electron dependencies in the `electron/` folder.
3.  Cleans up any existing processes on Port `8888`.
4.  Starts the **Python FastAPI Server** in the background.
5.  Launches the **Echo Sentinel Orb** (Electron Floating Widget).

---

## 3. The Desktop Orb (Electron)
The Orb is a WebGL-powered floating widget that sits on your desktop.
- **IDLE (Teal)**: Waiting for wallet input.
- **MONITORING (Gold)**: Real-time assessment of your trading sanity.
- **INTERVENTION (Red)**: Triggered during significant losses to provide philosophical grounding.
- **Right-Click**: Access a quick "Zen Review" with Stoic quotes.

---

## 4. Billing & User Logic
Echo Sentinel uses a hybrid persistence layer for high-speed demo verification.

### 💳 Billing Tiers (USDT on X Layer)
- **Single Experience**: `1 USDT` = 1 Credit (1 personalized voice session).
- **Monthly Subscription**: `10 USDT` = 30 Days + 100 Credits (Continuous monitoring).

### 🛡️ Security: The Payment Ledger
We implement **Double-Spending Protection** via a persistent ledger (`payments.json`).
1.  **Transaction Submission**: When a user pays, the frontend sends the `txHash` to the server.
2.  **Ledger Check**: The server rejects the request if the `txHash` exists in `payments.json`.
3.  **On-Chain Verification**: The `RiskAgent` uses an RPC call to X Layer to verify:
    - Transaction status is **Successful**.
    - Sender matches the user's wallet.
    - Recipient matches the configured **Treasury Address** in `.env`.
    - Asset is the correct **USDT Contract**.
    - Amount meets the required tier.

### 📝 User State (`users.json`)
Tracks wallet mapping, remaining credits, and subscription expiry.

---

## 5. External Access (ngrok)
To let judges use your local dashboard:

```bash
# Run in a new terminal tab
ngrok http 8888
```
Copy the `https://xxxx.ngrok-free.app` URL and distribute it.

---

## 6. Troubleshooting
- **Port 8888 Occupied**: `launch.sh` tries to kill previous instances automatically. If it fails, run `lsof -ti:8888 | xargs kill -9`.
- **RPC Errors**: Ensure your network has access to `https://rpc.xlayer.tech`.
- **Gemini Missing**: If `GEMINI_API_KEY` is not in `.env`, the system falls back to static philosophical quotes and disables AI TTS audio.

---
> [!IMPORTANT]
> **Mainnet Only**: Verification logic is hardcoded for **X Layer Mainnet**. Testnet transactions will be rejected by the `RiskAgent`.
