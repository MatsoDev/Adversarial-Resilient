# Academic dashboard presentation review

Date: 2026-11-18. Scope: `dashboard/web/`, not legacy Streamlit.
This is presentation work, not completion of a research milestone.

## Audit and implementation

All four routes and the five views within `research.html` were reviewed in
English and Arabic. The audit found overlapping cyan/dark palettes, inconsistent
primary navigation, Egyptian colloquial copy, untranslated dynamic/chart/error
messages, non-localized prediction status blocks, and direction-specific layout
rules. Translating document options also risked changing their API identifiers.

The implementation keeps plain HTML/CSS/JavaScript, routes, same-origin requests,
language persistence and the v0.6.0/Sprint 06 research identity:

- **Academic identity:** ink `#101a22`, slate panels `#182630`, pale foreground
  `#edf3f3`, restrained teal `#8ed8ca`, blue links and amber qualifications.
  Color distinguishes decisions and qualifications, alongside textual labels.
  Shared spacing, borders, navigation, tables, cards, forms and focus styling
  replace page-specific visual identities.
- **Typography:** Segoe UI/Arial for Latin and Tahoma-first for Arabic, with
  system fallbacks, more generous Arabic line height and no Arabic letter spacing.
  These are installed-font preferences, not redistributed fonts. No fonts,
  assets, packages or third-party tracking requests were added; the existing logo
  is retained without the former color inversion.
- **Research hierarchy:** an opening research question, train/challenge/improve
  explanation, explicit maturity statement, guided measured case and optional
  technical detail. Metric definitions support the research views. Exploratory
  results, missing transfer evidence, M1/frozen-benchmark blockers, pending
  technical review and future defenses remain distinct.
- **Bilingual copy:** concise English framing and formal Modern Standard Arabic,
  labelled **العربية** rather than **مصري**. Navigation, chart labels/tooltips,
  options, status messages, accessibility labels and prediction validation errors
  share the catalog in `locale.js`.
- **Arabic layout:** logical sidebar/main offsets and borders, correct `lang/dir`,
  directional stage arrows, isolated Latin identifiers/numbers/ratios and
  separately scrollable wide tables/charts. Keyboard users get a skip link,
  visible focus, current-view semantics and labelled scroll regions.
- **Prediction states:** explicit loading, disabled and localized failure states;
  invalid JSON has a stable translatable message. Tokens/rows are still not
  persisted; authentication, request identities and freeze gates are unchanged.

Raw JSON, parameter keys, hashes, model identities and original source documents
are retained as technical evidence, not translated. The methodology view explains
that source documents remain in their recorded language. Prose in status `<pre>`
blocks is explicitly opted into translation; successful JSON responses are not.
Option values are fixed before labels are localized.

## Presentation route

1. **AI journey:** research question, methodology, maturity, recorded three-step case.
2. **Attack comparison:** same-cohort accuracy/ASR counts, budgets and provenance.
3. **Threat context and transfer:** pending transfer versus measured white-box
   evidence, four realism questions and proposed—not approved—mappings.
4. **Models and data:** historical comparisons, data composition, methodology
   documents and the clearly separate MNIST tooling demonstration.

Do not describe the 128-row exploration as a full-data benchmark. A changed
feature-space decision does not establish a valid executable modification.

## Verification actually performed

- `make check` and `make lint coverage`: **625 passed, 6 skipped; 90% combined Python line/branch
  coverage**. Six skips are optional real-data/CleverHans cases, not UI failures.
  Existing third-party Matplotlib/Pyparsing deprecation warnings remain.
- Node-backed regressions cover consistent navigation/local assets, formal Arabic
  status copy, technical-identifier boundaries, measured-case rendering and
  prediction success, unavailable/unauthorized states and invalid inputs.
  Python coverage does not measure JavaScript line coverage.
  A final screenshot review caught reversed comma-group ordering in Arabic
  counts; whole-number directional isolation now has explicit regression cases
  for `1,000,000`, `22,500`, percentages, ratios and measurement tolerances.
- JavaScript syntax checks, `git diff --check` and task-file pre-commit hooks
  passed, including private-key and large-file guards.
- Cached Chromium, real local FastAPI on loopback: all four routes in both
  languages at **390, 760 and 1440 CSS px** (24 route/language/width combinations),
  plus all five research views in each combination for that route.
  Dataset switching to CICIDS and methodology switching to `sprint4` worked in
  both languages without changing endpoint values. No document-level horizontal
  overflow was detected; wide evidence regions scroll independently.
- Native Enter activation advanced the journey and focused the next `h3`;
  its focus outline was visible. Language choice persisted across routes.
  Representative desktop/mobile screenshots and an Arabic result-step screenshot
  were captured and inspected. Session-local files are under
  `/tmp/opencode/arsm-review/`; they are not repository assets.
- The real unconfigured prediction request remained disabled after its localized
  unavailable response. Browser-only empty/network-failure fixtures exercised
  journey/attack states and transfer error handling; they did not create reports
  or publish synthetic scores. No uncaught JavaScript exceptions were recorded.
- Computed core text contrast ratios: body **15.69:1**, secondary panel text
  **8.77:1**, links **9.30:1**, teal on slate **7.99:1**. These are specific token
  checks, not a complete accessibility certification.

The built-in UI has one dark theme and no theme selector; that behavior is
preserved. No alternate theme was invented or claimed tested.

## Limits

The in-app browser exposed DOM/accessibility inspection but its screenshot
operation reported an invisible-tab error. Screenshots and viewport/keyboard
checks above therefore used the already cached headless Chromium through its
loopback DevTools connection, without downloads or weakened browser sandboxing.
They are desktop-browser viewport emulation, not physical mobile-device,
screen-reader, Safari/Firefox or exhaustive keyboard testing.

No training, data/model downloads, experiment reruns, real authorized prediction,
production access or deployment was performed. No local Docker rebuild/security
scan was needed for this frontend-only change. Hosted CI status is reported in
the delivery message, not inferred from local checks. Existing CI builds/scans
the image but does not deploy.
