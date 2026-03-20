# Echo Sentinel: The Orb 🪐

**Echo Sentinel** is a decentralized trading soul companion designed for the **X Layer** ecosystem. It combines real-time on-chain portfolio monitoring with AI-driven philosophical guidance to help traders navigate the emotional volatility of the crypto markets.


## 🚀 Overview

The project features a **Desktop Widget (The Orb)** that floats on your screen, pulsing with different colors and intensities based on your current portfolio's health. All complex logic, AI generation, and payment verification are handled securely on our cloud backend.

- **ZEN Mode (Green/Teal)**: Triggered when you are in profit. AI provides reminders of impermanence and the process over luck.
- **INTERVENTION Mode (Red)**: Triggered during significant losses. AI acts as a Stoic companion, providing comfort and emotional stabilization.

## 🧑‍💻 For Judges & End Users (Quick Start)

To experience the Orb, you only need to run the lightweight desktop client. The backend server (which holds the AI models and verifies X Layer payments) is hosted remotely.

### Prerequisites
- Node.js & npm installed

### Launch the Desktop App
1. Clone the repository:
   ```bash
   git clone https://github.com/fuxue0503/echo.git
   cd echo/electron
   ```
2. Install dependencies & Run:
   ```bash
   npm install
   npm start
   ```
*The Orb will appear on your desktop. Enter your X Layer wallet address to begin.*

---

## 🔒 Security & Payment Flow

- **Secure API**: The Gemini API keys are safely stored on the centralized backend. The desktop client only communicates via secure endpoints.
- **Creator Economy**: Unlocking the AI Voice Meditation requires a `1.00 USDT` payment on the **X Layer Mainnet**. 
- **Direct to Creator**: Payments are routed directly to the creator's wallet (`X402_PAY_TO`). The backend independently verifies the transaction hash on-chain (preventing double-spending) before granting the user access to the premium audio stream.

---

## 🛠 For Developers (Backend Setup)

If you wish to host the backend server yourself (e.g., to run your own local instance or contribute to the core Logic), follow these steps:

### Prerequisites
- Python 3.9+
- [OnchainOS CLI](https://onchainos.com) installed and configured.

### Setup
1. Create a `.env` file in the root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   X402_PAY_TO=your_wallet_address_to_receive_payments
   ```
2. Install and run:
   ```bash
   pip install -r requirements.txt
   ./launch.sh
   ```
3. To expose it to the internet for the desktop app, use **ngrok**:
   ```bash
   ngrok http 8888
   ```
4. Then, update the `SERVER_URL` in `electron/main.js` to your new ngrok link.

## 📜 License
MIT License. Created for the X Layer Hackathon.
