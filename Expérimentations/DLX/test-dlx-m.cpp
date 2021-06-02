#include "dlx-m.hpp"
#include <iostream>
#include <string>

using namespace std;
using namespace DLX_M;

class Conc : public AbstrItem {
public:
    Conc(string s) { this->s = s; }
    void print() { cout << this->s; }

private:
    string s;
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

    dlx.all_solutions();
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

    dlx.all_solutions();
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

    dlx.all_solutions();
}

void test4() {
    Conc *x = new Conc("x");
    Conc *y = new Conc("y");

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

    dlx.all_solutions();
}

int main(int argc, char** argv) {
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