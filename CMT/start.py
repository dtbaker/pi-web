# USAGE
# python run.py
# python run.py --preview 1

# import the necessary packages
from __future__ import print_function

import sys
sys.path.append('/opt/ros/jade/lib/python2.7/dist-packages')

import serial
#import serial.threaded ? https://github.com/pyserial/pyserial/blob/master/examples/at_protocol.py
import threading

from imutils.video.pivideostream import PiVideoStream
import argparse
import imutils
import time
import cv2


from numpy import empty, nan
import os
import sys

import CMT
import numpy as np
import util

ser = serial.Serial('/dev/ttyAMA0', 19200, timeout=0.5)

CMT = CMT.CMT()


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()

ap.add_argument('inputpath', nargs='?', help='The input path.')
ap.add_argument('--challenge', dest='challenge', action='store_true', help='Enter challenge mode.')
ap.add_argument('--preview', dest='preview', action='store_const', const=True, default=None, help='Force preview')
ap.add_argument('--width', dest='width', type=int, default=240, help='Capture width')
ap.add_argument('--height', dest='height', type=int, default=180, help='Capture height')
ap.add_argument('--no-scale', dest='estimate_scale', action='store_false', help='Disable scale estimation')
ap.add_argument('--with-rotation', dest='estimate_rotation', action='store_true', help='Enable rotation estimation')
ap.add_argument('--bbox', dest='bbox', help='Specify initial bounding box.')
ap.add_argument('--pause', dest='pause', action='store_true', help='Pause after every frame and wait for any key.')
ap.add_argument('--output-dir', dest='output', help='Specify a directory for output data.')
ap.add_argument('--quiet', dest='quiet', action='store_true', help='Do not show graphical output (Useful in combination with --output-dir ).')
ap.add_argument('--skip', dest='skip', action='store', default=None, help='Skip the first n frames', type=int)

ap.add_argument("-n", "--num-frames", type=int, default=100, help="# of frames to loop over for FPS test")

args = ap.parse_args()

CMT.estimate_scale = args.estimate_scale
CMT.estimate_rotation = args.estimate_rotation

if args.pause:
	pause_time = 0
else:
	pause_time = 10


if args.output is not None:
	if not os.path.exists(args.output):
		os.mkdir(args.output)
	elif not os.path.isdir(args.output):
		raise Exception(args.output + ' exists, but is not a directory')


# Clean up
cv2.destroyAllWindows()
preview = args.preview
if preview is None:
	preview = False
quiet = args.quiet
if quiet is None:
	quiet = False


def motor_speeds_timed(motor1, motor2):
	print ("Done time")

# motor1 is left, motor2 is right
def motor_speeds(motor1, motor2):
	if(motor1 == 0 and motor2 == 0):
		if not quiet:
			print("Both motors stopping")
		ser.write(b'\xd0') # both stop
		ser.write(chr(motor1))
		ser.write(chr(motor2))
	elif(motor1 >= 0 and motor2 >= 0):
		if not quiet:
			print("Both motors forward")
		ser.write(b'\xd9')  # both forward
		ser.write(chr(motor1))
		ser.write(chr(motor2))
	elif(motor1 < 0 and motor2 < 0):
		if not quiet:
			print("Both motors back")
		ser.write(b'\xd6')  # both back
		ser.write(chr(abs(motor1)))
		ser.write(chr(abs(motor2)))
	elif(motor1 > 0 and motor2 <= 0):
		if not quiet:
			print("Turn right")
		ser.write(b'\xd5')  # turn right
		ser.write(chr(abs(motor1)))
		ser.write(chr(abs(motor2)))
	elif(motor1 < 0 and motor2 >= 0):
		if not quiet:
			print("Turn left")
		ser.write(b'\xdA')  # turn left
		ser.write(chr(abs(motor1)))
		ser.write(chr(abs(motor2)))
	else:
		if not quiet:
			print("Unknown motor command!")

	if not quiet:
		print ("Done")

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



# created a *threaded *video stream, allow the camera sensor to warmup,
# and start the FPS counter
if not quiet:
	print("Starting camera")
vs = PiVideoStream((args.width, args.height)).start()
time.sleep(2.0)

frame_counter = 0
frame_init_at = 20 # start processing once we've read this many frames, as it can take some time to get the cam warmed up
frame_limit = 1000

# 240 x 180
# 370 x 240
# image_resize = 300

tl = 0
br = 0


# read a bunch of frames from the camera to start
while frame_counter < frame_limit and os.path.isfile("running-flag.txt"):

	print(time.time())

	frame = vs.read()
	# frame = imutils.resize(frame, width=image_resize)

	frame_counter += 1
	#print("frame " + str(frame_counter))
	if(frame_counter == frame_init_at):
		# Read first frame
		im_gray0 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		im_draw = np.copy(frame)

		if args.bbox is not None:
			# Try to disassemble user specified bounding box
			values = args.bbox.split(',')
			try:
				values = [int(v) for v in values]
			except:
				raise Exception('Unable to parse bounding box')
			if len(values) != 4:
				raise Exception('Bounding box must have exactly 4 elements')
			bbox = np.array(values)

			# Convert to point representation, adding singleton dimension
			bbox = util.bb2pts(bbox[None, :])

			# Squeeze
			bbox = bbox[0, :]

			tl = bbox[:2]
			br = bbox[2:4]
		else:
			#print("bbox arg is required")
			#exit()
			(tl, br) = util.get_rect(im_draw)

		if not quiet:
			print( 'using', tl, br, 'as init bb' )

		CMT.initialise(im_gray0, tl, br)

	elif(frame_counter > frame_init_at):
		im_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		if preview or args.output is not None:
			im_draw = np.copy(frame)

		tic = time.time()
		CMT.process_frame(im_gray)
		toc = time.time()

		# Draw updated estimate
		if CMT.has_result:

			current_tl = int(CMT.tl[0])
			starting_tl = int(tl[0])

			if current_tl < starting_tl-20:
				# move robot left to catch up with object
				# t = threading.Thread(target=motor_speeds_timed, args=(-12, 12))
				# t.start()
				motor_speeds(-12, 12)
			elif current_tl > starting_tl+20:
				motor_speeds(12, -12)
			else:
				motor_speeds(0, 0)



			#print(np.array((CMT.tl, CMT.tr, CMT.br, CMT.bl, CMT.tl)))

			if preview or args.output is not None:
				cv2.line(im_draw, CMT.tl, CMT.tr, (255, 0, 0), 4)
				cv2.line(im_draw, CMT.tr, CMT.br, (255, 0, 0), 4)
				cv2.line(im_draw, CMT.br, CMT.bl, (255, 0, 0), 4)
				cv2.line(im_draw, CMT.bl, CMT.tl, (255, 0, 0), 4)

			if args.output is not None:
				# Original image
				cv2.imwrite('{0}/input_{1:08d}.png'.format(args.output, frame_counter), frame)
				# Output image
				cv2.imwrite('{0}/output_{1:08d}.png'.format(args.output, frame_counter), im_draw)

				# Keypoints
				with open('{0}/keypoints_{1:08d}.csv'.format(args.output, frame_counter), 'w') as f:
					f.write('x y\n')
					np.savetxt(f, CMT.tracked_keypoints[:, :2], fmt='%.2f')

				# Outlier
				with open('{0}/outliers_{1:08d}.csv'.format(args.output, frame_counter), 'w') as f:
					f.write('x y\n')
					np.savetxt(f, CMT.outliers, fmt='%.2f')

				# Votes
				with open('{0}/votes_{1:08d}.csv'.format(args.output, frame_counter), 'w') as f:
					f.write('x y\n')
					np.savetxt(f, CMT.votes, fmt='%.2f')

				# Bounding box
				with open('{0}/bbox_{1:08d}.csv'.format(args.output, frame_counter), 'w') as f:
					f.write('x y\n')
					# Duplicate entry tl is not a mistake, as it is used as a drawing instruction
					np.savetxt(f, np.array((CMT.tl, CMT.tr, CMT.br, CMT.bl, CMT.tl)), fmt='%.2f')



			if preview:

				util.draw_keypoints(CMT.tracked_keypoints, im_draw, (255, 255, 255))
				# this is from simplescale
				util.draw_keypoints(CMT.votes[:, :2], im_draw)  # blue
				util.draw_keypoints(CMT.outliers[:, :2], im_draw, (0, 0, 255))

				# check to see if the frame should be displayed to our screen
				cv2.imshow("Frame", im_draw)
				key = cv2.waitKey(2) & 0xFF

		else:
			motor_speeds(0, 0)


		# Remember image
		#im_prev = im_gray
	else:
		# check to see if the frame should be displayed to our screen
		if preview:
			cv2.imshow("Frame", frame)
			key = cv2.waitKey(1) & 0xFF


motor_speeds(0, 0)

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()
time.sleep(2.0)
ser.close()

