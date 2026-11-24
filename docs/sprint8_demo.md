# Sprint 8 | Phase 1 walkthrough

Use the Sprint 8 branch and the existing environment. From the repository
root, start the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

1. Open <http://localhost:8000/dashboard/>, verify **v0.8.0 · Sprint 08**, and
   find **Phase 1 demonstration**.
   Open the historical dataset and model views to explain EMBER features,
   the validation partition, and the frozen-model gate.
2. Replay the fixed successful case. On validation row 50020 the reference
   class and original prediction are malicious. Step through the recorded
   feature change to the benign prediction.
3. Replay the fixed unsuccessful case. On validation row 1614 the benign
   prediction stays correct. Both replays come from the same FGSM ε = 0.05
   snapshot, seed 42, and are illustrations from the 128-row cohort.
4. Open Attack comparison, then the report and CSV from the Phase 1 section.
   Compare 122/128 before and 121/128 after for the example. Use the
   [cohort figure](results/sprint7-cohort/cohort_example.png) to show the
   class counts. Mention the pending transfer and Security review.
5. In Models and data, show the feature upload, history and report controls.
   For a fresh playback checkout show their gated state. With an authorized,
   qualifying local frozen bundle, demonstrate a numeric JSON submission
   and compare the saved score and row order to the CSV after restart.

Playback, the report and the cohort export use committed artifacts and work
without local weights. Record the replay outcomes and commit in the team's
internal review before marking the independent reproduction complete.
