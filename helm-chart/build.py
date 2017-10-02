#!/usr/bin/env python3
import os
import subprocess
import argparse
from ruamel.yaml import YAML

yaml = YAML()
yaml.indent(offset=2)

BASEPATH = os.path.abspath(os.path.dirname(__file__))
CHARTPATH = os.path.join(BASEPATH, 'binderhub')
ROOTPATH = os.path.dirname(BASEPATH)
NAME = 'binderhub'
PYPKGPATH = os.path.join(ROOTPATH, NAME)
SETUP_PY = os.path.join(ROOTPATH, 'setup.py')

IMAGE_PATH = os.path.join(BASEPATH, 'images', NAME)
# IMAGE_FILES should be all paths that contribute to the binderhub image
# namely, the Python package itself and the image directory
IMAGE_FILES = [SETUP_PY, PYPKGPATH, IMAGE_PATH]

# CHART_FILES should be all files that contribute to the chart
# namely, all image files plus the chart itself
CHART_FILES = IMAGE_FILES + [CHARTPATH]

def last_git_modified(paths):
    """Return the short hash of the last commit on one or more paths"""
    if isinstance(paths, str):
        paths = [paths]
    return subprocess.check_output([
        'git',
        'log',
        '-n', '1',
        '--pretty=format:%h',
        '--',
    ] + list(paths)).decode('utf-8')


def path_changed(paths, commit_range):
    """Have the path(s) changed during the given commit range?"""
    if isinstance(paths, str):
        paths = [paths]
    return subprocess.check_output([
        'git', 'diff', '--name-only', commit_range, '--',
    ] + paths).decode('utf-8').strip() != ''


def build_images(prefix, images, commit_range=None, push=False):
    for image in images:
        image_path = os.path.join(BASEPATH, 'images', image)
        if commit_range:
            if path_changed(IMAGE_FILES, commit_range):
                print("Skipping {}, not touched in {}".format(image, commit_range))
                continue
        tag = last_git_modified(IMAGE_FILES)
        image_spec = '{}{}:{}'.format(prefix, image, tag)

        subprocess.check_call([
            'docker', 'build', '-t', image_spec,
            '--build-arg', 'BINDERHUB_VERSION=%s' % tag,
            image_path
        ])
        if push:
            subprocess.check_call([
                'docker', 'push', image_spec
            ])


def build_values(prefix):
    with open(os.path.join(CHARTPATH, 'values.yaml')) as f:
        values = yaml.load(f)

    values['image']['name'] = prefix + NAME
    values['image']['tag'] = last_git_modified(IMAGE_FILES)

    with open(os.path.join(CHARTPATH, 'values.yaml'), 'w') as f:
        yaml.dump(values, f)


def build_chart():
    version = last_git_modified([BASEPATH] + IMAGE_FILES)
    with open(os.path.join(CHARTPATH, 'Chart.yaml')) as f:
        chart = yaml.load(f)

    chart['version'] = chart['version'].split('-')[0] + '-' + version

    with open(os.path.join(CHARTPATH, 'Chart.yaml'), 'w') as f:
        yaml.dump(chart, f)


def publish_pages():
    version = last_git_modified('.')
    subprocess.check_call([
        'git', 'clone', '--no-checkout',
        'git@github.com:jupyterhub/helm-chart', 'gh-pages'],
        env=dict(os.environ, GIT_SSH_COMMAND='ssh -i travis')
    )
    subprocess.check_call(['git', 'checkout', 'gh-pages'], cwd='gh-pages')
    subprocess.check_call(['helm', 'repo', 'add', 'jupyterhub', 'https://jupyterhub.github.io/helm-chart/'])
    subprocess.check_call(['helm', 'repo', 'update'])
    subprocess.check_call([
        'helm', 'package', '--dependency-update', CHARTPATH,
        '--destination', 'gh-pages/'
    ])
    subprocess.check_call([
        'helm', 'repo', 'index', '.',
        '--url', 'https://jupyterhub.github.io/helm-chart'
    ], cwd='gh-pages')
    subprocess.check_call(['git', 'add', '.'], cwd='gh-pages')
    subprocess.check_call([
        'git',
        'commit',
        '-m', '[binderhub] Automatic update for commit {}'.format(version)
    ], cwd='gh-pages')
    subprocess.check_call(
        ['git', 'push', 'origin', 'gh-pages'],
        cwd='gh-pages',
        env=dict(os.environ, GIT_SSH_COMMAND='ssh -i ../travis')
    )


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '--image-prefix',
        default='jupyterhub/k8s-'
    )
    subparsers = argparser.add_subparsers(dest='action')

    build_parser = subparsers.add_parser('build', description='Build & Push images')
    build_parser.add_argument('--commit-range', help='Range of commits to consider when building images')
    build_parser.add_argument('--push', action='store_true')


    args = argparser.parse_args()

    images = ['binderhub']
    if args.action == 'build':
        build_images(args.image_prefix, images, args.commit_range, args.push)
        build_values(args.image_prefix)
        build_chart()
        if args.push:
            publish_pages()

main()
