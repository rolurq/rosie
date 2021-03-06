import logging
# TODO: more detailed error logs
try:
    from serial import Serial
except:
    logging.error("couldn't import serial")

from struct import *
from math import pi
from threading import Thread
from time import sleep

import os
from robot.motion.MotorHandler.MotorDriver.Dual import DualSpeedMotorDriver

COMMAND_SETPIDPARAM = 0xA6
COMMAND_SETPOINT = 0xA7
COMMAND_GETSTATE = b'\xA8'
COMMAND_GETSTATE_RESPONSE = b'\xA9'
COMMAND_ENCODER_RESET = b'\xAA'
COMMAND_START_SAMPLING_SPEEDS = b'\xAB'
COMMAND_STOP_SAMPLING_SPEEDS = b'\xAC'


class Arduino(DualSpeedMotorDriver):
    """
    A class to represent an Arduino Motor Driver

    @param steps_per_revolution: Encoders count in one wheel revolution
    @param max_speed: Maximum value of the speed of the motor
    """

    def __init__(self, max_speed, port='/dev/ttyACM0', baudrate=9600):

        try:
            self.serialPort = Serial(port, baudrate)
        except:
            logging.error("serial port not found")
        self.batteryStatus = 100
        self.sampling = False
        self.speed1 = []
        self.speed2 = []
        self.pulses1 = 0
        self.pulses2 = 0
        self.lastPulses1 = 0
        self.lastPulses2 = 0
        self.setpoint1 = 0.0
        self.setpoint2 = 0.0
        self.max_speed = max_speed

    # TODO: Implement a function to change encoders per revolution parameter

    def set_speeds(self, speed_1, speed_2):
        # if abs(speed_1) > abs(self.max_speed):
        #     speed_1 = self.max_speed
        # if abs(speed_2) > abs(self.max_speed):
        #     speed_2 = self.max_speed
        self.setpoint1 = speed_1
        self.setpoint2 = speed_2
        package = pack("<Bff", COMMAND_SETPOINT, speed_2, speed_1)
        try:
            self.serialPort.write(package)
        except:
            logging.error("setting speeds")

    def read_delta_encoders_count_state(self):
        try:
            self.serialPort.write(COMMAND_GETSTATE)
            header = self.serialPort.read()
            if header == COMMAND_GETSTATE_RESPONSE:
                pulses1 = self.serialPort.read()
                pulses1 += self.serialPort.read()
                pulses1 += self.serialPort.read()
                pulses1 += self.serialPort.read()
                pulses1, = unpack("i", pulses1)

                pulses2 = self.serialPort.read()
                pulses2 += self.serialPort.read()
                pulses2 += self.serialPort.read()
                pulses2 += self.serialPort.read()
                pulses2, = unpack("i", pulses2)

                batteryCharge, = unpack('B', self.serialPort.read())

                self.lastPulses1 = self.pulses1
                self.lastPulses2 = self.pulses2
                self.pulses1 = pulses1
                self.pulses2 = pulses2
                self.batteryStatus = batteryCharge
                delta_pulses1 = self.pulses1 - self.lastPulses1
                delta_pulses2 = self.pulses2 - self.lastPulses2
                return delta_pulses2, delta_pulses1, self.batteryStatus, 0, 0
        except:
            logging.error("reading encoders")
            return 0,0,0,0,0
    def set_constants(self, kc, ki, kd):
        package = pack("<Bfff", COMMAND_SETPIDPARAM, kc, ki, kd)
        try:
            self.serialPort.write(package)
        except:
            logging.error("setting constants")

    def reset_encoders(self):
        try:
            self.serialPort.write(COMMAND_ENCODER_RESET)
        except:
            logging.error("reseting encoders")

    def start_sampling_speeds(self):
        try:
            self.serialPort.write(COMMAND_START_SAMPLING_SPEEDS)
            self.sampling = True
        except:
            logging.error("start sampling")

    def stop_sampling_speeds(self):
        try:
            self.serialPort.write(COMMAND_STOP_SAMPLING_SPEEDS)
            self.sampling = False
        except:
            logging.error("stop sampling")

    # For debuggin propuses only
    # TODO: This should run in other thread
    def run_sampler(self):
        sleepLapse = 0.01
        while True:
            if self.sampling == True:
                try:
                    while self.serialPort.inWaiting() < 4:
                        sleep(sleepLapse)
                    speed1 = self.serialPort.read()
                    speed1 += self.serialPort.read()
                    speed1 += self.serialPort.read()
                    speed1 += self.serialPort.read()
                    speed1, = unpack("f", speed1)

                    while self.serialPort.inWaiting() < 4:
                        sleep(sleepLapse)
                    speed2 = self.serialPort.read()
                    speed2 += self.serialPort.read()
                    speed2 += self.serialPort.read()
                    speed2 += self.serialPort.read()
                    speed2, = unpack("f", speed2)

                    self.speed1.append(speed1)
                    self.speed2.append(speed2)
                except:
                    logging.error("running sampler")
            sleep(sleepLapse)
