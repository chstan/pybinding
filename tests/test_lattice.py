import pytest

import pybinding as pb
from pybinding.repository import graphene
from pybinding.repository import misc

lattices = {
    'square': pb.lattice.square(d=0.2, t=1),
    'graphene-monolayer': graphene.lattice.monolayer(),
    'graphene-monolayer-alt': graphene.lattice.monolayer_alt(),
    'graphene-monolayer-4atom': graphene.lattice.monolayer_4atom(),
    'graphene-monolayer-nn': graphene.lattice.monolayer_nn(),
    'graphene-bilayer': graphene.lattice.bilayer(),
    'mos2': misc.lattice.mos2(),
}


@pytest.fixture(scope='module', ids=list(lattices.keys()), params=lattices.values())
def lattice(request):
    return request.param


@pytest.fixture
def mock_lattice():
    a_cc, a, t = 1, 1.73, 1
    lat = pb.Lattice([a, 0], [0.5 * a, 0.866 * a])
    lat.add_sublattices(
        ['a', (0, -a_cc/2)],
        ['b', (0,  a_cc/2)]
    )
    lat.add_hoppings(
        [(0,  0), 'a', 'b', t],
        [(1, -1), 'a', 'b', t],
        [(0, -1), 'a', 'b', t]
    )
    lat.min_neighbors = 2
    return lat


def test_add_sublattice(mock_lattice):
    with pytest.raises(KeyError) as excinfo:
        mock_lattice.add_one_sublattice('a', (0, 0))
    assert "already exists" in str(excinfo.value)

    with pytest.raises(KeyError) as excinfo:
        assert mock_lattice['c']
    assert "There is no sublattice named 'c'" in str(excinfo.value)

    with pytest.raises(KeyError) as excinfo:
        assert mock_lattice[5]
    assert "There is no sublattice with ID = 5" in str(excinfo.value)

    with pytest.raises(RuntimeError) as excinfo:
        for i in range(127):
            mock_lattice.add_one_sublattice(str(i), (0, 0))
    assert "Cannot create more sublattices" in str(excinfo.value)


def test_add_hopping(mock_lattice):
    with pytest.raises(RuntimeError) as excinfo:
        mock_lattice.add_one_hopping((0,  1), 'a', 'a', 0)
    assert "Hopping energy must not be zero" in str(excinfo.value)

    with pytest.raises(RuntimeError) as excinfo:
        mock_lattice.add_one_hopping((0,  0), 'a', 'b', 1)
    assert "hopping already exists" in str(excinfo.value)

    with pytest.raises(RuntimeError) as excinfo:
        mock_lattice.add_one_hopping((0, 0), 'a', 'a', 1)
    assert "Don't define onsite potential here" in str(excinfo.value)

    with pytest.raises(KeyError) as excinfo:
        mock_lattice.add_one_hopping((0, 0), 'c', 'a', 1)
    assert "There is no sublattice named 'c'" in str(excinfo.value)

    mock_lattice.register_hopping_energies({
        't_nn': 0.1,
        't_nnn': 0.01
    })
    mock_lattice.add_one_hopping((0, 1), 'a', 'a', 't_nn')

    with pytest.raises(KeyError) as excinfo:
        mock_lattice.register_hopping_energies({'t_nn': 0.2})
    assert "already exists" in str(excinfo.value)

    with pytest.raises(KeyError) as excinfo:
        mock_lattice.add_one_hopping((0, 1), 'a', 'a', 'tt')
    assert "There is no hopping named 'tt'" in str(excinfo.value)

    with pytest.raises(RuntimeError) as excinfo:
        for i in range(1, 128):
            mock_lattice.add_one_hopping((0, i), 'a', 'b', i)
    assert "Can't create any more hoppings" in str(excinfo.value)


def test_pickle_round_trip(lattice, tmpdir):
    file_name = str(tmpdir.join('file.npz'))
    lattice.save(file_name)
    from_file = pb.Lattice.from_file(file_name)

    assert pytest.fuzzy_equal(lattice, from_file)


def test_expected(lattice, baseline, plot):
    expected = baseline(lattice)
    plot(lattice, expected, 'plot')
    assert pytest.fuzzy_equal(lattice, expected)


def test_make_lattice():
    a, t = 1, 1

    lat1 = pb.Lattice([a, 0], [0, a])
    lat1.add_one_sublattice('s', (0, 0))
    lat1.add_hoppings([(0,  1), 's', 's', t],
                      [(1,  0), 's', 's', t])
    lat1.min_neighbors = 2

    lat2 = pb.make_lattice(
        vectors=[[a, 0], [0, a]],
        sublattices=[['s', (0, 0)]],
        hoppings=[[(0, 1), 's', 's', t],
                  [(1, 0), 's', 's', t]],
        min_neighbors=2
    )

    assert pytest.fuzzy_equal(lat1, lat2)
