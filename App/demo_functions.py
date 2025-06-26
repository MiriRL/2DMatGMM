import cv2
import matplotlib.cm as cm
import numpy as np


def visualise_flakes(
    flakes,
    image: np.ndarray,
    confidence_threshold: float = 0.5,
) -> np.ndarray:
    """Visualise the flakes on the image.

    Args:
        flakes (List[Flake]): List of flakes to visualise.
        image (np.ndarray): Image to visualise the flakes on.
        confidence_threshold (float, optional): The confidence threshold to use, flakes with less confidence are not drawn. Defaults to 0.5.

    Returns:
        np.ndarray: Image with the flakes visualised.
    """

    confident_flakes = [
        flake
        for flake in flakes
        if (1 - flake.false_positive_probability) > confidence_threshold
    ]

    # get a colors for each flake
    colors = cm.rainbow(np.linspace(0, 1, len(confident_flakes)))[:, :3] * 255

    image = image.copy()
    for idx, flake in enumerate(confident_flakes):
        flake_contour = cv2.morphologyEx(
            flake.mask, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)
        )
        image[flake_contour > 0] = colors[idx]

        # put the text on the top right corner of the image
        cv2.putText(
            image,
            f"{(idx + 1):2}. {flake.thickness:1}L {int(flake.size):4}pixels {1- flake.false_positive_probability:.0%}",
            (10, 30 * (idx + 1)),
            cv2.QT_FONT_NORMAL,
            1,
            (255, 255, 255),
            2,
        )

        # draw a line from the text to the center of the flake
        cv2.line(
            image,
            (370, 30 * (idx + 1) - 15),
            (int(flake.center[0]), int(flake.center[1])),
            colors[idx],
            2,
        )

    return image


def remove_vignette(
    image,
    flatfield,
    max_background_value: int = 241,
):
    """Removes the Vignette from the Image

    Args:
        image (NxMx3 Array): The Image with the Vignette
        flatfield (NxMx3 Array): the Flat Field in RGB
        max_background_value (int): the maximum value of the background

    Returns:
        (NxMx3 Array): The Image without the Vignette
    """
    image_no_vigentte = image / flatfield * cv2.mean(flatfield)[:-1]
    image_no_vigentte[image_no_vigentte > max_background_value] = max_background_value
    return np.asarray(image_no_vigentte, dtype=np.uint8)


def calculate_background_color(img, radius=5):
    masks = []

    for i in range(3):
        img_channel = img[:, :, i]
        # Originally used a range (20, 230), but did not work with very bright/saturated backgrounds
        mask = cv2.inRange(img_channel, 0, 255)  # Accept all colors as possible background
        hist = cv2.calcHist([img_channel], [0], mask, [256], [0, 256])
        hist_mode = np.argmax(hist)
        thresholded_image = cv2.inRange(
            img_channel, int(hist_mode - radius), int(hist_mode + radius)
        )
        background_mask_channel = cv2.erode(
            thresholded_image, np.ones((3, 3)), iterations=3
        )
        masks.append(background_mask_channel)

    final_mask = cv2.bitwise_and(masks[0], masks[1])
    final_mask = cv2.bitwise_and(final_mask, masks[2])

    return cv2.mean(img, mask=final_mask)[:3]

def check_median_background(img, background_color, radius=10) -> bool:
    """Check if the median color of the image is close to the background color. """
    bg_color = np.array(background_color, dtype=np.uint8)
    range_array = np.array([radius] * 3, dtype=np.uint8)

    # Define lower and upper bounds
    lower_bound = np.clip(bg_color - range_array, 0, 255)
    upper_bound = np.clip(bg_color + range_array, 0, 255)

    # Create mask where pixels are within the color range
    mask = cv2.inRange(img, lower_bound, upper_bound)

    # Count matching pixels
    total_pixels = img.shape[0] * img.shape[1]
    matching_pixels = cv2.countNonZero(mask)

    # Check if matching pixels exceed 60%
    return (matching_pixels / total_pixels) > 0.6

