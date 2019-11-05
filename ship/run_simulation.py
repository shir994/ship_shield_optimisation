import click
import pickle
import numpy as np
import os
from run_ship import SHIPRunner
from geometry import GeometryManipulator
from utils import process_file


@click.command()
@click.option('--shield_params', type=str, default="")
@click.option('--n_events', type=int, default=1000)
@click.option('--first_event', type=int, default=0)
def main(shield_params=None):
    """
    Gets vector of optimised shield parameters(not full one), run SHiP simulation
    saves dict of magnet length, weight, optimised_paramteters, input kinematics and output hit distribution
    :return:
    """
    shield_params = np.array([float(x.strip()) for x in shield_params.split(',')], dtype=float)
    gm = GeometryManipulator()

    geofile = gm.generate_magnet_geofile("magnet_geo.root", list(gm.input_fixed_params(shield_params)))

    ship_runner = SHIPRunner(geofile)
    # Idealy, here we split the job between N nodes and the join them
    fair_runner = ship_runner.run_ship(n_events=n_events, first_event=first_event)

    l, w, tracker_ends = gm.extract_l_and_w(geofile, "full_ship_geofile.root", fair_runner)
    muons_stats = process_file(ship_runner.output_file, tracker_ends)

    returned_params = {
        "l": l,
        "w": w,
        "params": shield_params,
        "kinematic": muons_stats
    }

    with open(os.path.join(ship_runner.output_dir, "optimise_input.pkl"), "wb") as f:
        pickle.dump(returned_params, f)



if __name__ == '__main__':
    main()