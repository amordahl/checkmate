from checkmate.checkmate.models.Option import Option


def test_add_item():
    k = Option("op1")
    k.add_level(5)
    assert k.get_levels() == {5}


def test_add_items():
    k = Option("op2")
    k.add_level("a")
    k.add_level("b")
    assert k.get_levels() == {"a", "b"}


def test_add_precision():
    k = Option("op3")
    k.add_level("a")
    k.add_level("b")
    k.is_as_precise("a", "b")
    assert k.precision_compare("b", "a") == -1

def test_add_multiple_precision():
    k = Option("op3")
    k.add_level("a")
    k.add_level("b")
    k.add_level("c")
    k.is_as_precise("a", "b")
    k.is_as_precise("b", "c")
    assert k.precision_compare("c", "a") == -1

def test_add_items_same_precision():
    """
    Test that adding items at the same precision level
    appropriately consolidates them into a list.
    """
    k = Option("op4")
    k.add_level("a")
    k.add_level("b")
    k.add_level("c")
    k.add_level("d")
    k.is_as_precise("c", "b")
    k.is_as_precise("a", "b")
    k.is_as_precise("d", "a")
    assert k.precision == ["b", {"c", "a"}, "d"]


def test_more_precise():
    """
    Test that adding items at the same precision level
    appropriately consolidates them into a list.
    """
    k = Option("op4")
    k.add_level("a")
    k.add_level("b")
    k.add_level("c")
    k.add_level("d")
    k.is_as_precise("c", "b")
    k.is_as_precise("a", "b")
    k.is_as_precise("d", "a")
    assert k.more_precise_than("b") == [{"c", "a"}, "d"] and\
        k.more_precise_than("a") == ["d"] and\
        k.more_precise_than("d") == []


def test_numeric_options():
    """
    Test that numeric options are handled correctly.
    """
    k = Option("op5")
    k.add_level(-1)
    k.add_level("k")
    k.add_level("k+1")
    k.is_as_precise("k+1", "k")
    k.is_as_precise(-1, "k+1")
    assert k.precision_compare(6, 7) == -1 and\
        k.precision_compare(-1, 100) == 1 and\
        k.precision_compare(2, 2) == 0

