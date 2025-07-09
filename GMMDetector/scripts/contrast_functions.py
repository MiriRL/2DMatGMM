import cv2
import numpy as np
import matplotlib.pyplot as plt
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
    background_color = np.array(calculate_background_color(image, 10))

    if np.any(background_color == 0):
        print(f"Error with image {mask_name}; Invalid Background, skipping")
        return None

    flake_contrast = (flake_color / background_color) - 1

    contrasts.extend(flake_contrast)

    contrasts = np.array(contrasts)

    return contrasts

def create_histogram_plots(image_contrast_dict):
    """
    Display RGB histograms stacked vertically above each image using OpenCV for image loading.

    Parameters:
    - image_contrast_dict (dict): A dictionary where keys are image file paths,
      and values are NumPy arrays of RGB values used for contrast analysis.
    """

    for image_path, contrast_data in image_contrast_dict.items():
        # Ensure data is a NumPy array
        contrast_data = np.asarray(contrast_data)

        # Load the image using cv2 (BGR by default), then convert to RGB
        image_bgr = cv2.imread(image_path)
        if image_bgr is None:
            print(f"Warning: Could not load image at {image_path}")
            continue
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        # Create figure with 4 vertically stacked plots (3 histograms + 1 image)
        fig, axs = plt.subplots(4, 1, figsize=(8, 10), gridspec_kw={'height_ratios': [1, 1, 1, 3]})
        fig.suptitle(f"Image and RGB Histograms", fontsize=14)

        # Channel info
        channel_colors = ['red', 'green', 'blue']
        channel_names = ['Red', 'Green', 'Blue']

        for i in range(3):
            axs[i].hist(contrast_data[:, i], bins=256, color=channel_colors[i], alpha=0.8)
            axs[i].set_ylabel(f'{channel_names[i]}')
            axs[i].set_xlim(0, 255)  # keep x-range fixed for RGB values
            axs[i].set_xticks([])
            axs[i].set_yticks([])  # Optional: remove this line if you want to see tick values


        # Show the image
        axs[3].imshow(image_rgb)
        axs[3].axis('off')

        plt.tight_layout()
        plt.subplots_adjust(top=0.92)  # Make room for title
        plt.show()