'use strict';
const base = '/proposal-02/poisoning/api/';
const el = id => document.getElementById(id);
const text = (id, value) => { el(id).textContent = value; };
let state;
let stages = {};
let experimentQuestion = null;
let learningMode = 'investigator';
let learning = {};
let storageAvailable = true;
const noteFields = {
  hypothesis: 'What do you think is vulnerable, and why?',
  attack_design: 'What information did you submit, and which variables did you change?',
  observed_evidence: 'What happened to ingestion, ranking, retrieved sources and the chatbot response?',
  defensive_comparison: 'What changed when hardened mode was enabled?',
  conclusion: 'Which security weakness did you demonstrate, and which control prevented or reduced it?'
};
function readLocal(key, fallback) {
  try { return JSON.parse(sessionStorage.getItem(key)) || fallback; }
  catch { storageAvailable = false; el('storage-warning').hidden = false; return fallback; }
}
function writeLocal(key, value) {
  try { sessionStorage.setItem(key, JSON.stringify(value)); }
  catch { storageAvailable = false; el('storage-warning').hidden = false; }
}
function learningKey() { return `p2-investigation:${state.session_id}:${state.scenario.id}`; }
function saveLearning() { if (state) writeLocal(learningKey(), learning); }
function saveDraft() {
  if (!state) return;
  learning.draft = {answer:el('answer').value, question:el('question').value, rating:el('rating').value, account:el('account').value, source:el('source').value};
  saveLearning();
}
function restoreDraft() {
  const draft = learning.draft || {answer:'', question:'', rating:'3', account:'new', source:'practice-1'};
  for (const field of ['answer','question','rating','account','source']) el(field).value = draft[field];
}
function useExample() {
  el('answer').value = state.scenario.sample;
  el('question').value = state.scenario.target_question;
  el('rating').value = '5'; el('account').value = 'new'; el('source').value = 'practice-1';
  saveDraft();
}
function renderLearning() {
  if (!state) return;
  const guided = learningMode === 'guided';
  const spec = state.scenario;
  const guide = investigationGuide[spec.id];
  el('learning-mode').value = learningMode;
  document.querySelectorAll('.guided-only').forEach(node => { node.hidden = !guided; });
  el('investigation').hidden = guided;
  el('reference').hidden = !guided;
  el('trigger-note').hidden = !guided;
  text('description', guided ? spec.weakness : guide.incident);
  text('objective', guided ? spec.objective : guide.objective);
  text('investigation-scope', `Configured investigation scope: ${spec.target_id} · ${spec.topic}. Submissions inherit this article’s topic and keywords; arbitrary topics and arbitrary correction targets are not supported.`);
  text('explanation-text', spec.weakness);
  text('replay', guided ? 'Replay identical payload in both modes and compare' : 'Run automated comparison — optional');
  el('manual-advice').hidden = guided;
  el('comparison-details').open = guided;
  const used = Math.max(0, Math.min(3, Number(learning.hints) || 0));
  text('hint-count', ` ${used} of 3 hints used`);
  text('hint-next', used === 3 ? 'All hints revealed' : 'Reveal next hint');
  el('hints').replaceChildren(...guide.hints.slice(0, used).map(hint => {
    const li = document.createElement('li'); li.textContent = hint; return li;
  }));
}
function renderWorksheet() {
  el('worksheet').replaceChildren(...Object.entries(noteFields).map(([key, prompt]) => {
    const label = document.createElement('label'); label.htmlFor = 'note-' + key; label.textContent = prompt;
    const input = document.createElement('textarea'); input.id = label.htmlFor; input.maxLength = 10000;
    input.value = learning.notes?.[key] || '';
    input.addEventListener('input', () => { learning.notes = learning.notes || {}; learning.notes[key] = input.value; saveLearning(); });
    const group = document.createElement('div'); group.append(label, input); return group;
  }));
}
function worksheetDocument() {
  return {scenario_id:state.scenario.id, scenario_title:state.scenario.title, guidance_mode:learningMode,
    ...Object.fromEntries(Object.keys(noteFields).map(key => [key, learning.notes?.[key] || ''])),
    timestamp:new Date().toISOString(), experiment_identifiers:learning.experiments || [],
    storage:'Browser-local reflection; not authoritative SQLite evidence'};
}
function markdownNote(value) {
  // Keep reflection text inert even in Markdown viewers that permit raw HTML.
  return value.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replace(/([\\`*_{}\[\]()#+.!|])/g, '\\$1');
}
function downloadWorksheet(format) {
  const doc = worksheetDocument();
  const content = format === 'json' ? JSON.stringify(doc, null, 2) :
    `# ${doc.scenario_id} · ${doc.scenario_title}\n\nLearning mode: ${doc.guidance_mode}\nTimestamp: ${doc.timestamp}\n\n` +
    Object.keys(noteFields).map(key => `## ${key.replaceAll('_',' ')}\n\n${markdownNote(doc[key])}\n`).join('\n') +
    `\nExperiment identifiers (mode and evidence ID): ${JSON.stringify(doc.experiment_identifiers)}\n\n${doc.storage}\n`;
  const url = URL.createObjectURL(new Blob([content], {type:format === 'json' ? 'application/json' : 'text/markdown;charset=utf-8'}));
  const link = document.createElement('a'); link.href = url; link.download = `${doc.scenario_id}-worksheet.${format === 'json' ? 'json' : 'md'}`;
  link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function rememberExperiment(result) {
  learning.experiments = learning.experiments || [];
  learning.experiments.push({mode:result.mode, evidence_id:result.evidence_id, stage:result.stage, generation:result.generation});
  learning.experiments = learning.experiments.slice(-100); saveLearning();
}
function evidenceSummary(result) {
  const obs = result.observations;
  const lines = [
    `Protection: ${result.mode}; stage: ${result.stage}; evidence: ${result.evidence_id}.`,
    `Submission decisions: ${(result.submissions || []).map(r => r.disposition || 'accepted').join(', ') || 'No submissions in this query snapshot'}.`,
    `Untrusted information retrieved: ${obs.untrusted_content_retrieved ? 'Yes' : 'No'}.`,
    `Untrusted information ranked first: ${obs.untrusted_content_prioritised ? 'Yes' : 'No'}. Inspect full ranking to compare with trusted knowledge.`,
    `Answer changed from the same-question clean baseline: ${obs.model_answer_changed === null ? 'Not observed / no comparable model baseline' : obs.model_answer_changed ? 'Yes' : 'No'}.`,
    `Incorrect claim or instruction following: ${result.answer ? 'Manual review required. Compare the actual answer against approved knowledge.' : 'Not observed: model unavailable.'}`,
    result.answer || 'No model response observed.',
    'Retrieval manipulation and answer contamination are separate. A refusal to adopt a false claim can coexist with compromised retrieval. Switch protection mode and repeat unchanged inputs to inspect containment; full evidence retains each observation.'
  ];
  el('evidence-summary').replaceChildren(...lines.map(line => { const p = document.createElement('p'); p.textContent = line; return p; }));
}
async function api(path, data) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), ['benchmark', 'compare'].includes(path) ? 510000 : 150000);
  try {
    const response = await fetch(base + path, {signal: controller.signal, ...(data === undefined ? {} : {method: 'POST', headers: {'Content-Type':'application/json'}, body:JSON.stringify(data)})});
    const result = await response.json();
    if (!response.ok && !result.dataset) throw new Error(result.error || 'Request failed');
    return result;
  } finally { clearTimeout(timeout); }
}
async function action(fn) {
  const buttons = document.querySelectorAll('button, select');
  buttons.forEach(b => { b.disabled = true; });
  try { await fn(); } catch (error) { text('status', error.name === 'AbortError' ? 'Request timed out. Inspect exported evidence before retrying.' : error.message); }
  finally { buttons.forEach(b => { b.disabled = false; }); }
}
function options(id, rows, value, label) {
  el(id).replaceChildren(...rows.map(row => {
    const option = document.createElement('option'); option.value = value(row); option.textContent = label(row); return option;
  }));
}
function showState(data, selected = false) {
  // Another tab can change the shared server selection. Keep each local draft/worksheet in its own scope.
  if (state && (state.session_id !== data.session_id || state.scenario.id !== data.scenario.id)) {
    saveDraft(); selected = true;
  }
  if (!state || state.session_id !== data.session_id) {
    learningMode = readLocal(`p2-learning-mode:${data.session_id}`, 'investigator') === 'guided' ? 'guided' : 'investigator';
  }
  state = data;
  if (selected) learning = readLocal(learningKey(), {});
  const spec = data.scenario;
  el('scenario').value = spec.id;
  el('mode').value = data.mode;
  text('scope', `Mode: ${data.mode}. Local evidence session: ${data.session_id}. Fictional accounts grant no organiser authority.`);
  text('title', `${spec.id} · ${spec.title} · ${spec.difficulty}`);
  text('description', spec.weakness);
  text('objective', spec.objective);
  text('dataset', `Active dataset: ${data.dataset.stage}; ${data.dataset.active_entries} records; checksum ${data.dataset.checksum}`);
  text('reference', `Trusted original: ${spec.expected_clean_reference}`);
  text('trigger-note', spec.mechanism === 'trigger' ? 'This is retrieval-trigger poisoning, not a backdoor learned into model weights. Compare with and without starlight mode.' : '');
  const previousAccount = el('account').value;
  options('account', data.accounts, a => a.id, a => `${a.display_alias} · ${a.trust_level} · ${a.age_days} days old`);
  el('account').value = selected ? 'new' : previousAccount || 'new';
  el('records').replaceChildren(...data.records.map(record => {
    const item = document.createElement('article'); item.textContent = `${record.submission_id} · ${record.disposition || 'accepted'} · ${record.source_id} · ${record.account.trust_level} · rating ${record.rating}\n${record.answer}\n${record.explanation || 'Deliberately weak acceptance.'}\n${record.duplicate_status || ''} · ${record.conflict_status || ''}`; return item;
  }));
  if (selected) {
    restoreDraft();
    if (learningMode === 'guided' && !learning.draft) useExample();
    renderWorksheet();
    el('explanation').open = false;
    el('evidence-summary').replaceChildren();
    stages = {}; experimentQuestion = null; el('comparison').replaceChildren(); el('sources').replaceChildren(); text('technical', ''); text('benchmark', '');
  }
  renderLearning();
}
function renderComparison() {
  const names = ['clean', 'vulnerable', 'hardened', 'recovered'];
  const table = document.createElement('table');
  const fields = [
    ['Question', r => r.question],
    ['Dataset version / checksum', r => `${r.dataset.dataset_id}\n${r.dataset.checksum}`],
    ['Submitted payload / decision', r => JSON.stringify((r.submissions || []).map(s => ({payload:s.submitted_payload || {answer:s.original_submitted_text,account_id:s.account_id,rating:s.rating,source_label:s.original_source_label || s.source_id}, disposition:s.disposition || 'accepted',reason:s.explanation})))],
    ['Retrieved sources', r => r.retrieved_source_ids.join('\n')],
    ['Trust and ranking', r => JSON.stringify(r.sources.map(s => ({id:s.source_id,trust:s.trust_level,classification:s.source_classification,rank:s.rank,signals:s.signals})))],
    ['Actual Ollama response', r => r.answer || 'Not observed: local model unavailable'],
    ['Untrusted data supplied', r => String(r.observations.untrusted_data_supplied_to_model ?? 'Not recorded in historical evidence')],
    ['Deterministic observations', r => JSON.stringify(r.observations)],
    ['Semantic findings', () => 'Manual interpretation required. Retrieval integrity and answer correctness are separate.']
  ];
  const heading = document.createElement('tr');
  for (const value of ['Field', ...names]) { const cell = document.createElement('th'); cell.textContent = value; heading.append(cell); }
  table.append(heading);
  for (const [label, value] of fields) {
    const row = document.createElement('tr');
    for (const content of [label, ...names.map(name => stages[name] ? value(stages[name]) : 'Not recorded')]) {
      const cell = document.createElement('td'); cell.textContent = content; row.append(cell);
    }
    table.append(row);
  }
  el('comparison').replaceChildren(table);
}
function compare(result) {
  rememberExperiment(result); evidenceSummary(result);
  // Only the explicit replay compares attacks across modes. Individual queries
  // replace earlier stages, except a recorded recovery after that experiment.
  if (result.stage !== 'recovered') stages = {};
  if (experimentQuestion !== result.question) { stages = {}; experimentQuestion = result.question; }
  const name = result.stage === 'clean' ? 'clean' : result.stage === 'recovered' ? 'recovered' : result.mode;
  stages[name] = result;
  if (result.comparison?.clean) stages.clean = result.comparison.clean;
  renderComparison();
  el('sources').replaceChildren(...result.sources.map(source => {
    const item = document.createElement('article'); item.textContent = `#${source.rank} ${source.id} · ${source.source_id} · ${source.trust_level} · score ${source.score}\n${source.answer}\n${JSON.stringify(source.signals)}`; return item;
  }));
  text('technical', JSON.stringify(result, null, 2));
  text('status', result.error ? 'Retrieval recorded; local Ollama unavailable. No model response observed.' : 'Observed model response recorded. Review claims against the trusted reference.');
}
el('scenario').addEventListener('change', () => action(async () => { saveDraft(); showState(await api('select', {scenario_id:el('scenario').value}), true); text('status','Scenario selected.'); }));
function payload() { return {answer:el('answer').value, account_id:el('account').value, rating:Number(el('rating').value), source_label:el('source').value}; }
el('mode').addEventListener('change', () => action(async () => { showState(await api('mode', {mode:el('mode').value})); text('status','Isolated protection mode selected.'); }));
el('refresh').addEventListener('click', () => action(async () => showState(await api('state'))));
el('replay').addEventListener('click', () => action(async () => {
  text('status','Running separate clean, vulnerable and hardened Ollama queries…');
  const report = await api('compare', {question:el('question').value, payload:payload()});
  Object.values(report.stages).filter(Boolean).forEach(rememberExperiment);
  evidenceSummary(report.stages.hardened);
  stages = report.stages; experimentQuestion = report.question;
  renderComparison(); text('technical',JSON.stringify(report,null,2));
  showState(await api('state')); text('status','Identical payload replay recorded. Inspect decisions, sources and each actual response; no automatic semantic pass.');
}));
el('inject').addEventListener('submit', event => { event.preventDefault(); action(async () => {
  const result = await api('inject', payload());
  showState(await api('state')); text('evidence-summary', `Submission: ${result.status}. Retrieval and model effect have not yet been tested for this submission.`); text('status', `${result.status}: ${result.record.submission_id}. Now ask the same question.`);
}); });
for (const stage of ['clean', 'current']) {
  el(stage).addEventListener('click', () => action(async () => compare(await api('query', {question:el('question').value, stage}))));
  el('benchmark-' + stage).addEventListener('click', () => action(async () => { text('status','Running benchmark subset…'); text('benchmark',JSON.stringify(await api('benchmark', {stage}),null,2)); text('status','Benchmark recorded; semantic interpretation requires review.'); }));
}
el('reset').addEventListener('click', () => action(async () => { await api('reset', {}); showState(await api('state')); text('status','Selected mode reset. Ask current hardened sandbox for a new recovered response. Previous observations and evidence retained.'); }));
el('learning-mode').addEventListener('change', () => {
  saveDraft(); learningMode = el('learning-mode').value;
  writeLocal(`p2-learning-mode:${state.session_id}`, learningMode); renderLearning();
});
for (const field of ['answer','question','rating','account','source']) el(field).addEventListener('input', saveDraft);
el('use-example').addEventListener('click', () => {
  if (window.confirm('Replace question, answer, rating, account and source label with the Guided example? Your notes and evidence will remain.')) useExample();
});
el('hint-next').addEventListener('click', () => {
  learning.hints = Math.min(3, (Number(learning.hints) || 0) + 1); saveLearning(); renderLearning();
});
el('learning-restart').addEventListener('click', () => {
  if (!window.confirm('Clear this scenario’s browser-local notes and hints? Draft, sandbox records and evidence remain.')) return;
  learning.notes = {}; learning.hints = 0; saveLearning(); renderWorksheet(); renderLearning(); el('explanation').open = false;
});
el('worksheet-export').addEventListener('click', () => downloadWorksheet('md'));
el('worksheet-json').addEventListener('click', () => downloadWorksheet('json'));
action(async () => { const data = await api('state'); options('scenario',data.scenarios,s => s.id,s => `${s.id} · ${s.title}`); el('scenario').value = data.scenario.id; showState(data,true); text('status', storageAvailable ? 'Ready. Explore approved knowledge and choose a clean question before injecting.' : 'Browser storage unavailable. Notes will be lost on refresh; export before leaving.'); });
