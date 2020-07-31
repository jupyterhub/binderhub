#!/usr/bin/env python3
"""
Clean docker images

This serves as a substitute for Kubernetes ImageGC
which has thresholds that are not sufficiently configurable on GKE
at this time.
"""

from collections import defaultdict
import logging
import os
import time

import docker
import requests


logging.basicConfig(format='%(asctime)s %(message)s',
                    level=logging.INFO)


annotation_key = "hub.jupyter.org/image-cleaner-cordoned"


def get_absolute_size(path):
    """
    Directory size in bytes
    """
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for fname in filenames:
            f = os.path.join(dirpath, fname)
            # some files are links, skip them as they don't use
            # up additional space
            if os.path.isfile(f):
                total += os.path.getsize(f)

    return total


def get_used_percent(path):
    """
    Return disk usage as a percentage

    (100 is full, 0 is empty)

    Calculated by blocks or inodes,
    which ever reports as the most full.
    """
    stat = os.statvfs(path)
    inodes_avail = stat.f_favail / stat.f_files
    blocks_avail = stat.f_bavail / stat.f_blocks
    return 100 * (1 - min(blocks_avail, inodes_avail))


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
    # create dict by image id for O(1) lookup
    by_id = {image.id: image for image in images}
    # graph contains a set of all descendant (not just immediate)
    # images for each image
    graph = defaultdict(set)
    for image in images:
        while image.attrs['Parent']:
            graph[image.attrs['Parent']].add(image)
            image = by_id[image.attrs['Parent']]

    def image_key(image):
        """Sort images topologically and by size

        - Prefer images with fewer descendants, so that we never try to delete
          an image before its children (fails with 409)
        - Prefer untagged images to tagged ones (delete build intermediates first)
        - Sort topological peers by size
        """
        return (-len(graph[image.id]), not image.tags, image.attrs['Size'])

    images.sort(key=image_key, reverse=True)
    return images


def cordon(kube, node):
    """cordon a kubernetes node"""
    logging.info(f"Cordoning node {node}")
    kube.patch_node(
        node,
        {
            # record that we are the one responsible for cordoning
            "metadata": {
                "annotations": {
                    annotation_key: "true",
                },
            },
            "spec": {
                "unschedulable": True,
            },
        },
    )


def uncordon(kube, node):
    """uncordon a kubernetes node"""
    logging.info(f"Uncordoning node {node}")
    kube.patch_node(
        node,
        {
            # clear annotation since we're no longer the reason for cordoning,
            # if the node ever does become cordoned
            "metadata": {
                "annotations": {
                    annotation_key: None,
                },
            },
            "spec": {
                "unschedulable": False,
            },
        },
    )


def main():
    node = os.getenv('NODE_NAME')
    if node:
        import kubernetes.config
        import kubernetes.client
        try:
            kubernetes.config.load_incluster_config()
        except Exception:
            kubernetes.config.load_kube_config()
        kube = kubernetes.client.CoreV1Api()
        # verify that we can talk to the node
        node_info = kube.read_node(node)
        # recover from possible crash!
        if node_info.spec.unschedulable and node_info.metadata.annotations.get(annotation_key):
            logging.warning(f"Node {node} still cordoned, possibly leftover from earlier crash of image-cleaner")
            uncordon(kube, node)


    path_to_check = os.getenv('PATH_TO_CHECK', '/var/lib/docker')
    interval = float(os.getenv('IMAGE_GC_INTERVAL', '300'))
    delay = float(os.getenv('IMAGE_GC_DELAY', '1'))
    gc_threshold_type = os.getenv('IMAGE_GC_THRESHOLD_TYPE', 'relative')
    gc_low = float(os.getenv('IMAGE_GC_THRESHOLD_LOW', '60'))
    gc_high = float(os.getenv('IMAGE_GC_THRESHOLD_HIGH', '80'))

    logging.info(f'Pruning docker images when {path_to_check} has {gc_high}% inodes or blocks used')

    client = docker.from_env(version='auto')
    images = get_docker_images(client)

    # with the threshold type set to relative the thresholds are interpreted
    # as a percentage of how full the partition is. In absolute mode the
    # thresholds are interpreted as size in bytes. By default you should use
    # "relative" mode. Use "absolute" mode when you are using DIND and your
    # nodes only have one partition.
    if gc_threshold_type == "relative":
        get_used = get_used_percent
        used_msg = '{used:.1f}% used'
    else:
        get_used = get_absolute_size
        used_msg = '{used}bytes used'

    while True:
        used = get_used(path_to_check)
        logging.info(used_msg.format(used=used))
        if used < gc_high:
            # Do nothing! We have enough space
            pass
        else:
            images = get_docker_images(client)
            if not images:
                logging.info(f'No images to delete')
                time.sleep(interval)
                continue
            else:
                logging.info(f'{len(images)} images available to prune')

            start = time.perf_counter()
            images_before = len(images)

            if node:
                cordon(kube, node)

            deleted = 0

            while images and get_used(path_to_check) > gc_low:
                # Ensure the node is still cordoned
                if node:
                    cordon(kube, node)
                # Remove biggest image
                image = images.pop(0)
                if image.tags:
                    # does it have a name, e.g. jupyter/base-notebook:12345
                    name = image.tags[0]
                else:
                    # no name, use id
                    name = image.id
                gb = image.attrs['Size'] / (2**30)
                logging.info(f'Removing {name} (size={gb:.2f}GB)')
                try:
                    client.images.remove(image=image.id, force=True)
                    logging.info(f'Removed {name}')
                    # Delay between deletions.
                    # A sleep here avoids monopolizing the Docker API with deletions.
                    time.sleep(delay)
                except docker.errors.APIError as e:
                    if e.status_code == 409:
                        # This means the image can not be removed right now
                        logging.info(f'Failed to remove {name}, skipping this image')
                        logging.info(str(e))
                    elif e.status_code == 404:
                        logging.info(f'{name} not found, probably already deleted')
                    else:
                        if node:
                            # uncordon before giving up
                            uncordon(kube, node)
                        raise
                except requests.exceptions.ReadTimeout:
                    logging.warning(f'Timeout removing {name}')
                    # Delay longer after a timeout, which indicates that Docker is overworked
                    time.sleep(max(delay, 30))
                except Exception:
                    if node:
                        # uncordon before giving up
                        uncordon(kube, node)
                    raise
                else:
                    deleted += 1

            if node:
                uncordon(kube, node)

            # log what we did and how long it took
            duration = time.perf_counter() - start
            images_deleted = images_before - len(images)
            logging.info(f"Deleted {images_deleted} images in {int(duration)} seconds")

        time.sleep(interval)


if __name__ == '__main__':
    main()
