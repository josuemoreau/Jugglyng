/**
 * Implémentation de l'algorithme C
 * --------------------------------
 * 
 * La description de l'algorithme se trouve dans
 * The Art of Computer Programming, Volume 4, Fascicule 5
 */

#include <iostream>
#include <vector>
#include <unordered_map>
#include <string>
#include <functional>
#include <cmath>

#define INT long int
#define COLOR int
#define EMPTY_COLOR 0
#define IGNORE_COLOR -1

using namespace std;

struct Item {
    INT llink;
    INT rlink;
    void* name;
    INT slack;
    INT bound;

    Item(void* name, INT llink, INT rlink, INT slack, INT bound) : 
         name(name), llink(llink), rlink(rlink), slack(slack), bound(bound) {}
};

#define Primary(name, llink, rlink, slack, bound) Item(name, llink, rlink, slack, bound)
#define Secondary(name, llink, rlink) Item(name, llink, rlink, -1, -1)

enum NodeType {
    Header,
    Option
};

struct Node {
    NodeType type;
    INT tl;        // top si type = OptionNode, length si type = Header
    INT ulink;
    INT dlink;
    COLOR color;
    INT row_number;

    Node(NodeType type, INT tl, INT ulink, INT dlink, COLOR color, INT rnum) :
         type(type), tl(tl), ulink(ulink), dlink(dlink), color(color),
         row_number(rnum) {}
};

#define HNode(len, ulink, dlink, rnum) Node(Header, len, ulink, dlink, 0, rnum)
#define ONode(top, ulink, dlink, color, rnum) Node(Option, top, ulink, dlink, color, rnum)
#define SepNode(ulink, dlink) Node(Option, 0, ulink, dlink, EMPTY_COLOR, 0)

/* Définition de macros pour que le code écrit ressemble au code de Knuth */
#define DLINK(x) this->options[x].dlink
#define ULINK(x) this->options[x].ulink
#define TOP(x) this->options[x].tl
#define LEN(x) this->options[x].tl
#define CLR(x) this->options[x].color

#define LLINK(x) this->items[x].rlink
#define RLINK(x) this->items[x].llink
#define NAME(x) this->items[x].name
#define SLACK(x) this->items[x].slack
#define BOUND(x) this->items[x].bound

#define monus(x, y) max(x - y, (INT) 0)
#define branch_degree(p) monus(LEN(p) + 1, monus(BOUND(p), SLACK(p))) 

class DLX {
    public:
        DLX(vector<tuple<void*, INT, INT>> primary,
            vector<void*> secondary, 
            vector<tuple<vector<void*>, vector<tuple<void*, COLOR>>>> rows);

        void add_row(vector<void*> row_primary, 
                     vector<tuple<void*, COLOR>> row_secondary);
        
        vector<vector<INT>> all_solutions(function<void(void*)> pp);

        void print_table(function<void(void*)> pp);
        void print_rows(vector<INT> rows, function<void(void*)> pp);
        void print_solution(vector<INT> sol, function<void(void*)> pp);

    private:
        vector<Item> items;
        vector<Node> options;
        unordered_map<void*, INT> corresp;
        vector<tuple<vector<void*>, vector<tuple<void*, COLOR>>>> rows;

        INT nb_option_nodes = 1;
        INT nb_items = 0;
        INT nb_primary = 0;
        INT nb_rows = 0;

        void cover(INT i);
        void hide(INT i);
        void uncover(INT i);
        void unhide(INT i);
        void commit(INT p, INT j);
        void purify(INT p);
        void uncommit(INT p, INT j);
        void unpurify(INT p);
        void tweak(INT x, INT p);
        void tweak_special(INT x, INT p);
        void untweak(vector<INT> &ft, INT l);
        void untweak_special(vector<INT> &ft, INT l);
        INT choose();

        vector<INT> solution_lines(vector<INT> x, INT l);
};

DLX::DLX(vector<tuple<void*, INT, INT>> primary,
         vector<void*> secondary, 
         vector<tuple<vector<void*>, vector<tuple<void*, COLOR>>>> rows) {
    INT i = 0;
    void* name;
    INT u, v;

    this->items.push_back(Item(nullptr, primary.size(), 1, -1, -1));
    this->options.push_back(SepNode(0, 0));

    for (auto item : primary) {
        // le numéro de la colonne actuelle est i + 1
        // les numéros de colonnes commencent à 1
        tie(name, u, v) = item;
        this->items.push_back(Primary(name, i, i + 2, v - u, v));
        this->corresp.emplace(name, i + 1);
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
        vector<void*> row_primary;
        vector<tuple<void*, COLOR>> row_secondary;
        tie(row_primary, row_secondary) = row;
        this->add_row(row_primary, row_secondary);
    }
}

void DLX::add_row(vector<void*> row_primary, 
                  vector<tuple<void*, COLOR>> row_secondary) {
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
    
    void* element;    
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
    if (CLR(p) == EMPTY_COLOR) this->cover(j);
    else if (CLR(p) != IGNORE_COLOR) this->purify(p);
}

void DLX::purify(INT p) {
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

INT DLX::choose() {
    INT i = this->items[0].rlink;
    return i;
    INT p;

    for (p = i; p != 0; p = this->items[p].rlink)
        if (this->options[p].tl < this->options[i].tl)
            i = p;

    return i;
}

void DLX::print_table(function<void(void*)> pp) {
    cout << this->nb_items << " items (" << this->nb_primary << " primary)" << endl;

    for (auto& item : this->items) {
        cout << "Item(";
        if (item.name == nullptr) cout << "Null, ";
        else { pp(item.name); cout << ", "; }
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

vector<INT> DLX::solution_lines(vector<INT> x, INT l) {
    vector<INT> sol;
    INT i = 0;

    for (auto& opt_id : x) {
        if (i >= l || opt_id <= this->nb_items) break;

        sol.push_back(this->options[opt_id].row_number);
    }

    return sol;
}

void DLX::print_rows(vector<INT> rows, function<void(void*)> pp) {
    vector<void*> row_primary;
    vector<tuple<void*, COLOR>> row_secondary;

    for (auto& row_id : rows) {
        tie(row_primary, row_secondary) = this->rows[row_id];
        for (auto& elem : row_primary) {
            pp(elem);
            cout << " ";
        }

        for (auto& elem_color : row_secondary) {
            void* elem;
            COLOR clr;
            tie(elem, clr) = elem_color;
            pp(elem);
            cout << ":" << clr << " ";
        }

        cout << endl;
    }
}

void DLX::print_solution(vector<INT> sol, function<void(void*)> pp) {
    cout << "Solution [ ";
    for (auto& row_id : sol)
        cout << row_id << " ";
    cout << "] :" << endl;
    print_rows(sol, pp);
}

vector<vector<INT>> DLX::all_solutions(function<void(void*)> pp) {
    vector<INT> x(this->options.size());
    vector<INT> ft(this->options.size());
    INT l = 0;
    INT i, p, j, q;
    unsigned int nb_solutions = 0;

    vector<vector<INT>> solutions;

    M2: // cout << "M2" << endl;
        if (RLINK(0) == 0) {
            // cout << "====================================================" << endl;
            // cout << "Found solution :" << endl;
            // this->print_solution(x, l, pp);
            vector<INT> sol = this->solution_lines(x, l);
            solutions.push_back(sol);
            this->print_solution(sol, pp);
            nb_solutions++;
            // cout << "====================================================" << endl;
            goto M9;
        }
    M3: // cout << "M3" << endl;
        i = this->choose();
        // cout << "Choose " << i << endl;
        // cout << "Branch degree " << branch_degree(i) << endl;
        // cout << "BOUND(i) " << BOUND(i) << endl;
        if (branch_degree(i) == 0) goto M9;
    M4: // cout << "M4" << endl;
        x[l] = DLINK(i);
        BOUND(i)--;
        if (BOUND(i) == 0) this->cover(i);
        if (BOUND(i) != 0 || SLACK(i) != 0)
            ft[l] = x[l];
    M5: // cout << "M5" << endl;
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
        if (l == 0) {
            cout << "---------------------------------" << endl;
            cout << nb_solutions << " solutions found." << endl;
            cout << "---------------------------------" << endl; 
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

void pp_string(void* s) {
    cout << *((string*)s);
}

void test1() {
    string *p = new string("p");
    string *q = new string("q");
    string *r = new string("r");
    string *x = new string("x");
    string *y = new string("y");

    vector<tuple<void*, INT, INT>> primary = {
        make_tuple(p, 1, 1), 
        make_tuple(q, 1, 1), 
        make_tuple(r, 1, 1)
    };
    vector<void*> secondary = {x, y};

    DLX dlx(primary, secondary, {});
    dlx.add_row({p, q}, {make_tuple(x, EMPTY_COLOR), make_tuple(y, 1)});
    dlx.add_row({p, r}, {make_tuple(x, 1), make_tuple(y, EMPTY_COLOR)});
    dlx.add_row({p}, {make_tuple(x, 2)});
    dlx.add_row({q}, {make_tuple(x, 1)});
    dlx.add_row({r}, {make_tuple(y, 1)});
    
    dlx.print_table(pp_string);

    dlx.all_solutions(pp_string);
}

void test2() {
    string *p = new string("p");
    string *q = new string("q");
    string *r = new string("r");

    vector<tuple<void*, INT, INT>> primary = {
        make_tuple(p, 1, 1), 
        make_tuple(q, 1, 1), 
        make_tuple(r, 1, 1)
    };

    DLX dlx(primary, {}, {});
    dlx.add_row({p, q}, {});
    dlx.add_row({p, r}, {});
    dlx.add_row({p}, {});
    dlx.add_row({q}, {});
    dlx.add_row({r}, {});

    dlx.print_table(pp_string);

    dlx.all_solutions(pp_string);
}

void test3() {
    string *x = new string("x");

    vector<tuple<void*, INT, INT>> primary = {
        make_tuple(x, 0, 5)
    };

    DLX dlx(primary, {}, {});
    dlx.add_row({x}, {});
    dlx.add_row({x}, {});
    dlx.add_row({x}, {});
    dlx.add_row({x}, {});
    dlx.add_row({x}, {});

    dlx.print_table(pp_string);

    dlx.all_solutions(pp_string);
}

void test4() {
    string *x = new string("x");

    vector<tuple<void*, INT, INT>> primary = {
        make_tuple(x, 0, 3)
    };

    DLX dlx(primary, {}, {});
    dlx.add_row({x}, {});
    dlx.add_row({x}, {});
    dlx.add_row({x}, {});
    dlx.add_row({x}, {});
    dlx.add_row({x}, {});

    dlx.print_table(pp_string);

    dlx.all_solutions(pp_string);
}

int main(int argc, char** argv) {
    auto pp_string_lambda = [](void* s) {
        cout << *((string*)s);
    };

    cout << "======== TEST 1 ========" << endl;
    test1();
    cout << "======== TEST 2 ========" << endl;
    test2();
    cout << "======== TEST 3 ========" << endl;
    test3();
    cout << "======== TEST 4 ========" << endl;
    test4();
 
    return 0;
}