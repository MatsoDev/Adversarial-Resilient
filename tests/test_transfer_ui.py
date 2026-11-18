"""Node components and HTTP delivery; browser evidence is documented separately."""

import json
import shutil
import subprocess

import pytest
from api.main import create_app
from fastapi.testclient import TestClient
from src.config import ROOT
from src.evaluation.threat_context import threat_context

from tests import test_attacks, test_transfer

report_fixture = test_attacks.report_fixture
run = test_transfer.run
transfer_inputs = test_transfer.transfer_inputs
experiment_inputs = test_attacks.experiment_inputs


def node(script, payload):
    if not shutil.which("node"):
        pytest.skip("Node is unavailable")
    subprocess.run(
        ["node", "-e", script],
        input=json.dumps(payload),
        text=True,
        cwd=ROOT,
        check=True,
        capture_output=True,
        timeout=30,
    )


def test_transfer_rendering_languages_journey_and_escaping(transfer_inputs):
    report = run(transfer_inputs)
    node(
        """
const assert=require('node:assert/strict');
const fs=require('fs'), data=JSON.parse(fs.readFileSync(0,'utf8'));
const ui=require('./dashboard/web/transfer.js');
const journey=require('./dashboard/web/journey.js');
const locale=require('./dashboard/web/locale.js');
const html=ui.renderReport(data.report);
assert.ok(html.includes('Surrogate white-box') && html.includes('Black-box transfer'));
assert.ok(html.includes(data.report.identity.transfer_source.model_sha256));
assert.ok(html.includes('tabindex="0"'));
assert.ok(ui.renderReport(data.legacy).includes('Transfer results pending'));
const hostile=structuredClone(data.report);
hostile.identity.transfer_source.model_sha256='<img src=x onerror=alert(1)>';
assert.ok(!ui.renderReport(hostile).includes('<img'));
const mapped=ui.renderMappings(data.context,'ar');
assert.ok(mapped.includes(data.context.mappings[1].rationale_ar));
assert.ok(locale.translate('Threat context and transfer','ar').includes('نقل الهجوم'));
assert.ok(locale.translate('Black-box transfer','ar').includes('نقل الهجوم'));
assert.ok(locale.translate('Pending / unavailable','ar').includes('غير متاح'));
assert.equal(ui.ratio({numerator:0,denominator:0,rate:null}),'0/0 · Pending / unavailable');
const rows=journey.journeyRows(data.report);
const row=rows.find(r=>r.evidence_mode==='transfer');
const story=journey.renderCase(data.report,row,row.examples[0]);
assert.ok(story.includes('Source and target decisions'));
assert.ok(story.includes('Feature-space only'));
assert.ok(story.includes('not established'));
assert.equal(journey.cases(data.report).length,
 data.report.results.reduce((n,r)=>n+r.examples.length+r.transfer.examples.length,0));
""",
        {"report": report, "legacy": report_fixture(), "context": threat_context()},
    )


def test_transfer_loading_missing_partial_malformed_and_retry_states():
    node(
        """
const assert=require('node:assert/strict'), fs=require('fs');
const data=JSON.parse(fs.readFileSync(0,'utf8'));
(async()=>{
 for(const mode of ['ok','empty','offline','malformed','context-offline']) {
  const elements={};
  global.document={
   documentElement:{lang:'en'},addEventListener:()=>{},
   getElementById:id=>elements[id] ||= {value:'0',innerHTML:'',textContent:'',disabled:false}
  };
  global.fetch=async url=>{
   if(mode==='offline'||(mode==='context-offline'&&url.includes('context')))throw Error('down');
   return {ok:true,json:async()=>url.includes('context')?data.context:
    mode==='malformed'?{experiments:'invalid'}:
    {experiments:mode==='empty'?[]:[data.legacy],unavailable_reports:1,truncated:true}};
  };
  delete require.cache[require.resolve('./dashboard/web/transfer.js')];
  require('./dashboard/web/transfer.js');
  await new Promise(setImmediate);
  assert.equal(elements['transfer-refresh'].disabled,false);
  if(['offline','malformed'].includes(mode)){
   assert.ok(elements['transfer-state'].textContent.includes('Could not load'));
   assert.equal(elements['transfer-experiment'].disabled,true);
  } else if(mode==='empty'){
   assert.ok(elements['transfer-content'].innerHTML.includes('No measured results'));
  } else {
   assert.ok(elements['transfer-content'].innerHTML.includes('Transfer results pending'));
   assert.ok(elements['transfer-state'].textContent.includes('not all reports'));
  }
  if(mode==='context-offline')assert.ok(elements['transfer-mappings'].innerHTML.includes('unavailable'));
  assert.equal(typeof elements['transfer-refresh'].onclick,'function');
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
""",
        {"legacy": report_fixture(), "context": threat_context()},
    )


def test_transfer_page_is_static_readonly_with_shared_language_and_csp():
    with TestClient(create_app()) as client:
        response = client.get("/dashboard/transfer.html")
        assert response.status_code == 200
        assert "script-src 'self'" in response.headers["content-security-policy"]
        for asset in ("transfer.js", "transfer.css", "locale.js", "release.js"):
            assert client.get("/dashboard/" + asset).status_code == 200
        assert 'role="status"' in response.text and 'aria-live="polite"' in response.text
        assert "not authorized, not run" in response.text
        assert client.post("/v1/threat-context").status_code == 405
