"""Small in-memory failure probes for the read-only production collision verifier."""
import copy
import unittest
import xml.etree.ElementTree as ET

import verify_vv_collision_rbxmx as verifier


class CollisionVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ET.parse(verifier.STONE).getroot()
        cls.model = tree.find("./Item")
        cls.shared = {n.get('md5'): ''.join((n.text or '').split()) for n in tree.findall('./SharedStrings/SharedString')}

    def check_model(self, model, expected=118):
        errors, pending = [], []
        verifier.check_model(model, expected, self.shared, set(), errors, pending)
        return errors

    def test_authoritative_count(self):
        self.assertEqual(self.check_model(copy.deepcopy(self.model)), [])

    def test_missing_part(self):
        self.assertTrue(self.check_model(copy.deepcopy(self.model), 119))

    def test_wrong_fidelity(self):
        model=copy.deepcopy(self.model)
        verifier.prop(model.find('.//Item[@class="MeshPart"]'),'token','CollisionFidelity').text='0'
        self.assertTrue(self.check_model(model))

    def test_missing_mesh_id(self):
        model=copy.deepcopy(self.model)
        verifier.prop(model.find('.//Item[@class="MeshPart"]'),'Content','MeshId').find('url').text=''
        self.assertTrue(self.check_model(model))

    def test_nonzero_pivot(self):
        model=copy.deepcopy(self.model)
        verifier.prop(model,'OptionalCoordinateFrame','WorldPivotData').find('CFrame/X').text='4'
        self.assertTrue(self.check_model(model))

    def test_disabled_query(self):
        model=copy.deepcopy(self.model)
        verifier.prop(model.find('.//Item[@class="MeshPart"]'),'bool','CanQuery').text='false'
        self.assertTrue(self.check_model(model))

    def test_duplicate_mesh(self):
        model=copy.deepcopy(self.model)
        parts=model.findall('.//Item[@class="MeshPart"]')
        verifier.prop(parts[1],'Content','MeshId').find('url').text=verifier.prop(parts[0],'Content','MeshId').findtext('url')
        self.assertTrue(self.check_model(model))


if __name__ == '__main__':
    unittest.main()
