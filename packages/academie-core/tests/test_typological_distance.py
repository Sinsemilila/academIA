from academie_core.pedagogy.typological_distance import get_distance


def test_close_romance_pair():
    assert get_distance("fr", "es") == "close"
    assert get_distance("es", "fr") == "close"  # symmetric
    assert get_distance("IT", "PT") == "close"   # case-insensitive


def test_medium_germanic_romance():
    assert get_distance("fr", "en") == "medium"
    assert get_distance("en", "fr") == "medium"


def test_distant_non_ie():
    assert get_distance("fr", "ja") == "distant"
    assert get_distance("fr", "ru") == "distant"
    assert get_distance("en", "zh") == "distant"


def test_same_language_is_close():
    assert get_distance("fr", "fr") == "close"


def test_unknown_pair_defaults_medium():
    assert get_distance("xx", "yy") == "medium"


def test_empty_inputs_default_medium():
    assert get_distance("", "fr") == "medium"
    assert get_distance("fr", "") == "medium"
