#!/usr/bin/env bash
# Re-runs the whole scaffold from the raw inputs and checks it. Usage: ./run_all.sh [--no-exec]   (--no-exec skips executing the notebook)
# PY: interpreter (default ../.venv/bin/python; in the shared repo export PY=python3 or a venv with requirements.txt installed).
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-../.venv/bin/python}
[ -x "$PY" ] || command -v "$PY" >/dev/null 2>&1 || { echo "interpreter not found: $PY" >&2; exit 1; }
# stale-output guard: anything a later step reads must be produced by THIS run or be absent
rm -f results/r_fe_coefficients.csv results/figures/fig_map.png results/notebook_check.json
for s in 00_assemble_panel 01_prep_frame 02_fe_model 02b_event_study 02c_spec_curve 03_loco 04_residuals 05_figures; do echo "== $s"; "$PY" "$s.py"; done
# the R replica was retired on the 10 Sep call (v2.0): the estimator-agreement check in 06_report.py replaces it
for s in 08_concern_score 09_dml_sidebar; do echo "== $s (sidebar)"; "$PY" "$s.py" || echo "sidebar $s FAILED (non-fatal)" >&2; done
echo "== 06_report"; "$PY" 06_report.py
echo "== 07_make_notebook"; "$PY" 07_make_notebook.py "$@"
if [ "${SKIP_TESTS:-0}" != "1" ]; then echo "== tests"; "$PY" -m pytest tests -q; fi
PANEL_DIR=$("$PY" -c 'import config; print(config.PANEL_DIR)')
echo "== done: panel in $PANEL_DIR, data version $(cat "$PANEL_DIR/data_version.txt")"
