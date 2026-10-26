# null_test: label permutation of each CNN model's test predictions (100 models x 1000 controls, MCC); sign-flip null (1024 exact patterns) per benchmark.csv pair in lens A
controls: 1000
best_control: 0.1443
real: 0.2169
real_beats_all_controls: yes
command: python how-we-built-it/nt.py nulls (GPU machine; CNN outputs not shipped in this package); lens A: python how-we-built-it/fold_audit_v2.py benchmark.csv fold_audit_all_tasks.json
note: best_control = max permuted MCC over all 100 models (H3K4me3); real = min real fold MCC over all 100 models (H3K9me3 fold 4). Every model beats all of its 1000 controls.
