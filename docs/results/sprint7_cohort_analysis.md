# Sprint 7 recorded EMBER cohort analysis

The [summary JSON](sprint7-cohort/cohort_summary.json) contains 21 configuration
results from the same 128 operating-validation rows.
[View the example figure](sprint7-cohort/cohort_example.png).

The analysis validated the source report and recorded its SHA-256 over sorted,
compact JSON so line endings do not affect the digest. It verified the original model and preprocessing
digests, validation files, operating partition and exact ordered cohort.
Clean inference on those rows recovered the before matrix. The recorded number
of formerly correct decisions turned wrong gives the error-flip count. The
number of repaired errors is after-correct minus before-correct plus error
flips. For binary decisions, these are the only two kinds of flips.
The archived case records accounted for every flip in all 21 configurations.
The tool leaves the after matrix unavailable if any flips cannot be accounted
for.

In the FGSM example at ε = 0.05, rows are actual class and columns are predicted
class, both in benign, malicious order. The before matrix is
`[[46, 0], [6, 76]]` and the after matrix is `[[46, 0], [7, 75]]`.
The only changed decision was one additional missed malicious row.

The recorded policy allows one coordinate to vary. Each row therefore has
L0 equal to either 0 or 1 at the report's tolerance of 10⁻⁶. Multiplying the
recorded mean by the row count gives exactly the number of rows at L0 = 1.
For the example, the counts are 43 at zero and 85 at one. This describes how
many coordinates exceeded the tolerance. Positive L2 and L∞ averages do not
determine the distribution of change sizes.

To reproduce with the original trusted local bundle and processed validation
data, run:

```powershell
.\.venv\Scripts\python.exe scripts/analyze_recorded_cohort.py --output-dir docs/results/sprint7-cohort
```

The tool runs clean inference and reads archived outcomes. The official test
split, newer baseline candidate and original experiment metrics are unchanged.
