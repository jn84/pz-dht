# pz-dht

A tool to read and report DHT11/22 temperature and humidity sensors

Disclaimer:
Tested only with python 3.5

Depends on pigpio
 - pigpiod daemon must be running
 - see: http://abyz.me.uk/rpi/pigpio/index.html

 - In Raspbian Stretch:
 ```bash
   pi@raspberrypi:~ $ sudo apt-get update
   pi@raspberrypi:~ $ sudo apt-get install python3-pigpio
   pi@raspberrypi:~ $ sudo pigpiod
 ````

 - To build yourself
 ```bash
   pi@raspberrypi:~ $ git clone https://github.com/joan2937/pigpio.git
   pi@raspberrypi:~ $ cd pigpio
   pi@raspberrypi:~ $ make
   pi@raspberrypi:~ $ sudo make install
   pi@raspberrypi:~ $ sudo pigpiod
 ```
