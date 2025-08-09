// Keyboard-first shell runner
const output = document.getElementById('output');
const cmd = document.getElementById('cmd');
const clock = document.getElementById('clock');
const weatherBox = document.getElementById('weather');
const rssInner = document.getElementById('rss-inner');

const llmPanel = document.getElementById('panel-llmchat');
const llmLog = document.getElementById('llm-log');
const llmInput = document.getElementById('llm-input');

const notesPanel = document.getElementById('panel-notes');
const noteTitle = document.getElementById('note-title');
const noteEditor = document.getElementById('note-editor');

let llmSessionId = null;
let shellHistory = [];
let histIndex = -1;

// Focus shell input on load
window.addEventListener('load', () => {
  cmd.focus();
  printLine('type <span class=\"cmd\">help</span> to see commands');
  tickClock();
  setInterval(tickClock, 1000 * 10);
  updateWeather();
  updateRSS();
  startTickerLoop();
  setInterval(updateWeather, 1000 * 60 * 20);
  setInterval(updateRSS, 1000 * 60 * 5);
});

function tickClock() {
  const d = new Date();
  clock.textContent = d.toLocaleString();
}

function printLine(html) {
  const div = document.createElement('div');
  div.className = 'line';
  div.innerHTML = html;
  output.appendChild(div);
  output.scrollTop = output.scrollHeight;
}

function printCmd(c) {
  printLine(`<span class=\"cmd\">&gt; ${escapeHtml(c)}</span>`);
}

function escapeHtml(s) {
  return s.replace(/[&<>'"]/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[c]));
}

async function runCommand(c) {
  if (!c.trim()) return;
  printCmd(c);
  shellHistory.push(c);
  histIndex = shellHistory.length;

  try {
    const res = await fetch('/api/command', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ command: c })
    });
    const js = await res.json();
    handleCommandResponse(js);
  } catch (e) {
    printLine(`<span class=\"text\">(error: ${escapeHtml(String(e))})</span>`);
  }
}

function handleCommandResponse(js) {
  if (js.type === 'text') {
    const text = (js.text || '').split('\\n').map(escapeHtml).join('<br/>');
    printLine(`<span class=\"text\">${text}</span>`);
    return;
  }
  if (js.type === 'action' && js.action === 'open') {
    const panel = js.panel;
    if (panel === 'llmchat') {
      openLLM();
      return;
    }
    if (panel === 'notes') {
      openNotes(js.title || null);
      return;
    }
  }
  printLine(`<span class=\"text\">(no-op)</span>`);
}

// Shell input handlers
cmd.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    const c = cmd.value;
    cmd.value = '';
    runCommand(c);
    return;
  }
  if (e.key === 'ArrowUp') {
    if (histIndex > 0) {
      histIndex -= 1;
      cmd.value = shellHistory[histIndex] || '';
      setTimeout(() => cmd.setSelectionRange(cmd.value.length, cmd.value.length), 0);
    }
  }
  if (e.key === 'ArrowDown') {
    if (histIndex < shellHistory.length) {
      histIndex += 1;
      cmd.value = shellHistory[histIndex] || '';
      setTimeout(() => cmd.setSelectionRange(cmd.value.length, cmd.value.length), 0);
    }
  }
});

// Global escape -> close panels
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    if (!llmPanel.classList.contains('hidden')) {
      closeLLM();
    } else if (!notesPanel.classList.contains('hidden')) {
      closeNotes();
    } else {
      cmd.focus();
    }
  }
});

// LLM panel
function openLLM() {
  llmPanel.classList.remove('hidden');
  llmInput.focus();
}

function closeLLM() {
  llmPanel.classList.add('hidden');
  cmd.focus();
}

llmInput.addEventListener('keydown', async (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    const msg = llmInput.value.trim();
    if (!msg) return;
    llmInput.value = '';
    addLLMLine('you', msg);
    try {
      const res = await fetch('/api/llm/send', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ message: msg, session_id: llmSessionId || null })
      });
      const js = await res.json();
      llmSessionId = js.session_id;
      addLLMLine('assistant', js.reply || '');
    } catch (e) {
      addLLMLine('assistant', `(error: ${String(e)})`);
    }
  }
});

function addLLMLine(who, text) {
  const div = document.createElement('div');
  div.className = 'llm-msg ' + (who === 'you' ? 'llm-user' : 'llm-assistant');
  div.textContent = (who === 'you' ? '> ' : '') + text;
  llmLog.appendChild(div);
  llmLog.scrollTop = llmLog.scrollHeight;
}

// Notes panel
async function openNotes(titleOrNull) {
  notesPanel.classList.remove('hidden');
  noteEditor.value = '';
  noteTitle.textContent = '';
  try {
    const url = titleOrNull ? `/api/notes/open?title=${encodeURIComponent(titleOrNull)}` : '/api/notes/open';
    const res = await fetch(url);
    const js = await res.json();
    noteTitle.textContent = js.title;
    noteEditor.value = js.content;
  } catch (e) {
    noteTitle.textContent = 'error';
    noteEditor.value = String(e);
  }
  noteEditor.focus();
}

function closeNotes() {
  notesPanel.classList.add('hidden');
  cmd.focus();
}

// Save note with Ctrl+S
document.addEventListener('keydown', async (e) => {
  if (!notesPanel.classList.contains('hidden')) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
      e.preventDefault();
      try {
        const res = await fetch('/api/notes/save', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ title: noteTitle.textContent, content: noteEditor.value })
        });
        const js = await res.json();
        if (js.ok) {
          printLine(`saved note: <span class=\"cmd\">${escapeHtml(js.title)}</span>`);
        } else {
          printLine('(save failed)');
        }
      } catch (e) {
        printLine('(save error)');
      }
    }
  }
});


// JS-driven ticker for smooth, steady speed independent of CSS reflow
let tickerOffset = 0;
let tickerWidth = 0;
let tickerContainerWidth = 0;
let tickerRAF = null;

function measureTicker() {
  const container = document.getElementById('rss-ticker');
  const inner = document.getElementById('rss-inner');
  if (!container || !inner) return;
  tickerWidth = inner.offsetWidth;
  tickerContainerWidth = container.offsetWidth;
  if (tickerWidth === 0 || tickerContainerWidth === 0) return;
}

function stepTicker(ts) {
  // pixels per second (slow and readable)
  const speed = 40;
  // use performance.now delta implicitly via requestAnimationFrame timing
  // but we don't need ts math if we use fixed fps approximation
  tickerOffset -= speed / 60;
  const container = document.getElementById('rss-ticker');
  const inner = document.getElementById('rss-inner');
  if (!container || !inner) return;
  // wrap when fully passed
  const total = tickerWidth + tickerContainerWidth;
  if (tickerOffset <= -total) tickerOffset = 0;
  inner.style.transform = `translateX(${tickerOffset}px)`;
  tickerRAF = requestAnimationFrame(stepTicker);
}

function startTickerLoop() {
  cancelTicker();
  measureTicker();
  tickerOffset = 0;
  // Start next frame to ensure layout is measured
  tickerRAF = requestAnimationFrame(stepTicker);
}

function cancelTicker() {
  if (tickerRAF) cancelAnimationFrame(tickerRAF);
  tickerRAF = null;
}

// Ambient: weather + rss
async function updateWeather() {
  try {
    const res = await fetch('/api/weather/current');
    const js = await res.json();
    weatherBox.textContent = renderWeather(js);
  } catch (e) {
    weatherBox.textContent = '(weather error)';
  }
}

function renderWeather(js) {
  if (js.status === 'unconfigured') return '(set OPENWEATHER_API_KEY to enable)';
  if (js.status && js.status !== 'ok') return '(weather unavailable)';
  try {
    const city = js.city || (js.data && js.data.name) || '';
    const desc = (js.data.weather && js.data.weather[0] && js.data.weather[0].description) || '';
    const temp = js.data.main && js.data.main.temp;
    return `${city}: ${desc} ${temp}°`;
  } catch {
    return '(weather unavailable)';
  }
}

async function updateRSS() {
  try {
    const res = await fetch('/api/rss');
    const js = await res.json();
    const items = js.items || [];
    if (items.length === 0) {
      rssInner.textContent = 'Add feeds in config.json to enable the ticker';
      return;
    }
    const text = items.map(it => `${it.title}`).join('  •  ');
    rssInner.textContent = text;
    startTickerLoop();
  } catch (e) {
    rssInner.textContent = 'RSS unavailable';
  }
}
