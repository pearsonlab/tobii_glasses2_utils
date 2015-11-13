#!/usr/bin/env python
'''
    Add gaze data (processed by tobii_data_process) to scene camera video
    from Tobii Glasses 2.
'''
import argparse
import cv2
import pandas as pd


def process(gaze_file, infile, outfile):
    gaze = pd.read_csv(gaze_file)
    # only start tracking eyes once video starts
    gaze = gaze[~gaze.vts_time.isnull()]

    vid = cv2.VideoCapture(infile)

    size = (1920, 1080)
    fourcc = cv2.cv.CV_FOURCC(*'mp4v')
    out = cv2.VideoWriter()
    out.open(outfile + '.m4v', fourcc,
             vid.get(cv2.cv.CV_CAP_PROP_FPS) * 2, size, True)
    # note doubled framerate b/c eye tracking is at double the sampling rate
    # of video

    tot_frames = vid.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)

    i = 0
    gaze_val = gaze['gaze_pos_val'].values
    gaze_x = gaze['gaze_pos_x'].values
    gaze_y = gaze['gaze_pos_y'].values
    vts = gaze['vts_time'].values / 1000.

    print "Adding gaze..."
    while(vid.isOpened()):
        frame_num = vid.get(cv2.cv.CV_CAP_PROP_POS_FRAMES) + 1
        vid_time = vid.get(cv2.cv.CV_CAP_PROP_POS_MSEC)
        prog_ratio = (frame_num * 1.0 / tot_frames)
        print ('[' + int(prog_ratio * 50) * '=' + int((1 - prog_ratio) * 50) * '-' + ']'
               ' %.1f %% Complete\r' % (prog_ratio * 100)),

        ret, frame = vid.read()
        if ret:
            while vts[i] < vid_time:
                frame_cp = frame.copy()
                if gaze_val[i] == 0:
                    gp_x = gaze_x[i]
                    gp_y = gaze_y[i]
                    cv2.circle(
                        frame_cp, (int(1920 * gp_x), int(1080 * gp_y)),
                        8, [255, 0, 0], -2)
                out.write(frame_cp)
                i += 1
        else:
            break

    print
    vid.release()
    out.release()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('video', help='Location of Tobii video file')
    parser.add_argument('data', help='Location of gaze data csv file')
    parser.add_argument('out_video', help='Name of output video with gaze')
    args = parser.parse_args()

    process(args.data, args.video, args.out_video)
    print "Done!"
