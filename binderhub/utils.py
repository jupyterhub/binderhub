"""Miscellaneous utilities"""
from collections import OrderedDict
from hashlib import blake2b
import ipaddress
import time

from traitlets import Unicode, Integer, TraitError

from unittest.mock import Mock
from kubernetes.client import api_client


# default _request_timeout for kubernetes api requests
# tuple of two timeouts: (connect_timeout, read_timeout)
# the most important of these is the connect_timeout,
# which can hang for a *very* long time when there are internal
# kubernetes connection issues
KUBE_REQUEST_TIMEOUT = (3, 30)


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


class CPUSpecification(Unicode):
    """
    Allows specifying CPU limits

    Suffixes allowed are:
      - m -> millicore

    """

    # Default to allowing None as a value
    allow_none = True

    def validate(self, obj, value):
        """
        Validate that the passed in value is a valid cpu specification
        in the K8s CPU meaning.
        
        See https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-cpu

        It could either be a pure int or float, when it is taken as a value.
        In case of integer it can optionally have 'm' suffix to designate millicores.
        """

        def raise_error(value):
            raise TraitError(
                "{val} is not a valid cpu specification".format(
                    val=value
                )
            )

        # Positive filter for numberic values
        only_positive = lambda v : v if v >= 0 else raise_error(v)

        if value is None:
            return 0

        if isinstance(value, bool):
            raise_error(value)

        if isinstance(value, int):
            return only_positive(int(value))

        if isinstance(value, float):
            return only_positive(float(value))

        # Must be string
        if not isinstance(value, str):
            raise_error(value)

        # Try treat it as integer
        _int_value = None
        try:
            _int_value = int(value)
        except ValueError:
            pass

        if isinstance(_int_value, int):
            return only_positive(_int_value)

        # Try treat it as float
        _float_value = None
        try:
            _float_value = float(value)
        except ValueError:
            pass

        if isinstance(_float_value, float):
            return only_positive(_float_value)

        # Try treat it as millicore spec
        try:
            _unused = only_positive(int(value[:-1]))
        except ValueError:
            raise_error(value)

        if value[-1] not in ['m']:
            raise_error(value)

        return value

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

    def __init__(self, max_size=1024, max_age=0):
        self.max_size = max_size
        self.max_age = max_age
        self._ages = {}

    def _now(self):
        return time.perf_counter()

    def _check_expired(self, key):
        if not self.max_age:
            return False
        if self._ages[key] + self.max_age < self._now():
            self.pop(key)
            return True
        return False

    def get(self, key, default=None):
        """Get an item from the cache

        same as dict.get
        """
        if key in self and not self._check_expired(key):
            self.move_to_end(key)
        return super().get(key, default)

    def set(self, key, value):
        """Store an item in the cache

        - if already there, moves to the most recent
        - if full, delete the oldest item
        """
        self[key] = value
        self._ages[key] = self._now()
        self.move_to_end(key)
        if len(self) > self.max_size:
            first_key = next(iter(self))
            self.pop(first_key)

    def pop(self, key):
        result = super().pop(key)
        self._ages.pop(key)
        return result


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


def ip_in_networks(ip, networks, min_prefix_len=1):
    """Return whether `ip` is in the dict of networks

    This is O(1) regardless of the size of networks

    Implementation based on netaddr.IPSet.__contains__

    Repeatedly checks if ip/32; ip/31; ip/30; etc. is in networks
    for all netmasks that match the given ip,
    for a max of 32 dict key lookups for ipv4.

    If all netmasks have a prefix length of e.g. 24 or greater,
    min_prefix_len prevents checking wider network masks that can't possibly match.

    Returns `(netmask, networks[netmask])` for matching netmask
    in networks, if found; False, otherwise.
    """
    if min_prefix_len < 1:
        raise ValueError(f"min_prefix_len must be >= 1, got {min_prefix_len}")
    if not networks:
        return False
    check_net = ipaddress.ip_network(ip)
    while check_net.prefixlen >= min_prefix_len:
        if check_net in networks:
            return check_net, networks[check_net]
        check_net = check_net.supernet(1)
    return False


# FIXME: remove when instantiating a kubernetes client
# doesn't create N-CPUs threads unconditionally.
# monkeypatch threadpool in kubernetes api_client
# to avoid instantiating ThreadPools.
# This is known to work for kubernetes-4.0
# and may need updating with later kubernetes clients
_dummy_pool = Mock()
api_client.ThreadPool = lambda *args, **kwargs: _dummy_pool
