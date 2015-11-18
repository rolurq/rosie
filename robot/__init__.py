#### IMPORT ####

#---- rOSi import ----
from robot import controller as Controller
from robot.planner import planner

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

    def is_finished(self):
        self.get_robot_pos()
        return self.controller.finished
        
    def end_task(self):
        self.controller.end_move()

    def process_request(self, request):
        
        #---- set robot-action ----        
        #self.controller.action=request[1]
        self.controller.action='stop'
        
        #---- go to (place) ----
        path={}
        if request[0]:
            path=planner.path_xyt(self.position(),request[0])
        if path:
            self._track_switcher(path)
        else:
            self.controller.action_exec()
            
    def process_user_request(self, request):
        
        right, left = self.controller.async_speed(request[0], request[1])
        if right or left:
            encoder1, encoder2, _ = self.controller.get_state()
            self.controller.navigation(encoder1, encoder2)
            self.controller.set_speed(right, left)
    
    
    
