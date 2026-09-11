from __future__ import annotations

from pb_test_driver.ui import rows_from_cells


def test_rows_grouped_by_top_and_ordered_by_left() -> None:
    cells = [
        {"name": "name", "value": "beta", "top": 730, "left": 1352},
        {"name": "id", "value": "1", "top": 690, "left": 1260},
        {"name": "amount", "value": "10,50", "top": 690, "left": 1618},
        {"name": "name", "value": "alpha", "top": 690, "left": 1352},
        {"name": "id", "value": "2", "top": 730, "left": 1260},
        {"name": "amount", "value": "20,25", "top": 730, "left": 1618},
    ]
    assert rows_from_cells(cells) == [
        {"id": "1", "name": "alpha", "amount": "10,50"},
        {"id": "2", "name": "beta", "amount": "20,25"},
    ]


def test_freeform_is_one_column_per_line() -> None:
    cells = [
        {"name": "id", "value": "7", "top": 652, "left": 2090},
        {"name": "name", "value": "gamma", "top": 702, "left": 2090},
    ]
    assert rows_from_cells(cells) == [{"id": "7"}, {"name": "gamma"}]


def test_duplicate_and_empty_names_get_suffixes() -> None:
    cells = [
        {"name": "", "value": "a", "top": 0, "left": 0},
        {"name": "x", "value": "b", "top": 0, "left": 10},
        {"name": "x", "value": "c", "top": 0, "left": 20},
    ]
    assert rows_from_cells(cells) == [{"col1": "a", "x": "b", "x_3": "c"}]
