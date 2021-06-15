from recordclass import StructClass
from typing import List, Dict, Tuple, Union, Set, Any
from sage.all import MixedIntegerLinearProgram, OrderedSetPartitions, \
    cartesian_product, Arrangements
from DLX.dlxm import DLXM

from pylatex import Document
from pylatex.utils import NoEscape


def InsertAtEachPosition(l, e):
    for i in range(0, len(l) + 1):
        l1 = l.copy()
        l1.insert(i, e)
        yield l1


def EmpOrderedSetPartitions(s, k):
    for p in OrderedSetPartitions(s, k):
        yield p
    for i in range(k - 1, 0, -1):
        P = OrderedSetPartitions(s, i)
        for p in P:
            L = [list(p)]
            for j in range(0, k - i):
                L1 = []
                for pl in L:
                    e = set()
                    l1 = list(InsertAtEachPosition(pl, e))
                    L1 = L1 + l1
                L = L1
            for l in L:
                yield l


def HandsConfigurations(balls, nb_hands):
    L = []
    for p in EmpOrderedSetPartitions(balls, nb_hands):
        for config in cartesian_product([Arrangements(s, len(s)) for s in p]):
            L.append(tuple([tuple(hand_config) for hand_config in config]))
    return L


def next_configs(config):
    hands_next_configs = [[] for _ in range(len(config))]
    for hand in range(len(config)):
        n = len(config[hand])
        ch = config[hand]
        if n <= 1 or n == 4:
            hands_next_configs[hand].append(tuple(ch))
        elif n == 2 or n == 3:
            hands_next_configs[hand].append(tuple([ch[(i + 1) % n] for i in range(n)]))
        else:
            hands_next_configs[hand].append(tuple(ch))
    return [tuple([tuple(hand_config) for hand_config in config]) for config in cartesian_product(hands_next_configs)]


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

"""
class XItem(StructClass):
    throw: Throw
    hand: int
    flying_time: int

    def __hash__(self):
        return hash(str(self))

    def latex(self):
        return r"x_{}^{}".format("{" + str(self.throw) + "}",
                                 "{" + str(self.hand) + ", "
                                 + str(self.flying_time) + "}")


class LItem(StructClass):
    throw: Throw

    def __hash__(self):
        return hash(str(self))

    def latex(self):
        return r"l_{}".format("{" + str(self.throw) + "}")


class WItem(StructClass):
    time: int
    hand: int

    def __hash__(self):
        return hash(str(self))

    def latex(self):
        return r"w_{}".format("{" + str(self.time) + ", "
                              + str(self.hand) + "}")


class IItem(StructClass):
    time: int
    hand: int
    flying_time: int

    def __hash__(self):
        return hash(str(self))

    def latex(self):
        return r"i_{}".format("{" + str(self.time) + ", "
                              + str(self.hand) + ", "
                              + str(self.flying_time) + "}")


class MItem(StructClass):
    time: int
    hand: int
    multiplex: Tuple[int, ]

    def __hash__(self):
        return hash(str(self))

    def latex(self):
        return r"m_{}".format("{" + str(self.time) + ", "
                              + str(self.hand) + ", "
                              + str(self.multiplex) + "}")


class DItem(StructClass):
    time: int
    hand: int

    def __hash__(self):
        return hash(str(self))

    def latex(self):
        return r"D_{}^{}".format("{" + str(self.time) + "}",
                                 "{" + str(self.hand) + "}")


class UItem(StructClass):
    ball: str
    time: int
    hand: int

    def __hash__(self):
        return hash(str(self))

    def latex(self):
        return r"U_{}^{}".format("{" + self.ball + ", " + str(self.time) + "}",
                                 "{" + str(self.hand) + "}")


class BItem(StructClass):
    ball: str
    time: int

    def __hash__(self):
        return hash(str(self))

    def latex(self):
        return r"B_{}^{}".format("{" + self.ball + "}",
                                 "{" + str(self.time) + "}")


class PItem(StructClass):
    ball: str
    time: int

    def __hash__(self):
        return hash(str(self))

    def latex(self):
        return r"C_{}".format("{" + str(self.time) + "}")
"""


class Item(object):
    _name: str
    _print_order_down: List[str]
    _print_order_up: List[str]
    _dict: Dict[str, Any]

    bounds: Tuple[int, int]

    def __init__(self, name: str, params: Dict[str, Any],
                 print_order_down: List[str] = [],
                 print_order_up: List[str] = [],
                 low: int = 1, high: int = 1):
        self._name = name
        self._dict = params
        self._print_order_down = print_order_down
        self._print_order_up = print_order_up
        self.bounds = (low, high)

    def __getitem__(self, k):
        return self._dict[k]

    def __str__(self):
        return self._name + str(self._dict)

    def __repr__(self):
        s = self._name + "("
        s += ", ".join(["{}: {}".format(k, self._dict[k]) for k in self._dict])
        s += ")"
        return s

    def __hash__(self):
        return hash(self.__str__())

    def latex(self):
        s = "{} + {" % self._name
        s += ",".join([self._dict[k] for k in self._print_order_down])
        s += "}^{"
        s += ",".join([self._dict[k] for k in self._print_order_up])
        s += "}"
        return s

    def __getattribute__(self, name: str) -> Any:
        if name in object.__getattribute__(self, "_dict"):
            return object.__getattribute__(self, "_dict")[name]
        else:
            return object.__getattribute__(self, name)


class LItem(Item):
    def __init__(self, throw):
        super().__init__("l", {"throw": throw}, ["throw"])


class XItem(Item):
    def __init__(self, throw, hand, flying_time):
        super().__init__("x", {
            "throw": throw,
            "hand": hand,
            "flying_time": flying_time
        }, ["throw"], ["flying_time"], low=0, high=1)


class MItem(Item):
    def __init__(self, time, hand, multiplex):
        super().__init__("m", {
            "time": time,
            "hand": hand,
            "multiplex": multiplex
        }, ["time", "hand", "multiplex"], low=0, high=len(multiplex) - 1)


class DItem(Item):
    def __init__(self, time, hand):
        super().__init__("d", {
            "time": time,
            "hand": hand
        }, ["time", "hand"], low=0, high=1)


class UItem(Item):
    def __init__(self, time, ball, hand):
        super().__init__("u", {
            "time": time,
            "ball": ball,
            "hand": hand
        }, ["time", "ball", "hand"], low=0, high=1)


class BItem(Item):
    def __init__(self, time, ball):
        super().__init__("b", {
            "time": time,
            "ball": ball
        }, ["time", "ball"])


class PItem(Item):
    def __init__(self, time, hand, pos):
        super().__init__("p", {
            "time": time,
            "hand": hand,
            "pos": pos
        }, ["time", "hand"])


class SItem(Item):
    def __init__(self, time, hand, pos):
        super().__init__("s", {
            "time": time,
            "hand": hand,
            "pos": pos
        }, ["time", "hand"])


class NItem(Item):
    def __init__(self, time, hand, pos):
        super().__init__("n", {
            "time": time,
            "hand": hand,
            "pos": pos
        }, ["time", "hand"])


class FItem(Item):
    def __init__(self, time, ball):
        super().__init__("f", {
            "time": time,
            "ball": ball
        }, ["time", "ball"])


class CItem(Item):
    def __init__(self, time, hand):
        super().__init__("c", {
            "time": time,
            "hand": hand
        }, ["time", "hand"])


class ExactCoverInstance(StructClass):
    max_time: int = 0
    nb_hands: int = 1
    balls: Set[str] = set()

    prim_items: List[Item] = []
    sec_items: List[Item] = []

    colors: List[Tuple[int, int]] = []

    rows: List[List[Union[Item, Tuple[Item, int]]]] = []


class ExactCoverSolution(StructClass):
    max_time: int = 0
    nb_hands: int = 1
    balls: Set[str] = set()

    rows: List[List[Union[Item, Tuple[Item, Tuple[Item, int]]]]] = []


def throws_to_extended_exact_cover(balls: Set[str], throws: List[List[Throw]],
                                   nb_hands: int, H: int, K: int,
                                   forbidden_multiplex: List[Tuple[int, ]],
                                   forbidden_2sequences: List[Tuple[int, int]],
                                   multiple_throws: bool) \
        -> ExactCoverInstance:
    max_time = 0
    x_items = {}
    l_items = {}
    w_items = {}
    i_items = {}
    m_items = {}
    m_items_bounds = {}
    d_items = {}
    u_items = {}
    # Variables liées aux contraintes sur les mains
    b_items = {}
    p_items = {}
    s_items = {}
    f_items = {}
    n_items = {}
    c_items = {}

    colors = {}
    fmultiplex: Dict[int, List[Tuple[int, ]]] = {i: [] for i in range(1, H + 1)}
    fflying_time = []
    f2seqs: Dict[int, List[int]] = {i: [] for i in range(1, H + 1)}
    rows = []
    # Remplissage du dictionnaire des lancers multiplex interdits
    for fm in forbidden_multiplex:
        for i in fm:
            fmultiplex[i].append(fm)
    # Remplissage du dictionnaire des séquences de 2 lancers interdits
    for fs in forbidden_2sequences:
        f2seqs[fs[0]].append(fs[1])
    # Calcul du plus tard temps où atterrit une balle
    for t in range(len(throws) - 1, -1, -1):
        if len(throws[t]) > 0:
            max_height = 0
            for throw in throws[t]:
                if throw.max_height > max_height:
                    max_height = throw.max_height
            if t + max_height > max_time:
                max_time = t + max_height
    # Génération des items x et L
    for t in range(len(throws)):
        for throw in throws[t]:
            v = LItem(throw=throw)
            l_items[throw] = v

            for hand in range(nb_hands):
                for flying_time in range(1, min(H, throw.max_height) + 1):
                    x = XItem(throw=throw, hand=hand, flying_time=flying_time)
                    x_items[(throw, hand, flying_time)] = x
    # Génération des items w, M, D et U
    for t in range(max_time + 1):
        for hand in range(nb_hands):
            # w = WItem(time=t, hand=hand)
            # w_items[(t, hand)] = w

            d = DItem(time=t, hand=hand)
            d_items[(t, hand)] = d

            for f in forbidden_multiplex:
                if len(f) == 1:
                    fflying_time.append(f[0])
                else:
                    m = MItem(time=t, hand=hand, multiplex=f)
                    m_items[(t, hand, f)] = m
                    m_items_bounds[f] = (0, len(f) - 1)

            for ball in balls:
                u = UItem(ball=ball, time=t, hand=hand)
                u_items[(ball, t, hand)] = u
    # Génération des items I
    # for t in range(max_time + 1):
    #     for hand in range(nb_hands):
    #         for flying_time in range(1, H + 1):
    #             i = IItem(time=t, hand=hand, flying_time=flying_time)
    #             i_items[(t, hand, flying_time)] = i
    # Génération des items B, F, C, P, S, N
    for t in range(max_time + 1):
        for ball in balls:
            b = BItem(time=t, ball=ball)
            b_items[(t, ball)] = b
            f = FItem(time=t, ball=ball)
            f_items[(t, ball)] = f
        for hand in range(nb_hands):
            c = CItem(time=t, hand=hand)
            c_items[(t, hand)] = c
            for i in range(K):
                p = PItem(time=t, hand=hand, pos=i)
                p_items[(t, hand, i)] = p
                s = SItem(time=t, hand=hand, pos=i)
                s_items[(t, hand, i)] = s
                n = NItem(time=t, hand=hand, pos=i)
                n_items[(t, hand, i)] = n
    print(max_time)
    # Génération des couleurs
    colors["false"] = 1
    colors["true"] = 2
    k = 3
    for ball in balls:
        colors[ball] = k
        k += 1
    # Génération des lignes
    for t in range(len(throws)):
        for throw in throws[t]:
            for hand in range(nb_hands):
                for flying_time in range(1, min(H, throw.max_height) + 1):
                    if flying_time in fflying_time:
                        continue
                    row: List[Union[Item, Tuple[Item, int]]] = \
                        [x_items[(throw, hand, flying_time)], l_items[throw]]
                    if not multiple_throws:
                        row.append(d_items[(t + throw.max_height - flying_time, hand)])
                    # if flying_time == throw.max_height:
                    #     row.append(i_items[(t, hand, flying_time)])
                    for fmulti in fmultiplex[flying_time]:
                        row.append(m_items[(t + throw.max_height - flying_time,
                                   hand, fmulti)])
                    # for fnext in f2seqs[flying_time]:
                    #     row.append(i_items[(t + 1, hand, fnext)])
                    # for t1 in range(t, t + throw.max_height - flying_time + 1):
                    #     row.append(w_items[(t1, hand)])

                    # On garde ça pour l'instant ...
                    row.append(u_items[(throw.ball, throw.time, hand)])
                    if flying_time == 1:
                        row.append(u_items[(throw.ball,
                                            throw.time + throw.max_height,
                                            hand)])
                    row.append((p_items[(t + throw.max_height - flying_time,
                                         hand, 0)],
                                colors[ball]))
                    row.append((s_items[(t + throw.max_height - flying_time,
                                         hand, 0)],
                                colors["true"]))
                    row.append(n_items[(t + throw.max_height - flying_time,
                                        hand, 0)])
                    for t1 in range(t + throw.max_height - flying_time + 1, t + throw.max_height):
                        row.append(b_items[(t1, throw.ball)])
                        row.append((f_items[(t1, throw.ball)], colors["true"]))
                    # row.append((error, colors["false"]))
                    rows.append(row)
    for t in range(max_time + 1):
        for hand in range(nb_hands):
            # Génération des lignes des configurations autorisées
            for lim in range(0, K + 1):
                row = [c_items[(t, hand)]]
                for i in range(0, K):
                    if i < lim:
                        row.append((s_items[(t, hand, i)], colors["true"]))
                    else:
                        row.append((s_items[(t, hand, i)], colors["false"]))
                # row.append((error, colors["true"]))
                rows.append(row)
            # Génération des lignes de choix des configurations
            for i in range(0, K):
                for ball in balls:
                    rows.append([
                        b_items[(t, ball)],
                        n_items[(t, hand, i)],
                        (p_items[(t, hand, i)], colors[ball]),
                        (s_items[(t, hand, i)], colors["true"]),
                        (f_items[(t, ball)], colors["false"])
                    ])
                    rows.append([
                        b_items[(t, ball)],
                        (f_items[(t, ball)], colors["true"])
                    ])
                    rows.append([
                        n_items[(t, hand, i)],
                        (s_items[(t, hand, i)], colors["false"])
                    ])

    colors_list: List[str] = ["" for i in range(k)]
    for clr, i in colors.items():
        colors_list[i] = clr

    return ExactCoverInstance(prim_items=list(x_items.values())
                              + list(l_items.values())
                              + list(m_items.values())
                              + list(d_items.values())
                              + list(u_items.values())
                              + list(b_items.values())
                              + list(c_items.values())
                              + list(n_items.values()),
                              sec_items=list(p_items.values())
                              + list(s_items.values())
                              + list(f_items.values()),
                              colors=colors_list,
                              rows=rows,
                              max_time=max_time,
                              nb_hands=nb_hands,
                              balls=balls)


def solve_exact_cover_with_milp(ec_instance: ExactCoverInstance,
                                optimize: bool = False) \
        -> ExactCoverSolution:
    p = MixedIntegerLinearProgram(maximization=True)

    # Calcul, pour chaque colonne, des lignes qui ont un élément dans cette
    # colonne
    d: Dict[Union[Item, Tuple[Item, int]],
            List[int]] \
        = {item: [] for item in ec_instance.x_items + ec_instance.l_items
            + ec_instance.w_items + ec_instance.i_items
            + ec_instance.m_items + ec_instance.d_items
            + ec_instance.u_items}
    for i in range(len(ec_instance.rows)):
        row = ec_instance.rows[i]
        for item in row:
            d[item].append(i)

    # Dictionnaire pour stocker les expressions permettant de calculer les
    # variables D(t, m)
    d_expr = {}

    max_expr = 0
    min_expr = 0
    min_high = 0

    # Génération de l'instance de MILP
    x = p.new_variable(binary=True)
    for item in ec_instance.x_items:
        if len(d[item]) > 0:
            rows_vars = [x[i] for i in d[item]]
            if item.flying_time in {3, 4, 5}:  # Maximisation des lancers 3/4/5
                max_expr += sum(rows_vars)
            elif item.flying_time in {6, 7}:  # Minimisation des lancers 6/7
                min_expr += sum(rows_vars)
                min_high += len(rows_vars)
            p.add_constraint(ec_instance.x_items_bounds[0]
                             <= sum(rows_vars)
                             <= ec_instance.x_items_bounds[1])
    for item in ec_instance.l_items:
        if len(d[item]) > 0:
            rows_vars = [x[i] for i in d[item]]
            p.add_constraint(ec_instance.l_items_bounds[0]
                             <= sum(rows_vars)
                             <= ec_instance.l_items_bounds[1])
    for item in ec_instance.w_items:
        if len(d[item]) > 0:
            rows_vars = [x[i] for i in d[item]]
            p.add_constraint(ec_instance.w_items_bounds[0]
                             <= sum(rows_vars)
                             <= ec_instance.w_items_bounds[1])
    for item in ec_instance.i_items:
        if len(d[item]) > 0:
            rows_vars = [x[i] for i in d[item]]
            p.add_constraint(ec_instance.i_items_bounds[0]
                             <= sum(rows_vars)
                             <= ec_instance.i_items_bounds[1])
    for item in ec_instance.m_items:
        if len(d[item]) > 0:
            rows_vars = [x[i] for i in d[item]]
            p.add_constraint(ec_instance.m_items_bounds[item.multiplex][0]
                             <= sum(rows_vars)
                             <= ec_instance.m_items_bounds[item.multiplex][1])
    for item in ec_instance.d_items:
        if len(d[item]) > 0:
            rows_vars = [x[i] for i in d[item]]
            dvar = sum(rows_vars)
            d_expr[(item.time, item.hand)] = dvar
            p.add_constraint(ec_instance.d_items_bounds[0]
                             <= dvar
                             <= ec_instance.d_items_bounds[1])
        else:
            dvar = 0
            d_expr[(item.time, item.hand)] = dvar
    for item in ec_instance.u_items:
        if len(d[item]) > 0:
            row_vars = [x[i] for i in d[item]]
            p.add_constraint(ec_instance.u_items_bounds[0]
                             <= sum(row_vars)
                             <= ec_instance.u_items_bounds[1])

    if optimize:
        # Minimisation du nombre de lancers en même temps depuis des mains
        # différentes
        # a = p.new_variable(binary=True)
        # for t in range(ec_instance.max_time + 1):
        #     sum_dvar = 0
        #     for h in range(ec_instance.nb_hands):
        #         dvar = d_expr[(t, h)]
        #         sum_dvar += dvar
        #     p.add_constraint(a[t] >= (sum_dvar - 1) / ec_instance.nb_hands)
        # p.set_objective(sum([a[t] for t in range(ec_instance.max_time + 1)]))

        # Optimisation du score lié au jonglage
        p.set_objective(max_expr + min_high - min_expr)

    # Résolution
    p.solve()
    selected_rows = p.get_values(x)

    return ExactCoverSolution(max_time=ec_instance.max_time,
                              nb_hands=ec_instance.nb_hands,
                              balls=ec_instance.balls,
                              rows=[ec_instance.rows[i]
                                    for i in selected_rows if selected_rows[i] == 1.0])


def dlx_solver_instance(ec_instance: ExactCoverInstance) -> DLXM:
    dlx = DLXM()

    primary = {}
    secondary = dlx.new_variable(secondary=True)
    vars = {}
    for item in ec_instance.prim_items:
        if item.bounds not in vars:
            vars[item.bounds] = dlx.new_variable(item.bounds[0], item.bounds[1])
        primary[item] = vars[item.bounds][item]

    for row in ec_instance.rows:
        row_primary = []
        row_secondary = []
        for item in row:
            if isinstance(item, Item):
                row_primary.append(primary[item])
            else:
                it, clr = item
                row_secondary.append((secondary[it], clr))
        dlx.add_row(row_primary, row_secondary)

    return dlx


def all_solutions_with_dlx(ec_instance: ExactCoverInstance) -> List[ExactCoverSolution]:
    dlx = dlx_solver_instance()

    sols_selected_rows = dlx.all_solutions()
    sols = []
    for selected_rows in sols_selected_rows:
        rows = []
        for i in selected_rows:
            rows.append(dlx.row_obj(i))
        sols.append(ExactCoverSolution(max_time=ec_instance.max_time,
                                       nb_hands=ec_instance.nb_hands,
                                       balls=ec_instance.balls,
                                       rows=rows))
    return sols


def get_solution_with_dlx(ec_instance: ExactCoverInstance) -> List[ExactCoverSolution]:
    dlx = dlx_solver_instance(ec_instance)

    sol = dlx.get_solution()
    rows = []
    for i in sol:
        rows.append(dlx.row_obj(i))
    return ExactCoverSolution(max_time=ec_instance.max_time,
                              nb_hands=ec_instance.nb_hands,
                              balls=ec_instance.balls,
                              rows=rows)


def juggling_sol_to_simulator(sol):
    hand: List[Dict[str, int]] = [{} for t in range(sol.max_time + 1)]
    throws: List[List[List[Tuple(str, int, int)]]] = \
        [[[] for t in range(sol.max_time + 1)] for h in range(sol.nb_hands)]

    for row in sol.rows:
        for item in row:
            if isinstance(item, XItem):
                for t in range(item.throw.max_height - item.flying_time + 1):
                    hand[item.throw.time + t][item.throw.ball] = item.hand
    for row in sol.rows:
        for item in row:
            if isinstance(item, XItem):
                ball = item.throw.ball
                land_time = item.throw.time + item.throw.max_height
                throw_time = land_time - item.flying_time
                src_hand = item.hand
                dst_hand = \
                    hand[land_time][ball] if ball in hand[land_time] else 1 - src_hand
                throws[src_hand][throw_time] \
                    .append((ball,
                             dst_hand,
                             item.flying_time))
    return throws


# ============================================================================ #
#                                                                              #
#     FONCTIONS DE D'AFFICHAGE EN TEXTE DE LA SÉQUENCE DE JONGLAGE OBTENUE     #
#                    EN RESULTAT DE L'ALGORITHME                               #
#                                                                              #
# ============================================================================ #


def print_juggling_solution(sol):
    for row in sol.rows:
        for item in row:
            if isinstance(item, XItem):
                print("{} - {} : main {} ({} temps) --> {} temps"
                      .format(str(item.throw.time), item.throw.ball, item.hand,
                              item.throw.max_height - item.flying_time,
                              item.flying_time))


def print_juggling(sol):
    in_hand: List[List[Set[str]]] = [[set() for h in range(sol.nb_hands)]
                                     for t in range(sol.max_time + 1)]
    hand: List[Dict[str, int]] = [{} for t in range(sol.max_time + 1)]
    throws: List[List[Tuple[str, int]]] = [[] for t in range(sol.max_time + 1)]

    for row in sol.rows:
        for item in row:
            if isinstance(item, XItem):
                for t in range(item.throw.max_height - item.flying_time + 1):
                    in_hand[item.throw.time + t][item.hand].add(item.throw.ball)
                    hand[item.throw.time + t][item.throw.ball] = item.hand
    for row in sol.rows:
        for item in row:
            if isinstance(item, XItem):
                throws[item.throw.time + item.throw.max_height - item.flying_time] \
                    .append((item.throw.ball, item.flying_time))
    max_hand_width = [0 for i in range(sol.nb_hands)]
    for t in range(sol.max_time):
        for i in range(sol.nb_hands):
            h = in_hand[t][i]
            s = (str(h) if len(h) > 0 else "{}") + " "
            if len(s) > max_hand_width[i]:
                max_hand_width[i] = len(s)
    max_hands_width = sum(max_hand_width)
    for t in range(sol.max_time):
        s = ""
        for i in range(sol.nb_hands):
            h = in_hand[t][i]
            s1 = (str(h) if len(h) > 0 else "{}") + " "
            s += ("{:^" + str(max_hand_width[i]) + "}").format(s1)
        s += ": "
        if len(throws[t]) > 0:
            ball, flying_time = throws[t][0]
            s += "{} -- {} --> {}" \
                 .format(ball, flying_time,
                         hand[t + flying_time][ball]
                         if ball in hand[t + flying_time] else "?")
            print(s)
            for i in range(1, len(throws[t])):
                ball, flying_time = throws[t][i]
                print(" " * (max_hands_width + 2), end="")
                print("{} -- {} --> {}"
                      .format(ball, flying_time,
                              hand[t + flying_time][ball]
                              if ball in hand[t + flying_time] else "?"))
        else:
            print(s)


# ============================================================================ #
#                                                                              #
# FONCTIONS DE GÉNÉRATION DE LATEX POUR AFFICHER LA TABLE ENTIÈRE REPRÉSENTANT #
#                L'INSTANCE DE EXACT COVER GENERALISÉ                          #
#                                                                              #
# ============================================================================ #


def latex_x_items_columns(x_items):
    s = ""
    d = {}
    cnt = 0
    for x in x_items:
        d[x] = cnt
        s += x.latex() + " & "
        cnt += 1
    return s, d


def latex_l_items_columns(l_items):
    s = ""
    d = {}
    cnt = 0
    for u in l_items:
        d[u] = cnt
        s += u.latex() + " & "
        cnt += 1
    return s, d


def latex_w_items_columns(w_items):
    s = ""
    d = {}
    cnt = 0
    for w in w_items:
        d[w] = cnt
        s += w.latex() + " & "
        cnt += 1
    return s, d


def latex_i_items_columns(i_items):
    s = ""
    d = {}
    cnt = 0
    for i in i_items:
        d[i] = cnt
        s += i.latex() + " & "
        cnt += 1
    return s, d


def latex_m_items_columns(m_items):
    s = ""
    d = {}
    cnt = 0
    for m in m_items:
        d[m] = cnt
        s += m.latex() + " & "
        cnt += 1
    return s, d


def latex_rows_full_table(dx, dl, dw, di, dm, rows):
    x_offset = 0
    l_offset = x_offset + len(dx)
    w_offset = l_offset + len(dl)
    i_offset = w_offset + len(dw)
    m_offset = i_offset + len(di)
    row_len = m_offset + len(dm)

    rows_latex = ""

    for row in rows:
        row_elems = ["" for i in range(row_len)]
        for item in row:
            if isinstance(item, XItem):
                row_elems[x_offset + dx[item]] = r"\bullet"
            elif isinstance(item, LItem):
                row_elems[l_offset + dl[item]] = r"\bullet"
            elif isinstance(item, WItem):
                row_elems[w_offset + dw[item]] = r"\bullet"
            elif isinstance(item, IItem):
                row_elems[i_offset + di[item]] = r"\bullet"
            elif isinstance(item, MItem):
                row_elems[m_offset + dm[item]] = r"\bullet"
        rows_latex += " & ".join(row_elems) + r"\\"

    return rows_latex


def latex_full_table(ec_instance: ExactCoverInstance):
    sx, dx = latex_x_items_columns(ec_instance.x_items)
    sl, dl = latex_l_items_columns(ec_instance.l_items)
    sw, dw = latex_w_items_columns(ec_instance.w_items)
    si, di = latex_i_items_columns(ec_instance.i_items)
    sm, dm = latex_m_items_columns(ec_instance.m_items)

    nb_cols = len(ec_instance.x_items) + len(ec_instance.l_items) \
        + len(ec_instance.w_items) + len(ec_instance.i_items) \
        + len(ec_instance.m_items)

    s = r"\begin{array}{" + "|" + "c|" * nb_cols + "}"
    s += r"\hline "
    s += sx + sl + sw + si + sm
    s += r"\hline\hline "
    s += latex_rows_full_table(dx, dl, dw, di, dm, ec_instance.rows)
    s += r"\hline "
    s += r"\end{array}"

    return s


def generate_full_table(ec_instance: ExactCoverInstance):
    ltx = latex_full_table(ec_instance)
    doc = Document('full_table',
                   documentclass='standalone',
                   document_options={
                       'border': '2.5cm'
                   })
    ltxs = '$' + ltx + '$'
    doc.append(NoEscape(ltxs))
    doc.generate_pdf()


def item_key(ec_instance: ExactCoverInstance):
    items = ec_instance.x_items + ec_instance.l_items + ec_instance.w_items \
        + ec_instance.i_items + ec_instance.m_items

    return lambda x: items.index(x)


def latex_table(ec_instance: ExactCoverInstance):
    nb_cols = max([len(row) for row in ec_instance.rows])
    key = item_key(ec_instance)

    s = r"\begin{array}{" + "c" * nb_cols + "}"
    s += r"\hline "
    for row in ec_instance.rows:
        sorted_row = sorted(row, key=key)
        row_latex = sorted_row[0].latex()
        for i in range(1, len(sorted_row)):
            row_latex += " & " + sorted_row[i].latex()
        s += row_latex + r"\\"
    s += r"\hline "
    s += r"\end{array}"

    return s


def generate_table(ec_instance):
    ltx = latex_table(ec_instance)
    doc = Document('table',
                   documentclass='standalone',
                   document_options={
                       'border': '2.5cm'
                   })
    ltxs = '$' + ltx + '$'
    doc.append(NoEscape(ltxs))
    doc.generate_pdf()
