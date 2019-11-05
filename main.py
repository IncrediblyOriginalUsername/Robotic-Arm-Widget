# ////////////////////////////////////////////////////////////////
# //                     IMPORT STATEMENTS                      //
# ////////////////////////////////////////////////////////////////

import math
import sys
import time
import threading
import spidev

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
from threading import Thread
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from kivy.config import Config
from kivy.core.window import Window
from pidev.kivy import DPEAButton
from pidev.kivy import PauseScreen
from time import sleep
import RPi.GPIO as GPIO 
from pidev.stepper import stepper
spi = spidev.SpiDev()
from pidev.Cyprus_Commands import Cyprus_Commands_RPi as cyprus


# ////////////////////////////////////////////////////////////////
# //                      GLOBAL VARIABLES                      //
# //                         CONSTANTS                          //
# ////////////////////////////////////////////////////////////////
ON = False
OFF = True
HOME = True
TOP = False
OPEN = False
CLOSE = True
YELLOW = .180, 0.188, 0.980, 1
BLUE = 0.917, 0.796, 0.380, 1
DEBOUNCE = 0.1
global RAMP_LENGTH
global INIT_RAMP_SPEED
INIT_RAMP_SPEED = 150
RAMP_LENGTH = 725
cyprus.initialize()



# ////////////////////////////////////////////////////////////////
# //            DECLARE APP CLASS AND SCREENMANAGER             //
# //                     LOAD KIVY FILE                         //
# ////////////////////////////////////////////////////////////////
class MyApp(App):
    def build(self):
        self.title = "Perpetual Motion"
        return sm

Builder.load_file('main.kv')
Window.clearcolor = (.1, .1,.1, 1) # (WHITE)

cyprus.open_spi()

# ////////////////////////////////////////////////////////////////
# //                    SLUSH/HARDWARE SETUP                    //
# ////////////////////////////////////////////////////////////////
sm = ScreenManager()
ramp = stepper(port = 0, speed = INIT_RAMP_SPEED)

# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////
	
# ////////////////////////////////////////////////////////////////
# //        DEFINE MAINSCREEN CLASS THAT KIVY RECOGNIZES        //
# //                                                            //
# //   KIVY UI CAN INTERACT DIRECTLY W/ THE FUNCTIONS DEFINED   //
# //     CORRESPONDS TO BUTTON/SLIDER/WIDGET "on_release"       //
# //                                                            //
# //   SHOULD REFERENCE MAIN FUNCTIONS WITHIN THESE FUNCTIONS   //
# //      SHOULD NOT INTERACT DIRECTLY WITH THE HARDWARE        //
# ////////////////////////////////////////////////////////////////
s0 = stepper(port=0, micro_steps=32, hold_current=20, run_current=20, accel_current=20, deaccel_current=20,
                 steps_per_unit=200, speed=8)
s0.free_all()
global sv
sv = True
class MainScreen(Screen):
    version = cyprus.read_firmware_version()
    staircaseSpeedText = '0'
    rampSpeed = INIT_RAMP_SPEED
    staircaseSpeed = 40
    global stairz
    global rampz
    global dire
    global bruh
    bruh = False
    dire =1
    rampz = rampSpeed
    stairz = staircaseSpeed
    global rampstatus
    global autot
    global stairstatus
    autot = False
    rampstatus = False
    stairstatus = False
    cyprus.initialize()
    cyprus.setup_servo(2)
    global aaaaa
    aaaaa = False
    global s0
    s0 = stepper(port=0, micro_steps=32, hold_current=20, run_current=20, accel_current=20, deaccel_current=20,
                 steps_per_unit=200, speed=8)
    cyprus.set_pwm_values(1, period_value=100000, compare_value=0,
                          compare_mode=cyprus.LESS_THAN_OR_EQUAL)



    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.initialize()

    def toggleGate(self):
        global sv
        if sv == True:
            cyprus.set_servo_position(2, 0.5)
            print("Open")
            sv = False
        elif sv == False:
            cyprus.set_servo_position(2, 0)
            print("Closed")
            sv = True
    def debounce(self):
        print("Not sure why we need a seperate debounce method but it says it needs one in the instructions")
    def isBallatTop(self):
        global autot
        if(cyprus.read_gpio() & 0b0001) == 0:
            print("gamers")
            sleep(.01)
        else:
            sleep(.01)
            self.toggleRamp()

    def isBallatBottom(self):
        global autot
        global dire
        global bruh
        global sv
        if (cyprus.read_gpio() & 0b0001) == 1:
            print("gamers")
            sleep(.01)
        else:
            sleep(.01)
            dire = 1
            print(sv)
            if(sv == False):
                if(bruh == True):
                    self.toggleGate()
                    sleep(1)
                    self.toggleStaircase()
                    sleep(1)
                    bruh = False
                    autot = False
                    print("activatedfff")
    def runThing(self):
        global aaaaa
        global dire
        while autot == True & aaaaa == True:
            self.isBallatBottom()
            #self.isBallatTop()
    def buttonStair(self):
        if(aaaaa == False):
            self.toggleStaircase()
    def buttonGate(self):
        if (aaaaa == False):
            self.toggleGate()
    def buttonRamp(self):
        if(aaaaa == False):
            self.toggleRamp()
    def toggleStaircase(self):
        global stairstatus
        global stairz
        stair = stairz * 800
        if stairstatus == False:
            stairstatus = True
            print("yep + %d" % stair)
            cyprus.set_pwm_values(1, period_value=100000, compare_value=stair,
                                  compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        else:
            stairstatus = False
            cyprus.set_pwm_values(1, period_value=100000, compare_value=0,
                                  compare_mode=cyprus.LESS_THAN_OR_EQUAL)
        print("Turn on and off staircase here")

    def toggleRamp(self):
        global rampz
        global dire
        global autot
        if(dire == 1):
            s0.set_speed_in_steps(rampz*4)
            s0.relative_move(28.5)
            dire = 0
            self.toggleRamp()
        elif s0.isBusy() == False:
            sleep(0.05)
            s0.stop()
            sleep(0.5)
            s0.set_speed_in_steps(rampz * 6)
            s0.relative_move(-28.5)
            #s0.run(0, rampz * 6)
            autot = False
            dire =1

    def auto(self):
        global aaaaa
        global autot
        if(aaaaa == False):
            aaaaa = True
            Thread(target=self.autom).start()
            Thread.daemon = True
        else:
            autot = False
            aaaaa = False

    def autom(self):
        global aaaaa
        while aaaaa == True:
            global bruh
            bruh = True
            global autot
            if (aaaaa == False):
                return
            self.toggleRamp()
            if(aaaaa == False):
                return
            sleep(1)
            if (aaaaa == False):
                return
            self.toggleGate()
            if (aaaaa == False):
                return
            sleep(1)
            if (aaaaa == False):
                return
            self.toggleStaircase()
            if (aaaaa == False):
                return
            autot = True
            self.runThing()
            if (aaaaa == False):
                return


     #   print("Run through one cycle of the perpetual motion machine")
        
    def setRampSpeed(self, speed):
        global rampz
        global on
        rampz = self.ids.rampSpeed.value
        print("%d" % rampz)
        self.ids.rampSpeedLabel.text = "%d" % rampz
        print("Set the ramp speed and update slider text")
        
    def setStaircaseSpeed(self, speed):
        global stairz
        global on
        stairz = self.ids.staircaseSpeed.value
        self.ids.staircaseSpeedLabel.text = "%d" % stairz
        print("%d" % stairz)
        print("Set the staircase speed and update slider text")
        
    def initialize(self):
        print("Close gate, stop staircase and home ramp here")

    def resetColors(self):
        self.ids.gate.color = YELLOW
        self.ids.staircase.color = YELLOW
        self.ids.ramp.color = YELLOW
        self.ids.auto.color = BLUE
    
    def quit(self):
        print("Exit")
        s0.free_all()
        spi.close()
        GPIO.cleanup()
        cyprus.close()
        MyApp().stop()

sm.add_widget(MainScreen(name = 'main'))

# ////////////////////////////////////////////////////////////////
# //                          RUN APP                           //
# ////////////////////////////////////////////////////////////////

MyApp().run()
cyprus.close_spi()
