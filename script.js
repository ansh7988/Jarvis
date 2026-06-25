/* ============================================================
   J.A.R.V.I.S — System Interface
   Behavior layer
   ============================================================ */

/* ---------- Clock ---------- */
function tickClock(){
  const now = new Date();
  const h = String(now.getHours()).padStart(2,'0');
  const m = String(now.getMinutes()).padStart(2,'0');
  const s = String(now.getSeconds()).padStart(2,'0');
  document.getElementById('clock').textContent = `${h}:${m}:${s}`;

  const days = ['SUN','MON','TUE','WED','THU','FRI','SAT'];
  const months = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
  document.getElementById('dateline').textContent =
    `${days[now.getDay()]} ${now.getDate()} ${months[now.getMonth()]} ${now.getFullYear()}`;
}
tickClock();
setInterval(tickClock, 1000);

/* ---------- Animated waveform ring ---------- */
const waveGroup = document.getElementById('waveRing');
const WAVE_RADIUS = 150;
const WAVE_POINTS = 64;
let waveAmplitude = 4;   // idle amplitude
let waveSpeed = 0.02;
let t = 0;

function buildWavePath(amplitude){
  let d = '';
  for(let i=0;i<=WAVE_POINTS;i++){
    const angle = (i / WAVE_POINTS) * Math.PI * 2;
    const noise = Math.sin(angle * 6 + t) * amplitude + Math.sin(angle * 3 - t*1.3) * (amplitude*0.5);
    const r = WAVE_RADIUS + noise;
    const x = 240 + r * Math.cos(angle);
    const y = 240 + r * Math.sin(angle);
    d += (i === 0 ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1) + ' ';
  }
  return d + 'Z';
}

function renderWave(){
  waveGroup.innerHTML = `<path d="${buildWavePath(waveAmplitude)}"/>`;
  t += waveSpeed;
  requestAnimationFrame(renderWave);
}
renderWave();

/* ---------- Sparkline (system activity) ---------- */
const spark = document.getElementById('sparkline');
let sparkData = Array.from({length: 24}, () => 20 + Math.random()*20);

function renderSpark(){
  sparkData.push(Math.max(4, Math.min(56, sparkData[sparkData.length-1] + (Math.random()-0.5)*14)));
  sparkData.shift();
  const step = 220 / (sparkData.length - 1);
  const pts = sparkData.map((v,i) => `${(i*step).toFixed(1)},${(60-v).toFixed(1)}`).join(' ');
  spark.setAttribute('points', pts);
}
renderSpark();
setInterval(renderSpark, 1200);

/* ---------- Live-ish stat meters ---------- */
function jitterMeter(elId, valId, base, suffix='%'){
  const val = Math.max(8, Math.min(96, base + (Math.random()-0.5)*10));
  document.getElementById(elId).style.width = val + '%';
  document.getElementById(valId).textContent = Math.round(val) + suffix;
  return val;
}
setInterval(() => {
  jitterMeter('cpuMeter','cpuVal', 42);
  jitterMeter('memMeter','memVal', 61);
}, 2500);

/* ---------- Assistant state machine ---------- */
const coreWrap = document.getElementById('coreWrap');
const stateLabel = document.getElementById('stateLabel');
const transcript = document.getElementById('transcript');
const micBtn = document.getElementById('micBtn');
const logFeed = document.getElementById('logFeed');

const STATE_CONFIG = {
  idle:      { label:'IDLE',      amp:4,  speed:0.02, text:'Awaiting voice input…' },
  listening: { label:'LISTENING', amp:14, speed:0.05, text:'Listening…' },
  thinking:  { label:'PROCESSING',amp:8,  speed:0.09, text:'Processing request…' },
  speaking:  { label:'RESPONDING',amp:11, speed:0.06, text:'Responding…' },
};

function setAssistantState(state){
  const cfg = STATE_CONFIG[state];
  coreWrap.classList.remove('listening','thinking');
  stateLabel.classList.remove('listening');

  if(state === 'listening'){ coreWrap.classList.add('listening'); stateLabel.classList.add('listening'); }
  if(state === 'thinking'){ coreWrap.classList.add('thinking'); }

  stateLabel.textContent = cfg.label;
  transcript.textContent = cfg.text;
  waveAmplitude = cfg.amp;
  waveSpeed = cfg.speed;
}

function addLogEntry(tag, text){
  const entry = document.createElement('div');
  entry.className = `log-entry log-${tag.toLowerCase() === 'jarvis' ? 'jarvis' : tag.toLowerCase() === 'sys' ? 'sys' : 'user'}`;
  entry.innerHTML = `<span class="log-tag">${tag}</span><span class="log-text"></span>`;
  entry.querySelector('.log-text').textContent = text;
  logFeed.appendChild(entry);
  logFeed.scrollTop = logFeed.scrollHeight;
}

/* ---------- Mic button interaction ---------- */
let isListening = false;

micBtn.addEventListener('click', () => {
  isListening = !isListening;
  micBtn.classList.toggle('active', isListening);
  micBtn.setAttribute('aria-pressed', String(isListening));
  micBtn.querySelector('span').textContent = isListening ? 'STOP' : 'ENGAGE';

  if(isListening){
    setAssistantState('listening');
  } else {
    setAssistantState('thinking');
    addLogEntry('USER', '[voice command captured]');
    setTimeout(() => {
      setAssistantState('speaking');
      addLogEntry('JARVIS', 'Request received. Working on it now.');
      setTimeout(() => setAssistantState('idle'), 2200);
    }, 1400);
  }
});

/* ---------- Text input ---------- */
const textInput = document.getElementById('textInput');
const sendBtn = document.getElementById('sendBtn');

function submitText(){
  const val = textInput.value.trim();
  if(!val) return;
  addLogEntry('USER', val);
  textInput.value = '';
  setAssistantState('thinking');
  setTimeout(() => {
    setAssistantState('speaking');
    addLogEntry('JARVIS', `Acknowledged: "${val}"`);
    setTimeout(() => setAssistantState('idle'), 2200);
  }, 1000);
}

sendBtn.addEventListener('click', submitText);
textInput.addEventListener('keydown', (e) => { if(e.key === 'Enter') submitText(); });

/* ---------- Quick command chips ---------- */
document.querySelectorAll('.cmd-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    const cmd = chip.dataset.cmd;
    addLogEntry('USER', cmd);
    setAssistantState('thinking');
    setTimeout(() => {
      setAssistantState('speaking');
      addLogEntry('JARVIS', `Executing: ${cmd}.`);
      setTimeout(() => setAssistantState('idle'), 2200);
    }, 1000);
  });
});

/* ---------- Init ---------- */
setAssistantState('idle');
