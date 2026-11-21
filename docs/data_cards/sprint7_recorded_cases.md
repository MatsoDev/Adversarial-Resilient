# Sprint 7 recorded EMBER cases

The [recorded evaluation](../results/attack_reference.json) contains 57 case
records across 21 configurations from a 128-row operating-validation cohort.
A single original row can appear under several configurations. Cases were
selected for explanation, so their counts cannot estimate attack success or
classifier performance. Use the full cohort counts in Attack comparison for
evaluation.

The dashboard exports the filtered case index as CSV. Each reference identifies
the recorded run, method, configuration, evaluation mode, and split row. The
export includes the dataset, split, seed, model, manifest and policy digests,
known class and both recorded predictions. Class 0 is benign and class 1 is
malicious. The original EMBER source and its data limitations are documented in
the [EMBER data card](ember2018.md).

The source model is a development candidate. The results describe numeric
features and do not establish executable validity or benchmark acceptance.
The case index is a compact research artifact for replay and analysis.
It contains no feature vectors or model weights.

The recorded aggregate provides accuracy, attack success counts, and mean
norms. Full-cohort confusion matrices and perturbation histograms require
full-cohort class-pair counts and per-row distances. The selected cases cannot
be used to reconstruct those distributions.
