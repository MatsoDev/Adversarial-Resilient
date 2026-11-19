# Light-mode academic dashboard review

Date: 2026-11-19. Scope: the primary HTML/CSS/JavaScript dashboard, not the
legacy Streamlit app. This is a presentation update; it does not complete a
research milestone or change the API, prediction authorization, model freeze
gate, data, measurements, or experimental status.

## Inventory and design

The interface comprises the recorded-case overview, attack comparison,
threat/transfer, and models/data routes. Models/data contains five views:
overview, model performance, dataset explorer, methodology, and the separate
MNIST tooling demonstration. Copy is in HTML, JavaScript renderers and
`dashboard/web/locale.js`; recorded JSON and source documents retain their
original language. Comparison charts use Canvas and SVG, not a chart library.

The earlier dark presentation had several rhetorical headings, repetitive
panels, small supporting text and chart series identified primarily by color.
The revised presentation uses an off-white report background, white surfaces,
ink text, blue actions and visible non-color status indicators. Active
stylesheets use the shared custom properties in `theme.css`; no remote fonts,
assets or dependencies were added. The stack uses local system fonts for Latin
with Arabic-capable fallbacks in the Arabic setting, a 1200px content maximum,
18px base text and 1.5/1.7 Latin/Arabic line height.

The overview now defines adversarial examples and distinguishes a recorded
feature-space case from a live experiment. A project-reference status strip
states that results are exploratory and limited to feature space, real transfer
is pending, the frozen benchmark is not yet accepted, and defenses are planned.
It describes the **current reference evidence**,
not a live approval or the status of a newly selected report. Selected experiment
qualification and constraint-review status remain data-driven and separately
displayed. If the reference evidence changes, maintainers must update the status
strip and the underlying research documentation together.

Attack filters and the detailed results table use native disclosures. The
filter group has a visible legend, associated labels and an explicit reset
action; result updates announce through the existing live region. Chart series
have line patterns or bar hatching in addition to color; exact data is available
in labelled tables. The MNIST figure has an accompanying table and a
warning that historical Sprint 1 `attack_success_rate` fields represent overall
adversarial error, not the conditional ASR used in current experiments. This
clarification comes from [the development guide](development.md#run-the-art-demo),
not a recalculation of measured evidence.

## Arabic terminology

The UI uses Western numerals and keeps identifiers, JSON and hashes in their
source form. Ambiguous machine-learning and security terms stay in Latin script
in the Arabic UI. Each term carries a short Arabic gloss at its first explanatory
use; later labels and table headings use the English term alone. General prose
and unambiguous concepts remain translated, including “فضاء الخصائص”.

| English (retained) | Arabic gloss |
|---|---|
| white-box | وصول كامل إلى النموذج |
| black-box | دون معرفة داخلية بالهدف |
| transfer | نقل الهجوم |
| surrogate | نموذج بديل |
| cohort | مجموعة التقييم |
| norm | مقياس التعديل |
| perturbation | تعديل الخصائص |
| frozen benchmark | التقييم المرجعي المجمّد |
| freeze gate | عتبة التجميد |

The rest of the working glossary remains translated:

| English | Arabic |
|---|---|
| Adversarial example | مثال تضليلي |
| Feature space | فضاء الخصائص |
| Malware detector | كاشف البرمجيات الضارة |
| Attack success rate | معدّل نجاح الهجوم |
| Frozen baseline | خط الأساس المجمّد |
| Exploratory / pending / planned | استكشافي / قيد الانتظار / مخطّط |

The first explanatory use is page-aware. The shared status strip introduces
`transfer` and `frozen benchmark`; the transfer overview introduces `white-box`,
its black-box paragraph introduces `black-box`, and its results table and mapping
rationale introduce `surrogate`. The overview introduces `cohort`, the case
details introduce `norm`, and the readiness notes introduce `freeze gate`. The
attacks filter and metric definitions introduce `norm` and `perturbation`. The
browser review confirms these terms remain visible and directionally isolated at
narrow and wide widths.

This glossary and the final Arabic prose **have not been approved by a native
Arabic reviewer or supervisor**. Human review remains necessary.

## Local verification

- Focused Node/Python regressions cover light-palette contrast, absence of
  hard-coded color values in component stylesheets, chart pattern/table
  alternatives, bilingual status text, evidence provenance and prediction gates.
- The full `make lint coverage` suite was run in a clean detached worktree
  containing only the task diff. The source checkout contains the user's
  untracked brief in `docs/`; the documentation reachability test scans
  untracked Markdown and flags that document as unindexed. The brief was not
  moved, modified, linked to a nonexistent remote file, or committed. The final
  run passed with **629 passed, 6 skipped and 90% total coverage**.
- Cached Chromium with the local FastAPI service: all four routes in English
  and Arabic at **320×740, 390×844, 844×390, 1366×768 and 1920×1080 CSS px**;
  the five research views were also opened at each size and language.
  Document-level horizontal overflow was checked; wide tables and charts
  remain independently scrollable. The MNIST figure and data table were loaded
  from the recorded artifact. Screenshots are in
  `/tmp/opencode/arsm-light-review/`, outside the repository.
- At 390 and 1366 px the root text size was doubled to test text enlargement
  on each route in both languages. This is not a substitute for actual browser
  zoom testing. Language persistence and selection of the L2 filter across a
  language switch were checked. Keyboard Enter advanced two recorded-case
  stages and focused their headings; forced-colors emulation retained borders.
  Synthetic browser-only empty/offline states and the actual unconfigured
  prediction state were checked; no uncaught JavaScript exceptions were logged.
- Lighthouse snapshot audits in Chromium scored **1.0** for accessibility, best
  practices and SEO on the four default English route states in the final pass;
  the earlier bilingual pass also scored 1.0 before the final editorial changes.
  The favicon request now resolves to the local project logo. Automated checks
  do not establish accessibility compliance or cover every dynamic state.
- Computed contrast examples: primary text on page **17.02:1**, secondary text
  on white **10.63:1**, links on white **8.04:1**, warning **7.55:1**, error
  **7.27:1**, information **7.62:1**, control border on white **4.72:1**.
  Chart series against white range from **6.35:1 to 7.53:1**. Automated token
  tests cover the documented foreground/background combinations; actual
  projection and all rendered combinations require separate assessment.

## Outstanding checks and projector procedure

No physical mobile device, real projector, Firefox/Safari, screen reader,
complete keyboard walkthrough, actual browser zoom or native Arabic review was
available for this work. The in-app browser's screenshot operation could not
capture an invisible tab, so viewport screenshots used cached headless Chromium.

Before the presentation, display the actual overview, chart, table and warning
states in the real room with the intended ambient lighting. Check readability
from the back row, repeat with grayscale and a color-vision simulator, and
adjust contrast or weight if needed. Keep screenshots or a PDF of the key views
as a presentation fallback. Do not report this projector check as completed
until the team actually performs it.
