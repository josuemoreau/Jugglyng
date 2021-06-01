#include <vector>
#include <unordered_map>
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
            vector<tuple<vector<void*>, vector<tuple<void*, COLOR>>>> rows,
            function<void(void*)> pp);

        DLX(vector<tuple<void*, INT, INT>> primary,
            vector<void*> secondary, 
            vector<tuple<vector<void*>, vector<tuple<void*, COLOR>>>> rows) :
            DLX(primary, secondary, rows, nullptr) {};

        void add_row(vector<void*> row_primary, 
                     vector<tuple<void*, COLOR>> row_secondary);
        
        vector<vector<INT>> all_solutions();

        void print_table();
        void print_rows(vector<INT> rows);
        void print_solution(vector<INT> sol);

    private:
        vector<Item> items;
        vector<Node> options;
        unordered_map<void*, INT> corresp;
        vector<tuple<vector<void*>, vector<tuple<void*, COLOR>>>> rows;

        function<void(void*)> pp;

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