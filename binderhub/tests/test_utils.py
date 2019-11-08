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
