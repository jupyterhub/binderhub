"""Launching a binder via API

The binder build API yields a sequence of messages via event-stream.
This example demonstrates how to consume events from the stream
and redirect to the URL when it is ready.

When the image is ready, your browser will open at the desired URL.
"""

import argparse
import json
import sys
import webbrowser

import requests


def build_binder(repo, ref, *, binder_url="https://mybinder.org", build_only):
    """Launch a binder

    Yields Binder's event-stream events (dicts)
    """
    print(f"Building binder for {repo}@{ref}")
    url = binder_url + f"/build/gh/{repo}/{ref}"
    params = {}
    if build_only:
        params = {"build_only": "true"}

    r = requests.get(url, stream=True, params=params)
    r.raise_for_status()
    for line in r.iter_lines():
        line = line.decode("utf8", "replace")
        if line.startswith("data:"):
            yield json.loads(line.split(":", 1)[1])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=str, help="The GitHub repo to build")
    parser.add_argument("--ref", default="HEAD", help="The ref of the repo to build")
    parser.add_argument(
        "--build-only",
        action="store_true",
        help="When passed, the image will not be launched after build",
    )
    file_or_url = parser.add_mutually_exclusive_group()
    file_or_url.add_argument("--filepath", type=str, help="The file to open, if any.")
    file_or_url.add_argument("--urlpath", type=str, help="The url to open, if any.")
    parser.add_argument(
        "--binder",
        default="https://mybinder.org",
        help="""
        The URL of the binder instance to use.
        Use `http://localhost:8585` if you are doing local testing.
    """,
    )
    opts = parser.parse_args()

    for evt in build_binder(
        opts.repo, ref=opts.ref, binder_url=opts.binder, build_only=opts.build_only
    ):
        if "message" in evt:
            print(
                "[{phase}] {message}".format(
                    phase=evt.get("phase", ""),
                    message=evt["message"].rstrip(),
                )
            )
        if evt.get("phase") == "ready":
            if opts.build_only:
                break
            elif opts.filepath:
                url = "{url}notebooks/{filepath}?token={token}".format(
                    **evt, filepath=opts.filepath
                )
            elif opts.urlpath:
                url = "{url}{urlpath}?token={token}".format(**evt, urlpath=opts.urlpath)
            else:
                url = "{url}?token={token}".format(**evt)
            print(f"Opening {url}")
            webbrowser.open(url)
            break
    else:
        sys.exit("binder never became ready")
