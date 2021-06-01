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
