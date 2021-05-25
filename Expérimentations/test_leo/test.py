import numpy as np
import networkx as nx

def enumerate_list_states(b, h):
    if h < b:
        return
    elif h == b:
        yield ["1"]*h
    elif b < 0:
        yield ["0"]*h
    else:
        for substate in enumerate_list_states(b, h-1):
            substate.append("0")
            yield substate
        for substate in enumerate_list_states(b-1, h-1):
            substate.append("1")
            yield substate

def enumerate_states(b, h):
    for state in enumerate_list_states(b, h):
        yield "".join(state)

def get_next_lstate(state):
    lstate = list(state[1:])
    lstate.append("0")
    return lstate

G = nx.DiGraph()
b = 3
h = 5
G.add_nodes_from(enumerate_states(b, h))
for state in G.nodes:
    next_lstate = get_next_lstate(state)
    if state[0] == 0:
        G.add_edge(state, "".join(next_lstate))
    else:
        for i, elem in enumerate(next_lstate):
            if elem == 0:
                next_lstate[i] = 1
                G.add_edge(state, next_lstate.split(""))
                next_lstate[i] = 0