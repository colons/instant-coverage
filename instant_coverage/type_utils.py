import sys
import types
from typing import Any, Dict, Tuple, TYPE_CHECKING, Type, Union

from django.test.client import _MonkeyPatchedWSGIResponse as TestHttpResponse


ERROR_TYPE = Union[Tuple[None, None, None], Tuple[Type[BaseException], BaseException, types.TracebackType]]


if TYPE_CHECKING:
    from typing import TypedDict

    class InstantCacheDict(TypedDict):
        responses: Dict[str, TestHttpResponse]
        errors: Dict[str, ERROR_TYPE]
else:
    InstantCacheDict = Any
