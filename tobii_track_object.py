#!/usr/bin/env python
"""
This script will track gaze points over a static image, based on gaze data and
scene camera video from a glasses recording.
"""
import argparse
import cv2
import numpy as np
import pandas as pd
import sys
import os

OPENCV3 = (cv2.__version__.split('.')[0] == '3')


def object_find(match_sift, frame, MIN_MATCH_COUNT):
    '''
    Finds an object (from precomputed sift features) within a frame.  If
    found it returns the transformation matrix from frame to still.

    This code is based on the OpenCV feature detection tutorial
    '''
    if OPENCV3:
        sift = cv2.xfeatures2d.SIFT_create()
    else:
        sift = cv2.SIFT()
    kp1, des1 = match_sift
    kp2, des2 = sift.detectAndCompute(frame, None)

    FLANN_INDEX_KDTREE = 0
    num_matches = 2
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    if len(kp1) >= num_matches and len(kp2) >= num_matches:
        matches = flann.knnMatch(des1, des2, k=num_matches)
    else:
        return None

    good = []
    for m, n in matches:
        if m.distance < 0.7*n.distance:
            good.append(m)

    if len(good) > MIN_MATCH_COUNT:
        src_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)

        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

        return M

    else:
        return None


def track_objects(vid_path, gaze, matches, verbose=True):
    """
    Tracks gaze over matches using sift feature matching in openCV.
    Saves a video of gaze plotted over each match as well as a .npy
    file of gaze coordinates in each match image's coordinates
    """
    if verbose:
        print "Tracking gaze over match images..."
        sys.stdout.write('  0.00%')

    gaze = pd.read_csv(gaze)
    gaze = gaze[~gaze.vts_time.isnull()]  # only start tracking eyes once video starts

    matches = [{'path': m} for m in matches]

    vid = cv2.VideoCapture(vid_path)

    if OPENCV3:
        sift = cv2.xfeatures2d.SIFT_create()
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        tot = vid.get(cv2.CAP_PROP_FRAME_COUNT)*2.0
        fps = vid.get(cv2.CAP_PROP_FPS)*2
    else:
        sift = cv2.SIFT()
        fourcc = cv2.cv.CV_FOURCC(*'mp4v')
        tot = vid.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)*2.0
        fps = vid.get(cv2.cv.CV_CAP_PROP_FPS)*2

    ind = 1

    # get gaze values
    gaze_val = gaze['gaze_pos_val'].values
    gaze_x = gaze['gaze_pos_x'].values
    gaze_y = gaze['gaze_pos_y'].values
    vts = gaze['vts_time'].values / 1000.

    # setup sift features and output for each match
    for i in range(len(matches)):
        matches[i]['name'] = os.path.basename(matches[i]['path']).split('.')[0]
        outfile = vid_path.split('.mp4')[0] + '_match_%s.m4v' % matches[i]['name']
        matches[i]['img'] = cv2.imread(matches[i]['path'])
        matches[i]['sift'] = sift.detectAndCompute(cv2.cvtColor(
                                                   matches[i]['img'],
                                                   cv2.COLOR_BGR2GRAY), None)
        matches[i]['size'] = (matches[i]['img'].shape[1],
                              matches[i]['img'].shape[0])
        matches[i]['video'] = cv2.VideoWriter()
        matches[i]['video'].open(outfile, fourcc,
                                 fps,
                                 matches[i]['size'], True)
        # x, y pairs of gaze locations over object. Init as -1
        matches[i]['obj_gaze'] = np.ones((len(gaze_x), 2)) * -1

    while vid.isOpened():
        if OPENCV3:
            vid_time = vid.get(cv2.CAP_PROP_POS_MSEC)
        else:
            vid_time = vid.get(cv2.cv.CV_CAP_PROP_POS_MSEC)
        ret, frame = vid.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            for i in range(len(matches)):
                matches[i]['M'] = object_find(matches[i]['sift'], frame, 50)
            while vts[ind] < vid_time:
                if gaze_val[ind] == 0:  # if gaze point is valid
                    org_pos = np.array((1920*gaze_x[ind], 1080*gaze_y[ind])).reshape(-1, 1, 2)
                    for match in matches:
                        img_cp = match['img'].copy()
                        if match['M'] is not None:
                            trans_pos = cv2.perspectiveTransform(org_pos, match['M'])
                            trans_pos = tuple(np.int32(trans_pos[0, 0]))
                            if (trans_pos[0] <= match['size'][0] and trans_pos[0] >= 0 and
                                    trans_pos[1] <= match['size'][1] and trans_pos[1] >= 0):
                                cv2.circle(img_cp, trans_pos, 8, [255, 0, 0], -2)  # draw blue circle on current frame
                                cv2.circle(match['img'], trans_pos, 8, [0, 255, 0], 2)  # draw green circle as trace
                            match['obj_gaze'][ind, :] = trans_pos
                        match['video'].write(img_cp)
                ind += 1
                if ind % 10 == 0 and verbose:
                    sys.stdout.write('\r' + '%6.2f%%' % ((ind/tot)*100))
                    sys.stdout.flush()

    vid.release()
    for i in range(len(matches)):
        obj_gaze_path = vid_path.split('.mp4')[0] + '_match_%s.npy' % matches[i]['name']
        matches[i]['video'].release()  # save video
        np.save(obj_gaze_path, matches[i]['obj_gaze'])  # save gaze points

    if verbose:
        print
        print "Done!"


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'video', help='Tobii scene camera video')
    parser.add_argument(
        'data', help='Tobii gaze data (converted to csv by tobii_data_process')
    parser.add_argument(
        '-m', '--match', nargs='+',
        help='REQUIRED: Image(s) to find in the video', required=True)
    args = parser.parse_args()

    track_objects(args.video, args.data, args.match)
