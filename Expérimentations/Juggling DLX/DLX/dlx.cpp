/**
 * Implémentation de l'algorithme X
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

    Node(NodeType type, INT tl, INT ulink, INT dlink) :
         type(type), tl(tl), ulink(ulink), dlink(dlink) {}
};

class DLX {
    public:
        DLX(vector<void*> items, vector<vector<void*>> rows);
        void print_table(function<void(void*)> pp);
        void all_solutions(function<void(void*)> pp);
        void print_solution(vector<INT> sol, function<void(void*)> pp);

    private:
        vector<Item> items;
        vector<Node> options;
        unordered_map<void*, INT> corresp;
        INT nb_option_nodes = 1;

        void add_row(vector<void*> row);
        void cover(INT i);
        void hide(INT i);
        void uncover(INT i);
        void unhide(INT i);
        INT choose();
};

DLX::DLX(vector<void*> items, vector<vector<void*>> rows) {
    INT i = 0;

    this->items.push_back(Item(nullptr, items.size(), 1));
    this->options.push_back(Node(Option, 0, 0, 0));

    for (auto item : items) {
        // le numéro de la colonne actuelle est i + 1
        // les numéros de colonnes commencent à 1
        this->items.push_back(Item(item, i, i + 2));
        this->corresp.emplace(item, i + 1);
        this->options.push_back(Node(Header, 0, i + 1, i + 1));
        this->nb_option_nodes++;
        i++;
    }

    this->items.back().rlink = 0;
    this->options.push_back(Node(Option, 0, 0, 0));
    this->nb_option_nodes++;

    for (auto row : rows)
        this->add_row(row);
}

void DLX::add_row(vector<void*> row) {
    INT first_node = this->nb_option_nodes;

    for (auto option : row) {
        INT item_id = this->corresp[option];
        INT last_item_node = this->options[item_id].ulink;
        this->options.push_back(Node(Option, item_id, last_item_node, item_id));
        this->options[last_item_node].dlink = this->nb_option_nodes;
        this->options[item_id].ulink = this->nb_option_nodes;
        this->options[item_id].tl++;
        this->nb_option_nodes++;
    }

    this->options[first_node - 1].dlink = this->nb_option_nodes - 1;
    this->options.push_back(Node(Option, -1, first_node, 0));
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
        else {
            this->options[u].dlink = q;
            this->options[d].ulink = q;
            this->options[x].tl++;
            q--;
        }
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
             << option.dlink << ")" << endl;
        i++;
    }
}

void DLX::print_solution(vector<INT> sol, function<void(void*)> pp) {
    vector<vector<void*>> rows;

    for (auto& opt_id : sol) {
        if (opt_id == 0) break;
        vector<void*> row = {this->items[this->options[opt_id].tl].name};
        INT p = opt_id + 1;
        INT x;
        while (p != opt_id) {
            x = this->options[p].tl;
            if (x <= 0) p = this->options[p].ulink;
            else {
                row.push_back(this->items[x].name);
                p++;
            }
        }
        rows.push_back(row);
    }

    // print rows
    for (auto& row : rows) {
        for (auto& opt : row) {
            pp(opt);
            cout << " ";
        }
        cout << endl;
    }
}

void DLX::all_solutions(function<void(void*)> pp) {
    vector<INT> x(this->options.size());
    INT l = 0;
    INT i, p, j;

    X2: if (this->items[0].rlink == 0) {
            cout << "Found solution :" << endl;
            this->print_solution(x, pp);
            goto X8;
        }
    X3: i = this->choose();
    X4: this->cover(i);
        x[l] = this->options[i].dlink;
    X5: if (x[l] == i) goto X7;
        else {
            p = x[l] + 1;
            while (p != x[l]) {
                j = this->options[p].tl;
                if (j <= 0) p = this->options[p].ulink;
                else {
                    this->cover(j);
                    p++;
                }
            }
            l++;
            goto X2;
        }
    X6: p = x[l] - 1;
        while (p != x[l]) {
            j = this->options[p].tl;
            if (j <= 0) p = this->options[p].dlink;
            else {
                this->uncover(j);
                p--;
            }
        }
        i = this->options[x[l]].tl;
        x[l] = this->options[x[l]].dlink;
        goto X5;
    X7: this->uncover(i);
    X8: if (l == 0) return;
        else {
            l--;
            goto X6;
        }
}

void pp_string(void* s) {
    cout << *((string*)s);
}

int main(int argc, char** argv) {
    string *a = new string("a");
    string *b = new string("b");
    string *c = new string("c");
    string *d = new string("d");
    string *e = new string("e");
    string *f = new string("f");
    string *g = new string("g");

    vector<void*> items = {a, b, c, d, e, f, g};

    vector<vector<void*>> rows({
        {c, e},
        {a, d, g},
        {b, c, f},
        {a, d, f},
        {b, g},
        {d, e, g}
    });

    DLX x(items, rows);

    auto pp_string_lambda = [](void* s) {
        cout << *((string*)s);
    };

    x.print_table(pp_string_lambda);

    x.all_solutions(pp_string_lambda);

    return 0;
}