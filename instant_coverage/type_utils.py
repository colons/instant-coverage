import types
from typing import Dict, Tuple, Type, TypedDict, Union

from django.http import HttpResponse


ERROR_TYPE = Union[Tuple[None, None, None], Tuple[Type[BaseException], BaseException, types.TracebackType]]


class InstantCacheDict(TypedDict):
    responses: Dict[str, HttpResponse]
    errors: Dict[str, ERROR_TYPE]
