from graphviz import Digraph
from typing import List


class Automata():
    def __init__(self, nb_balls: int, max_height: int):
        self.nb_balls = nb_balls
        self.max_height = max_height
        self.initial = [i < nb_balls for i in range(max_height)]

    def transition(self, state: List[bool], time: int):
        s = state.copy()
        r = s[0]
        del s[0]
        s.append(False)

        if r and time > 0:
            if s[time - 1]:
                raise Exception("conflict")
            else:
                s[time - 1] = True
        elif r:
            raise Exception("conflict")
        elif time > 0:
            raise Exception("conflict")
        return s

    def generate(self):
        states = []
        transitions = []
        queue = [self.initial]

        while queue != []:
            state = queue.pop()
            states.append(state)
            for time in range(self.max_height + 1):
                try:
                    s = self.transition(state, time)
                    transitions.append((state, time, s))
                    if s not in states and s not in queue:
                        queue.append(s)
                except Exception as e:
                    if e.args[0] != "conflict":
                        raise e

        return states, transitions

    def possible_transitions(self, state: List[bool]):
        transitions = {}

        for time in range(self.max_height + 1):
            try:
                s = self.transition(state, time)
                transitions[time] = s
            except Exception as e:
                if e.args[0] != "conflict":
                    raise e

        return transitions

    def state_str(self, s: List[bool]):
        s1 = ["o" if x else "x" for x in s]
        return "".join(s1)

    def draw(self):
        states, transitions = self.generate()
        dot = Digraph(comment='Juggling Automata', graph_attr={'layout': 'dot'})
        for s in states:
            dot.node(self.state_str(s))
        for (s1, a, s2) in transitions:
            dot.edge(self.state_str(s1), self.state_str(s2), label=str(a), constraint='true')
        dot.render('automata-output/automata.gv', view=True)


if __name__ == "__main__":
    a = Automata(3, 5)

    a.draw()
