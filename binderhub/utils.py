"""Miscellaneous utilities"""
from collections import OrderedDict
from hashlib import blake2b

from traitlets import Integer, TraitError


def blake2b_hash_as_int(b):
    """Compute digest of the bytes `b` using the Blake2 hash function.

    Returns a unsigned 64bit integer.
    """
    return int.from_bytes(blake2b(b, digest_size=8).digest(), "big")


def rendezvous_rank(buckets, key):
    """Rank the buckets for a given key using Rendez-vous hashing

    Each bucket is scored for the specified key. The return value is a list of
    all buckets, sorted in decreasing order (highest ranked first).
    """
    ranking = []
    for bucket in buckets:
        # The particular hash function doesn't matter a lot, as long as it is
        # one that maps the key to a fixed sized value and distributes the keys
        # uniformly across the output space
        score = blake2b_hash_as_int(
            b"%s-%s" % (str(key).encode(), str(bucket).encode())
        )
        ranking.append((score, bucket))

    return [b for (s, b) in sorted(ranking, reverse=True)]


class ByteSpecification(Integer):
    """
    Allow easily specifying bytes in units of 1024 with suffixes

    Suffixes allowed are:
      - K -> Kilobyte
      - M -> Megabyte
      - G -> Gigabyte
      - T -> Terabyte

    Stolen from JupyterHub
    """

    UNIT_SUFFIXES = {
        "K": 1024,
        "M": 1024 * 1024,
        "G": 1024 * 1024 * 1024,
        "T": 1024 * 1024 * 1024 * 1024,
    }

    # Default to allowing None as a value
    allow_none = True

    def validate(self, obj, value):
        """
        Validate that the passed in value is a valid memory specification

        It could either be a pure int, when it is taken as a byte value.
        If it has one of the suffixes, it is converted into the appropriate
        pure byte value.
        """
        if isinstance(value, (int, float)):
            return int(value)

        try:
            num = float(value[:-1])
        except ValueError:
            raise TraitError(
                "{val} is not a valid memory specification. Must be an int or a string with suffix K, M, G, T".format(
                    val=value
                )
            )
        suffix = value[-1]
        if suffix not in self.UNIT_SUFFIXES:
            raise TraitError(
                "{val} is not a valid memory specification. Must be an int or a string with suffix K, M, G, T".format(
                    val=value
                )
            )
        else:
            return int(float(num) * self.UNIT_SUFFIXES[suffix])


class Cache(OrderedDict):
    """Basic LRU Cache with get/set"""

    def __init__(self, max_size=1024):
        self.max_size = max_size

    def get(self, key, default=None):
        """Get an item from the cache

        same as dict.get
        """
        if key in self:
            self.move_to_end(key)
        return super().get(key, default)

    def set(self, key, value):
        """Store an item in the cache

        - if already there, moves to the most recent
        - if full, delete the oldest item
        """
        self[key] = value
        self.move_to_end(key)
        if len(self) > self.max_size:
            first_key = next(iter(self))
            self.pop(first_key)


def url_path_join(*pieces):
    """Join components of url into a relative url.

    Use to prevent double slash when joining subpath. This will leave the
    initial and final / in place.

    Copied from `notebook.utils.url_path_join`.
    """
    initial = pieces[0].startswith("/")
    final = pieces[-1].endswith("/")
    stripped = [s.strip("/") for s in pieces]
    result = "/".join(s for s in stripped if s)

    if initial:
        result = "/" + result
    if final:
        result = result + "/"
    if result == "//":
        result = "/"

    return result


# FIXME: remove when instantiating a kubernetes client
# doesn't create N-CPUs threads unconditionally.
# monkeypatch threadpool in kubernetes api_client
# to avoid instantiating ThreadPools.
# This is known to work for kubernetes-4.0
# and may need updating with later kubernetes clients

from unittest.mock import Mock
from kubernetes.client import api_client

_dummy_pool = Mock()
api_client.ThreadPool = lambda *args, **kwargs: _dummy_pool
