#include "dlx_m.hpp"
#include <iostream>
#include <string>

using namespace std;
using namespace DLX_M;

class Conc : public AbstrItem {
public:
    Conc(string s) { this->s = s; }
    void print() { cout << this->s; }
    void set_id(INT i) { this->dlx_id = i; }
    INT get_id() { return this->dlx_id; }

private:
    string s;
    INT dlx_id = 0;
};

void test1() {
    Conc *p = new Conc("p");
    Conc *q = new Conc("q");
    Conc *r = new Conc("r");
    Conc *x = new Conc("x");
    Conc *y = new Conc("y");

    vector<tuple<AbstrItem*, INT, INT>> primary = {
        make_tuple(p, 1, 1), 
        make_tuple(q, 1, 1), 
        make_tuple(r, 1, 1)
    };
    vector<AbstrItem*> secondary = {x, y};

    DLX dlx(primary, secondary, {});
    dlx.add_row({p, q}, {make_tuple(x, EMPTY_COLOR), make_tuple(y, 1)});
    dlx.add_row({p, r}, {make_tuple(x, 1), make_tuple(y, EMPTY_COLOR)});
    dlx.add_row({p}, {make_tuple(x, 2)});
    dlx.add_row({q}, {make_tuple(x, 1)});
    dlx.add_row({r}, {make_tuple(y, 1)});
    
    dlx.print_table();

    dlx.all_solutions(true);
}

void test2() {
    Conc *p = new Conc("p");
    Conc *q = new Conc("q");
    Conc *r = new Conc("r");

    vector<tuple<AbstrItem*, INT, INT>> primary = {
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

    dlx.print_table();

    dlx.all_solutions(true);
}

void test3() {
    Conc *x = new Conc("x");

    vector<tuple<AbstrItem*, INT, INT>> primary = {
        make_tuple(x, 0, 5)
    };

    DLX dlx(primary, {}, {});
    dlx.add_row({x}, {});
    dlx.add_row({x}, {});
    dlx.add_row({x}, {});
    dlx.add_row({x}, {});
    dlx.add_row({x}, {});

    dlx.print_table();

    dlx.all_solutions(true);
}

void test4() {
    Conc *x = new Conc("x");

    vector<tuple<AbstrItem*, INT, INT>> primary = {
        make_tuple(x, 0, 3)
    };

    DLX dlx(primary, {}, {});
    dlx.add_row({x}, {});
    dlx.add_row({x}, {});
    dlx.add_row({x}, {});
    dlx.add_row({x}, {});
    dlx.add_row({x}, {});

    dlx.print_table();

    dlx.all_solutions(true);
}

void test5() {
    Conc *a = new Conc("a");
    Conc *b = new Conc("b");
    Conc *c = new Conc("c");

    vector<tuple<AbstrItem*, INT, INT>> primary = {
        make_tuple(a, 0, 1),
        make_tuple(b, 1, 1),
        make_tuple(c, 0, 1)
    };

    DLX dlx(primary, {}, {});
    dlx.add_row({a, b, c}, {});
    dlx.add_row({b}, {});
    dlx.add_row({c}, {});

    dlx.print_table();

    dlx.all_solutions(true);
}

void test6() {
    Conc *a = new Conc("a");
    Conc *b = new Conc("b");
    Conc *c = new Conc("c");

    vector<tuple<AbstrItem*, INT, INT>> primary = {
        make_tuple(a, 1, 1),
        make_tuple(b, 1, 1)
    };

    DLX dlx(primary, {c}, {});
    dlx.add_row({a}, {make_tuple(c, 0)});
    dlx.add_row({a}, {make_tuple(c, 3)});
    dlx.add_row({b}, {make_tuple(c, 0)});
    dlx.add_row({b}, {make_tuple(c, 3)});

    dlx.print_table();

    dlx.all_solutions(true);
}

void test7() {
    Conc *a = new Conc("a");
    Conc *b = new Conc("b");
    Conc *e = new Conc("e");

    vector<tuple<AbstrItem*, INT, INT>> primary = {
        make_tuple(a, 1, 1),
        make_tuple(b, 1, 1)
    };

    DLX dlx(primary, {e}, {});
    dlx.add_row({a}, {make_tuple(e, 0)});
    dlx.add_row({b}, {make_tuple(e, 0)});

    dlx.print_table();

    dlx.all_solutions(true);
}

void test8() {
    Conc *a = new Conc("a");
    Conc *b = new Conc("b");
    Conc *c = new Conc("c");

    vector<tuple<AbstrItem*, INT, INT>> primary = {
        make_tuple(a, 0, 1),
        make_tuple(b, 1, 1),
        make_tuple(c, 0, 1)
    };

    DLX dlx(primary, {}, {});
    dlx.add_row({a, b, c}, {});
    dlx.add_row({b}, {});
    dlx.add_row({c}, {});

    dlx.print_table();

    try {
        dlx.print_solution(dlx.search(false));
        dlx.print_solution(dlx.search(true));
        dlx.print_solution(dlx.search(true));
        dlx.print_solution(dlx.search(true));
    } catch (const NoSolution& e) {
        cout << "No solution !" << endl;
    }
    
}

void test9() {
    Conc *a = new Conc("a");
    Conc *b = new Conc("b");
    Conc *c = new Conc("c");

    vector<tuple<AbstrItem*, INT, INT>> primary = {
        make_tuple(a, 0, 1),
        make_tuple(b, 1, 1),
        make_tuple(c, 0, 1)
    };

    DLX dlx(primary, {}, {});

    cout << "a : " << a->get_id() << endl;
    cout << "b : " << b->get_id() << endl;
    cout << "c : " << c->get_id() << endl;
}

int main(int argc, char** argv) {
    // cout << "======== TEST 1 ========" << endl;
    // test1();
    // cout << "======== TEST 2 ========" << endl;
    // test2();
    // cout << "======== TEST 3 ========" << endl;
    // test3();
    // cout << "======== TEST 4 ========" << endl;
    // test4();
    cout << "======== TEST 5 ========" << endl;
    test5();
    // cout << "======== TEST 6 ========" << endl;
    // test6();
    // cout << "======== TEST 7 ========" << endl;
    // test7();
    cout << "======== TEST 8 ========" << endl;
    test8();
    cout << "======== TEST 9 ========" << endl;
    test9();

    return 0;
}