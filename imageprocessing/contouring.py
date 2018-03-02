from multiprocessing.pool import ThreadPool

import cv2
import numpy as np
import os
from PIL import Image


def cnt_from_img(im, write_files=False):
    # Load the image
    #im = cv2.imread(img)
    npim = np.array(im.convert('RGB'))
    npim = npim[:, :, ::-1].copy()
    copy = npim.copy()
    # Crop the 4096x2160 image to
    #im = im[200:700, 1698:2398]
    # Convert to greyscale
    imgray = cv2.cvtColor(npim, cv2.COLOR_BGR2GRAY)
    # Denoise
    #denoise = cv2.fastNlMeansDenoising(imgray, templateWindowSize=7, searchWindowSize=21, h=12)
    # Blur
    blur = cv2.bilateralFilter(imgray, 9, 75, 75)
    #blur = cv2.GaussianBlur(denoise, (5, 5), 0)
    # Thresholding
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 23, 2)
    #ret, thresh = cv2.threshold(blur, 127, 255, cv2.THRESH_BINARY)
    # Detect edges
    #edges = cv2.Canny(thresh, 100, 100)
    # Get contours
    im2, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    # Sort contours by area
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    return contours


def img_with_contour(img, cnt):
    cv2.drawContours(img, [cnt], 0, (0, 255, 0), 1)
    #res = empty[:]
    #copy_condition = empty[:, :, 3] > 0
    #res[copy_condition] = empty[copy_condition]
    return img


def save_contour(cnt, width, height, path):
    #x, y, w, h = cv2.boundingRect(cnt)
    empty = np.zeros((height, width, 3))
    cv2.drawContours(empty, [cnt], 0, (0, 255, 0), 1)
    #crop_img = empty[y:y + h, x:x + w]

    cv2.imwrite(path + ".bmp", empty)


def save_image(img, path):

    if not os.path.exists(path):
        cv2.imwrite(path + ".bmp", np.array(img))


