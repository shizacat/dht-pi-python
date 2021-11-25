#!/usr/bin/env python3

import time

from dht import DHT22

pin_number_on_board = 32
m = DHT22(pin_number_on_board)
m.delay_between_readings = 0.5

while True:
    try:
        temperature, humidity = m.measure()
        print("humidity", humidity)
        print("temperature", temperature)
    except RuntimeError as e:
        print("Error:", e)
    time.sleep(0.5)
