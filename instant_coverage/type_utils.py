import sys
import types
from typing import Any, Dict, TYPE_CHECKING, Tuple, Type, Union


ERROR_TYPE = Union[Tuple[None, None, None], Tuple[Type[BaseException], BaseException, types.TracebackType]]


if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing import _TypedDict as TypedDict

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse as TestHttpResponse

    class InstantCacheDict(TypedDict):
        responses: Dict[str, TestHttpResponse]
        errors: Dict[str, ERROR_TYPE]
else:
    from django.http import HttpResponse as TestHttpResponse
    InstantCacheDict = Any
