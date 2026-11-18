'use strict';
(() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const pct = value => value == null ? 'Unavailable' : `${(value * 100).toFixed(2)}%`;
  const number = value => Number(value).toLocaleString('en-US', {maximumFractionDigits: 5});
  const label = value => value === 1 ? 'Malicious' : 'Benign';
  const outcomes = {successful_attack:'Successful attack', remained_correct:'Remained correct', preexisting_error:'Preexisting error'};
  function configLabel(row) {
    const p = row.parameters;
    if (row.attack === 'CW-L2') return `CW-L2 · ${p.iterations} iterations · ${p.binary_search_steps} searches`;
    return `${row.attack} · ε ${p.epsilon}${row.attack === 'PGD' ? ` · step ${p.step_size} · ${p.iterations} iterations` : ''}`;
  }
  function cases(report) {
    return journeyRows(report).flatMap((row, rowIndex) => (row.examples || []).map((example, exampleIndex) => ({row, rowIndex, example, exampleIndex})));
  }
  function journeyRows(report) {
    return report.results.flatMap(row => [row, ...(row.transfer ? [{...row, evidence_mode:'transfer', metrics:row.transfer.target_metrics, examples:row.transfer.examples}] : [])]);
  }
  function explain(example) {
    if (example.outcome === 'preexisting_error') return 'The model was already wrong. This case is not evidence of a successful attack and is excluded from the ASR denominator.';
    if (example.outcome === 'remained_correct') return 'The model stayed correct after this attempt. That is one resisted case, not a guarantee against every attack.';
    return example.true_label === 1
      ? 'The model initially detected this malicious sample, then called it benign after the feature change. This attempt successfully fooled the decision on this feature row.'
      : 'This sample is benign. The model was initially correct, but the change caused a malicious verdict: a false alarm, not malware escaping detection.';
  }
  function decision(title, prediction, score, truth) {
    return `<article class="decision ${prediction === truth ? 'correct' : 'incorrect'}"><span>${title}</span><strong>${label(prediction)}</strong><p>${prediction === truth ? 'Correct decision' : 'Incorrect decision'} against the known label</p><details class="decision-score"><summary>See the model score</summary><meter min="0" max="1" value="${score}" aria-label="Malicious-class score"></meter><small>Model score for malicious: <b dir="ltr">${pct(score)}</b></small></details></article>`;
  }
  function renderCase(report, row, example) {
    const m = row.metrics, q = report.baseline_qualification, candidate = report.experiment_stage === 'development_candidate_not_frozen';
    const changes = example.changes.map(c => `<tr><td>${c.index === 616 ? 'Recorded file-size value' : esc(c.operation)}<small class="technical-coordinate">Feature ${esc(c.index)}</small></td><td dir="ltr">${number(c.raw_before)}</td><td dir="ltr">${number(c.raw_after_approx)}</td></tr>`).join('');
    const sample = `<div class="truth">Known dataset label: <strong>${label(example.true_label)}</strong><small>This reference label is how we judge correctness; it is not a model guess.</small></div>`;
    const comparison = `<div class="decision-grid">${decision('Before attack', example.clean_prediction, example.clean_malicious_score, example.true_label)}<div class="attack-bridge"><span aria-hidden="true">←</span><strong>${esc(row.attack)}</strong></div>${decision('After attack', example.attacked_prediction, example.attacked_malicious_score, example.true_label)}</div>`;
    const transfer = row.evidence_mode === 'transfer';
    const context = `<section class="panel"><h2>${transfer ? 'Black-box transfer' : 'White-box'} · Feature-space only</h2><p>Scalar constraints only. Coupled consistency, executable realizability and preserved behavior are not established.</p><p>Constraint review: ${esc(report.constraint.security_review || report.constraint.status)}</p>${transfer ? `<p>Source gradients only; no target feedback during crafting. Public true labels. All rows retained, with no target-based filtering.</p><details><summary>Source and target decisions</summary><p dir="ltr">Source ${esc(report.identity.transfer_source.model_sha256)} · ${example.source_clean_prediction} → ${example.source_attacked_prediction}</p><p dir="ltr">Target ${esc(report.identity.model_sha256)} · ${example.clean_prediction} → ${example.attacked_prediction}</p><p>Known label: ${example.true_label}. Scores are not file-safety guarantees.</p></details>` : '<p>White-box target gradients. Transfer has not been measured for this case.</p>'}<a href="transfer.html">Threat context and transfer</a></section>`;
    return `${context}<section class="readiness"><strong>${candidate ? 'Experimental detector — research only' : 'Frozen evaluation model'}</strong><p>This is a research prototype, not an assurance that a file is safe.</p><details><summary>Model readiness details</summary><p>${candidate ? `Full operating-validation accuracy: ${pct(q?.validation_metrics?.accuracy)}, below the 93% freeze gate. Small-cohort results below do not replace full validation.` : 'A frozen model does not establish that a feature edit is a valid executable modification.'}</p></details></section>
    <section class="panel guided-story" aria-label="Recorded example walkthrough"><div class="story-heading"><div><span class="eyebrow">ONE MEASURED CASE</span><h2>A file description. One decision. One challenge.</h2></div><span class="sample-id" dir="ltr">EMBER · ${esc(report.identity.split)} row ${example.split_row_index}</span></div>
    <div class="walkthrough-tabs" role="group" aria-label="Walkthrough steps"><button type="button" data-step="0" aria-pressed="true">1 · Original sample</button><button type="button" data-step="1" aria-pressed="false">2 · The change</button><button type="button" data-step="2" aria-pressed="false">3 · The result</button></div>
    <section data-stage="0"><span class="step-counter">STEP 1 OF 3</span><h3>First, check the answer before any attack.</h3><p>The dataset tells us the known label. The AI makes its own prediction. Comparing the two tells us whether the AI started out correct.</p><p class="label-glossary">Benign means non-malicious. Malicious means labelled as malware. A model prediction is not a file-safety guarantee.</p>${sample}<div class="single-decision">${decision('Before attack',example.clean_prediction,example.clean_malicious_score,example.true_label)}</div><p class="step-caption">${example.clean_prediction === example.true_label ? 'The AI got this example right. Next, we will challenge that decision.' : 'The AI was already wrong here. Keep that in mind: this is not an attack-induced error.'}</p></section>
    <section data-stage="1" hidden><span class="step-counter">STEP 2 OF 3</span><h3>Change the description, then ask the AI again.</h3><p>An adversarial attack deliberately looks for an allowed change that makes the model answer incorrectly. We replay the measured change below; no experiment runs in your browser.</p>${changes ? `<div class="table-wrap"><table><thead><tr><th>Feature</th><th>Before</th><th>After ≈</th></tr></thead><tbody>${changes}</tbody></table></div>` : '<p>No coordinates changed above the 10⁻⁶ measurement tolerance.</p>'}<div class="feature-context"><strong>What this means in this experiment</strong><p>${example.changes.length ? (report.constraint.policy?.features?.length === 1 && report.constraint.policy.features[0].index === 616 ? 'Only the listed numeric features changed. For this size-only probe, all other 2,380 coordinates stayed fixed. The raw size values above are approximate bytes, reconstructed from the measured model inputs.' : 'Only the listed numeric features changed above the measurement tolerance. Raw values are approximate inverse transforms of the measured model inputs.') : 'This recorded attempt produced no feature change above the measurement tolerance. That is a real outcome too.'}</p><p>No bytes in an actual file were changed. We are testing the model on feature descriptions.</p></div><details><summary>Technical attack settings</summary><p dir="ltr">${esc(configLabel(row))}</p><pre dir="ltr">${esc(JSON.stringify(row.parameters,null,2))}</pre><p>Raw values after the change are approximate inverse transforms, rounded for integer features. These are feature edits, not edits to an actual file.</p><p dir="ltr">L0: ${number(example.norms.L0)} · L2: ${number(example.norms.L2)} · L∞: ${number(example.norms.Linf)}</p><p>Norms use standardized model coordinates; ε is not a percentage.</p></details></section>
    <section data-stage="2" hidden><span class="step-counter">STEP 3 OF 3</span><h3>${outcomes[example.outcome]}</h3>${sample}${comparison}<details class="score-explanation"><summary>How should I read the scores?</summary><p class="score-note">The score is not file safety or attack success rate. The classification threshold is 50%.</p></details><section class="takeaway"><h2>What happened?</h2><p>${explain(example)}</p></section><div class="feature-context"><h3>Why does this matter?</h3><p>This test helps engineers find where an AI detector can fail. They can then compare a stronger version under the same conditions. One case explains a failure; the whole cohort measures its frequency.</p></div><details class="cohort-summary"><summary>How often did this happen in the experiment?</summary><p>The first available case of each outcome is deliberately selected for explanation, not as an independent statistical sample.</p><div class="summary-numbers"><div><strong>${m.samples}</strong><span>evaluated samples</span></div><div><strong dir="ltr">${m.clean_correct} → ${m.attacked_correct}</strong><span>correct decisions: before → after</span></div><div><strong dir="ltr">${m.successful_attacks}/${m.asr_denominator}</strong><span>induced errors / initially correct · <bdi>${pct(m.attack_success_rate)}</bdi></span></div></div><p>ASR includes errors induced in either class, not only missed malicious samples.</p></details><section class="next-defense"><span class="tag">Planned · Sprint 9–12</span><h3>What happens after hardening?</h3><p>We will add measured hardened-model comparisons and re-attack that model. Defense results are not available yet; no improvement is assumed.</p></section></section>
    <div class="walkthrough-actions"><button type="button" id="journey-previous" disabled>Previous step</button><span id="journey-progress" role="status">1 / 3</span><button type="button" id="journey-next" class="primary-action">Next: see the change →</button></div></section>
    <section class="panel"><details><summary>Case provenance and comparison limits</summary><p dir="ltr">${esc(report.generated_at)} · ART ${esc(row.library_version)} · CleverHans: ${esc(row.cross_check.status)}</p><p>Constraint review: ${esc(report.constraint.security_review || report.constraint.status)}. Problem-space validity: not established.</p><p>Same recorded model, cohort and policy. The row is a dataset split reference, not an uploaded filename. No executables or complete feature arrays reach the browser.</p><dl class="provenance" dir="ltr"><dt>Model SHA-256</dt><dd data-evidence>${esc(report.identity.model_sha256)}</dd><dt>Cohort SHA-256</dt><dd data-evidence>${esc(report.identity.indices_sha256)}</dd><dt>Policy SHA-256</dt><dd data-evidence>${esc(report.identity.constraint_sha256)}</dd></dl><p>Larger evaluations and an accepted baseline are needed before generalizing. Aggregate-only historical reports remain available in Attack comparison.</p></details></section>`;

  }
  if (typeof module !== 'undefined') module.exports = {cases, explain, renderCase, journeyRows};
  if (typeof document === 'undefined') return;
  const get = id => document.getElementById(id);
  let reports = [];
  function selectedReport() {
    const report = reports[Number(get('journey-experiment').value)];
    return report ? {...report,results:journeyRows(report)} : undefined;
  }
  let step = 0;
  function showStep(value, moveToStory=false) {
    step = Math.max(0,Math.min(2,value));
    document.querySelectorAll('[data-stage]').forEach(el => el.hidden = Number(el.dataset.stage) !== step);
    document.querySelectorAll('[data-step]').forEach(el => el.setAttribute('aria-pressed',String(Number(el.dataset.step) === step)));
    get('journey-previous').disabled = step === 0;
    get('journey-next').textContent = ['Next: see the change →','Next: see the result →','Restart walkthrough ↻'][step];
    get('journey-progress').textContent = `${step+1} / 3`;
    if (moveToStory) {
      const heading = document.querySelector(`[data-stage="${step}"] h3`);
      heading.setAttribute('tabindex','-1');
      heading.focus({preventScroll:true});
      document.querySelector('.guided-story').scrollIntoView({block:'start'});
    }
  }
  function render() {
    const report = selectedReport(), row = report?.results[Number(get('journey-attack').value)];
    const example = row?.examples?.[Number(get('journey-case').value)];
    get('journey-content').innerHTML = example ? renderCase(report,row,example) : '<section class="panel">No individual case is recorded for this configuration. Open Attack comparison for aggregate results.</section>';
    if (example) {
      document.querySelectorAll('[data-step]').forEach(button => button.onclick = () => showStep(Number(button.dataset.step),true));
      get('journey-previous').onclick = () => showStep(step-1,true);
      get('journey-next').onclick = () => showStep(step === 2 ? 0 : step+1,true);
      showStep(0);
    }
  }
  function updateCases() {
    const row = selectedReport()?.results[Number(get('journey-attack').value)];
    get('journey-case').innerHTML = (row?.examples || []).map((e,i) => `<option value="${i}">${outcomes[e.outcome]} · row ${e.split_row_index}</option>`).join('');
    get('journey-case').disabled = !row?.examples?.length;
    render();
  }
  function updateAttacks() {
    const report = selectedReport();
    get('journey-attack').innerHTML = report.results.map((r,i) => ({r,i})).filter(({r}) => r.examples?.length).map(({r,i}) => `<option value="${i}">${r.evidence_mode === 'transfer' ? 'Black-box transfer' : 'White-box'} · ${esc(configLabel(r))}</option>`).join('');
    const success = report.results.findIndex(r => r.examples?.some(e => e.outcome === 'successful_attack'));
    if (success >= 0) get('journey-attack').value = String(success);
    get('journey-attack').disabled = false;
    updateCases();
  }
  async function load() {
    const controller = new AbortController(), timer = setTimeout(() => controller.abort(),10000);
    try {
      const response = await fetch('/v1/attacks', {signal:controller.signal});
      if (!response.ok) throw Error('API unavailable');
      const data = await response.json();
      reports = data.experiments.filter(r => cases(r).length);
      if (!reports.length) { get('journey-state').textContent = 'No measured individual cases are available yet. Open Attack comparison for aggregate results; we will not invent a story from aggregate numbers.'; return; }
      get('journey-experiment').innerHTML = reports.map((r,i) => `<option value="${i}">${esc(r.identity.dataset)} · ${r.identity.samples} rows · ${esc(r.generated_at)} · ${esc(r.compatibility_id.slice(0,8))}</option>`).join('');
      get('journey-experiment').disabled = false;
      get('journey-state').textContent = `${reports.length} experiment(s) with measured individual cases.${data.unavailable_reports ? ` Invalid reports excluded: ${data.unavailable_reports}.` : ''}${data.truncated ? ' The list is bounded; not all reports are shown.' : ''}`;
      updateAttacks();
    } catch (_) { get('journey-state').innerHTML = 'Could not load results. Check that the API is running, then <button id="journey-retry" type="button">Retry</button>.'; get('journey-retry').onclick = load; }
    finally { clearTimeout(timer); }
  }
  get('journey-experiment').onchange = updateAttacks;
  get('journey-attack').onchange = updateCases;
  get('journey-case').onchange = render;
  load();
})();
