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
import collections
from pygame import mixer
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

"""
def copy_ball(ball):
    b = Ball(name=ball.name,
             color=ball.color,
             tone=ball.tone,
             source_hand=ball.source_hand,
             target_hand=ball.target_hand,
             time_flying=ball.time_flying,
             time_to_land=ball.time_to_land,
             number=ball.number,
             last_time_played=ball.last_time_played)
    return b"""

State=collections.namedtuple('State',
                             ['hands', 'balls'])
Throw=collections.namedtuple('Throw',
                             ['ball_number', 'source_hand', 'target_hand', 'duration'])

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

        balls = []
        balls_dict = dict()
        nb_hands = len(pattern)
        nb_steps = len(pattern[0]) #Pattern vide ?
        hands = [[] for i in range(nb_hands)]
        #Remplacer balls par dict pour avoir acces à une balle par son nom ?
        #ball_properties = List(Tuple(name, sound, color))
        #Guess where each ball should be
        #SOURCE HAND ? TARGET HAND ?
        #Pour l'instant, on ne peut pas mettre de balle inutilisée dans une main,
        #et on doit spécifier toutes les mains utilisées dans le pattern.
        for ball_number, ball_prop in enumerate(ball_properties):
            if "tone" in ball_prop:
                tone = "../../sounds/{}.wav".format(ball_prop["tone"])
            else:
                tone = None
            if "color" in ball_prop:
                color = ball_prop["color"]
            else:
                color = None
            name = ball_prop["name"]
            number = len(balls)
            ball : Ball = Ball(name   = name,
                               color  = color,
                               tone   = tone,
                               number = len(balls))
            balls.append(ball)
            balls_dict[name] = ball_number
        
        #Copie et modifie le pattern pour le rendre compatible avec les numéros de balle
        pattern2 = []
        for hand_pattern in pattern:
            hand2 = []
            for throws in hand_pattern:
                step2 = []
                for ball_name, target, duration in throws:
                    step2.append((balls_dict[ball_name], target, duration))
                hand2.append(step2)
            pattern2.append(hand2)
        
        pattern = pattern2

        #Parcours tout le pattern pour savoir où sont initialement les balles
        placed = [False]*len(balls)
        for step in range(nb_steps):
            if all(placed):
                break
            balls_added_this_step = set()
            for hand in range(nb_hands):
                for ball_number, target, duration in pattern[hand][step]:
                    if not placed[ball_number]:
                        placed[ball_number] = True
                        balls_added_this_step.add(ball_number)
                        ball = balls[ball_number]
                        ball.source_hand = hand
                        hands[hand].append(ball.number)
                    elif ball_number in balls_added_this_step:
                        raise Exception("La balle {} est présente initialement dans 2 mains.".format(ball_name))
        
        for ball_number, elem in enumerate(placed):
            if not elem:
                ball = balls[ball_number]
                ball.source_hand = 0
                hands[0].append(ball.number)

        ballst : Tuple[Ball, ...]                = tuple(balls)
        handst : Tuple[List[Optional[int]], ...] = tuple(hands)
        self.balls = ballst
        self.states = [State(balls=balls, hands=handst)]
        self.balls_dict = balls_dict
        self.nb_hands = len(handst)
        self.pattern = pattern
        self.pattern_len = len(pattern[0])

    def get_throws(self, step : int):
        if step >= self.pattern_len:
            return []
        throws = []
        for hand in range(self.nb_hands):
            for ball_number, target, duration in self.pattern[hand][step]:
                throw = Throw(ball_number = ball_number,
                              source_hand = hand,
                              target_hand = target,
                              duration = duration)
                throws.append(throw)
        return throws

    def transition(self, state : State, throws : List[Throw]):
        hands = copy.deepcopy(state.hands)
        balls = copy.deepcopy(state.balls)
        #balls = tuple([copy_ball(x) for x in state.balls])
        for b in balls:
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
                hands[b.source_hand].append(b.number)
        for throw in throws:
            if throw.ball_number in hands[throw.source_hand]:
                ball = balls[throw.ball_number]
                hand = hands[throw.source_hand]
                hand.pop(ball.number)
                if throw.duration == 0: #téléportation !
                    ball.just_landed = True
                    ball.source_hand = throw.target_hand
                    hands[ball.source_hand].append(ball.number)
                else:
                    ball.source_hand = throw.source_hand
                    ball.target_hand = throw.target_hand
                    ball.time_flying = 0
                    ball.time_to_land = throw.duration
                    ball.is_flying = True
            else:
                print("Balle {} n'est pas dans la main {} à l'étape {}".format(balls[ball_number].name, throw.source_hand, t))
        return State(balls=balls, hands=hands)

    def state(self, t : int):
        for t1 in range(len(self.states)-1, t):
            self.states.append(self.transition(self.states[-1], self.get_throws(t1)))
        return self.states[t]

class BallView:
    def __init__(self, ball : Ball):
        self.mesh = Mesh(
            SphereBufferGeometry(5, 32, 16),
            MeshStandardMaterial(color=ball.color)
        )
        #self.tone = mixer.Sound(ball.tone)
        self.tone = Audio(ball.tone)

class HandView:
    def __init__(self, x : int =  0, y    : int = 0, z     : int = -30, 
                       r : int = 10, side : int = 1, phase : int =   0):
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

class View:
    height_constant = 7

    def __init__(self, model : Model, slider_step : float):

        self.model : Model = model

        mixer.init()
        mixer.set_num_channels(len(model.balls))

        self.time_in_hand = 0.0
        initial_state = self.model.state(0)
        self.balls : List[BallView] = [BallView(ball)
                                       for ball in initial_state.balls]
        self.hands : List[HandView] = [HandView(x=25*hand)
                                       for hand in range(self.model.nb_hands)]

        width=500
        height=500
        hands_midpoint = 25*(self.model.nb_hands)
        camera = PerspectiveCamera(position=[0, 0, -100], up = [0,1,0], aspect=width/height)

        objects = [object.mesh for object in self.hands] + [object.mesh for object in self.balls]
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

    def hand_position(self, hand : HandView, t : float):
        alpha = pi * (t + hand.phase)
        return hand.x+hand.side*hand.r*cos(alpha), hand.z-hand.r*sin(alpha), hand.y

    def update(self, t : float, old_t : float):
        """t : float = change["new"]
        old_t : float = change["old"]"""
        step  = int(t)
        state = self.model.state(step)
        
        for hand, view in zip(state.hands, self.hands):
            x, z, y = self.hand_position(view, t)
            view.mesh.position = x, z-4, y

        for ball in state.balls:

            #On cherche la balle correspondante dans View pour lui faire jouer un son si besoin
            view_ball = self.balls[ball.number]

            if view_ball.tone is not None:
                #if ball.just_landed and (old_t < step <= t or old_t > step >= t):
                if ball.just_landed and old_t < step <= t:
                    print(ball.source_hand)
                    view_ball.tone.play()

            #On actualise la position de la balle
            #A MIEUX REDIGER A L'AVENIR ! -> DEPLACER CES PROPRIETES VERS LE MODELE PLUTOT QUE VIEW ! + JUGGLING LADDER ?
            if ball.is_flying and ball.time_flying + (t - step) - self.time_in_hand > 0:
                throw_time = step - ball.time_flying + self.time_in_hand
                catch_time = step + ball.time_to_land
                x0,z0,y0 = self.hand_position(self.hands[ball.source_hand], throw_time)  # type: ignore
                x1,z1,y1 = self.hand_position(self.hands[ball.target_hand], catch_time) # type: ignore
                a = (t - throw_time) / (catch_time - throw_time)
                h = self.height_constant * (ball.time_flying + ball.time_to_land)**2 #throw height
                x = x0 * (1-a) + x1 * a
                y = y0 * (1-a) + y1 * a
                z = z0 * (1-a) + z1 * a + h * 4*a*(1-a)
            else:
                x, z, y = self.hand_position(self.hands[ball.source_hand], t) # type: ignore

            self.balls[ball.number].mesh.position = x, z, y
            

"""Pour ce qui est du son.
Dans Model, on calcule à quel moment le son de réception est censé être joué.
(Normal, vu que l'état des balles dépend de chaque instant t)
En revanche, c'est depuis View que le son est joué.
(Puisque les balles sont uniques, quelque soit l'instant, on peut donc savoir si un
son est déjà en train d'être joué, et s'il faut l'interrompre ou non)
"""