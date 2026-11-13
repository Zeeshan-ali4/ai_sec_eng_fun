'use strict';
const base = '/proposal-02/poisoning/api/';
const el = id => document.getElementById(id);
const text = (id, value) => { el(id).textContent = value; };
let state;
let stages = {};
let experimentQuestion = null;
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
  state = data;
  const spec = data.scenario;
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
    el('answer').value = spec.sample; el('question').value = spec.target_question;
    stages = {}; experimentQuestion = null; el('comparison').replaceChildren(); el('sources').replaceChildren(); text('technical', ''); text('benchmark', '');
  }
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
el('scenario').addEventListener('change', () => action(async () => { showState(await api('select', {scenario_id:el('scenario').value}), true); text('status','Scenario selected.'); }));
function payload() { return {answer:el('answer').value, account_id:el('account').value, rating:Number(el('rating').value), source_label:el('source').value}; }
el('mode').addEventListener('change', () => action(async () => { showState(await api('mode', {mode:el('mode').value})); text('status','Isolated protection mode selected.'); }));
el('refresh').addEventListener('click', () => action(async () => showState(await api('state'))));
el('replay').addEventListener('click', () => action(async () => {
  text('status','Running separate clean, vulnerable and hardened Ollama queries…');
  const report = await api('compare', {question:el('question').value, payload:payload()});
  stages = report.stages; experimentQuestion = report.question;
  renderComparison(); text('technical',JSON.stringify(report,null,2));
  showState(await api('state')); text('status','Identical payload replay recorded. Inspect decisions, sources and each actual response; no automatic semantic pass.');
}));
el('inject').addEventListener('submit', event => { event.preventDefault(); action(async () => {
  const result = await api('inject', payload());
  showState(await api('state')); text('status', `${result.status}: ${result.record.submission_id}. Now ask the same question.`);
}); });
for (const stage of ['clean', 'current']) {
  el(stage).addEventListener('click', () => action(async () => compare(await api('query', {question:el('question').value, stage}))));
  el('benchmark-' + stage).addEventListener('click', () => action(async () => { text('status','Running benchmark subset…'); text('benchmark',JSON.stringify(await api('benchmark', {stage}),null,2)); text('status','Benchmark recorded; semantic interpretation requires review.'); }));
}
el('reset').addEventListener('click', () => action(async () => { await api('reset', {}); showState(await api('state')); text('status','Selected mode reset. Ask current hardened sandbox for a new recovered response. Previous observations and evidence retained.'); }));
action(async () => { const data = await api('state'); options('scenario',data.scenarios,s => s.id,s => `${s.id} · ${s.title}`); el('scenario').value = data.scenario.id; showState(data,true); text('status','Ready. Ask the clean snapshot before injecting.'); });
