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

    # counnt how many keys were moved and which bucket were they moved from
    n_moved = 0
    from_b1 = 0
    from_b2 = 0

    for i in range(n_keys):
        key = f"key-{i}"
        two_buckets = utils.rendezvous_rank(["b1", "b2"], key)
        three_buckets = utils.rendezvous_rank(["b1", "b2", "b3"], key)

        if two_buckets[0] != three_buckets[0]:
            n_moved += 1
            if two_buckets[0] == "b1":
                from_b1 += 1
            if two_buckets[0] == "b2":
                from_b2 += 1
            # should always move to the newly added bucket
            assert three_buckets[0] == "b3"

    # because of statistical fluctuations we have to leave some room when
    # making this comparison
    assert 0.31 < n_moved / n_keys < 0.35
    # keys should move from the two original buckets with approximately
    # equal probability
    assert abs(from_b1 - from_b2) < 10
