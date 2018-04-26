#!/usr/bin/env python

# 2014-07-11 DHT22.py
# Source: http://abyz.me.uk/rpi/pigpio/examples.html

# TODO: Clean up, add comments, and rework

import atexit
import pigpio
import time


class DhtSensor:
    """
    A class to read relative humidity and temperature from the
    DHT22 sensor.  The sensor is also known as the AM2302.
    """

    def __init__(self, pigpio_d, gpio_pin):
        """
        Instantiate with the Pi and gpio to which the DHT22 output
        pin is connected.

        Taking readings more often than about once every two seconds will
        eventually cause the DHT22 to hang.  A 3 second interval seems OK.
        """

        self.pigpio_d = pigpio_d
        self.gpio_data_pin = gpio_pin

        self.powered = True

        self.cb = None

        atexit.register(self.cancel)

        self.bad_CS = 0  # Bad checksum count.
        self.bad_SM = 0  # Short message count.
        self.bad_MM = 0  # Missing message count.

        # Power cycle if timeout > MAX_TIMEOUTS.
        self.no_response = 0
        self.MAX_NO_RESPONSE = 2

        # Relative humidity storage
        self.rhum = -999
        # Temperature storage
        self.temp = -999

        self.tov = None

        self.high_tick = 0
        self.bit_counter = 40

        pigpio_d.set_pull_up_down(gpio_pin, pigpio.PUD_OFF)

        pigpio_d.set_watchdog(gpio_pin, 0)  # Kill any watchdogs.

        self.cb = pi.callback(gpio_pin, pigpio.EITHER_EDGE, self._cb)

    # Parse a single bit of output from the DHT sensor
    def _cb(self, gpio, level, tick):
        """
        Accumulate the 40 data bits.  Format into 5 bytes, humidity high,
        humidity low, temperature high, temperature low, checksum.
        """
        # Get width of pulse in microseconds
        pulse_len = pigpio.tickDiff(self.high_tick, tick)

        if level == 0:

            # Pulse width determines bit state
            # Pulse width of 26~28 us = LOW  = 0
            # Pulse width of   ~70 us = HIGH = 1

            # Long pulse > bit high
            if pulse_len >= 50:
                bit_value = 1

                # Pulse too long -> error
                if pulse_len >= 200:  # Bad bit?
                    self.read_checksum = 256  # Force bad checksum.

            # Short pulse > bit low
            else:
                bit_value = 0

            # Keep individual payload bytes separated
            # TODO: Why?

            # Message complete.
            if self.bit_counter >= 40:
                self.bit_counter = 40

            # Receiving checksum byte
            elif self.bit_counter >= 32:
                self.read_checksum = (self.read_checksum << 1) + bit_value

                if self.bit_counter == 39:

                    # 40th bit received.
                    # Stop watching for new bits
                    self.pigpio_d.set_watchdog(self.gpio_data_pin, 0)

                    self.no_response = 0

                    read_full_payload = self.hH + self.hL + self.tH + self.tL

                    if (read_full_payload & 255) == self.read_checksum:  # Is checksum ok?

                        self.rhum = ((self.hH << 8) + self.hL) * 0.1

                        # If bit mask is > 0, leftmost bit is set -> negative number
                        if self.tH & 128:  # Negative temperature.
                            temp_multiplier = -0.1
                            # Mask out the sign bit
                            self.tH = self.tH & 127
                        else:
                            temp_multiplier = 0.1

                        # Shift the high byte so that it lines up with the low byte
                        self.temp = ((self.tH << 8) + self.tL) * temp_multiplier

                        self.tov = time.time()

                    else:

                        self.bad_CS += 1

            elif self.bit_counter >= 24:  # in temp low byte
                self.tL = (self.tL << 1) + bit_value

            elif self.bit_counter >= 16:  # in temp high byte
                self.tH = (self.tH << 1) + bit_value

            elif self.bit_counter >= 8:  # in humidity low byte
                self.hL = (self.hL << 1) + bit_value

            elif self.bit_counter >= 0:  # in humidity high byte
                self.hH = (self.hH << 1) + bit_value

            else:  # header bits
                pass

            self.bit_counter += 1

        elif level == 1:
            self.high_tick = tick
            if pulse_len > 250000:
                self.bit_counter = -2
                self.hH = 0
                self.hL = 0
                self.tH = 0
                self.tL = 0
                self.read_checksum = 0

        else:  # level == pigpio.TIMEOUT:
            self.pi.set_watchdog(self.gpio, 0)
            if self.bit_counter < 8:  # Too few data bits received.
                self.bad_MM += 1  # Bump missing message count.
                self.no_response += 1
                if self.no_response > self.MAX_NO_RESPONSE:
                    self.no_response = 0
            elif self.bit_counter < 39:  # Short message receieved.
                self.bad_SM += 1  # Bump short message count.
                self.no_response = 0

            else:  # Full message received.
                self.no_response = 0

    def temperature(self):
        """Return current temperature."""
        return self.temp

    def humidity(self):
        """Return current relative humidity."""
        return self.rhum

    def staleness(self):
        """Return time since measurement made."""
        if self.tov is not None:
            return time.time() - self.tov
        else:
            return -999

    def bad_checksum(self):
        """Return count of messages received with bad checksums."""
        return self.bad_CS

    def short_message(self):
        """Return count of short messages."""
        return self.bad_SM

    def missing_message(self):
        """Return count of missing messages."""
        return self.bad_MM

    def sensor_resets(self):
        """Return count of power cycles because of sensor hangs."""
        return self.bad_SR

    def trigger(self):
        """Trigger a new relative humidity and temperature reading."""
        if self.powered:
            if self.LED is not None:
                self.pi.write(self.LED, 1)

            self.pi.write(self.gpio, pigpio.LOW)
            time.sleep(0.017)  # 17 ms
            self.pi.set_mode(self.gpio, pigpio.INPUT)
            self.pi.set_watchdog(self.gpio, 200)

    def cancel(self):
        """Cancel the DHT22 sensor."""

        self.pi.set_watchdog(self.gpio, 0)

        if self.cb != None:
            self.cb.cancel()
            self.cb = None


if __name__ == "__main__":

    import time

    import pigpio

    import DHT22

    # Intervals of about 2 seconds or less will eventually hang the DHT22.
    INTERVAL = 3

    pi = pigpio.pi()

    s = DHT22.sensor(pi, 22, LED=16, power=8)

    r = 0

    next_reading = time.time()

    while True:
        r += 1

        s.trigger()

        time.sleep(0.2)

        print("{} {} {} {:3.2f} {} {} {} {}".format(
            r, s.humidity(), s.temperature(), s.staleness(),
            s.bad_checksum(), s.short_message(), s.missing_message(),
            s.sensor_resets()))

        next_reading += INTERVAL

        time.sleep(next_reading - time.time())  # Overall INTERVAL second polling.

    s.cancel()

    pi.stop()
