from recordclass import RecordClass
from typing import Optional, List, Dict, Tuple, Union, Any, Set

# musique = [( 1, "do"), ( 2, "do"), ( 3, "do"), 
#            ( 4, "ré"), ( 5, "mi"), ( 7, "ré"), 
#            ( 9, "do"), (10, "mi"), (11, "ré"),
#            (12, "ré"), (13, "do")]

class Throw(RecordClass):
    ball : str
    time : int
    max_height : int

    def __eq__(self, other):
        return type(other) == Throw and self.ball == other.ball and self.time == other.time and self.max_height == other.max_height

    def __hash__(self):
        return hash((self.ball, self.time, self.max_height))

def music_to_throws(music : List[Tuple[int, str]]) -> Tuple[Set[str], List[List[Throw]]]:
    notes : Set[str] = {n for t, n in music}
    sorted_music = sorted(music, key=lambda x: x[0])
    flying_note_time : Dict[str, int] = {n: 0 for n in notes}
    throws : List[List[Throw]] = []
    time = 0
    for t, n in sorted_music:
        for n1 in notes:
            flying_note_time[n1] += t - time
        for i in range(time, t):
            throws.append([])
        time = t
        throw = Throw(ball=n, time=t - flying_note_time[n], max_height=flying_note_time[n])
        throws[t - flying_note_time[n]].append(throw)
        flying_note_time[n] = 0
    return notes, throws

class XItem(RecordClass):
    throw : Throw
    hand : int
    flying_time : int

class LItem(RecordClass):
    throw : Throw

class WItem(RecordClass):
    time : int
    hand : int

class IItem(RecordClass):
    time : int
    hand : int
    flying_time : int

class MItem(RecordClass):
    time : int
    hand : int
    multiplex : Tuple[int,]

def throws_to_extended_exact_cover(balls : Set[str], throws : List[List[Throw]], 
                                   nb_hands : int, H : int, K : int,
                                   forbidden_multiplex : List[Tuple[int,]],
                                   forbidden_2sequences : List[Tuple[int, int]]):
    max_time = 0
    x_items = {}
    l_items = {}
    w_items = {}
    i_items = {}
    m_items = {}
    fmultiplex : Dict[int, List[Tuple[int,]]] = {i: [] for i in range(1, H + 1)}
    f2seqs : Dict[int, List[int]] = {i: [] for i in range(1, H + 1)}
    rows = []
    # Remplissage du dictionnaire des lancers multiplex interdits
    for fm in forbidden_multiplex:
        for i in fm:
            fmultiplex[i].append(fm)
    # Remplissage du dictionnaire des séquences de 2 lancers interdits
    for fs in forbidden_2sequences:
        f2seqs[fs[0]].append(fs[1])
    # Calcul du plus tard temps où atterrit une balle
    for t in range(len(throws) - 1, -1, -1):
        if len(throws[t]) > 0:
            max_height = 0
            for throw in throws[t]:
                if throw.max_height > max_height:
                    max_height = throw.max_height
            max_time = t + max_height
            break
    # Génération des items x et I
    for t in range(len(throws)):
        for throw in throws[t]:
            l = LItem(throw=throw)
            l_items[throw] = l

            for hand in range(nb_hands):
                for flying_time in range(1, min(H, throw.max_height) + 1):
                    x = XItem(throw=throw, hand=hand, flying_time=flying_time)
                    x_items[(throw, hand, flying_time)] = x
    # Génération des items w
    for t in range(max_time + 1):
        for hand in range(nb_hands):
            w = WItem(time=t, hand=hand)
            w_items[(t, hand)] = w

            for f in forbidden_multiplex:
                m = MItem(time=t, hand=hand, multiplex=f)
                m_items[(t, hand, f)] = m
    # Génération des items I
    for t in range(max_time + 1):
        for hand in range(nb_hands):
            for flying_time in range(1, H + 1):
                i = IItem(time=t, hand=hand, flying_time=flying_time)
                i_items[(t, hand, flying_time)] = i
    # Génération des lignes
    for t in range(len(throws)):
        for throw in throws[t]:
            for hand in range(nb_hands):
                for flying_time in range(1, min(H, throw.max_height) + 1):
                    row = [x_items[(throw, hand, flying_time)], l_items[throw]]
                    if flying_time == throw.max_height:
                        row.append(i_items[(t, hand, flying_time)])
                    for fmulti in fmultiplex[flying_time]:
                        row.append(m_items[(t + throw.max_height - flying_time, hand, fm)])
                    for fnext in f2seqs[flying_time]:
                        row.append(i_items[(t + 1, hand, fnext)])
                    rows.append(row)

    return list(x_items.values()), list(l_items.values()), list(w_items.values()), list(i_items.values()), list(m_items.values()), rows
        