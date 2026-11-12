'use strict';
const form = document.querySelector('#chat-form');
const input = document.querySelector('#message');
const log = document.querySelector('#conversation');
const status = document.querySelector('#status');
const reset = document.querySelector('#reset');
let busy = false;
function setBusy(value) {
  busy = value;
  document.querySelectorAll('button').forEach(button => { button.disabled = value; });
  input.disabled = value;
}
function append(role, text) {
  document.querySelector('#welcome')?.remove();
  const row = document.createElement('article');
  row.className = `message ${role}`;
  const label = document.createElement('strong');
  label.textContent = role === 'user' ? 'YOU' : 'FAKEFORD ASSISTANT';
  const content = document.createElement('div');
  content.textContent = text;
  row.append(label, content);
  log.append(row);
  log.scrollTop = log.scrollHeight;
}
async function request(path, data) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 135000);
  try {
    const response = await fetch(path, {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data), signal: controller.signal});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Request failed. Please retry.');
    return result;
  } finally { clearTimeout(timer); }
}
form.addEventListener('submit', async event => {
  event.preventDefault();
  const message = input.value.trim();
  if (busy || !message) return;
  append('user', message);
  input.value = '';
  setBusy(true);
  status.textContent = 'Thinking · waiting for the local model…';
  try {
    const result = await request('/api/chat', {message});
    append('assistant', result.reply);
    status.textContent = '';
  } catch (error) {
    status.textContent = error.name === 'AbortError' ? 'The request timed out. Reset before retrying if the conversation is out of sync.' : error.message;
    input.value = message;
  } finally { setBusy(false); input.focus(); }
});
input.addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    form.requestSubmit();
  }
});
document.querySelectorAll('[data-prompt]').forEach(button => button.addEventListener('click', () => {
  input.value = button.dataset.prompt;
  form.requestSubmit();
}));
reset.addEventListener('click', async () => {
  if (busy) return;
  setBusy(true);
  try {
    await request('/api/reset', {});
    log.replaceChildren();
    input.value = '';
    status.textContent = 'Conversation cleared. Start a new enquiry.';
  } catch (error) { status.textContent = error.message; }
  finally { setBusy(false); input.focus(); }
});
fetch('/api/health').then(async response => {
  const data = await response.json();
  document.querySelector('#health').textContent = response.ok ? `● Local model · ${data.ollama.model}` : '○ Local model unavailable';
}).catch(() => { document.querySelector('#health').textContent = '○ Application unavailable'; });
