'use strict';
(() => {
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const ratio = value => value == null ? 'Pending / unavailable' : `${value.numerator}/${value.denominator} · ${value.rate == null ? 'Pending / unavailable' : (100*value.rate).toFixed(2)+'%'}`;
  const asr = m => ratio({numerator:m.successful_attacks,denominator:m.asr_denominator,rate:m.attack_success_rate});
  function renderReport(report) {
    const identity = report.identity, source = identity.transfer_source;
    const rows = report.results.map(row => {
      const t = row.transfer;
      const result = (mode, subject, m, outcomes) => `<tr><td>${esc(row.attack)}<pre>${esc(JSON.stringify(row.parameters))}</pre></td><td>${mode}</td><td>${subject}</td><td>${m ? `${m.attacked_correct}/${m.samples}` : 'Pending / unavailable'}</td><td>${m ? asr(m) : 'Pending / unavailable'}</td><td>${outcomes ? ratio(outcomes.malware_evasion) : 'Pending / unavailable'}</td><td>${outcomes ? ratio(outcomes.false_positive_induction) : 'Pending / unavailable'}</td><td>${outcomes ? outcomes.preexisting_errors : (m ? m.samples-m.clean_correct : 'Pending / unavailable')}</td></tr>`;
      return result('White-box','Target',row.metrics,row.outcomes) + (t ? result('Surrogate white-box','Source',t.source_metrics,t.source_outcomes) : '') + result('Black-box transfer','Target',t?.target_metrics,t?.target_outcomes);
    }).join('');
    return `<section class="panel"><h2>Attacker knowledge and provenance</h2><p>${source ? 'Source gradients only; no target feedback during crafting. Public true labels. All rows retained, with no target-based filtering.' : 'White-box target gradients. Transfer has not been measured in this snapshot.'}</p><p>${esc(report.experiment_stage || 'frozen_baseline')} · ${esc(identity.split)} · ${esc(identity.cohort)} · ${identity.samples} samples · seed ${esc(identity.seed)} · threshold ${identity.threshold}</p><p>Constraint review: ${esc(report.constraint.security_review || report.constraint.status)}</p><details><summary>Model, cohort and policy provenance</summary><dl class="provenance" dir="ltr"><dt>Target SHA-256</dt><dd>${esc(identity.model_sha256)}</dd><dt>Source SHA-256</dt><dd>${source ? esc(source.model_sha256) : 'Pending / unavailable'}</dd><dt>Dataset manifest SHA-256</dt><dd>${esc(identity.manifest_sha256)}</dd><dt>Cohort SHA-256</dt><dd>${esc(identity.indices_sha256)}</dd><dt>Policy SHA-256</dt><dd>${esc(identity.constraint_sha256)}</dd><dt>Preprocessing SHA-256</dt><dd>${esc(identity.preprocessing_sha256)}</dd></dl><pre>${esc(JSON.stringify({identity,constraint:report.constraint,generated_at:report.generated_at,source_sha256:report.source_sha256},null,2))}</pre></details></section>
    <section class="panel"><h2>White-box and black-box results</h2><p>Correct / all rows; ASR numerator / clean-correct denominator. Class-specific rates use class-specific clean-correct denominators.</p><div class="table-wrap" tabindex="0" role="region" aria-label="White-box and black-box results"><table><thead><tr><th>Attack and parameters</th><th>Knowledge</th><th>Model</th><th>Attacked correct</th><th>ASR</th><th>Malware evasion</th><th>False-positive induction</th><th>Preexisting errors</th></tr></thead><tbody>${rows}</tbody></table></div></section>
    ${source ? `<section class="panel"><h2>Conditional transfer</h2>${report.results.map(row => `<p>${esc(row.attack)} · ${esc(JSON.stringify(row.parameters))} · ${ratio(row.transfer.conditional_transfer)}</p><details><summary>Transferred sample digest</summary><code>${esc(row.transfer.candidate_sha256)}</code></details>`).join('')}<p>Deliberately selected case studies are available in the AI journey when recorded.</p></section>` : '<section class="callout">Transfer results pending. Recorded white-box results are not black-box evidence.</section>'}`;
  }
  function renderMappings(context, language='en') {
    return context.mappings.map(mapping => `<article><h3>${esc(mapping.attacks.join(' / '))} · ${mapping.mode === 'transfer' ? 'Black-box transfer' : 'White-box'}</h3><p dir="ltr">${esc(mapping.atlas.join(', '))} · ${esc(mapping.owasp.join(', '))}</p><p>${esc(language === 'ar' ? mapping.rationale_ar : mapping.rationale_en)}</p></article>`).join('') + context.references.map(ref => {
      // Only same known authoritative HTTPS hosts; never insert artifact-selected URLs.
      let url; try { url = new URL(ref.url); } catch (_) { return ''; }
      if (url.protocol !== 'https:' || url.hostname !== 'github.com' || url.username || url.password) return '';
      return `<p><a href="${esc(url.href)}" rel="noreferrer">${esc(ref.name)} · ${esc(ref.version)}</a> · <code>${esc(ref.revision)}</code></p>`;
    }).join('') + '<p>OWASP ML07 transfer learning is not adversarial-example transfer. ATLAS evasion intent does not establish executable evasion.</p>';
  }
  if (typeof module !== 'undefined') module.exports = {renderReport,renderMappings,ratio};
  if (typeof document === 'undefined') return;
  const get = id => document.getElementById(id);
  let reports = [], context = null;
  function render() {
    const report = reports[Number(get('transfer-experiment').value)];
    get('transfer-content').innerHTML = report ? renderReport(report) : '<section class="callout">No measured results available. Missing evidence is not a zero success rate.</section>';
    get('transfer-mappings').innerHTML = context ? renderMappings(context,document.documentElement.lang) : 'Threat mappings unavailable.';
  }
  async function load() {
    get('transfer-refresh').disabled = true;
    get('transfer-experiment').disabled = true;
    reports = []; context = null; render();
    get('transfer-state').textContent = 'Loading measured results…';
    const controller = new AbortController(), timer = setTimeout(() => controller.abort(),10000);
    try {
      const results = await Promise.allSettled(['/v1/attacks','/v1/threat-context'].map(async url => {
        const response = await fetch(url,{signal:controller.signal});
        if (!response.ok) throw Error('API unavailable');
        return response.json();
      }));
      const attacks = results[0].status === 'fulfilled' ? results[0].value : null;
      if (attacks && !Array.isArray(attacks.experiments)) throw Error('Malformed response');
      reports = attacks?.experiments || [];
      context = results[1].status === 'fulfilled' ? results[1].value : null;
      if (context && (!Array.isArray(context.mappings) || !Array.isArray(context.references))) throw Error('Malformed context');
      get('transfer-experiment').innerHTML = reports.map((r,i) => `<option value="${i}">${esc(r.identity.dataset)} · ${esc(r.compatibility_id.slice(0,12))} · ${esc(r.generated_at)}</option>`).join('');
      get('transfer-experiment').disabled = !reports.length;
      get('transfer-state').textContent = !attacks ? 'Could not load results. Use refresh to retry.' : `Completed snapshots: ${reports.length}. Invalid reports excluded: ${attacks.unavailable_reports || 0}.${attacks.truncated ? ' The list is bounded; not all reports are shown.' : ''}`;
      render();
    } catch (_) {
      reports = []; context = null; render();
      get('transfer-state').textContent = 'Could not load results. Use refresh to retry.';
    } finally { clearTimeout(timer); get('transfer-refresh').disabled = false; }
  }
  get('transfer-refresh').onclick = load;
  get('transfer-experiment').onchange = render;
  document.addEventListener('arsm-language',render);
  load();
})();
