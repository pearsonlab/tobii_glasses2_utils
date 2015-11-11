#!/usr/bin/env python
'''
    Process and sort data from Tobii eye tracker recordings into columnar format
'''

import json
import cPickle
import pandas as pd
import numpy as np


def read_data(json_data):
    organized_data = {}
    pts_time_sync_data = {}
    vts_time_sync_data = {}
    for entry in json_data:
        if 'pts' in entry.keys():
            pts_time_sync_data[entry['ts']] = {}
            pts_time_sync_data[entry['ts']]['PTS time'] = entry['pts']
            pts_time_sync_data[entry['ts']]['Pipeline Version'] = entry['pv']
            pts_time_sync_data[entry['ts']]['PTS validity'] = entry['s']
            continue
        elif 'vts' in entry.keys():
            vts_time_sync_data[entry['ts']] = {}
            vts_time_sync_data[entry['ts']]['VTS time'] = entry['vts']
            vts_time_sync_data[entry['ts']]['VTS validity'] = entry['s']
            continue
        elif entry['ts'] not in organized_data.keys():
            organized_data[entry['ts']] = {}
        if 'eye' in entry.keys():
            which_eye = entry['eye']
            if 'pc' in entry.keys():
                organized_data[entry['ts']][
                    which_eye + ' pupil center x'] = entry['pc'][0]
                organized_data[entry['ts']][
                    which_eye + ' pupil center y'] = entry['pc'][1]
                organized_data[entry['ts']][
                    which_eye + ' pupil center z'] = entry['pc'][2]
                organized_data[entry['ts']][
                    which_eye + ' pupil center validity'] = entry['s']
            elif 'pd' in entry.keys():
                organized_data[entry['ts']][
                    which_eye + ' pupil diameter'] = entry['pd']
                organized_data[entry['ts']][
                    which_eye + ' pupil diameter validity'] = entry['s']
            elif 'gd' in entry.keys():
                organized_data[entry['ts']][
                    which_eye + ' gaze direction x'] = entry['gd'][0]
                organized_data[entry['ts']][
                    which_eye + ' gaze direction y'] = entry['gd'][1]
                organized_data[entry['ts']][
                    which_eye + ' gaze direction z'] = entry['gd'][2]
                organized_data[entry['ts']][
                    which_eye + ' gaze direction validity'] = entry['s']
        else:
            if 'gp' in entry.keys():
                organized_data[entry['ts']]['gaze position x'] = entry['gp'][0]
                organized_data[entry['ts']]['gaze position y'] = entry['gp'][1]
                organized_data[entry['ts']][
                    'gaze position validity'] = entry['s']
            elif 'gp3' in entry.keys():
                organized_data[entry['ts']][
                    '3d gaze position x'] = entry['gp3'][0]
                organized_data[entry['ts']][
                    '3d gaze position y'] = entry['gp3'][1]
                organized_data[entry['ts']][
                    '3d gaze position z'] = entry['gp3'][2]
                organized_data[entry['ts']][
                    '3d gaze position validity'] = entry['s']

    return organized_data, pts_time_sync_data, vts_time_sync_data


def cleanseries(data, *args):
    if data.name == 'index':
        return data
    bad = (data == 0)

    dd = data.diff()
    sig = np.median(np.absolute(dd) / 0.67449)
    th = 5
    disc = np.absolute(dd) > th * sig

    to_remove = np.nonzero(bad | disc)[0]
    up_one = range(len(to_remove))
    for i in range(len(to_remove)):
        up_one[i] = to_remove[i] + 1
    down_one = range(len(to_remove))
    for i in range(len(to_remove)):
        down_one[i] = to_remove[i] - 1
    isolated = np.intersect1d(up_one, down_one)

    allbad = np.union1d(to_remove, isolated)

    newdat = pd.Series(data)
    newdat[allbad] = np.nan

    goodinds = np.nonzero(np.invert(np.isnan(newdat)))[0]
    if len(goodinds) == 0:
        print "Not enough good data to clean. Aborting."
        return data
    else:
        if interp_type == 1:
            return pd.Series.interpolate(newdat, method='linear')
        elif interp_type == 2:
            return pd.Series.interpolate(newdat, method='polynomial', order=3)


# adds 'seconds' column that converts tobii timestamps to seconds
def add_seconds(df):
    sample_rate = 30.0
    df = df.reset_index()
    df['seconds'] = (df['index'] - df['index'][0]) / 1000000.0
    df = df.set_index('index', drop=True)
    return df

if __name__ == "__main__":
    datafile_name = str(raw_input("Please enter the name of the data file\n"))
    # datafile_name = 'test1data.json' # test data
    json_data = []  # creates array to hold dicts from json data

    # opens json file and stores each line (dict) in an array: json_data
    with open(str(datafile_name)) as json_data_file:
        for line in json_data_file:
            json_data.append(json.loads(''.join(line)))

    organized_data, pts_time_sync_data, vts_time_sync_data = read_data(
        json_data)
    # output = open('organized_test1data.pkl', 'wb')
    # cPickle.dump(organized_data, output)
    # cPickle.dump(vts_time_sync_data, output)
    # cPickle.dump(pts_time_sync_data, output)

    df = pd.DataFrame.from_dict(organized_data, orient='index')
    should_clean = str(raw_input("Would you like to clean the data? (y/n): "))
    if should_clean == 'y':
        interp_type = int(
            raw_input("Linear (1) or Polynomial (2) interpolation? "))
        df = df.reset_index()
        df = df.apply(cleanseries, args=[interp_type])
        df = df.set_index('index', drop=True)
    df = add_seconds(df)
    csv_name = str(raw_input("Please enter the desired .csv file name\n"))
    df.to_csv(csv_name + '.csv')

    df = pd.DataFrame.from_dict(vts_time_sync_data, orient='index')
    df.to_csv(csv_name + '_video_sync.csv')
