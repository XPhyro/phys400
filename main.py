#!/usr/bin/env python3
#
#
# Assess and display entropy of images via different methods.
# For usage, see `./main.py --help`.
#
#
# ---------------------------------
# method         | resources
#
# pseudo-spatial | TO BE ADDED
#
# 2d-gradient    | https://arxiv.org/abs/1609.01117
#
# 2d-delentropy  | https://arxiv.org/abs/1609.01117
#                | https://github.com/Causticity/sipp
# ---------------------------------


from PIL import Image
from copy import deepcopy as duplicate
from matplotlib import pyplot as plt
from sys import argv
import argparse
import cv2 as cv
import imageio
import numpy as np


def log(msg):
    print(f"{execname}: {msg}")


def method_pseudo_spatial():
    log("reading image")

    inputimg = Image.open(args.input)
    greyimg = inputimg.convert("L")
    inputimgarr = np.array(inputimg)
    greyimgarr = np.array(greyimg)

    imgarr = duplicate(greyimgarr)
    imgshape = imgarr.shape

    kernsize = args.kernel_size
    kernrad = round((kernsize - 1) / 2)

    log("processing image")

    entropies = []
    for i in range(imgshape[0]):
        for j in range(imgshape[1]):
            region = greyimgarr[
                # ymax:ymin, xmax:xmin
                np.max([0, i - kernrad]) : np.min([imgshape[0], i + kernrad]),
                np.max([0, j - kernrad]) : np.min([imgshape[1], j + kernrad]),
            ].flatten()
            size = region.size

            probs = [np.size(region[region == i]) / size for i in set(region)]
            entropy = np.sum([p * np.log2(1 / p) for p in probs])

            entropies.append(entropy)
            imgarr[i, j] = entropy

    log("showing image")

    plt.subplot(1, 4, 1)
    plt.imshow(inputimgarr)
    plt.title(f"Input Image")

    plt.subplot(1, 4, 2)
    plt.imshow(greyimgarr, cmap=plt.cm.gray)
    plt.title(f"Greyscale Image")

    plt.subplot(1, 4, 3)
    plt.imshow(imgarr, cmap=plt.cm.jet)
    plt.colorbar()
    plt.title(f"Entropy Map With {kernsize}x{kernsize} Kernel")

    refimg = cv.imread("ref/barbara.png")
    plt.subplot(1, 4, 4)
    plt.imshow(refimg, cmap=plt.cm.gray)
    plt.title("Reference Map")

    log(f"entropy = {np.average(entropies)} ± {np.std(entropies)}")

    plt.show()


def method_gradient():
    log("reading image")

    inputimg = cv.imread(args.input)
    greyimg = cv.cvtColor(inputimg, cv.COLOR_BGR2GRAY)

    log("processing image")

    # parameters
    realgrad = True
    concave = True

    if realgrad:
        grads = np.gradient(greyimg)
        gradx = grads[0]
        grady = grads[1]
    else:
        gradx = cv.filter2D(
            greyimg,
            cv.CV_8U,
            cv.flip(np.array([[1, 0, -1], [1, 0, -1], [1, 0, -1]]), -1),
            borderType=cv.BORDER_CONSTANT,
        )
        grady = cv.filter2D(
            greyimg,
            cv.CV_8U,
            cv.flip(np.array([[1, 1, 1], [0, 0, 0], [-1, -1, -1]]), -1),
            borderType=cv.BORDER_CONSTANT,
        )

    log("showing image")

    plt.subplot(1, 4, 1)
    plt.imshow(inputimg)
    plt.title(f"Input Image")

    plt.subplot(1, 4, 2)
    plt.imshow(greyimg, cmap=plt.cm.gray)
    plt.title(f"Greyscale Image")

    plt.subplot(1, 4, 3)
    entimg = (
        np.bitwise_or(gradx, grady)
        if not realgrad
        else (
            gradx + grady
            if not concave
            else np.invert(np.array(gradx + grady, dtype=int))
        )
    )

    log(f"gradient = {np.average(entimg)} ± {np.std(entimg)}")
    plt.imshow(entimg, cmap=plt.cm.gray)
    plt.title(f"Gradient")

    refimg = cv.imread("ref/barbara.png")
    plt.subplot(1, 4, 4)
    plt.imshow(refimg, cmap=plt.cm.gray)
    plt.title("Reference Map")

    plt.show()


def method_delentropy():
    usecv = True

    if usecv:
        inputimg = cv.imread(args.input)
        greyimg = cv.cvtColor(inputimg, cv.COLOR_BGR2GRAY).astype(int)
    else:
        inputimg = imageio.imread(args.input).astype(int)
        greyimg = imageio.imread(args.input, pilmode="L").astype(int)

    ### 1609.01117 page 10

    # $\nabla f(n) \approx f(n) - f(n - 1)$
    fx = greyimg[:, 2:] - greyimg[:, :-2]
    fy = greyimg[2:, :] - greyimg[:-2, :]

    # fix shape
    fx = fx[1:-1, :]
    fy = fy[:, 1:-1]

    # TODO: is this how fx and fy are combined? (it's for plotting and not used in computation anyways)
    gradimg = fx + fy

    # ensure $-255 \leq J \leq 255$
    jrng = np.max([np.max(np.abs(fx)), np.max(np.abs(fy))])
    assert jrng <= 255

    ### 1609.01117 page 16

    nbins = 2 * jrng + 1
    hist, edgex, edgey = np.histogram2d(
        fx.flatten(),
        fy.flatten(),
        bins=nbins,
        range=[[-jrng, jrng], [-jrng, jrng]],
    )

    deldensity = hist / np.sum(hist)
    entimg = deldensity * np.ma.log2(deldensity)
    entimg /= 2  # 4.3 Papoulis generalized sampling halves the delentropy
    entropy = -np.sum(entimg)

    # TODO: entropy is different from `sipp`, but similar
    log(f"entropy: {entropy}")

    plt.subplot(2, 3, 1)
    plt.imshow(inputimg, cmap=plt.cm.gray)
    plt.title(f"Image")

    plt.subplot(2, 3, 2)
    plt.imshow(greyimg, cmap=plt.cm.gray)
    plt.title(f"Greyscale Image")

    # the reference image seems to be bitwise inverted, I don't know why
    gradimg = np.invert(gradimg)
    plt.subplot(2, 3, 3)
    plt.imshow(gradimg, cmap=plt.cm.gray)
    plt.title(f"Gradient")

    refimg = cv.imread("ref/barbara.png")
    plt.subplot(2, 3, 4)
    plt.imshow(refimg, cmap=plt.cm.gray)
    plt.title("Reference")

    # TODO: deldensity seems *mostly* zero, is this normal?
    plt.subplot(2, 3, 5)
    plt.imshow(deldensity, cmap=plt.cm.gray)
    plt.colorbar()
    plt.title(f"Deldensity")

    plt.subplot(2, 3, 6)
    plt.imshow(np.abs(entimg))
    plt.colorbar()
    plt.title(f"Delentropy")

    plt.show()


def main():
    # don't hurt eyes
    plt.style.use("dark_background")

    if args.method == "pseudo-spatial":
        method_pseudo_spatial()
    elif args.method == "2d-delentropy":
        method_delentropy()
    elif args.method == "2d-gradient":
        method_gradient()


def argtypemethod(val):
    if val != "pseudo-spatial" and val != "2d-delentropy" and val != "2d-gradient":
        raise argparse.ArgumentTypeError(f"{val} is not a valid method.")
    return val


def argtypekernelsize(val):
    ival = int(val)
    if ival <= 1 or ival % 2 != 1:
        raise argparse.ArgumentTypeError(f"{ival} is not a valid kernel size.")
    return ival


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Image Entropy")

    parser.add_argument("-i", "--input", help="path to input image file", type=str)
    parser.add_argument(
        "-k",
        "--kernel-size",
        help="kernel size. must be a positive odd integer. (default: 11, minimum: 3)",
        type=argtypekernelsize,
        default=11,
    )
    parser.add_argument(
        "-m",
        "--method",
        help="method to use. possible values: pseudo-spatial, 2d-delentropy, 2d-gradient (default: 2d-delentropy)",
        type=argtypemethod,
        default="2d-delentropy",
    )
    # parser.add_argument("files", help="paths to input image files", nargs="*")

    args = parser.parse_args()

    execname = argv[0]

    main()
