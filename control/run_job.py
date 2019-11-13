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
from control import config
import tarfile
import uuid
from time import time

redis = Redis()
client = docker.from_env()


def create_job(command, container_id):
    container = client.containers.run(
        image=str(container_id),
        detach=True,
        auto_remove=False,
        command=command,
        #volumes={host_dir: {'bind': container_dir, 'mode': 'rw'}}
        volumes = {
            os.path.join(config.DOCKER_ABS_PATH_AT_HOST, "muon_samples"): {"bind": "/ship/muon_input", "mode": "rw"},
            # os.path.join(DOCKER_ABS_PATH_AT_HOST, "shield_files"): {"bind": "/ship/shield_files", "mode": "rw"},
        }
    )
    return container


def create_container(dockerfile_folder="./ship"):
    image, _ = client.images.build(path=dockerfile_folder)
    return image.id


def extract_file_from_container(container, path, local_filename, remote_full_path):
    f = open(os.path.join(path, local_filename + '.tar'), 'wb')
    bits, stat = container.get_archive(remote_full_path)
    for chunk in bits:
        f.write(chunk)
    f.close()
    tar = tarfile.open(os.path.join(path, local_filename + '.tar'))
    for member in tar.getmembers():
        f = tar.extractfile(member)
        content = f.read()
    return content.decode()


def run_simulation(magnet_config, job_uuid, n_events, first_event):
    # make random directory for ship docker
    # to store input files and output files
    input_dir = 'input_dir_{}_{}'.format(job_uuid, first_event)
    host_dir = '{}/{}'.format(config.CONTAINER_DIRECTORY, input_dir)
    host_dir = os.path.abspath(host_dir)
    os.mkdir(host_dir)

    command = "alienv setenv -w /sw FairShip/latest -c " \
              "/ship/run_simulation.sh {} {} {}".\
              format(",".join(map(str, magnet_config)), n_events, first_event)
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
    start_time = time()
    result = {
        'uuid': job_uuid,
        'container_id': container.id,
        'container_status': container.status,
        'message': None
    }
    redis.set(job_uuid, json.dumps(result))
    try:
        container.wait()
        print(container.logs().decode())
        print("job running time: {0:.2f} s".format(time() - start_time))
        container.reload()
        optimise_input = json.loads(extract_file_from_container(container, host_dir,
                                                                "optimise_input",
                                                                "/ship/shield_files/outputs/optimise_input.json"))

        result = {
            'uuid': job_uuid,
            'container_id': container.id,
            'container_status': container.status,
            'kinematics': optimise_input["kinematics"],
            "params": optimise_input["params"],
            "veto_points": optimise_input["veto_points"],
            "l": optimise_input["l"],
            "w": optimise_input["w"],
            'message': None
        }
        redis.set(job_uuid, json.dumps(result))
    except Exception as e:
        print(e)
        container.reload()
        result = {
            'uuid': job_uuid,
            'container_id': container.id,
            'container_status': "failed",
            'message': traceback.format_exc()
        }
        redis.set(job_uuid, json.dumps(result))
    shutil.rmtree(host_dir)
    return result


def retrieve_params(magnet_config):
    input_dir = 'input_dir_{}'.format(str(uuid.uuid4()))
    host_dir = '{}/{}'.format(config.CONTAINER_DIRECTORY, input_dir)
    host_dir = os.path.abspath(host_dir)
    os.mkdir(host_dir)

    image_id = create_container()
    command = "alienv setenv -w /sw FairShip/latest -c " \
              "/ship/get_params.sh {}".\
              format(",".join(map(str, magnet_config)))
    container = create_job(command=command, container_id=image_id)
    print("job started")
    container.wait()
    print(container.logs().decode())
    container.reload()
    params = json.loads(extract_file_from_container(container, host_dir,
                                                    "query_params",
                                                    "/ship/shield_files/outputs/query_params.json"))
    shutil.rmtree(host_dir)
    return params


def get_result(job_uuid):
    result = redis.get(job_uuid)
    if result is None:
        return {
            'uuid': None,
            'container_id': None,
            'container_status': 'failed',
            'message': None
        }
    result = json.loads(result)
    return result
