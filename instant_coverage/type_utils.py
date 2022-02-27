import types
from typing import Dict, Type, TypedDict, Union

from django.http import HttpResponse


ERROR_TYPE = Union[tuple[None, None, None], tuple[Type[BaseException], BaseException, types.TracebackType]]


class InstantCacheDict(TypedDict):
    responses: Dict[str, HttpResponse]
    errors: Dict[str, ERROR_TYPE]
