'use strict';
const el = id => document.getElementById(id);
const status = text => { el('status').textContent = text; };
async function api(path, data) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 150000);
  try {
    const response = await fetch('/proposal-02/api/' + path, {
      method: data === undefined ? 'GET' : 'POST',
      headers: {'Content-Type': 'application/json'},
      body: data === undefined ? undefined : JSON.stringify(data), signal: controller.signal
    });
    const value = await response.json();
    if (!response.ok) throw new Error(value.error || 'Local request failed.');
    return value;
  } finally { clearTimeout(timer); }
}
function detail(parent, title, value) {
  const item = document.createElement('details');
  const summary = document.createElement('summary');
  summary.textContent = title;
  const content = document.createElement('pre');
  content.textContent = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
  item.append(summary, content); parent.append(item);
}
function bubble(role, text, sources) {
  const box = document.createElement('div'); box.className = 'message ' + role;
  const heading = document.createElement('strong'); heading.textContent = role;
  const content = document.createElement('div'); content.textContent = text;
  box.append(heading, content);
  if (sources) detail(box, 'Approved references retrieved: ' + (sources.map(s => s.id).join(', ') || 'none'), sources);
  el('conversation').append(box); box.scrollIntoView({block:'nearest'});
}
let entries = [];
function showKnowledge() {
  const query = el('search').value.toLowerCase(); el('knowledge').replaceChildren();
  for (const entry of entries.filter(e => JSON.stringify(e).toLowerCase().includes(query))) {
    detail(el('knowledge'), entry.id + ' · ' + entry.topic + ' · v' + entry.version, entry);
  }
}
async function refresh() {
  const [baseline, knowledge, proposals] = await Promise.all([api('baseline'), api('knowledge'), api('submissions')]);
  el('baseline').textContent = `${baseline.dataset_version} · ${baseline.trusted_entries} trusted entries · ${baseline.state}\nSHA-256: ${baseline.checksum}`;
  entries = knowledge.entries; showKnowledge();
  const selected = el('entry').value;
  el('entry').replaceChildren(new Option('New answer', ''));
  entries.forEach(e => el('entry').add(new Option(e.id + ' · ' + e.topic, e.id)));
  el('entry').value = selected;
  el('submissions').replaceChildren();
  proposals.submissions.forEach(s => detail(el('submissions'), '#' + s.id + ' · ' + s.status + ' · ' + s.topic, s));
}
el('search').addEventListener('input', showKnowledge);
el('refresh').addEventListener('click', () => refresh().catch(e => status(e.message)));
el('chat-form').addEventListener('submit', async event => {
  event.preventDefault(); const message = el('message').value.trim(); if (!message) return;
  el('send').disabled = true; el('reset').disabled = true; bubble('user', message); status('Consulting approved knowledge…');
  try { const value = await api('chat', {message}); bubble('assistant', value.reply, value.sources); el('message').value = ''; status('Response recorded locally. References show retrieval, not proof of factual correctness.'); }
  catch (e) { status(e.name === 'AbortError' ? 'Request timed out. Check the local model before retrying.' : e.message); }
  finally { el('send').disabled = false; el('reset').disabled = false; }
});
el('reset').addEventListener('click', async () => {
  try { const result = await api('reset', {}); el('conversation').replaceChildren(); status(result.status); } catch (e) { status(e.message); }
});
el('submission-form').addEventListener('submit', async event => {
  event.preventDefault(); const button = event.submitter; button.disabled = true;
  const data = {account_id:el('account').value, entry_id:el('entry').value, topic:el('topic').value, answer:el('answer').value, explanation:el('explanation').value, rating:el('rating').value ? Number(el('rating').value) : null};
  try { const value = await api('submissions', data); status('Submission #' + value.id + ' is pending organiser review.'); el('submission-form').reset(); await refresh(); }
  catch (e) { status(e.message); } finally { button.disabled = false; }
});
(async () => {
  try { const data = await api('accounts'); data.accounts.forEach(a => el('account').add(new Option(a.display_alias + ' · ' + a.account_type + ' · ' + a.trust_level, a.id))); await refresh(); }
  catch (e) { status(e.message); }
  try { const response = await fetch('/api/health'); const state = await response.json(); el('health').textContent = state.ollama.model_ready ? 'Local model ready · ' + state.ollama.model : 'Local Ollama unavailable; knowledge browsing and submissions remain available.'; }
  catch (_) { el('health').textContent = 'Could not check local model.'; }
})();
