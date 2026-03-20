# Echo Sentinel: The Orb 🪐

**Echo Sentinel** is a decentralized trading soul companion designed for the **X Layer** ecosystem. It combines real-time on-chain portfolio monitoring with AI-driven philosophical guidance to help traders navigate the emotional volatility of the crypto markets.


## 🚀 Overview

The project features a **Desktop Widget (The Orb)** that floats on your screen, pulsing with different colors and intensities based on your current portfolio's health. 

- **ZEN Mode (Green/Teal)**: Triggered when you are in profit. AI provides reminders of impermanence and the importance of process over luck.
- **INTERVENTION Mode (Red)**: Triggered during significant losses. AI acts as a Stoic companion, providing comfort and emotional stabilization to prevent revenge trading.

## ✨ Key Features

- **Real On-Chain PnL**: Powered by the **OnchainOS CLI**, the system fetches authentic DEX realized PnL directly from the X Layer blockchain. No simulation, just pure data.
- **AI Soul Companion**: Uses **Gemini 2.5 Flash** to generate personalized philosophical insights based on your recent trade history.
- **Voice Meditation**: Paid users can unlock high-fidelity TTS audio streams (with ambient background music) for a deep, immersive reflection experience.
- **X Layer Native**: Integrated with the X Layer mainnet for balance tracking and secure USDT payment verification.
- **Double-Spending Protection**: A robust backend ledger ensures every payment txHash is only processed once.

## 🛠 Tech Stack

- **Backend**: Python, FastAPI, Web3.py
- **Frontend**: HTML5, Vanilla CSS, WebGL (Dynamic Orb Visualization)
- **Desktop**: Electron (Floating transparent widget)
- **Data Layer**: [OnchainOS](https://onchainos.com) CLI
- **AI Model**: Google Gemini Pro & Flash

## 📦 Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js & npm
- [OnchainOS CLI](https://onchainos.com) installed and configured with OKX API credentials.

### Steps
1. **Clone the repository**:
   ```bash
   git clone https://github.com/fuxue0503/echo.git
   cd echo
   ```

2. **Configure Environment Variables**:
   Create a `.env` file in the root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   X402_PAY_TO=your_wallet_address_to_receive_payments
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   cd electron && npm install && cd ..
   ```

4. **Launch the Application**:
   Use the provided automation script:
   ```bash
   chmod +x launch.sh
   ./launch.sh
   ```

## 📜 License
MIT License. Created for the X Layer Hackathon.
