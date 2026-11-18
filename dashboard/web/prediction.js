'use strict';
// Tokens and feature rows remain in this page only: no storage, uploads or history.
(() => {
  const element = id => document.getElementById(id);
  let identity = null;
  function status(id, message, evidence=false) {
    const target = element(id);
    target.toggleAttribute('data-ui-copy', !evidence);
    target.textContent = message;
  }
  const failure = error => error instanceof TypeError || error.name === 'AbortError'
    ? 'Connection failed or timed out. Please retry.' : error.message;
  async function request(path, payload) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    try {
      const headers = {'Authorization': `Bearer ${element('prediction-token').value}`};
      if (payload) headers['Content-Type'] = 'application/json';
      const response = await fetch(path, {method: payload ? 'POST' : 'GET', headers,
        body: payload ? JSON.stringify(payload) : undefined, signal: controller.signal,
        redirect: 'error', credentials: 'omit', cache: 'no-store'});
      if (!response.ok) {
        const messages = {401:'Access denied. Check the prediction token.', 413:'Request too large.',
          422:'Invalid rows or schema/preprocessing identity.', 429:'Query budget exceeded. Wait one minute.',
          503:'Prediction unavailable: token not configured or M1 baseline not frozen.'};
        throw new Error(messages[response.status] || 'Prediction request failed.');
      }
      return await response.json();
    } finally { clearTimeout(timer); }
  }
  element('baseline-load').onclick = async () => {
    identity = null;
    element('prediction-submit').disabled = true;
    element('baseline-load').disabled = true;
    status('baseline-info','Loading frozen model identity…');
    try {
      identity = await request('/v1/baseline');
      status('baseline-info',JSON.stringify(identity, null, 2),true);
      element('prediction-submit').disabled = false;
    } catch (error) { status('baseline-info',failure(error)); }
    finally { element('baseline-load').disabled = false; }
  };
  element('prediction-submit').onclick = async () => {
    if (!identity) return;
    element('prediction-submit').disabled = true;
    element('baseline-load').disabled = true;
    status('prediction-result','Classifying feature rows…');
    try {
      const text = element('prediction-rows').value;
      if (text.length > 2 * 1024 * 1024) throw new Error('Request too large.');
      let rows;
      try { rows = JSON.parse(text); }
      catch (_) { throw new Error('Invalid JSON. Enter an array of numeric rows.'); }
      if (!Array.isArray(rows) || rows.length < 1 || rows.length > 32 ||
          rows.some(row => !Array.isArray(row) || row.length !== 2381 ||
            row.some(value => typeof value !== 'number' || !Number.isFinite(value)))) {
        throw new Error('Expected 1–32 finite numeric rows, each with exactly 2381 features.');
      }
      const result = await request('/predict', {model_version: identity.model_version,
        representation: element('prediction-representation').value,
        preprocessing_id: identity.preprocessing_sha256,
        feature_schema_sha256: identity.feature_schema_sha256, rows});
      status('prediction-result',JSON.stringify(result, null, 2),true);
    } catch (error) { status('prediction-result',failure(error)); }
    finally {
      element('prediction-submit').disabled = !identity;
      element('baseline-load').disabled = false;
    }
  };
})();
