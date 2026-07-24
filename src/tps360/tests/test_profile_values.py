import pytest

from tps360.community_profile.value_objects import (
    Capacity,
    ContactReference,
    DataQuality,
    PopulationCount,
    ProfileVersion,
)


@pytest.mark.parametrize("v", [(0, 0, 0), (1, 2, 3)])
def test_version(v):
    assert str(ProfileVersion(*v)) == ".".join(map(str, v))


def test_next():
    assert (
        str(ProfileVersion(1, 2, 3).next_minor()) == "1.3.0"
        and str(ProfileVersion(1, 2, 3).next_patch()) == "1.2.4"
    )


@pytest.mark.parametrize("v", [-1, -2])
def test_version_bad(v):
    with pytest.raises(ValueError):
        ProfileVersion(v)


@pytest.mark.parametrize("v", [0, 1])
def test_population(v):
    assert PopulationCount(v).value == v


def test_population_bad():
    with pytest.raises(ValueError):
        PopulationCount(-1)


def test_capacity():
    assert Capacity(0, "people").unit == "people"


@pytest.mark.parametrize("v,u", [(-1, "x"), (1, "")])
def test_capacity_bad(v, u):
    with pytest.raises(ValueError):
        Capacity(v, u)


@pytest.mark.parametrize("text", ["a@b.com", "+380 67 123 4567"])
def test_contact_bad(text):
    with pytest.raises(ValueError):
        ContactReference(text, "label", "restricted")


def test_contact():
    assert ContactReference("secret:1", "label", "restricted").reference_id == "secret:1"


@pytest.mark.parametrize("v", [0, 100])
def test_quality_bounds(v):
    assert DataQuality(v, v, v, "high").freshness_score == v


@pytest.mark.parametrize("v", [-1, 101])
def test_quality_bad(v):
    with pytest.raises(ValueError):
        DataQuality(v, 0, 0, "low")
