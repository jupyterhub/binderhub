import pytest
from binderhub import builder


@pytest.mark.parametrize("fullname,basename,tag", [
    ("jupyterhub/k8s-binderhub:0.2.0-a2079a5", "jupyterhub/k8s-binderhub", "0.2.0-a2079a5"),
    ("jupyterhub/jupyterhub", "jupyterhub/jupyterhub", "latest"),
    ("gcr.io/project/image:tag", "project/image", "tag"),
    ("weirdregistry.com/image:tag", "image", "tag"),
    ("gitlab-registry.example.com/group/project:some-tag", "group/project", "some-tag"),
    ("gitlab-registry.example.com/group/project/image:latest", "group/project/image", "latest"),
    ("gitlab-registry.example.com/group/project/my/image:rc1", "group/project/my/image", "rc1")
])
def test_image_basename_resolution(fullname, basename, tag):
    resulting_basename, resulting_tag = builder.BuildHandler._get_image_basename_and_tag(fullname)
    assert resulting_basename == basename
    assert resulting_tag == tag
