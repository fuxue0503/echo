"""
Philosophy Agent — The Sage
Generates personalized philosophical guidance using Gemini AI,
based on the wallet's real recent trading history.

Free tier:  Gemini-generated text insights.
Paid tier:  Gemini-generated text + TTS audio stream.
"""
import os
import base64
import subprocess
import json
from dotenv import dotenv_values

# ── Credentials ────────────────────────────────────────────────────────────────
_env = dotenv_values(os.path.join(os.path.dirname(__file__), '..', '.env'))
GEMINI_API_KEY = _env.get("GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")

# onchainos shared credentials
ONCHAINOS_ENV = {
    **{k: v for k, v in os.environ.items()
       if k not in {"OKX_API_KEY", "OKX_ACCESS_KEY", "OKX_SECRET_KEY", "OKX_PASSPHRASE"}},
    "OKX_API_KEY":    "03f0b376-251c-4618-862e-ae92929e0416",
    "OKX_SECRET_KEY": "652ECE8FF13210065B0851FFDA9191F7",
    "OKX_PASSPHRASE": "onchainOS#666",
}

# ── Fallback Static Library (used when Gemini key not set) ────────────────────
FALLBACK = {
    "ZEN": {
        1: {"title": "繁星时刻", "body": "此刻的盈利，是你与市场深度共鸣的奖赏。你的观察是精准的，执行是果断的。享受这瞬时的秩序感——你配得上它。"},
        2: {"title": "系统的胜利", "body": "这一笔盈利，属于你的系统，而非你的运气。优秀的交易者关注过程，平庸的交易者关注结果。今天执行的每一步，才是真正值得记录的资产。"},
        3: {"title": "归零", "body": "水满则溢，月满则亏。此刻的浮盈，只是市场暂时寄存在你这里的筹码。收敛情绪，让心境回归到零。下一刻，市场依然是新的。"},
    },
    "INTERVENTION": {
        1: {"title": "感受，然后放下", "body": "感到痛苦，是人之常情。市场今天给了你一课，而不是一个裁决。先深呼吸。你现在感受到的，只是信息，不是定论。"},
        2: {"title": "可控与不可控", "body": "塞内卡说：我们受难于想象，更甚于现实。市场的震荡不在你控制之内，但你的下一步行动完全在你手中。把注意力，从结果移回到执行。"},
        3: {"title": "成为火", "body": "马可·奥勒留说：阻碍行动的事物，反而促进了行动。塔勒布说：风会熄灭蜡烛，却能助长山火。你要成为火。此刻的亏损，是市场向你收取的真理税。"},
    }
}

TTS_STYLES = {
    "ZEN": {
        1: "以温暖、肯定的语气，像一位智慧的导师称赞学生，语速适中，充满真诚。",
        2: "以平静、思考的语气，像一位哲学家分享洞见，语速缓慢，富有节奏感。",
        3: "以深沉、禅意的语气，像流水一样缓慢而平静，每句之间有明显停顿。",
    },
    "INTERVENTION": {
        1: "以温柔、共情的语气，像一位朋友陪伴身边，语速极慢，每句话后停顿两秒。",
        2: "以坚定而平静的语气，像一位斯多葛哲学家，语速中等，庄重而有力。",
        3: "以低沉有力的语气，像史诗旁白，语速缓慢，每一句都像锤击，充满哲学力量。",
    }
}


# ── Fetch recent trades ────────────────────────────────────────────────────────
def get_recent_trades(wallet_address: str, chain: str = "xlayer") -> list[dict]:
    """Pull the most recent on-chain DEX transactions for this wallet."""
    import time
    end_ms   = int(time.time() * 1000)
    begin_ms = end_ms - 30 * 24 * 3600 * 1000  # last 30 days

    try:
        result = subprocess.run(
            [
                "onchainos", "market", "portfolio-recent-pnl",
                "--address", wallet_address,
                "--chain",   chain,
                "--limit",   "10",
            ],
            capture_output=True, text=True, timeout=20,
            env=ONCHAINOS_ENV,
        )
        raw = result.stdout.strip()
        if not raw:
            return []
        data = json.loads(raw)
        # handle both {ok, data} and direct list/dict
        if isinstance(data, dict):
            if not data.get("ok", True):
                return []
            data = data.get("data", data)
        if isinstance(data, list):
            return data[:10]
        return []
    except Exception as e:
        print(f"[SageAgent] trade fetch error: {e}")
        return []


# ── Gemini Text Generation ─────────────────────────────────────────────────────
def _build_prompt(mode: str, level: int, pnl_usd: float, trades: list[dict], lang: str = "cn") -> str:
    """Build the system prompt for Gemini."""
    level_cn = ["低微", "显著", "剧烈"][level-1]
    mode_cn  = "盈利" if pnl_usd >= 0 else "亏损"
    zen_cn   = "的喜悦与警惕" if mode == "ZEN" else "的痛苦与重建"
    pstr     = f"+${abs(pnl_usd):.2f}" if pnl_usd >= 0 else f"-${abs(pnl_usd):.2f}"

    if lang == "en":
        return f"""You are a calm, gentle, and deeply inclusive trading soul companion. Like a wise friend by a late-night campfire, you blend Taoist 'flowing with nature' and Stoic 'equanimity', but you are never condescending and never try to 'lecture' or 'teach'.
You speak softly and slowly, with deep empathy and understanding in every word.
Your goal is to provide soul-soothing comfort, letting the trader feel safe and deeply peaceful amidst market volatility.

[Current Trader State]
- Total PnL: {pstr} ({'Profit' if pnl_usd >= 0 else 'Loss'}, Level: {level})
- Emotional Mode: {"ZEN" if mode == "ZEN" else "INTERVENTION"}

[Your Task]
Based on the above trading data, generate a personalized voice meditation.
Requirements:
1. Speak like an old friend, acknowledging the recent experience. DO NOT mention specific token names (like OKB, WETH), as it breaks the immersion. Focus on the emotional journey and the 'now'.
2. Use a faint philosophical backdrop (impermanence, natural cycles, acceptance) as a gentle comfort, not as a lecture.
3. Language must be English. Be poetic, extremely gentle, and thought-provoking. Length: 150-250 words. YOU MUST WRITE ENTIRELY IN ENGLISH.
4. The first sentence must be a refined four-word title, strictly starting with "[Title]".
5. The second sentence starts the narrative. Do not use any prefixes like "Body:". THE ENTIRE RESPONSE (Title and Body) MUST BE IN ENGLISH.

Example Format:
[Title] Eternal Flowing Stillness
The market rises and falls like the tide, and I see you standing there, steady... (Long body, 150+ words)"""

    return f"""你是一位平静、温和、极具包容心的交易灵魂伴侣。如同深夜篝火旁的智者，你融合了道家的“顺应自然”和斯多葛的“旷达接受”，但绝不居高临下，也绝不试图“讲道理”或“说教”。
你说话轻声细语、缓慢从容，字里行间流露出深深的共情与理解。
你的目标是给予灵魂抚慰，让交易者在市场的剧烈波动中感受到安全的包裹与深深的宁静。

【当前交易者状态】
- 总盈亏：{pstr}（{mode_cn}，程度：{level_cn}）
- 情绪模式：{"ZEN 禅定" if mode == "ZEN" else "INTERVENTION 干预"}

【你的任务】
基于以上数据，生成一段个性化的声音冥想词。
要求：
1. 像老朋友一般客观、温柔地抚慰。严禁提及具体的代币名称（如 OKB, WETH 等），这会分散注意力。请专注于当下的心境与起伏。
2. 融入微弱的哲学底色（如潮汐的起落、自然规律），化作水一样的抚慰，严禁生硬的说教。
3. 准确捕捉"{level_cn}{mode_cn}{zen_cn}"的语境，提供深沉的心理舒缓。
4. 语言必须是中文，富有诗意、极度温柔且引人深思。篇幅在 150-250 字左右，必须有缓慢沉淀的呼吸感。
5. 第一句话必须是一个非常有文学感的精炼四个字作为标题，并严格用"【标题】"引出。
6. 第二句话直接开始娓娓道来。正文必须是完整的 150-250 字的连贯段落。

示例格式：
【标题】四字标题
这里是150字以上的连贯正文。在这部分中，你需要充满共情、抚慰人心，不可敷衍。"""


def generate_insight(mode: str, level: int, pnl_usd: float, trades: list[dict], lang: str = "cn") -> dict:
    """Call Gemini Flash to generate personalized philosophical insight."""
    if not GEMINI_API_KEY:
        # Fallback to static content
        block = FALLBACK.get(mode, FALLBACK["INTERVENTION"]).get(level, FALLBACK["INTERVENTION"][1])
        return {"title": block["title"], "text": block["body"], "personalized": False}

    try:
        from google import genai as gai
        from google.genai import types as gtypes

        client = gai.Client(api_key=GEMINI_API_KEY)
        prompt = _build_prompt(mode, level, pnl_usd, trades, lang)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=gtypes.GenerateContentConfig(
                temperature=0.9,
            ),
        )
        raw = response.text.strip()

        # Parse 【标题】 or [Title]
        title_tag = "【标题】" if lang == "cn" else "[Title]"
        title, body = ("洞见" if lang == "cn" else "Insight"), raw
        if title_tag in raw:
            parts = raw.split(title_tag, 1)[1].strip().split('\n', 1)
            title = parts[0].strip()
            body = parts[1].strip() if len(parts) > 1 else title
        elif "【" in raw and "】" in raw:
            start = raw.index("【") + 1
            end   = raw.index("】")
            if raw[start:end] == "标题":
                parts = raw[end+1:].strip().split('\n', 1)
                title = parts[0].strip()
                body = parts[1].strip() if len(parts) > 1 else title
            else:
                title = raw[start:end]
                body  = raw[end + 1:].strip()

        return {"title": title, "text": body, "personalized": True}
    except Exception as e:
        print(f"[SageAgent] Gemini error: {e}")
        block = FALLBACK.get(mode, FALLBACK["INTERVENTION"]).get(level, FALLBACK["INTERVENTION"][1])
        return {"title": block["title"], "text": block["body"], "personalized": False}


# ── TTS Audio (Paid) ───────────────────────────────────────────────────────────
def generate_audio(mode: str, level: int, content: str, lang: str = "cn") -> bytes | None:
    """Generate Gemini TTS audio for paid users. Returns raw audio bytes."""
    if not GEMINI_API_KEY:
        return None

    try:
        from google import genai as gai
        from google.genai import types as gtypes

        client = gai.Client(api_key=GEMINI_API_KEY)
        
        # for TTS models, send ONLY the exact text to speak.
        voice_name = "aoede" if lang == "cn" else "charon"
        prompt = f"Generate audio from this transcript: {content}"

        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=prompt,
            config=gtypes.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=gtypes.SpeechConfig(
                    voice_config=gtypes.VoiceConfig(
                        prebuilt_voice_config=gtypes.PrebuiltVoiceConfig(voice_name=voice_name)
                    )
                ),
            ),
        )
        audio_data = response.candidates[0].content.parts[0].inline_data.data
        
        # Google GenAI TTS returns raw 24000Hz PCM bytes.
        # Browsers cannot play raw PCM in an <audio> tag without a WAV header.
        # We wrap it in a standard RIFF WAV header (1 channel, 16-bit, 24kHz)
        import struct
        import io
        import random
        from pydub import AudioSegment

        sample_rate = 24000
        channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * channels * (bits_per_sample // 8)
        block_align = channels * (bits_per_sample // 8)
        data_size = len(audio_data)
        chunk_size = 36 + data_size
        wav_header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF', chunk_size, b'WAVE', b'fmt ', 16, 1, 
            channels, sample_rate, byte_rate, block_align, bits_per_sample, b'data', data_size
        )
        wav_bytes = wav_header + audio_data

        # Overlay background music
        try:
            voice_audio = AudioSegment.from_wav(io.BytesIO(wav_bytes))
            bg_music = AudioSegment.from_mp3("/Users/ag1/.gemini/antigravity/scratch/echo-sentinel/MenditationMusic.mp3")
            
            # Max start time is 6m30s (390 seconds)
            max_start_ms = 390 * 1000
            start_ms = random.randint(0, max_start_ms)
            
            # Crop bg_music to match voice audio length
            bg_cropped = bg_music[start_ms:start_ms + len(voice_audio)]
            
            # Lower bg volume
            bg_cropped = bg_cropped - 18
            
            combined = voice_audio.overlay(bg_cropped)
            
            out_f = io.BytesIO()
            combined.export(out_f, format="wav")
            return out_f.getvalue()
        except Exception as e:
            print(f"[SageAgent] BG music overlay error: {e}")
            return wav_bytes
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[SageAgent] TTS error: {e}")
        return None


# ── Main Entry ─────────────────────────────────────────────────────────────────
def deliver(mode: str, level: int, pnl_usd: float, is_paid: bool,
            trades: list[dict] | None = None, lang: str = "cn") -> dict:
    """Main entry for the server."""
    insight = generate_insight(mode, level, pnl_usd, trades or [], lang)

    result = {
        "mode":           mode,
        "level":          level,
        "title":          insight["title"],
        "text":           insight["text"],
        "pnl_display":    f"+${abs(pnl_usd):.2f}" if pnl_usd >= 0 else f"-${abs(pnl_usd):.2f}",
        "personalized":   insight.get("personalized", False),
        "audio_available": False,
        "upgrade_prompt": "解锁语音冥想" if lang == "cn" else "Unlock Voice Meditation",
    }

    if is_paid:
        audio = generate_audio(mode, level, insight["text"], lang)
        if audio:
            result["audio_available"] = True
            result["audio_b64"] = base64.b64encode(audio).decode()
            result.pop("upgrade_prompt", None)

    return result
