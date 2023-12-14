# Copyright 2020 Hochschule Luzern - Informatik
# Author: Peter Sollberger <peter.sollberger@hslu.ch>
import RPi.GPIO as GPIO


class Encoder:
    """
    Maintains position from encoder signals A and B.
    """
    pos = 0
    last = 0
    delta = 0
    bits = 0
    lastToggle = -1

    def __init__(self, inpA, inpB):
        """
        Initialize encoder
        :param inpA: Input pin for encoder signal A
        :param inpB: Input pin for encoder signal B
        """
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)  # Use BCM GPIO numbers

        self.inpA = inpA
        self.inpB = inpB

        GPIO.setup(self.inpA, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.inpB, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        GPIO.add_event_detect(self.inpA, GPIO.BOTH, callback=self.__input_callback)  # add edge detection on channel
        GPIO.add_event_detect(self.inpB, GPIO.BOTH, callback=self.__input_callback)  # add edge detection on channel

    def __del__(self):
        """
        Stop and clean up.
        """
        GPIO.remove_event_detect(self.inpA)
        GPIO.remove_event_detect(self.inpB)

    def __input_callback(self, channel):
        """
        ISR on both input signals.
        """
        b = self.bits
        m = 1 << channel
        if GPIO.input(channel):
            b |= m
        else:
            b &= ~m
        t = b ^ self.bits
        self.bits = b
        if t == self.lastToggle:
            return
        self.lastToggle = t

        x = 0
        if self.bits & (1 << self.inpA):
            x = 3
        if self.bits & (1 << self.inpB):
            x ^= 1
        diff = self.last - x  # difference last - new
        if diff & 1:  # bit 0 = value (1)
            self.last = x  # store new as next last
            self.delta += (diff & 2) - 1  # bit 1 = direction (+/-)

            val = self.delta
            self.delta = val % 1
            val //= 1
            if val:
                self.pos += val

    def getPosition(self):
        """
        :return: Current position in [mm]
        """
        # 1024 tics/rotation, 4 edge-detects pro tic, pi * 58 mm/rotation
        return int(self.pos / 1024.0 / 4.0 * 3.142 * 58.0)

    def resetPosition(self):
        """
        Reset position to zero.
        """
        self.pos = 0
