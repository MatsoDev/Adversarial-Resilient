'use strict';
// Tokens and feature rows remain in this page only: no storage, uploads or history.
(() => {
  const element = id => document.getElementById(id);
  let identity = null;
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
    try {
      identity = await request('/v1/baseline');
      element('baseline-info').textContent = JSON.stringify(identity, null, 2);
      element('prediction-submit').disabled = false;
    } catch (error) { element('baseline-info').textContent = error.message; }
  };
  element('prediction-submit').onclick = async () => {
    if (!identity) return;
    element('prediction-submit').disabled = true;
    try {
      const text = element('prediction-rows').value;
      if (text.length > 2 * 1024 * 1024) throw new Error('Request too large.');
      const rows = JSON.parse(text);
      if (!Array.isArray(rows) || rows.length < 1 || rows.length > 32 ||
          rows.some(row => !Array.isArray(row) || row.length !== 2381 ||
            row.some(value => typeof value !== 'number' || !Number.isFinite(value)))) {
        throw new Error('Expected 1–32 finite numeric rows, each with exactly 2381 features.');
      }
      const result = await request('/predict', {model_version: identity.model_version,
        representation: element('prediction-representation').value,
        preprocessing_id: identity.preprocessing_sha256,
        feature_schema_sha256: identity.feature_schema_sha256, rows});
      element('prediction-result').textContent = JSON.stringify(result, null, 2);
    } catch (error) { element('prediction-result').textContent = error.message; }
    finally { element('prediction-submit').disabled = !identity; }
  };
})();
