import logging
import os

import cv2
import numpy as np

logger = logging.getLogger(__name__)
logger.setLevel(10)


def cnt_from_img(im, thresh_val=40):
    npim = np.array(im.convert('RGB'))
    npim = npim[:, :, ::-1].copy()

    # Convert to greyscale
    imgray = cv2.cvtColor(npim, cv2.COLOR_BGR2GRAY)

    # Blur
    blur = cv2.GaussianBlur(imgray, (5, 5), 0)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl1 = clahe.apply(blur)

    # Thresholding
    thresh, ret = cv2.threshold(cl1, thresh_val, 255, cv2.THRESH_BINARY)

    # Get contours
    im2, contours, hierarchy = cv2.findContours(ret, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    # Sort contours by area
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    return contours


def img_with_contour(img, cnt):
    cv2.drawContours(img, [cnt], 0, (0, 255, 0), 1)

    return img


def save_contour(cnt, width, height, path):
    empty = np.zeros((height, width, 3))
    cv2.drawContours(empty, [cnt], 0, (0, 255, 0), 1)

    cv2.imwrite(path + ".bmp", empty)


def save_image(img, path):
    if not os.path.exists(path):
        cv2.imwrite(path + ".bmp", np.array(img))
