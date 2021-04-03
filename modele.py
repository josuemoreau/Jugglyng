"""
Musical juggling model and view

Principle of this implementation:

The time-step model takes as input an initial state and sequence of
throws (currently periodic with single throw at each step), and
generates the sequence of states.

The view then interpolates between the states, adding the geometric
information

"""

import copy
import simpleaudio
import collections
import time
from recordclass import recordclass, RecordClass
from pythreejs import Mesh, SphereBufferGeometry, SphereGeometry, OrbitControls, MeshLambertMaterial, MeshStandardMaterial, PerspectiveCamera, Scene, Renderer, AmbientLight
from numpy import pi, cos, sin
from typing import Optional

# utilisation de RecordClass ainsi au lieu de recordclass
# pour pouvoir utiliser le type Ball dans le typage avec mypy
class Ball(RecordClass):
    color : str = 'white'
    tone : Optional[str] = None
    source_hand : Optional[int] = None
    target_hand : Optional[int] = None
    time_flying : int = 0
    time_to_land : int = 0
    number : Optional[int] = None
    last_time_played : float = True

State=collections.namedtuple('State',
                             ['hands', 'balls'])
Throw=collections.namedtuple('Throw',
                             ['source_hand', 'target_hand', 'duration'])

class Model:

    balls : tuple[Ball, ...]
    states : list[State]
    number_of_hands : int
    time_in_hand : float
    pattern : list[int]


    """
    # Hypotheses
    # - the number of hands does not change
    # - the number of balls does not change

    # Data structure
    # - balls: a tuple of Balls'
    # - hands: a tuple of list of ball numbers:
    #   for each hand, the numbers of the balls it holds
    """
    def __init__(self, *hand_content : list[dict], pattern : list[int] =[3]):
        balls : list[Ball] = []
        hands = []
        i : int
        content : list[dict]
        for i,content in enumerate(hand_content):
            hand : list[Optional[int]] = []
            for color in content:
                if isinstance(color, dict):
                    tone = simpleaudio.WaveObject.from_wave_file(color["tone"]+".wav")
                    color = color["color"]
                else:
                    tone = None
                ball : Ball = Ball(color=color,
                                   tone=tone,
                                   target_hand=i,
                                   time_to_land=0,
                                   number=len(balls),
                                   last_time_played=0.)
                balls.append(ball)
                hand.append(ball.number)
            hands.append(hand)
        ballst : tuple[Ball, ...] = tuple(balls)
        handst = tuple(hands)
        self.balls = ballst
        self.states = [State(balls=ballst, hands=handst)]
        self.number_of_hands = len(handst)
        self.time_in_hand = 0.9
        self.pattern=pattern

    def throw(self, t : int):
        duration = self.pattern[t % len(self.pattern)]
        return Throw(source_hand = t % self.number_of_hands,
                     target_hand = (t + duration) % self.number_of_hands,
                     duration = duration)

    def transition(self, state : recordclass, throw : Throw):
        hands = copy.deepcopy(state.hands)
        balls = copy.deepcopy(state.balls)
        thrown_balls : list[recordclass] = []
        for b in balls:
            if b.time_to_land > 1:   # flying ball
                b.time_to_land -= 1;
                b.time_flying += 1;
            elif b.time_to_land > 0: # landing ball
                b.time_to_land = 0;
                b.time_flying = None
                b.source_hand = None
                hands[b.target_hand].append(b.number)
        if throw.duration > 0:
            if hands[throw.source_hand]:
                # TODO: handle multiplex throws
                ball = balls[hands[throw.source_hand].pop()]
                ball.source_hand = throw.source_hand
                ball.target_hand = throw.target_hand
                ball.time_flying = 0
                ball.time_to_land = throw.duration - self.time_in_hand
            else:
                print("main vide!")
        return State(balls=balls, hands=hands)

    def state(self, t : int):
        for t1 in range(len(self.states)-1, t):
            self.states.append(self.transition(self.states[-1], self.throw(t1)))
        return self.states[t]

class BallView:
    def __init__(self, color):
        self.mesh = Mesh(
            SphereBufferGeometry(5, 32, 16),
            MeshStandardMaterial(color=color)
        )
        self.played_sound = False

class HandView:
    def __init__(self, x=0, y=0, z=-30, r=10, side=1, phase=0):
        self.x=x
        self.y=y
        self.z=z
        self.r=r
        self.side = side
        self.phase = phase
        self.mesh =  Mesh(
            SphereBufferGeometry(4, 32, 16),
            MeshStandardMaterial(color="white")
        )

class View:
    height_constant = 7
    def __init__(self, model):
        self.model = model
        initial_state = self.model.state(0)
        self.balls = [BallView(ball.color)
                      for ball in initial_state.balls]
        # TODO: currently hardcoded for two hands
        self.hands = [HandView(x=-25, side=-1),
                      HandView(x= 25, side=1, phase=1)]

        width=500
        height=500
        camera = PerspectiveCamera(position=[0, 0, -100], up = [0,1,0], aspect=width/height)
        objects = [object.mesh for object in self.hands + self.balls]
        scene  = Scene(children= objects + [camera, AmbientLight()])
        self.widget = Renderer(scene=scene,
                               camera=camera,
                               alpha=True,
                               clearOpacity=0,
                               controls=[OrbitControls(controlling=camera)],
                               width=width,
                               height=height,
        )
        self.update(0)

    def hand_position(self, hand, t):
        alpha = pi * (t + hand.phase)
        return hand.x+hand.side*hand.r*cos(alpha), hand.z-hand.r*sin(alpha), hand.y

    def update(self, t):
        step = int(t)
        state = self.model.state(step)
        for hand, view in zip(state.hands, self.hands):
            x, z, y = self.hand_position(view, t)
            view.mesh.position = x, z-4, y
            #x,z,y = position
            #for i in hand:
            #    self.balls[i].mesh.position = x,z,y
            #    y = y + 10
        for ball in state.balls:
            if ball.tone is not None and ball.time_to_land > 0 and ball.time_to_land < .5:
                if not self.balls[ball.number].played_sound:
                    ball.tone.play()
                    self.balls[ball.number].played_sound = True
            else:
                self.balls[ball.number].played_sound = False
            if ball.time_to_land > t - step:
                x0,z0,y0 = self.hand_position(self.hands[ball.source_hand], step - ball.time_flying)
                x1,z1,y1 = self.hand_position(self.hands[ball.target_hand], step + ball.time_to_land)
                a = (ball.time_flying+t-step)/(ball.time_flying + ball.time_to_land)
                h = self.height_constant*(ball.time_flying + ball.time_to_land)**2
                x = x0 * (1-a) + x1 * a
                y = y0 * (1-a) + y1 * a
                z = z0 * (1-a) + z1 * a + h * 4*a*(1-a)
            else:
                x, z, y = self.hand_position(self.hands[ball.target_hand], t)

            self.balls[ball.number].mesh.position = x, z, y

