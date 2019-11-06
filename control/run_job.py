# !/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil
import json
import docker
from shutil import copy
import numpy as np
from redis import Redis
import traceback


redis = Redis()
client = docker.from_env()

DOCKER_ABS_PATH_AT_HOST = "/"

def create_job(command, container_id):
    container = client.containers.run(
        image=str(container_id),
        detach=True,
        command=command,
        #volumes={host_dir: {'bind': container_dir, 'mode': 'rw'}}
        volumes = {
            os.path.join(DOCKER_ABS_PATH_AT_HOST, "muon_samples"): {"bind": "/ship/muon_input", "mode": "rw"},
            os.path.join(DOCKER_ABS_PATH_AT_HOST, "shield_files"): {"bind": "/ship/shield_files", "mode": "rw"},
        }
    )
    return container

def create_container(dockerfile_folder="./ship"):
    image, _ = client.images.build(path=dockerfile_folder)
    return image.id


def run_simulation(magnet_config, job_uuid):
    ##
    N_EVENTS = 100
    FIRST_EVENT = 0

    # make random directory for ship docker
    # to store input files and output files
    # input_dir = 'input_dir_{}'.format(job_uuid)
    # host_dir = '{}/{}'.format(config.CONTAINER_DIRECTORY, input_dir)
    # host_dir = os.path.abspath(host_dir)
    # host_outer_dir = '{}/{}'.format(config.HOST_DIRECTORY, input_dir)
    # os.mkdir(host_dir)


    # copy preprocessing file to destination
    # copy('./preprocess_root_file.py', host_dir)

    # set container dir
    # container_dir = '/root/host_directory'

    print(magnet_config)
    command = "alienv setenv -w /sw FairShip/latest -c " \
              "/ship/run_simulation.sh {} {} {}".\
              format(",".join(map(str, magnet_config)), N_EVENTS, FIRST_EVENT)
    result = {
        'uuid': None,
        'container_id': None,
        'container_status': 'starting',
        'message': None
    }
    redis.set(job_uuid, json.dumps(result))

    image_id = create_container()
    print("image created")
    container = create_job(command=command, container_id=image_id)
    print("job started")
    result = {
        'uuid': job_uuid,
        'container_id': container.id,
        'container_status': container.status,
        'message': None
    }
    redis.set(job_uuid, json.dumps(result))
    try:
        container.wait()
        print(container.logs())

        container.reload()
        with open(os.path.join("/shield_files/outputs/", "optimise_input.json"), "r") as f:
            optimise_input = json.load(f)
        print(optimise_input)
        result = {
            'uuid': job_uuid,
            'container_id': container.id,
            'container_status': container.status,
            'optimise_input': optimise_input,
            'message': None
        }
        redis.set(job_uuid, json.dumps(result))
    except Exception as e:
        container.reload()
        result = {
            'uuid': job_uuid,
            'container_id': container.id,
            'container_status': "failed",
            'muons_momentum': None,
            'message': traceback.format_exc()
        }
        redis.set(job_uuid, json.dumps(result))
    # shutil.rmtree(host_dir)
    return result


def get_result(job_uuid):
    result = redis.get(job_uuid)
    if result is None:
        return {
            'uuid': None,
            'container_id': None,
            'container_status': 'failed',
            'muons_momentum': None,
            'veto_points': None
        }
    result = json.loads(result)
    return result