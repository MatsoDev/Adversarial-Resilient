"""Exercise the dependency-free prediction JavaScript with a minimal DOM, when Node exists."""

import shutil
import subprocess

import pytest
from src.config import ROOT


@pytest.mark.skipif(
    shutil.which("node") is None, reason="Optional Node JavaScript runtime unavailable"
)
def test_prediction_javascript_success_invalid_input_and_unavailable():
    script = r"""
const assert = require('node:assert/strict');
const elements = {};
global.document = {getElementById: id => elements[id] ||= {value: '', textContent: '', disabled: false}};
let status = 200, calls = [];
const identity = {model_version:'baseline_v1', preprocessing_sha256:'a'.repeat(64), feature_schema_sha256:'b'.repeat(64)};
global.fetch = async (path, options) => {
  calls.push({path, options});
  return {ok: status === 200, status, json: async () => path === '/v1/baseline' ? identity : {predictions:[{label:1,score:0.8}]}};
};
require(process.argv[1]);
for (const id of ['prediction-token', 'prediction-rows', 'prediction-representation', 'prediction-result', 'baseline-info']) document.getElementById(id);
(async () => {
  elements['prediction-token'].value = 'test-token';
  await elements['baseline-load'].onclick();
  assert.equal(elements['prediction-submit'].disabled, false);
  elements['prediction-rows'].value = JSON.stringify([Array(2381).fill(0)]);
  elements['prediction-representation'].value = 'raw';
  await elements['prediction-submit'].onclick();
  assert.match(elements['prediction-result'].textContent, /0.8/);
  const request = calls.at(-1);
  assert.equal(request.path, '/predict');
  assert.equal(request.options.headers.Authorization, 'Bearer test-token');
  assert.equal(JSON.parse(request.options.body).preprocessing_id, identity.preprocessing_sha256);
  assert.equal(request.options.credentials, 'omit');
  assert.equal(request.options.redirect, 'error');
  const before = calls.length;
  elements['prediction-rows'].value = JSON.stringify([Array(2381).fill('0')]);
  await elements['prediction-submit'].onclick();
  assert.equal(calls.length, before);
  assert.match(elements['prediction-result'].textContent, /finite numeric/);
  status = 503;
  await elements['baseline-load'].onclick();
  assert.equal(elements['prediction-submit'].disabled, true);
  assert.match(elements['baseline-info'].textContent, /not frozen/);
})().catch(error => { console.error(error); process.exitCode = 1; });
"""
    result = subprocess.run(
        [shutil.which("node"), "-e", script, str(ROOT / "dashboard/web/prediction.js")],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
