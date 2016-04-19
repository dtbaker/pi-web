# USAGE
# python robot.py

# import the necessary packages
from __future__ import print_function

import serial
import string

import argparse
import time
import threading
from numpy import empty, nan
import os
import sys

import numpy as np

import zmq
import pigpio

import pylibmc


servo_speed = 5

c = threading.Condition()

# servo pulse width settings:
PW	= [1400, 1300]
desired_servo_PW = [1430,1330]
LIMIT	= [[800, 2300], [800, 1500]]

class Move_Servo_Thread(threading.Thread):
	def __init__(self, name):
		threading.Thread.__init__(self)
		self.name = name

	def run(self):
		global PW # current servo PW
		global desired_servo_PW # desired PW, swing over to this range.
		while True:
			c.acquire()
			if(set(desired_servo_PW) == set(PW)):
				print("thread waiting...")
				c.wait()  # wait for the object tracking thread to tell us the object has moved.
			else:

				if desired_servo_PW[0] > LIMIT[0][1]:
					desired_servo_PW[0] = LIMIT[0][1]
				elif desired_servo_PW[0] < LIMIT[0][0]:
					desired_servo_PW[0] = LIMIT[0][0]
				if desired_servo_PW[1] > LIMIT[1][1]:
					desired_servo_PW[1] = LIMIT[1][1]
				elif desired_servo_PW[1] < LIMIT[1][0]:
					desired_servo_PW[1] = LIMIT[1][0]

				if PW[0] < desired_servo_PW[0]:
					PW[0] += servo_speed
				elif PW[0] > desired_servo_PW[0]:
					PW[0] -= servo_speed
				if PW[1] < desired_servo_PW[1]:
					PW[1] += servo_speed
				elif PW[1] > desired_servo_PW[1]:
					PW[1] -= servo_speed

				print("change servo PW to:")
				print(PW)
				# code to send PW here....
			c.release()



class ServerWorker(threading.Thread):
	def __init__(self, name):
		threading.Thread.__init__ (self)
		self.name = name

	def run(self):
		global PW
		global desired_servo_PW

		context = zmq.Context()
		worker = context.socket(zmq.REP)
		worker.bind('tcp://*:5555')

		print('Worker started')

		while True:

			c.acquire()
			print("waiting for message from ZMQ...")
			#  Wait for next request from client
			message = worker.recv()
			# print("Received request: %s" % message)
			worker.send("ok")
			print("processing message from ZMQ...")

			# code here sets desired_servo_PW[] based on received message
			desired_servo_PW[0] = .....
			desired_servo_PW[1] = .....
			c.notify_all()

			print("done processing ZMQ message...")
			c.release()
