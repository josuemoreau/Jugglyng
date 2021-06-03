from typing import List, Tuple, Any, Dict, Callable, Hashable, Iterator, Union
from typing_extensions import Protocol
import cppyy

cppyy.include('dlx-m.hpp')
cppyy.load_library('dlx-m.so')

_std = cppyy.gbl.std
_DLX_M = cppyy.gbl.DLX_M
_INT = _DLX_M.INT
_COLOR = _DLX_M.COLOR
_DLX = _DLX_M.DLX
_EMPTY_COLOR = 0
_AbstrItem: Any = _DLX_M.AbstrItem

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
    def set(self, x: Any):
        self.x = x

    def get(self):
        return self.x

    def str(self):
        return str(self.x)

    def print(self):
        print(self.x, end="", flush=True)


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
        if x not in self.dict:
            id = self.new_id()
            obj = ConcItem()
            obj.set('x_' + str(id))
            self.dict[x] = obj
        return self.dict[x]

    def __iter__(self) -> Iterator[Hashable]:
        return self.dict.__iter__()


class DLXM():
    variables: List[DLXMVariable]
    new_id: NewId
    rows: List[Tuple[List[ConcItem], List[Tuple[ConcItem, int]]]]

    def __init__(self):
        self.variables = []
        self.new_id = _new_id_generator()
        self.rows = []
        self.rows_cpp = []

    def new_variable(self, lower_bound: int = 0, upper_bound: int = 1,
                     secondary: bool = False) -> DLXMVariable:
        x = DLXMVariable(self.new_id, lower_bound, upper_bound, secondary)
        self.variables.append(x)
        return x

    def add_row(self, row_primary: List[ConcItem] = [],
                row_secondary: List[Tuple[ConcItem, int]] = []):
        self.rows.append((row_primary, row_secondary))
        self.rows_cpp.append((_RP(row_primary), _RS(row_secondary)))

    def row(self, i: int) -> List[Union[Any, Tuple[Any, int]]]:
        p, s = self.rows[i]
        return [e.get() for e in p] + [(e.get(), c) for (e, c) in s]

    def all_solutions(self, verbose: bool = False):
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

        dlx = _DLX(primary, secondary, rows)
        for p, s in self.rows_cpp:
            dlx.add_row(p, s)
        sols = dlx.all_solutions(verbose)
        return [set(sol) for sol in sols]
