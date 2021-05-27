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

#define INT long int
#define COLOR int
#define EMPTY_COLOR 0
#define IGNORE_COLOR -1

using namespace std;

struct Item {
    INT llink;
    INT rlink;
    void* name;

    Item(void* name, INT llink, INT rlink) : 
         name(name), llink(llink), rlink(rlink) {}
};

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

class DLX {
    public:
        DLX(vector<void*> primary, vector<void*> secondary, 
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
        void cover(INT i);
        void hide(INT i);
        void uncover(INT i);
        void unhide(INT i);
        void commit(INT p, INT j);
        void purify(INT p);
        void uncommit(INT p, INT j);
        void unpurify(INT p);
        INT choose();
};

DLX::DLX(vector<void*> primary, vector<void*> secondary, 
         vector<tuple<vector<void*>, vector<tuple<void*, COLOR>>>> rows) {
    INT i = 0;

    this->items.push_back(Item(nullptr, primary.size(), 1));
    this->options.push_back(ONode(0, 0, 0, EMPTY_COLOR));

    for (auto item : primary) {
        // le numéro de la colonne actuelle est i + 1
        // les numéros de colonnes commencent à 1
        this->items.push_back(Item(item, i, i + 2));
        this->corresp.emplace(item, i + 1);
        this->options.push_back(HNode(0, i + 1, i + 1));
        this->nb_option_nodes++;
        i++;
    }
    this->items.back().rlink = 0;
    
    INT j = i + 1;
    for (auto item : secondary) {
        this->items.push_back(Item(item, i, i + 2));
        this->corresp.emplace(item, i + 1);
        this->options.push_back(HNode(0, i + 1, i + 1));
        this->nb_option_nodes++;
        i++;
    }
    this->items.push_back(Item(nullptr, i, j));
    this->items[j].llink = i + 1;
    
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
        if (item.name == nullptr) {
            cout << "Item(Null, "
                 << item.llink << ", "
                 << item.rlink << ")" << endl;
        } else {
            cout << "Item(";
            pp(item.name);
            cout << ", "
                 << item.llink << ", "
                 << item.rlink << ")" << endl;
        }
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
    INT l = 0;
    INT i, p, j;

    C2: if (this->items[0].rlink == 0) {
            cout << "Found solution :" << endl;
            this->print_solution(x, pp);
            goto C8;
        }
    C3: i = this->choose();
    C4: this->cover(i);
        x[l] = this->options[i].dlink;
    C5: if (x[l] == i) goto C7;
        else {
            p = x[l] + 1;
            while (p != x[l]) {
                j = this->options[p].tl;
                if (j <= 0) p = this->options[p].ulink;
                else {
                    this->commit(p, j);
                    p++;
                }
            }
            l++;
            goto C2;
        }
    C6: p = x[l] - 1;
        while (p != x[l]) {
            j = this->options[p].tl;
            if (j <= 0) p = this->options[p].dlink;
            else {
                this->uncommit(p, j);
                p--;
            }
        }
        i = this->options[x[l]].tl;
        x[l] = this->options[x[l]].dlink;
        goto C5;
    C7: this->uncover(i);
    C8: if (l == 0) return;
        else {
            l--;
            goto C6;
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

    vector<void*> primary = {p, q, r};
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