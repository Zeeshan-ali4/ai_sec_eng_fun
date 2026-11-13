'use strict';
const base = '/proposal-02/poisoning/api/';
const el = id => document.getElementById(id);
const text = (id, value) => { el(id).textContent = value; };
let state;
let clean = null;
async function api(path, data) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), path === 'benchmark' ? 510000 : 150000);
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
    const item = document.createElement('article'); item.textContent = `${record.submission_id} · accepted · ${record.source_id} · ${record.account.trust_level} · rating ${record.rating}\n${record.answer}`; return item;
  }));
  if (selected) {
    el('answer').value = spec.sample; el('question').value = spec.target_question;
    clean = null; el('comparison').replaceChildren(); el('sources').replaceChildren(); text('technical', ''); text('benchmark', '');
  }
}
function compare(result) {
  if (result.stage === 'clean') clean = result;
  const candidate = result.comparison.clean || clean;
  const baseline = candidate?.question === result.question && candidate?.generation === result.generation ? candidate : null;
  const table = document.createElement('table');
  const rows = [['Field','Clean','Current'], ['Question',baseline?.question || 'Ask clean snapshot first',result.question],
    ['Dataset',baseline?.dataset.checksum || 'Not recorded',result.dataset.checksum],
    ['Retrieved sources',baseline?.retrieved_source_ids.join('\n') || 'Not recorded',result.retrieved_source_ids.join('\n')],
    ['Answer',baseline?.answer || 'No model answer',result.answer || 'No model answer: local model unavailable'],
    ['Provenance',baseline?.sources.map(s => `${s.source_id}: ${s.trust_level}`).join('\n') || 'Not recorded', result.sources.map(s => `${s.source_id}: ${s.trust_level}`).join('\n')],
    ['Retrieval integrity','Original trusted snapshot',JSON.stringify(result.observations)],
    ['Answer correctness','Review against trusted reference','Manual review required; changed prose alone does not prove false claims']];
  for (const [n, row] of rows.entries()) {
    const tr = document.createElement('tr');
    row.forEach(value => { const cell = document.createElement(n ? 'td':'th'); cell.textContent = value; tr.append(cell); }); table.append(tr);
  }
  el('comparison').replaceChildren(table);
  el('sources').replaceChildren(...result.sources.map(source => {
    const item = document.createElement('article'); item.textContent = `#${source.rank} ${source.id} · ${source.source_id} · ${source.trust_level} · score ${source.score}\n${source.answer}\n${JSON.stringify(source.signals)}`; return item;
  }));
  text('technical', JSON.stringify(result, null, 2));
  text('status', result.error ? 'Retrieval recorded; local Ollama unavailable. No model response observed.' : 'Observed model response recorded. Review claims against the trusted reference.');
}
el('scenario').addEventListener('change', () => action(async () => { showState(await api('select', {scenario_id:el('scenario').value}), true); text('status','Scenario selected.'); }));
el('inject').addEventListener('submit', event => { event.preventDefault(); action(async () => {
  const result = await api('inject', {answer:el('answer').value, account_id:el('account').value, rating:Number(el('rating').value), source_label:el('source').value});
  showState(await api('state')); text('status', `${result.status}: ${result.record.submission_id}. Now ask the same question.`);
}); });
for (const stage of ['clean', 'current']) {
  el(stage).addEventListener('click', () => action(async () => compare(await api('query', {question:el('question').value, stage}))));
  el('benchmark-' + stage).addEventListener('click', () => action(async () => { text('status','Running benchmark subset…'); text('benchmark',JSON.stringify(await api('benchmark', {stage}),null,2)); text('status','Benchmark recorded; semantic interpretation requires review.'); }));
}
el('reset').addEventListener('click', () => action(async () => { await api('reset', {}); showState(await api('state'), true); text('status','Selected sandbox restored. Previous evidence retained.'); }));
action(async () => { const data = await api('state'); options('scenario',data.scenarios,s => s.id,s => `${s.id} · ${s.title}`); el('scenario').value = data.scenario.id; showState(data,true); text('status','Ready. Ask the clean snapshot before injecting.'); });
