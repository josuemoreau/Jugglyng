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

    Node(NodeType type, INT tl, INT ulink, INT dlink, COLOR color) :
         type(type), tl(tl), ulink(ulink), dlink(dlink), color(color) {}
};

#define HNode(len, ulink, dlink) Node(Header, len, ulink, dlink, 0)
#define ONode(top, ulink, dlink, color) Node(Option, top, ulink, dlink, color)

#define monus(x, y) max(x - y, (INT) 0)
#define branch_degree(p) monus(this->options[p].tl + 1, \
                               monus(this->items[p].bound, this->items[p].slack)) 

class DLX {
    public:
        DLX(vector<tuple<void*, INT, INT>> primary,
            vector<void*> secondary, 
            vector<tuple<vector<void*>, vector<tuple<void*, COLOR>>>> rows);
        void print_table(function<void(void*)> pp);
        void all_solutions(function<void(void*)> pp);
        void print_solution(vector<INT> sol, function<void(void*)> pp);

        void add_row(vector<void*> row_primary, 
                     vector<tuple<void*, COLOR>> row_secondary);

    private:
        vector<Item> items;
        vector<Node> options;
        unordered_map<void*, INT> corresp;

        INT nb_option_nodes = 1;
        INT nb_items = 0;
        INT nb_primary = 0;

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
};

DLX::DLX(vector<tuple<void*, INT, INT>> primary,
         vector<void*> secondary, 
         vector<tuple<vector<void*>, vector<tuple<void*, COLOR>>>> rows) {
    INT i = 0;
    void* name;
    INT u, v;

    this->items.push_back(Item(nullptr, primary.size(), 1, -1, -1));
    this->options.push_back(ONode(0, 0, 0, EMPTY_COLOR));

    for (auto item : primary) {
        // le numéro de la colonne actuelle est i + 1
        // les numéros de colonnes commencent à 1
        tie(name, u, v) = item;
        this->items.push_back(Primary(name, i, i + 2, v - u, v));
        this->corresp.emplace(name, i + 1);
        this->options.push_back(HNode(0, i + 1, i + 1));
        this->nb_option_nodes++;
        i++;
    }
    this->items.back().rlink = 0;

    this->nb_primary = this->nb_option_nodes - 1;
    
    INT j = i + 1;
    for (auto item : secondary) {
        this->items.push_back(Secondary(item, i, i + 2));
        this->corresp.emplace(item, i + 1);
        this->options.push_back(HNode(0, i + 1, i + 1));
        this->nb_option_nodes++;
        i++;
    }
    this->items.push_back(Secondary(nullptr, i, j));
    this->items[j].llink = i + 1;

    this->nb_items = this->nb_option_nodes - 1;
    
    this->options.push_back(ONode(0, 0, 0, EMPTY_COLOR));
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

    for (auto option : row_primary) {
        item_id = this->corresp[option];
        last_item_node = this->options[item_id].ulink;
        this->options.push_back(ONode(item_id, last_item_node, item_id, EMPTY_COLOR));
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
        this->options.push_back(ONode(item_id, last_item_node, item_id, color));
        this->options[last_item_node].dlink = this->nb_option_nodes;
        this->options[item_id].ulink = this->nb_option_nodes;
        this->options[item_id].tl++;
        this->nb_option_nodes++;
    }

    this->options[first_node - 1].dlink = this->nb_option_nodes - 1;
    this->options.push_back(ONode(-1, first_node, 0, EMPTY_COLOR));
    this->nb_option_nodes++;
}

void DLX::cover(INT i) {
    INT p = this->options[i].dlink;
    INT l = this->items[i].llink;
    INT r = this->items[i].rlink;
    while (p != i) {
        this->hide(p);
        p = this->options[p].dlink;
    }
    this->items[l].rlink = r;
    this->items[r].llink = l;
}

void DLX::hide(INT p) {
    INT q = p + 1;
    INT x, u, d;
    while (q != p) {
        x = this->options[q].tl;
        u = this->options[q].ulink;
        d = this->options[q].dlink;
        if (x <= 0) q = u;
        else if (this->options[q].color == IGNORE_COLOR) q++;
        else {
            this->options[u].dlink = d;
            this->options[d].ulink = u;
            this->options[x].tl--;
            q++;
        }
    }
}

void DLX::uncover(INT i) {
    INT p = this->options[i].ulink;
    INT l = this->items[i].llink;
    INT r = this->items[i].rlink;
    this->items[l].rlink = i;
    this->items[r].llink = i;
    while (p != i) {
        this->unhide(p);
        p = this->options[p].ulink;
    }
}

void DLX::unhide(INT p) {
    INT q = p - 1;
    INT x, u, d;
    while (q != p) {
        x = this->options[q].tl;
        u = this->options[q].ulink;
        d = this->options[q].dlink;
        if (x <= 0) q = d;
        else if (this->options[q].color == IGNORE_COLOR) q--;
        else {
            this->options[u].dlink = q;
            this->options[d].ulink = q;
            this->options[x].tl++;
            q--;
        }
    }
}

void DLX::commit(INT p, INT j) {
    if (this->options[p].color == EMPTY_COLOR) this->cover(j);
    else if (this->options[p].color != IGNORE_COLOR) this->purify(p);
}

void DLX::purify(INT p) {
    COLOR c = this->options[p].color;
    INT i = this->options[p].tl;
    INT q = this->options[i].dlink;
    while (q != i) {
        if (this->options[q].color == c) this->options[q].color = IGNORE_COLOR;
        else this->hide(q);
        q = this->options[q].dlink;
    }
}

void DLX::uncommit(INT p, INT j) {
    if (this->options[p].color == EMPTY_COLOR) this->uncover(j);
    else if (this->options[p].color != IGNORE_COLOR) this->unpurify(p);
}

void DLX::unpurify(INT p) {
    COLOR c = this->options[p].color;
    INT i = this->options[p].tl;
    INT q = this->options[i].ulink;
    while (q != i) {
        if (this->options[q].color == IGNORE_COLOR) this->options[q].color = c;
        else this->unhide(q);
        q = this->options[q].ulink;
    }
}

void DLX::tweak(INT x, INT p) {
    this->hide(x);
    INT d = this->options[x].dlink;
    this->options[p].dlink = d;
    this->options[d].ulink = p;
    this->options[p].tl--;
}

void DLX::tweak_special(INT x, INT p) {
    INT d = this->options[x].dlink;
    this->options[p].dlink = d;
    this->options[d].ulink = p;
    this->options[p].tl--;
}

void DLX::untweak(vector<INT> &ft, INT l) {
    INT a = ft[l], x = a, k = 0;
    INT p = (a <= this->nb_items) ? a : this->options[a].tl;
    INT y = p;
    INT z = this->options[p].dlink;
    this->options[p].dlink = x;
    while (x != z) {
        this->options[x].ulink = y;
        k++;
        this->unhide(x);
        y = x;
        x = this->options[x].dlink;
    }
    this->options[z].ulink = y;
    this->options[p].tl += k;
}

void DLX::untweak_special(vector<INT> &ft, INT l) {
    INT a = ft[l], x = a, k = 0;
    INT p = (a <= this->nb_items) ? a : this->options[a].tl;
    INT y = p;
    INT z = this->options[p].dlink;
    this->options[p].dlink = x;
    while (x != z) {
        this->options[x].ulink = y;
        k++;
        y = x;
        x = this->options[x].dlink;
    }
    this->options[z].ulink = y;
    this->options[p].tl += k;
    this->uncover(p);
}

INT DLX::choose() {
    INT i = this->items[0].rlink;
    INT p;

    for (p = i; p != 0; p = this->items[p].rlink)
        if (this->options[p].tl < this->options[i].tl)
            i = p;

    return i;
}

void DLX::print_table(function<void(void*)> pp) {
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

void DLX::print_solution(vector<INT> sol, function<void(void*)> pp) {
    vector<vector<tuple<void*, COLOR>>> rows;
    unordered_map<INT, COLOR> colors;
    COLOR color;
    INT p, x;

    for (auto& opt_id : sol) {
        if (opt_id == 0) break;

        x = this->options[opt_id].tl;
        color = this->options[opt_id].color;
        if (color != EMPTY_COLOR)
            colors.emplace(x, color);
        
        vector<tuple<void*, COLOR>> row = 
            {make_tuple(this->items[x].name, color)};
        
        p = opt_id + 1;
        while (p != opt_id) {
            x = this->options[p].tl;
            color = this->options[p].color;
            if (x <= 0) p = this->options[p].ulink;
            else {
                if (color == IGNORE_COLOR)
                    color = colors[x];
                else if (color != EMPTY_COLOR)
                    colors.emplace(x, color);
                row.push_back(make_tuple(this->items[x].name, color));
                p++;
            }
        }
        rows.push_back(row);
    }

    // print rows
    void* name;
    for (auto& row : rows) {
        for (auto& opt : row) {
            tie(name, color) = opt;
            pp(name);
            if (color != EMPTY_COLOR) cout << ":" << color;
            cout << " ";
        }
        cout << endl;
    }
}

void DLX::all_solutions(function<void(void*)> pp) {
    vector<INT> x(this->options.size());
    vector<INT> ft(this->options.size());
    INT l = 0;
    INT i, p, j, q;

    M2: if (this->items[0].rlink == 0) {
            cout << "Found solution :" << endl;
            this->print_solution(x, pp);
            goto M9;
        }
    M3: i = this->choose();
        if (branch_degree(i)) goto M9;
    M4: x[l] = this->options[i].dlink;
        this->items[i].bound--;
        if (this->items[i].bound == 0) this->cover(i);
        if (this->items[i].bound != 0 || this->items[i].slack != 0)
            ft[l] = x[l];
    M5: if (this->items[i].bound == 0 && this->items[i].slack == 0) {
            if (x[l] != i) goto M6;
            else goto M8;
        } else if (this->options[i].tl <= this->items[i].bound - this->items[i].slack) {
            goto M8;
        } else if (x[l] != i) {
            if (this->items[i].bound == 0) this->tweak_special(x[l], i);
            else this->tweak(x[l], i);
        } else if (this->items[i].bound != 0) {
            p = this->items[i].llink;
            q = this->items[i].rlink;
            this->items[p].rlink = q;
            this->items[q].llink = p;
        }
    M6: if (x[l] != i) {
            p = x[l] + 1;
            while (p != x[l]) {
                j = this->options[p].tl;
                if (j <= 0) p = this->options[p].ulink;
                else if (j <= this->nb_primary) {
                    this->items[j].bound--;
                    p++;
                    if (this->items[j].bound == 0) this->cover(j);
                } else {
                    this->commit(p, j);
                    p++;
                }
            }
            l++;
            goto M2;
        }
    M7: if (x[l] != i) {
            p = x[l] - 1;
            while (p != x[l]) {
                j = this->options[p].tl;
                if (j <= 0) p = this->options[p].dlink;
                else if (j <= this->nb_primary) {
                    this->items[j].bound++;
                    p--;
                    if (this->items[j].bound == 1) this->uncover(j);
                } else {
                    this->uncommit(p, j);
                    p--;
                }
            }
            x[l] = this->options[x[l]].dlink;
            goto M5;
        }
    M8: if (this->items[i].bound == 0 && this->items[i].slack == 0)
            this->uncover(i);
        else if (this->items[i].bound == 0) this->untweak_special(ft, l);
        else this->untweak(ft, l);
        this->items[i].bound++;
    M9: if (l == 0) return;
        else {
            l--;
            if (x[l] <= this->nb_items) {
                i = x[l];
                p = this->items[i].llink;
                q = this->items[i].rlink;
                this->items[p].rlink = i;
                this->items[q].llink = i;
                goto M8;
            } else {
                i = this->options[x[l]].tl;
                goto M7;
            }
        }
}

void pp_string(void* s) {
    cout << *((string*)s);
}

int main(int argc, char** argv) {
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

    vector<tuple<vector<void*>, vector<tuple<void*, COLOR>>>> rows;

    DLX dlx(primary, secondary, {});
    dlx.add_row({p, q}, {make_tuple(x, EMPTY_COLOR), make_tuple(y, 1)});
    dlx.add_row({p, r}, {make_tuple(x, 1), make_tuple(y, EMPTY_COLOR)});
    dlx.add_row({p}, {make_tuple(x, 2)});
    dlx.add_row({q}, {make_tuple(x, 1)});
    dlx.add_row({r}, {make_tuple(y, 1)});

    auto pp_string_lambda = [](void* s) {
        cout << *((string*)s);
    };

    dlx.print_table(pp_string_lambda);

    dlx.all_solutions(pp_string_lambda);

    return 0;
}