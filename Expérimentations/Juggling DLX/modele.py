"""
Musical juggling model and view

Principle of this implementation:

The time-step model takes as input an initial state and sequence of
throws (currently periodic with single throw at each step), and
generates the sequence of states.

The view then interpolates between the states, adding the geometric
information and managing sound.
"""

import copy
import os
import collections
from audio import Audio
from recordclass import RecordClass
from pythreejs import Mesh, SphereBufferGeometry, SphereGeometry, OrbitControls, MeshLambertMaterial, MeshStandardMaterial, PerspectiveCamera, Scene, Renderer, AmbientLight
from numpy import pi, cos, sin
from typing import Optional, List, Dict, Tuple, Union, Any


# utilisation de RecordClass ainsi au lieu de recordclass
# pour pouvoir utiliser le type Ball dans le typage avec mypy
class Ball(RecordClass):
    name : str = ''
    color : str = 'white'
    tone : Any = None
    source_hand : Optional[int] = None
    target_hand : Optional[int] = None
    time_flying : int = 0
    time_to_land : int = 0
    number : int = 0
    just_landed : bool = False
    is_flying : bool = False

State=collections.namedtuple('State',
                             ['hands', 'balls'])
Throw=collections.namedtuple('Throw',
                             ['ball_name', 'source_hand', 'target_hand', 'duration'])

class Model:

    #balls : Tuple[Ball, ...]
    states : List[State]
    nb_hands : int
    time_in_hand : float
    pattern : List[int]


    """
    # Hypotheses
    # - the number of hands does not change
    # - the number of balls does not change

    # Data structure
    # - balls: a tuple of Balls'
    # - hands: a tuple of list of ball numbers:
    #   for each hand, the numbers of the balls it holds
    """

    #1 balle de chaque pour l'instant
    #pattern = [MAIN1[(BALLE, VERSMAIN), ...],
    #           MAIN2[...], ...             ],
    #           ...                         ]]
    def __init__(self, ball_properties, pattern : List[int] = [3]):
        """balls : List[Ball] = []
        hands : List[List[Optional[int]]] = []"""

        balls = dict()
        nb_hands = len(pattern)
        nb_steps = len(pattern[0]) #Pattern vide ?
        hands = [[] for i in range(nb_hands)]
        #Remplacer balls par dict pour avoir acces à une balle par son nom ?
        #ball_properties = List(Tuple(name, sound, color))
        #Guess where each ball should be
        #SOURCE HAND ? TARGET HAND ?
        #Pour l'instant, on ne peut pas mettre de balle inutilisée dans une main,
        #et on doit spécifier toutes les mains utilisées dans le pattern.

        for number, ball_prop in enumerate(ball_properties):
            if "tone" in ball_prop:
                tone = "sounds/{}.wav".format(ball_prop["tone"])
            else:
                tone = None
            if "color" in ball_prop:
                color = ball_prop["color"]
            else:
                color = None
            name = ball_prop["name"]
            ball : Ball = Ball(name   = name,
                               color  = color,
                               tone   = tone,
                               number = number)
            balls[name] = ball
        
        """#Copie et modifie le pattern pour le rendre compatible avec les numéros de balle
        pattern2 = []
        for hand_pattern in pattern:
            hand2 = []
            for throws in hand_pattern:
                step2 = []
                for ball_name, target, duration in throws:
                    step2.append((balls_dict[ball_name], target, duration))
                hand2.append(step2)
            pattern2.append(hand2)
        
        pattern = pattern2"""

        #Parcours tout le pattern pour savoir où sont initialement les balles
        placed = {name : False for name in balls}
        for step in range(nb_steps):
            if all(placed.values()):
                break
            balls_added_this_step = set()
            for hand in range(nb_hands):
                for ball_name, target, duration in pattern[hand][step]:
                    if not placed[ball_name]:
                        placed[ball_name] = True
                        balls_added_this_step.add(ball_name)
                        ball = balls[ball_name]
                        ball.source_hand = hand
                        hands[hand].append(ball.name)
                    elif ball_name in balls_added_this_step:
                        raise Exception("La balle {} est présente initialement dans 2 mains.".format(ball_name))
        
        #Si une balle n'est pas déclarée dans le pattern, elle est par défaut placée dans la main 0.
        for ball_name, elem in placed.items():
            if not elem:
                ball = balls[ball_name]
                ball.source_hand = 0
                hands[0].append(ball.name)

        handst : Tuple[List[Optional[int]], ...] = tuple(hands)
        self.balls = balls
        self.states = [State(balls=balls, hands=handst)]
        self.nb_hands = len(handst)
        self.pattern = pattern
        self.pattern_len = len(pattern[0])

    def get_throws(self, step : int):
        if step >= self.pattern_len:
            return []
        throws = []
        for hand in range(self.nb_hands):
            for ball_name, target, duration in self.pattern[hand][step]:
                throw = Throw(ball_name = ball_name,
                              source_hand = hand,
                              target_hand = target,
                              duration = duration)
                throws.append(throw)
        return throws

    def transition(self, state : State, throws : List[Throw], step : int):
        hands = copy.deepcopy(state.hands)
        balls = copy.deepcopy(state.balls)
        #balls = tuple([copy_ball(x) for x in state.balls])
        for b in balls.values():
            b.just_landed = False
            if b.time_to_land > 1:   # flying ball
                b.time_to_land -= 1
                b.time_flying += 1
            elif b.time_to_land == 1: # landing ball
                b.time_to_land = 0
                b.just_landed = True
                b.is_flying = False
                b.time_flying = 0
                b.source_hand = b.target_hand
                b.target_hand = None
                hands[b.source_hand].append(b.name)
        for throw in throws:
            if throw.ball_name in hands[throw.source_hand]:
                ball = balls[throw.ball_name]
                hand = hands[throw.source_hand]
                hand.remove(ball.name)
                if throw.duration == 0: #téléportation !
                    ball.just_landed = True
                    ball.source_hand = throw.target_hand
                    hands[ball.source_hand].append(ball.name)
                else:
                    ball.source_hand = throw.source_hand
                    ball.target_hand = throw.target_hand
                    ball.time_flying = 0
                    ball.time_to_land = throw.duration
                    ball.is_flying = True
            else:
                raise Exception("Balle {} n'est pas dans la main {} à l'étape {}".format(throw.ball_name, throw.source_hand, step))
        return State(balls=balls, hands=hands)

    def state(self, t : int):
        for t1 in range(len(self.states)-1, t):
            self.states.append(self.transition(self.states[-1], self.get_throws(t1), t1))
        return self.states[t]

class BallView:
    def __init__(self, ball : Ball):
        self.mesh = Mesh(
            SphereBufferGeometry(5, 32, 16),
            MeshStandardMaterial(color=ball.color)
        )
        #self.tone = mixer.Sound(ball.tone)
        self.tone = Audio(ball.tone) if ball.tone else None

class HandView:
    def __init__(self, id: int, throw_times: List[int],
                       x : int =  0, y    : int = 0, z     : int = -30,
                       r : int = 5, side : int = 1, phase : int =   0):
        self.x : int = x
        self.y : int = y
        self.z : int = z
        self.r : int = r
        self.side  : int = side #???
        self.phase : int = phase
        self.mesh =  Mesh(
            SphereBufferGeometry(4, 32, 16),
            MeshStandardMaterial(color="white")
        )
        self.id: int = id
        self.throw_times: List[int] = throw_times
        # Variables d'animation
        self.animation: bool = False
        self.animation_time: float = 0.0
        self.last_time: float = 0.0

    def land_position(self):
        alpha = pi - pi * (0.90 + self.phase)
        return self.x + self.side * self.r * cos(alpha), self.z + self.r * sin(alpha), self.y

    def throw_position(self):
        alpha = pi * (0.80 + self.phase)
        return self.x + self.side * self.r * cos(alpha), self.z + self.r * sin(alpha), self.y

class View:
    height_constant = 4

    def __init__(self, model : Model, sides: List[int]):

        self.model : Model = model

        """mixer.init()
        mixer.set_num_channels(len(model.balls))"""

        self.time_in_hand = 0.5
        initial_state = self.model.state(0)
        self.balls : List[BallView] = {name : BallView(ball)
                                       for name, ball in initial_state.balls.items()}

        # Création des vues des mains
        self.hands : List[HandView] = []
        for hand in range(self.model.nb_hands):
            throws = self.model.pattern[hand]
            throw_times = [t + 1 for t in range(len(throws)) if len(throws[t]) > 0]
            hview = HandView(x=25*hand, id=hand,
                             throw_times=throw_times, side=sides[hand])
            self.hands.append(hview)

        width=500
        height=500
        hands_midpoint = 25*(self.model.nb_hands)
        camera = PerspectiveCamera(position=[0, 0, -100], up = [0,1,0], aspect=width/height)

        objects = [object.mesh for object in self.hands] + [object.mesh for object in self.balls.values()]
        scene   = Scene(children= objects + [camera, AmbientLight()])
        self.widget = Renderer(scene=scene,
                               camera=camera,
                               alpha=True,
                               clearOpacity=0,
                               controls=[OrbitControls(controlling=camera)],
                               width=width,
                               height=height,
        )
        self.update(0, 0)

    def hand_position(self, hand : HandView, t : float, balls: List[Ball]):
        alpha = 0  # Sans lancer, les mains ne bougent pas
        # Suite d'une animation déjà lancée
        if hand.animation:
            dt = t - hand.last_time
            hand.animation_time += 2 * dt
            hand.last_time = t
            if hand.animation_time >= 2.0:
                hand.animation = False
                hand.last_time = 0
            else:
                alpha = pi * (hand.animation_time + hand.phase)
        if alpha == 0 and int(t) + 1 in hand.throw_times \
           and t - int(t) >= 0.9 and not hand.animation:
            hand.animation = True
            hand.animation_time = 0
            hand.last_time = t
            alpha = pi * (hand.animation_time + hand.phase)
        return hand.x+hand.side*hand.r*cos(alpha), hand.z-hand.r*sin(alpha), hand.y

    def update(self, t : float, old_t : float):
        """t : float = change["new"]
        old_t : float = change["old"]"""
        step  = int(t)
        state = self.model.state(step)
        balls = list(state.balls.values())

        for hand, view in zip(state.hands, self.hands):
            x, z, y = self.hand_position(view, t, balls)
            view.mesh.position = x, z-4, y

        for ball in balls:

            #On cherche la balle correspondante dans View pour lui faire jouer un son si besoin
            view_ball = self.balls[ball.name]

            if view_ball.tone is not None:
                #if ball.just_landed and (old_t < step <= t or old_t > step >= t):
                if ball.just_landed and old_t < step <= t:
                    view_ball.tone.play()

            #On actualise la position de la balle
            #A MIEUX REDIGER A L'AVENIR ! -> DEPLACER CES PROPRIETES VERS LE MODELE PLUTOT QUE VIEW ! + JUGGLING LADDER ?
            if ball.is_flying and ball.time_flying + (t - step) - self.time_in_hand > 0:
                throw_time = step - ball.time_flying + self.time_in_hand
                catch_time = step + ball.time_to_land
                x0, z0, y0 = self.hands[ball.source_hand].throw_position()
                x1, z1, y1 = self.hands[ball.target_hand].land_position()
                a = (t - throw_time) / (catch_time - throw_time)
                h = self.height_constant * (ball.time_flying + ball.time_to_land)**2 #throw height
                x = x0 * (1-a) + x1 * a
                y = y0 * (1-a) + y1 * a
                z = z0 * (1-a) + z1 * a + h * 4*a*(1-a)
            else:
                x, z, y = self.hand_position(self.hands[ball.source_hand], t, balls) # type: ignore

            #A little offset between balls to differentiate them (linear between +1 and -1 offset)
            x += 1 - 2*(ball.number/len(self.balls))

            self.balls[ball.name].mesh.position = x, z, y