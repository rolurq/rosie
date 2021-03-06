import thread
from string import Template
import os

from robot.motion.MovementSupervisor.Differential import DifferentialDriveMovementSupervisor


class FileLoggerMovementSupervisor(DifferentialDriveMovementSupervisor):
    """
    Class to supervise a differential drive mobile robot in a movement using a .m file

    @param robot_parameters: Parameters of the robot
    @param file_name_provider: The name provider used to create the files
    @type robot_parameters: motion.RobotParameters.DifferentialDriveRobotParameters
    @type file_name_provider: motion.FileNameProvider.FileNameProvider
    """

    def __init__(self, robot_parameters, file_name_provider):
        super(FileLoggerMovementSupervisor, self).__init__()
        self.robot_parameters = robot_parameters
        self.file_name_provider = file_name_provider
        self.output_directory = os.path.join(os.path.dirname(__file__), 'logs')
        # create output directory
        if not os.path.exists(self.output_directory):
            os.mkdir(self.output_directory)

        self.time_vector = list()
        self.sample_time_vector = list()
        self.x_position_vector = list()
        self.x_speed_vector = list()
        self.y_position_vector = list()
        self.y_speed_vector = list()
        self.z_position_vector = list()
        self.z_speed_vector = list()

        self.x_ref_vector = list()
        self.x_ref_speed_vector = list()
        self.y_ref_vector = list()
        self.y_ref_speed_vector = list()
        self.z_ref_vector = list()
        self.z_ref_speed_vector = list()

        self.speed_x_ref_vector = list()
        self.speed_y_ref_vector = list()
        self.angular_speed_1_vector = list()
        self.current_1_vector = list()
        self.angular_1_ref_vector = list()
        self.angular_speed_2_vector = list()
        self.current_2_vector = list()
        self.angular_2_ref_vector = list()

        self.updates_done = 0
        self.expected_updates = None

    def movement_begin(self, expected_updates):
        """
        Method to be called when the movement begins

        @param expected_updates: Number of times movement_updates wil be called
        @type expected_updates: int
        """
        self.updates_done = 0
        self.expected_updates = expected_updates

    def movement_update(self, robot_state):
        """
        Method to be called when the state of the robot changes during the movement

        @type robot_state: motion.RobotState.DifferentialDriveRobotState
        @param robot_state: the new state of the robot
        """
        if self.expected_updates is None:
            return
        elif self.updates_done >= self.expected_updates:
            return

        self.sample_time_vector.append(robot_state.elapsed_time)

        self.x_position_vector.append(robot_state.location.x_position)
        self.y_position_vector.append(robot_state.location.y_position)
        self.z_position_vector.append(robot_state.location.z_position)

        self.x_ref_vector.append(robot_state.reference_location.x_position)
        self.y_ref_vector.append(robot_state.reference_location.y_position)
        self.z_ref_vector.append(robot_state.reference_location.z_position)

        self.x_ref_speed_vector.append(robot_state.reference_speed.x_speed)
        self.y_ref_speed_vector.append(robot_state.reference_speed.y_speed)
        self.z_ref_speed_vector.append(robot_state.reference_speed.z_speed)

        self.speed_x_ref_vector.append(robot_state.x_speed_ref)
        self.speed_y_ref_vector.append(robot_state.y_speed_ref)

        self.angular_speed_1_vector.append(robot_state.angular_speed_1)
        self.angular_1_ref_vector.append(robot_state.set_point_1)
        self.current_1_vector.append(robot_state.current_1)

        self.angular_speed_2_vector.append(robot_state.angular_speed_2)
        self.angular_2_ref_vector.append(robot_state.set_point_2)
        self.current_2_vector.append(robot_state.current_2)

        self.updates_done += 1

    def movement_end(self):
        """
        Method to be called when the movement ends

        """
        if self.expected_updates is None:
            return
        file_name = self.file_name_provider.get_file_name() + ".m"
        file_name = os.path.join(self.output_directory, file_name)
        thread.start_new_thread(FileLoggerMovementSupervisor.file_writer_thread,
                                (file_name, self.updates_done, self.x_position_vector, self.y_position_vector,
                                 self.z_position_vector, self.x_speed_vector, self.y_speed_vector, self.z_speed_vector,
                                 self.x_ref_vector, self.y_ref_vector, self.z_ref_vector, self.x_ref_speed_vector,
                                 self.y_ref_speed_vector, self.z_ref_speed_vector, self.angular_speed_1_vector,
                                 self.angular_speed_2_vector, self.current_1_vector, self.current_2_vector,
                                 self.angular_1_ref_vector, self.angular_2_ref_vector, self.speed_x_ref_vector,
                                 self.speed_y_ref_vector, self.sample_time_vector, self.time_vector,
                                 self.robot_parameters.wheel_radius, self.robot_parameters.wheel_distance,
                                 self.robot_parameters.constant_b, self.robot_parameters.constant_k1,
                                 self.robot_parameters.constant_k2, self.robot_parameters.constant_kc,
                                 self.robot_parameters.constant_ki, self.robot_parameters.constant_kd))

    @staticmethod
    def file_writer_thread(file_name, updates_done, x_position_vector, y_position_vector, z_position_vector,
                           x_speed_vector,
                           y_speed_vector, z_speed_vector, x_ref_vector, y_ref_vector, z_ref_vector,
                           x_ref_speed_vector,
                           y_ref_speed_vector, z_ref_speed_vector, angular_speed_1_vector, angular_speed_2_vector,
                           current_1_vector, current_2_vector, angular_1_ref_vector, angular_2_ref_vector,
                           speed_x_ref_vector, speed_y_ref_vector, sample_time_vector, time_vector, wheel_radius,
                           wheel_distance, constant_b, constant_k1, constant_k2, constant_kc, constant_ki,
                           constant_kd):

        time_vector = [0.]
        for i in range(updates_done - 1):
            time_vector.append(time_vector[-1] + sample_time_vector[i])
            x_speed_vector.append((x_position_vector[i + 1] - x_position_vector[i]) / \
                                (sample_time_vector[i]))
            y_speed_vector.append((y_position_vector[i + 1] - y_position_vector[i]) / \
                                (sample_time_vector[i]))
            z_speed_vector.append((z_position_vector[i + 1] - z_position_vector[i]) / \
                                (sample_time_vector[i]))

        x_speed_vector.append(x_speed_vector[-1])
        y_speed_vector.append(y_speed_vector[-1])
        z_speed_vector.append(z_speed_vector[-1])

        dict_current_log = {
            's_angular_speed_1_vector': " ".join((str(i) for i in angular_speed_1_vector)),
            's_angular_speed_2_vector': " ".join((str(i) for i in angular_speed_2_vector)),
            's_current_1_vector': " ".join((str(i) for i in current_1_vector)),
            's_current_2_vector': " ".join((str(i) for i in current_2_vector)),
            's_time_vector': " ".join((str(i) for i in time_vector)),
            's_sample_time_vector': " ".join((str(i) for i in sample_time_vector)),
            's_angular_1_ref_vector': " ".join((str(i) for i in angular_1_ref_vector)),
            's_angular_2_ref_vector': " ".join((str(i) for i in angular_2_ref_vector)),
            's_x_position_vector': " ".join((str(i) for i in x_position_vector)),
            's_y_position_vector': " ".join((str(i) for i in y_position_vector)),
            's_z_position_vector': " ".join((str(i) for i in z_position_vector)),
            's_x_ref_vector': " ".join((str(i) for i in x_ref_vector)),
            's_y_ref_vector': " ".join((str(i) for i in y_ref_vector)),
            's_z_ref_vector': " ".join((str(i) for i in z_ref_vector)),
            's_x_speed_vector': " ".join((str(i) for i in x_speed_vector)),
            's_y_speed_vector': " ".join((str(i) for i in y_speed_vector)),
            's_z_speed_vector': " ".join((str(i) for i in z_speed_vector)),
            's_x_ref_speed_vector': " ".join((str(i) for i in x_ref_speed_vector)),
            's_y_ref_speed_vector': " ".join((str(i) for i in y_ref_speed_vector)),
            's_z_ref_speed_vector': " ".join((str(i) for i in z_ref_speed_vector)),
            's_speed_x_ref_vector': " ".join((str(i) for i in speed_x_ref_vector)),
            's_speed_y_ref_vector': " ".join((str(i) for i in speed_y_ref_vector)),
            'updates_done': str(updates_done),
            'wheel_radius': str(wheel_radius),
            'wheel_distance': str(wheel_distance),
            'constant_b': str(constant_b),
            'constant_k1': str(constant_k1),
            'constant_k2': str(constant_k2),
            'constant_ki': str(constant_ki),
            'constant_kd': str(constant_kd),
            'constant_kc': str(constant_kc)
        }

        save_file = open(file_name, 'Uw+')

        current_log = """
        close all
        clear all
        clc

        count = $updates_done ;
        radius = $wheel_radius ;
        distance = $wheel_distance ;
        constant_b = $constant_b ;
        constant_k1 = $constant_k1 ;
        constant_k2 = $constant_k2 ;
        constant_ki = $constant_ki ;
        constant_kd = $constant_kd ;
        constant_kc = $constant_kc ;

        speed1 = [ $s_angular_speed_1_vector ] ;
        speed2 = [ $s_angular_speed_2_vector ] ;
        current1 = [ $s_current_1_vector ] ;
        current2 = [ $s_current_2_vector ] ;
        time = [ $s_time_vector ] ;
        sample_time = [ $s_sample_time_vector ] ;
        ref1 = [ $s_angular_1_ref_vector ] ;
        ref2 = [ $s_angular_2_ref_vector ] ;
        x = [ $s_x_position_vector ] ;
        y = [ $s_y_position_vector ] ;
        z = [ $s_z_position_vector ] ;
        xd = [ $s_x_ref_vector ] ;
        yd = [ $s_y_ref_vector ] ;
        zd = [ $s_z_ref_vector ] ;
        dx = [ $s_x_speed_vector ] ;
        dy = [ $s_y_speed_vector ] ;
        dz = [ $s_z_speed_vector ] ;
        dxd = [ $s_x_ref_speed_vector ] ;
        dyd = [ $s_y_ref_speed_vector ] ;
        dzd = [ $s_z_ref_speed_vector ] ;
        dxr = [ $s_speed_x_ref_vector ] ;
        dyr = [ $s_speed_y_ref_vector ] ;


        figure;
        plot(time,x,time,xd) ;
        title('X Position vs Time.') ;
        legend('X','X - Reference') ;
        xlabel('Time (s)') ;
        ylabel('X Position (m)') ;
        grid on

        figure;
        plot(time,y,time,yd) ;
        title('Y Position vs Time.') ;
        legend('Y','Y - Reference') ;
        xlabel('Time (s)') ;
        ylabel('Y Position (m)') ;
        grid on

        figure;
        plot(time,z,time,zd) ;
        title('Orientation vs Time.') ;
        legend('Z','Z - Reference') ;
        xlabel('Time (s)') ;
        ylabel('Z Position (rad)') ;
        grid on

        figure;
        plot(x,y,xd,yd) ;
        title('Y Position vs X Position (Path).') ;
        legend('Path','Path - Reference') ;
        xlabel('X Position (m)') ;
        ylabel('Y Position (m)') ;
        grid on

        figure;
        plot(time,speed1,time,ref1) ;
        title('WL vs Time.') ;
        legend('WL','WL - Reference') ;
        xlabel('Time (s)') ;
        ylabel('Angular Speed (rad/s)') ;
        grid on

        figure;
        plot(time,speed2,time,ref2) ;
        title('WR vs Time.') ;
        legend('WR','WR - Reference') ;
        xlabel('Time (s)') ;
        ylabel('Angular Speed (rad/s)') ;
        grid on

        figure;
        plot(time,current1,time,current2) ;
        title('Currents vs Time.') ;
        legend('Left Motor','Right Motor') ;
        xlabel('Time (s)') ;
        ylabel('Current (A)') ;
        grid on

        figure;
        plot(time,dx,time,dxr,time,dxd) ;
        title('X Speed vs Time.') ;
        legend('DX','DXR - Reference','DXD - Planning') ;
        xlabel('Time (s)') ;
        ylabel('X Speed (m/s)') ;
        grid on

        figure;
        plot(time,dy,time,dyr,time,dyd) ;
        title('Y Speed vs Time.') ;
        legend('DY','DYR - Reference','DYD - Planning') ;
        xlabel('Time (s)') ;
        ylabel('Y Speed (m/s)') ;
        grid on

        figure;
        plot(time,dz,time,dzd) ;
        title('Z Speed vs Time.') ;
        legend('DZ','DZD - Planning') ;
        xlabel('Time (s)') ;
        ylabel('Z Speed (rad/s)') ;
        grid on

        figure;
        plot(sample_time*1000);
        title('Sample Time.');
        ylabel ( 'Sample Time (ms)' ) ;
        xlabel ( 'Sample (k)' ) ;
        grid on
        """

        template_current_log = Template(current_log)
        current_log = template_current_log.substitute(dict_current_log)

        save_file.write(current_log)
        save_file.close()
