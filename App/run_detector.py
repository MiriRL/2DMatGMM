import os
import json
import cv2

from GMMDetector import MaterialDetector
from demo_functions import visualise_flakes, remove_vignette
from Parameters import Parameters


MODEL_DIR = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "Models")


def run_algorithm(gmm_file_name, images_dir, parameters: Parameters):
    """ Calls the 2DMatGMM detector as shown in the demo.\n

    gmm_file_name: name of the constrast model parameters json file. Should be stored in the Models folder.\n
    images_dir: Directory path to the folder containing the images to be run through the model. Should be in __png__ format.\n
    parameters: an instance of the Parameters class, which stores all the parameters that can be adjusted when running the detector.
    """
    # Load the trained parameters
    gmm_file_path = os.path.join(MODEL_DIR, gmm_file_name)
    if not os.path.exists(gmm_file_path):
        raise FileNotFoundError(f"Parameter file {gmm_file_name} does not exist in {MODEL_DIR}")

    contrast_dict = json.load(open(gmm_file_path, "r"))
    # TODO: add options to change the size threshold
    model = MaterialDetector(
        contrast_dict=contrast_dict,
        size_threshold=parameters.get_size(),
        standard_deviation_threshold=5,
        used_channels="BGR",
    )

    # TODO: add options to change the confidence threshold

    # TODO: add flatfield correction option
    if parameters.use_flatfield:
        flatfield = cv2.imread(parameters.flatfield_path)

    image_names = os.listdir(images_dir)
    for image_name in image_names:
        if image_name == ".DS_Store":  # If it's the .DS_store file we skip this file and continue with the next images
            continue
        image_path = os.path.join(images_dir, image_name)
        image = cv2.imread(image_path)
        
        # Remove vignette if necessary
        if parameters.use_flatfield:
            image = remove_vignette(image, flatfield)

        flakes = model.detect_flakes(image)

        image = visualise_flakes(
            flakes,
            image,
            confidence_threshold=parameters.min_confidence,
        )
        # Save the processed image with detected flakes
        cv2.imwrite(os.path.join(images_dir, "detected_" + image_name), image)
        print(f"Processed {image_name} with {len(flakes)} flakes detected.")
        print(os.path.join(images_dir, "detected_" + image_name))