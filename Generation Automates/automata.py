from graphviz import Digraph

class Automata():
    def __init__(self, nb_balls : int, max_height : int):
        self.max_height = max_height
        self.initial = [i < nb_balls for i in range(max_height)]
    
    def transition(self, state : list[bool], time : int):
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
                    if not s in states and not s in queue:
                        queue.append(s)
                except Exception as e:
                    if e.args[0] != "conflict":
                        raise e
        
        return states, transitions

    def state_str(self, s : list[bool]):
        s1 = ["o" if x else "x" for x in s]
        return "".join(s1)

    def draw(self):
        states, transitions = self.generate()
        dot = Digraph(comment='Juggling Automata', graph_attr={'layout': 'circo'})
        for s in states:
            dot.node(self.state_str(s))
        for (s1, a, s2) in transitions:
            dot.edge(self.state_str(s1), self.state_str(s2), label=str(a), constraint='true')
        dot.render('automata-output/automata.gv', view=True)


if __name__ == "__main__":
    a = Automata(3, 5)

    a.draw()