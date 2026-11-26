"""Small hand-worked check for the Holm step-down adjustment."""

from build_results_inventory import holm_adjust


def test_holm_hand_worked_example():
    p_values = [0.01, 0.04, 0.03, 0.005]
    assert holm_adjust(p_values) == [0.03, 0.06, 0.06, 0.02]
