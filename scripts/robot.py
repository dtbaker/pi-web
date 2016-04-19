# USAGE
# python robot.py

# import the necessary packages
from __future__ import print_function


import serial
#import serial.threaded ? https://github.com/pyserial/pyserial/blob/master/examples/at_protocol.py
import threading

import argparse
import time

from numpy import empty, nan
import os
import sys

import numpy as np

import zmq
import pigpio



context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")

ser = serial.Serial('/dev/ttyAMA0', 19200, timeout=0.5)

		# pan | tilt
SERVO = [20, 21]     # Servos connected these GPIO pins
DIR   = [1, -1]
PW    = [1400, 1300] # current servo pwm
CENTER    = [1400, 1300]  # center point.
LIMIT    = [[800, 2300], [800, 1500]]
SPEED = [10, 10]

pi = pigpio.pi() # Connect to local Pi.

for x in SERVO:
	pi.set_mode(x, pigpio.OUTPUT) # Set gpio as an output.

for x in range(len(SERVO)):  # For each servo.
	pi.set_servo_pulsewidth(SERVO[x], CENTER[x])


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()


ap.add_argument('--width', dest='width', type=int, default=320, help='Capture width')
ap.add_argument('--height', dest='height', type=int, default=240, help='Capture height')
ap.add_argument('--maxspeed', dest='maxspeed', type=int, default=20, help='Max robot speed')
ap.add_argument('--minspeed', dest='minspeed', type=int, default=11, help='Min robot speed')
ap.add_argument('--objectwidth', dest='objectwidth', type=int, default=10, help='Rough width of initial object in cm')
ap.add_argument('--focallength', dest='focallength', type=float, default=3.6, help='Camera focal length in mm')
ap.add_argument('--quiet', dest='quiet', action='store_true', help='Do not show graphical output (Useful in combination with --output-dir ).')

args = ap.parse_args()

quiet = args.quiet
if quiet is None:
	quiet = False


# motor1 is left, motor2 is right
def motor_speeds(motor1, motor2):
	motor1 = int(motor1)
	motor2 = int(motor2)
	# replace xd with xe in below serial bytes to get acceleration working
	if(motor1 == 0 and motor2 == 0):
		ser.write(b'\xe0') # both stop
		ser.write(chr(motor1))
		ser.write(chr(motor2))
	elif(motor1 >= 0 and motor2 >= 0):
		ser.write(b'\xe9')  # both forward
		ser.write(chr(motor1))
		ser.write(chr(motor2))
	elif(motor1 < 0 and motor2 < 0):
		ser.write(b'\xe6')  # both back
		ser.write(chr(abs(motor1)))
		ser.write(chr(abs(motor2)))
	elif(motor1 > 0 and motor2 <= 0):
		ser.write(b'\xe5')  # turn right
		ser.write(chr(abs(motor1)))
		ser.write(chr(abs(motor2)))
	elif(motor1 < 0 and motor2 >= 0):
		ser.write(b'\xeA')  # turn left
		ser.write(chr(abs(motor1)))
		ser.write(chr(abs(motor2)))
	else:
		if not quiet:
			print("Unknown motor command!")

#def PolyArea(x, y):
#	return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

def PolygonArea(corners):
	n = len(corners)  # of corners
	area = 0.0
	for i in range(n):
		j = (i + 1) % n
		area += corners[i][0] * corners[j][1]
		area -= corners[j][0] * corners[i][1]
	area = abs(area) / 2.0
	return area

previous_motor_speed = [0,0]
current_motor_speed = [0,0]
initial_object_position = [(0,0),(0,0),(0,0),(0,0)]
initial_object_center_position = [0,0]
initial_object_size = 0
current_object_position = [(0,0),(0,0),(0,0),(0,0)]
current_object_center_position = [0,0]
current_object_size = 0


# write a stop signal to serial so our robot doesn't take off when we start
motor_speeds(0, 0)
time.sleep(0.5)
# motor_speeds(12, 12)  # forward
# time.sleep(1)
# motor_speeds(-12, -12)  # back
# time.sleep(1)
# motor_speeds(0, 12)  # turn left with one wheel
# time.sleep(1)
# motor_speeds(-12, 12)  # turn left with spin
# time.sleep(1)
# motor_speeds(12, 0)  # turn right with one wheel
# time.sleep(1)
# motor_speeds(12, -12)  # turn right with spin
# time.sleep(1)



object_size_percentage_average = []
object_size_percentage_limit = 12
kfilterfactor = 0.5

tl = 0
br = 0

first_run = True


while True:
	#  Wait for next request from client
	message = socket.recv()
	# print("Received request: %s" % message)
	socket.send(b"ok")

	if message == "reset":
		for x in range(len(SERVO)):  # For each servo.
			PW[x] = CENTER[x]
			pi.set_servo_pulsewidth(SERVO[x], PW[x])
	elif message != "none":
		bits = message.split("|")
		if len(bits) == 4:
			print(bits)
			tl = bits[0].split(":")
			tr = bits[1].split(":")
			br = bits[2].split(":")
			bl = bits[3].split(":")
			tl[0] = int(tl[0])
			tl[1] = int(tl[1])
			tr[0] = int(tr[0])
			tr[1] = int(tr[1])
			br[0] = int(br[0])
			br[1] = int(br[1])
			bl[0] = int(bl[0])
			bl[1] = int(bl[1])
			#  Send reply back to client
			if first_run:
				first_run = False
				initial_object_position = [tl,tr,br,bl]  # set from message.
				initial_object_center_position = [(tl[0] + tr[0]) / 2, (tl[1] + bl[1]) / 2]  # set from message.
				initial_object_size = 1  # set from message.

			# split our message up to get the sizes etc..

			current_object_position = [tl, tr, br, bl]  # set from message.
			current_object_center_position = [(tl[0] + tr[0]) / 2, (tl[1] + bl[1]) / 2]
			# current_object_center_position_new = [(CMT.tl[0] + CMT.tr[0]) / 2, (CMT.tl[1] + CMT.bl[1]) / 2]
			# current_object_center_position[0] = (current_object_center_position_new[0] * kfilterfactor) + (current_object_center_position[0] * (1.0 - kfilterfactor))
			# current_object_center_position[1] = (current_object_center_position_new[1] * kfilterfactor) + (current_object_center_position[1] * (1.0 - kfilterfactor))
			# current_object_size = PolygonArea([CMT.tl, CMT.tr, CMT.br, CMT.bl])
			current_object_size_new = PolygonArea([tl, tr, br, bl])
			current_object_size = (current_object_size_new * kfilterfactor) + (
			current_object_size * (1.0 - kfilterfactor))
			# work out averages / kfilter

			if initial_object_size == current_object_size and set(current_object_center_position) == set(
					initial_object_center_position):
				# object hasn't moved
				if not quiet:
					print("object hasn't moved")
			else:
				# object has moved
				# work out how far it has moved ( left/right and forward/back ) then calculate what speed we have to move the motors
				# we do this by working out how much of a percentage the object has moved to the left/right

				# movement_multiplier = 0.01
				# current_object_center_position[0] - initial_object_center_position[0]
				left_right_diff = current_object_center_position[0] - (args.width / 2)
				up_down_diff = current_object_center_position[1] - (args.height / 2)
				speed = np.interp(abs(left_right_diff), [0, 100], [args.minspeed, args.maxspeed])

				object_size_percent1 = round((current_object_size / initial_object_size) * 100)
				object_size_percent2 = round(((float(tr[0]) - float(tl[0])) / (float(initial_object_position[1][0]) - float(initial_object_position[0][0]))) * 100)

				forward_back = int(np.interp(abs(object_size_percent1), [0, 100], [args.maxspeed, 0]))

				with open("log.txt", "a") as logfile:
					s = "Current Pos: " + str(current_object_center_position[0]) + " , " + str(
						current_object_center_position[1]) + " " + str(
						int(left_right_diff)) + "% | " + str(
						int(up_down_diff)) + "% from center, speed: " + str(
						speed)
					if not quiet:
						print(s)
					logfile.write(s + "\n")
					s = "Current Size: " + str(current_object_size) + ", " + str(object_size_percent1) + "%, " + str(
						object_size_percent2) + "% " + str(tr[0]) + ":" + str(tl[0])
					if not quiet:
						print(s)
					logfile.write(s + "\n")
					s = "Forward Back Speed: " + str(forward_back)
					if not quiet:
						print(s)
					logfile.write(s + "\n")

				# first we move the camera to track the object. if the camera turns past our left/right limits that
				# is when we start turning the robot.

				PWM_change = 30
				if left_right_diff < -20 or left_right_diff > 20:
					PW[0] += int(np.interp(left_right_diff, [-100, 100], [40, -40]))
				if up_down_diff < -20 or up_down_diff > 20:
					PW[1] += int(np.interp(up_down_diff, [-100, 100], [-40, 40]))

				# pan_servo_pos = np.interp(int(left_right_diff), [-150, 150], [100, -100])
				# PW[0] += int(pan_servo_pos)
				# tilt_servo_pos = np.interp(int(up_down_diff), [-150, 150], [-100, 100])
				# PW[1] += int(tilt_servo_pos)


				if PW[0] > LIMIT[0][1]:
					PW[0] = LIMIT[0][1]
				elif PW[0] < LIMIT[0][0]:
					PW[0] = LIMIT[0][0]
				if PW[1] > LIMIT[1][1]:
					PW[1] = LIMIT[1][1]
				elif PW[1] < LIMIT[1][0]:
					PW[1] = LIMIT[1][0]
				pi.set_servo_pulsewidth(SERVO[0], PW[0])
				pi.set_servo_pulsewidth(SERVO[1], PW[1])

				with open("log.txt", "a") as logfile:
					s = "Servo Pos: " + str(PW[0]) + " , " + str(PW[1])
					if not quiet:
						print(s)
					logfile.write(s + "\n")

				if left_right_diff < -10:
					# object has moved left more than 10%, turn the robot left,
					# increase speed of right motors, decrease speed of left motors
					# current_motor_speed[0] -= abs(left_right_diff) * movement_multiplier
					# current_motor_speed[1] += abs(left_right_diff) * movement_multiplier
					current_motor_speed[0] = forward_back + (speed * -1)
					current_motor_speed[1] = forward_back + (speed * 1)

				elif left_right_diff > 10:
					# object has moved right, turn the robot right
					# increase speed of left motors, decrease speed of right motors
					# current_motor_speed[0] += abs(left_right_diff) * movement_multiplier
					# current_motor_speed[1] -= abs(left_right_diff) * movement_multiplier
					current_motor_speed[0] = forward_back + (speed * 1)
					current_motor_speed[1] = forward_back + (speed * -1)


				elif forward_back > 5:
					current_motor_speed[0] = forward_back
					current_motor_speed[1] = forward_back
				else:
					# object hasn't moved left/right yet, maybe forward/back
					# todo: move forward/back with object size and ultrasound sensor
					current_motor_speed[0] = 0
					current_motor_speed[1] = 0

				with open("log.txt", "a") as logfile:
					s = "Motor: " + str(current_motor_speed[0]) + " , " + str(current_motor_speed[1])
					if not quiet:
						print(s)
					logfile.write(s + "\n")

				# check speed limits.
				if current_motor_speed[0] > args.maxspeed:
					current_motor_speed[0] = args.maxspeed
				if current_motor_speed[1] > args.maxspeed:
					current_motor_speed[1] = args.maxspeed
				if current_motor_speed[0] < (args.maxspeed * -1):
					current_motor_speed[0] = (args.maxspeed * -1)
				if current_motor_speed[1] < (args.maxspeed * -1):
					current_motor_speed[1] = (args.maxspeed * -1)

				send_motor_speed = [int(current_motor_speed[0]), int(current_motor_speed[1])]
				if (set(previous_motor_speed) != set(send_motor_speed)):
					with open("log.txt", "a") as logfile:
						s = "Send Motor: " + str(send_motor_speed[0]) + " , " + str(send_motor_speed[1])
						if not quiet:
							print(s)
						logfile.write(s + "\n")

					motor_speeds(send_motor_speed[0], send_motor_speed[1])
					previous_motor_speed = send_motor_speed

				# print(np.array((CMT.tl, CMT.tr, CMT.br, CMT.bl, CMT.tl)))

		else:
			print("Failed to get coordinates")



motor_speeds(0, 0)

time.sleep(2.0)
ser.close()

for x in SERVO:
	pi.set_servo_pulsewidth(x, 0) # Switch servo pulses off.

pi.stop()

print("finished")



