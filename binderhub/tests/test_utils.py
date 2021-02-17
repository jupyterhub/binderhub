import ipaddress
from unittest import mock

import pytest

from binderhub import utils


def test_rendezvous_rank():
    # check that a key doesn't move if its assigned bucket remains but the
    # other buckets are removed
    key = "crazy frog is a crazy key"
    first_round = utils.rendezvous_rank(["b1", "b2", "b3"], key)
    second_round = utils.rendezvous_rank([first_round[0], first_round[1]], key)

    assert first_round[0] == second_round[0], key


def test_rendezvous_independence():
    # check that the relative ranking of 80 buckets doesn't depend on the
    # presence of 20 extra buckets
    key = "k1"
    eighty_buckets = utils.rendezvous_rank(["b%i" % i for i in range(80)], key)
    hundred_buckets = utils.rendezvous_rank(["b%i" % i for i in range(100)], key)

    for i in range(80, 100):
        hundred_buckets.remove("b%i" % i)

    assert eighty_buckets == hundred_buckets


def test_rendezvous_redistribution():
    # check that approximately a third of keys move to the new bucket
    # when one is added
    n_keys = 3000

    # count how many keys were moved, which bucket a key started from and
    # which bucket a key was moved from (to the new bucket)
    n_moved = 0
    from_bucket = {"b1": 0, "b2": 0}
    start_in = {"b1": 0, "b2": 0}

    for i in range(n_keys):
        key = f"key-{i}"
        two_buckets = utils.rendezvous_rank(["b1", "b2"], key)
        start_in[two_buckets[0]] += 1
        three_buckets = utils.rendezvous_rank(["b1", "b2", "b3"], key)

        if two_buckets[0] != three_buckets[0]:
            n_moved += 1
            from_bucket[two_buckets[0]] += 1

            # should always move to the newly added bucket
            assert three_buckets[0] == "b3"

    # because of statistical fluctuations we have to leave some room when
    # making this comparison
    assert 0.31 < n_moved / n_keys < 0.35
    # keys should move from the two original buckets with approximately
    # equal probability. We pick 30 because it is "about right"
    assert abs(from_bucket["b1"] - from_bucket["b2"]) < 30
    # the initial distribution of keys should be roughly the same
    # We pick 30 because it is "about right"
    assert abs(start_in["b1"] - start_in["b2"]) < 30


def test_cache():
    cache = utils.Cache(max_size=2)
    cache.set('a', 1)
    cache.set('b', 2)
    assert 'a' in cache
    cache.set('c', 3)
    assert 'a' not in cache
    cache.set('b', 3)
    assert 'b' in cache
    cache.set('d', 4)
    assert 'b' in cache
    assert 'c' not in cache
    assert len(cache) == 2


def test_cache_expiry():
    cache = utils.Cache(2, max_age=10)
    before_now = cache._now

    def later():
        return before_now() + 20

    expired = mock.patch.object(cache, '_now', later)

    cache.set('a', 1)
    assert 'a' in cache
    assert cache.get('a')
    with expired:
        assert not cache.get('a')
        assert 'a' not in cache
        assert 'a' not in cache._ages

    cache.set('a', 1)
    # no max age means no expiry
    with expired, mock.patch.object(cache, 'max_age', 0):
        assert cache.get('a')

    # retrieving an item does *not* update the age
    before_age = cache._ages['a']
    with mock.patch.object(cache, '_now', lambda: before_now() + 1):
        cache.get('a')
    assert cache._ages['a'] == before_age


@pytest.mark.parametrize(
    "ip, cidrs, found",
    [
        ("192.168.1.1", ["192.168.1.1/32", "255.255.0.0/16"], True),
        ("192.168.1.2", ["192.168.1.1/32", "255.255.0.0/16"], False),
        ("192.168.1.2", ["192.168.1.0/24", "255.255.0.0/16"], True),
        ("192.168.1.2", ["255.255.0.0/16", "192.168.1.0/24"], True),
        ("192.168.1.2", [], False),
    ],
)
def test_ip_in_networks(ip, cidrs, found):
    networks = {ipaddress.ip_network(cidr): f"message {cidr}" for cidr in cidrs}
    if networks:
        min_prefix = min(net.prefixlen for net in networks)
    else:
        min_prefix = 1
    match = utils.ip_in_networks(ip, networks, min_prefix)
    if found:
        assert match
        net, message = match
        assert message == f"message {net}"
        assert ipaddress.ip_address(ip) in net
    else:
        assert match == False


def test_ip_in_networks_invalid():
    with pytest.raises(ValueError):
        utils.ip_in_networks("1.2.3.4", {}, 0)
