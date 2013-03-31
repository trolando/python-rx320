RX320 Python controller
===========
This project consists of two parts, a controller using pySerial to manage the connection to the RX320 device by Ten-Tec, and a simple TCP/IP interface that allows one to control the RX320 over TCP/IP using text commands. 

Motivation for this project was that the original Java implementation of this controller used too many resources on the Raspberry Pi, possibly due to the RXTX library. It turned out that using Python and pySerial for this task not only resulted in leaner code but also improved the efficiency.
