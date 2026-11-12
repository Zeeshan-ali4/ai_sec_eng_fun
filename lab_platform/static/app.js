'use strict';
const form = document.querySelector('#chat-form');
const input = document.querySelector('#message');
const log = document.querySelector('#conversation');
const status = document.querySelector('#status');
const reset = document.querySelector('#reset');
let busy = false;
function setBusy(value) {
  busy = value;
  document.querySelectorAll('button, select').forEach(button => { button.disabled = value; });
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
  const timer = setTimeout(() => controller.abort(), 510000);
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
    await refreshEvidence();
  } catch (error) {
    status.textContent = error.name === 'AbortError' ? 'The request timed out. Reset before retrying if the conversation is out of sync.' : error.message;
    input.value = message;
  } finally {
    await refreshEvidence().catch(() => {});
    setBusy(false); input.focus();
  }
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
    status.textContent = 'Conversation cleared. Evidence retained.';
    await refreshEvidence();
  } catch (error) { status.textContent = error.message; }
  finally { setBusy(false); input.focus(); }
});
fetch('/api/health').then(async response => {
  const data = await response.json();
  document.querySelector('#health').textContent = response.ok ? `● Local model · ${data.ollama.model}` : '○ Local model unavailable';
}).catch(() => { document.querySelector('#health').textContent = '○ Application unavailable'; });

let latestAttempt = null;
async function refreshEvidence() {
  const response = await fetch('/api/challenge');
  if (!response.ok) throw new Error('Could not load evidence.');
  const data = await response.json();
  document.querySelector('#attempt-count').textContent = data.attempt_count;
  document.querySelector('#progress').textContent = data.progress.map(p => `${p.challenge_id} · ${p.mode} · ${p.evaluation}: ${p.attempts}`).join('\n') || 'No attempts yet.';
  latestAttempt = data.attempts.find(attempt => attempt.completed)?.id ?? null;
  const panel = document.querySelector('#evidence');
  panel.replaceChildren();
  for (const attempt of data.attempts) {
    const item = document.createElement('pre');
    item.textContent = `${attempt.challenge_id} · ${attempt.mode} · Attempt ${attempt.number} · ${attempt.timestamp}
Prompt: ${attempt.prompt}
Response: ${attempt.response ?? '(request failed; no completed response)'}
Tool requested: ${Boolean(attempt.tool_requested)} · Action executed: ${Boolean(attempt.action_executed)}
Evaluation: ${attempt.evaluation} · ${attempt.evaluation_reason}
Controls: ${attempt.controls}
Instructor: ${attempt.status} · Submitted: ${Boolean(attempt.submitted)}`;
    panel.append(item);
  }
}
document.querySelector('#submit-attempt').addEventListener('click', async () => {
  if (busy || latestAttempt === null) { status.textContent = 'Complete an attempt first.'; return; }
  setBusy(true);
  try {
    await request('/api/challenge/submit', {attempt_id: latestAttempt});
    await refreshEvidence();
    status.textContent = 'Submitted for instructor review. Automated checks and instructor decisions are shown separately.';
  } catch (error) { status.textContent = error.message; }
  finally { setBusy(false); }
});
document.querySelector('#restart-challenge').addEventListener('click', async () => {
  if (busy) return;
  setBusy(true);
  try {
    await request('/api/challenge/reset', {});
    await loadDocument();
    log.replaceChildren();
    await refreshEvidence();
    status.textContent = 'Challenge restarted. Attempt numbering and instructor evidence retained.';
  } catch (error) { status.textContent = error.message; }
  finally { setBusy(false); }
});
initializeChallenges().catch(error => { status.textContent = error.message; });

let challenges = [];
const challengeSelect = document.querySelector('#challenge-select');
const modeSelect = document.querySelector('#mode-select');
async function loadDocument() {
  document.querySelector('#document-editor').hidden = challengeSelect.value !== 'CH-005';
  if (challengeSelect.value !== 'CH-005') return;
  const response = await fetch('/api/challenge/document');
  const data = await response.json();
  if (!response.ok) throw new Error(data.error);
  document.querySelector('#document-content').value = data.content;
  document.querySelector('#document-revision').textContent = `Revision ${data.revision} · ${data.classification}`;
}
function showChallenge() {
  const c = challenges.find(c => c.id === challengeSelect.value);
  document.querySelector('#challenge-title').textContent = `${c.id} · ${c.title}`;
  document.querySelector('#challenge-description').textContent = `${c.difficulty} · ${c.learning_objective}`;
  document.querySelector('#challenge-objective').textContent = `Objective: ${c.instructions} Expected legitimate behaviour: ${c.expected_behaviour}`;
  document.querySelector('#active-mode').textContent = modeSelect.value;
}
async function initializeChallenges() {
  const response = await fetch('/api/challenges');
  const data = await response.json();
  challenges = data.challenges;
  for (const c of challenges) {
    const option = document.createElement('option');
    option.value = c.id; option.textContent = `${c.id} · ${c.title}`;
    challengeSelect.append(option);
  }
  challengeSelect.value = data.selected.challenge_id;
  modeSelect.value = data.selected.mode;
  showChallenge();
  await loadDocument();
  await refreshEvidence();
}
async function selectConfiguration() {
  if (busy) return;
  setBusy(true);
  try {
    await request('/api/challenge/select', {challenge_id: challengeSelect.value, mode: modeSelect.value});
    log.replaceChildren();
    showChallenge(); await loadDocument(); await refreshEvidence();
    status.textContent = 'Configuration selected. Its isolated conversation history is retained on the server.';
  } catch (error) { status.textContent = error.message; }
  finally { setBusy(false); }
}
challengeSelect.addEventListener('change', selectConfiguration);
modeSelect.addEventListener('change', selectConfiguration);
document.querySelector('#save-document').addEventListener('click', async () => {
  if (busy) return;
  setBusy(true);
  try {
    await request('/api/challenge/document', {id: 'support-001', content: document.querySelector('#document-content').value});
    await loadDocument(); status.textContent = 'Session-specific document saved. Ask for a support ticket summary.';
  } catch (error) { status.textContent = error.message; }
  finally { setBusy(false); }
});
