import cv2
import numpy as np
from enum import Enum

class VideoType(Enum):
    VIDEO = 0
    WEBCAM = 1

class VideoPlayer:
    def __init__(self, source, debug=True):
        self.cap = cv2.VideoCapture(source)
        self.paused = False
        self.frame = None
        self.loop = True
        if isinstance(source, int):
            self.video_type = VideoType.WEBCAM 
        elif isinstance(source, str):
            self.video_type = VideoType.VIDEO
        else:
            raise Exception("source format is not recognized.")
        self.recording = False
        self.recording_paused = False
        self.record_out = None
        self.debug = debug
    
    def read(self):
        """if not self.cap.isopened():
            return False, None"""
        
        if self.paused:
            if self.recording and not self.recording_paused:
                self.record_out.write(self.frame)
            return True, self.frame

        ret, self.frame = self.cap.read()
        if self.loop and not ret:
            self.restart()
            ret, self.frame = self.cap.read()
        if not ret:
            self.stop_recording()
        if self.recording and not self.recording_paused:
            self.record_out.write(self.frame)
        return ret, self.frame
        
    def pause(self):
        if self.frame is None:
            self.read()
        self.paused = not(self.paused)
        
    def release(self): #Alias de stop
        self.stop()

    def stop(self):
        self.stop_recording()
        self.cap.release()
    
    def restart(self):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        #Si en pause, on change l'image renvoyée
        if self.paused:
            _, self.frame = self.cap.read()
    
    def get_time(self):
        return self.cap.get(cv2.CAP_PROP_POS_MSEC)
    
    def get_dim(self):
        return int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    def get_fps(self):
        return self.cap.get(cv2.CAP_PROP_FPS)

    def start_recording(self, path, fps=None):
        #ATTENTION ! EXPERIMENTAL (framerate variable si traitement)
        #Ne pas oublier de faire self.stop_record à la fin pour proprement finir l'enregistrement.
        #Le faire dans le not ret ???
        if self.recording:
            print("Un enregistrement a déjà lieu, veuillez l'arrêter avant.")
            return
        if path[-4:] != '.avi':
            raise Exception("Le fichier doit être un .avi")
        fourcc = cv2.VideoWriter_fourcc(*'XVID') #codec
        if fps is None:
            fps = self.get_fps()
        self.record_out = cv2.VideoWriter(path, fourcc, fps, self.get_dim())
        self.recording = True
        self.recording_paused = False
        if self.debug:
            print("Enregistrement commencé.")

    def pause_recording(self):
        if self.recording:
            self.recording_paused = not(self.recording_paused)
        if self.debug:
            if self.recording_paused:
                print("Enregistrement mis en pause.")
            else:
                print("Enregistrement plus en pause.")
    
    def stop_recording(self):
        if self.recording:
            self.recording = False
            self.recording_paused = False
            self.record_out.release()
            print("Enregistrement terminé.")
