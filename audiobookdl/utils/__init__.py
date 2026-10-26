import importlib.resources
from typing import Sequence
import shutil
from urllib3.poolmanager import PoolManager
from requests.adapters import HTTPAdapter
from ssl import SSLContext

def levenstein_distance(a: str, b: str) -> int:
    """
    Calculates the Levenshtein distance between `a` and `b`

    https://en.wikipedia.org/wiki/Levenshtein_distance
    """
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, 1):
        current = [i]
        for j, char_b in enumerate(b, 1):
            current.append(min(
                previous[j] + 1, # Character is deleted
                current[j-1] + 1, # Character is inserted
                previous[j-1] + (char_a != char_b) # Character is replaced
            ))
        previous = current
    return previous[-1]

def nearest_string(input: str, list: Sequence[str]) -> str:
    """
    Returns the closest element in `list` to `input` based on the levenstein
    distance
    """
    return sorted(list, key = lambda x: levenstein_distance(input, x))[0]


def read_asset_file(path: str) -> str:
    return importlib.resources.files("audiobookdl") \
        .joinpath(path) \
        .read_text(encoding="utf8")


def program_in_path(program: str) -> bool:
    """Checks whether `program` is in the path"""
    return shutil.which(program) is not None

class CustomSSLContextHTTPAdapter(HTTPAdapter):
    """Transport adapter that allows us to use a custom SSLContext."""

    def __init__(self, ssl_context: SSLContext, **kwargs) -> None:
        self.ssl_context: SSLContext = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context,
        )
