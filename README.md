# Echo: The Orb 🪐
### *Your Emotional Anchor in the Decentralized Market*

**Echo** is a state-of-the-art trading companion for the **X Layer** ecosystem. It transforms dry on-chain data into a living, breathing visual orb and a philosophical voice, helping traders maintain mental equanimity amid market volatility.

---

## 📽️ The Experience

The **Orb** is a desktop-native widget that lives on your screen. It doesn't just show numbers; it reflects your "Trading Soul":

*   **🟢 ZEN STATE**: When your portfolio is thriving, Echo pulses with calm, teal light. Its AI (The Sage) reminds you to stay humble and avoid the trap of greed.
*   **🔴 INTERVENTION**: When the market turns and losses mount, Echo shifts to a deep crimson with sharp, jittery pulses. It proactively interrupts "revenge trading" with Stoic wisdom and calming meditations.

---

## 🧠 Core Intelligence

### 🧬 Risk Agent (On-Chain Awareness)
Built on the **OnchainOS CLI**, Echo doesn't rely on delayed centralized price feeds. It performs real-time queries of your **DEX Realized PnL** directly from the X Layer blockchain, ensuring your "Soul State" is always based on ground truth.

### 🧘 Sage Agent (AI Philosophical Guide)
Powered by **Google Gemini**, the Sage analyzes your actual trade history to provide hyper-personalized insights. It's not just a bot; it's a mentor trained in Eastern philosophy and Western Stoicism.

---

## ⚡ Quick Start for Judges

Experience the Orb in seconds. No complex backend setup required for end-users.

### 1. Requirements
*   Node.js (v16+) & npm

### 2. Launching the Desktop Client
```bash
git clone https://github.com/fuxue0503/echo.git
cd echo/electron
npm install
npm start
```
*Note: The Orb will connect to our hosted backend automatically. Simply input an X Layer wallet address (e.g., `0x...`) to begin monitoring.*

---

## 💳 X Layer Integration Highlights

*   **Native Payments**: Unlock "Premium Voice Meditations" with a seamless **1.00 USDT** transfer on X Layer.
*   **x402 Protocol**: The backend implements its own verification engine to confirm USDT transfers on-chain before unlocking features.
*   **Developer Economy**: All payments go directly to the creator's wallet (`X402_PAY_TO`).

---

## 🛠️ Architecture (For Developers)

If you wish to host your own instance of the Echo ecosystem:

1.  **Backend**: `Python 3.10+` + `FastAPI`.
2.  **Data**: Install `onchainos` CLI and configure OKX API keys.
3.  **Secrets**: Set up `.env` with `GEMINI_API_KEY` and `X402_PAY_TO`.
4.  **Run**: `./launch.sh`

---

## 📜 License
MIT License. Developed for the **X Layer Hackathon**.
