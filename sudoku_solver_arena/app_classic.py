"""Sudoku Solver Arena - Streamlit app.  Run:  streamlit run app.py"""
import time

import pandas as pd
import streamlit as st

from solver import (SAMPLES, STRATEGIES, candidates, find_conflicts,
                    parse_puzzle, replay, solve)

MAX_TRACE = 20000
CSS = ("<style>.sdk{border-collapse:collapse;margin:8px auto;border:3px solid #222}"
       ".sdk td{width:44px;height:44px;text-align:center;font:22px monospace;color:#111;"
       "background:#fff;border:1px solid #999;padding:0}"
       ".sdk td.bl{border-left:3px solid #222}.sdk td.bt{border-top:3px solid #222}"
       ".sdk td.given{background:#e3e7fa;font-weight:700}.sdk td.cur{background:#fff176}"
       ".sdk td.back{background:#ffab91}.sdk td.conf{background:#ef5350;color:#fff}</style>")

st.set_page_config(page_title="Sudoku Solver Arena", page_icon="🧩", layout="wide")


def board_html(board, given, cur=None, kind=None, conflicts=()):
    rows = []
    for r in range(9):
        tds = []
        for c in range(9):
            cls = []
            if c % 3 == 0:
                cls.append("bl")
            if r % 3 == 0:
                cls.append("bt")
            if (r, c) in conflicts:
                cls.append("conf")
            elif cur == (r, c):
                cls.append("back" if kind == "backtrack" else "cur")
            elif given[r][c]:
                cls.append("given")
            tds.append(f'<td class="{" ".join(cls)}">{board[r][c] or ""}</td>')
        rows.append("<tr>" + "".join(tds) + "</tr>")
    return CSS + '<table class="sdk">' + "".join(rows) + "</table>"


@st.cache_data(show_spinner="Solving...")
def run(grid_key, strategy, limit):
    return solve([list(r) for r in grid_key], strategy, max_record=MAX_TRACE, max_placements=limit)


def draw(view, grid, res, k):
    board = replay(grid, res.steps, k)
    cur = res.steps[k - 1] if k else None
    placed = sum(1 for s in res.steps[:k] if s.action == "place")
    undone = k - placed
    if cur is None:
        msg = "Initial puzzle. The algorithm has not made any decision yet."
    elif cur.action == "place":
        before = replay(grid, res.steps, k - 1)
        cands = candidates(before, cur.row, cur.col)
        msg = (f"Step {k}: place **{cur.value}** at R{cur.row + 1}C{cur.col + 1} "
               f"(legal candidates there: {cands}). Constraints checked - still consistent. "
               f"Depth {cur.depth + 1}.")
    else:
        msg = (f"Step {k}: **BACKTRACK** - removed {cur.value} from R{cur.row + 1}C{cur.col + 1}; "
               f"no completion exists beneath that choice.")
    with view.container():
        st.markdown(board_html(board, grid, (cur.row, cur.col) if cur else None,
                               cur.action if cur else None), unsafe_allow_html=True)
        st.markdown(msg)
        a, b = st.columns(2)
        a.metric("Placements so far", placed)
        b.metric("Backtracks so far", undone)
        if k == len(res.steps) and res.solved and not res.truncated:
            st.success("Solved - every row, column and 3x3 box contains 1-9.")


# ---------------------------------------------------------------- sidebar: input
with st.sidebar:
    st.header("Puzzle")
    sample = st.selectbox("Sample puzzle", list(SAMPLES))
    mode = st.radio("Input method", ["Sample", "Paste text", "Grid editor"])
    base = parse_puzzle(SAMPLES[sample])
    if mode == "Sample":
        grid = base
    elif mode == "Paste text":
        text = st.text_area("81 cells - digits 1-9, blanks as 0 or .", SAMPLES[sample],
                            height=170, key=f"txt_{sample}")
        try:
            grid = parse_puzzle(text)
        except ValueError as e:
            st.error(str(e))
            st.stop()
    else:
        df = pd.DataFrame(base, columns=[str(i) for i in range(1, 10)])
        cfg = {c: st.column_config.NumberColumn(c, min_value=0, max_value=9, step=1)
               for c in df.columns}
        edited = st.data_editor(df, key=f"ed_{sample}", hide_index=True, column_config=cfg)
        grid = [[0 if pd.isna(v) else int(v) for v in row] for row in edited.values.tolist()]
        st.caption("0 = blank")
    strategy = st.selectbox("Algorithm", list(STRATEGIES), format_func=STRATEGIES.get)
    limit = st.select_slider("Search limit (max placements)", [500_000, 5_000_000, 20_000_000, 50_000_000],
                             value=20_000_000, format_func=lambda n: f"{n:,}")
    st.caption("Python is much slower than the browser version: a 10M-placement search takes a while.")

st.title("Sudoku Solver Arena")
st.caption("Backtracking + constraint checking, visualized one decision at a time.")

conflicts = find_conflicts(grid)
if conflicts:
    st.error(f"Invalid entries: {len(conflicts)} cells repeat a digit in a row, column or box.")
    st.markdown(board_html(grid, grid, conflicts=conflicts), unsafe_allow_html=True)
    st.stop()

grid_key = tuple(tuple(r) for r in grid)
tab_viz, tab_cmp = st.tabs(["Step-by-step visualizer", "Compare algorithms"])

# ---------------------------------------------------------------- visualizer
with tab_viz:
    res = run(grid_key, strategy, limit)
    total = len(res.steps)
    if res.limit_hit:
        st.warning("This algorithm hit the search limit without finishing - raise the search limit or try the MRV strategy.")
    elif not res.solved:
        st.error("This puzzle has no solution (the search exhausted every possibility).")
    else:
        st.info(f"{STRATEGIES[strategy]}: {res.placements} placements, {res.backtracks} "
                f"backtracks, {res.checks} constraint checks, {res.seconds * 1000:.1f} ms.")
    if res.truncated:
        st.caption(f"Only the first {MAX_TRACE:,} steps are recorded for replay.")

    view = st.empty()
    if total == 0:
        draw(view, grid, res, 0)
    else:
        sig = (grid_key, strategy)
        if st.session_state.get("sig") != sig:
            st.session_state.sig = sig
            st.session_state.step = 0
        if "pending" in st.session_state:
            st.session_state.step = st.session_state.pop("pending")

        def jump(delta=None, to=None):
            cur = st.session_state.step
            new = to if to is not None else cur + delta
            st.session_state.step = max(0, min(total, new))

        st.slider("Step", 0, total, key="step")
        c1, c2, c3, c4 = st.columns(4)
        c1.button("⏮ Reset", on_click=jump, kwargs={"to": 0})
        c2.button("◀ Prev", on_click=jump, kwargs={"delta": -1})
        c3.button("Next ▶", on_click=jump, kwargs={"delta": 1})
        play = c4.button("▶ Play")
        stride = st.slider("Steps per animation frame", 1, 200, 1)
        if play:
            for k in range(st.session_state.step, total + 1, stride):
                draw(view, grid, res, k)
                time.sleep(0.05)
            st.session_state.pending = total
            st.rerun()
        else:
            draw(view, grid, res, st.session_state.step)

# ---------------------------------------------------------------- comparison
with tab_cmp:
    rows, sols = [], []
    for key, label in STRATEGIES.items():
        r = run(grid_key, key, limit)
        sols.append(r.grid if r.solved else None)
        status = "Yes" if r.solved else ("Step limit" if r.limit_hit else "No solution")
        rows.append({"Algorithm": label, "Solved": status, "Placements": r.placements,
                     "Backtracks": r.backtracks, "Constraint checks": r.checks,
                     "Time (ms)": round(r.seconds * 1000, 2)})
    table = pd.DataFrame(rows).set_index("Algorithm")
    st.dataframe(table, use_container_width=True)
    st.bar_chart(table[["Placements", "Backtracks"]])
    if all(s is not None for s in sols) and sols[0] == sols[1]:
        st.success("Both algorithms reached the same solution; they differ only in effort.")
    st.markdown("**Why the difference?** Plain backtracking blindly takes the next empty cell, "
                "so it can explore huge dead branches. MRV always branches on the most "
                "constrained cell and spots a cell with no legal digit immediately, pruning "
                "those branches early.")
