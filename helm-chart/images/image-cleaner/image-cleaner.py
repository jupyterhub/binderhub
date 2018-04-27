#!/usr/bin/env python3
import os
import sys
import docker
import time

def get_inodes_available_fraction(path):
    """
    Return available_inodes / total_inodes in device containing path
    """
    stat = os.statvfs(path)
    return float(stat.f_favail) / float(stat.f_files)


def get_docker_images(client):
    """
    Return list of docker images, sorted by size
    """
    images = client.images.list()
    images.sort(key=lambda i: i.attrs['Size'], reverse=True)
    return images


def main():
    if 'PATH_TO_CHECK' not in os.environ:
        print(
            'Set PATH_TO_CHECK to path to monitor for inode exhaustion',
            file=sys.stderr
        )
        sys.exit(1)

    if 'INODE_AVAIL_THRESHOLD' not in os.environ:
        print(
            'Set INODE_AVAIL_THRESHOLD to threshold at which docker images should be cleaned up',
            file=sys.stderr
        )
        sys.exit(1)

    path_to_check = os.environ['PATH_TO_CHECK']
    inode_avail_threshold = float(os.environ['INODE_AVAIL_THRESHOLD'])
    client = docker.from_env(version='auto')
    images = get_docker_images(client)

    print(f'Pruning docker images when {path_to_check} has less than {inode_avail_threshold * 100:.1f}% inodes free')

    while True:
        inode_avail = get_inodes_available_fraction(path_to_check)
        if inode_avail > inode_avail_threshold:
            # Do nothing! We have enough inodes
            print(f'{inode_avail * 100}% inodes available, not pruning any images')
        else:
            images = get_docker_images(client)
            if not images:
                print(f'No images to delete but only {inode_avail * 100}% inodes available')
            else:
                print(f'{inode_avail * 100:.1f}% inodes available, pruning from {len(images)} images')

            while images and get_inodes_available_fraction(path_to_check) < inode_avail_threshold:
                if not images:
                    avail_percent = get_inodes_available_fraction(path_to_check) * 100
                    break
                # Remove biggest image
                image = images.pop(0)
                if image.tags:
                    # does it have a name, e.g. jupyter/base-notebook:12345
                    name = image.tags[0]
                else:
                    # no name, use id
                    name = image.id
                gb = image.attrs['Size'] / (2**30)
                print(f'Removing image {name} (size={gb:.2f}GB)')
                try:
                    client.images.remove(image=image.id)
                    print(f'Removed {name}')
                except docker.errors.APIError as e:
                    if e.status_code == 409:
                        # This means the image can not be removed right now
                        print(f'Failed to remove {name}, skipping this image')
                        print(str(e))
                    else:
                        raise
        time.sleep(60)


if __name__ == '__main__':
    main()
