from collections import namedtuple
from enum import Enum
import random as rd
from copy import deepcopy

#Erreurs
class JugglingError(Exception):
    pass

class TooMuchBallsInHand(Exception):
    pass

class EmptyHand(Exception):
    pass



class MultihandSequence():
    def __init__(self, balls, seq):
        self.sequence = seq
        self.nb_hands = len(seq)
        self.ball_names = self.get_balls()
    
    def get_balls(self):
        return set(throw.ball for hand in self.sequence for throw in hand)

    def simulate(self):
        pass

#pieces de puzzle pas compatibles

class Hand():
    def __init__(self, balls):
        if len(balls) > 4:
            raise TooMuchBallsInHand()
        self.balls = balls
        #Pas plus de 4 balles ?

    def swap(self):
        nb_balls = len(self.balls)
        self.balls = [self.balls[(i+1) % nb_balls] for i in range(nb_balls)]

    def catch(self, ball):
        self.balls.append(ball)

    def throw(self):
        if len(self.balls) == 0:
            raise EmptyHand()
        return self.balls.pop(0)

def T(self):
    for ball in self.sequence:
        last_hand = ball[0]
        time_in_air = 0
        flying = False
        for i in range(1, len(ball)):
            if ball[i] != last_hand:
                flying = True
    pass

#HYpothèses :
#A tout moment, un indivu ne commence ni ne termine pas 0.

#Voisinage accessible : 
#Changer une suite complète de ii...ii par jj...jj (!=0)
#Ralonger un nombre en bord de suite vers la droite ou la gauche (iiijjj -> iiiijj ou iijjjj)
#SAUF s'ils correspondant à des contraintes de bord/de notes.

#Plus tard:
#Transformer un nombre en 0 ou un 0 en nombre pour créer des balles muettes.

#Pour l'instant une balle de chaque type, pas de balle muette
#music = [notes au temps i]
#hmax = hauteur max > 0
#nb_hands = nombre de mains

def translate_music_josue(music_josue):
    music_josue.sort(key = lambda x : x[0])
    music_leo = [set() for i in range(music_josue[-1][0]+1)]
    for note in music_josue:
        music_leo[note[0]].add(note[1])
    return music_leo

def generate_sequence(music, hmax, nb_hands):
    balls = find_balls(music)
    #On rajoute à la musique hmax premiers temps pour avoir le temps de lancer les balles.
    mask = {ball : [False]*(hmax) + [ball in notes for notes in music] for ball in balls}
    seq = {ball : [rd.randrange(1, nb_hands+1) if elem else 0 for elem in mask[ball]] for ball in balls}
    seq_len = hmax + len(music)
    return seq, mask, seq_len

def find_balls(music):
    return set(note for notes in music for note in notes)

def choose_neighbour(seq, mask, balls, hmax, nb_hands):
    p = rd.random()
    ball = rd.choice(balls)
    #On ne s'autaurise pas à prendre de "0" pour l'instant.
    #A changer quand on voudra rajouter des lancers silencieux.
    #pos = rd.randrange(0, len(seq[ball]))
    pos = rd.choice([i for i in range(len(seq[ball])) if seq[ball][i] != 0 or mask[ball][i]])
    pos_start = pos      #Inclus
    pos_end = pos + 1    #Non inclus
    #On identifie la suite de chiffres identiques à laquelle pos appartient
    while pos_start >= 0 and seq[ball][pos] == seq[ball][pos_start]:
        pos_start -= 1
    while pos_end <= len(seq[ball]) and seq[ball][pos] == seq[ball][pos_end - 1]:
        pos_end += 1

    if p < 0.1:
        #On change toute la suite de nombres en une autre.
        new_hand = rd.choice([i for i in range(1, nb_hands + 1) if i != seq[ball][pos]])
        for i in range(pos_start, pos_end):
            seq[ball][i] = new_hand
    else:
        #On étend un nombre, ou on le diminue.
        p2 = rd.random()
        if p2 < 0.5 and pos_end <= len(seq[ball]):
                seq[pos_end] = seq[pos]
        else:
                seq[pos_end - 1] = 0

#nb_hands prend en compte
#position des balles dans les mains à faire ?

def evaluate_sequence(seq, seq_len, hmax, nb_hands, K=4):
    #Condition 1 : Pas plus de K balles en main au même moment
    hand_weight_issues = []
    for t in range(seq_len):
        hand_weight = [0]*(nb_hands+1)
        for ball_seq in seq:
            hand_weight[ball_seq[t]] += 1
        for hand, weight in enumerate(hand_weight):
            if weight > K:
                hand_weight_issues.append((t, hand, weight))
    
    #Condition 2 : Respecte la musique.
    #ie les chiffres du masque ne sont pas nuls, et le chiffre le précédent sont différents.
    notes_not_made = []
    for ball, ball_mask in mask.items():
        for t, must_play in enumerate(ball_mask):
            #On ne prend pas en compte les balles silencieuses qui ne sont pas encore implémantées.
            #t-1 indice valable car si hmax > 0, t=0 donne must_play=False.
            if must_play and not(seq[ball][t] != 0 and seq[ball][t] != seq[ball][t-1]):
                note_not_made.append((t, ball))

    #Condition 3 : Pas de balle en l'air au début ou à la fin.
    ball_flying_on_sides = []
    for ball, ball_seq in seq.items():
        if ball_seq[0] == 0:
            ball_flying_on_sides.append((ball, "SRT"))
        if ball_seq[-1] == 0:
            ball_flying_on_sides.append((ball, "END"))

    #Condition 4 : Ne pas dépasser des lancers de hauteur plus de hmax
    #On considère les lancers de 1 toujours valides donc on ne s'y intéresse pas.
    #On peut donc repérer les lancers par des 0 dans la séquences.
    throws_too_high = []
    for ball, ball_seq in seq.items():
        flying = False
        launch_time = 0
        for t, hand in enumerate(ball_seq):
            if hand == 0 and not flying:
                flying = True
                launch_time = t
            elif hand != 0 and flying:
                flying = False
                height = t - launch_time
                if height > hmax:
                    throws_too_high.append((t, ball, launch_time, height))
                    
    #Calcul du score :
    score = - len(hand_weight_issues) - len(notes_not_made) - len(throws_too_high) - len(ball_flying_on_sides)



def recuit_simule(music, hmax, nb_hands, max_iter):
    seq, mask, seq_len = generate_sequence(music, hmax, nb_hands)
    print(seq, mask, seq_len)
    balls = list(find_balls(music))
    print(balls)
    score = evaluate_sequence(seq, mask, balls, seq_len, hmax, nb_hands)
    best_sequence = deepcopy(seq)
    best_score = score
    try:
        for i in range(max_iter):
            seq = choose_neighbour(seq, mask, balls)
            score = evaluate_sequence(seq)
            if score > best_score:
                best_seq = deepcopy(seq)
                best_score = score
        return best_sequence, best_score
    except KeyboardInterrupt:
        return best_sequence, best_score


au_clair_de_la_lune_josue = [( 1, "do"), ( 2, "do"), ( 3, "do"), 
         ( 4, "re"), ( 5, "mi"), ( 7, "re"), 
         ( 9, "do"), (10, "mi"), (11, "re"),
         (12, "re"), (13, "do")]

music = translate_music_josue(au_clair_de_la_lune_josue)
print(music)
recuit_simule(music, 7, 2, 100)

"""Throw = namedtuple('Throw', ['ball', 'target', 'height'])
Swap = namedtuple('Swap', ['hand'])

data = []

class EventType(Enum):
    THROW

class JugglingSample():
    def __init__(self):
        self.max_time
        self.events"""


