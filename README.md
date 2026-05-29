# Chip design class
 Diseño e implementación de prototipos de sistemas digitales usando la tarjeta FRDM KL25z, diseñando y/o adaptando hardware y desarrollando el software necesarios.
[NEW] Device 20:25:05:00:A8:59 RPI_LINK

[ WARN:0@1.411] global cap_gstreamer.cpp:1777 open OpenCV | GStreamer warning: Cannot query video position: status=0, value=-1, duration=-1
Iniciando hilo Bluetooth...
Conectando al Dobot Magician...
Traceback (most recent call last):
  File "/usr/lib/python3/dist-packages/serial/serialposix.py", line 322, in open
    self.fd = os.open(self.portstr, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
              ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/dev/ttyAMA0'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/ingenierinis/GOAT/chip-design-class/DOBORT/pydobot/main_dobot.py", line 217, in <module>
    robot = pydobot.Dobot(port=PORT, verbose=False)
  File "/home/ingenierinis/GOAT/chip-design-class/DOBORT/pydobot/pydobot/dobot.py", line 21, in __init__
    self.ser = serial.Serial(port,
               ~~~~~~~~~~~~~^^^^^^
                             baudrate=115200,
                             ^^^^^^^^^^^^^^^^
                             parity=serial.PARITY_NONE,
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^
                             stopbits=serial.STOPBITS_ONE,
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                             bytesize=serial.EIGHTBITS)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/serial/serialutil.py", line 244, in __init__
    self.open()
    ~~~~~~~~~^^
  File "/usr/lib/python3/dist-packages/serial/serialposix.py", line 325, in open
    raise SerialException(msg.errno, "could not open port {}: {}".format(self._port, msg))
serial.serialutil.SerialException: [Errno 2] could not open port /dev/ttyAMA0: [Errno 2] No such file or directory: '/dev/ttyAMA0'


------------------
(program exited with code: 1)
Press return to continue

[ WARN:0@1.411] global cap_gstreamer.cpp:1777 open OpenCV | GStreamer warning: Cannot query video position: status=0, value=-1, duration=-1
Iniciando hilo Bluetooth...
Conectando al Dobot Magician...
Traceback (most recent call last):
  File "/usr/lib/python3/dist-packages/serial/serialposix.py", line 322, in open
    self.fd = os.open(self.portstr, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
              ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/dev/ttyAMA0'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/ingenierinis/GOAT/chip-design-class/DOBORT/pydobot/main_dobot.py", line 217, in <module>
    robot = pydobot.Dobot(port=PORT, verbose=False)
  File "/home/ingenierinis/GOAT/chip-design-class/DOBORT/pydobot/pydobot/dobot.py", line 21, in __init__
    self.ser = serial.Serial(port,
               ~~~~~~~~~~~~~^^^^^^
                             baudrate=115200,
                             ^^^^^^^^^^^^^^^^
                             parity=serial.PARITY_NONE,
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^
                             stopbits=serial.STOPBITS_ONE,
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                             bytesize=serial.EIGHTBITS)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/serial/serialutil.py", line 244, in __init__
    self.open()
    ~~~~~~~~~^^
  File "/usr/lib/python3/dist-packages/serial/serialposix.py", line 325, in open
    raise SerialException(msg.errno, "could not open port {}: {}".format(self._port, msg))
serial.serialutil.SerialException: [Errno 2] could not open port /dev/ttyAMA0: [Errno 2] No such file or directory: '/dev/ttyAMA0'


------------------
(program exited with code: 1)
Press return to continue


