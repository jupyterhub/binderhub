import pytest

from binderhub.builder import _generate_build_name


@pytest.mark.parametrize('ref,build_slug', [
    # a long ref, no special characters at critical positions
    ('3035124.v3.0', 'dataverse-dvn-2ftjclkp'),
    # with ref_length=6 this has a full stop that gets escaped to a -
    # as the last character, this used to cause an error
    ('20460.v1.0', 'dataverse-s6-2fde95rt'),
    # short ref, should just work and need no special processing
    ('123456', 'dataverse-s6-2fde95rt')
])
def test_build_name(build_slug, ref):
    # Build names have to be usable as pod names, which means they have to
    # be usable as hostnames as well.
    build_name = _generate_build_name(build_slug, ref)

    last_char = build_name[-1]
    assert last_char not in ("-", "_", ".")
