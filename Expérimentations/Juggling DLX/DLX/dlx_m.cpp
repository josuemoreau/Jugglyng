/**
 * Implémentation de l'algorithme M
 * --------------------------------
 * 
 * La description de l'algorithme se trouve dans
 * The Art of Computer Programming, Volume 4, Fascicule 5
 */

#include "dlx_m.hpp"

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