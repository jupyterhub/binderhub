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

    print(f'Pruning docker images when {path_to_check} has less than {inode_avail_threshold}% inodes free')

    while True:
        inode_avail = get_inodes_available_fraction(path_to_check) 
        if inode_avail > inode_avail_threshold:
            # Do nothing! We have enough inodes
            print(f'{inode_avail} inode% available, not pruning any images')
            time.sleep(60)
            continue
        else:
            client = docker.from_env()

            images = get_docker_images(client)
            while get_inodes_available_fraction(path_to_check) < inode_avail_threshold:
                # Remove biggest image
                image = images.pop(0)
                try:
                    client.images.remove(image=image.id)
                    print(f'Removed {image.id}')
                except docker.errors.APIError as e:
                    if e.status_code == 409:
                        # This means the image can not be removed right now
                        print(str(e))
                    else:
                        raise

if __name__ == '__main__':
    main()