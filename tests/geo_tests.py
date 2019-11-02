import sys
sys.path.append("../")

from ship_shield_optimisation.geometry import GeometryManipulator

def test_geo():
    gm = GeometryManipulator()
    geofile = gm.generate_magnet_geofile("test_geo.root", gm.default_magent_config)
    l, w = gm.extract_l_and_w(geofile, "full_ship_geo_test.root")
    print("L={} cm, W={} kg".format(l, w))


if __name__ == '__main__':
    test_geo()