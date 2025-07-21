from __future__ import annotations

from typing import Any

from contextlib import contextmanager

from mckit.utils.accept import accept, on_unknown_acceptor


def test_accept_single_level():
    class DemoContainer(list):
        pass

    class DemoItem:
        def __init__(self, a: int):
            self.name = a

    dc = DemoContainer(map(DemoItem, range(10)))
    my_sum = sum(range(10))

    @contextmanager
    def visit_container(demo_obj: Any) -> int:
        if isinstance(demo_obj, DemoContainer):

            def at_item(a: Any, b: DemoItem) -> Any:
                a[0] += b.name
                return a

            yield at_item, [0, len(demo_obj)]
        else:
            on_unknown_acceptor(demo_obj)

    _sum, _len = accept(dc, visit_container)
    assert _sum == my_sum
    assert _len == 10


def test_accept_two_levels():
    class DemoContainer(list):
        pass

    class Intermediate(list):
        pass

    class DemoItem:
        def __init__(self, a: int):
            self.name = a

        def __repr__(self):
            return f"Item({self.name})"

    dc = DemoContainer(map(Intermediate, [map(DemoItem, range(2)), map(DemoItem, range(2, 4))]))
    expected = [[sum(range(2)), 2], [sum(range(2, 4)), 2]]

    def at_item(initial: Any, b: DemoItem) -> Any:
        initial[0] += b.name
        return initial

    @contextmanager
    def visit_intermediate(intermediate: Intermediate):
        if isinstance(intermediate, Intermediate):
            initial_for_item = [0, len(intermediate)]
            yield at_item, initial_for_item
        else:
            on_unknown_acceptor(intermediate)

    def at_intermediate(initial: Any, intermediate: Intermediate):
        initial.append(accept(intermediate, visit_intermediate))
        return initial

    @contextmanager
    def visit_container(demo_obj: Any) -> Any:
        if isinstance(demo_obj, DemoContainer):
            initial_for_intermediate = []
            yield at_intermediate, initial_for_intermediate
        else:
            on_unknown_acceptor(demo_obj)

    actual = accept(dc, visit_container)
    assert actual == expected
