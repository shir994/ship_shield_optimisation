import sys
sys.path.append("../")

from ship_shield_optimisation.run_ship import SHIPRunner


def test_ship():
    runner = SHIPRunner()
    runner.run_ship()

if __name__ == '__main__':
    test_ship()