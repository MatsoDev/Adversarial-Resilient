# Reading list (Sprint 1 — foundations)

> Rule: no fake URLs. Search by title unless a URL is verified.

1. **Explaining and Harnessing Adversarial Examples** — Goodfellow, Shlens, Szegedy (2015).
   Why: introduces FGSM and the linearity hypothesis; basis for all evasion work.
2. **Towards Deep Learning Models Resistant to Adversarial Attacks** — Madry et al. (2018).
   Why: formalizes PGD + adversarial training (min-max); our hardening baseline.
3. **Towards Evaluating the Robustness of Neural Networks** — Carlini & Wagner (2017).
   Why: C&W L2/L0/Linf attacks; the strong white-box benchmark we reproduce on MNIST.
4. **Adversarial Robustness Toolbox (ART) documentation** — IBM (maintained).
   Why: the exact `PyTorchClassifier` + `FastGradientMethod`/`ProjectedGradientDescent`/`CarliniL2Method` API we use.
5. **EMBER: An Open Dataset for Training Static PE Malware Machine Learning Models** — Anderson & Roth (2018).
   Why: our primary dataset; read for features, splits, and baseline LightGBM results.
6. **Adversarial Examples for Malware Detection** — Grosse et al., ESORICS 2017.
   Why: first feature-space (Android/DREBIN) malware evasion; motivates
   functionality-preserving constraints. (Title corrected in the pre-merge
   audit; the earlier title here was wrong.)
7. **Distillation as a Defense to Adversarial Perturbations against Deep Neural Networks** — Papernot et al. (2016).
   Why: defensive distillation; Sprint 10 defense candidate (read with skepticism — later broken by C&W).
8. **Troubleshooting an Intrusion Detection Dataset: the CICIDS2017 Case Study** — Engelen et al. (2021).
   Why: documents labeling errors/duplicates in CICIDS2017; read before
   trusting any network-track numbers (Sprint 2).
