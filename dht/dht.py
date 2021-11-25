"""
Base on https://github.com/adafruit/Adafruit_CircuitPython_DHT/blob/main/adafruit_dht.py
"""

import time
from typing import Tuple

import RPi.GPIO as GPIO


class DHT22:
    """Support for DHT22 device.

    :param int pin: digital pin used for communication (By board number)
    """

    def __init__(self, pin: int):
        self.pin = pin
        
        # config
        self.delay_between_readings = 2  # second
        self._max_pulses = 81
        self._hiLevel = 51  # us, Level if great is 1 bit, else 0 bit 
        # state
        self._last_called = 0

        GPIO.setmode(GPIO.BOARD)
    
    def __del__(self):
        GPIO.cleanup(self.pin)
    
    def measure(self):
        """Measure runs the communications to the DHT11/22 type device.
        if successful, the class properties temperature and humidity will
        return the reading returned from the device.
        
        Raises
            RuntimeError exception for checksum failure and for insufficient
            data returned from the device (try again)
        """
        self._check_last_call()

        # start
        transitions = self._get_response()

        if len(transitions) < 81:
            raise RuntimeError(f"Few transitions received ({len(transitions)})")

        # convert transtions to microsecond delta pulses, use last 81 pulses
        pulses = self._transitions_to_pulse(transitions, 81)

        # Convert pulses to binary
        package = []
        for byte_start in range(0, 80, 16):
            package.append(self._pulses_to_binary(pulses, byte_start, 16))

        # check sum
        self._check_sum(package)
        # View
        return self._get_temp_humidity(package)
    
    def _check_last_call(self):
        if (
            self._last_called != 0
            and (time.monotonic() - self._last_called) < self.delay_between_readings
        ):
            raise RuntimeError("Very frequent call")
        self._last_called = time.monotonic()

    def _get_response(self) -> list:
        """_get_pulses implements the communication protcol for
        DHT11 and DHT22 type devices.  It sends a start signal
        of a specific length and listens and measures the
        return signal lengths.
        return pulses (array.array uint16) contains alternating high and low
        transition times starting with a low transition time.  Normally
        pulses will have 81 elements for the DHT11/22 type devices.
        """
        transitions = []
        dhtval = True
        timestamp = time.monotonic()  # take timestamp

        # start transmit
        GPIO.setup(self.pin, GPIO.OUT, initial=GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(self.pin, GPIO.LOW)
        time.sleep(20 / 1000)  # ms
        GPIO.output(self.pin, GPIO.HIGH)

        # response
        GPIO.setup(self.pin, GPIO.IN)
        while time.monotonic() - timestamp < 0.3:
            if dhtval != GPIO.input(self.pin):
                dhtval = not dhtval  # we toggled
                transitions.append(time.monotonic())  # save the timestamp
        return transitions
    
    def _transitions_to_pulse(self, transitions: list, last: int = 81) -> list:
        """Convert transition to pulse (duration, us)

        Args:
            last - how many last transition have been used
        
        Return
            pulses
        """
        pulses = []
        transitions = transitions[-81:]
        for i in range(1, len(transitions)):
            pulses_micro_sec = int(1000000 * (transitions[i] - transitions[i - 1]))
            pulses.append(min(pulses_micro_sec, 65535))
        return pulses

    def _pulses_to_binary(self, pulses: list, start: int, length: int) -> int:
        """Takes pulses, a list of transition times, and converts
        them to a 1's or 0's.  The pulses array contains the transition times.
        pulses starts with a low transition time followed by a high transistion time.
        then a low followed by a high and so on.  The low transition times are
        ignored.  Only the high transition times are used.  If the high
        transition time is greater than __hiLevel, that counts as a bit=1, if the
        high transition time is less that __hiLevel, that counts as a bit=0.

        Args:
            pulses is the array transition times
            start is the starting index in pulses to start converting
            length is the count of pulses
        
        Returns
            an integer containing the converted 1 and 0 bits
        """
        binary = 0
        for pulse in pulses[start:start + length:2]:
            bit = 1 if pulse > self._hiLevel else 0
            binary = binary << 1 | bit
        return binary

    def _get_temp_humidity(self, package: list) -> Tuple[float, float]:
        """View

        Return
            temperature (C degree), humidity
        """
        # humidity is 2 bytes
        humidity = ((package[0] << 8) | package[1]) / 10
        # temperature is 2 bytes
        # MSB is sign, bits 0-14 are magnitude)
        temperature = (((package[2] & 0x7F) << 8) | package[3]) / 10
        # set sign
        if package[2] & 0x80:
            temperature = -temperature
        return temperature, humidity
    
    def _check_sum(self, package: list):
        """Check checksum and raise if error"""
        chk_sum = 0
        for b in package[0:4]:
            chk_sum += b
        if chk_sum & 0xFF != package[4]:
            raise RuntimeError("Wrong checksum")
