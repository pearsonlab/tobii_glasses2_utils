'''
Run this script to ensure that your version of OpenCv is working with ffmpeg
enabled. It should produce a video called 'test.m4v' that is simply a black
screen turning white.
'''
import cv2
import numpy as np

def main():
    fourcc = cv2.cv.CV_FOURCC(*'mp4v')
    out = cv2.VideoWriter()
    out.open('test.m4v', fourcc,
             30, (200, 200), True)
    img = np.ones((200, 200, 3), dtype=np.uint8)
    for i in range(255):
        out.write(img * i)

if __name__ == '__main__':
    main()