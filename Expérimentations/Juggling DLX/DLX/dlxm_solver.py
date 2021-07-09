from dlxm import DLXM


if __name__ == "__main__":
    vars_line = input()
    primary_mode = True
    primary_vars = []
    secondary_vars = []
    for p in vars_line.split(' '):
        if p == "":
            continue
        if p == "|":
            primary_mode = False
        elif primary_mode:
            d = p.split('|')
            if len(d) == 1:
                primary_vars.append((d[0], 1, 1))
            elif len(d) == 2:
                b = d[0].split(':')
                if len(b) == 2:
                    primary_vars.append((d[1], int(b[0]), int(b[1])))
                else:
                    print('syntax error on bounds')
                    exit(1)
            else:
                print('syntax error in primary items')
                exit(1)
        else:
            secondary_vars.append(p)
    print("primary :", primary_vars)
    print("secondary :", secondary_vars)

    dlx = DLXM()
    d_primary = {}
    vars_primary = {}
    for (v, l, h) in primary_vars:
        if (l, h) not in d_primary:
            d_primary[(l, h)] = dlx.new_variable(l, h)
    vars_secondary = dlx.new_variable(secondary=True)

    for (v, l, h) in primary_vars:
        vars_primary[v] = d_primary[(l, h)][v]

    while True:
        try:
            line = input()
            if line.strip()[0] == "#":
                continue
            row_primary = []
            row_secondary = []
            for v in line.split(' '):
                if v in vars_primary:
                    row_primary.append(vars_primary[v])
                else:
                    s = v.split(':')
                    if len(s) == 2:
                        row_secondary.append((vars_secondary[s[0]], int(s[1])))
                    else:
                        print('syntax error on secondary item on line ' + line)
                        exit(1)
            dlx.add_row(row_primary, row_secondary)
        except EOFError:
            break

    for i in range(len(dlx.rows)):
        print(dlx.row_obj(i))

    dlx.all_solutions(True)
