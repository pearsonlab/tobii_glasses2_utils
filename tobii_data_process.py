#!/usr/bin/env python
'''
    Process and sort data from Tobii eye tracker recordings into columnar format
'''

import argparse
import json
import pandas as pd
import numpy as np


def read_data(json_fname):
    df = pd.DataFrame()
    pts_sync = {}
    vts_sync = {}
    with open(json_fname) as f:
        for line in f:
            entry = json.loads(line)
            if 'pts' in entry.keys():
                pts_sync[entry['ts']] = {}
                pts_sync[entry['ts']]['PTS time'] = entry['pts']
                pts_sync[entry['ts']]['Pipeline Version'] = entry['pv']
                pts_sync[entry['ts']]['PTS validity'] = entry['s']
                continue
            elif 'vts' in entry.keys():
                vts_sync[entry['ts']] = {}
                vts_sync[entry['ts']]['VTS time'] = entry['vts']
                vts_sync[entry['ts']]['VTS validity'] = entry['s']
                continue
            if 'eye' in entry.keys():
                which_eye = entry['eye'][:1]
                if 'pc' in entry.keys():
                    df.loc[entry['ts'], 
                        which_eye + '_pup_cent_x'] = entry['pc'][0]
                    df.loc[entry['ts'], 
                        which_eye + '_pup_cent_y'] = entry['pc'][1]
                    df.loc[entry['ts'], 
                        which_eye + '_pup_cent_z'] = entry['pc'][2]
                    df.loc[entry['ts'], 
                        which_eye + '_pup_cent_val'] = entry['s']
                elif 'pd' in entry.keys():
                    df.loc[entry['ts'], 
                        which_eye + '_pup_diam'] = entry['pd']
                    df.loc[entry['ts'], 
                        which_eye + '_pup_diam_val'] = entry['s']
                elif 'gd' in entry.keys():
                    df.loc[entry['ts'], 
                        which_eye + '_gaze_dir_x'] = entry['gd'][0]
                    df.loc[entry['ts'], 
                        which_eye + '_gaze_dir_y'] = entry['gd'][1]
                    df.loc[entry['ts'], 
                        which_eye + '_gaze_dir_z'] = entry['gd'][2]
                    df.loc[entry['ts'], 
                        which_eye + '_gaze_dir_val'] = entry['s']
            else:
                if 'gp' in entry.keys():
                    df.loc[entry['ts'], 'gaze_pos_x'] = entry['gp'][0]
                    df.loc[entry['ts'], 'gaze_pos_y'] = entry['gp'][1]
                    df.loc[entry['ts'], 
                        'gaze_pos_val'] = entry['s']
                elif 'gp3' in entry.keys():
                    df.loc[entry['ts'], 
                        '3d_gaze_pos_x'] = entry['gp3'][0]
                    df.loc[entry['ts'], 
                        '3d_gaze_pos_y'] = entry['gp3'][1]
                    df.loc[entry['ts'], 
                        '3d_gaze_pos_z'] = entry['gp3'][2]
                    df.loc[entry['ts'], 
                        '3d_gaze_pos_val'] = entry['s']

    return df


def cleanseries(data, *args):
    if data.name != 'l_pup_diam' and data.name != 'r_pup_diam':
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
    parser = argparse.ArgumentParser()
    parser.add_argument('tobii_in', help='Location of tobii JSON file to convert')
    parser.add_argument('csv_out', help='Name of csv file to output')
    parser.add_argument('--clean', default=0, help='Flag to clean pupil size data, 1 for linear interpolation,',
                                                   '2 for polynomial interpolation. Default is no cleaning.')
    args = parser.parse_args()

    df = read_data(args.tobii_in)

    if args.clean in (1, 2):
        df = df.reset_index()
        df = df.apply(cleanseries, args=[args.clean])
        df = df.set_index('index', drop=True)
    df = add_seconds(df)

    df.to_csv(args.csv_out + '.csv')
