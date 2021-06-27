import ipywidgets as widgets
from IPython.display import display
import threading
import cv2
import numpy as np
from enum import Enum
from collections import deque
import imutils
import time
import json
from copy import deepcopy

from videoplayer import *

class Mode(Enum):
    HSV_FINDER = 0
    BALL_TRACKER = 1
    QUIT = 2

#Rajouter count ?
class Ball:
    maxlen = 16
    def __init__(self, name, lower_hsv=(0, 0, 0), higher_hsv=(179, 255, 255), data=dict(), count=1, tracked=True):
        self.name = name #Changer en "name" ?
        self.lower_hsv = tuple(lower_hsv)
        self.higher_hsv = tuple(higher_hsv)
        self.trail = deque(maxlen = self.maxlen)
        #Les fonctions de dessin d'opencv utilisent BGR
        hsv_trail_color = ((lower_hsv[0] + higher_hsv[0]) // 2, 255, 255)
        self.trail_color = convert_single_color(hsv_trail_color, cv2.COLOR_HSV2BGR)
        #Opencv utilise BGR, Matplotlib utilise  RGB
        self.plt_color = tuple(elem/255 for elem in self.trail_color)[::-1]
        self.data = data
        self.count = count
        self.tracked = tracked
    
    def to_dict(self):
        return {"name" : self.name, "lower_hsv" : self.lower_hsv,
                "higher_hsv" : self.higher_hsv, "data" : self.data,
                "count" : self.count}

    @classmethod
    def from_dict(cls, d):
        #Json.dump convertit les entrées de dictionnaire en string !
        #Ainsi, dans certains cas, ball_data["data"] a pour clé des strings !
        d["data"] = {float(key) : value for key, value in d["data"].items()}
        return Ball(d["name"], lower_hsv=d["lower_hsv"], higher_hsv=d["higher_hsv"],
                    data=d["data"], count=d["count"])                
    
    def __repr__(self):
        return "Ball(name = '{}', lower_hsv = {}, higher_hsv = {}, count = {})".format(self.name, self.lower_hsv, self.higher_hsv, self.count)

def convert_single_color(color, convertion_function):
    #Cette couleur est bien convertie, mais les entiers qu'elle contient sont du type np.uint8
    #On souhaite donc les convertir en le type int natif de python.
    converted_color = cv2.cvtColor(np.uint8([[color]]), convertion_function)[0][0]
    return tuple(int(elem) for elem in converted_color)

class BallTracker():
    def __init__(self, source=0, data_path=None, mode=Mode.HSV_FINDER):
        #self.dropdown.options est un tuple
        #Hypothèse : les clés de self.balls sont exactement les éléments de self.dropdown.options
        layout = widgets.Layout(width='50%')
        button_layout = widgets.Layout(width = '40px')
        
        #Widgets HSV_FINDER
        h_low  = widgets.IntSlider(value=0, min=0, max=179, description='h_low:', layout=layout)
        s_low  = widgets.IntSlider(value=0, min=0, max=255, description='s_low:', layout=layout)
        v_low  = widgets.IntSlider(value=0, min=0, max=255, description='v_low:', layout=layout)
        h_high = widgets.IntSlider(value=179, min=0, max=179, description='h_high:', layout=layout)
        s_high = widgets.IntSlider(value=255, min=0, max=255, description='s_high:', layout=layout)
        v_high = widgets.IntSlider(value=255, min=0, max=255, description='v_high:', layout=layout)
        speed  = widgets.IntSlider(value=1, min=1, max=100, description='speed:', layout=layout)

        name_ball = widgets.Text(placeholder='Name ball color')
        add_ball = widgets.Button(icon='plus', layout=button_layout)
        remove_ball = widgets.Button(icon='remove', layout=button_layout)
        modify_ball = widgets.Button(icon='refresh', layout=button_layout)
        add_ball.on_click(lambda b : self.add_ball())
        remove_ball.on_click(lambda b : self.remove_ball())
        modify_ball.on_click(lambda b : self.modify_ball())
        
        ball_count = widgets.IntSlider(value=1, min=0, max=3, description='count :', layout=layout)
        tracked = widgets.Checkbox(value=True, description='Tracked')

        play = widgets.ToggleButtons(options = [('', 0), (' ', 1), ('  ', 2)], value=0,
                icons=['play', 'pause', 'stop'], button_style='info',
                style=widgets.ToggleButtonsStyle(button_width='40px'))
        
        toggle = widgets.ToggleButton(value = True, description = 'Processing shown',
    icon='eye',
    button_style='warning',
    layout=widgets.Layout(width='150px')
)
        modes = widgets.ToggleButtons(options = [('Color Picker  ', 0), ('Ball Tracker  ', 1)], value=0,
              icons=['paint-brush', 'bullseye'],
              button_style='warning',
              style=widgets.ToggleButtonsStyle(button_width='150px'))

        lines = widgets.ToggleButton(
    description = 'Thresholds hidden',
    icon='arrows',
    button_style='warning',
    layout=widgets.Layout(width='150px')
)
        def play_observe(change):
            value = change['new']
            if value == 0 or value == 1:
                self.vp.pause()
            else: #value == 2
                self.stop()
        
        def toggle_observe(change):
            self.only_video = not(self.only_video)
            widget = self.widgets['toggle']
            if not change["new"]:
                widget.icon = 'eye-slash'
                widget.description = 'Processing hidden'
            else:
                widget.icon = 'eye'
                widget.description = 'Processing shown'
        
        def modes_observe(change):
            if not self.save_tracking: #A fixer un jour
                if self.mode == Mode.HSV_FINDER:
                    self.mode = Mode.BALL_TRACKER
                elif self.mode == Mode.BALL_TRACKER:
                    self.mode = Mode.HSV_FINDER

        def lines_observe(change):
            self.draw_lines = not(self.draw_lines)
            widget = self.widgets['lines']
            if change["new"]:
                lines.description = 'Thresholds shown'
            else:
                lines.description = 'Thresholds hidden'

        play.observe(lambda change : play_observe(change), names='value')
        toggle.observe(lambda change : toggle_observe(change), names='value')
        modes.observe(lambda change : modes_observe(change), names='value')
        lines.observe(lambda change : lines_observe(change), names='value')
        
        dropdown = widgets.Dropdown(description='Balls :', options=[])
        dropdown.observe(lambda change : self.dropdown_observe(change), names="value")
        
        """upload_balls = widgets.Button(icon='upload', layout=button_layout)
        download_balls = widgets.Button(icon= 'download', layout=button_layout)
        
        upload_balls.on_click(lambda b : self.upload_balls())
        download_balls.on_click(lambda b : self.download_balls())"""

        #Widgets BALL_TRACKER
        #...
        
        #Widgets GENERAUX
        #...
        
        self.widgets = {"h_low" : h_low, "s_low" : s_low, "v_low" : v_low,
                       "h_high" : h_high, "s_high" : s_high, "v_high" : v_high,
                       "speed" : speed, "name_ball" : name_ball, "add_ball" : add_ball,
                       "remove_ball" : remove_ball, "modify_ball" : modify_ball,
                       "ball_count" : ball_count,
                       "tracked" : tracked,
                       "dropdown" : dropdown,
                       "play" : play, "toggle" : toggle, "modes" : modes, "lines" : lines}
        self.dropdown = dropdown #A SUPPRIMER ? 
        self.balls = dict()
        
        self.only_video = False
        self.vp = None
        #self.vp = VideoPlayer(source=source)
        self.source = source
        self.mode = mode #Check mode ? isinstance(mode, Mode)
        self.window_name = 'frame'
        self.thread = None
        self.switch_id = 0
        self.switch_list = []
        self.save_tracking = False
        self.base_time = 0
        self.halt = False
        self.halt_foo = None
        self.halt_args = dict()

        #Attributs pour utiliser les thresholds de détection
        self.draw_lines = False
        self.moving_line_x = False
        self.moving_line_y = False
        self.line_x = 0
        self.line_y = 0
        self.line_color = (0, 255, 255)
        self.line_thickness = 5
        self.line_eps = 2*self.line_thickness
        
        if data_path is not None:
            self.load_config(data_path)

    def mouse_event_thresholds(self, event, x, y, flags, param):
        if not self.draw_lines:
            return

        if event == cv2.EVENT_LBUTTONDOWN:
            if abs(self.line_x - x) < self.line_eps:
                self.moving_line_x = True
            if abs(self.line_y - y) < self.line_eps:
                self.moving_line_y = True
            
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.moving_line_x:
                self.line_x = x
                self.line_x = max(0, self.line_x)
                self.line_x = min(self.vp.width, self.line_x)
            if self.moving_line_y:
                self.line_y = y
                self.line_y = max(0, self.line_y)
                self.line_y = min(self.vp.height, self.line_y)
        
        elif event == cv2.EVENT_LBUTTONUP:
            self.moving_line_x = False
            self.moving_line_y = False

    def get_ball_properties_from_widget(self):
        name = self.widgets["name_ball"].value
        lower_hsv  = (self.widgets["h_low"].value, self.widgets["s_low"].value,
                      self.widgets["v_low"].value)
        higher_hsv = (self.widgets["h_high"].value, self.widgets["s_high"].value,
                      self.widgets["v_high"].value)
        count = self.widgets["ball_count"].value
        tracked = self.widgets["tracked"].value
        return name, lower_hsv, higher_hsv, count, tracked
    
    def add_ball(self):
        name, lower_hsv, higher_hsv, count, tracked = self.get_ball_properties_from_widget()
        if name in self.dropdown.options :
            print("{} existe déjà.".format(name))
            return
        self.balls[name] = Ball(name, lower_hsv=lower_hsv, higher_hsv=higher_hsv, count=count, tracked=tracked)
        self.dropdown.options = list(self.dropdown.options) + [name]
        self.dropdown.value = name
        print(self.balls)
    
    def remove_ball(self):
        #Principe : on supprime ou modifie le nom actuellement sélectionné.
        name, *_ = self.get_ball_properties_from_widget()
        if len(self.dropdown.options) == 0:
            return
        to_remove = self.dropdown.value
        self.balls.pop(name)
        self.dropdown.options = [elem for elem in self.dropdown.options if elem != to_remove]
        print(self.balls)
        
    def modify_ball(self):
        new_name, lower_hsv, higher_hsv, count, tracked = self.get_ball_properties_from_widget()
        old_name = self.dropdown.value
        if old_name != new_name and new_name in self.dropdown.options:
            print("{} existe déjà.".format(new_name))
            return
        ball = self.balls.pop(old_name)
        self.balls[new_name] = Ball(new_name, lower_hsv=lower_hsv, higher_hsv=higher_hsv, count=count, tracked=tracked)
        self.dropdown.options = [elem if elem != old_name else new_name for elem in self.dropdown.options]
        self.dropdown.value = new_name
        print(self.balls)
    
    def dropdown_observe(self, change):
        #ATTENTION, IL FAUT D'ABORD CHANGER LES VALEURS, PUIS A LA FIN CHANGER LE SLIDER !
        #SINON PB LORS DE L'UPDATE
        name = change['new']
        ball = self.balls[name]
        #A refaire plus proprement
        self.widgets["h_low"].value, self.widgets["s_low"].value, self.widgets["v_low"].value = ball.lower_hsv
        self.widgets["h_high"].value, self.widgets["s_high"].value, self.widgets["v_high"].value = ball.higher_hsv
        self.widgets["name_ball"].value = name
        self.widgets["ball_count"].value = ball.count
        self.widgets["tracked"].value = ball.tracked
    

    def save_config(self, path):
        data = {'balls' : [self.balls[name].to_dict() for name in self.dropdown.options],
                'thresholds' : [self.line_x, self.line_y]}
        with open(path, 'w') as f:
            json.dump(data, f)
        
    def load_config(self, path):
        with open(path, 'r') as f:
            data = json.load(f)

        self.line_x, self.line_y = data['thresholds']

        options = []
        self.balls = dict()
        for ball_data in data['balls']:
            ball = Ball.from_dict(ball_data)
            self.balls[ball.name] = ball
            options.append(ball.name)
        self.dropdown.options = options
    
    def display(self):
        #Faire avec Out à l'avenir
        """display(
            widgets.VBox([
                self.widgets["h_low"],
                self.widgets["s_low"],
                self.widgets["v_low"],
                self.widgets["h_high"],
                self.widgets["s_high"],
                self.widgets["v_high"],
                self.widgets["speed"], 
                widgets.HBox([
                    widgets.Label("Balle :"),
                    self.widgets["name_ball"],
                    self.widgets["add_ball"],
                    self.widgets["remove_ball"],
                    self.widgets["modify_ball"]
                ]),
                self.widgets["ball_count"],
                self.widgets["tracked"],
                self.widgets["dropdown"]
            ])
        )"""
        display(
            widgets.VBox([
                widgets.HBox([
                    self.widgets["play"],
                    self.widgets["speed"],
                    widgets.Label("faster <---> slower")
                ]),
                widgets.HBox([
                    widgets.Label("Choose mode :"),
                    self.widgets["modes"]
                ]),
                widgets.HBox([
                    self.widgets["toggle"],
                    self.widgets["lines"]
                ]),
                self.widgets["dropdown"],
                widgets.HBox([
                    widgets.Label("Balle :"),
                    self.widgets["name_ball"],
                    self.widgets["add_ball"],
                    self.widgets["remove_ball"],
                    self.widgets["modify_ball"]
                ]),
                self.widgets["tracked"],
                self.widgets["h_low"],
                self.widgets["s_low"],
                self.widgets["v_low"],
                self.widgets["h_high"],
                self.widgets["s_high"],
                self.widgets["v_high"]
            ])
        )
    
    def start_data(self, path=None):
        self.halt = True
        self.halt_foo = self._start_data
        self.halt_args = {"path" : path}
    
    def stop_data(self):
        self.halt = True
        self.halt_foo = self._stop_data
        self.halt_args = dict()

    def _start_data(self, path=None): 
        if self.save_tracking:
            print("Tracking déjà en cours.")
            return

        #On reset les données des balles
        for ball in self.balls.values():
            ball.data = dict()

        #On définit toutes les variables qu'il faut.
        self.mode = Mode.BALL_TRACKER
        self.save_tracking = True
        if self.vp.paused:
            self.vp.pause()
        if self.vp.video_type == VideoType.WEBCAM:
            self.base_time = self.vp.get_time()
            if path is None:
                print("Avec une webcam, il est conseillé de spécifier le path où enregistrer la vidéo.")
            else:
                self.vp.start_recording(path)
        else:
            self.base_time = 0
            if path is not None:
                print("Avec une caméra, la vidéo n'est pas enregistrée.")
            self.vp.restart()
            self.vp.loop = False

    #Corriger ball trail quand loop ou pause ?
    #Réalisation que les CENTROIDS SONT TRAQUES, pas le centre de la balle...

    def _stop_data(self): #FONCTIONNE UNIQUEMENT AVEC WEBCAM
        if not self.save_tracking:
            print("Tracking non démarré.")
            return
        self.save_tracking = False
        self.vp.stop_recording()
        if self.vp.video_type == VideoType.VIDEO:
            self.vp.loop = True

    #Rajouter choix du mode quand on peut load data.
    def start(self, threaded=True):
        self.vp = VideoPlayer(source=self.source)
        self.display()
        #self.mode = Mode.BALL_TRACKER
        if threaded:
            self.thread = threading.Thread(target=self.run)
            #thread = threading.Thread(target = self.test)
            self.thread.start()
            print("started")
        else: #Pour aider au débuggage. Ignorer sinon.
            self.load_balls(path='test_train.json')
            self.start_data(path='test_train.avi')
            print("started")
            self.run()
    
    def stop(self):
        self.mode = Mode.QUIT
        if self.save_tracking:
            self._stop_data()

    def run(self): #Runs on thread
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self.window_name, self.mouse_event_thresholds)
        while True:
            #Cas où une fonction qu'on peut appeler dynamiquement à besoin d'être traitée avant le traitement
            if self.halt:
                self.halt_foo(**self.halt_args)
                self.halt = False

            #On récupère la frame à traiter
            ret, original_frame = self.vp.read()
            if not ret:
                self.stop()
                break

            #Choix du mode
            frame = deepcopy(original_frame) #deepcopy nécessaire ou seulement copy ?
            if self.mode == Mode.HSV_FINDER:
                frame = self.hsv_finder(frame)
            elif self.mode == Mode.BALL_TRACKER:
                frame = self.ball_tracker(frame)
            elif self.mode == Mode.QUIT: #Encore nécessaire ?
                break
            else:
                raise ValueError("{} n'est pas un mode reconnu.".format(self.mode))

            frame_to_draw = original_frame if self.only_video else frame

            if self.draw_lines:
                cv2.line(frame_to_draw, (0, self.line_y), (self.vp.width, self.line_y),
                         self.line_color, self.line_thickness)
                cv2.line(frame_to_draw, (self.line_x, 0), (self.line_x, self.vp.height),
                         self.line_color, self.line_thickness)

            cv2.imshow(self.window_name, frame_to_draw)

            speed = self.widgets["speed"].value
            k = cv2.waitKey(speed) & 0xFF
            if k == 27: #REINTEGRER SWITCH ? REtour visuel ?
                self.stop()
                break
            elif k == ord('p'):
                self.vp.pause()
            elif k == ord('t'):
                self.only_video = not(self.only_video) 
            elif k == ord('l'):
                self.draw_lines = not(self.draw_lines) 
            #elif k == ord('s'):
            #    self.switch_id = (self.switch_id + 1) % len(self.switch_list)
            elif k == ord('m') and not self.save_tracking:
                #Choses à faire à chaque fois qu'on change de mode
                #...
                #+on ne change pas de mode pendant le save_tracking
                if self.mode == Mode.HSV_FINDER:
                    self.mode = Mode.BALL_TRACKER
                elif self.mode == Mode.BALL_TRACKER:
                    self.mode = Mode.HSV_FINDER

        #Une fois sorti de la boucle, on détruit les fenêtres et met fin à vp.
        cv2.destroyWindow(self.window_name)
        self.vp.stop()
    

    def hsv_finder(self, frame): #Runs on thread

        h_low  = self.widgets["h_low"].value
        s_low  = self.widgets["s_low"].value
        v_low  = self.widgets["v_low"].value
        h_high = self.widgets["h_high"].value
        s_high = self.widgets["s_high"].value
        v_high = self.widgets["v_high"].value

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower = np.array([h_low, s_low, v_low])
        upper = np.array([h_high, s_high, v_high])
        mask = cv2.inRange(hsv, lower, upper)
        res = cv2.bitwise_and(frame, frame, mask=mask)

        return res

    #Sauvegarder avec frames plutot qu'avec temps pour eviter pb echelle avec webcam ?

    def ball_tracker(self, frame): #Runs on thread
                
        video_time = self.vp.get_time() - self.base_time

        #frame = imutils.resize(frame, width=600)
        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        # construct a mask for the given color, then perform a series of dilations
        # and erosions to remove any small blobs left in the mask
        for ball in self.balls.values():
            if not ball.tracked:
                continue
            mask1 = cv2.inRange(hsv, ball.lower_hsv, ball.higher_hsv)
            mask2 = cv2.erode(mask1, None, iterations=2)
            mask3 = cv2.dilate(mask2, None, iterations=2)
            # find contours in the mask and initialize the current (x, y) center of the ball
            cnts = cv2.findContours(mask3.copy(), cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            center = None
            # find the largest contour in the mask, then use it to compute the minimum 
            # enclosing circle and centroid
            cnts.sort(key = cv2.contourArea)
            cnts = cnts[:ball.count]
            for c in cnts:
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                M = cv2.moments(c)
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                # only proceed if the radius meets a minimum size
                if radius > 10:
                    # draw the circle and centroid on the frame, then update the list of tracked points
                    if not self.only_video :
                        cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)

            # update the points queue.
            # DEGEULASSE : on n'affiche le trail que si on ne traque qu'une balle de la couleur donnée
            if ball.count == 1 and not self.vp.paused:
                ball.trail.appendleft(center)
        
            if self.save_tracking and not self.vp.paused: #A FAIRE
                if center is None:
                    ball.data[video_time] = (float('nan'), float('nan'))
                else:
                    ball.data[video_time] = center
            
            # loop over the set of tracked points
            for i in range(1, len(ball.trail)):
                # if either of the tracked points are None, ignore them
                if ball.trail[i - 1] is None or ball.trail[i] is None:
                    continue
                # otherwise, compute the thickness of the line and draw the connecting lines
                thickness = int(np.sqrt(Ball.maxlen / float(i + 1)) * 2.5)
                if not self.only_video:
                    cv2.line(frame, ball.trail[i - 1], ball.trail[i], ball.trail_color, thickness)

        #t = [frame, blurred, hsv]
        return frame