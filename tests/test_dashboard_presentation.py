"""Presentation contracts; Node checks do not replace browser/viewport review."""

import re
import shutil
import subprocess
from html.parser import HTMLParser

import pytest
from src.config import ROOT

WEB = ROOT / "dashboard/web"


def _contrast(first, second):
    def luminance(value):
        channels = [int(value[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
        return sum(
            channel * weight
            for channel, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True)
        )

    values = sorted((luminance(first), luminance(second)))
    return (values[1] + 0.05) / (values[0] + 0.05)


def test_light_palette_tokens_and_contrast():
    css = (WEB / "theme.css").read_text()
    colors = dict(re.findall(r"(--[\w-]+):\s*(#[0-9a-fA-F]{6});", css))
    pairs = [
        ("--text-primary", "--bg-page", 7),
        ("--text-primary", "--bg-surface", 7),
        ("--text-primary", "--bg-subtle", 7),
        ("--text-primary", "--info-bg", 7),
        ("--text-primary", "--warning-bg", 7),
        ("--text-secondary", "--bg-surface", 7),
        ("--text-muted", "--bg-surface", 7),
        ("--link", "--bg-surface", 4.5),
        ("--link-visited", "--bg-surface", 4.5),
        ("--on-accent", "--link", 4.5),
        ("--success-fg", "--success-bg", 7),
        ("--warning-fg", "--warning-bg", 7),
        ("--error-fg", "--error-bg", 7),
        ("--info-fg", "--info-bg", 7),
        ("--focus", "--bg-surface", 3),
        ("--border-strong", "--bg-surface", 3),
        *((f"--chart-{index}", "--bg-surface", 3) for index in range(1, 7)),
    ]
    for foreground, background, minimum in pairs:
        assert _contrast(colors[foreground], colors[background]) >= minimum, (
            foreground,
            background,
        )
    assert "color-scheme: light" in css
    for name in ("styles.css", "journey.css", "attacks.css", "transfer.css"):
        assert not re.search(r"#[0-9a-fA-F]{3,8}\b", (WEB / name).read_text())


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


def test_research_status_is_consistent_and_filters_are_grouped():
    status = (
        "Exploratory, feature-space only · Real transfer pending · "
        "Frozen benchmark not yet accepted · Defenses planned"
    )
    for page in ("index", "attacks", "transfer", "research"):
        html = (WEB / f"{page}.html").read_text()
        assert (
            f'<div class="research-status"><strong>Research status</strong><span>{status}</span></div>'
            in html
        )
    attacks = (WEB / "attacks.html").read_text()
    assert '<fieldset class="attack-filters"><legend>Filter results</legend>' in attacks
    assert 'id="attack-reset" type="button" disabled>Reset filters</button>' in attacks
    styles = (WEB / "styles.css").read_text()
    assert ".content { max-width: 1200px;" in styles
    assert "line-height: 1.7" in styles


@pytest.mark.skipif(shutil.which("node") is None, reason="Optional Node unavailable")
def test_formal_arabic_status_copy_and_identifier_boundaries():
    script = r"""
const assert=require('node:assert/strict');
const {translate,isolate,copy}=require(process.argv[1]);
for(const number of ['1,000,000','22,500','92.18%','1/122','10⁻⁶']) {
  assert.equal(isolate(number),'\u2066'+number+'\u2069');
}
assert.equal(isolate('EMBER.'),'\u2066EMBER\u2069.');
assert.equal(isolate('0.'),'\u20660\u2069.');
assert.equal(isolate('frozen benchmark'),'\u2066frozen benchmark\u2069');
assert.equal(isolate('freeze gate'),'\u2066freeze gate\u2069');
assert.equal(isolate('transfer learning'),'\u2066transfer learning\u2069');
assert.equal(isolate('feature space'),'\u2066feature space\u2069');
assert.equal(isolate('adversarial examples'),'\u2066adversarial examples\u2069');
assert.equal(isolate('frozen model'),'\u2066frozen model\u2069');
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
for(const text of [
  'Research status',
  'Exploratory, feature-space only · Real transfer pending · Frozen benchmark not yet accepted · Defenses planned',
  'Filter results','Reset filters','Exploratory · feature space','Historical validation',
  'Gated · authentication and a verified frozen model required',
  'Recorded classification case','Feature-space modification',
  'Scroll the table horizontally to view all columns.',
  'MNIST accuracy by attack strength'
]) assert.match(translate(text,'ar'),/[\u0600-\u06ff]/);
for(const [en,ar] of copy) {
  assert.ok(en && ar);
  assert.ok(!/مفيش|علشان|الموديل|إزاي|التيم/.test(ar),ar);
}
assert.match(translate('Black-box transfer','ar'),/black-box · transfer/);
const statusArabic = translate('Exploratory, feature-space only · Real transfer pending · Frozen benchmark not yet accepted · Defenses planned','ar');
for(const pattern of [
  /استكشافي ضمن feature space فقط/,
  /transfer: القياس الفعلي قيد الانتظار/,
  /frozen benchmark: لم يُعتمد بعد/,
  /الدفاعات مخطَّط لها/
]) assert.match(statusArabic,pattern);
for(const avoided of [
  'فضاء الخصائص','نقل الهجوم','التقييم المرجعي المجمّد','عتبة التجميد',
  'وصول كامل','دون معرفة','مجموعة التقييم','مقياس التعديل','نموذج بديل'
]) assert.ok(!statusArabic.includes(avoided),avoided);
for(const [text,term,gloss] of [
  ['Recorded white-box results and available transfer evidence, with the limits of feature-space evaluation.','white-box','وصول كامل'],
  ['White-box target gradients. Transfer has not been measured for this case.','white-box','وصول كامل'],
  ['Shared training data and preprocessing are attacker knowledge assumptions, not a strict unknown-data black-box scenario.','black-box','دون معرفة'],
  ['Surrogate white-box','surrogate','نموذج بديل'],
  ['A selected case illustrates one outcome. Aggregate results describe the evaluated cohort under the specified model, sample selection and constraints; neither establishes a valid executable modification.','cohort','مجموعة التقييم'],
  ['One exact model, dataset, split, row subset and policy per snapshot. Norms stay separate.','norm','مقياس التعديل'],
  ['Perturbations:','perturbation','تعديل الخصائص'],
  ['Frozen evaluation model','frozen model','نموذج مجمّد'],
  ['Frozen baseline · feature prediction (Sprint 4)','frozen baseline','خط الأساس'],
  ['Feature-space only','feature space','فضاء الخصائص'],
  ['Adversarial resilience in malware detection','adversarial attacks','التضليلية'],
  ['An adversarial attack deliberately looks for an allowed change that makes the model answer incorrect. We replay the measured change below; no experiment runs in your browser.','adversarial attack','التضليلي']
]) {
  const arabic = translate(text,'ar');
  assert.ok(arabic.includes(term),text+' missing '+term);
  assert.ok(!arabic.includes(gloss),text+' still uses '+gloss);
}
assert.equal(translate('ASR','ar'),'ASR');
assert.equal(translate('Epsilon','ar'),'ε');
for(const [text,pattern] of [
  ['White-box and black-box results',/white-box/],
  ['Transfer results pending',/transfer/],
  ['Results for the evaluated cohort',/cohort/],
  ['Norm',/Norm/]
]) assert.match(translate(text,'ar'),pattern);
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
def test_attack_chart_uses_labeled_patterns_and_table_alternative():
    script = r"""
const assert=require('node:assert/strict');
const {curve,renderReport}=require(process.argv[1]);
const metrics={clean_accuracy:.9,attacked_accuracy:.8,clean_correct:9,attacked_correct:8,
  samples:10,successful_attacks:1,asr_denominator:9,attack_success_rate:1/9,
  mean_norms:{L0:1,L2:.1,Linf:.1}};
const row={attack:'FGSM',norm:'Linf',parameters:{epsilon:.1},metrics,projection:'each_step',
  library_version:'1',cross_check:{status:'not_run',reason:'not requested'}};
const report={identity:{dataset:'x',model_version:'x',split:'val',samples:10,
  seed:1,threshold:.5,model_sha256:'x',indices_sha256:'y',constraint_sha256:'z'},
  constraint:{status:'reviewed_feature_space',reviewer:'fixture'},results:[row]};
const chart=curve([row]);
assert.ok(chart.includes('series-swatch'));
assert.ok(chart.includes('exact values and counts are in the results table'));
const html=renderReport(report,'Linf','all');
assert.ok(html.includes('<caption>Clean versus attacked'));
assert.ok(html.includes('<th scope="col">'));
assert.ok(html.includes('does not establish a valid executable modification'));
"""
    result = subprocess.run(
        [shutil.which("node"), "-e", script, str(WEB / "attacks.js")],
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
