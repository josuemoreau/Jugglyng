from typing import List, Tuple, Any, Dict, Callable, Hashable, Iterator, Union, Set, Optional
from typing_extensions import Protocol
import cppyy
import os

_dir_path = os.path.dirname(os.path.realpath(__file__))
_cur_path = os.getcwd()
os.chdir(_dir_path)

cppyy.include('dlx_m.hpp')
# cppyy.load_library('dlx_m.so')

cppyy.cppdef("""
/**
 * Implémentation de l'algorithme M
 * --------------------------------
 * 
 * La description de l'algorithme se trouve dans
 * The Art of Computer Programming, Volume 4, Fascicule 5
 */

// #include "dlx_m.hpp"

#include <iostream>
#include <string>

using namespace DLX_M;

DLX::DLX(vector<tuple<AbstrItem*, INT, INT>> primary,
         vector<AbstrItem*> secondary, 
         vector<tuple<vector<AbstrItem*>, vector<tuple<AbstrItem*, COLOR>>>> rows) :
    DLX(primary, secondary, rows, [](DLX* dlx) -> INT {
        INT i = dlx->items[0].rlink;
        INT p;

        for (p = i; p != 0; p = dlx->items[p].rlink)
            if (dlx->options[p].tl < dlx->options[i].tl)
                i = p;

        return i;
    }) {}

DLX::DLX(vector<tuple<AbstrItem*, INT, INT>> primary,
         vector<AbstrItem*> secondary, 
         vector<tuple<vector<AbstrItem*>, vector<tuple<AbstrItem*, COLOR>>>> rows,
         function<INT(DLX*)> choose) {
    INT i = 0;
    AbstrItem* name;
    INT u, v;

    this->items.push_back(Item(nullptr, primary.size(), 1, -1, -1));
    this->options.push_back(SepNode(0, 0));

    for (auto item : primary) {
        // le numéro de la colonne actuelle est i + 1
        // les numéros de colonnes commencent à 1
        tie(name, u, v) = item;
        this->items.push_back(Primary(name, i, i + 2, v - u, v));
        this->corresp.emplace(name, i + 1);
        // cout << "Set dlx_id for item " << i + 1 << endl;
        name->set_id(i + 1);
        this->options.push_back(HNode(0, i + 1, i + 1, -1));
        this->nb_option_nodes++;
        i++;
    }
    this->items.back().rlink = 0;

    this->nb_primary = this->nb_option_nodes - 1;
    
    INT j = i + 1;
    for (auto item : secondary) {
        this->items.push_back(Secondary(item, i, i + 2));
        this->corresp.emplace(item, i + 1);
        this->options.push_back(HNode(0, i + 1, i + 1, -1));
        this->nb_option_nodes++;
        i++;
    }
    this->items.push_back(Secondary(nullptr, i, j));
    this->items[j].llink = i + 1;

    this->nb_items = this->nb_option_nodes - 1;
    
    this->options.push_back(SepNode(0, 0));
    this->nb_option_nodes++;

    for (auto row : rows) {
        vector<AbstrItem*> row_primary;
        vector<tuple<AbstrItem*, COLOR>> row_secondary;
        tie(row_primary, row_secondary) = row;
        this->add_row(row_primary, row_secondary);
    }

    this->choose = choose;
    this->covered = (bool *) malloc(sizeof(bool) * (this->nb_primary + 1));
    this->covered[0] = true;
    for (int k = 1; k <= this->nb_primary; k++)
        this->covered[k] = false;
}

void DLX::add_row(vector<AbstrItem*> row_primary, 
                  vector<tuple<AbstrItem*, COLOR>> row_secondary) {
    INT first_node = this->nb_option_nodes;
    INT item_id, last_item_node;

    this->rows.push_back(make_tuple(row_primary, row_secondary));

    for (auto option : row_primary) {
        item_id = this->corresp[option];
        last_item_node = this->options[item_id].ulink;
        this->options.push_back(ONode(item_id, last_item_node, item_id, 
                                      EMPTY_COLOR, this->nb_rows));
        this->options[last_item_node].dlink = this->nb_option_nodes;
        this->options[item_id].ulink = this->nb_option_nodes;
        this->options[item_id].tl++;
        this->nb_option_nodes++;
    }
    
    AbstrItem* element;    
    COLOR color;
    for (auto option : row_secondary) {
        tie(element, color) = option;
        item_id = this->corresp[element];
        last_item_node = this->options[item_id].ulink;
        this->options.push_back(ONode(item_id, last_item_node, item_id, 
                                      color, this->nb_rows));
        this->options[last_item_node].dlink = this->nb_option_nodes;
        this->options[item_id].ulink = this->nb_option_nodes;
        this->options[item_id].tl++;
        this->nb_option_nodes++;
    }

    this->options[first_node - 1].dlink = this->nb_option_nodes - 1;
    this->options.push_back(SepNode(first_node, 0));
    this->nb_option_nodes++;
    this->nb_rows++;
}

void DLX::cover(INT i) {
    INT p = DLINK(i);
    while (p != i) {
        this->hide(p);
        p = DLINK(p);
    }
    INT l = LLINK(i);
    INT r = RLINK(i);
    RLINK(l) = r;
    LLINK(r) = l;
    this->covered[i] = true;
}

void DLX::hide(INT p) {
    INT q = p + 1;
    INT x, u, d;
    while (q != p) {
        x = TOP(q);
        u = ULINK(q);
        d = DLINK(q);
        if (x <= 0) q = u;
        else if (CLR(q) == IGNORE_COLOR) q++;
        else {
            DLINK(u) = d;
            ULINK(d) = u;
            LEN(x)--;
            q++;
        }
    }
}

void DLX::uncover(INT i) {
    INT l = LLINK(i);
    INT r = RLINK(i);
    RLINK(l) = i;
    LLINK(r) = i;
    INT p = ULINK(i);
    while (p != i) {
        this->unhide(p);
        p = ULINK(p);
    }
    this->covered[i] = false;
}

void DLX::unhide(INT p) {
    INT q = p - 1;
    INT x, u, d;
    while (q != p) {
        x = TOP(q);
        u = ULINK(q);
        d = DLINK(q);
        if (x <= 0) q = d;
        else if (CLR(q) == IGNORE_COLOR) q--;
        else {
            DLINK(u) = q;
            ULINK(d) = q;
            LEN(x)++;
            q--;
        }
    }
}

void DLX::commit(INT p, INT j) {
    // cout << "commit secondary column " << j << " from node " << p << endl;
    if (CLR(p) == EMPTY_COLOR) this->cover(j);
    else if (CLR(p) != IGNORE_COLOR) this->purify(p);
}

void DLX::purify(INT p) {
    // cout << "purify line of node " << p << endl;
    COLOR c = CLR(p);
    INT i = TOP(p);
    CLR(i) = c;
    INT q = DLINK(i);
    while (q != i) {
        if (CLR(q) == c) CLR(q) = IGNORE_COLOR;
        else this->hide(q);
        q = DLINK(q);
    }
}

void DLX::uncommit(INT p, INT j) {
    if (CLR(p) == EMPTY_COLOR) this->uncover(j);
    else if (CLR(p) != IGNORE_COLOR) this->unpurify(p);
}

void DLX::unpurify(INT p) {
    COLOR c = CLR(p);
    INT i = TOP(p);
    INT q = ULINK(i);
    while (q != i) {
        if (CLR(q) == IGNORE_COLOR) CLR(q) = c;
        else this->unhide(q);
        q = ULINK(q);
    }
}

void DLX::tweak(INT x, INT p) {
    // cout << "tweak " << x << " for item " << p << endl;
    this->hide(x);
    INT d = DLINK(x);
    DLINK(p) = d;
    ULINK(d) = p;
    LEN(p)--;
}

void DLX::tweak_special(INT x, INT p) {
    // cout << "tweak " << x << " for item " << p << endl;
    INT d = DLINK(x);
    DLINK(p) = d;
    ULINK(d) = p;
    LEN(p)--;
}

void DLX::untweak(vector<INT> &ft, INT l) {
    // cout << "UNTWEAK" << endl;
    INT a = ft[l], x = a, k = 0;
    INT p = (a <= this->nb_items) ? a : TOP(a);
    INT y = p;
    INT z = DLINK(p);
    DLINK(p) = x;
    while (x != z) {
        // cout << "untweak " << x << endl;
        ULINK(x) = y;
        k++;
        this->unhide(x);
        y = x;
        x = DLINK(x);
    }
    ULINK(z) = y;
    LEN(p) += k;
}

void DLX::untweak_special(vector<INT> &ft, INT l) {
    // cout << "UNTWEAK" << endl;
    INT a = ft[l], x = a, k = 0;
    INT p = (a <= this->nb_items) ? a : TOP(a);
    INT y = p;
    INT z = DLINK(p);
    DLINK(p) = x;
    while (x != z) {
        // cout << "untweak " << x << endl;
        ULINK(x) = y;
        k++;
        y = x;
        x = DLINK(x);
    }
    ULINK(z) = y;
    LEN(p) += k;
    this->uncover(p);
}

// INT DLX::choose() {
//     INT i = this->items[0].rlink;
//     INT p;

//     for (p = i; p != 0; p = this->items[p].rlink)
//         if (this->options[p].tl < this->options[i].tl)
//             i = p;

//     return i;
// }

void DLX::print_table() {
    cout << this->nb_items << " items (" << this->nb_primary << " primary)" << endl;

    for (auto& item : this->items) {
        cout << "Item(";
        if (item.name == nullptr) cout << "Null, ";
        else { item.name->print(); cout << ", "; }
        cout << item.llink << ", "
                << item.rlink;
        if (item.slack != -1 && item.bound != -1)
            cout << ", "
                    << item.slack << ", "
                    << item.bound;
        cout << ")" << endl;
    }

    INT i = 0;
    for (auto& option : this->options) {
        cout << i << " : " 
             << ((option.type == Header)?"Header":"Option") << "("
             << option.tl << ", "
             << option.ulink << ", "
             << option.dlink;
        if (option.type == Option) 
            cout << ", " << option.color << ")" << endl;
        else
            cout << ")" << endl;
        i++;
    }
}

vector<INT> DLX::solution_rows(vector<INT> x, INT l) {
    vector<INT> sol;
    INT i = 0;

    for (auto& opt_id : x) {
        if (i >= l) break;
        if (opt_id <= this->nb_items) continue;

        sol.push_back(this->options[opt_id].row_number);
    }

    return sol;
}

void DLX::print_rows(vector<INT> rows) {
    vector<AbstrItem*> row_primary;
    vector<tuple<AbstrItem*, COLOR>> row_secondary;

    for (auto& row_id : rows) {
        tie(row_primary, row_secondary) = this->rows[row_id];
        for (auto& elem : row_primary) {
            elem->print();
            cout << " ";
        }

        AbstrItem* elem;
        COLOR clr;
        for (auto& elem_color : row_secondary) {
            tie(elem, clr) = elem_color;
            elem->print();
            cout << ":" << clr << " ";
        }

        cout << endl;
    }
}

void DLX::print_solution(vector<INT> sol) {
    cout << "Solution [ ";
    for (auto& row_id : sol)
        cout << row_id << " ";
    cout << "] :" << endl;
    print_rows(sol);
}

vector<vector<INT>> DLX::all_solutions(bool verbose) {
    vector<INT> x(this->options.size());
    vector<INT> ft(this->options.size());
    INT l = 0;
    INT i, p, j, q;
    unsigned int nb_solutions = 0;

    vector<vector<INT>> solutions;

    auto ppx = [](vector<INT> x, INT l) {
        INT i = 0;
        for (auto& e : x) {
            if (i++ >= l) break;
            cout << e << " ";
        }
        cout << endl;
    };

    M2: // cout << "M2" << endl;
        ppx(x, l);
        if (RLINK(0) == 0) {
            // cout << "====================================================" << endl;
            // cout << "Found solution :" << endl;
            // this->print_solution(x, l, pp);
            vector<INT> sol = this->solution_rows(x, l);
            solutions.push_back(sol);
            if (verbose) this->print_solution(sol);
            nb_solutions++;
            // cout << "====================================================" << endl;
            goto M9;
        }
    M3: // cout << "M3" << endl;
        ppx(x, l);
        i = this->choose(this);
        // cout << "Choose " << i << endl;
        // cout << "Branch degree " << branch_degree(i) << endl;
        // cout << "BOUND(i) " << BOUND(i) << endl;
        if (branch_degree(i) == 0) goto M9;
    M4: // cout << "M4" << endl;
        ppx(x, l);
        x[l] = DLINK(i);
        BOUND(i)--;
        if (BOUND(i) == 0) this->cover(i);
        if (BOUND(i) != 0 || SLACK(i) != 0)
            ft[l] = x[l];
    M5: // cout << "M5" << endl;
        ppx(x, l);
        if (BOUND(i) == 0 && SLACK(i) == 0) {
            if (x[l] != i) goto M6;
            else goto M8;
        } else if (LEN(i) <= BOUND(i) - SLACK(i)) {
            goto M8;
        } else if (x[l] != i) {
            if (BOUND(i) == 0) this->tweak_special(x[l], i);
            else this->tweak(x[l], i);
        } else if (BOUND(i) != 0) {
            p = LLINK(i);
            q = RLINK(i);
            RLINK(p) = q;
            LLINK(q) = p;
        }
    M6: // cout << "M6" << endl;
        ppx(x, l);
        if (x[l] != i) {
            p = x[l] + 1;
            while (p != x[l]) {
                j = TOP(p);
                if (j <= 0) p = ULINK(p);
                else if (j <= this->nb_primary) {
                    BOUND(j)--;
                    p++;
                    if (BOUND(j) == 0) this->cover(j);
                } else {
                    this->commit(p, j);
                    p++;
                }
            }
        }
        // print_table();
        l++;
        goto M2;
    M7: // cout << "M7" << endl;
        ppx(x, l);
        // if (x[l] != i) {
        p = x[l] - 1;
        while (p != x[l]) {
            j = TOP(p);
            if (j <= 0) p = DLINK(p);
            else if (j <= this->nb_primary) {
                BOUND(j)++;
                p--;
                if (BOUND(j) == 1) this->uncover(j);
            } else {
                this->uncommit(p, j);
                p--;
            }
        }
        // }
        x[l] = DLINK(x[l]);
        // cout << "x_l " << x[l] << endl;
        goto M5;
    M8: // cout << "M8" << endl;
        ppx(x, l);
        // cout << "BOUND(i) " << BOUND(i) << endl;
        // cout << "SLACK(i) " << SLACK(i) << endl;
        if (BOUND(i) == 0 && SLACK(i) == 0)
            this->uncover(i);
        else if (BOUND(i) == 0) this->untweak_special(ft, l);
        else this->untweak(ft, l);
        BOUND(i)++;
        // cout << "BOUND(i) " << BOUND(i) << endl;
    M9: // cout << "M9" << endl;
        // cout << "M9 - l=" << l << endl;
        ppx(x, l);
        if (l == 0) {
            if (verbose) {
                cout << "---------------------------------" << endl;
                cout << nb_solutions << " solutions found." << endl;
                cout << "---------------------------------" << endl; 
            }
            return solutions;
        } else l--;
        // cout << "M9 - l=" << l << endl;
        // cout << "x_l " << x[l] << endl;
        // cout << "N " << this->nb_items << endl;
        if (x[l] <= this->nb_items) {
            i = x[l];
            p = LLINK(i);
            q = RLINK(i);
            RLINK(p) = i;
            LLINK(q) = i;
            goto M8;
        } else {
            i = TOP(x[l]);
            goto M7;
        }
}

vector<INT> DLX::search(bool resume) {
    vector<INT> x(this->options.size());
    vector<INT> ft(this->options.size());
    INT l = 0;
    INT i, p, j, q;

    auto ppx = [](vector<INT> x, INT l) {
        INT i = 0;
        for (auto& e : x) {
            if (i++ >= l) break;
            cout << e << " ";
        }
        cout << endl;
    };

    if (resume) {
        x  = this->x;
        ft = this->ft;
        l  = this->l;
        i  = this->i;
        goto M9;
    }

    M2: // cout << "M2" << endl;
        // ppx(x, l);
        if (RLINK(0) == 0) {
            // cout << "====================================================" << endl;
            // cout << "Found solution :" << endl;
            // this->print_solution(x, l, pp);
            vector<INT> sol = this->solution_rows(x, l);
            // this->print_solution(sol);
            
            // Sauvegarde de l'état de la recherche
            this->x  = x;
            this->ft = ft;
            this->l  = l;
            this->i  = i;

            return sol;

            // cout << "====================================================" << endl;
            goto M9;
        }
    M3: // cout << "M3" << endl;
        // ppx(x, l);
        i = this->choose(this);
        // cout << "Choose " << i << endl;
        // cout << "Branch degree " << branch_degree(i) << endl;
        // cout << "BOUND(i) " << BOUND(i) << endl;
        if (branch_degree(i) == 0) goto M9;
    M4: // cout << "M4" << endl;
        // ppx(x, l);
        x[l] = DLINK(i);
        BOUND(i)--;
        if (BOUND(i) == 0) this->cover(i);
        if (BOUND(i) != 0 || SLACK(i) != 0)
            ft[l] = x[l];
    M5: // cout << "M5" << endl;
        // ppx(x, l);
        if (BOUND(i) == 0 && SLACK(i) == 0) {
            if (x[l] != i) goto M6;
            else goto M8;
        } else if (LEN(i) <= BOUND(i) - SLACK(i)) {
            goto M8;
        } else if (x[l] != i) {
            if (BOUND(i) == 0) this->tweak_special(x[l], i);
            else this->tweak(x[l], i);
        } else if (BOUND(i) != 0) {
            p = LLINK(i);
            q = RLINK(i);
            RLINK(p) = q;
            LLINK(q) = p;
        }
    M6: // cout << "M6" << endl;
        // ppx(x, l);
        if (x[l] != i) {
            p = x[l] + 1;
            while (p != x[l]) {
                j = TOP(p);
                if (j <= 0) p = ULINK(p);
                else if (j <= this->nb_primary) {
                    BOUND(j)--;
                    p++;
                    if (BOUND(j) == 0) this->cover(j);
                } else {
                    this->commit(p, j);
                    p++;
                }
            }
        }
        l++;
        goto M2;
    M7: // cout << "M7" << endl;
        // ppx(x, l);
        // if (x[l] != i) {
        p = x[l] - 1;
        while (p != x[l]) {
            j = TOP(p);
            if (j <= 0) p = DLINK(p);
            else if (j <= this->nb_primary) {
                BOUND(j)++;
                p--;
                if (BOUND(j) == 1) this->uncover(j);
            } else {
                this->uncommit(p, j);
                p--;
            }
        }
        // }
        x[l] = DLINK(x[l]);
        // cout << "x_l " << x[l] << endl;
        goto M5;
    M8: // cout << "M8" << endl;
        // ppx(x, l);
        // cout << "BOUND(i) " << BOUND(i) << endl;
        // cout << "SLACK(i) " << SLACK(i) << endl;
        if (BOUND(i) == 0 && SLACK(i) == 0)
            this->uncover(i);
        else if (BOUND(i) == 0) this->untweak_special(ft, l);
        else this->untweak(ft, l);
        BOUND(i)++;
        // cout << "BOUND(i) " << BOUND(i) << endl;
    M9: // cout << "M9" << endl;
        // cout << "M9 - l=" << l << endl;
        // ppx(x, l);
        if (l == 0) {
            throw NoSolution();
        } else l--;
        // cout << "M9 - l=" << l << endl;
        // cout << "x_l " << x[l] << endl;
        // cout << "N " << this->nb_items << endl;
        if (x[l] <= this->nb_items) {
            i = x[l];
            p = LLINK(i);
            q = RLINK(i);
            RLINK(p) = i;
            LLINK(q) = i;
            goto M8;
        } else {
            i = TOP(x[l]);
            goto M7;
        }
}
""")

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
