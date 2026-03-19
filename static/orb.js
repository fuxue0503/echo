/**
 * Echo Sentinel — The Orb WebGL Widget + App Controller
 *
 * State Machine: IDLE → MONITORING → INTERVENTION
 * Right-click → Zen Review overlay
 * Hover → Sanity Score tooltip
 */

// ── State ─────────────────────────────────────────────────────────────────────
const STATE = { IDLE: 'IDLE', MONITORING: 'MONITORING', INTERVENTION: 'INTERVENTION' };
let currentState = STATE.IDLE;
let currentData = null;
let animFrame = null;
let pollInterval = null;

// ── Colors per state ──────────────────────────────────────────────────────────
const COLORS = {
  IDLE:         { r: 0.00, g: 0.83, b: 0.78, glow: '#00d4c8' },
  MONITORING:   { r: 0.94, g: 0.71, b: 0.16, glow: '#f0b429' },
  INTERVENTION: { r: 0.75, g: 0.22, b: 0.17, glow: '#c0392b' },
};

// ── Canvas Setup ──────────────────────────────────────────────────────────────
const canvas = document.getElementById('orb-canvas');
const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
const SIZE = 260;
canvas.width = SIZE; canvas.height = SIZE;

// ── WebGL Shader Sources ──────────────────────────────────────────────────────
const VS_SOURCE = `
  attribute vec2 a_position;
  void main() { gl_Position = vec4(a_position, 0.0, 1.0); }
`;

const FS_SOURCE = `
  precision mediump float;
  uniform float u_time;
  uniform vec2  u_resolution;
  uniform vec3  u_color;
  uniform float u_intensity;  // 0=idle, 0.5=monitoring, 1=intervention
  uniform float u_shake;      // 0-1 for intervention shockwave

  float sdCircle(vec2 p, float r) { return length(p) - r; }

  float noise(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
  }

  float smoothNoise(vec2 p) {
    vec2 i = floor(p); vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(noise(i + vec2(0,0)), noise(i + vec2(1,0)), u.x),
               mix(noise(i + vec2(0,1)), noise(i + vec2(1,1)), u.x), u.y);
  }

  void main() {
    vec2 uv = (gl_FragCoord.xy / u_resolution.xy) * 2.0 - 1.0;
    uv.y *= -1.0;

    float speed = 0.6 + u_intensity * 2.5;
    float wobble = sin(u_time * speed + uv.x * 3.0) * 0.02 * (1.0 + u_intensity);
    vec2 distorted = uv + vec2(wobble, wobble * 0.7);

    // Main orb
    float d = sdCircle(distorted, 0.62);
    float orb = smoothstep(0.01, -0.04, d);

    // Core glow
    float core = exp(-length(uv) * 2.5) * 0.6;

    // Breathing pulse
    float breathe = 0.5 + 0.5 * sin(u_time * (0.8 + u_intensity * 1.5));
    float pulse = exp(-length(uv) * (3.5 - breathe * 0.8)) * 0.4;

    // Particle layer for monitoring/intervention
    float particles = 0.0;
    if (u_intensity > 0.2) {
      for (float i = 0.0; i < 6.0; i++) {
        float angle = i / 6.0 * 6.2832 + u_time * (speed * 0.5);
        float r = 0.55 + sin(u_time * 2.1 + i) * 0.06;
        vec2 pPos = vec2(cos(angle), sin(angle)) * r;
        float pSize = 0.025 + u_intensity * 0.015;
        particles += smoothstep(pSize, 0.0, length(uv - pPos)) * u_intensity;
      }
    }

    // Shockwave for intervention
    float shock = 0.0;
    if (u_shake > 0.01) {
      float wave = abs(sin(length(uv) * 8.0 - u_time * 6.0)) * u_shake;
      shock = wave * exp(-length(uv) * 1.5);
    }

    float brightness = orb * (core + pulse) + particles * 0.6 + shock;
    vec3 col = u_color * brightness;

    // Outer subtle glow
    float outerGlow = exp(-max(d, 0.0) * 4.0) * 0.15;
    col += u_color * outerGlow;

    // Edge dimming
    col *= 1.0 - smoothstep(0.55, 0.75, length(uv)) * 0.4;

    gl_FragColor = vec4(col, orb * 0.95 + outerGlow);
  }
`;

// ── Compile Shaders ───────────────────────────────────────────────────────────
function compileShader(src, type) {
  const sh = gl.createShader(type);
  gl.shaderSource(sh, src); gl.compileShader(sh);
  if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) console.error(gl.getShaderInfoLog(sh));
  return sh;
}
const program = gl.createProgram();
gl.attachShader(program, compileShader(VS_SOURCE, gl.VERTEX_SHADER));
gl.attachShader(program, compileShader(FS_SOURCE, gl.FRAGMENT_SHADER));
gl.linkProgram(program); gl.useProgram(program);

const quad = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, quad);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,1,1]), gl.STATIC_DRAW);
const posLoc = gl.getAttribLocation(program, 'a_position');
gl.enableVertexAttribArray(posLoc);
gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

const uTime       = gl.getUniformLocation(program, 'u_time');
const uRes        = gl.getUniformLocation(program, 'u_resolution');
const uColor      = gl.getUniformLocation(program, 'u_color');
const uIntensity  = gl.getUniformLocation(program, 'u_intensity');
const uShake      = gl.getUniformLocation(program, 'u_shake');

let shakeVal = 0;
let targetIntensity = 0;
let currentIntensity = 0;

// ── Render Loop ───────────────────────────────────────────────────────────────
function render(t) {
  const ts = t * 0.001;
  const c = COLORS[currentState];

  // Smooth intensity transitions
  const targetI = currentState === STATE.IDLE ? 0 : currentState === STATE.MONITORING ? 0.5 : 1.0;
  currentIntensity += (targetI - currentIntensity) * 0.04;

  // Intervention shockwave decay
  if (currentState === STATE.INTERVENTION) shakeVal = Math.min(shakeVal + 0.03, 0.6);
  else shakeVal *= 0.92;

  gl.viewport(0, 0, SIZE, SIZE);
  gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
  gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

  gl.uniform1f(uTime, ts);
  gl.uniform2f(uRes, SIZE, SIZE);
  gl.uniform3f(uColor, c.r, c.g, c.b);
  gl.uniform1f(uIntensity, currentIntensity);
  gl.uniform1f(uShake, shakeVal);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

  // Canvas glow
  canvas.style.boxShadow = `0 0 ${30 + currentIntensity * 40}px ${c.glow}40`;
  animFrame = requestAnimationFrame(render);
}
requestAnimationFrame(render);

// ── State Controller ──────────────────────────────────────────────────────────
function setState(newState) {
  currentState = newState;
  const label = document.getElementById('orb-label');
  const labels = { IDLE: 'IDLE · 待机', MONITORING: 'MONITORING · 监控中', INTERVENTION: 'ALERT · 干预模式' };
  label.textContent = labels[newState] || newState;

  document.body.style.transition = 'background 1s ease';
  const bgColors = {
    IDLE: 'radial-gradient(ellipse 80% 60% at 50% -20%, rgba(0,212,200,0.07) 0%, transparent 70%), radial-gradient(ellipse 60% 40% at 80% 100%, rgba(100,60,200,0.05) 0%, transparent 60%)',
    MONITORING: 'radial-gradient(ellipse 80% 60% at 50% -20%, rgba(240,180,41,0.06) 0%, transparent 70%), radial-gradient(ellipse 60% 40% at 80% 100%, rgba(100,60,200,0.05) 0%, transparent 60%)',
    INTERVENTION: 'radial-gradient(ellipse 80% 60% at 50% -20%, rgba(192,57,43,0.10) 0%, transparent 70%), radial-gradient(ellipse 60% 40% at 80% 100%, rgba(192,57,43,0.06) 0%, transparent 60%)',
  };
  document.body.style.backgroundImage = bgColors[newState];
}

// ── Level Dots ────────────────────────────────────────────────────────────────
function setLevel(level, mode) {
  document.querySelectorAll('.level-dot').forEach((d, i) => {
    d.classList.toggle('active', i < level);
    if (mode === 'INTERVENTION') d.classList.add('red'); else d.classList.remove('red');
  });
}

// ── API Calls ─────────────────────────────────────────────────────────────────
async function loadPnl(address) {
  setState(STATE.MONITORING);
  showLoading(true);
  try {
    const res = await fetch(`/api/pnl?address=${encodeURIComponent(address)}`);
    const data = await res.json();
    if (data.error) { showError(data.error); setState(STATE.IDLE); return; }
    currentData = data;
    handleData(data);
  } catch(e) {
    showError('Network error. Is the server running?');
    setState(STATE.IDLE);
  } finally { showLoading(false); }
}

async function loadDemo(scenario) {
  setState(STATE.MONITORING);
  showLoading(true);
  try {
    const res = await fetch(`/api/demo?scenario=${scenario}`);
    const data = await res.json();
    currentData = data;
    handleData(data);
  } catch(e) {
    showError('Demo failed — is the server running?');
    setState(STATE.IDLE);
  } finally { showLoading(false); }
}

function handleData(data) {
  setState(data.orb_state || STATE.MONITORING);
  setLevel(data.level, data.mode);
  updateSanityScore(data);
  renderCard(data);
}

// ── Sanity Score ──────────────────────────────────────────────────────────────
function updateSanityScore(data) {
  const pct = data.total_pnl_usd > 0 ? Math.min(100, 50 + data.total_pnl_usd * 0.1)
                                       : Math.max(0, 50 + data.total_pnl_usd * 0.15);
  const score = Math.round(pct);
  document.getElementById('sanity-score').textContent = `理智分 ${score} / 100`;
}

// ── Card Renderer ─────────────────────────────────────────────────────────────
function renderCard(data) {
  const card = document.getElementById('info-card');
  const isZen = data.mode === 'ZEN';
  const pnl = data.total_pnl_usd;
  const pnlStr = pnl >= 0 ? `+$${Math.abs(pnl).toFixed(2)}` : `-$${Math.abs(pnl).toFixed(2)}`;
  const pnlClass = pnl >= 0 ? 'pos' : 'neg';

  card.innerHTML = `
    <div class="pnl-badge ${isZen ? 'zen' : 'intervention'}">
      ${isZen ? '⬆ ZEN MODE · L' : '⚡ INTERVENTION · L'}${data.level}
    </div>
    <div class="card-title">${data.title || ''}</div>
    <div class="card-body">${(data.text || '').replace(/\n/g, '<br>')}</div>
    <div class="pnl-stats">
      <div class="stat">
        <div class="stat-label">当日盈亏</div>
        <div class="stat-value ${pnlClass}">${pnlStr}</div>
      </div>
      ${data.win_rate ? `<div class="stat">
        <div class="stat-label">胜率</div>
        <div class="stat-value">${(data.win_rate * 100).toFixed(1)}%</div>
      </div>` : ''}
    </div>
    <div class="audio-panel" id="audio-panel">
      <div id="audio-player-wrap"></div>
      <div id="upgrade-msg">${data.upgrade_prompt || ''}</div>
      ${!data.audio_available ? `<button class="unlock-btn" onclick="unlockAudio()">🔓 解锁语音冥想</button>` : ''}
    </div>
    <div class="level-dots">
      <div class="level-dot ${data.level >= 1 ? `active${data.mode==='INTERVENTION'?' red':''}` : ''}"></div>
      <div class="level-dot ${data.level >= 2 ? `active${data.mode==='INTERVENTION'?' red':''}` : ''}"></div>
      <div class="level-dot ${data.level >= 3 ? `active${data.mode==='INTERVENTION'?' red':''}` : ''}"></div>
    </div>
  `;
  card.style.display = 'block';

  const panel = document.getElementById('audio-panel');
  if (panel) panel.style.display = 'block';

  if (data.audio_b64) renderAudio(data.audio_b64);
}

function renderAudio(b64) {
  const wrap = document.getElementById('audio-player-wrap');
  if (!wrap) return;
  const blob = b64ToBlob(b64, 'audio/wav');
  const url = URL.createObjectURL(blob);
  wrap.innerHTML = `<audio controls autoplay src="${url}"></audio>`;
}

function b64ToBlob(b64, mime) {
  const bin = atob(b64);
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  return new Blob([arr], { type: mime });
}

// ── Unlock Audio (x402 flow placeholder) ─────────────────────────────────────
async function unlockAudio() {
  if (!currentData) return;
  const btn = document.querySelector('.unlock-btn');
  if (btn) btn.textContent = '🔑 处理支付中...';

  try {
    const res = await fetch(
      `/api/meditate?mode=${currentData.mode}&level=${currentData.level}&pnl_usd=${currentData.total_pnl_usd || 0}&paid=true`
    );
    const data = await res.json();
    if (data.audio_b64) {
      renderAudio(data.audio_b64);
      if (btn) btn.style.display = 'none';
    } else {
      if (btn) btn.textContent = '🔓 解锁语音冥想';
      alert('Audio generation failed — check GEMINI_API_KEY in .env');
    }
  } catch(e) {
    if (btn) btn.textContent = '🔓 解锁语音冥想';
  }
}

// ── Zen Review (Right-click) ──────────────────────────────────────────────────
const RANDOM_QUOTES = [
  '"我们受难于想象，更甚于现实。" — 塞内卡',
  '"阻碍行动的事物，反而促进了行动；阻碍道路的事物，反而成为了道路。" — 马可·奥勒留',
  '"风会熄灭蜡烛，却能助长山火。你要成为火。" — 塔勒布',
  '"反脆弱性超越了韧性。韧性只是抵抗冲击，而反脆弱性则从冲击中获益。" — 塔勒布',
  '"如果一个决定在短期内痛苦，在长期内可能是有益的。" — 纳瓦尔',
  '"交易不是为了战胜市场，而是为了在市场的起伏中保持自我的完整。"',
  '"在波动中寻找不动心。"',
];
canvas.addEventListener('contextmenu', (e) => {
  e.preventDefault();
  const quote = RANDOM_QUOTES[Math.floor(Math.random() * RANDOM_QUOTES.length)];
  document.getElementById('zen-quote').textContent = quote;
  document.getElementById('zen-overlay').classList.add('open');
});
document.getElementById('zen-close').addEventListener('click', () => {
  document.getElementById('zen-overlay').classList.remove('open');
});

// ── Wallet Input ──────────────────────────────────────────────────────────────
document.getElementById('connect-btn').addEventListener('click', () => {
  const addr = document.getElementById('wallet-input').value.trim();
  if (!addr) return;
  if (pollInterval) clearInterval(pollInterval);
  loadPnl(addr);
  // Poll every 60s
  pollInterval = setInterval(() => loadPnl(addr), 60000);
});
document.getElementById('wallet-input').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') document.getElementById('connect-btn').click();
});

// ── Demo Buttons ──────────────────────────────────────────────────────────────
document.querySelectorAll('.demo-btn').forEach(btn => {
  btn.addEventListener('click', () => loadDemo(btn.dataset.scenario));
});

// ── Helpers ───────────────────────────────────────────────────────────────────
function showLoading(show) {
  document.getElementById('loading-dots').style.display = show ? 'flex' : 'none';
}
function showError(msg) {
  const card = document.getElementById('info-card');
  card.innerHTML = `<div style="color:#c0392b;font-size:13px;">⚠ ${msg}</div>`;
  card.style.display = 'block';
}

// ── Init ──────────────────────────────────────────────────────────────────────
setState(STATE.IDLE);
document.getElementById('info-card').style.display = 'none';
