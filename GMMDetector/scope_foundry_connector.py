import json
import sys
import os
import cv2
from pathlib import Path

PATH_TO_SCOPE_FOUNDRY = Path("C:/Users/Darcey/Documents/scopefoundry_apps/monark-2d-qmap-director/Measurements/Catalog/2DMatGMM_connector")
FILE_OUTPUT_NAME = Path("flake_data.json")

from GMMDetector import MaterialDetector
from Parameters import Parameters
from demo_functions import visualise_flakes, remove_vignette, calculate_background_color, check_median_background

MODEL_DIR = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "Models")

def run_detector(params):
    # Interpret parameter dictionary
    images_dir = params["images_dir"]
    material = params["material"]
    model_name = params["model_file_name"]

    size_threshold = params["size_threshold"]
    min_confidence = params["min_confidence"]

    use_flatfield = params["use_flatfield"]
    flatfield_path = params["flatfield_path"]
    
    output = run_model(
        images_dir,
        model_name,
        size_threshold,
        min_confidence,
        use_flatfield,
        flatfield_path
    )

    flake_data: dict = {
        "flakes": [flake.to_database_dict(output[flake], material) for flake in output],
        "parameters": params,
    }

    # Output json with flake data into scope foundry path
    with open(PATH_TO_SCOPE_FOUNDRY / FILE_OUTPUT_NAME, "w") as file:
        json.dump(flake_data, file, indent=4)
        
    print(f"Saved flake data to {PATH_TO_SCOPE_FOUNDRY / FILE_OUTPUT_NAME}")


def run_model(
    images_dir: Path,
    model_name: str = None,
    size_threshold: int = 500,
    min_confidence: float = 0.0,
    use_flatfield: bool = False,
    flatfield_path: str = "",
):
    """ Run. Works on individual images files (not TIFF stack files) """
    # Load the trained parameters
    gmm_file_path = os.path.join(MODEL_DIR, model_name)
    if not os.path.exists(gmm_file_path):
        message = f"Parameter file {model_name} does not exist in {MODEL_DIR}"
        raise FileNotFoundError(message)
    contrast_dict = json.load(open(gmm_file_path, "r"))
    
    model: MaterialDetector = None
    try:
        model = MaterialDetector(
            contrast_dict=contrast_dict,
            size_threshold=size_threshold,
            standard_deviation_threshold=5,
            used_channels="BGR",
        )
    except Exception as e:
        message = f"Failed to initialize MaterialDetector: {e}"
        print(message)
        return

    if use_flatfield:
        flatfield = cv2.imread(flatfield_path)
        if flatfield is None:
            message = f"Could not load flatfield image from: {flatfield_path}"
            raise ValueError(message)

    image_file_names = os.listdir(images_dir)
    all_flakes = {}
    
    for name in image_file_names:
        image_path = os.path.join(images_dir, name)

        if image_path.endswith((".png", ".jpg", ".jpeg")):
            image = cv2.imread(image_path)
        else: 
            message = f"Unsupported image format for {name}. Skipping."
            print(message)
            continue

        # Remove vignette if necessary
        if use_flatfield:
            image = remove_vignette(image, flatfield)
        
            # Check if the image background is not the substrate color (requires a flatfield)
            flatfield_color = calculate_background_color(flatfield, 10)
            if not check_median_background(image, flatfield_color):
                print(f"Image {name} background color does not match flatfield. Skipping.")
                continue


        flakes = model.detect_flakes(image)
        for flake in flakes:
            all_flakes[flake] = name  # Store the flake with its image name

        if len(flakes) == 0:
            print(f"No flakes detected in {name}. Skipping.")
            continue
            
        print(f"Processed {name} with {len(flakes)} flakes detected.")

    return all_flakes
        

if __name__ == "__main__":
    # The info and parameters temp file name should be included when this is called
    if len(sys.argv) < 2:
        print("Expected parameter JSON file path", file=sys.stderr)
        sys.exit(1)

    # Get the parameters from the temp json file
    param_file = sys.argv[1]

    try:
        with open(param_file, "r") as f:
            params = json.load(f)
        run_detector(params)
    except Exception as e:
        print(f"Failed to load or process parameter file: {e}", file=sys.stderr)
        sys.exit(1)
    
    