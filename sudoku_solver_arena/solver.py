"""Sudoku Solver Arena - core algorithms (no UI dependencies).

Two backtracking strategies, both with constraint checking after every decision:
  naive : fill the first empty cell (row-major), try 1..9.
  mrv   : pick the empty cell with the fewest legal candidates (forward checking);
          a cell with zero candidates is detected immediately as a dead end.
Every decision is recorded as a Step so the search can be replayed.
"""
import time
from dataclasses import dataclass

STRATEGIES = {
    "naive": "Plain backtracking (row-major)",
    "mrv": "Backtracking + MRV forward checking",
}

SAMPLES = {
    "Easy": "003020600900305001001806400008102900700000008006708200002609500800203009005010300",
    "Medium": "530070000600195000098000060800060003400803001700020006060000280000419005000080079",
    "Hard (slow for plain backtracking)": "400000805030000000000700000020000060000080400000010000000603070500200000104000000",
    "Hardest (Inkala)": "800000000003600000070090200050007000000045700000100030001000068008500010090000400",
    "Extreme - Easter Monster": "1.......2.9.4...5...6...7...5.9.3.......7.......85..4.7.....6...3...9.8...2.....1",
    "Extreme - Golden Nugget": ".......39.....1..5..3.5.8....8.9...6.7...2...1..4.......9.8..5..2....6..4..7.....",
    "Extreme - 17 clues (breaks plain backtracking)": "..............3.85..1.2.......5.7.....4...1...9.......5......73..2.1........4...9",
    "Extreme - Norvig's hardest": "85...24..72......9..4.........1.7..23.5...9...4...........8..7..17..........36.4.",
}

EMPTY_CHARS = set("0._*-")
SKIP_CHARS = set(" \t\r\n|,+")


def parse_puzzle(text):
    """Parse 81 cells (digits 1-9; 0 . _ * - are blanks; whitespace and | , + ignored)."""
    cells = [ch for ch in text if ch not in SKIP_CHARS]
    if len(cells) != 81:
        raise ValueError(f"Expected 81 cells, found {len(cells)}.")
    flat = []
    for ch in cells:
        if ch in EMPTY_CHARS:
            flat.append(0)
        elif ch in "123456789":
            flat.append(int(ch))
        else:
            raise ValueError(f"Invalid character {ch!r}: use digits 1-9 and 0 or . for blanks.")
    return [flat[i * 9:(i + 1) * 9] for i in range(9)]


def _units():
    for i in range(9):
        yield [(i, c) for c in range(9)]
        yield [(r, i) for r in range(9)]
        br, bc = 3 * (i // 3), 3 * (i % 3)
        yield [(br + k // 3, bc + k % 3) for k in range(9)]


def find_conflicts(grid):
    """Return the set of (row, col) cells that duplicate a digit in a row, column or box."""
    bad = set()
    for unit in _units():
        seen = {}
        for r, c in unit:
            if grid[r][c]:
                seen.setdefault(grid[r][c], []).append((r, c))
        for cells in seen.values():
            if len(cells) > 1:
                bad.update(cells)
    return bad


def candidates(grid, r, c):
    """Digits that can legally go in (r, c), ignoring the cell's current value."""
    used = set()
    for k in range(9):
        used.add(grid[r][k])
        used.add(grid[k][c])
    br, bc = 3 * (r // 3), 3 * (c // 3)
    for i in range(3):
        for j in range(3):
            used.add(grid[br + i][bc + j])
    own = grid[r][c]
    # The cell's own value only counts as used if it is also present elsewhere; we
    # evaluate on a copy with the cell blanked to keep this simple and correct.
    if own:
        tmp = [row[:] for row in grid]
        tmp[r][c] = 0
        return candidates(tmp, r, c)
    return [v for v in range(1, 10) if v not in used]


@dataclass
class Step:
    action: str  # "place" or "backtrack"
    row: int
    col: int
    value: int
    depth: int


@dataclass
class Result:
    solved: bool
    grid: list
    steps: list
    placements: int = 0
    backtracks: int = 0
    checks: int = 0
    seconds: float = 0.0
    truncated: bool = False   # step trace was capped (search itself still completed)
    limit_hit: bool = False   # search aborted at max_placements


class _Limit(Exception):
    pass


def solve(grid, strategy="naive", max_record=20000, max_placements=500_000):
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy {strategy!r}")
    if find_conflicts(grid):
        raise ValueError("Puzzle has conflicting given digits.")
    board = [row[:] for row in grid]
    rows, cols, boxes = [0] * 9, [0] * 9, [0] * 9
    for r in range(9):
        for c in range(9):
            if board[r][c]:
                bit = 1 << board[r][c]
                rows[r] |= bit
                cols[c] |= bit
                boxes[r // 3 * 3 + c // 3] |= bit
    res = Result(False, [row[:] for row in grid], [])

    def record(action, r, c, v, depth):
        if len(res.steps) < max_record:
            res.steps.append(Step(action, r, c, v, depth))
        else:
            res.truncated = True

    def pick():
        best, best_n = None, 10
        for r in range(9):
            for c in range(9):
                if board[r][c]:
                    continue
                m = ~(rows[r] | cols[c] | boxes[r // 3 * 3 + c // 3]) & 0x3FE
                if strategy == "naive":
                    return r, c, m
                n = bin(m).count("1")
                if n < best_n:
                    best, best_n = (r, c, m), n
                    if n <= 1:
                        return best
        return best

    def rec(depth):
        cell = pick()
        if cell is None:
            return True
        r, c, m = cell
        b = r // 3 * 3 + c // 3
        for v in range(1, 10):
            res.checks += 1
            if not (m >> v) & 1:
                continue
            if res.placements >= max_placements:
                raise _Limit
            bit = 1 << v
            board[r][c] = v
            rows[r] |= bit
            cols[c] |= bit
            boxes[b] |= bit
            res.placements += 1
            record("place", r, c, v, depth)
            if rec(depth + 1):
                return True
            rows[r] ^= bit
            cols[c] ^= bit
            boxes[b] ^= bit
            board[r][c] = 0
            res.backtracks += 1
            record("backtrack", r, c, v, depth)
        return False

    start = time.perf_counter()
    try:
        res.solved = rec(0)
    except _Limit:
        res.limit_hit = True
    res.seconds = time.perf_counter() - start
    if res.solved:
        res.grid = board
    return res


def replay(grid, steps, upto):
    """Board state after applying the first `upto` recorded steps."""
    board = [row[:] for row in grid]
    for s in steps[:upto]:
        board[s.row][s.col] = s.value if s.action == "place" else 0
    return board
