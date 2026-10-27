# REPRODUCE skeptic: nucleotide-transformer-benchmark-mcc (claim p3, fold-variance audit of the histone tasks)
context: subagent (fresh knowledgeWork context, given only the claim folder (now this package) and the kit RUN.md step-6 REPRODUCE instruction)
date: 2026-10-21 (Europe/Madrid, UTC+2), box CPU only, 1 thread per process, at most 6 processes; the user's PC/GPU was not used.

## Definition checked (quoted from README.md and how-we-built-it/PREREG.md)
- "exact paired sign-flip tests over the 10 per-fold MCC values" (PREREG lens A: "every model pair: exact paired sign-flip test over 10 folds (1024 patterns), two-sided"; PREREG v2: "rows without exactly 10 folds excluded and listed").
- "SE_test = bootstrap sd (1000) of MCC of the CNN fold-0 test predictions"; "meaningful only if (i) paired sign-flip p < 0.05 over folds AND (ii) |gap| > 2 x SE_test".
- MCC = (TP*TN - FP*FN) / sqrt((TP+FP)(TP+FN)(TN+FP)(TN+FN)), predictions = score > 0.5.

## Own checkers (written from the definition before reading the author's code)
- reviewer scratch script my_signflip.py on benchmark.csv (the-record-we-beat/record.md) (sha256 a93c1e72...0ca6, matches README.md): best vs second has p >= 0.05 on exactly H2AFZ (0.281), H3K36me3 (0.314), H3K4me1 (0.615), H3K4me3 (0.494), H3K9me3 (0.451), H4K20me1 (0.996); p < 0.05 on H3K27ac, H3K27me3, H3K4me2, H3K9ac. 6 tasks, as claimed. Per-task counts of pairs with p < 0.05 (72, 83, 74, 87, 79, 86, 76, 92, 58, 75) match the CNN threshold output (not shipped). The same 4 HyenaDNA rows with 9/12/13/14 folds are excluded. Best, second, gap and p match object/fold_audit_histone.json (0 mismatches; the reviewer checked all 18 tasks of the run's full audit, whose 10 histone tasks are this object).
- reviewer scratch script my_cnn_check.py: all 100 CNN model outputs (<task>__f<k>, not shipped) are present (done.json, model.pt, score_test.npy). I recomputed every per-fold test MCC from score_test.npy against the labels of the HF test split. The labels come from InstaDeepAI/nucleotide_transformer_downstream_tasks_revised at rev 851f9946252e90c665cdb3cc3eedb78f1f26197c, and all 20 parquet files pass sha256 against the run's HF parquet sha256 list (not shipped). Result: 0 mismatches against done.json test_mcc and the CNN null output NULLS.json (not shipped) fold_mcc (tolerance 1e-12). Also checked: n_test values, params 238722, seed = fold, test_deterministic true. the CNN run log (not shipped) has exactly 100 distinct TEST_READ lines and 100 DONE lines (one test read per model).
- reviewer scratch script my_threshold_robust.py uses 20 independent bootstrap seeds of 1000 resamples each. SE_test spans 0.0146-0.0340, so the threshold is about 0.029-0.068. Best vs second is meaningful only on H3K4me2 under every seed: gap 0.0482 against a threshold of 0.035-0.039. On every histone task, 0.02 stays below the smallest threshold. The conclusions do not depend on the bootstrap RNG.

## Author code, run as given
- sha256: how-we-built-it/nt.py 7503acd1...6bd9e1c and how-we-built-it/fold_audit_v2.py 2de549f3...613c8772 both equal PREREG / PREREG v2. how-we-built-it/threshold_apply.py (ec3f27ec...42906f5) has no hash in PREREG; I read it and it applies the stated rule literally.
- `python how-we-built-it/fold_audit_v2.py benchmark.csv fold_audit_all_tasks.json` gives output whose 10 histone tasks have the same pairs, diffs and p-values as object/fold_audit_histone.json.
- `python how-we-built-it/nt.py nulls` (output dir = copy of the CNN outputs, same call order) gives a NULLS.json equal value-for-value to the CNN null output NULLS.json (not shipped). The only byte difference is CRLF vs LF line endings. Then `python how-we-built-it/threshold_apply.py` gives output byte-identical to the CNN threshold output (not shipped). SE_test 0.0151-0.0331 and threshold 0.0302-0.0662 are exactly as claimed.

## Determinism / retraining (CPU)
- how-we-built-it/nt.py trains on CUDA only. I made a CPU copy (reviewer's scratch copy, not shipped) that changes only dev = 'cpu', set_num_threads(1) and the output dir.
- I trained H3K4me3 fold 0 twice for the full 25 epochs, independently. Weights (all tensors torch.equal), score_test.npy (byte-identical) and done.json (all fields except train_s) are identical: deterministic.
- 1-epoch twin runs were also identical.
- CPU retraining cannot match the saved GPU weights bit for bit: the RNG stream comes from a CUDA generator and the arithmetic differs. Retrained folds 0-3 give test MCC 0.536 / 0.593 / 0.562 / 0.557 (mean 0.562). The saved GPU models give 0.560 / 0.562 / 0.570 / 0.562 (mean 0.563). Same distribution.
- I loaded the saved model.pt files on CPU for fold 0 of all 10 tasks and folds 1-5 of H3K4me3. CPU predictions differ from score_test.npy by up to 2e-3 (0-2 label flips per model; H3K9ac f0 MCC 0.4410 becomes 0.4374).

## Findings (do not change the claimed values; for the gate)
1. Precision label. PREREG says "fp32 training and inference", but the saved GPU scores match a CPU emulation of TF32 matmul/conv (reviewer's scratch check, not shipped). Under that emulation the mean |diff| falls about 20x and there are 0 label flips, so the GPU run very likely used PyTorch's default cuDNN TF32. The claim's numbers come from the saved scores, which reproduce exactly, and the conclusions survive the CPU-fp32 differences.
2. The claim folder does not ship the parquet splits that the CNN lens needs. I fetched them from the pinned public HF revision and verified every sha256 (then deleted my copy). Data copies were not included, as RUN.md step 6 asks.
3. GPU bitwise retraining was not checked: optional, and the user's PC was excluded. Training determinism is confirmed on CPU only.
4. Table-access audit: no user-agent, cookie, retry or 403/429 code in how-we-built-it/.

Every claimed property and value was recomputed from the saved files with my own checkers and with the author's code. There is no mismatch, no missing object and no non-determinism.
pass: true
