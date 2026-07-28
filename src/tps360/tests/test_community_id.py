from tps360.core.domain.community_id import is_katottg_code, normalize_community_id


def test_normalize_trims_and_lowercases() -> None:
    assert normalize_community_id("  UA48060030000037887 ") == "ua48060030000037887"


def test_valid_katottg_code() -> None:
    assert is_katottg_code("UA48060030000037887")
    assert is_katottg_code("ua48060030000037887")


def test_rejects_non_katottg() -> None:
    assert not is_katottg_code("a29d6fbd-02c3-4d43-a651-7efd6fbd02c3")  # UUID
    assert not is_katottg_code("ua123")  # too short
    assert not is_katottg_code("48060030000037887")  # missing UA prefix
    assert not is_katottg_code("verkhovyna")
