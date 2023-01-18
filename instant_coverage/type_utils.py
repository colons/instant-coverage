import sys
import types
from typing import Dict, TYPE_CHECKING, Tuple, Type, Union


ERROR_TYPE = Union[Tuple[None, None, None], Tuple[Type[BaseException], BaseException, types.TracebackType]]


if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

if TYPE_CHECKING and sys.version_info >= (3, 7):
    from django.test.client import _MonkeyPatchedWSGIResponse as TestHttpResponse
else:
    from django.http import HttpResponse as TestHttpResponse


class InstantCacheDict(TypedDict):
    responses: Dict[str, TestHttpResponse]
    errors: Dict[str, ERROR_TYPE]
