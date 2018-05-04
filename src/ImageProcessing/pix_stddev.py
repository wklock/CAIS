from multiprocessing.pool import ThreadPool

import cv2
import numpy as np


def stddev_for_pix(x, y, std_arr, images):
    std_arr[x, y] = np.std(images[:, x, y])


def pix_int_stddev(image_stack, parallel=False):
    if not image_stack:
        print("image_stack is empty")
        return

    # open images
    images = []
    for image in image_stack:
        im = cv2.imread(image, 0)
        images.append(im)

    images = np.asarray(images)
    l, w = np.shape(images[0])
    stddev_arr = np.zeros(np.shape(images[0]))
    if parallel:
        p = ThreadPool(8)
        args = [(x, y, stddev_arr, images) for x in range(0, l) for y in range(0, w)]
        p.starmap(stddev_for_pix, args)
    else:
        for x in range(0,l):
            for y in range(0,w):
                stddev_for_pix(x, y, stddev_arr, images)
    return stddev_arr