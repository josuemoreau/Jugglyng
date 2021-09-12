from typing import List, Tuple, Any, Dict, Callable, Hashable, Iterator, Union, Set, Optional
from typing_extensions import Protocol
import cppyy
import os

_dir_path = os.path.dirname(os.path.realpath(__file__))
_cur_path = os.getcwd()
os.chdir(_dir_path)

cppyy.include('dlx_m.hpp')
cppyy.load_library('dlx_m.so')

os.chdir(_cur_path)

_std = cppyy.gbl.std
_DLX_M = cppyy.gbl.DLX_M
_INT = _DLX_M.INT
_COLOR = _DLX_M.COLOR
_DLX = _DLX_M.DLX
_EMPTY_COLOR = 0
_AbstrItem: Any = _DLX_M.AbstrItem
_NoSolution = _DLX_M.NoSolution

_primary_tpl = _std.make_tuple['DLX_M::AbstrItem*', _INT, _INT]
_primary_vct = _std.vector[_std.tuple['DLX_M::AbstrItem*', _INT, _INT]]
_secondary_vct = _std.vector['DLX_M::AbstrItem*']

_row_primary_vct = _std.vector['DLX_M::AbstrItem*']
_row_secondary_tpl = _std.make_tuple['DLX_M::AbstrItem*', _COLOR]
_row_secondary_vct = _std.vector[_std.tuple['DLX_M::AbstrItem*', _COLOR]]
_row_tpl = _std.make_tuple[_row_primary_vct, _row_secondary_vct]
_row_vct = _std.vector[_std.tuple[_row_primary_vct, _row_secondary_vct]]


def _P(x: List[Tuple[_AbstrItem, int, int]]):
    return _primary_vct([_primary_tpl(obj, low, high) for (obj, low, high) in x])


def _S(x: List[_AbstrItem]):
    return _secondary_vct(x)


def _RP(x: List[_AbstrItem]):
    return _row_primary_vct(x)


def _RS(x: List[Tuple[_AbstrItem, int]]):
    return _row_secondary_vct([_row_secondary_tpl(obj, clr) for (obj, clr) in x])


def _R(x: List[Tuple[List[_AbstrItem], List[Tuple[_AbstrItem, int]]]]):
    return _row_vct([_row_tpl(_RP(p), _RS(s)) for (p, s) in x])


def _new_id_generator() -> Callable[[], int]:
    x = -1

    def f():
        nonlocal x
        x += 1
        return x
    return f


class NewId(Protocol):
    def __call__(self) -> int:
        pass


class ConcItem(_AbstrItem):
    def set(self, repr: Any, x: Any):
        self.x = x
        self.dlx_id = 0
        self.repr = repr

    def get_repr(self):
        return self.repr

    def get_obj(self):
        return self.x

    def str(self):
        return str(self.repr)

    def print(self):
        print(self.repr, end="", flush=True)

    def get_id(self):
        return self.dlx_id

    def set_id(self, id):
        self.dlx_id = id


class DLXMVariable():
    dict: Dict[Hashable, ConcItem]
    new_id: NewId  # Callable[[], int]
    lower_bound: int
    upper_bound: int
    secondary: bool

    def __init__(self, id_generator: Callable[[], int],
                 lower_bound: int, upper_bound: int, secondary: bool):
        self.dict = {}
        self.new_id = id_generator
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.secondary = secondary

    def __getitem__(self, x: Hashable) -> ConcItem:
        """ Renvoie la variable associée à `x`. Si aucune variable ne lui est
        associée, crée une nouvelle variable, l'associe à `x` puis la renvoie.

        >>> new_id = _new_id_generator()
        >>> v = DLXMVariable(new_id, 0, 5, False)
        >>> a, b, c = v[0], v['123'], v[0.8]
        >>> a == v[0]
        True
        >>> a.get_repr(), b.get_repr(), c.get_repr()
        ('x_0', 'x_1', 'x_2')
        """
        if x not in self.dict:
            id = self.new_id()
            obj = ConcItem()
            obj.set('x_' + str(id), x)
            self.dict[x] = obj
        return self.dict[x]

    def __contains__(self, x: Hashable) -> bool:
        """ Renvoie `True` si `x` est associée à une variable.

        >>> new_id = _new_id_generator()
        >>> v = DLXMVariable(new_id, 0, 5, False)
        >>> a = v[0]
        >>> 0 in v
        True
        """
        return x in self.dict

    def __iter__(self) -> Iterator[Hashable]:
        """ Renvoie un itérateur sur les objets associés à des variables.

        >>> new_id = _new_id_generator()
        >>> v = DLXMVariable(new_id, 0, 5, False)
        >>> a, b, c = v[0], v['123'], v[0.8]
        >>> lk = [x for x in v]
        >>> lv = [v[k].get_repr() for k in lk]
        >>> lk, lv
        ([0, '123', 0.8], ['x_0', 'x_1', 'x_2'])
        """
        return self.dict.__iter__()


class DLXM():
    variables: List[DLXMVariable]
    new_id: NewId
    rows: List[Tuple[List[ConcItem], List[Tuple[ConcItem, int]]]]
    resume: bool
    compiled_only: bool

    def __init__(self, choose=None):
        self.variables = []
        self.new_id = _new_id_generator()
        self.rows = []
        self.rows_cpp = []
        self.resume = False
        self.compiled_only = False
        self.dlx = None
        self.choose = choose

    def new_variable(self, lower_bound: int = 0, upper_bound: int = 1,
                     secondary: bool = False) -> DLXMVariable:
        """ Crée un nouvel ensemble de variables encadrées par `lower_bound`
        et `upper_bound`. Ces variables peuvent être secondaires si `secondary`
        est mis à `True`. Dans ce cas, `lower_bound` et `upper_bound` peuvent
        être n'importes quelles valeurs.

        >>> x = DLXM()
        >>> p = x.new_variable(lower_bound=0, upper_bound=5)
        >>> p.lower_bound, p.upper_bound
        (0, 5)
        >>> a, b, c = p[0], p['x'], p[0.2]
        >>> 0 in p, 'x' in p, 0.2 in p, 0.5 in p
        (True, True, True, False)
        """
        x = DLXMVariable(self.new_id, lower_bound, upper_bound, secondary)
        self.variables.append(x)
        return x

    def add_row(self, row_primary: List[ConcItem] = [],
                row_secondary: List[Tuple[ConcItem, int]] = []):
        """ Ajoute une nouvelle ligne à l'instance de exact cover avec
        multiplicités.

        >>> x = DLXM()
        >>> pv = x.new_variable(lower_bound=0, upper_bound=2)
        >>> sv = x.new_variable(secondary=True)
        >>> a, b = pv[0], pv[1]
        >>> c = sv[0]
        >>> x.add_row([a, b], [(c, 1)])
        >>> x.add_row([a], [(c, 0)])
        >>> x.add_row([b], [(c, 1)])
        >>> x.add_row([b], [(c, 0)])
        >>> len(x.rows)
        4
        >>> [([e.get_repr() for e in p], [(e.get_repr(), c) for (e, c) in s]) for (p, s) in x.rows]
        [(['x_0', 'x_1'], [('x_2', 1)]), (['x_0'], [('x_2', 0)]), (['x_1'], [('x_2', 1)]), (['x_1'], [('x_2', 0)])]
        """
        self.rows.append((row_primary, row_secondary))
        self.rows_cpp.append((_RP(row_primary), _RS(row_secondary)))

    def primary_variables(self, lower_bound: int, upper_bound: int) -> Optional[DLXMVariable]:
        for var in self.variables:
            if var.lower_bound == lower_bound and var.upper_bound == upper_bound and not var.secondary:
                return var
        return None

    def secondary_variables(self) -> Optional[DLXMVariable]:
        for var in self.variables:
            if var.secondary:
                return var
        return None

    def row_repr(self, i: int) -> List[Union[Any, Tuple[Any, int]]]:
        """ Renvoie la représentation de la ligne `i`.

        >>> x = DLXM()
        >>> pv = x.new_variable(lower_bound=0, upper_bound=2)
        >>> sv = x.new_variable(secondary=True)
        >>> a, b = pv[0], sv[0]
        >>> x.add_row([a], [(b, 1)])
        >>> x.row_repr(0)
        ['x_0', ('x_1', 1)]
        >>> x.add_row([a])
        >>> x.add_row([], [(b, 0)])
        >>> x.row_repr(0)
        ['x_0', ('x_1', 1)]
        >>> x.row_repr(2)
        [('x_1', 0)]
        """
        p, s = self.rows[i]
        return [e.get_repr() for e in p] + [(e.get_repr(), c) for (e, c) in s]

    def row_obj(self, i: int) -> List[Union[Any, Tuple[Any, int]]]:
        """ Renvoie la ligne `i` avec les objets à la place des noms de
        variables.

        """
        p, s = self.rows[i]
        return [e.get_obj() for e in p] + [(e.get_obj(), c) for (e, c) in s]

    def compile(self):
        primary_items: List[Tuple[ConcItem, int, int]] = []
        secondary_items: List[ConcItem] = []

        x: DLXMVariable
        for x in self.variables:
            if x.secondary:
                for k in x:
                    secondary_items.append(x[k])
            else:
                for k in x:
                    primary_items.append((x[k], x.lower_bound, x.upper_bound))

        primary = _P(primary_items)
        secondary = _S(secondary_items)
        rows = _R([])

        dlx = _DLX(primary, secondary, rows, self.choose) \
            if self.choose is not None else _DLX(primary, secondary, rows)
        for p, s in self.rows_cpp:
            dlx.add_row(p, s)

        self.dlx = dlx
        self.compiled_only = True

    def set_choose_function(self, choose):
        self.choose = choose
        self.dlx.set_choose_function(choose)

    def all_solutions(self, verbose: bool = False) -> List[Set[int]]:
        """ Renvoie toutes les solutions à l'instance de exact cover avec
        multiplicité.

        >>> x = DLXM()
        >>> pv = x.new_variable(lower_bound=0, upper_bound=3)
        >>> a = pv[0]
        >>> x.add_row([a])
        >>> x.add_row([a])
        >>> x.add_row([a])
        >>> x.all_solutions()
        [{0, 1, 2}, {0, 1}, {0, 2}, {0}, {1, 2}, {1}, {2}, set()]

        >>> x = DLXM()
        >>> x.all_solutions()
        [set()]

        >>> x = DLXM()
        >>> pv = x.new_variable(1, 1)
        >>> sv = x.new_variable(secondary=True)
        >>> p, q, r = pv[0], pv[1], pv[2]
        >>> a, b = sv[0], sv[1]
        >>> x.add_row([p, q], [(a, 0), (b, 1)])
        >>> x.add_row([p, r], [(a, 1), (b, 0)])
        >>> x.add_row([p], [(a, 2)])
        >>> x.add_row([q], [(a, 1)])
        >>> x.add_row([r], [(b, 1)])
        >>> x.all_solutions()
        [{0, 4}, {1, 3}]

        >>> x = DLXM()
        >>> p1 = x.new_variable(lower_bound=1, upper_bound=1)
        >>> p2 = x.new_variable(lower_bound=2, upper_bound=3)
        >>> s = x.new_variable(secondary=True)
        >>> A, B, C, X, Y = p1[0], p1[1], p2[0], s[0], s[1]
        >>> x.add_row([A, B], [(X, 0), (Y, 0)])
        >>> x.add_row([A, C], [(X, 1), (Y, 1)])
        >>> x.add_row([C], [(X, 0)])
        >>> x.add_row([B], [(X, 1)])
        >>> x.add_row([C], [(Y, 1)])
        >>> x.all_solutions()
        [{1, 3, 4}]
        """
        primary_items: List[Tuple[ConcItem, int, int]] = []
        secondary_items: List[ConcItem] = []

        x: DLXMVariable
        for x in self.variables:
            if x.secondary:
                for k in x:
                    secondary_items.append(x[k])
            else:
                for k in x:
                    primary_items.append((x[k], x.lower_bound, x.upper_bound))

        primary = _P(primary_items)
        secondary = _S(secondary_items)
        rows = _R([])

        dlx = _DLX(primary, secondary, rows, self.choose) \
            if self.choose is not None else _DLX(primary, secondary, rows)
        for p, s in self.rows_cpp:
            dlx.add_row(p, s)
        sols = dlx.all_solutions(verbose)
        return [set(sol) for sol in sols]

    def search(self) -> Optional[Set[int]]:
        if self.compiled_only:
            self.compiled_only = False
            try:
                sol = self.dlx.search(False)
                self.resume = True
                return set(sol)
            except _NoSolution:
                return None
        elif self.resume:
            try:
                sol = self.dlx.search(True)
                return set(sol)
            except _NoSolution:
                return None

        primary_items: List[Tuple[ConcItem, int, int]] = []
        secondary_items: List[ConcItem] = []

        x: DLXMVariable
        for x in self.variables:
            if x.secondary:
                for k in x:
                    secondary_items.append(x[k])
            else:
                for k in x:
                    primary_items.append((x[k], x.lower_bound, x.upper_bound))

        primary = _P(primary_items)
        secondary = _S(secondary_items)
        rows = _R([])

        dlx = _DLX(primary, secondary, rows, self.choose) \
            if self.choose is not None else _DLX(primary, secondary, rows)
        for p, s in self.rows_cpp:
            dlx.add_row(p, s)

        try:
            sol = dlx.search(False)
            self.dlx = dlx
            self.resume = True

            return set(sol)
        except _NoSolution:
            return None


if __name__ == "__main__":
    print("hello, world !")
