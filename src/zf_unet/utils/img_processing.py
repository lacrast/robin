import os

import cv2
import numpy as np


def split_img(img: np.array, size_x: int = 128, size_y: int = 128) -> ([np.array], int, int):
    """Split image to parts (little images).

    Walk through the whole image by the window of size size_x * size_y without overlays and
    save all parts in list. If the image sizes are not multiples of the window sizes,
    the image will be complemented by a frame of suitable size.

    """
    max_y, max_x = img.shape[:2]
    border_y = 0
    if max_y % size_y != 0:
        border_y = (size_y - (max_y % size_y) + 1) // 2
        img = cv2.copyMakeBorder(img, border_y, border_y, 0, 0, cv2.BORDER_CONSTANT, value=[255, 255, 255])
        max_y = img.shape[0]
    border_x = 0
    if max_x % size_x != 0:
        border_x = (size_x - (max_x % size_x) + 1) // 2
        img = cv2.copyMakeBorder(img, 0, 0, border_x, border_x, cv2.BORDER_CONSTANT, value=[255, 255, 255])
        max_x = img.shape[1]

    parts = []
    curr_y = 0
    # TODO: rewrite with generators.
    while (curr_y + size_y) <= max_y:
        curr_x = 0
        while (curr_x + size_x) <= max_x:
            parts.append(img[curr_y:curr_y + size_y, curr_x:curr_x + size_x])
            curr_x += size_x
        curr_y += size_y
    return parts, border_y, border_x


def combine_imgs(imgs: [np.array], border_y: int, border_x: int, max_y: int, max_x: int) -> np.array:
    """Combine image parts to one big image.

    Walk through list of images and create from them one big image with sizes max_x * max_y.
    If border_x and border_y are non-zero, they will be removed from created image.
    The list of images should contain data in the following order:
    from left to right, from top to bottom.

    """
    max_y += (border_y * 2)
    max_x += (border_x * 2)
    img = np.zeros((max_y, max_x), np.float)
    size_y, size_x = imgs[0].shape
    curr_y = 0
    i = 0
    # TODO: rewrite with generators.
    while (curr_y + size_y) <= max_y + border_y * 2:
        curr_x = 0
        while (curr_x + size_x) <= max_x + border_x * 2:
            try:
                img[curr_y:curr_y + size_y, curr_x:curr_x + size_x] = imgs[i]
            except:
                i -= 1
            i += 1
            curr_x += size_x
        curr_y += size_y
    img = img[border_y:img.shape[0] - border_y, border_x:img.shape[1] - border_x]
    return img


def normalize_img(img: np.array) -> np.array:
    """Normalize image channels from uint[0..255] to float[0.0..1.0]."""
    return img.astype(float) / 255


def preprocess_img(img: np.array) -> np.array:
    """"""
    return img


def process_unet_img(img: np.array, model, batchsize: int = 20) -> np.array:
    """Split image to 128x128 parts and run U-net for every part."""
    parts, border_y, border_x = split_img(img)
    for i in range(len(parts)):
        parts[i] = parts[i] / 255
    parts = np.array(parts)
    parts.shape = (parts.shape[0], parts.shape[1], parts.shape[2], 1)
    parts = model.predict(parts, batchsize)
    tmp = []
    for part in parts:
        part.shape = (128, 128)
        tmp.append(part)
    parts = tmp
    img = combine_imgs(parts, border_y, border_x, img.shape[0], img.shape[1])
    img = img * 255
    img = img.astype(np.uint8)
    return img


def postprocess_img(img: np.array) -> np.array:
    """Apply Otsu threshold and bottom-hat transform to image."""
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    img = cv2.erode(img, kernel, 1)
    img = cv2.dilate(img, kernel, 1)
    return img


def binarize_img(img: np.array, model, batchsize: int = 20) -> np.array:
    """Binarize image, using U-net, Otsu, bottom-hat transform etc."""
    img = preprocess_img(img)
    img = process_unet_img(img, model, batchsize)
    img = postprocess_img(img)
    return img


def mkdir_s(path: str):
    """Create directory in specified path, if not exists."""
    if not os.path.exists(path):
        os.makedirs(path)
