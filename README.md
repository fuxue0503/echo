# Echo: The Orb 🪐
### *Your Emotional Anchor in the Decentralized Market*
### *您在去中心化市场中的情绪锚点*

---

[English](#english) | [中文](#chinese)

---

<a name="english"></a>
## 🇺🇸 English Version

### **Overview**
**Echo** is a state-of-the-art trading companion for the **X Layer** ecosystem. It transforms dry on-chain data into a living, breathing visual orb and a philosophical voice, helping traders maintain mental equanimity amid market volatility.

### **📽️ The Experience**
The **Orb** is a desktop-native widget that reflects your "Trading Soul":
*   **🟢 ZEN STATE**: When your portfolio is thriving, Echo pulses with calm, teal light. The Sage AI reminds you to stay humble.
*   **🔴 INTERVENTION**: During significant losses, Echo shifts to deep crimson, interrupting "revenge trading" with Stoic wisdom and meditations.

### **🧠 Core Intelligence**
*   **🧬 Risk Agent (On-Chain Awareness)**: Powered by **OnchainOS CLI**, Echo performs real-time queries of your **DEX Realized PnL** directly from X Layer.
*   **🧘 Sage Agent (AI Philosophical Guide)**: Powered by **Google Gemini**, analyzing your actual trade history to provide hyper-personalized insights.

### **⚡ Quick Start for Judges**
1. **Requirements**: Node.js (v16+) & npm.
2. **Launch Client**:
   ```bash
   git clone https://github.com/fuxue0503/echo.git
   cd echo/electron
   npm install && npm start
   ```

---

<a name="chinese"></a>
## 🇨🇳 中文版

### **项目简介**
**Echo** 是为 **X Layer** 生态系统打造的顶尖交易伴侣。它将枯燥的链上数据转化为一个“有呼吸、有生命”的视觉灵动球（The Orb）和富有哲学深度的语音建议，帮助交易者在市场波动中保持内心的平静。

### **📽️ 产品体验**
**灵动球（The Orb）** 是一个常驻桌面的原生小部件，它不只是显示数字，更是您“交易灵魂”的映射：
*   **🟢 禅定模式 (ZEN)**：当您的投资组合处于盈利时，Echo 闪烁着宁静的青绿色光芒。贤者 AI 会提醒您保持谦逊，避免掉入贪婪的陷阱。
*   **🔴 干预模式 (INTERVENTION)**：当遭遇重大亏损时，Echo 会变为深红色并震颤，通过斯多葛学派的智慧和冥想指导，主动阻止“报复性交易”。

### **🧠 核心智能**
*   **🧬 风险代理 (链上感知)**：基于 **OnchainOS CLI** 构建，Echo 直接从 X Layer 区块链实时查询您的 **DEX 已实现盈亏 (PnL)**，确保感知完全基于事实。
*   **🧘 贤者代理 (AI 哲学引导)**：由 **Google Gemini** 驱动，分析您的真实交易历史，提供高度个性化的洞见。它不仅是一个机器人，更是一位精通东西方哲学的心灵导师。

### **⚡ 评委快速启动**
无需复杂的后端设置，仅需运行桌面客户端即可体验：
1. **环境要求**：Node.js (v16+) 与 npm。
2. **启动客户端**：
   ```bash
   git clone https://github.com/fuxue0503/echo.git
   cd echo/electron
   npm install && npm start
   ```
*注意：桌面端将自动连接到我们的云端服务器。只需输入 X Layer 钱包地址即可开始监控。*

---

## 💳 X Layer 集成亮点 (Integration)

*   **原生支付 (Native Payments)**：通过 X Layer 网络支付 **1.00 USDT** 即可解锁“流媒体语音冥想”。
*   **x402 协议**: 后端实现独立的链上校验引擎，在确认 USDT 转账后自动解锁高级功能。
*   **开发者经济**: 所有收益直接进入创作者地址 (`X402_PAY_TO`)。

---

## 🛠️ 技术架构 (Architecture)
*   **Backend**: Python 3.10+ / FastAPI / Web3.py
*   **Market Data**: [OnchainOS](https://onchainos.com) CLI
*   **AI Model**: Google Gemini 1.5 Flash & Pro

---

## 📜 License
MIT License. Developed for the **X Layer Hackathon**.
