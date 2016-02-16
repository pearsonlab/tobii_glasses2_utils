# tobii_glasses2_utils
Various utilities to record and process Tobii Glasses 2 eye-tracking data

Dependencies (that aren't automtically included in the Anaconda Python distribution):

**INSTALL THESE IN ORDER**

1. ffmpeg
    * Can be installed with homebrew on OS X. Just do `brew install ffmpeg`
1. OpenCV
    * Must install the version with ffmpeg enabled, available by simply entering `conda install -c https://conda.anaconda.org/shariqiqbal2810 opencv`

## tobii_data_process.py

We have found that finding discontinuous points in eye tracking data is most effective when using the mean of a window around each point and comparing that value to the point itself. After some testing we decided to set the window size at 10. This value does the best job of removing discontinuous points without removing too much information, as can be seen in the examples below.

<img src="images/org_data.png">

<img src="images/window5.png">

<img src="images/window10.png">