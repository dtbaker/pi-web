# USAGE
# python run.py
# python run.py --preview 1

# import the necessary packages
from __future__ import print_function

import sys
# sys.path.append('/opt/ros/jade/lib/python2.7/dist-packages')

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


import zmq

with open("/var/www/html/running-flag.txt", "a") as logfile:
	logfile.write("start")

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()

ap.add_argument('inputpath', nargs='?', help='The input path.')
ap.add_argument('--challenge', dest='challenge', action='store_true', help='Enter challenge mode.')
ap.add_argument('--preview', dest='preview', action='store_const', const=True, default=None, help='Force preview')
ap.add_argument('--width', dest='width', type=int, default=240, help='Capture width')
ap.add_argument('--height', dest='height', type=int, default=180, help='Capture height')
ap.add_argument('--maxspeed', dest='maxspeed', type=int, default=20, help='Max robot speed')
ap.add_argument('--minspeed', dest='minspeed', type=int, default=11, help='Min robot speed')
ap.add_argument('--objectwidth', dest='objectwidth', type=int, default=10, help='Rough width of initial object in cm')
ap.add_argument('--focallength', dest='focallength', type=float, default=3.6, help='Camera focal length in mm')
ap.add_argument('--no-scale', dest='estimate_scale', action='store_false', help='Disable scale estimation')
ap.add_argument('--with-rotation', dest='estimate_rotation', action='store_true', help='Enable rotation estimation')
ap.add_argument('--bbox', dest='bbox', help='Specify initial bounding box.')
ap.add_argument('--frameimage', dest='frameimage', help='Specify start frame image.')
ap.add_argument('--pause', dest='pause', action='store_true', help='Pause after every frame and wait for any key.')
ap.add_argument('--output-dir', dest='output', help='Specify a directory for output data.')
ap.add_argument('--tracker', dest='tracker', default='CMT', help='Which tracker to use.')
ap.add_argument('--quiet', dest='quiet', action='store_true', help='Do not show graphical output (Useful in combination with --output-dir ).')
ap.add_argument('--skip', dest='skip', action='store', default=None, help='Skip the first n frames', type=int)

ap.add_argument("-n", "--num-frames", type=int, default=100, help="# of frames to loop over for FPS test")

args = ap.parse_args()

preview = args.preview
if preview is None:
	preview = False
quiet = args.quiet
if quiet is None:
	quiet = False


if(args.tracker == 'CMT'):
	CMT = CMT.CMT()
	CMT.estimate_scale = args.estimate_scale
	CMT.estimate_rotation = args.estimate_rotation
else:
	CMT = cv2.Tracker_create(args.tracker)

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

# created a *threaded *video stream, allow the camera sensor to warmup,
# and start the FPS counter
if not quiet:
	print("Starting camera")
vs = PiVideoStream((args.width, args.height)).start()
time.sleep(2.0)

context = zmq.Context()
if not quiet:
	print("Connecting to robot movement server")
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")
socket.send(b"none")
message_reply = socket.recv()

frame_counter = 0
frame_init_at = 20  # start processing once we've read this many frames, as it can take some time to get the cam warmed up
frame_limit = 10000

tl = 0
br = 0

time_start = 0

# read a bunch of frames from the camera to start
while frame_counter < frame_limit and os.path.isfile("/var/www/html/running-flag.txt"):

	# print(time.time())

	frame = vs.read()
	# frame = imutils.resize(frame, width=image_resize)

	frame_counter += 1
	# print("frame " + str(frame_counter))
	if (frame_counter == frame_init_at):
		# Read first frame
		if args.frameimage is not None:
			frame = cv2.imread(args.frameimage)
			frame = imutils.resize(frame, width=args.width)
			with open("log.txt", "a") as logfile:
				logfile.write("Using frame image: " + str(args.frameimage) + "\n")

		if preview:
			cv2.imshow("Frame", frame)
			key = cv2.waitKey(2) & 0xFF

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
			# print("bbox arg is required")
			# exit()
			(tl, br) = util.get_rect(im_draw)

		if not quiet:
			print('using', tl, br, 'as init bb')

		socket.send(b"" + str(tl[0]) + ":" + str(tl[1]) + "|" + str(br[0]) + ":" + str(tl[1]) + "|" + str(br[0]) + ":" + str(br[1]) + "|" + str(tl[0]) + ":" + str(br[1]))
		message_reply = socket.recv()

		tic = time.time()
		if args.tracker == 'CMT':
			CMT.initialise(im_gray0, tl, br)
		else:
			CMT.init(frame, (tl[0], tl[1], br[0] - tl[0], br[1] - tl[1]))
		toc = time.time()

		with open("log.txt", "a") as logfile:
			s = "Tracker Init Time: " + str(args.tracker) + ": " + str(toc - tic)
			if not quiet:
				print(s)
			logfile.write(s + "\n")

		time_start = time.time()


	elif (frame_counter > frame_init_at):
		im_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		if preview or args.output is not None:
			im_draw = np.copy(frame)

		tic = time.time()
		has_result = False
		if args.tracker == 'CMT':
			CMT.process_frame(im_gray)
			if CMT.has_result:
				has_result = True

		else:
			has_result, newbox = CMT.update(frame)
			print(newbox)
		toc = time.time()

		# Draw updated estimate
		if has_result:

			socket.send(b"" + str(CMT.tl[0]) + ":" + str(CMT.tl[1]) + "|" + str(CMT.tr[0]) + ":" + str(CMT.tr[1]) + "|" + str(CMT.br[0]) + ":" + str(CMT.br[1]) + "|" + str(CMT.bl[0]) + ":" + str(CMT.bl[1]))
			message_reply = socket.recv()

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
			socket.send(b"none")
			message_reply = socket.recv()
			if preview:
				if CMT.tracked_keypoints != None:
					util.draw_keypoints(CMT.tracked_keypoints, frame, (255, 255, 255))
				# check to see if the frame should be displayed to our screen
				cv2.imshow("Frame", frame)
				key = cv2.waitKey(2) & 0xFF



	else:
		# check to see if the frame should be displayed to our screen
		if preview:
			cv2.imshow("Frame", frame)
			key = cv2.waitKey(1) & 0xFF


	this_frame_time = time.time()
	if time_start and (frame_counter % 10) == 0:
		fps = frame_counter / (this_frame_time - time_start)
		print("FPS: " + str(fps))

socket.send(b"none")
message_reply = socket.recv()
print(message_reply)

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()
time.sleep(2.0)
print("finished")



