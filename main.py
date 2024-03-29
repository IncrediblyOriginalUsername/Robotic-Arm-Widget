# ////////////////////////////////////////////////////////////////
# //                     IMPORT STATEMENTS                      //
# ////////////////////////////////////////////////////////////////

import math
import sys
import time
import threading

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import *
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from kivy.config import Config
from kivy.core.window import Window
from pidev.kivy import DPEAButton
from pidev.kivy import PauseScreen
from threading import Thread
from time import sleep
import RPi.GPIO as GPIO 
from pidev.stepper import stepper
from pidev.Cyprus_Commands import Cyprus_Commands_RPi as cyprus


# ////////////////////////////////////////////////////////////////
# //                      GLOBAL VARIABLES                      //
# //                         CONSTANTS                          //
# ////////////////////////////////////////////////////////////////
START = True
STOP = False
UP = False
DOWN = True
ON = True
OFF = False
YELLOW = .180, 0.188, 0.980, 1
BLUE = 0.917, 0.796, 0.380, 1
CLOCKWISE = 0
COUNTERCLOCKWISE = 1
ARM_SLEEP = 2.5
DEBOUNCE = 0.10
cyprus.initialize()

lowerTowerPosition = 60
upperTowerPosition = 76


# ////////////////////////////////////////////////////////////////
# //            DECLARE APP CLASS AND SCREENMANAGER             //
# //                     LOAD KIVY FILE                         //
# ////////////////////////////////////////////////////////////////
class MyApp(App):

    def build(self):
        self.title = "Robotic Arm"
        return sm

Builder.load_file('main.kv')
Window.clearcolor = (.1, .1,.1, 1) # (WHITE)

cyprus.open_spi()

# ////////////////////////////////////////////////////////////////
# //                    SLUSH/HARDWARE SETUP                    //
# ////////////////////////////////////////////////////////////////

sm = ScreenManager()
arm = stepper(port = 0, speed = 10)

# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////
s0 = stepper(port=0, micro_steps=32, hold_current=20, run_current=20, accel_current=20, deaccel_current=20,
             steps_per_unit=200, speed=8)
global arm
arm = True
global magnet
magnet = False
global tall
global game
game = 0
tall = False
global short
short = False

class MainScreen(Screen):
    version = cyprus.read_firmware_version()
    armPosition = 0
    lastClick = time.clock()

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.initialize()

    def debounce(self):
        processInput = False
        currentTime = time.clock()
        if ((currentTime - self.lastClick) > DEBOUNCE):
            processInput = True
        self.lastClick = currentTime
        return processInput

    def startDetect(self):
        print('working?')
        Thread(target=self.isBallOnTallTower).start()
        Thread(target=self.isBallOnShortTower).start()

    def toggleArm(self):
        global arm
        if arm == False:
            cyprus.set_pwm_values(1, period_value=100000, compare_value=0,
                                  compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            print("Up")

            arm = True
        else:
            cyprus.set_pwm_values(1, period_value=100000, compare_value=100000,
                                  compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            arm = False
            print("Down")

    def toggleMagnet(self):
        global magnet
        if magnet == False:
            cyprus.set_servo_position(2, 1)
            magnet = True
            print('magnet on')
        else:
            cyprus.set_servo_position(2, 0.5)
            magnet = False
            print('magnet off')
        
    def auto(self):
        global tall
        global short
        global f
        global game
        global magnet
        if(game == 0):
            self.isBallOnTallTower()
            game = 1
        if tall == True:
            print('running auto 1')
            if(f == False):
                s0.go_to_position(1.53)
            else:
                s0.go_to_position(-0.47)
            sleep(1)
            self.toggleArm()
            sleep(1)
            self.toggleMagnet()
            sleep(1)
            self.toggleArm()
            sleep(1)
            self.isBallOnTallTower()
            self.auto()
        else:
            if(f == False):
                s0.go_to_position(1.2)
            else:
                s0.go_to_position(-.8)
            sleep(1)
            self.toggleArm()
            sleep(1)
            self.toggleMagnet()
            sleep(1)
            self.toggleArm()
            sleep(1)
            print("running auto 2")
            if(magnet == True):
                tall = True
                print("yeet")
                self.auto()
            else:
                tall = False
                self.auto()

    def setArmPosition(self, position):
        s0.set_speed(.5)
        s0.go_to_position(self.ids.moveArm.value / 5000)
        self.ids.armControlLabel.text = "Arm Position: %s" % (self.ids.moveArm.value / 5000)

    def homeArm(self):
        global f
        s0.set_speed(1)
        s0.start_relative_move(4)
        while not s0.read_switch():
            print("es")
            continue
        if(s0.get_position_in_units()>1):
            print("yes")
            s0.relative_move(-.5)
            s0.start_relative_move(-4)
            while not s0.read_switch():
                print("stop")
                continue
            s0.hardStop()
            s0.set_as_home()
            f = False
        else:
            s0.hardStop()
            s0.set_as_home()
            f = True
        print('ok')
        
    def isBallOnTallTower(self):
        global tall
        if (cyprus.read_gpio() & 0b0001) == 1:
            sleep(0.01)
            if (cyprus.read_gpio() & 0b0001) == 1:
                tall = False
        else:
            sleep(0.01)
            tall = True
            print("Ball on top of tall tower")

    def isBallOnShortTower(self):
        global short
        while True:
            if (cyprus.read_gpio() & 0b0010) == 1:
                sleep(0.01)
                if (cyprus.read_gpio() & 0b0010) == 1:
                    short = False
                    print("Ball on top of short tower")
            else:
                sleep(0.01)
                short = True

        
    def initialize(self):
        self.homeArm()
        cyprus.set_servo_position(2, 0.5)
        print("Home arm and turn off magnet")

    def resetColors(self):
        self.ids.armControl.color = YELLOW
        self.ids.magnetControl.color = YELLOW
        self.ids.auto.color = BLUE

    def quit(self):
        s0.free_all()
        GPIO.cleanup()
        cyprus.close()
        MyApp().stop()
    
sm.add_widget(MainScreen(name = 'main'))


# ////////////////////////////////////////////////////////////////
# //                          RUN APP                           //
# ////////////////////////////////////////////////////////////////

MyApp().run()
cyprus.close_spi()
