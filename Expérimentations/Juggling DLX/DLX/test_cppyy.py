import cppyy

cppyy.cppdef("""class Abstr {
public:
    virtual void print() {}
};""")

cppyy.cppdef("""void test(Abstr* t) { t->print(); }""")


class Conc(cppyy.gbl.Abstr):
    def set(self, x):
        self.x = x

    def print(self):
        print(self.x)


a = Conc()
a.set(5)
cppyy.gbl.test(a)


b = Conc()
b.set("Hello, world !")
cppyy.gbl.test(b)


# Expérimentations
cppyy.cppdef("""class Abstr {
public:
    virtual void print() {}
};""")


class Conc(cppyy.gbl.Abstr):
    def print(self):
        print(510)


std = cppyy.gbl.std
res = std.make_tuple['Abstr*', int](Conc(), 5)
(x, y) = res  # erreur


res = std.make_tuple[int, int](5, 10)
cppyy.cppdef("""void test2(std::tuple<int, int> tpl) { int x, y; std::tie(x, y) = tpl; std::cout << x << std::endl; }""")
cppyy.gbl.test2(res)  # affiche 5


res = std.make_tuple['Abstr*', int](Conc(), 5)
cppyy.cppdef("""void test3(std::tuple<Abstr*, int> tpl) { Abstr* obj; int low; std::tie(obj, low) = tpl; obj->print(); }""")
cppyy.gbl.test3(res)  # erreur parce que le Conc() a déjà été détruit !!!!


c = Conc()
res = std.make_tuple['Abstr*', int](c, 5)
cppyy.cppdef("""void test3(std::tuple<Abstr*, int> tpl) { Abstr* obj; int low; std::tie(obj, low) = tpl; obj->print(); }""")
cppyy.gbl.test3(res)  # affiche 510


c = Conc()
res = std.make_tuple['Abstr*', int](c, 5)
(x, y) = res  # fonctionne
