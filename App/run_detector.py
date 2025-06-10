import os
import json
import cv2

from GMMDetector import MaterialDetector
from demo_functions import visualise_flakes


MODEL_DIR = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "Models")

def run_algorithm(parameter_file_name, images_dir):
    # Load the trained parameters
    parameter_file_path = os.path.join(MODEL_DIR, parameter_file_name)
    if not os.path.exists(parameter_file_path):
        raise FileNotFoundError(f"Parameter file {parameter_file_name} does not exist in {MODEL_DIR}")

    contrast_dict = json.load(open(parameter_file_path, "r"))
    # TODO: add options to change the size threshold
    model = MaterialDetector(
        contrast_dict=contrast_dict,
        size_threshold=1000,
        standard_deviation_threshold=5,
        used_channels="BGR",
    )

    # TODO: add options to change the confidence threshold
    CONFIDENCE_THRESHOLD = 0.0

    # TODO: add flatfield correction option
    # flatfield = cv2.imread("flatfield.png")

    image_names = os.listdir(images_dir)
    for image_name in image_names:
        image_path = os.path.join(images_dir, image_name)
        image = cv2.imread(image_path)
        
        # Remove vignette if necessary
        # image = remove_vignette(image, flatfield)

        flakes = model.detect_flakes(image)

        image = visualise_flakes(
            flakes,
            image,
            confidence_threshold=CONFIDENCE_THRESHOLD,
        )
        # Save the processed image with detected flakes
        cv2.imwrite(os.path.join(images_dir, "detected_" + image_name), image)
        print(f"Processed {image_name} with {len(flakes)} flakes detected.")
        print(os.path.join(images_dir, "detected_" + image_name))