"""Presentation contracts; Node checks do not replace browser/viewport review."""

import shutil
import subprocess
from html.parser import HTMLParser

import pytest
from src.config import ROOT

WEB = ROOT / "dashboard/web"


class NavigationParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.primary = False
        self.links = []
        self.assets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "nav":
            self.primary = attrs.get("aria-label") == "Main navigation"
        if tag == "a" and self.primary:
            self.links.append(attrs["href"])
        if tag in {"script", "link"}:
            self.assets.append(attrs.get("src", attrs.get("href", "")))

    def handle_endtag(self, tag):
        if tag == "nav":
            self.primary = False


@pytest.mark.parametrize("page", ["index", "attacks", "transfer", "research"])
def test_primary_navigation_and_local_assets_are_consistent(page):
    parser = NavigationParser()
    parser.feed((WEB / f"{page}.html").read_text())
    assert parser.links == ["index.html", "attacks.html", "transfer.html", "research.html"]
    assert parser.assets.index("theme.css") > parser.assets.index("styles.css")
    if page == "index":
        assert parser.assets.index("theme.css") > parser.assets.index("journey.css")
    assert all(not asset.startswith(("http:", "https:", "//")) for asset in parser.assets)


@pytest.mark.skipif(shutil.which("node") is None, reason="Optional Node unavailable")
def test_formal_arabic_status_copy_and_identifier_boundaries():
    script = r"""
const assert=require('node:assert/strict');
const {translate,isolate,copy}=require(process.argv[1]);
for(const number of ['1,000,000','22,500','92.18%','1/122','10⁻⁶']) {
  assert.equal(isolate(number),'\u2066'+number+'\u2069');
}
for(const text of ['sprint4_candidate','step_size','random_start','MODELXYZ',
                  'a1fb1499fc5b','92.18% / 1/122 / 22,500']) {
  assert.equal(translate(text,'ar'),text);
}
for(const text of ['Access denied. Check the prediction token.',
                  'Load a verified frozen baseline first.',
                  'Invalid JSON. Enter an array of numeric rows.',
                  'Expected 1–32 finite numeric rows, each with exactly 2381 features.',
                  'Scrollable evidence table','Interface language',
                  'Grouped comparison of accuracy, F1 and AUC; exact values in the model table.']) {
  assert.match(translate(text,'ar'),/[\u0600-\u06ff]/);
  assert.notEqual(translate(text,'ar'),text);
  assert.equal(translate(translate(text,'ar'),'en'),text);
}
for(const [en,ar] of copy) {
  assert.ok(en && ar);
  assert.ok(!/مفيش|علشان|الموديل|إزاي|التيم/.test(ar),ar);
}
assert.match(translate('Black-box transfer','ar'),/نقل الهجوم/);
"""
    result = subprocess.run(
        [shutil.which("node"), "-e", script, str(WEB / "locale.js")],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(shutil.which("node") is None, reason="Optional Node unavailable")
def test_prediction_messages_remain_localizable_and_gates_remain_closed():
    script = r"""
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const elements=new Map();
const element=id=>{
  if(!elements.has(id))elements.set(id,{value:'',disabled:false,textContent:'',attributes:new Set(),
    toggleAttribute(name,on){on?this.attributes.add(name):this.attributes.delete(name)}});
  return elements.get(id);
};
let status=401,calls=[];
const context={document:{getElementById:element},AbortController,setTimeout,clearTimeout,
  fetch:async (path,options)=>{
    calls.push({path,options});
    return {ok:status===200,status,json:async()=>({model_version:'fixture',
      preprocessing_sha256:'fixture-preprocessing',feature_schema_sha256:'fixture-schema'})};
  }};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),context);
(async()=>{
  element('prediction-token').value='synthetic-test-token';
  for(const code of [401,503]) {
    status=code;await element('baseline-load').onclick();
    assert.equal(element('prediction-submit').disabled,true);
    assert.equal(element('baseline-load').disabled,false);
    assert.ok(element('baseline-info').attributes.has('data-ui-copy'));
  }
  status=200;await element('baseline-load').onclick();
  assert.equal(element('prediction-submit').disabled,false);
  assert.ok(!element('baseline-info').attributes.has('data-ui-copy'));
  const before=calls.length;
  for(const [input,message] of [['not JSON','Invalid JSON.'],['[]','Expected 1–32'],
       [JSON.stringify([[null]]),'Expected 1–32']]) {
    element('prediction-rows').value=input;await element('prediction-submit').onclick();
    assert.ok(element('prediction-result').textContent.startsWith(message));
    assert.ok(element('prediction-result').attributes.has('data-ui-copy'));
    assert.equal(calls.length,before);
  }
  assert.equal(calls[0].options.headers.Authorization,'Bearer synthetic-test-token');
  assert.equal(calls[0].options.credentials,'omit');
  assert.equal(calls[0].options.redirect,'error');
})().catch(error=>{console.error(error);process.exitCode=1});
"""
    result = subprocess.run(
        [shutil.which("node"), "-e", script, str(WEB / "prediction.js")],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    html = (WEB / "research.html").read_text()
    assert 'id="baseline-info" data-ui-copy role="status"' in html
    assert 'id="prediction-result" data-ui-copy role="status"' in html
