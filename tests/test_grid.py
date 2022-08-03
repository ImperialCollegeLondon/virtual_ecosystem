from virtual_rainforest.core.grid import CoreGridConfig


def test_CoreGridConfig():
    obj_1 = CoreGridConfig()
    assert obj_1.grid_type == "square"
    assert obj_1.cell_contiguity == "rook"
    assert obj_1.cell_area == 100
    assert obj_1.cell_nx == 10
    assert obj_1.cell_ny == 10
