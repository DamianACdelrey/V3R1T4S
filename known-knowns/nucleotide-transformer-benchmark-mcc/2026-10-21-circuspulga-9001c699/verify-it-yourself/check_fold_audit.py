# Standalone checker (Python standard library only), written from the definition:
# for each histone task, for every pair of benchmark.csv entries with exactly 10 per-fold MCC values,
# p = fraction of the 1024 sign patterns s with |mean(s*d)| >= |mean(d)| (d = per-fold differences, two-sided exact sign-flip test).
# Checks object/fold_audit_histone.json against a recomputation from benchmark.csv (path as argv[1]; URL and sha256 in the-record-we-beat/record.md),
# and the claimed statement: best entry not significantly above the second (p >= 0.05) on the six named tasks.
import json, itertools, sys, os, csv, ast, hashlib
here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHA = 'a93c1e722f6b15312818903dc048207845598925889f415caaf61e3af7d60ca6'
csv_path = sys.argv[1]
if hashlib.sha256(open(csv_path, 'rb').read()).hexdigest() != SHA: print('benchmark.csv sha256 differs from record.md'); print('FAIL'); sys.exit(1)
obj = json.load(open(os.path.join(here, 'object', 'fold_audit_histone.json')))
signs = list(itertools.product([1, -1], repeat=10)); ok = True
def mean(v): return sum(v) / len(v)
by = {}
for r in csv.DictReader(open(csv_path, newline='')):
    if r['Dataset'] in obj['tasks']: by.setdefault(r['Dataset'], []).append(dict(task=r['Dataset'], model=r['Model'], mcc_folds=ast.literal_eval(r['MCC'])))
for task, rows in sorted(by.items()):
    rows = [r for r in rows if len(r['mcc_folds']) == 10]
    rows.sort(key=lambda r: -mean(r['mcc_folds']))
    got = {}
    for a, b in itertools.combinations(rows, 2):
        d = [x - y for x, y in zip(a['mcc_folds'], b['mcc_folds'])]; obs = abs(mean(d))
        p = sum(1 for s in signs if abs(mean([si * di for si, di in zip(s, d)])) >= obs - 1e-12) / 1024
        got[(a['model'], b['model'])] = (mean(d), p)
    o = obj['tasks'][task]; op = {(q['a'], q['b']): (q['diff'], q['p']) for q in o['pairs']}
    if set(op) != set(got): print('MISMATCH pairs', task); ok = False; continue
    for k, (dm, p) in got.items():
        if abs(op[k][0] - dm) > 1e-9 or abs(op[k][1] - p) > 1e-12: print('MISMATCH', task, k, op[k], (dm, p)); ok = False
    if rows[0]['model'] != o['best']: print('MISMATCH best', task); ok = False
    p12 = got[(rows[0]['model'], rows[1]['model'])][1]
    print('%-9s n=%2d best=%-28s second=%-28s gap=%.4f p=%.4f' % (task, len(rows), rows[0]['model'], rows[1]['model'],
          mean(rows[0]['mcc_folds']) - mean(rows[1]['mcc_folds']), p12))
    if task in ('H2AFZ', 'H3K36me3', 'H3K4me1', 'H3K4me3', 'H3K9me3', 'H4K20me1') and not p12 >= 0.05: print('CLAIM FAILS', task); ok = False
print('PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
