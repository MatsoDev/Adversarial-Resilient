'use strict';
(() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const pct = value => value == null ? 'Unavailable' : `${(value * 100).toFixed(2)}%`;
  const number = value => Number(value).toLocaleString('en-US', {maximumFractionDigits: 5});
  function selectRows(experiment, norm, attack) {
    return experiment.results.filter(r => r.norm === norm && (attack === 'all' || r.attack === attack));
  }
  function seriesKey(row) {
    const parameters = {...row.parameters};
    delete parameters.epsilon;
    return `${row.attack} ${JSON.stringify(parameters)}`;
  }
  function curve(rows) {
    const eligible = rows.filter(r => r.norm === 'Linf' && r.attack !== 'CW-L2');
    if (!eligible.length) return '<p>CW-L2 uses optimization parameters and L2 distortion. No epsilon curve applies.</p>';
    const maxE = Math.max(...eligible.map(r => r.parameters.epsilon), 0.001);
    const x = e => 65 + 680 * e / maxE, y = accuracy => 260 - 220 * accuracy;
    const groups = new Map();
    eligible.forEach(row => {const key = seriesKey(row); if (!groups.has(key)) groups.set(key, []); groups.get(key).push(row);});
    let body = '';
    for (let i = 0; i <= 4; i++) body += `<line class="gridline" x1="65" x2="745" y1="${y(i/4)}" y2="${y(i/4)}"/><text x="12" y="${y(i/4)+4}">${i*25}%</text>`;
    body += `<line class="cleanline" x1="65" x2="745" y1="${y(eligible[0].metrics.clean_accuracy)}" y2="${y(eligible[0].metrics.clean_accuracy)}"/>`;
    let legend = '<p>Dashed line: clean accuracy. Exact values and counts appear below.</p>';
    [...groups].forEach(([key, values], i) => {
      values.sort((a,b) => a.parameters.epsilon - b.parameters.epsilon);
      const color = `c${i%5}`;
      body += `<polyline class="series ${color}" points="${values.map(r => `${x(r.parameters.epsilon)},${y(r.metrics.attacked_accuracy)}`).join(' ')}"/>`;
      values.forEach(r => body += `<circle class="${color}" cx="${x(r.parameters.epsilon)}" cy="${y(r.metrics.attacked_accuracy)}" r="4"><title>${esc(key)} · ε ${r.parameters.epsilon} · ${pct(r.metrics.attacked_accuracy)}</title></circle>`);
      const first = values[0];
      const label = first.attack === 'PGD' ? `PGD · step ${first.parameters.step_size} · ${first.parameters.iterations} iterations` : first.attack;
      legend += `<p class="attack-series-label ${color}">${esc(label)}</p>`;
    });
    const epsilons = [...new Set(eligible.map(r => r.parameters.epsilon))].sort((a,b) => a-b);
    epsilons.forEach(e => body += `<text x="${x(e)}" y="283" text-anchor="middle">${e}</text>`);
    body += '<text x="400" y="312" text-anchor="middle">ε · standardized model coordinates</text>';
    return `<div class="attack-chart-scroll" tabindex="0" aria-label="Scrollable accuracy chart"><svg class="attack-chart" viewBox="0 0 800 330" role="img" aria-label="Accuracy versus epsilon; exact values in the results table">${body}</svg></div><p class="chart-scroll-hint">Scroll the chart horizontally for all epsilon values. Exact values are in the table below.</p>${legend}`;
  }
  function renderReport(experiment, norm, attack) {
    const rows = selectRows(experiment, norm, attack), id = experiment.identity;
    const qualification = experiment.baseline_qualification;
    const candidate = experiment.experiment_stage === 'development_candidate_not_frozen';
    const provenance = `<section class="panel"><h2>Comparison identity</h2>
      <p>${esc(id.dataset)} · ${esc(id.model_version)} · ${esc(id.split)}<br>${number(id.samples)} rows · seed ${esc(id.seed)} · threshold ${id.threshold}</p>
      <details><summary>Model, cohort and policy provenance</summary><div class="identity-grid">
      <p>Model bundle SHA-256<br><code>${esc(id.model_sha256)}</code></p>
      <p>Exact row indices SHA-256<br><code>${esc(id.indices_sha256)}</code></p>
      <p>Constraint policy SHA-256<br><code>${esc(id.constraint_sha256)}</code></p></div>
      <p>Constraint status: ${esc(experiment.constraint.status)} · reviewer: ${esc(experiment.constraint.reviewer)} · problem-space validation: unavailable.</p></details></section>`;
    let html = candidate ? `<section class="panel"><h2>Development model — not frozen</h2>
      <p>Full operating-validation accuracy: <strong>${pct(qualification?.validation_metrics?.accuracy)}</strong> on ${number(qualification?.validation_metrics?.n_samples || 0)} rows. Charts use ${id.samples} selected validation rows and cannot satisfy the 93% freeze gate.</p>
      <details><summary>Experiment scope and readiness</summary><p>This exploratory experiment does not complete M1 or enable prediction. ${esc(experiment.candidate_reason)}</p><p>Official test evaluated for this model: ${qualification?.test_evaluated ? 'yes' : 'no'}. Attack cohort: ${esc(id.cohort)}.</p></details></section>` : '';
    html += `<p class="kicker">Feature-space experiment · Technical Security review: ${esc(experiment.constraint.security_review || 'Asserted by the named local reviewer')} · Problem-space validation: unavailable.</p>`;
    if (!rows.length) return html + '<section class="panel attack-empty">No completed results match these filters. Choose another attack or norm.</section>' + provenance;
    const clean = rows[0].metrics;
    const rates = rows.map(r => r.metrics.attack_success_rate).filter(r => r != null);
    const maximumAsr = rates.length ? Math.max(...rates) : null;
    html += `<div class="stats"><article class="stat"><div class="stat-label">CLEAN ACCURACY</div><strong>${pct(clean.clean_accuracy)}</strong><small>${clean.clean_correct} / ${clean.samples} correct</small></article><article class="stat"><div class="stat-label">EVALUATED ROWS</div><strong>${clean.samples}</strong><small>Identical rows for every displayed result</small></article><article class="stat"><div class="stat-label">ASR DENOMINATOR</div><strong>${clean.asr_denominator}</strong><small>Originally correct · both classes</small></article><article class="stat"><div class="stat-label">MAXIMUM MEASURED ASR</div><strong>${pct(maximumAsr)}</strong><small>${rows.length} ${esc(norm)} configurations</small></article></div>`;
    html += `<section class="panel"><h2>${norm === 'L2' ? 'CW-L2 optimization' : 'Accuracy versus epsilon'}</h2>${curve(rows)}</section>`;
    html += '<section class="panel"><h2>Clean versus attacked · measured results</h2><div class="table-wrap"><table><thead><tr><th>ATTACK / PARAMETERS</th><th>CLEAN</th><th>ATTACKED</th><th>ASR / COUNTS</th><th>MEAN L0 / L2 / L∞</th><th>PROVENANCE / CROSS-CHECK</th></tr></thead><tbody>';
    rows.forEach(r => {
      const m = r.metrics, c = r.cross_check;
      const cross = c.status === 'completed' ? `CleverHans ${esc(c.version)} · accuracy ${pct(c.metrics.attacked_accuracy)} · ASR ${pct(c.metrics.attack_success_rate)} (${c.metrics.successful_attacks}/${c.metrics.asr_denominator}) · prediction agreement ${pct(c.prediction_agreement)} · mean candidate L2 difference ${number(c.mean_candidate_l2_difference)}` : `CleverHans: Not run · ${esc(c.reason)}`;
      html += `<tr><td><strong>${esc(r.attack)}</strong><br>${esc(JSON.stringify(r.parameters))}<br>${esc(r.projection)}</td><td>${pct(m.clean_accuracy)}<br>${m.clean_correct}/${m.samples}</td><td>${pct(m.attacked_accuracy)}<br>${m.attacked_correct}/${m.samples}</td><td>${pct(m.attack_success_rate)}<br>${m.successful_attacks}/${m.asr_denominator}</td><td>${['L0','L2','Linf'].map(k => number(m.mean_norms[k])).join(' / ')}</td><td>ART ${esc(r.library_version)}<br>${cross}</td></tr>`;
    });
    return html + `</tbody></table></div><details><summary>Full stored experiment and reproducibility data</summary><pre class="attack-detail">${esc(JSON.stringify(experiment,null,2))}</pre></details></section>` + provenance;
  }
  // Pure rendering helpers are also exercised by the optional Node test.
  if (typeof module !== 'undefined') module.exports = {selectRows, seriesKey, curve, renderReport};
  if (typeof document === 'undefined') return;
  const get = id => document.getElementById(id);
  let reports = [], request = 0;
  function render() {
    const report = reports[Number(get('attack-experiment').value)];
    get('attack-content').innerHTML = report ? renderReport(report, get('attack-norm').value, get('attack-method').value) : '';
  }
  async function load() {
    const token = ++request;
    const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 10000);
    get('attack-state').textContent = 'Loading completed experiments…';
    try {
      const response = await fetch('/v1/attacks', {signal:controller.signal, credentials:'omit', redirect:'error'});
      if (!response.ok) throw Error('Unable to fetch results');
      const payload = await response.json();
      if (token !== request) return;
      reports = payload.experiments;
      ['attack-experiment','attack-norm','attack-method'].forEach(id => get(id).disabled = !reports.length);
      get('attack-experiment').innerHTML = reports.map((r,i) => `<option value="${i}">${esc(r.generated_at)} · ${esc(r.identity.split)} · ${r.identity.samples} rows · ${esc(r.compatibility_id.slice(0,12))}</option>`).join('');
      get('attack-state').textContent = reports.length ? `${reports.length} completed experiment snapshots. ${payload.unavailable_reports} invalid reports excluded.${payload.truncated ? ' Result listing limited; some reports are omitted.' : ''}` : `Results pending. ${payload.pending_reason}. No measured EMBER attack scores are available.${payload.unavailable_reports ? ` ${payload.unavailable_reports} invalid reports excluded.` : ''}`;
      render();
    } catch (error) {
      if (token !== request) return;
      reports = [];
      ['attack-experiment','attack-norm','attack-method'].forEach(id => get(id).disabled = true);
      get('attack-content').innerHTML = '';
      get('attack-state').textContent = 'Results unavailable. Check the API and refresh. No cached scores are being shown.';
    } finally {clearTimeout(timer);}
  }
  ['attack-experiment','attack-norm','attack-method'].forEach(id => get(id).onchange = render);
  get('attack-refresh').onclick = load;
  load();
})();
