# -*- coding: utf-8 -*-
import os, math, time, signal

from robot.control import pid, track
from robot import settings

#==== import and load the robot control board ====
board=None
if os.path.exists(os.path.join(os.getcwd(),'robot','boards',settings.FILENAME)):
    try:
        exec("from robot.boards import "+settings.FILENAME[:-3]+' as board')
        board=locals()['board']
        print('    ROBOT: '+settings.MOBILE_ROBOT)
    except:
        board=None

COUNTER_POS=0

class Controller:
    def __init__(self):
        try:
            self.robot=board.Board()
        except:
            print("    ERROR: The control board wasn't loaded")
            self.robot=None
      
        #---- constants for the tracking process ----
        self.constant_b = 0.1  #0.05
        self.constant_k1 = 1.0 #3.0
        self.constant_k2 = 1.0 #3.0
        #---- position ----
        self.x_position = 0
        self.y_position = 0
        self.z_position = 0
        #---- encoders ----
        self.encoder1 = 0
        self.encoder2 = 0
        self.prev_encoder1 = 0
        self.prev_encoder2 = 0
        self.prev_delta_encoder_1 = 0
        self.prev_delta_encoder_2 = 0
        #---- others ----
        self.smooth = True
        self.finished = True 
        self.count = 0        
        self.sample_time = 0.05
        self.action = 'stop'
        self.SEND_POSITION = lambda x, y, theta: None     
        self.COUNTER_POS = 0
        self.reference = track.Track()

        self.timer_init()

    def robot_speed(self,set_point1, set_point2):
        self.robot.set_speeds(set_point1, set_point2)
    
    def ask_status(self):
        encoder1, encoder2, battery = self.robot.read_state()
        # self.robot.reset_encoders()
        self.encoder1 = encoder1
        self.encoder2 = encoder2

    def movement_init(self, x, y, t):
        self.smooth = True
        self.experiment_reset()

        delta_x = x - self.globalPositionX
        delta_y = y - self.globalPositionY

        beta = math.atan2(delta_y, delta_x)
        theta_n = self.globalPositionZ
        alpha = beta - theta_n
        l = math.sqrt(delta_x * delta_x + delta_y * delta_y)
        xf_p = l * math.cos(alpha)
        yf_p = l * math.sin(alpha)

        track_parameters = {
            'x_planning': [0, xf_p],
            'y_planning': [0, yf_p],
            't_planning': [0, t],
            'sample_time': self.sample_time
        }

        self.reference.generate(**track_parameters)

        self.timer_start()

    def experiment_init(self, save_file, smooth, track_parameters):
        
        self.smooth = smooth
        self.experiment_reset()

        track_parameters['sample_time'] = self.sample_time

        self.reference.generate(**track_parameters)
        
        self.timer_start()

    def experiment_finish(self):
        self.robot.set_speeds(0, 0)
        try:
            signal.setitimer(signal.ITIMER_REAL, 0, 0)
        except:
            print ("    Error signal")
        self.finished = True
    
    def experiment_reset(self):
        self.finished = False
        self.count = 0
		
		#==== ROVERT ====        
        if not settings.PID:
            pid.reset()

    def timer_handler(self, signum, frame):
        
        #---- check for end the movement unavoidably ----
        if self.finished:
            self.action_exec()
            return
		#==== ROVERT ====        
        if not settings.PID:
            elapsed = pid.process_time()

            encoder1, encoder2, battery, current1, current2 = self.robot.read_state()
            delta_encoder_1, delta_encoder_2 = self.navigation(encoder1, encoder2)
            set_point1, set_point2 = self.tracking()
            um1, um2 = pid.speeds_regulation(set_point1, set_point2, delta_encoder_1, delta_encoder_2, elapsed, 0, 0, battery)
            self.robot.set_speeds(um1, um2)
		
		#==== TLBOT ====
        else:
            encoder1, encoder2, battery = self.robot.read_state()
            self.navigation(encoder1, encoder2)
            set_point1, set_point2 = self.tracking()	
            
            self.robot.set_speeds(set_point1, set_point2)
		#---------------------------------

        self.count += 1

        if self.count >= self.reference.n_points:
            self.finished = True

    def calculatePosition(self, encoder1, encoder2):
        global COUNTER_POS
    
        delta_encoder_1 = encoder1 - self.prev_encoder1
        delta_encoder_2 = encoder2 - self.prev_encoder2

        self.encoder1 = encoder1
        self.encoder2 = encoder2

        if delta_encoder_1 > 130 or delta_encoder_1 < -130:
            delta_encoder_1 = self.prev_delta_encoder_1
            self.encoder1 = 0
            self.encoder2 = 0
            self.robot.reset_encoders()

        if delta_encoder_2 > 130 or delta_encoder_2 < -130:
            delta_encoder_2 = self.prev_delta_encoder_2
            self.encoder1 = 0
            self.encoder2 = 0
            self.robot.reset_encoders()

        if encoder1 > 2000000000 or encoder1 < -2000000000 or encoder2 > 2000000000 or encoder2 < -2000000000:
            self.encoder1 = 0
            self.encoder2 = 0
            self.robot.reset_encoders()

        self.prev_encoder1 = self.encoder1
        self.prev_encoder2 = self.encoder2

        self.prev_delta_encoder_1 = delta_encoder_1
        self.prev_delta_encoder_2 = delta_encoder_2

        dfr = delta_encoder_2 * 2 * math.pi / settings.ENCODER_STEPS
        dfl = delta_encoder_1 * 2 * math.pi / settings.ENCODER_STEPS

        ds = (dfr + dfl) * settings.RADIUS / 2
        dz = (dfr - dfl) * settings.RADIUS / settings.DISTANCE

        self.x_position += ds * math.cos(self.z_position + dz / 2)
        self.y_position += ds * math.sin(self.z_position + dz / 2)
        self.z_position += dz

        # send position
        COUNTER_POS+=1
        if COUNTER_POS==3:
            print('bot', -self.y_position, self.x_position, self.z_position)
            self.SEND_POSITION(-self.y_position, self.x_position, self.z_position)
            COUNTER_POS=0;
		
        
        return delta_encoder_1, delta_encoder_2

    def navigation(self, encoder1, encoder2):
        delta_encoder_1, delta_encoder_2 = self.calculatePosition(encoder1, encoder2)
        return delta_encoder_1, delta_encoder_2

    def _tracking(self):
        """
        Calculate the speed of each wheel according to the track.
        """
        xd = self.reference.xd_vector[self.count]
        xd_dot = self.reference.xd_dot_vector[self.count]
        yd = self.reference.yd_vector[self.count]
        yd_dot = self.reference.yd_dot_vector[self.count]
        zd = self.reference.zd_vector[self.count]
        zd_dot = self.reference.zd_dot_vector[self.count]

        y1 = self.x_position + self.constant_b * math.cos(self.z_position)
        y2 = self.y_position + self.constant_b * math.sin(self.z_position)

        if self.smooth:
            y1d = xd
            y2d = yd
            y2d_dot = yd_dot
            y1d_dot = xd_dot
        else:
            y1d = xd + self.constant_b * math.cos(zd)
            y2d = yd + self.constant_b * math.sin(zd)

            y2d_dot = yd_dot + self.constant_b * math.cos(zd) * zd_dot
            y1d_dot = xd_dot - self.constant_b * math.sin(zd) * zd_dot

        u2 = y2d_dot + self.constant_k2 * (y2d - y2)
        u1 = y1d_dot + self.constant_k1 * (y1d - y1)

        the_v = math.cos(self.z_position) * u1 + u2 * math.sin(self.z_position)
        the_omega = u1 * (- math.sin(self.z_position) / self.constant_b) + u2 * math.cos(
            self.z_position) / self.constant_b

        set_point2 = the_v / settings.RADIUS + the_omega * settings.DISTANCE / 2 / settings.RADIUS
        set_point1 = the_v / settings.RADIUS - the_omega * settings.DISTANCE / 2 / settings.RADIUS

        return set_point1, set_point2

    def wasd_velocities(self, x, y):
        left = right = y
        ratio = abs(x/settings.MAX_SPEED)
        if x > 0:
            right *= 1 - ratio
        elif x < 0:
            left *= 1 - ratio
        return right, left

    def timer_start(self):
        try:
            if not settings.PID:
                config_parameters = {
                    'prev': time.time(),
                    'sample': self.sample_time
                }
                pid.config(**config_parameters)
            signal.setitimer(signal.ITIMER_REAL, self.sample_time, self.sample_time)
        except:
            print("    Error signal")

    def timer_init(self):
        try:
            signal.signal(signal.SIGALRM, self.timer_handler)
            signal.setitimer(signal.ITIMER_REAL, 0, 0)
        except:
            print("    Error signal")

    def action_exec(self):
        """
        Execute predefined actions for the robot.
        
        This function read and execute the actions defined in ``actions.py`` 
        
        >>> controller=Controller()
        >>> controller.action_exec()
        """
        try:
            actions=open(os.path.join(os.getcwd(),'robot','actions.py'),'rU').read()
            exec(actions)
        except OSError:
            print("    ERROR: Actions")
