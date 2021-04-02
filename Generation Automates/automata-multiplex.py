from graphviz import Digraph
from sage.all import Combinations

class Automata():
    def __init__(self, nb_balls : int, max_height : int):
        self.max_height = max_height
        self.nb_balls = nb_balls
        self.initial = [1 if i < nb_balls else 0 for i in range(max_height)]
    
    def transition(self, state : list[int], times : list[int]):
        s = state.copy()
        r = s[0]
        del s[0]
        s.append(0)

        if r >= 0 and len(times) == r:
            for t in times:
                s[t - 1] += 1
        else:
            raise Exception("error")
        return s

    def generate(self):
        states = []
        transitions = []
        queue = [self.initial]

        while queue != []:
            state = queue.pop()
            states.append(state)
            for c in Combinations(state[0] * list(range(1, self.max_height + 1)), state[0]):
                try:
                    s = self.transition(state, c)
                    transitions.append((state, c, s))
                    if not s in states and not s in queue:
                        queue.append(s)
                except Exception as e:
                    if e.args[0] != "error":
                        raise e
        
        return states, transitions

    def state_str(self, s : list[int]):
        s1 = [str(x) for x in s]
        return "".join(s1)

    def draw(self):
        states, transitions = self.generate()
        dot = Digraph(comment='Juggling Automata', graph_attr={'layout': 'dot'})
        for s in states:
            dot.node(self.state_str(s))
        for (s1, a, s2) in transitions:
            dot.edge(self.state_str(s1), self.state_str(s2), label=str(a), constraint='true')
        dot.render('automata-output/automata-multiplex-'
                    + str(self.nb_balls) + '-'
                    + str(self.max_height)
                    + '.gv', view=True)


if __name__ == "__main__":
    a = Automata(3, 5)

    a.draw()