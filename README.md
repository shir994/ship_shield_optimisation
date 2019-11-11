This repository contains code for running SHiP simulation service via Flaks. The Dokckerfile in the main folder is to 
build Flask service container. After that, the service is started as follows:
```
docker run -d --rm \
-v "/$(pwd)/ship_shield_optimisation:/ship_shield_optimisation" \
-v "/$(pwd)/muon_samples:/muon_input:rw" \
-v "/$(pwd)/shield_files:/shield_files:rw" \
-v /var/run/docker.sock:/var/run/docker.sock \
-v /mnt/shirobokov/temp:/temp/ \
-p 5432:5432 -it ship_test:1 \
/bin/bash -c "(nohup redis-server & ); (uwsgi --ini control/app.ini)"
```

The config file contains the parameters of the service and SHiP simulation. 
After the service is running, one can start submitting jobs using this repo ([link](https://github.com/SchattenGenie/diff-surrogate/)) as follows:

```
nohup python end_to_end.py --model GANModel --optimizer TorchOptimizer --optimized_function FullSHiPModel \
--project_name full_ship  --work_space shir994 --tags test --epochs 300 --n_samples 42 --n_samples_per_dim 50000 \
--init_psi  "208.0, 207.0, 281.0, 248.0, 305.0, 242.0, 72.0, 51.0, 29.0, 46.0, 10.0, 7.0, 54.0, 38.0, 46.0, 192.0, 14.0, 9.0, 10.0, 31.0, 35.0, 31.0, 51.0, 11.0, 3.0, 32.0, 54.0, 24.0, 8.0, 8.0, 22.0, 32.0, 209.0, 35.0, 8.0, 13.0, 33.0, 77.0, 85.0, 241.0, 9.0, 26.0" \
--reuse_optimizer True --step_data_gen 1 --lr 0.1 &
```
