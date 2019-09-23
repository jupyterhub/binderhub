from binderhub import utils


def test_rendezvous_rank():
    # check that a key doesn't move if its assigned bucket remains but the
    # other buckets are removed
    key = "k1"
    first_round = utils.rendezvous_rank(["b1", "b2", "b3"], key)
    second_round = utils.rendezvous_rank([first_round[0], first_round[1]], key)

    assert first_round[0] == second_round[0], key

    key = "sdsdggdddddd"
    first_round = utils.rendezvous_rank(["b1", "b2", "b3"], key)
    second_round = utils.rendezvous_rank([first_round[0], first_round[1]], key)

    assert first_round[0] == second_round[0], key

    key = "crazy frog is a crazy key"
    first_round = utils.rendezvous_rank(["b1", "b2", "b3"], key)
    second_round = utils.rendezvous_rank([first_round[0], first_round[1]], key)

    assert first_round[0] == second_round[0], key


def test_rendezvous_independence():
    # check that the relative ranking of two buckets doesn't depend on the
    # presence of a third bucket
    key = "k1"
    two_buckets = utils.rendezvous_rank(["b1", "b3"], key)
    three_buckets = utils.rendezvous_rank(["b1", "b2", "b3"], key)
    # remove "b2" and check ranking
    three_buckets.remove("b2")

    assert two_buckets == three_buckets
