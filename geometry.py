from array import array
import ROOT as r
import os
from ShipGeoConfig import ConfigRegistry
import shipDet_conf


class GeometryManipulator(object):
    def __init__(self, geometry_dir="shield_files/geometry/"):
        self.geometry_dir = geometry_dir
        self.default_magent_config = (70.0, 170.0, 208.0, 207.0, 281.0, 248.0, 305.0,
        242.0, 40.0, 40.0, 150.0, 150.0, 2.0, 2.0, 80.0, 80.0, 150.0, 150.0, 2.0, 2.0,
        72.0, 51.0, 29.0, 46.0, 10.0, 7.0, 54.0, 38.0, 46.0, 192.0, 14.0, 9.0, 10.0,
        31.0, 35.0, 31.0, 51.0, 11.0, 3.0, 32.0, 54.0, 24.0, 8.0, 8.0, 22.0, 32.0,
        209.0, 35.0, 8.0, 13.0, 33.0, 77.0, 85.0, 241.0, 9.0, 26.0)

    def generate_magnet_geofile(self, geofile, params):
        f = r.TFile.Open(os.path.join(self.geometry_dir, geofile), 'recreate')
        parray = r.TVectorD(len(params), array('d', params))
        parray.Write('params')
        f.Close()
        print('Geofile constructed at ' + os.path.join(self.geometry_dir, geofile))
        return geofile

    def get_magnet_mass(self, muonShield):
        """Calculate magnet weight [kg]
        Assumes magnets contained in `MuonShieldArea` TGeoVolumeAssembly and
        contain `Magn` in their name. Calculation is done analytically by
        the TGeoVolume class.
        """
        nodes = muonShield.GetNodes()
        m = 0.
        for node in nodes:
            volume = node.GetVolume()
            if 'Mag' in volume.GetName():
                m += volume.Weight(0.01, 'a')
        return m

    def get_magnet_length(self, muonShield):
        """Ask TGeoShapeAssembly for magnet length [cm]
        Note: Ignores one of the gaps before or after the magnet
        Also note: TGeoShapeAssembly::GetDZ() returns a half-length
        """
        length = 2 * muonShield.GetShape().GetDZ()
        return length

    def extract_l_and_w(self, magnet_geofile, full_geometry_file):
        ship_geo = ConfigRegistry.loadpy(
            '$FAIRSHIP/geometry/geometry_config.py',
            Yheight=10,
            tankDesign=5,
            muShieldDesign=8,
            muShieldGeo=os.path.join(self.geometry_dir, magnet_geofile))

        print
        'Config created with ' + os.path.join(self.geometry_dir, magnet_geofile)

        outFile = r.TMemFile('output', 'create')
        run = r.FairRunSim()
        run.SetName('TGeant4')
        run.SetOutputFile(outFile)
        run.SetUserConfig('g4Config.C')
        shipDet_conf.configure(run, ship_geo)
        run.Init()
        run.CreateGeometryFile(os.path.join(self.geometry_dir, full_geometry_file))
        sGeo = r.gGeoManager
        muonShield = sGeo.GetVolume('MuonShieldArea')
        L = self.get_magnet_length(muonShield)
        W = self.get_magnet_mass(muonShield)
        g = r.TFile.Open(os.path.join(self.geometry_dir, magnet_geofile), 'read')
        params = g.Get("params")
        f = r.TFile.Open(os.path.join(self.geometry_dir, full_geometry_file), 'update')
        f.cd()
        length = r.TVectorD(1, array('d', [L]))
        length.Write('length')
        weight = r.TVectorD(1, array('d', [W]))
        weight.Write('weight')
        params.Write("params")
        return L, W