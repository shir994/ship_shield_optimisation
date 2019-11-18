#!/usr/bin/env python
# -*- coding: utf-8 -*-
from control import config
from flask import Flask
from flask import request as flask_request
from threading import Thread
from control import run_job
import json
import uuid


app = Flask(__name__)


@app.route('/simulate', methods=['POST'])
def simulate():
    parameters = json.loads(flask_request.data)
    magnet_config = parameters["shape"]
    requested_num_events = parameters["n_events"]
    requested_num_events = min(requested_num_events, config.EVENTS_TOTAL)
    job_uuid: str = str(uuid.uuid4())

    n_events_per_job = requested_num_events // config.N_JOBS
    for job_id in range(config.N_JOBS):
        first_event = n_events_per_job * job_id
        if job_id + 1 == config.N_JOBS:
            n_events_per_job += requested_num_events % config.N_JOBS

        Thread(target=run_job.run_simulation, kwargs=dict(magnet_config=magnet_config,
                                                          job_uuid=job_uuid,
                                                          n_events=n_events_per_job,
                                                          first_event=first_event)).start()
    return job_uuid


# TODO: lazy evaluation
@app.route('/retrieve_result', methods=['POST'])
def retrieve_result():
    data = json.loads(flask_request.data)
    result = run_job.get_result(data['uuid'])
    # if result is None
    # that there are two possible situations
    # calculation is not finished yet
    # or no key!
    return result


@app.route('/retrieve_params', methods=['POST'])
def retrieve_params():
    data = json.loads(flask_request.data)
    result = run_job.retrieve_params(data["shape"])
    return result


def main():
    app.run(host=config.HOST, port=config.PORT)


if __name__ == "__main__":
    main()
