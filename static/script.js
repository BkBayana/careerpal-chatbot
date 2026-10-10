/* CareerPal front-end: chat UI + voice input (SpeechRecognition) + voice output (speechSynthesis) */
const $ = (s) => document.querySelector(s);
const messagesEl = $('#messages');
const quickEl = $('#quick');
const form = $('#form');
const input = $('#input');
const micBtn = $('#micBtn');
const hint = $('#voiceHint');
const speakToggle = $('#speakToggle');
const autoSpeakBox = $('#autoSpeak');
const voiceSelect = $('#voiceSelect');
const rateEl = $('#rate');
const rateOut = $('#rateOut');

let autoSpeak = true;
let busy = false;

/* ---------------- rendering ---------------- */
function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function inline(s) {
  return escapeHtml(s)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*\w])\*(?!\s)([^*]+?)\*(?!\w)/g, '$1<em>$2</em>');
}
function renderMarkdown(text) {
  let html = '';
  let list = null;
  const close = () => { if (list) { html += `</${list}>`; list = null; } };
  for (const raw of text.split('\n')) {
    const line = raw.trimEnd();
    let m;
    if (line.trim() === '---') { close(); html += '<hr>'; }
    else if ((m = line.match(/^\s*[-•]\s+(.*)/))) {
      if (list !== 'ul') { close(); html += '<ul>'; list = 'ul'; }
      html += `<li>${inline(m[1])}</li>`;
    } else if ((m = line.match(/^\s*(\d+)[.)]\s+(.*)/))) {
      if (list !== 'ol') { close(); html += `<ol start="${m[1]}">`; list = 'ol'; }
      html += `<li>${inline(m[2])}</li>`;
    } else if (line.trim() === '') { close(); }
    else { close(); html += `<p>${inline(line)}</p>`; }
  }
  close();
  return html;
}
function toSpeech(text) {
  return text
    .replace(/^---$/gm, '. ')
    .replace(/\*\*|\*/g, '')
    .replace(/[★☆]/g, '')
    .replace(/\p{Extended_Pictographic}|️/gu, '')
    .replace(/→/g, ' then ')
    .replace(/–|—/g, ', ')
    .replace(/\n+/g, '. ')
    .replace(/(\.\s*){2,}/g, '. ')
    .trim();
}
const timeNow = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

function addMessage(role, text, opts = {}) {
  const wrap = document.createElement('div');
  wrap.className = `msg ${role}`;
  const avatar = document.createElement('div');
  avatar.className = `avatar ${role === 'bot' ? 'bot-avatar' : 'user-avatar'}`;
  avatar.textContent = role === 'bot' ? 'CP' : 'You';
  const body = document.createElement('div');
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  if (role === 'bot') bubble.innerHTML = renderMarkdown(text);
  else bubble.textContent = text;
  const meta = document.createElement('div');
  meta.className = 'meta';
  meta.innerHTML = `<span>${timeNow()}</span>`;
  if (opts.voice) meta.innerHTML += '<span class="badge">🎙 voice</span>';
  if (role === 'bot') {
    const btn = document.createElement('button');
    btn.className = 'replay';
    btn.type = 'button';
    btn.textContent = '🔊 Listen';
    btn.onclick = () => speak(text, true);
    meta.appendChild(btn);
  }
  body.append(bubble, meta);
  wrap.append(avatar, body);
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}
function showTyping() {
  const el = document.createElement('div');
  el.className = 'msg bot typing';
  el.id = 'typing';
  el.innerHTML = '<div class="avatar bot-avatar">CP</div><div class="bubble"><span></span><span></span><span></span></div>';
  messagesEl.appendChild(el);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}
const hideTyping = () => $('#typing')?.remove();

function setQuick(replies) {
  quickEl.innerHTML = '';
  (replies || []).forEach((r) => {
    const b = document.createElement('button');
    b.className = 'chip';
    b.type = 'button';
    b.textContent = r;
    b.onclick = () => send(r);
    quickEl.appendChild(b);
  });
}

/* ---------------- networking ---------------- */
async function send(text, viaVoice = false) {
  text = (text || '').trim();
  if (!text || busy) return;
  busy = true;
  addMessage('user', text, { voice: viaVoice });
  input.value = '';
  autoGrow();
  setQuick([]);
  showTyping();
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();
    await new Promise((r) => setTimeout(r, 350)); // small natural delay
    hideTyping();
    addMessage('bot', data.reply);
    setQuick(data.quick_replies);
    if (autoSpeak) speak(data.reply);
  } catch (err) {
    hideTyping();
    addMessage('bot', '⚠️ Sorry, I could not reach the server. Is the Flask app running?');
  } finally {
    busy = false;
    input.focus();
  }
}
async function loadWelcome(url = '/api/welcome', method = 'GET') {
  const res = await fetch(url, { method });
  const data = await res.json();
  addMessage('bot', data.reply);
  setQuick(data.quick_replies);
}

/* ---------------- voice output ---------------- */
const synth = window.speechSynthesis;
let voices = [];
function loadVoices() {
  if (!synth) return;
  voices = synth.getVoices().filter((v) => v.lang && v.lang.toLowerCase().startsWith('en'));
  const prev = voiceSelect.value;
  voiceSelect.innerHTML = '';
  if (!voices.length) voiceSelect.innerHTML = '<option value="">Browser default voice</option>';
  voices.forEach((v, i) => {
    const o = document.createElement('option');
    o.value = i;
    o.textContent = `${v.name} (${v.lang})`;
    voiceSelect.appendChild(o);
  });
  if (!voices.length) return;
  const preferred = voices.findIndex((v) => /Google US English|Samantha|Jenny|Aria|Zira/i.test(v.name));
  voiceSelect.value = prev || (preferred >= 0 ? preferred : 0);
}
function speak(text, force = false) {
  if (!synth || (!autoSpeak && !force)) return;
  synth.cancel();
  // split into sentences so long replies are not cut off by some browsers
  const chunks = toSpeech(text).match(/[^.!?]+[.!?]*/g) || [];
  chunks.forEach((chunk) => {
    const u = new SpeechSynthesisUtterance(chunk.trim());
    const v = voices[voiceSelect.value];
    if (v) u.voice = v;
    u.lang = v ? v.lang : 'en-US';
    u.rate = parseFloat(rateEl.value);
    synth.speak(u);
  });
}
if (synth) {
  loadVoices();
  synth.onvoiceschanged = loadVoices;
} else {
  autoSpeak = false;
  autoSpeakBox.checked = false;
  autoSpeakBox.disabled = true;
}
function setAutoSpeak(on) {
  autoSpeak = on;
  autoSpeakBox.checked = on;
  speakToggle.classList.toggle('off', !on);
  speakToggle.textContent = on ? '🔊' : '🔈';
  if (!on && synth) synth.cancel();
}
speakToggle.onclick = () => setAutoSpeak(!autoSpeak);
autoSpeakBox.onchange = () => setAutoSpeak(autoSpeakBox.checked);
rateEl.oninput = () => { rateOut.textContent = `${parseFloat(rateEl.value).toFixed(1)}×`; };

/* ---------------- voice input ---------------- */
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let recog = null;
let listening = false;
let finalText = '';
let voiceError = false;

if (SR) {
  recog = new SR();
  recog.lang = 'en-US';
  recog.interimResults = true;
  recog.continuous = false;
  recog.maxAlternatives = 1;

  recog.onstart = () => {
    listening = true;
    voiceError = false;
    finalText = '';
    micBtn.classList.add('listening');
    hint.textContent = '🎙 Listening… speak now (click the mic again to stop)';
    if (synth) synth.cancel();
  };
  recog.onresult = (e) => {
    let interim = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const t = e.results[i][0].transcript;
      if (e.results[i].isFinal) finalText += t;
      else interim += t;
    }
    input.value = (finalText + ' ' + interim).trim();
    autoGrow();
  };
  recog.onerror = (e) => {
    voiceError = true;
    const msgs = {
      'not-allowed': 'Microphone access was blocked. Allow the mic in your browser settings.',
      'no-speech': "I didn't hear anything — click the mic and try again.",
      'audio-capture': 'No microphone was found.',
      network: 'Voice recognition needs an internet connection.',
    };
    hint.textContent = msgs[e.error] || `Voice error: ${e.error}`;
  };
  recog.onend = () => {
    listening = false;
    micBtn.classList.remove('listening');
    const text = input.value.trim();
    if (!voiceError) hint.textContent = '';
    if (finalText.trim() && text) send(text, true);
  };
} else {
  micBtn.disabled = true;
  hint.textContent = 'Voice input works in Google Chrome or Microsoft Edge. You can still type.';
}
micBtn.onclick = () => {
  if (!recog) return;
  if (listening) { recog.stop(); return; }
  try { recog.start(); } catch (_) { /* already started */ }
};

/* ---------------- composer & sidebar ---------------- */
function autoGrow() {
  input.style.height = 'auto';
  input.style.height = Math.min(input.scrollHeight, 180) + 'px';
}
input.addEventListener('input', autoGrow);
input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input.value); }
});
form.addEventListener('submit', (e) => { e.preventDefault(); send(input.value); });

document.querySelectorAll('.feature').forEach((b) => {
  b.onclick = () => { $('#sidebar').classList.remove('open'); send(b.dataset.msg); };
});
$('#menuBtn').onclick = () => $('#sidebar').classList.toggle('open');
$('#resetBtn').onclick = async () => {
  if (synth) synth.cancel();
  messagesEl.innerHTML = '';
  $('#sidebar').classList.remove('open');
  await loadWelcome('/api/reset', 'POST');
};

loadWelcome();
input.focus();
