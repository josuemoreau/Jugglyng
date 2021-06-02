from typing import List, Tuple, Any, Dict
import cppyy

cppyy.include('dlx-m.hpp')
cppyy.load_library('dlx-m.so')

std = cppyy.gbl.std
DLX_M = cppyy.gbl.DLX_M
INT = DLX_M.INT
COLOR = DLX_M.COLOR
DLX = DLX_M.DLX
EMPTY_COLOR = 0
AbstrItem = DLX_M.AbstrItem

primary_tpl = std.make_tuple['DLX_M::AbstrItem*', INT, INT]
primary_vct = std.vector[std.tuple['DLX_M::AbstrItem*', INT, INT]]
secondary_vct = std.vector['DLX_M::AbstrItem*']

row_primary_vct = std.vector['DLX_M::AbstrItem*']
row_secondary_tpl = std.make_tuple['DLX_M::AbstrItem*', COLOR]
row_secondary_vct = std.vector[std.tuple['DLX_M::AbstrItem*', COLOR]]
row_tpl = std.make_tuple[row_primary_vct, row_secondary_vct]
row_vct = std.vector[std.tuple[row_primary_vct, row_secondary_vct]]


def P(x: List[Tuple[AbstrItem, int, int]]):
    return primary_vct([primary_tpl(obj, low, high) for (obj, low, high) in x])


def S(x: List[AbstrItem]):
    return secondary_vct(x)


def RP(x: List[AbstrItem]):
    return row_primary_vct(x)


def RS(x: List[Tuple[AbstrItem, int]]):
    return row_secondary_vct([row_secondary_tpl(obj, clr) for (obj, clr) in x])


def R(x: List[Tuple[List[AbstrItem], List[Tuple[AbstrItem, int]]]]):
    return row_vct([row_tpl(RP(p), RS(s)) for (p, s) in x])


def new_id_generator():
    x = -1

    def f():
        nonlocal x
        x += 1
        return x
    return f


class ConcItem(AbstrItem):
    def set(self, x):
        self.x = x

    def get(self):
        return self.x

    def str(self):
        return str(self.x)

    def print(self):
        print(self.x, end="", flush=True)


class DLXMVariable():
    dict: Dict[Any, ConcItem]
    lower_bound: int
    upper_bound: int
    secondary: bool

    def __init__(self, id_generator, lower_bound, upper_bound, secondary):
        self.dict = {}
        self.new_id = id_generator
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.secondary = secondary

    def __getitem__(self, x):
        if x not in self.dict:
            id = self.new_id()
            obj = ConcItem()
            obj.set('x_' + str(id))
            self.dict[x] = obj
        return self.dict[x]

    def __iter__(self):
        return self.dict.__iter__()


class DLXM():
    def __init__(self):
        self.primary_items = {}
        self.secondary_items = {}
        self.variables = []
        self.new_id = new_id_generator()
        self.rows = []
        self.rows_cpp = []

    def new_variable(self, lower_bound=0, upper_bound=1, secondary=False):
        x = DLXMVariable(self.new_id, lower_bound, upper_bound, secondary)
        self.variables.append(x)
        return x

    def add_row(self, row_primary: List[ConcItem] = [],
                row_secondary: List[Tuple[ConcItem, int]] = []):
        self.rows.append((row_primary, row_secondary))
        self.rows_cpp.append((RP(row_primary), RS(row_secondary)))

    def row(self, i):
        p, s = self.rows[i]
        return [e.get() for e in p] + [(e.get(), c) for (e, c) in s]

    def all_solutions(self, verbose=False):
        primary_items = []
        secondary_items = []

        x: DLXMVariable
        for x in self.variables:
            if x.secondary:
                for k in x:
                    secondary_items.append(x[k])
            else:
                for k in x:
                    primary_items.append((x[k], x.lower_bound, x.upper_bound))

        primary = P(primary_items)
        secondary = S(secondary_items)
        rows = R([])

        dlx = DLX(primary, secondary, rows)
        for p, s in self.rows_cpp:
            dlx.add_row(p, s)
        sols = dlx.all_solutions(verbose)
        return [set(sol) for sol in sols]


# Test
# x = ConcItem()
# x.set('x')

# primary = P([(x, 0, 5)])
# secondary = S([])
# rows = R([])

# dlx = DLX(primary, secondary, rows)
# dlx.add_row(RP([x]), RS([]))
# dlx.add_row(RP([x]), RS([]))
# dlx.add_row(RP([x]), RS([]))
# dlx.add_row(RP([x]), RS([]))
# dlx.add_row(RP([x]), RS([]))
# dlx.all_solutions()

if __name__ == "__main__":
    def print_solutions(sols):
        for sol in sols:
            print("Solution", sol, ":")
            for i in sol:
                print(dlx.row(i))
        print("--\n%d solutions" % len(sols))

    print("=== TEST 1 ===")
    dlx = DLXM()
    pv = dlx.new_variable(1, 1)
    sv = dlx.new_variable(secondary=True)
    p, q, r = pv[0], pv[1], pv[2]
    x, y = sv[0], sv[1]
    dlx.add_row([p, q], [(x, 0), (y, 1)])
    dlx.add_row([p, r], [(x, 1), (y, 0)])
    dlx.add_row([p], [(x, 2)])
    dlx.add_row([q], [(x, 1)])
    dlx.add_row([r], [(y, 1)])
    sols = dlx.all_solutions()
    print_solutions(sols)

    print("=== TEST 2 ===")
    dlx = DLXM()
    x = dlx.new_variable(1, 1)
    dlx.add_row([x[0], x[1]])
    dlx.add_row([x[0], x[2]])
    dlx.add_row([x[0]])
    dlx.add_row([x[1]])
    dlx.add_row([x[2]])
    sols = dlx.all_solutions()
    print_solutions(sols)

    print("=== TEST 3 ===")
    dlx = DLXM()
    x = dlx.new_variable(0, 5)
    dlx.add_row([x[0]])
    dlx.add_row([x[0]])
    dlx.add_row([x[0]])
    dlx.add_row([x[0]])
    dlx.add_row([x[0]])
    sols = dlx.all_solutions()
    print_solutions(sols)
