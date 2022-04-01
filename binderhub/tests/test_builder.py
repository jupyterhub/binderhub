import pytest

from binderhub.builder import _generate_build_name, _get_image_basename_and_tag


@pytest.mark.parametrize(
    "fullname,basename,tag",
    [
        (
            "jupyterhub/k8s-binderhub:0.2.0-a2079a5",
            "jupyterhub/k8s-binderhub",
            "0.2.0-a2079a5",
        ),
        ("jupyterhub/jupyterhub", "jupyterhub/jupyterhub", "latest"),
        ("gcr.io/project/image:tag", "project/image", "tag"),
        ("weirdregistry.com/image:tag", "image", "tag"),
        (
            "gitlab-registry.example.com/group/project:some-tag",
            "group/project",
            "some-tag",
        ),
        (
            "gitlab-registry.example.com/group/project/image:latest",
            "group/project/image",
            "latest",
        ),
        (
            "gitlab-registry.example.com/group/project/my/image:rc1",
            "group/project/my/image",
            "rc1",
        ),
    ],
)
def test_image_basename_resolution(fullname, basename, tag):
    result_basename, result_tag = _get_image_basename_and_tag(fullname)
    assert result_basename == basename
    assert result_tag == tag


@pytest.mark.parametrize(
    "ref,build_slug",
    [
        # a long ref, no special characters at critical positions
        ("3035124.v3.0", "dataverse-dvn-2ftjclkp"),
        # with ref_length=6 this has a full stop that gets escaped to a -
        # as the last character, this used to cause an error
        ("20460.v1.0", "dataverse-s6-2fde95rt"),
        # short ref, should just work and need no special processing
        ("123456", "dataverse-s6-2fde95rt"),
    ],
)
def test_build_name(build_slug, ref):
    # Build names have to be usable as pod names, which means they have to
    # be usable as hostnames as well.
    build_name = _generate_build_name(build_slug, ref)

    last_char = build_name[-1]
    assert last_char not in ("-", "_", ".")
