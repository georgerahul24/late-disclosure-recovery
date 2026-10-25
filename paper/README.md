# paper/

The LaTeX draft of the paper. Build it with `latexmk -pdf main.tex` (needs a TeX install).

- `main.tex`: the frame, introduction, related work and ethics.
- `sections/*.tex`: the benchmark, method, setup and limitations, written by hand.
- `sections/results.tex`: **generated** from `results/` (to be done: `scripts/make_tables.py`). Never type numbers by hand.
- `refs.bib`: only references verified in `papers.md` or `docs/clinical_sources.md`.

Writing style: plain, short sentences (George's rule). Every claim needs a citation or a pointer to a result file.
