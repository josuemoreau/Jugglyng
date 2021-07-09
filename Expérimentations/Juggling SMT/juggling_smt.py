from recordclass import StructClass
from typing import List, Dict, Tuple, Union, Set, Any
from sage.all import MixedIntegerLinearProgram

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


def solve_with_smt_solver(balls: List[str], throws: List[List[Throw]],
                          nb_hands: int, H: int, max_weight: int,
                          forbidden_multiplex: List[Tuple[int, ]]):
    solver = z3.Solver()
    Pair, mk_pair, (first, second) = z3.TupleSort("Pair", [z3.IntSort(), z3.IntSort()])
    T = throws_to_define_fun(throws)
    # affect = z3.Function('affect', z3.IntSort(), z3.StringSort(), z3.IntSort(),
    #                      z3.IntSort(), z3.IntSort(), z3.BoolSort())
    affect = z3.Function('affect', z3.IntSort(), z3.StringSort(), z3.IntSort(), Pair)
    t, hmax, m, h = z3.Ints('t hmax m h')
    b = z3.String('b')
    solver.add(z3.ForAll([t, b, hmax, m, h],
                         z3.Implies(z3.And(0 <= m, m < nb_hands,
                                           0 <= h, h <= hmax,
                                           affect(t, b, hmax) == mk_pair(m, h)),
                                    T(t, b, hmax))))
    solver.add(z3.ForAll([t, b, hmax],
                         z3.Implies(T(t, b, hmax),
                                    z3.Exists([m, h],
                                              z3.And(0 <= m, m < nb_hands,
                                                     0 <= h, h <= hmax,
                                                     affect(t, b, hmax) == mk_pair(m, h))))))
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
    if check == z3.sat:
        model = solver.model()
        print(type(model))

        print(model.evaluate(affect(0, z3.StringVal('mi'), 5)))
        print(model.evaluate(affect(0, z3.StringVal('do'), 1)))
        print(model.evaluate(affect(1, z3.StringVal('mi'), 2)))

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
