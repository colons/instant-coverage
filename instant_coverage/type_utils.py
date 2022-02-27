import sys
import types
from typing import Any, Dict, Tuple, Type, Union

from django.http import HttpResponse


ERROR_TYPE = Union[Tuple[None, None, None], Tuple[Type[BaseException], BaseException, types.TracebackType]]


if sys.version_info >= (3, 8):
    from typing import TypedDict

    class InstantCacheDict(TypedDict):
        responses: Dict[str, HttpResponse]
        errors: Dict[str, ERROR_TYPE]
else:
    InstantCacheDict = Any
