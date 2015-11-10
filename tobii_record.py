'''
    Script to collect data on Tobii Glasses 2

    Based on Tobii SDK
'''

import urllib2
import json
import time
import socket
import sys

GLASSES_IP = "192.168.71.50"  # IPv4 address
PORT = 49152
base_url = 'http://' + GLASSES_IP
timeout = 1


# Create UDP socket
def mksock(peer):
    iptype = socket.AF_INET
    if ':' in peer[0]:
        iptype = socket.AF_INET6
    return socket.socket(iptype, socket.SOCK_DGRAM)


# Callback function
def send_keepalive_msg(socket, msg, peer):
    global running
    while running:
        socket.sendto(msg, peer)
        time.sleep(timeout)


def post_request(api_action, data=None):
    url = base_url + api_action
    req = urllib2.Request(url)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(data)
    response = urllib2.urlopen(req, data)
    data = response.read()
    json_data = json.loads(data)
    return json_data


def get_request(api_action):
    url = base_url + api_action
    req = urllib2.Request(url)
    req.add_header('Content-Type', 'application/json')
    response = urllib2.urlopen(req)
    data = response.read()
    json_data = json.loads(data)
    return json_data


def wait_for_status(api_action, key, values):
    url = base_url + api_action
    running = True
    while running:
        req = urllib2.Request(url)
        req.add_header('Content-Type', 'application/json')
        response = urllib2.urlopen(req, None)
        data = response.read()
        json_data = json.loads(data)
        if json_data[key] in values:
            running = False
        time.sleep(1)

    return json_data[key]


def create_project():
    json_data = post_request('/api/projects')
    return json_data['pr_id']


def create_participant(project_id):
    data = {'pa_project': project_id}
    json_data = post_request('/api/participants', data)
    return json_data['pa_id']


def create_calibration(project_id, participant_id):
    data = {'ca_project': project_id, 'ca_type': 'default',
            'ca_participant': participant_id}
    json_data = post_request('/api/calibrations', data)
    return json_data['ca_id']


def start_calibration(calibration_id):
    post_request('/api/calibrations/' + calibration_id + '/start')


def create_recording(participant_id):
    data = {'rec_participant': participant_id}
    json_data = post_request('/api/recordings', data)
    return json_data['rec_id']


def start_recording(recording_id):
    post_request('/api/recordings/' + recording_id + '/start')


def stop_recording(recording_id):
    post_request('/api/recordings/' + recording_id + '/stop')


if __name__ == "__main__":
    peer = (GLASSES_IP, PORT)

    try:
        project_id = create_project()
        participant_id = create_participant(project_id)
        calibration_id = create_calibration(project_id, participant_id)

        print "Project: " + project_id, ", Participant: ", participant_id, ", Calibration: ", calibration_id, " "

        input_var = raw_input("Press enter to calibrate")
        print ('Calibration started...')
        start_calibration(calibration_id)
        status = wait_for_status(
            '/api/calibrations/' + calibration_id + '/status', 'ca_state', ['failed', 'calibrated'])

        if status == 'failed':
            print ('Calibration failed, quitting')
            sys.exit()
        else:
            print ('Calibration successful')

        recording_id = create_recording(participant_id)
        print ('Recording started...')
        start_recording(recording_id)
        raw_input("Press enter to stop recording")
        stop_recording(recording_id)
        status = wait_for_status('/api/recordings/' + recording_id + '/status',
                                 'rec_state', ['failed', 'done'])
        if status == 'failed':
            print ('Recording failed')
        else:
            print ('Recording successful')
    except:
        raise
