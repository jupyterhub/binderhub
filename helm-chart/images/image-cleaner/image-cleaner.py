#!/usr/bin/env python3
"""
Clean docker images

This serves as a substitute for Kubernetes ImageGC
which has thresholds that are not sufficiently configurable on GKE
at this time.
"""

import os
import time

import docker


def get_inodes_used_percent(path):
    """
    Return used_inodes / total_inodes in device containing path
    as a percentage (100 is full, 0 is empty)
    """
    stat = os.statvfs(path)
    return 100 * (1 - float(stat.f_favail) / float(stat.f_files))


def image_key(image):
    """Sort key for images

    Prefers untagged images, sorted by size
    """
    return (not image.tags, image.attrs['Size'])


def get_docker_images(client):
    """Return list of docker images, sorted by size

    Untagged images will come first
    """
    images = client.images.list(all=True)
    images.sort(key=image_key, reverse=True)
    return images


def main():
    path_to_check = os.getenv('PATH_TO_CHECK', '/var/lib/docker')
    inode_gc_low = float(os.getenv('IMAGE_GC_THRESHOLD_LOW', '60'))
    inode_gc_high = float(os.getenv('IMAGE_GC_THRESHOLD_HIGH', '80'))
    client = docker.from_env(version='auto')
    images = get_docker_images(client)

    print(f'Pruning docker images when {path_to_check} has used {inode_gc_high}% inodes used')

    while True:
        inodes_used = get_inodes_used_percent(path_to_check)
        print(f'{inodes_used:.1f}% inodes used')
        if inodes_used < inode_gc_high:
            # Do nothing! We have enough inodes
            pass
        else:
            images = get_docker_images(client)
            if not images:
                print(f'No images to delete')
            else:
                print(f'Pruning from {len(images)} images')

            while images and get_inodes_used_percent(path_to_check) > inode_gc_low:
                # Remove biggest image
                image = images.pop(0)
                if image.tags:
                    # does it have a name, e.g. jupyter/base-notebook:12345
                    name = image.tags[0]
                else:
                    # no name, use id
                    name = image.id
                gb = image.attrs['Size'] / (2**30)
                print(f'Removing {name} (size={gb:.2f}GB)')
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
