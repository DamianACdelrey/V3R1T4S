# 🗺 Known unknowns

The hills nobody has climbed yet: **288 open problems in 18 categories**. Each page says what the problem is, what counts as a win, how a win is checked, where to check it is still open, ideas to start from, and the traps that produced false wins before.

Pick one, then tell your agent:

```
set up V3R1T4S: https://github.com/elder-plinius/V3R1T4S and hunt known-unknowns/<category>/<problem>.md
```

Or don't pick: your agent can roam anywhere, as long as a stranger's computer can check the answer.

| Category | Open | What's in it |
|---|---|---|
| 🧬 [Disease research](disease-research/README.md) | 51 | Cancer, rare and neglected diseases, antimicrobial resistance and outbreaks: public data, public scorers, computational claims only. |
| 🦠 [Biology](biology/README.md) | 29 | Protein, DNA and evolution benchmarks and record tables with mechanical checkers. |
| ⚛️ [Physics](physics/README.md) | 27 | Statistical mechanics, lattice models, quantum information and materials: exact counts, certified bounds, constants to record precision and public leaderboards. |
| 🔢 [Number hunts](number-hunts/README.md) | 19 | Certified bounds, exact searches and explicit solutions in number theory and computability. |
| ⚪ [Packings and physics](packings-physics/README.md) | 19 | Circle, sphere and point configurations and energy minima vs live tables. |
| 📊 [Record tables](record-tables/README.md) | 18 | Codes, designs, packings and constructions measured against public tables. |
| 🌍 [Earth and sky](earth-and-sky/README.md) | 18 | Missed events in open geophysical and space archives, checked against live catalogs. |
| 🔐 [Unbroken ciphers](unbroken-ciphers/README.md) | 17 | Historical and challenge ciphers nobody has read yet. |
| 📜 [Undeciphered scripts](undeciphered-scripts/README.md) | 16 | Writing systems and corpora nobody can read; wins are frozen, checkable predictions, never interpretations. |
| 🕸️ [Graphs, games and automata](graphs-games-automata/README.md) | 14 | Graph records, puzzles, tilings and cellular automata. |
| ✏️ [Erdős problems and proofs](erdos-and-proofs/README.md) | 13 | Erdős problems and relatives: counterexamples, small cases, machine-checked proofs. |
| 💊 [Drug discovery](drug-discovery/README.md) | 12 | Molecular property, binding, docking and design leaderboards scored on official splits. |
| 🚚 [Optimization benchmarks](optimization-benchmarks/README.md) | 9 | Best-known solutions on public routing, scheduling and MIP benchmark libraries. |
| 🔭 [Sky archives](sky-archives/README.md) | 7 | New vetted candidates in public astronomy archives (never 'a planet', only 'a candidate'). |
| ⚡ [Algorithms](algorithms/README.md) | 6 | Fast matrix multiplication schemes and other algorithmic records. |
| 🛡️ [ML robustness](ml-robustness/README.md) | 5 | Stronger attacks and soundness counterexamples on public, locally run benchmark models. |
| 🏺 [Ancient texts and fragments](ancient-texts/README.md) | 4 | Unidentified papyri, tablet fragments, lacunae and sign detection, scored against held-out data. |
| 🌋 [Herculaneum scrolls](herculaneum-scrolls/README.md) | 4 | Ink detection and surface segmentation on the public Vesuvius Challenge data. |

Tractability, compute and status dates are guesses from the day each page was written; the status page linked on each problem is the only authority. Every page is generated from [`bank/targets.json`](../bank/targets.json): `python3 bank/build_known_unknowns.py`.
