from collections import namedtuple
from enum import Enum

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
        for i in range(1, len(ball)):
            if ball[i] == curr_value:
                time_in_air += 1
            else:
                if 
                
                


"""Throw = namedtuple('Throw', ['ball', 'target', 'height'])
Swap = namedtuple('Swap', ['hand'])

data = []

class EventType(Enum):
    THROW

class JugglingSample():
    def __init__(self):
        self.max_time
        self.events"""


