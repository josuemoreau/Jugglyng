from dlxm import DLXM


def print_solution(sol):
    print("Solution", sol, ":")
    for i in sol:
        for e in dlx.row_repr(i):
            if type(e) == tuple:
                print(e[0] + ":" + str(e[1]), end=" ")
            else:
                print(e, end=" ")
        print("")


def print_solutions(sols):
    for sol in sols:
        print_solution(sol)
    print("--\n%d solutions" % len(sols))


print("=== TEST 1 ===")
dlx = DLXM()
pv = dlx.new_variable(1, 1)
sv = dlx.new_variable(secondary=True)
p, q, r = pv[0], pv[1], pv[2]
x, y = sv[0], sv[1]
dlx.add_row([p, q], [(x, 0), (y, 1)])
dlx.add_row([p, r], [(x, 1), (y, 0)])
dlx.add_row([p], [(x, 2)])
dlx.add_row([q], [(x, 1)])
dlx.add_row([r], [(y, 1)])
sols = dlx.all_solutions()
print_solutions(sols)

print("=== TEST 2 ===")
dlx = DLXM()
pv = dlx.new_variable(1, 1)
dlx.add_row([pv[0], pv[1]])
dlx.add_row([pv[0], pv[2]])
dlx.add_row([pv[0]])
dlx.add_row([pv[1]])
dlx.add_row([pv[2]])
sols = dlx.all_solutions()
print_solutions(sols)

print("=== TEST 3 ===")
dlx = DLXM()
pv = dlx.new_variable(0, 5)
dlx.add_row([pv[0]])
dlx.add_row([pv[0]])
dlx.add_row([pv[0]])
dlx.add_row([pv[0]])
dlx.add_row([pv[0]])
sols = dlx.all_solutions()
print_solutions(sols)

print("=== TEST 4 ===")
dlx = DLXM()
pv = dlx.new_variable(0, 3)
dlx.add_row([pv[0]])
dlx.add_row([pv[0]])
dlx.add_row([pv[0]])
dlx.add_row([pv[0]])
dlx.add_row([pv[0]])
sols = dlx.all_solutions()
print_solutions(sols)

print("=== TEST 5 ===")
dlx = DLXM()
pv = dlx.new_variable(0, 3)
dlx.add_row([pv[0]])
dlx.add_row([pv[0]])
dlx.add_row([pv[0]])
dlx.add_row([pv[0]])
dlx.add_row([pv[0]])
sol = dlx.search()
while sol is not None:
    print_solution(sol)
    sol = dlx.search()

print("=== TEST 6 ===")
dlx = DLXM()
pv = dlx.new_variable(1, 1)
dlx.add_row([pv[0], pv[1], pv[2]])
dlx.search()
print(pv[0].get_id())
print(pv[1].get_id())
print(pv[2].get_id())

print("=== TEST 7 ===")
dlx = DLXM()
pv = dlx.new_variable(1, 1)
dlx.add_row([pv[0], pv[1], pv[2]])
dlx.compile()
print(pv[0].get_id())
print(pv[1].get_id())
print(pv[2].get_id())

