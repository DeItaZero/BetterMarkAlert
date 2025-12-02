from typing import Callable

type module_type = tuple[str, str, str]
type exam_type = tuple[int, int]
type dist_type = list[dict[str, str | int]]
type callable_type = Callable[[module_type, dist_type, dist_type], None]
