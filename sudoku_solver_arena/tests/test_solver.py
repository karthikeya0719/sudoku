import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from solver import *


def is_valid_solution(sol, given):
    full = set(range(1, 10))
    if find_conflicts(sol):
        return False
    if any(set(row) != full for row in sol):
        return False
    return all(not given[r][c] or given[r][c] == sol[r][c] for r in range(9) for c in range(9))


class T(unittest.TestCase):
    def test_samples_solve_both_strategies(self):
        for name, text in SAMPLES.items():
            g = parse_puzzle(text)
            sols = []
            for s in STRATEGIES:
                r = solve(g, s)
                if name.startswith(("Hard (", "Extreme - 17")) and s == "naive":
                    self.assertTrue(r.limit_hit and not r.solved)
                    continue
                self.assertTrue(r.solved, f"{name}/{s}")
                self.assertTrue(is_valid_solution(r.grid, g), f"{name}/{s}")
                sols.append(r.grid)
                if not r.truncated:
                    self.assertEqual(replay(g, r.steps, len(r.steps)), r.grid)
                self.assertEqual(r.placements - r.backtracks, sum(1 for row in g for v in row if not v))
            if len(sols) == 2:
                self.assertEqual(sols[0], sols[1], name)

    def test_known_solution(self):
        r = solve(parse_puzzle(SAMPLES["Medium"]), "mrv")
        self.assertEqual("".join(map(str, r.grid[0])), "534678912")

    def test_unsolvable(self):
        g = parse_puzzle("12345678." + "........9" + "." * 63)
        for s in STRATEGIES:
            r = solve(g, s)
            self.assertFalse(r.solved)
            self.assertEqual(r.grid, g)

    def test_conflicts_and_parse(self):
        g = parse_puzzle("55" + "0" * 79)
        self.assertEqual(find_conflicts(g), {(0, 0), (0, 1)})
        with self.assertRaises(ValueError):
            solve(g)
        with self.assertRaises(ValueError):
            parse_puzzle("123")
        with self.assertRaises(ValueError):
            parse_puzzle("x" * 81)

    def test_candidates(self):
        g = parse_puzzle(SAMPLES["Medium"])
        self.assertEqual(candidates(g, 0, 2), [1, 2, 4])
        self.assertEqual(candidates(g, 0, 0), [1, 2, 5])  # filled cell: evaluated as if blank

    def test_limit(self):
        r = solve(parse_puzzle(SAMPLES["Hardest (Inkala)"]), "naive", max_placements=100)
        self.assertTrue(r.limit_hit and not r.solved)


if __name__ == "__main__":
    unittest.main()
