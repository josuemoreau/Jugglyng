#include <vector>
#include <unordered_map>
#include <functional>
#include <cmath>
#include <stdexcept>

namespace DLX_M {

typedef long int INT;
typedef int COLOR;

#define EMPTY_COLOR 0
#define IGNORE_COLOR -1

using namespace std;

class AbstrItem {
public:
    virtual void print() {}
    virtual void set_id(INT) {}
    virtual INT get_id() { return 0; }
};

struct Item {
    INT llink;
    INT rlink;
    AbstrItem* name;
    INT slack;
    INT bound;

    Item(AbstrItem* name, INT llink, INT rlink, INT slack, INT bound) : 
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

class NoSolution : public std::exception {
    public:
        const char *what() const throw() {
            return "No solution !";
        }
};

class DLX {
    public:
        DLX(vector<tuple<AbstrItem*, INT, INT>> primary,
            vector<AbstrItem*> secondary, 
            vector<tuple<vector<AbstrItem*>, vector<tuple<AbstrItem*, COLOR>>>> rows);
        DLX(vector<tuple<AbstrItem*, INT, INT>> primary,
            vector<AbstrItem*> secondary, 
            vector<tuple<vector<AbstrItem*>, vector<tuple<AbstrItem*, COLOR>>>> rows,
            function<INT(DLX*)> choose);

        void add_row(vector<AbstrItem*> row_primary, 
                     vector<tuple<AbstrItem*, COLOR>> row_secondary);
        
        vector<vector<INT>> all_solutions(bool verbose = false);
        vector<INT> search(bool resume);
        // vector<INT> get_solution();

        vector<INT> solution_rows(vector<INT> x, INT l);

        void print_table();
        void print_rows(vector<INT> rows);
        void print_solution(vector<INT> sol);

        Item item(INT i) { return this->items[i]; }
        Node option(INT i) { return this->options[i]; }

        bool is_covered(INT i) { return this->covered[i]; }

        void set_choose_function(function<INT(DLX*)> choose) { this->choose = choose; }

    private:
        vector<Item> items;
        vector<Node> options;
        unordered_map<AbstrItem*, INT> corresp;
        vector<tuple<vector<AbstrItem*>, vector<tuple<AbstrItem*, COLOR>>>> rows;

        INT nb_option_nodes = 1;
        INT nb_items = 0;
        INT nb_primary = 0;
        INT nb_rows = 0;

        // Variables de sauvegarde de l'état de la recherche
        vector<INT> x;
        vector<INT> ft;
        INT l, i, p, j, q;

        function<INT(DLX*)> choose;
        bool *covered;

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
        // INT choose();
};

}