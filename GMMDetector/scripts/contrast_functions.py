import cv2
import numpy as np
import os

from App.demo_functions import calculate_background_color, remove_vignette

def get_contrasts_from_img(
    image_path,
    mask_path,
    flatfield_path=None,
    use_flatfield=True,
):
    contrasts = []

    if use_flatfield and flatfield_path is not None:
        flatfield = cv2.imread(flatfield_path)
        assert (
            flatfield is not None
        ), f"Could not load flatfield at '{flatfield_path}', have you selected the correct path?"

    mask_name = os.path.basename(mask_path)

    
    print(f"{mask_name} read", end="\r")

    # check if the image is either in the png or jpg format
    if not os.path.exists(image_path):
        print(f"Could not find image corresponding to mask '{mask_name}', skipping")

    mask = cv2.imread(mask_path, 0)
    image = cv2.imread(image_path)

    assert mask is not None, f"Could not load mask {mask_path}"
    assert image is not None, f"Could not load image {image_path}"

    mask = cv2.erode(
        mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), iterations=1
    )

    # If the mask is empty, skip this image
    if cv2.countNonZero(mask) < 10:
        return None

    if use_flatfield and flatfield_path is not None:
        image = remove_vignette(image, flatfield)

    flake_color = np.array(image[mask != 0])
    if use_flatfield and flatfield_path is not None:
        background_color = np.array(calculate_background_color(flatfield, 10))
    else:
        background_color = np.array(calculate_background_color(image, 10))

    if np.any(background_color == 0):
        print(f"Error with image {mask_name}; Invalid Background, skipping")
        return None

    flake_contrast = (flake_color / background_color) - 1

    contrasts.extend(flake_contrast)

    contrasts = np.array(contrasts)

    return contrasts