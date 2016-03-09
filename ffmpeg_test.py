'''
Run this script to ensure that your version of OpenCv is working with ffmpeg
enabled. It should produce a video called 'test.m4v' that is simply a black
screen turning white.
'''
import cv2
import numpy as np

OPENCV3 = (cv2.__version__.split('.')[0] == '3')

def main():
    if OPENCV3:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    else:
        fourcc = cv2.cv.CV_FOURCC(*'mp4v')
    out = cv2.VideoWriter()
    ret = out.open('test.m4v', fourcc,
                   30, (200, 200), True)
    if not ret:
        raise Exception('Unable to write video files')
    img = np.ones((200, 200, 3), dtype=np.uint8)
    for i in range(255):
        out.write(img * i)

if __name__ == '__main__':
    main()