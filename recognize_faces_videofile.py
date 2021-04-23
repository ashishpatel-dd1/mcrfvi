# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 11:51:46 2021

@author: Ashish
"""
# python recognize_faces_videofile.py -e encodings.pickle -i input/friends_s01e01.mkv -o output/ex1_2.mp4 -y 0

import argparse
import pickle

from cv2 import cv2
import imutils
import progressbar

import constants
from face_recog_techniques import FaceRec

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-e", "--encodings", required=True,
                help="path to serialized db of facial encodings")
ap.add_argument("-i", "--input", required=True,
                help="path to the input vide file")
ap.add_argument("-o", "--output", type=str,
                help="path to output video")
ap.add_argument("-y", "--display", type=int, default=1,
                help="whether or not to display output frame to screen")
ap.add_argument("-d", "--detection-method", type=str, default="cnn",
                help="face detection model to use: either `hog` or `cnn`")
ap.add_argument("-fnn", "--fast-nn", action="store_true")
args = vars(ap.parse_args())
print(args) 

# load the known faces and embeddings
print("[INFO] loading encodings...")
data = pickle.loads(open(args["encodings"], "rb").read())

# initialize the video stream and pointer to output video file, then
# allow the camera sensor to warm up
print("Processing Video")
vs = cv2.VideoCapture(args["input"])
writer = None

# set up progress bar
bar = progressbar.ProgressBar(maxval=int(vs.get(cv2.CAP_PROP_FRAME_COUNT)),
                              widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
i = 0
bar.start()

faceRec = FaceRec()

# loop over frames from the video file stream
while True:

    # update progress bar
    bar.update(i)
    i += 1

    # grab the frame from the threaded video stream
    (grabbed, frame) = vs.read()

    # If frame wasn't grabbed, we've reached the end
    if not grabbed:
        break

    # convert the input frame from BGR to RGB then resize it to have
    # a width of 750px (to speedup processing)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image_rgb_resized = imutils.resize(frame, width=750)
    r = frame.shape[1] / float(image_rgb_resized.shape[1])

    # based on user args select fast kdtree based nn or linear search
    names, boxes = faceRec.getAllFacesInImage(image_rgb_resized, args["detection_method"], args["fast_nn"],
                                              data[constants.KNOWN_ENCODINGS], data[constants.ENCODING_STRUCTURE],
                                              data[constants.KNOWN_NAMES])

    # loop over the recognized faces
    for ((top, right, bottom, left), name) in zip(boxes, names):
        # rescale the face coordinates
        top = int(top * r)
        right = int(right * r)
        bottom = int(bottom * r)
        left = int(left * r)

        # draw the predicted face name on the image
        cv2.rectangle(frame, (left, top), (right, bottom),
                      (0, 255, 0), 2)
        y = top - 15 if top - 15 > 15 else top + 15
        cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
                    0.75, (0, 255, 0), 2)

    # if the video writer is None *AND* we are supposed to write
    # the output video to disk initialize the writer
    if writer is None and args["output"] is not None:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(args["output"], fourcc, 20,
                                 (frame.shape[1], frame.shape[0]), True)

    # if the writer is not None, write the frame with recognized
    # faces to disk
    if writer is not None:
        writer.write(frame)

    # check to see if we are supposed to display the output frame to
    # the screen
    if args["display"] > 0:
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF

        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break

# Cleanup
vs.release()

# check to see if the video writer point needs to be released
if writer is not None:
    writer.release()
