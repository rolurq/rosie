# -*- coding: utf-8 -*-
"""
Created on Mon Apr 13 21:32:24 2015

@author: Toni
"""

__all__=['Master', '__version__']

###### INFORMATION ######

__version__ = '1.12'

#### IMPORT ####

#---- rOSi import ----
from robot import controller as Controller
from robot import planner

#### GLOBAL VARIABLES ####

PATH_METHOD="Lineal Smooth"
            # "Cubic"
            # None

#### CLASS ####

class Master:
    def __init__(self):
        self.controller = Controller.Controller()
    
    #==== PRIVATE FUNCTIONS ====

    def _track_switcher(self, track):
        """
        Path controller switcher.
        
        :param track: trace to follow
        :type track: dict
        """
        #---- Cubic ----
        if PATH_METHOD == "Cubic":
            track['z_planning'] = track['t_planning']   
            track['constant_t'] = 10
            track['constant_k'] = 5
            track['cubic'] = True
        #---- Lineal Smooth ----        
        elif PATH_METHOD == "Lineal Smooth":
            if self.controller.finished:
                self.controller.move(track)
            return
        #---- None ----
        if self.controller.finished:
            self.controller.move(track, False)
    
    #==== PUBLIC FUNCTIONS ====
    
    def position(self,x=None,y=None,theta=None):
        """
        Get or set the position of the robot
        
        :param x: X value of (X,Y)
        :type x: float
        :param y: Y value of (X,Y)
        :type y: float
        :param theta: orientation
        :type theta: float      
        :return: current position (when ``x``, ``y`` and ``theta`` are None)
        :type: tuple
        
        >>> master=Master()
        >>> master.position(2,3,0.5)
        >>> master.position()
        (2, 3, 0.5)
        """
        #---- get position ----
        if x==None and y==None and theta==None:
            return (-self.controller.y_position,
                    self.controller.x_position,
                    self.controller.z_position)
        #---- set position ----
        self.controller.y_position=-x
        self.controller.x_position=y
        self.controller.z_position=theta
    
    def is_ended(self):
        """
        Get task status of the robot.
        
        :return: current task status
        :type: bool
        
        >>> master=Master()
        >>> master.is_ended()
        True
        """
        return self.controller.finished
        
    def end_current_task(self):
        """
        End current task of the robot.
        
        >>> master=Master()
        >>> master.end_current_task()
        """
        self.controller.end_move()

    def sync_request(self, request):
        """
        Process the request of the synchronous handler.

        :param request: synchronous request
        :type request: dict
        
        >>> cmd={'place': [(0,0),(1,1)]}
        >>> master=Master()
        >>> master.sync_request(cmd)
        """
        if request:        
            #---- set action ----
            try:
                self.controller.action=request['action']
            except KeyError:
                self.controller.action='stop'
            #---- process path (place) ----
            path=planner.path_xyt(self.position(),request)
            if path:
                self._track_switcher(path)
            #---- execute action ----
            else:
                self.controller.action_exec()
            
    def async_request(self, request):
        """
        Process the request of the asynchronous handler.

        :param request: asynchronous request
        :type request: tuple       
        
        >>> cmd=(2.0,5.0)
        >>> master=Master()
        >>> master.async_request(cmd)
        """
        #XXX check for generic request
        right, left = self.controller.async_speed(request[0], request[1])
        if right or left:
            encoder1, encoder2, _ = self.controller.get_state()
            self.controller.navigation(encoder1, encoder2)
            self.controller.set_speed(right, left)
    