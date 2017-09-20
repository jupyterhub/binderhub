#!/usr/bin/env python3
import os
import subprocess
import argparse
import yaml

def last_git_modified(path):
    return subprocess.check_output([
        'git',
        'log',
        '-n', '1',
        '--pretty=format:%h',
        path
    ]).decode('utf-8')

def image_touched(image, commit_range):
    return subprocess.check_output([
        'git', 'diff', '--name-only', commit_range, os.path.join('images', image)
    ]).decode('utf-8').strip() != ''

def build_images(prefix, images, commit_range=None, push=False):
    for image in images:
        if commit_range:
            if not image_touched(image, commit_range):
                print("Skipping {}, not touched in {}".format(image, commit_range))
                continue
        image_path = os.path.join('images', image)
        tag = last_git_modified(image_path)
        image_spec = '{}{}:{}'.format(prefix, image, tag)

        subprocess.check_call([
            'docker', 'build', '-t', image_spec, image_path
        ])
        if push:
            subprocess.check_call([
                'docker', 'push', image_spec
            ])

def build_values(prefix):
    with open('jupyterhub/values.yaml') as f:
        values = yaml.safe_load(f)

    values['hub']['image']['name'] = prefix + 'hub'
    values['hub']['image']['tag'] = last_git_modified('images/hub')

    values['singleuser']['image']['name'] = prefix + 'singleuser-sample'
    values['singleuser']['image']['tag'] = last_git_modified('images/singleuser-sample')

    with open('jupyterhub/values.yaml', 'w') as f:
        yaml.dump(values, f, default_flow_style=False)


def build_chart():
    version = last_git_modified('.')
    with open('jupyterhub/Chart.yaml') as f:
        chart = yaml.safe_load(f)

    chart['version'] = chart['version'] + '-' + version

    with open('jupyterhub/Chart.yaml', 'w') as f:
        yaml.dump(chart, f, default_flow_style=False)

def publish_pages():
    version = last_git_modified('.')
    subprocess.check_call([
        'git', 'clone', '--no-checkout',
        'git@github.com:jupyterhub/helm-chart', 'gh-pages'],
        env=dict(os.environ, GIT_SSH_COMMAND='ssh -i travis')
    )
    subprocess.check_call(['git', 'checkout', 'gh-pages'], cwd='gh-pages')
    subprocess.check_call([
        'helm', 'package', 'jupyterhub',
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
        '-m', 'Automatic update for commit {}'.format(version)
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

    images = ['hub', 'singleuser-sample']
    if args.action == 'build':
        build_images(args.image_prefix, images, args.commit_range, args.push)
        build_values(args.image_prefix)
        build_chart()
        if args.push:
            publish_pages()

main()
