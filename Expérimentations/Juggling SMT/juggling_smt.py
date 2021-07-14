from recordclass import StructClass
from typing import List, Dict, Tuple, Set

import modele
import ipywidgets
import pythreejs

import z3


class Throw(StructClass):
    ball: str
    time: int
    max_height: int

    def __hash__(self):
        return hash(str(self))

    def latex(self):
        return r"T({}, {}, {})".format(self.time, self.ball, self.max_height)


def music_to_throws(music: List[Tuple[int, str]]) \
        -> Tuple[Set[str], List[List[Throw]]]:
    notes: Set[str] = {n for t, n in music}
    sorted_music = sorted(music, key=lambda x: x[0])
    flying_note_time: Dict[str, int] = {n: 0 for n in notes}
    throws: List[List[Throw]] = []
    time = 0
    for t, n in sorted_music:
        for n1 in notes:
            flying_note_time[n1] += t - time
        for i in range(time, t):
            throws.append([])
        time = t
        throw = Throw(ball=n,
                      time=t - flying_note_time[n],
                      max_height=flying_note_time[n])
        throws[t - flying_note_time[n]].append(throw)
        flying_note_time[n] = 0
    return notes, throws


# ============================================================================ #
#                                                                              #
#              RÉSOLUTION DES CONTRAINTES AVEC UN SOLVEUR SMT                  #
#                                                                              #
# ============================================================================ #

def throws_to_define_fun(throws: List[List[Throw]]):
    def T(t, b, hmax):
        nonlocal throws
        args = []
        for t1 in range(len(throws)):
            for throw in throws[t1]:
                args.append(z3.And(t == throw.time,
                                   b == z3.StringVal(throw.ball),
                                   hmax == throw.max_height))
        return z3.If(z3.Or(*args), z3.BoolVal(True), z3.BoolVal(False))
    return T


def throws_max_time(throws: List[List[Throw]]):
    max_time = 0
    for t in range(len(throws)):
        for throw in throws[t]:
            if t + throw.max_height > max_time:
                max_time = t + throw.max_height
    return max_time


def solve_with_smt_solver(balls: List[str], throws: List[List[Throw]],
                          nb_hands: int, H: int, max_weight: int,
                          forbidden_multiplex: List[Tuple[int, ]]):
    max_time = throws_max_time(throws)
    solver = z3.Solver()
    Pair, mk_pair, (first, second) = z3.TupleSort("Pair", [z3.IntSort(), z3.IntSort()])
    T = throws_to_define_fun(throws)
    # affect = z3.Function('affect', z3.IntSort(), z3.StringSort(), z3.IntSort(),
    #                      z3.IntSort(), z3.IntSort(), z3.BoolSort())
    affect = z3.Function('affect', z3.IntSort(), z3.StringSort(), z3.IntSort(), Pair)
    t, hmax, m, h, t1, hmax1, m1, h1 = z3.Ints('t hmax m h t1 hmax1 m1 h1')
    b, b1 = z3.Strings('b b1')
    solver.add(z3.ForAll([t, b, hmax, m, h],
                         z3.Implies(z3.And(0 <= t, t <= max_time,
                                           z3.Or(*[b == z3.StringVal(ball) for ball in balls]),
                                           1 <= hmax, hmax <= max_time,
                                           1 <= m, m <= nb_hands,
                                           1 <= h, h <= hmax,
                                           affect(t, b, hmax) == mk_pair(m, h)),
                                    T(t, b, hmax))))
    solver.add(z3.ForAll([t, b, hmax],
                         z3.Implies(z3.And(0 <= t, t <= max_time,
                                           z3.Or(*[b == z3.StringVal(ball) for ball in balls]),
                                           1 <= hmax, hmax <= max_time,
                                           T(t, b, hmax)),
                                    z3.Exists([m, h],
                                              z3.And(1 <= m, m <= nb_hands,
                                                     1 <= h, h <= hmax,
                                                     affect(t, b, hmax) == mk_pair(m, h))))))
    weights: List[List[Tuple[Throw, int]]] = [[] for t in range(max_time + 1)]
    for t_it in range(len(throws)):
        for throw in throws[t_it]:
            for h_it in range(1, min(throw.max_height, H) + 1):
                for t1_it in range(t_it, t_it + throw.max_height - h_it):
                    weights[t1_it].append((throw, h_it))
    for m_it in range(1, nb_hands + 1):
        for t1_it in range(len(weights)):
            args = [affect(throw.time, z3.StringVal(throw.ball), throw.max_height) == mk_pair(m_it, h_it)
                    for (throw, h_it) in weights[t1_it]]
            if len(args) > 0:
                solver.add(z3.AtMost(*args, max_weight))
    solver.add(z3.ForAll([t, b, hmax, hmax1, m, h],
                         z3.Implies(z3.And(0 <= t, t <= max_time,
                                           z3.Or(*[b == z3.StringVal(ball) for ball in balls]),
                                           1 <= hmax, hmax <= max_time,
                                           1 <= hmax1, hmax1 <= max_time,
                                           1 <= m, m <= nb_hands,
                                           1 <= h, h <= hmax1,
                                           affect(t, b, hmax) == mk_pair(m, 1)),
                                    affect(t + hmax, b, hmax1) != mk_pair(m, h))))
    solver.add(z3.ForAll([t, t1, b, b1, hmax, hmax1, m, h, h1],
                         z3.Implies(z3.And(0 <= t, t <= max_time,
                                           0 <= t1, t1 <= max_time,
                                           z3.Or(*[b == z3.StringVal(ball) for ball in balls]),
                                           z3.Or(*[b1 == z3.StringVal(ball) for ball in balls]),
                                           1 <= hmax, hmax <= max_time,
                                           1 <= hmax1, hmax1 <= max_time,
                                           1 <= m, m <= nb_hands,
                                           1 <= h, h <= hmax,
                                           1 <= h1, h1 <= hmax1,
                                           affect(t, b, hmax) == mk_pair(m, h),
                                           affect(t1, b1, hmax1) == mk_pair(m, h1),
                                           t + hmax == t1 + hmax1),
                                    z3.And(t == t1, b == b1, hmax == hmax1, h == h1))))
    hand = z3.Function('hand', z3.IntSort(), z3.IntSort(), z3.IntSort(), z3.BoolSort())
    fm: Tuple[int, ]
    for fm in forbidden_multiplex:
        if len(fm) == 1:
            solver.add(z3.ForAll([t, b, hmax, m],
                                 z3.Implies(z3.And(0 <= t, t <= max_time,
                                                   z3.Or(*[b == z3.StringVal(ball) for ball in balls]),
                                                   1 <= hmax, hmax <= max_time,
                                                   1 <= m, m <= nb_hands),
                                            affect(t, b, hmax) != mk_pair(m, fm[0]))))
        elif len(fm) == 2:
            if fm[0] == fm[1]:
                solver.add(z3.ForAll([t, t1, b, b1, hmax, hmax1, m],
                                     z3.Implies(z3.And(0 <= t, t <= max_time,
                                                       0 <= t1, t1 <= max_time,
                                                       z3.Or(*[b == z3.StringVal(ball) for ball in balls]),
                                                       z3.Or(*[b1 == z3.StringVal(ball) for ball in balls]),
                                                       1 <= hmax, hmax <= max_time,
                                                       1 <= hmax1, hmax1 <= max_time,
                                                       1 <= m, m <= nb_hands,
                                                       affect(t, b, hmax) == mk_pair(m, fm[0]),
                                                       affect(t1, b1, hmax1) == mk_pair(m, fm[0]),
                                                       t + hmax - fm[0] == t1 + hmax1 - fm[0]),
                                                b == b1)))
            else:
                solver.add(z3.ForAll([t, b, hmax, m, h],
                                     z3.Implies(z3.And(0 <= t, t <= max_time,
                                                       z3.Or(*[b == z3.StringVal(ball) for ball in balls]),
                                                       1 <= hmax, hmax <= max_time,
                                                       1 <= m, m <= nb_hands,
                                                       1 <= h, h <= hmax,
                                                       affect(t, b, hmax) == mk_pair(m, h)),
                                                hand(t + hmax - h, m, h))))
                solver.add(z3.ForAll([t, m],
                                     z3.Implies(z3.And(0 <= t, t <= max_time,
                                                       1 <= m, m <= nb_hands),
                                                z3.Or(z3.Not(hand(t, m, fm[0])),
                                                      z3.Not(hand(t, m, fm[1]))))))
        else:
            raise RuntimeError("Erreur: Interdiction de lancers multiplex de plus de 2 lancers non supporté.")
    # print(solver.sexpr())
    # solver.add(z3.ForAll([t, b, hmax, m, h],
    #                      z3.Implies(affect(t, b, hmax, m, h),
    #                                 T(t, b, hmax))))
    # solver.add(z3.ForAll([t, b, hmax],
    #                      z3.Implies(T(t, b, hmax),
    #                                 z3.Exists([m, h],
    #                                           z3.And(0 <= m, m < nb_hands,
    #                                                  0 <= h, h <= hmax,
    #                                                  affect(t, b, hmax, m, h))))))
    # m1, m2, h1, h2 = z3.Ints('m1 m2 h1 h2')
    # solver.add(z3.ForAll([t, b, hmax, m1, m2, h1, h2],
    #                      z3.Implies(affect(t, b, hmax, m1, h1),
    #                                 z3.Implies(affect(t, b, hmax, m2, h2),
    #                                            z3.And(m1 == m2, h1 == h2)))))

    check = solver.check()
    print(check)
    # if check == z3.sat:
    #     model = solver.model()
    #     print(type(model))

    #     print(model.evaluate(affect(0, z3.StringVal('mi'), 5)))
    #     print(model.evaluate(affect(0, z3.StringVal('do'), 1)))
    #     print(model.evaluate(affect(1, z3.StringVal('mi'), 2)))

        # print(model.evaluate(affect(0, z3.StringVal('mi'), 5, 0, 1)))
        # print(model.evaluate(affect(0, z3.StringVal('mi'), 5, 0, 2)))
        # print(model.evaluate(affect(0, z3.StringVal('mi'), 5, 0, 3)))
        # print(model.evaluate(affect(0, z3.StringVal('mi'), 5, 0, 4)))
        # print(model.evaluate(affect(0, z3.StringVal('mi'), 5, 0, 5)))
        # print(model.evaluate(affect(0, z3.StringVal('mi'), 5, 1, 1)))
        # print(model.evaluate(affect(0, z3.StringVal('mi'), 5, 1, 2)))
        # print(model.evaluate(affect(0, z3.StringVal('mi'), 5, 1, 3)))
        # print(model.evaluate(affect(0, z3.StringVal('mi'), 5, 1, 4)))
        # print(model.evaluate(affect(0, z3.StringVal('mi'), 5, 1, 5)))


def music_max_time(music: List[Tuple[int, str]]):
    m = 0
    for t, _ in music:
        if t > m:
            m = t
    return m


def imp(*args):
    e = args[-1]
    for i in range(len(args) - 2, -1, -1):
        e = z3.Implies(args[i], e)
    return e


def solve_with_smt_solver2(balls: List[str], music: List[Tuple[int, str]],
                           nb_hands: int, H: int, max_weight: int,
                           forbidden_multiplex: List[Tuple[int, ]]):
    max_time = music_max_time(music)
    solver = z3.Solver()
    # solver.set(priority='box')
    Pair, mk_pair, (first, second) = z3.TupleSort("Pair", [z3.IntSort(), z3.IntSort()])
    h = {ball: z3.Const('h_' + ball, z3.SeqSort(z3.IntSort())) for ball in balls}
    p = {ball: z3.Const('h_' + ball, z3.SeqSort(z3.IntSort())) for ball in balls}
    t, m, i, k = z3.Ints('t m i k')
    for ball in balls:
        solver.add(z3.Length(h[ball]) == max_time + 1)
        solver.add(z3.Length(p[ball]) == max_time + 1)
        solver.add(z3.ForAll([t], z3.Implies(z3.And(0 <= t, t <= max_time), z3.And(0 <= h[ball][t], h[ball][t] <= nb_hands))))
    for tm, bm in music:
        solver.add(z3.And(h[bm][tm] != 0, h[bm][tm - 1] != h[bm][tm]))
    solver.add(z3.ForAll([t, m],
                         imp(0 <= t, t <= max_time,
                             1 <= m, m <= nb_hands,
                             z3.AtMost(*[z3.And(h[ball][t] == m) for ball in balls], max_weight))))
    solver.add(z3.ForAll([t, m],
                         imp(1 <= t, t <= max_time,
                             1 <= m, m <= nb_hands,
                             z3.AtMost(*[z3.And(h[ball][t] != 0, h[ball][t - 1] != h[ball][t]) for ball in balls], 1))))
    solver.add(z3.ForAll([t, m, i],
                         imp(0 <= t, t <= max_time,
                             1 <= m, m <= nb_hands,
                             1 <= i, i <= max_weight,
                             z3.AtMost(*[z3.And(h[ball][t] == m, p[ball][t] == i) for ball in balls], 1))))
    for ball in balls:
        solver.add(z3.ForAll([t, m, i],
                             imp(0 <= t, t <= max_time,
                                 1 <= m, m <= nb_hands,
                                 2 <= i, i <= max_weight,
                                 h[ball][t] == m,
                                 p[ball][t] == i,
                                 z3.Or(z3.And(h[ball][t + 1] == m, p[ball][t + 1] == i),
                                       z3.And(h[ball][t + 1] == m, p[ball][t + 1] == i - 1),
                                       z3.And(*[imp(h[ball][t] == m, p[ball][t] <= i, h[ball][t + 1] != m) for ball in balls])))))
    # solver.add(z3.ForAll([t, m, k],
    #                      imp(0 <= t, t <= max_time,
    #                          1 <= m, m <= nb_hands,
    #                          2 <= k, k <= max_weight,
    #                          h[ball][t] == m,
    #                          p[ball][t] == i,
    #                          z3.Or(z3.And(h[ball][t + 1] == m, p[ball][t + 1] == i),
    #                                z3.And(h[ball][t + 1] == m, p[ball][t + 1] == i - 1)))))
    # for ball in balls:
    #     for t in range(0, max_time + 1):
    #         solver.minimize(p[ball][t])
    #         solver.minimize(z3.If(p[ball][t] == 0, 1, 0))
    check = solver.check()
    print(check)
