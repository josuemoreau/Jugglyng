from recordclass import StructClass
from typing import List, Dict, Tuple, Union, Set
from sage.all import MixedIntegerLinearProgram

from pylatex import Document
from pylatex.utils import NoEscape

# musique = [( 1, "do"), ( 2, "do"), ( 3, "do"),
#            ( 4, "ré"), ( 5, "mi"), ( 7, "ré"),
#            ( 9, "do"), (10, "mi"), (11, "ré"),
#            (12, "ré"), (13, "do")]


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


class ExactCoverInstance(StructClass):
    max_time: int = 0
    nb_hands: int = 1
    balls: Set[str] = set()

    x_items: List[XItem] = []
    l_items: List[LItem] = []
    w_items: List[WItem] = []
    i_items: List[IItem] = []
    m_items: List[MItem] = []
    d_items: List[DItem] = []

    x_items_bounds: Tuple[int, int] = (0, 1)
    l_items_bounds: Tuple[int, int] = (1, 1)
    w_items_bounds: Tuple[int, int] = (0, 1)
    i_items_bounds: Tuple[int, int] = (0, 1)
    m_items_bounds: Tuple[int, int] = (0, 1)
    d_items_bounds: Tuple[int, int] = (0, 1)

    rows: List[List[Union[XItem, LItem, WItem, IItem, MItem, DItem]]] = []


class ExactCoverSolution(StructClass):
    max_time: int = 0
    nb_hands: int = 1
    balls: Set[str] = set()

    rows: List[List[Union[XItem, LItem, WItem, IItem, MItem, DItem]]] = []


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
    d_items = {}
    fmultiplex: Dict[int, List[Tuple[int, ]]] = {i: [] for i in range(1, H + 1)}
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
    # Génération des items x et I
    for t in range(len(throws)):
        for throw in throws[t]:
            u = LItem(throw=throw)
            l_items[throw] = u

            for hand in range(nb_hands):
                for flying_time in range(1, min(H, throw.max_height) + 1):
                    x = XItem(throw=throw, hand=hand, flying_time=flying_time)
                    x_items[(throw, hand, flying_time)] = x
    # Génération des items w, M et D
    for t in range(max_time + 1):
        for hand in range(nb_hands):
            w = WItem(time=t, hand=hand)
            w_items[(t, hand)] = w

            d = DItem(time=t, hand=hand)
            d_items[(t, hand)] = d

            for f in forbidden_multiplex:
                m = MItem(time=t, hand=hand, multiplex=f)
                m_items[(t, hand, f)] = m
    # Génération des items I
    for t in range(max_time + 1):
        for hand in range(nb_hands):
            for flying_time in range(1, H + 1):
                i = IItem(time=t, hand=hand, flying_time=flying_time)
                i_items[(t, hand, flying_time)] = i
    # Génération des lignes
    for t in range(len(throws)):
        for throw in throws[t]:
            for hand in range(nb_hands):
                for flying_time in range(1, min(H, throw.max_height) + 1):
                    row = [x_items[(throw, hand, flying_time)], l_items[throw]]
                    if multiple_throws:
                        row.append(d_items[(t + throw.max_height - flying_time, hand)])
                    if flying_time == throw.max_height:
                        row.append(i_items[(t, hand, flying_time)])
                    for fmulti in fmultiplex[flying_time]:
                        row.append(m_items[(t + throw.max_height - flying_time,
                                   hand, fm)])
                    for fnext in f2seqs[flying_time]:
                        row.append(i_items[(t + 1, hand, fnext)])
                    for t1 in range(t, t + throw.max_height - flying_time + 1):
                        row.append(w_items[(t1, hand)])
                    rows.append(row)

    return ExactCoverInstance(x_items=list(x_items.values()),
                              l_items=list(l_items.values()),
                              w_items=list(w_items.values()),
                              i_items=list(i_items.values()),
                              m_items=list(m_items.values()),
                              d_items=list(d_items.values()),
                              w_items_bounds=(0, K),
                              rows=rows,
                              max_time=max_time,
                              nb_hands=nb_hands,
                              balls=balls)


def solve_exact_cover_with_milp(ec_instance: ExactCoverInstance) -> ExactCoverSolution:
    p = MixedIntegerLinearProgram()

    # Calcul, pour chaque colonne, des lignes qui ont un élément dans cette
    # colonne
    d: Dict[Union[XItem, LItem, WItem, IItem, MItem, DItem], List[int]] \
        = {item: [] for item in ec_instance.x_items + ec_instance.l_items
            + ec_instance.w_items + ec_instance.i_items
            + ec_instance.m_items + ec_instance.d_items}
    for i in range(len(ec_instance.rows)):
        row = ec_instance.rows[i]
        for item in row:
            d[item].append(i)

    # Génération de l'instance de MILP
    x = p.new_variable(binary=True)
    for item in ec_instance.x_items:
        if len(d[item]) > 0:
            rows_vars = [x[i] for i in d[item]]
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
            p.add_constraint(ec_instance.m_items_bounds[0]
                             <= sum(rows_vars)
                             <= ec_instance.m_items_bounds[1])
    for item in ec_instance.d_items:
        if len(d[item]) > 0:
            rows_vars = [x[i] for i in d[item]]
            p.add_constraint(ec_instance.d_items_bounds[0]
                             <= sum(rows_vars)
                             <= ec_instance.d_items_bounds[1])

    # Résolution
    p.solve()
    selected_rows = p.get_values(x)

    return ExactCoverSolution(max_time=ec_instance.max_time,
                              nb_hands=ec_instance.nb_hands,
                              balls=ec_instance.balls,
                              rows=[ec_instance.rows[i]
                                    for i in selected_rows if selected_rows[i] == 1.0])

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
