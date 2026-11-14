"""Pure explorer checks: exact snapshot selection, norms, curve series and escaping."""

import shutil
import subprocess

import pytest
from src.config import ROOT


@pytest.mark.skipif(shutil.which("node") is None, reason="Optional Node runtime unavailable")
def test_attack_explorer_filters_and_chart_values():
    script = r"""
const assert = require('node:assert/strict');
const ui = require(process.argv[1]);
const metrics = {samples:10,clean_correct:8,attacked_correct:5,asr_denominator:8,
  clean_accuracy:.8,attacked_accuracy:.5,successful_attacks:3,attack_success_rate:.375,
  mean_norms:{L0:2,L2:.3,Linf:.2}};
const row = {attack:'FGSM',norm:'Linf',parameters:{epsilon:.1,random_start:false},metrics,
  library:'ART',library_version:'1.20.1',projection:'each_step',
  cross_check:{status:'not_run',reason:'<script>unsafe</script>'}};
const pgd = {...row,attack:'PGD',parameters:{epsilon:.2,step_size:.01,iterations:20}};
const cw = {...row,attack:'CW-L2',norm:'L2',parameters:{iterations:100,confidence:0},projection:'after_generation'};
const report = {identity:{dataset:'ember2018',model_version:'baseline_v1',split:'test',samples:10,
  model_sha256:'a'.repeat(64),indices_sha256:'b'.repeat(64),constraint_sha256:'c'.repeat(64),seed:42,threshold:.5},
  constraint:{status:'reviewed_feature_space',reviewer:'fixture'},results:[row,pgd,cw]};
assert.deepEqual(ui.selectRows(report,'Linf','all'),[row,pgd]);
assert.deepEqual(ui.selectRows(report,'L2','CW-L2'),[cw]);
assert.deepEqual(ui.selectRows(report,'Linf','CW-L2'),[]);
assert.notEqual(ui.seriesKey(pgd),ui.seriesKey({...pgd,parameters:{...pgd.parameters,iterations:10}}));
const html=ui.renderReport(report,'Linf','all');
assert.match(html,/50.00%/); assert.match(html,/37.50%/); assert.match(html,/3\/8/);
assert.match(html,/CleverHans: Not run/); assert.match(html,/&lt;script&gt;/);
assert.ok(!html.includes('<script>unsafe'));
assert.ok(!html.includes('<strong>CW-L2</strong>'));
const cwHtml=ui.renderReport(report,'L2','all');
assert.match(cwHtml,/No epsilon curve applies/); assert.ok(!cwHtml.includes('<svg'));
const chart=ui.curve([row,pgd]);
assert.match(chart,/y1="83.99999999999997"|y1="84"/);
assert.match(chart,/cy="150"/); // 50% attacked accuracy from the stored metric.
const other={...report,identity:{...report.identity,indices_sha256:'d'.repeat(64)},results:[]};
assert.ok(!ui.renderReport(other,'Linf','all').includes('50.00%'));
"""
    result = subprocess.run(
        [shutil.which("node"), "-e", script, str(ROOT / "dashboard/web/attacks.js")],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
