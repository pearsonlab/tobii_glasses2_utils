# tobii_glasses2_utils
Various utilities to record and process Tobii Glasses 2 eye-tracking data

Installing Dependencies (that aren't automtically included in the Anaconda Python distribution):

**DO THESE IN ORDER**

1. ffmpeg
    * Can be installed with homebrew on OS X. Just do `brew install ffmpeg`
1. OpenCV
    * Must install the version with ffmpeg enabled, available by simply entering `conda install -c https://conda.anaconda.org/shariqiqbal2810 opencv`
1. Run ffmpeg_test.py in order to ensure that everything installed correctly
    * It should produce a video called 'test.m4v' that is simply a black
screen turning white.

## tobii_data_process.py

We have found that finding discontinuous points in eye tracking data is most effective when using the mean of a window around each point and comparing that value to the point itself. After some testing we decided to set the window size at 10. This value does the best job of removing discontinuous points without removing too much information, as can be seen in the examples below.

<img src="images/org_data.png">

<img src="images/window5.png">

<img src="images/window10.png">