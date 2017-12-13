#!/usr/bin/env python3
import argparse
import os
import subprocess
import shutil
from tempfile import TemporaryDirectory

from ruamel.yaml import YAML

# use safe roundtrip yaml loader
yaml = YAML(typ='rt')
yaml.indent(offset=2)

def last_modified_commit(*paths, **kwargs):
    return subprocess.check_output([
        'git',
        'log',
        '-n', '1',
        '--pretty=format:%h',
        *paths
    ], **kwargs).decode('utf-8')

def last_modified_date(*paths, **kwargs):
    return subprocess.check_output([
        'git',
        'log',
        '-n', '1',
        '--pretty=format:%cd',
        '--date=iso',
        *paths
    ], **kwargs).decode('utf-8')

def path_touched(*paths, commit_range):
    return subprocess.check_output([
        'git', 'diff', '--name-only', commit_range, *paths
    ]).decode('utf-8').strip() != ''


def render_build_args(options, ns):
    """Get docker build args dict, rendering any templated args."""
    build_args = options.get('buildArgs', {})
    for key, value in build_args.items():
        build_args[key] = value.format(**ns)
    return build_args

def build_image(image_path, image_spec, build_args):
    cmd = ['docker', 'build', '-t', image_spec, image_path]

    for k, v in build_args.items():
        cmd += ['--build-arg', '{}={}'.format(k, v)]
    subprocess.check_call(cmd)

def build_images(prefix, images, tag=None, commit_range=None, push=False):
    value_modifications = {}
    for name, options in images.items():
        image_path = os.path.join('images', name)
        paths = options.get('paths', []) + [image_path]
        last_commit = last_modified_commit(*paths)
        if tag is None:
            tag = last_commit
        image_name = prefix + name
        image_spec = '{}:{}'.format(image_name, tag)
        value_modifications[options['valuesPath']] = {
            'name': image_name,
            'tag': tag
        }

        if commit_range and not path_touched(*paths, commit_range=commit_range):
            print(f"Skipping {name}, not touched in {commit_range}")
            continue

        template_namespace = {
            'LAST_COMMIT': last_commit,
            'TAG': tag,
        }

        build_args = render_build_args(options, template_namespace)
        build_image(image_path, image_spec, build_args)

        if push:
            subprocess.check_call([
                'docker', 'push', image_spec
            ])
    return value_modifications

def build_values(name, values_mods):
    """Update name/values.yaml with modifications"""

    values_file = os.path.join(name, 'values.yaml')

    with open(values_file) as f:
        values = yaml.load(f)

    for key, value in values_mods.items():
        parts = key.split('.')
        mod_obj = values
        for p in parts:
            mod_obj = mod_obj[p]
        mod_obj.update(value)


    with open(values_file, 'w') as f:
        yaml.dump(values, f)


def build_chart(name, version=None, paths=None):
    """Update chart with specified version or last-modified commit in path(s)"""
    chart_file = os.path.join(name, 'Chart.yaml')
    with open(chart_file) as f:
        chart = yaml.load(f)

    if version is None:
        if paths is None:
            paths = ['.']
        commit = last_modified_commit(*paths)
        version = chart['version'].split('-')[0] + '-' + commit

    chart['version'] = version

    with open(chart_file, 'w') as f:
        yaml.dump(chart, f)


def publish_pages(name, paths, git_repo, published_repo):
    """publish helm chart index to github pages"""
    version = last_modified_commit(*paths)
    checkout_dir = '{}-{}'.format(name, version)
    subprocess.check_call([
        'git', 'clone', '--no-checkout',
        'git@github.com:{}'.format(git_repo), checkout_dir],
    )
    subprocess.check_call(['git', 'checkout', 'gh-pages'], cwd=checkout_dir)

    # package the latest version into a temporary directory
    # and run helm repo index with --merge to update index.yaml
    # without refreshing all of the timestamps
    with TemporaryDirectory() as td:
        subprocess.check_call([
            'helm', 'package', name,
            '--destination', td + '/',
        ])

        subprocess.check_call([
            'helm', 'repo', 'index', td,
            '--url', published_repo,
            '--merge', os.path.join(checkout_dir, 'index.yaml'),
        ])

        # equivalent to `cp td/* checkout/`
        # copies new helm chart and updated index.yaml
        for f in os.listdir(td):
            shutil.copy2(
                os.path.join(td, f),
                os.path.join(checkout_dir, f)
            )
    subprocess.check_call(['git', 'add', '.'], cwd=checkout_dir)
    subprocess.check_call([
        'git',
        'commit',
        '-m', '[{}] Automatic update for commit {}'.format(name, version)
    ], cwd=checkout_dir)
    subprocess.check_call(
        ['git', 'push', 'origin', 'gh-pages'],
        cwd=checkout_dir,
    )


def main():
    with open('chartpress.yaml') as f:
        config = yaml.load(f)

    argparser = argparse.ArgumentParser()

    argparser.add_argument('--commit-range', help='Range of commits to consider when building images')
    argparser.add_argument('--push', action='store_true')
    argparser.add_argument('--publish-chart', action='store_true')
    argparser.add_argument('--tag', default=None, help='Use this tag for images & charts')

    args = argparser.parse_args()

    for chart in config['charts']:
        value_mods = build_images(chart['imagePrefix'], chart['images'], args.tag, args.commit_range, args.push)
        build_values(chart['name'], value_mods)
        chart_paths = ['.'] + chart.get('paths', [])
        build_chart(chart['name'], paths=chart_paths, version=args.tag)
        if args.publish_chart:
            publish_pages(chart['name'],
                paths=chart_paths,
                git_repo=chart['repo']['git'],
                published_repo=chart['repo']['published'],
            )

main()
