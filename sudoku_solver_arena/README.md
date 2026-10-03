# Sudoku Solver Arena

Interactive Sudoku solver that accepts puzzles, validates entries, and visualizes
backtracking step by step. Core algorithms: **Backtracking, Constraint Checking**.

## Contents
- `solver.py`  - algorithm core (parsing, validation, traced backtracking, replay)
- `app.py`     - Streamlit launcher that shows the redesigned UI (`web/index.html`)
- `app_classic.py` - original Python-solver Streamlit app (visualizer + algorithm comparison)
- `web/index.html` - standalone HTML/CSS/JS version (no install; just open in a browser). Redesigned: colourful UI, dark mode, separate Custom puzzle panel, step-by-step player and comparison tab
- `tests/`     - unit tests (`python -m unittest discover -s tests`)

## Run
    pip install -r requirements.txt
    streamlit run app.py            # new UI
    streamlit run app_classic.py    # original Streamlit UI

## Algorithms
1. **Plain backtracking** - first empty cell (row-major); try 1-9; check row/column/box
   constraints before every placement; undo the placement when no digit leads to a solution.
2. **Backtracking + MRV** - same, but always branches on the empty cell with the fewest legal
   candidates; a cell with zero candidates is a dead end detected immediately.

## Features
- Input via sample puzzles, pasted text (0 or . = blank), or an editable 9x9 grid
- Validation: duplicate digits in a row/column/box are highlighted in red; unsolvable puzzles reported
- Step-by-step viewer: slider, prev/next, play; each step shows the cell, legal candidates,
  depth, and running placement/backtrack counts (yellow = placed, orange = backtracked)
- Comparison tab: placements, backtracks, constraint checks and time for both algorithms
- Search limit of 500,000 placements guards against runaway searches; the "Hard" sample
  intentionally exceeds it for plain backtracking but MRV solves it in 718 placements

## Search limit & extreme puzzles
- The web version uses a fast, time-sliced solver (progress bar + Cancel) with a selectable search limit
  (500K / 10M / 100M / 1B placements). At the 100M default, plain backtracking solves the "Hard" sample
  (~9.7M placements) and the 17-clue "brute-force breaker" (~69M placements) in a few seconds.
- Samples now include four extreme puzzles (Easter Monster, Golden Nugget, a 17-clue brute-force breaker,
  Norvig's hardest). MRV solves every one in under 60K placements.
- The classic Python/Streamlit version (`app_classic.py`) has the same limit as a sidebar slider (default 20M). Python is far slower than
  the browser: plain backtracking on "Hard" takes about 35 seconds.
