from recordclass import StructClass
from typing import List, Dict, Tuple, Union, Set, Any, Optional
from sage.all import MixedIntegerLinearProgram
from DLX.dlxm import DLXM
from queue import Queue

import cppyy

from pylatex import Document
from pylatex.utils import NoEscape

import modele
import ipywidgets as ipw
import pythreejs

_maximize_model = """
for (auto i : {{ {} }})
    if (!dlx->is_covered(i))
        return i;
"""

_choose_model = """
long int choose_{}(DLX_M::DLX* dlx) {{
    long int i = dlx->item(0).rlink;
    long int p;

    for (p = i; p != 0; p = dlx->item(p).rlink)
        if (dlx->option(p).tl == 0)
            return p;
        // if (dlx->option(p).tl == 0 && dlx->option(p).tl < dlx->option(i).tl)
        //     i = p;

    // if (dlx->option(i).tl == 0) return i;

    {}

    for (p = i; p != 0; p = dlx->item(p).rlink)
        if (dlx->option(p).tl < dlx->option(i).tl)
            i = p;

    return i;
}}
"""

_choose_counter = 0


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


class WItem(Item):
    def __init__(self, max_weight, time, hand):
        super().__init__("w", {
            "time": time,
            "hand": hand
        }, ["time", "hand"], low=0, high=max_weight)


class DItem(Item):
    def __init__(self, time, hand, multiplex):
        super().__init__("d", {
            "time": time,
            "hand": hand,
            "multiplex": multiplex
        }, ["time", "hand", "multiplex"], low=0, high=1)


class MItem(Item):
    def __init__(self, time, hand, multiplex):
        super().__init__("m", {
            "time": time,
            "hand": hand,
            "multiplex": multiplex
        }, ["time", "hand", "multiplex"])


class CItem(Item):
    def __init__(self, time, hand):
        super().__init__("c", {
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


class ExactCoverInstance(StructClass):
    # max_time: int = 0
    # nb_hands: int = 1
    # max_weight: int = 1
    # balls: Set[str] = set()

    params: Dict[str, Any] = {}

    prim_items: List[Item] = []
    sec_items: List[Item] = []

    colors: List[Tuple[int, int]] = []

    rows: List[List[Union[Item, Tuple[Item, int]]]] = []


class ExactCoverSolution(StructClass):
    params: Dict[str, Any] = {}

    rows: List[List[Union[Item, Tuple[Item, Tuple[Item, int]]]]] = []


class ImpossibleHandPosition(Exception):
    pass


class FinalThrow(StructClass):
    ball: str
    time: int
    time_in_hand: int
    flying_time: int
    src_hand: int
    dst_hand: int
    full_time: int


class JugglingSolution(StructClass):
    params: Dict[str, Any] = {}
    throws: List[FinalThrow] = []


def throws_to_extended_exact_cover(balls: Set[str], throws: List[List[Throw]],
                                   nb_hands: int, H: int, max_weight: int,
                                   forbidden_multiplex: List[Tuple[int, ]],
                                   multiple_throws: bool) \
        -> ExactCoverInstance:
    max_time = 0
    x_items = {}
    l_items = {}
    w_items = {}
    d_items = {}
    m_items = {}
    # m_items_bounds = {}
    c_items = {}
    u_items = {}

    colors = {}
    fmultiplex: Dict[int, List[Tuple[int, ]]] = {i: [] for i in range(1, H + 1)}
    fflying_time = []
    rows = []
    # Remplissage du dictionnaire des lancers multiplex interdits
    for fm in forbidden_multiplex:
        if len(fm) == 2:
            if fm[0] == fm[1]:
                fmultiplex[fm[0]].append(fm)
            else:
                fmultiplex[fm[0]].append(fm)
                fmultiplex[fm[1]].append(fm)
        # for i in fm:
        #     fmultiplex[i].append(fm)
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
                for flying_time in range(min(H, throw.max_height) + 1):
                    x = XItem(throw=throw, hand=hand, flying_time=flying_time)
                    x_items[(throw, hand, flying_time)] = x
    # Génération des items w, D, M, C et U
    for t in range(max_time + 1):
        for hand in range(nb_hands):
            w = WItem(max_weight=max_weight, time=t, hand=hand)
            w_items[(t, hand)] = w

            c = CItem(time=t, hand=hand)
            c_items[(t, hand)] = c

            for f in forbidden_multiplex:
                if len(f) == 1 and f[0] not in fflying_time:
                    fflying_time.append(f[0])
                elif len(f) == 1:
                    pass
                elif len(f) == 2 and f[0] == f[1]:
                    d = DItem(time=t, hand=hand, multiplex=f)
                    d_items[(t, hand, f)] = d
                    # m = MItem(time=t, hand=hand, multiplex=f)
                    # m_items[(t, hand, f)] = m
                    # m_items_bounds[f] = (0, len(f) - 1)
                elif len(f) == 2:
                    m = MItem(time=t, hand=hand, multiplex=f)
                    m_items[(t, hand, f)] = m
                else:
                    raise Exception("Erreur: l'interdiction de lancers multiplex de taille > 2 n'est pas supportée.")

            for ball in balls:
                u = UItem(ball=ball, time=t, hand=hand)
                u_items[(ball, t, hand)] = u
    # Génération des couleurs
    # colors["false"] = 1
    # colors["true"] = 2
    k = 1
    for h in range(1, max_height + 1):
        colors[h] = k
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
                        row.append(c_items[(t + throw.max_height - flying_time, hand)])
                    for fmulti in fmultiplex[flying_time]:
                        if fmulti[0] == fmulti[1]:
                            row.append(d_items[(t + throw.max_height - flying_time,
                                                hand, fmulti)])
                        else:
                            row.append((m_items[(t + throw.max_height - flying_time,
                                                 hand, fmulti)],
                                        colors[flying_time]))
                    for t1 in range(t, t + throw.max_height - flying_time + 1):
                        row.append(w_items[(t1, hand)])

                    # On garde ça pour l'instant ...
                    row.append(u_items[(throw.ball, throw.time, hand)])
                    if flying_time == 1:
                        row.append(u_items[(throw.ball,
                                            throw.time + throw.max_height,
                                            hand)])
                    rows.append(row)

    colors_list: List[int] = [0 for i in range(k)]
    for h, clr in colors.items():
        colors_list[clr] = h

    return ExactCoverInstance(prim_items=list(x_items.values())  # type: ignore
                              + list(l_items.values())           # type: ignore
                              + list(w_items.values())           # type: ignore
                              + list(m_items.values())           # type: ignore
                              + list(c_items.values())           # type: ignore
                              + list(u_items.values())           # type: ignore
                              + list(d_items.values()),          # type: ignore
                              sec_items=list(m_items.values()),
                              colors=colors_list,
                              rows=rows,
                              params={
                                  'max_time': max_time,
                                  'max_weight': max_weight,
                                  'nb_hands': nb_hands,
                                  'balls': balls})


def solve_exact_cover_with_milp(ec_instance: ExactCoverInstance,
                                optimize: bool = False,
                                maximize: List[int] = []) \
        -> ExactCoverSolution:
    p = MixedIntegerLinearProgram(maximization=False)

    # Calcul, pour chaque colonne, des lignes qui ont un élément dans cette
    # colonne
    d_prim: Dict[Item, List[int]] \
        = {item: [] for item in ec_instance.prim_items}
    # d_sec: Dict[Tuple[Item, int], List[int]] \
    #     = {(item, clr): []
    #        for item in ec_instance.sec_items
    #        for clr in range(1, len(ec_instance.colors) + 1)}
    for i in range(len(ec_instance.rows)):
        row = ec_instance.rows[i]
        for item in row:
            if isinstance(item, Item):
                d_prim[item].append(i)
            # else:
            #     it, clr = item
            #     d_sec[(it, clr)].append(i)

    # Dictionnaire pour stocker les expressions permettant de calculer les
    # variables D(t, m)
    d_expr = {}

    # Génération des contraintes pour les éléments primaires
    x = p.new_variable(binary=True)
    for item in ec_instance.prim_items:
        if len(d_prim[item]) > 0:
            rows_vars = [x[i] for i in d_prim[item]]
            # if isinstance(item, XItem):
            #     if item.flying_time in {3, 4}:  # Maximisation des lancers 3/4
            #         max_expr += sum(rows_vars)
            #     elif item.flying_time in {5, 6, 7}:  # Minimisation des lancers 5/6/7
            #         min_expr += sum(rows_vars)
            #         min_high += len(rows_vars)
            # elif isinstance(item, CItem):
            #     d_expr[(item.time, item.hand)] = sum(rows_vars)
            p.add_constraint(item.bounds[0]
                             <= sum(rows_vars)
                             <= item.bounds[1])
        # elif isinstance(item, CItem):
        #     d_expr[(item.time, item.hand)] = 0

    # Génération des contraintes pour les éléments secondaires
    # a = p.new_variable(binary=True)
    # for item in ec_instance.sec_items:
    #     s = 0
    #     for clr in range(1, len(ec_instance.colors)):
    #         s += a[(item, clr)]
    #         for r in d_sec[(item, clr)]:
    #             p.add_constraint(a[(item, clr)] >= x[r])
    #     p.add_constraint(s <= 1)

    if optimize:
        # Minimisation du nombre de lancers en même temps depuis des mains
        # différentes
        # a = p.new_variable(binary=True)
        # for t in range(ec_instance.params['max_time'] + 1):
        #     sum_dvar = 0
        #     for h in range(ec_instance.params['nb_hands']):
        #         dvar = d_expr[(t, h)]
        #         sum_dvar += dvar
        #     p.add_constraint(a[t] >= (sum_dvar - 1) / ec_instance.params['nb_hands'])
        # p.set_objective(sum([a[t] for t in range(ec_instance.params['max_time'] + 1)]))

        # Génération de la fonction à optimiser

        max_throws = 0
        min_throws = 0
        min_throws_high = 0

        multiplex_throws = 0

        o = p.new_variable(binary=True)
        for item in ec_instance.prim_items:
            if len(d_prim[item]) > 0:
                rows_vars = [x[i] for i in d_prim[item]]
                if isinstance(item, XItem):
                    # minimisation de certains lancers
                    # (i.e. maximisation des autres)
                    if item.flying_time in maximize:
                        max_throws += sum(rows_vars)
                    elif item.flying_time not in maximize:
                        min_throws += sum(rows_vars)
                        min_throws_high += len(rows_vars)
                elif isinstance(item, WItem):
                    # minimisation du nombre de lancers multiplex
                    # (au sens du livre, i.e. les lancers où il y a plusieurs
                    #  balles dans la main, même si toutes ne sont pas lancées)
                    p.add_constraint(o[(item.time, item.hand)]
                                     >= (sum(rows_vars) - 1) / ec_instance.params['max_weight'])
                    multiplex_throws += o[(item.time, item.hand)]

        # Optimisation du score
        p.set_objective(min_throws_high * multiplex_throws + min_throws)

        # Optimisation du score lié au jonglage
        # p.set_objective(max_expr + min_high - min_expr)

    # Résolution
    p.solve()
    selected_rows = p.get_values(x)

    return ExactCoverSolution(rows=[ec_instance.rows[i]
                                    for i in selected_rows if selected_rows[i] == 1.0],
                              params=ec_instance.params)


def exact_cover_solution_to_juggling_solution(sol: ExactCoverSolution):
    max_time = sol.params['max_time']
    nb_hands = sol.params['nb_hands']
    max_weight = sol.params['max_weight']
    in_hand: List[List[Set[str]]] = [[set() for _ in range(nb_hands)]
                                     for _ in range(max_time + 1)]
    hand: List[Dict[str, int]] = [{} for _ in range(max_time + 1)]

    for row in sol.rows:
        for item in row:
            if isinstance(item, XItem):
                for d in range(item.throw.max_height - item.flying_time + 1):
                    in_hand[item.throw.time + d][item.hand].add(item.throw.ball)
                    hand[item.throw.time + d][item.throw.ball] = item.hand
    for row in sol.rows:
        for item in row:
            if isinstance(item, XItem):
                # La balle n'est pas relancée i.e. c'est le dernier lancer et
                # il faut décider vers quelle main lancer la balle
                if item.throw.ball not in hand[item.throw.time + item.throw.max_height]:
                    for h in range(nb_hands):
                        if item.flying_time > 1 or h != hand[item.throw.time][item.throw.ball]:
                            for t1 in range(item.throw.time + item.throw.max_height, max_time + 1):
                                if len(in_hand[t1][h]) + 1 > max_weight:  # la main contient déjà trop de balles
                                    if h == nb_hands - 1:  # aucune main ne peut réceptionner la balle -> erreur
                                        raise ImpossibleHandPosition()
                                    break  # on cherche une autre main
                            else:  # on a trouvé une main pour réceptionner la balle
                                for t1 in range(item.throw.time + item.throw.max_height, max_time + 1):
                                    in_hand[t1][h].add(item.throw.ball)
                                    hand[t1][item.throw.ball] = h
    final_throws = []
    for row in sol.rows:
        for item in row:
            if isinstance(item, XItem):
                final_throws.append(FinalThrow(ball=item.throw.ball,
                                               time=item.throw.time,
                                               time_in_hand=item.throw.max_height - item.flying_time,
                                               flying_time=item.flying_time,
                                               src_hand=item.hand,
                                               dst_hand=hand[item.throw.time + item.throw.max_height][item.throw.ball],
                                               full_time=item.throw.max_height))
    return JugglingSolution(params=sol.params,
                            throws=final_throws)


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

    dlx.compile()

    return dlx


def all_solutions_with_dlx(ec_instance: ExactCoverInstance,
                           maximize: List[int] = []) \
        -> List[ExactCoverSolution]:

    cppyy.cppdef(_choose_model)

    dlx = dlx_solver_instance(ec_instance)
    dlx.set_choose_function(cppyy.gbl.choose)

    sols_selected_rows = dlx.all_solutions()
    sols = []
    for selected_rows in sols_selected_rows:
        rows = []
        for i in selected_rows:
            rows.append(dlx.row_obj(i))
        sols.append(ExactCoverSolution(params=ec_instance.params,
                                       rows=rows))
    return sols


def check_hand_position(sol: ExactCoverSolution):
    max_time = sol.params['max_time']
    nb_hands = sol.params['nb_hands']
    max_weight = sol.params['max_weight']
    in_hand: List[List[Set[str]]] = [[set() for _ in range(nb_hands)]
                                     for _ in range(max_time + 1)]
    hand: List[Dict[str, int]] = [{} for _ in range(max_time + 1)]
    throws: List[List[Set[str]]] = [[set() for _ in range(nb_hands)]
                                    for _ in range(max_time + 1)]
    catch: List[List[Optional[str]]] = [[None for _ in range(nb_hands)]
                                        for _ in range(max_time + 1)]
    locked: List[List[bool]] = [[False for _ in range(nb_hands)]
                                for _ in range(max_time + 1)]

    for row in sol.rows:
        for item in row:
            if isinstance(item, XItem):
                for d in range(item.throw.max_height - item.flying_time + 1):
                    in_hand[item.throw.time + d][item.hand].add(item.throw.ball)
                    hand[item.throw.time + d][item.throw.ball] = item.hand
                throws[item.throw.time + item.throw.max_height - item.flying_time][item.hand].add(item.throw.ball)
                catch[item.throw.time][item.hand] = item.throw.ball
                if item.throw.time > 0 or item.flying_time == item.throw.max_height:
                    locked[item.throw.time][item.hand] = True
                    locked[item.throw.time + item.throw.max_height - item.flying_time][item.hand] = True
    for row in sol.rows:
        for item in row:
            if isinstance(item, XItem):
                # La balle n'est pas relancée i.e. c'est le dernier lancer et
                # il faut décider vers quelle main lancer la balle
                if item.throw.ball not in hand[item.throw.time + item.throw.max_height]:
                    for h in range(nb_hands):
                        if item.flying_time > 1 or h != hand[item.throw.time][item.throw.ball]:
                            for t1 in range(item.throw.time + item.throw.max_height, max_time + 1):
                                if len(in_hand[t1][h]) + 1 > max_weight:  # la main contient déjà trop de balles
                                    if h == nb_hands - 1:  # aucune main ne peut réceptionner la balle -> erreur
                                        raise ImpossibleHandPosition()
                                    break  # on cherche une autre main
                            else:  # on a trouvé une main pour réceptionner la balle
                                locked[item.throw.time + item.throw.max_height][h] = True
                                for t1 in range(item.throw.time + item.throw.max_height, max_time + 1):
                                    in_hand[t1][h].add(item.throw.ball)
                                    hand[t1][item.throw.ball] = h

    for h in range(nb_hands):
        q: Queue = Queue()
        # Configuration initiale de la main
        n = len(in_hand[0][h])
        balls_in_hand = list(in_hand[0][h])
        for d in range(n):
            pos = {}
            for i in range(n):
                pos[balls_in_hand[i]] = (i + d) % n
            q.put((0, pos))
        # Recherche de solution
        while not q.empty():
            (t, pos) = q.get()
            if locked[t][h]:  # un lancer ou une réception s'effectue ici
                nb_throws = len(throws[t][h])
                l = [False for _ in range(nb_throws)]
                for b in throws[t][h]:
                    if pos[b] >= nb_throws:
                        break
                    l[pos[b]] = True
                if False not in l:
                    if t + 1 > max_time:
                        return True
                    pos1 = {}  # nouvelle position pour la main à l'instant t + 1
                    # Décalage des balles non lancées
                    for b in pos:
                        if b not in throws[t][h]:
                            pos1[b] = pos[b] - nb_throws
                    # Réception ou non d'une balle
                    if catch[t + 1][h] is not None:
                        pos1[catch[t + 1][h]] = len(pos1)
                    q.put((t + 1, pos1))
            else:  # aucun lancer ou réception
                pos1 = {}
                n = len(pos)
                for b in pos:
                    pos1[b] = (pos[b] - 1) % n
                # Réception ou non d'une balle au temps suivant
                if catch[t + 1][h] is not None:
                    pos[catch[t + 1][h]] = len(pos)
                    pos1[catch[t + 1][h]] = len(pos1)
                q.put((t + 1, pos))   # aucun échange de balles dans la main
                q.put((t + 1, pos1))  # échange de balles dans la main
        return False


def get_solution_with_dlx(ec_instance: ExactCoverInstance,
                          maximize: List[int] = []) \
        -> ExactCoverSolution:

    global _choose_counter
    _choose_counter += 1

    dlx = dlx_solver_instance(ec_instance)

    maximized_xvars: List[int] = []
    pvar = dlx.primary_variables(0, 1)
    if pvar is None:
        raise Exception("No x variables.")
    for item in ec_instance.prim_items:
        if isinstance(item, XItem):
            if item.flying_time in maximize:
                maximized_xvars.append(pvar[item].get_id())

    if maximized_xvars == []:
        cppyy.cppdef(_choose_model.format(str(_choose_counter), ""))
    else:
        max = _maximize_model.format(", ".join([str(x) for x in maximized_xvars]))
        cppyy.cppdef(_choose_model.format(str(_choose_counter), max))

    dlx.set_choose_function(getattr(cppyy.gbl, 'choose_' + str(_choose_counter)))

    sol = dlx.search()

    rows = []
    for i in sol:
        rows.append(dlx.row_obj(i))
    ec_sol = ExactCoverSolution(params=ec_instance.params,
                                rows=rows)

    while not check_hand_position(ec_sol):
        sol = dlx.search()
        rows = []
        for i in sol:
            rows.append(dlx.row_obj(i))
        ec_sol = ExactCoverSolution(params=ec_instance.params,
                                    rows=rows)
    return ec_sol


def juggling_sol_to_simulator(sol: JugglingSolution, colors):
    # hand: List[Dict[str, int]] = [{} for t in range(sol.params['max_time'] + 1)]
    throws: List[List[List[Tuple[str, int, int]]]] = \
        [[[] for t in range(sol.params['max_time'] + 1)]
         for h in range(sol.params['nb_hands'])]

    for throw in sol.throws:
        throws[throw.src_hand][throw.time + throw.time_in_hand] \
            .append((throw.ball,
                     throw.dst_hand,
                     throw.flying_time))

    balls = []
    j = 0
    for ball in sol.params['balls']:
        balls.append({"color": colors[j], "tone": ball, "name": ball})
        j += 1

    return balls, throws


def solve_and_print(music, nb_hands, max_height, max_weight, forbidden_multiplex, method="DLX", optimize=True, maximize=[]):
    balls, throws = music_to_throws(music)
    ec_instance = throws_to_extended_exact_cover(balls, throws, nb_hands, max_height, max_weight,
                                                 forbidden_multiplex, True)
    sol = None
    if method == "DLX":
        sol = get_solution_with_dlx(ec_instance, maximize)
    elif method == "MILP":
        sol = solve_exact_cover_with_milp(ec_instance, optimize, maximize)
    if len(sol) == 0:
        raise RuntimeError("No solution.")
    jsol = exact_cover_solution_to_juggling_solution(sol)

    print_juggling(jsol)
    return jsol


def solve_and_simulate(music, nb_hands, max_height, max_weight, forbidden_multiplex, colors, sides, method="DLX", optimize=True, maximize=[], step=10):
    balls, throws = music_to_throws(music)
    ec_instance = throws_to_extended_exact_cover(balls, throws, nb_hands, max_height, max_weight,
                                                 forbidden_multiplex, True)
    sol = None
    if method == "DLX":
        sol = get_solution_with_dlx(ec_instance, maximize)
    elif method == "MILP":
        sol = solve_exact_cover_with_milp(ec_instance, optimize, maximize)
    if len(sol) == 0:
        raise RuntimeError("No solution.")
    jsol = exact_cover_solution_to_juggling_solution(sol)
    balls, pattern = juggling_sol_to_simulator(jsol, colors)

    model = modele.Model(balls, pattern)
    # slider = ipw.FloatSlider(min=0, max=40, step=0.05)
    play = ipw.Play(
        value=0,
        min=0,
        max=4000,
        step=step,
        interval=30,
        description="Press play",
        disabled=False
    )
    slider = ipw.IntSlider(min=0, max=4000)
    ipw.jslink((play, 'value'), (slider, 'value'))
    view = modele.View(model, sides)
    slider.observe(lambda change: view.update(change['new'] / 100, change['old'] / 100), names="value")
    return ipw.VBox([view.widget, ipw.HBox([play, slider])])


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


def juggling_to_formatted_str(sol: JugglingSolution):
    max_time = sol.params['max_time']
    in_hand: List[List[Set[str]]] = [[set() for _ in range(sol.params['nb_hands'])]
                                     for _ in range(max_time + 1)]
    hand: List[Dict[str, int]] = [{} for _ in range(max_time + 1)]
    throws: List[List[Tuple[str, int]]] = [[] for _ in range(max_time + 1)]
    last_throws: List[FinalThrow] = []

    for throw in sol.throws:
        for t in range(throw.time_in_hand + 1):
            in_hand[throw.time + t][throw.src_hand].add(throw.ball)
            hand[throw.time + t][throw.ball] = throw.src_hand
        for throw1 in last_throws:
            if throw.ball == throw1.ball and throw.time > throw1.time:
                last_throws.remove(throw1)
                last_throws.append(throw)
                break
        else:
            for throw1 in last_throws:
                if throw.ball == throw1.ball:
                    break
            else:
                last_throws.append(throw)
        throws[throw.time + throw.time_in_hand] \
            .append((throw.ball, throw.flying_time))
    for throw in last_throws:
        for t in range(throw.time + throw.full_time, max_time + 1):
            hand[t][throw.ball] = throw.dst_hand
            in_hand[t][throw.dst_hand].add(throw.ball)
    max_hand_width = [0 for i in range(sol.params['nb_hands'])]
    for t in range(max_time):
        for i in range(sol.params['nb_hands']):
            h = in_hand[t][i]
            s = (str(h) if len(h) > 0 else "{}") + " "
            if len(s) > max_hand_width[i]:
                max_hand_width[i] = len(s)
    max_hands_width = sum(max_hand_width)
    output = ""
    for t in range(max_time):
        s = ""
        for i in range(sol.params['nb_hands']):
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
            output += s + "\n"
            for i in range(1, len(throws[t])):
                ball, flying_time = throws[t][i]
                output += " " * (max_hands_width + 2)
                output += "{} -- {} --> {}" \
                    .format(ball, flying_time,
                            hand[t + flying_time][ball]
                            if ball in hand[t + flying_time] else "?") + "\n"
        else:
            output += s + "\n"
    return output


def print_juggling(sol: JugglingSolution):
    print(juggling_to_formatted_str(sol))
    return None


def display_interface():
    out = ipw.Output()

    l_inttext = ipw.Layout(width='100px')
    l_text = ipw.Layout(width='150px')
    l_simulation_text = ipw.Layout(width='400px')

    w_nb_hands = ipw.IntText(
        value=2,
        disabled=False,
        layout=l_inttext
    )
    w_max_weight = ipw.IntText(
        value=3,
        disabled=False,
        layout=l_inttext
    )
    w_max_height = ipw.IntText(
        value=5,
        disabled=False,
        layout=l_inttext
    )
    w_no_multiplex = ipw.Checkbox(
        value=False,
        disabled=False,
        indent=False
    )
    w_generate_forbidden_multiplex = ipw.Button(
        description='Générer',
        disabled=False,
        button_style='',
        icon='refresh'
    )
    w_forbidden_multiplex = ipw.SelectMultiple(
        options=[''],
        value=[],
        disabled=False,
    )
    w_forbidden_throws = ipw.Text(
        value='',
        placeholder='',
        disabled=False
    )

    def fill_forbidden_multiplex(args):
        nonlocal w_forbidden_multiplex
        old_options = w_forbidden_multiplex.options
        selected = w_forbidden_multiplex.value
        max_height = w_max_height.value
        options = []
        for i in range(1, max_height + 1):
            for j in range(i, max_height + 1):
                options.append(str(i) + ", " + str(j))
        w_forbidden_multiplex.options = options
        w_forbidden_multiplex.disabled = w_no_multiplex.value
        new_selected = []
        for s in selected:
            i = int(s.split(', ')[0])
            j = int(s.split(', ')[1])
            if i <= max_height and j <= max_height:
                new_selected.append(str(i) + ', ' + str(j))
        w_forbidden_multiplex.value = new_selected
        # logger.debug(old_options)
        if len(old_options) == 1:
            w_forbidden_multiplex.selected = ["1, 1", "1, 2", "1, 3", "1, 4", "1, 5"]
        out.clear_output()
        with out:
            display(ui)

    w_maximize = ipw.Text(
        value='',
        placeholder='',
        disabled=False
    )
    w_generate_hands = ipw.Button(
        description='Générer',
        disabled=False,
        button_style='',
        icon='refresh'
    )
    hands_constraints = {}
    w_hands_constraints = ipw.Accordion([])

    def fill_hand_constraints(args):
        nonlocal hands_constraints, w_hands_constraints
        max_weight_old = len(hands_constraints) + 1
        max_weight = w_max_weight.value
        if max_weight > max_weight_old:
            for k in range(max_weight_old + 1, max_weight + 1):
                w_throw = ipw.BoundedIntText(value=1, min=1, max=k, step=1, disabled=False, layout=l_text)
                w_catch = ipw.BoundedIntText(value=k, min=1, max=k, step=1, disabled=False, layout=l_text)
                w_perm = ipw.Text(value='', placeholder='', disabled=False, layout=l_text)
                hands_constraints[k] = {
                    'throw': w_throw,
                    'catch': w_catch,
                    'perm': w_perm,
                    'box': ipw.GridBox([
                        ipw.Label('Lancer :'), w_throw,
                        ipw.Label('Récupération :'), w_catch,
                        ipw.Label('Permutations :'), w_perm
                    ], layout=ipw.Layout(grid_template_columns="repeat(2, 100px)"))
                }
        else:
            for k in range(max_weight + 1, max_weight_old + 1):
                hands_constraints.pop(k)
        w_hands_constraints = ipw.Accordion([hands_constraints[k]['box'] for k in range(2, max_weight + 1)], layout=ipw.Layout(width='300px'))
        for k in range(2, max_weight + 1):
            w_hands_constraints.set_title(index=k - 2, title=str(k) + " mains")
        tab.children = [tab1, tab2, tab3()]
        out.clear_output()
        with out:
            display(ui)

    def tab3():
        return ipw.GridBox([
            ipw.Label('Contraintes sur les mains :'), w_generate_hands,
            ipw.Label(''), w_hands_constraints
        ], layout=ipw.Layout(grid_template_columns="repeat(2, 210px)"))
    tab1 = ipw.GridBox([
        ipw.Label('Nombre de mains :'), w_nb_hands,
        ipw.Label('Nombre maximal de balles dans une main :'), w_max_weight,
        ipw.Label('Hauteur maximale :'), w_max_height
    ], layout=ipw.Layout(grid_template_columns="repeat(2, 260px)"))
    tab2 = ipw.GridBox([
        ipw.Label('Maximiser les lancers :'), w_maximize,
        ipw.Label('Aucun lancer multiple :'), w_no_multiplex,
        ipw.Label('Lancers interdits :'), w_forbidden_throws,
        ipw.Label('Lancers multiples interdits :'), w_generate_forbidden_multiplex,
        ipw.VBox([
            ipw.Label('(maintenir Ctrl pour', layout=ipw.Layout(height='20px')),
            ipw.Label('sélectionner/désélectionner)', layout=ipw.Layout(height='20px'))]),
        w_forbidden_multiplex
    ], layout=ipw.Layout(grid_template_columns="repeat(2, 170px)"))

    tab = ipw.Tab(layout=ipw.Layout(width='550px', margin='0px 0px 10px 0px'))
    tab.children = [tab1, tab2, tab3()]
    tab.set_title(index=0, title="Général")
    tab.set_title(index=1, title="Lancers")
    tab.set_title(index=2, title="Mains")

    model = modele.Model({}, [[], []])
    play = ipw.Play(
        value=0,
        min=0,
        max=4000,
        step=5,
        interval=30,
        description="Press play",
        disabled=False
    )
    slider = ipw.IntSlider(min=0, max=4000)
    ipw.jslink((play, 'value'), (slider, 'value'))
    view = modele.View(model, [-1, -1, 1])
    slider.observe(lambda change: view.update(change['new'] / 100, change['old'] / 100), names="value")

    w_music = ipw.Textarea(
        value='[1 do] [2 do] [3 do] [4 re] [5 mi] [7 re] [9 do] [10 mi] [11 re] [12 re] [13 do]',
        placeholder='',
        description='',
        disabled=False,
        layout=ipw.Layout(width='475px', margin='0px 0px 10px 0px')
    )
    w_working = ipw.Label('Prêt')
    w_solve = ipw.Button(
        description='Résoudre les contraintes',
        disabled=False,
        button_style='',
        icon='check',
        layout=ipw.Layout(width='345px')
    )
    w_simulate = ipw.Button(
        description='Simuler',
        disabled=True,
        button_style='',
        icon='check',
        layout=ipw.Layout(width='200px')
    )
    w_step = ipw.IntText(
        value=5,
        disabled=False,
        layout=l_inttext
    )
    w_sides = ipw.Text(
        value='-1, 1',
        placeholder='',
        disabled=False,
        layout=l_simulation_text
    )
    w_colors = ipw.Text(
        value='blue, red, green, yellow, purple, cyan, magenta',
        placeholder='',
        disabled=False,
        layout=l_simulation_text
    )
    w_method = ipw.RadioButtons(
        options=['Programmation Linéaire (rapide, ne respecte pas les contraintes sur les mains)',
                 'Dancing Links (lent, respecte les contraintes sur les mains)'],
        description='',
        disabled=False,
        layout={'width': 'max-content'}
    )
    w_result = ipw.Textarea(
        value='',
        placeholder='',
        disabled=True,
        layout={'width': '516px', 'height': '553px'}
    )

    # balls = {}
    # pattern = [[], []]
    jsol = None
    tab_res_sim = ipw.Tab()

    def ui_view(view, play, slider):
        tab_res_sim.children = [ipw.VBox([view.widget, ipw.HBox([play, slider])], layout=ipw.Layout(margin="10px")), w_result]
        tab_res_sim.set_title(index=0, title="Simulation")
        tab_res_sim.set_title(index=1, title="Résultat")
        return ipw.HBox([
            ipw.VBox([
                ipw.HBox([ipw.Label('Musique :', layout=ipw.Layout(width='70px')), w_music]),
                tab,
                ipw.GridBox([
                    ipw.Label('Pas :'), w_step,
                    ipw.Label('Orientation des mains :'), w_sides,
                    ipw.Label('Couleurs :'), w_colors
                ], layout=ipw.Layout(grid_template_columns='repeat(2, 150px)')),
                w_working,
                w_method,
                ipw.HBox([w_solve, w_simulate])], layout=ipw.Layout(margin="10px")),
            tab_res_sim
        ])

    def solve(args):
        nonlocal jsol
        if w_working.value != "Prêt":
            return
        music = []
        for s in w_music.value.split('] ['):
            s1 = s.strip()
            if s1[0] == '[':
                s1 = s1[1:]
            elif s1[-1] == ']':
                s1 = s1[:-1]
            p = s1.split(' ')
            for i in range(1, len(p)):
                music.append((int(p[0]), p[i]))

        nb_hands = w_nb_hands.value
        max_height = w_max_height.value
        max_weight = w_max_weight.value
        forbidden_multiplex = []
        if w_forbidden_throws.value.strip() != '':
            for s in w_forbidden_throws.value.split(' '):
                i = int(s)
                forbidden_multiplex.append((i, ))
        for s in w_forbidden_multiplex.value:
            i = int(s.split(', ')[0])
            j = int(s.split(', ')[1])
            forbidden_multiplex.append((i, j))
        maximize = [int(s) for s in w_maximize.value.split(' ')] if w_maximize.value.strip() != '' else []
        method = 'DLX' if w_method.value.startswith('Dancing Links') else 'MILP'
        optimize = w_maximize.value != ""
        w_working.value = "En cours..."
        balls, throws = music_to_throws(music)
        ec_instance = throws_to_extended_exact_cover(balls, throws, nb_hands, max_height, max_weight,
                                                     forbidden_multiplex, True)
        sol = None
        if method == "DLX":
            sol = get_solution_with_dlx(ec_instance, maximize=maximize)
        elif method == "MILP":
            sol = solve_exact_cover_with_milp(ec_instance, optimize=optimize, maximize=maximize)
        if len(sol) == 0:
            raise RuntimeError("No solution.")
        jsol = exact_cover_solution_to_juggling_solution(sol)
        formatted_str = juggling_to_formatted_str(jsol)
        w_result.value = formatted_str
        w_working.value = "Prêt"
        w_simulate.disabled = False
        tab_res_sim.selected_index = 1

    def simulate(args):
        colors = w_colors.value.split(', ')
        sides = [int(x) for x in w_sides.value.split(', ')]
        step = w_step.value
        balls, pattern = juggling_sol_to_simulator(jsol, colors)
        model = modele.Model(balls, pattern)
        play = ipw.Play(
            value=0,
            min=0,
            max=4000,
            step=step,
            interval=30,
            description="Press play",
            disabled=False
        )
        slider = ipw.IntSlider(min=0, max=4000)
        ipw.jslink((play, 'value'), (slider, 'value'))
        view = modele.View(model, sides, out)
        slider.observe(lambda change: view.update(change['new'] / 100, change['old'] / 100), names="value")
        with out:
            out.clear_output()
            tab_res_sim.selected_index = 0
            display(ui_view(view, play, slider))

    w_generate_forbidden_multiplex.on_click(fill_forbidden_multiplex)
    w_generate_hands.on_click(fill_hand_constraints)
    w_solve.on_click(solve)
    w_simulate.on_click(simulate)

    ui = ui_view(view, play, slider)

    with out:
        display(ui)
    return out






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
