import json
import sys
import os
import cv2
from pathlib import Path

PATH_TO_SCOPE_FOUNDRY = Path("C:/Users/Darcey/Documents/scopefoundry_apps/monark-2d-qmap-director/Measurements/Catalog/2DMatGMM_connector")
FILE_OUTPUT_NAME = Path("flake_data.json")

from GMMDetector import MaterialDetector
from copied_from_app.image_processing import remove_vignette, calculate_background_color, check_median_background
from copied_from_app.Parameters import Parameters

MODEL_DIR = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "Models")

def make_parameters(params: dict):
    parameters = Parameters()
    for key in params.keys():
        match key:
            case "size_threshold":
                parameters.size_threshold = params["size_threshold"]
            case "min_confidence":
                parameters.min_confidence = params["min_confidence"]
                # Minimum confidence filter is not currently applied in the detection
            case "use_flatfield":
                parameters.use_flatfield = params["use_flatfield"]
            case "flatfield_path":
                parameters.flatfield_path = params["flatfield_path"]

    return parameters

def run_detector_on_folder(params: dict):
    # Interpret parameter dictionary
    if "images_dir" in params.keys():
        images_dir = params["images_dir"]
        if not os.path.isdir():
            print("Warning: Image directory invalid. Exiting 2DMatGMM.")
            return
    else:
        print("Warning: No image directory provided. Exiting 2DMatGMM.")
        return

    if "material" in params.keys():
        material = params["material"]
    else:
        material = "N/A"
    
    if "model_file_name" in params.keys():
        model_name = params["model_file_name"]
    else:
        print("Warning: No model file name provided. Exiting 2DMatGMM.")
        return

    parameters = make_parameters(params)
    
    output = run_model_on_folder(
        images_dir,
        model_name,
        parameters.size_threshold,
        parameters.min_confidence,
        parameters.use_flatfield,
        parameters.flatfield_path
    )

    flake_data: dict = {
        "flakes": [flake.to_database_dict(output[flake], material) for flake in output],
        "parameters": params,
    }

    # Output json with flake data into scope foundry path
    with open(PATH_TO_SCOPE_FOUNDRY / FILE_OUTPUT_NAME, "w") as file:
        json.dump(flake_data, file, indent=4)
        
    print(f"Saved flake data to {PATH_TO_SCOPE_FOUNDRY / FILE_OUTPUT_NAME}")


def run_model_on_folder(
    images_dir: Path,
    model_name,
    size_threshold: int = 500,
    min_confidence: float = 0.0,  # Filter for min confidence is not implemented. Could just remove.
    use_flatfield: bool = False,
    flatfield_path: str = "",
):
    """ Run. Works on individual images files saved in a folder (not TIFF stack files) """
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

        if image_path.endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
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
    

def run_detector_on_image(params: dict):
    # Interpret parameter dictionary
    if "image_path" in params.keys():
        image_path: Path = params["image_path"]
        if not image_path.exists():
            print("Warning: Image path invalid. Exiting 2DMatGMM.")
            return
    else:
        print("Warning: No image path provided. Exiting 2DMatGMM.")
        return

    if "material" in params.keys():
        material = params["material"]
    else:
        material = "N/A"
    
    if "model_file_name" in params.keys():
        model_name = params["model_file_name"]
    else:
        print("Warning: No model file name provided. Exiting 2DMatGMM.")
        return

    parameters = make_parameters(params)
    
    output = run_model_on_image(
        image_path,
        model_name,
        parameters.size_threshold,
        parameters.min_confidence,
        parameters.use_flatfield,
        parameters.flatfield_path
    )

    flake_data: dict = {
        "flakes": [flake.to_database_dict(output[flake], material) for flake in output],
        "parameters": params,
    }

    # Output json with flake data into scope foundry path
    with open(PATH_TO_SCOPE_FOUNDRY / FILE_OUTPUT_NAME, "w") as file:
        json.dump(flake_data, file, indent=4)
        
    print(f"Saved flake data to {PATH_TO_SCOPE_FOUNDRY / FILE_OUTPUT_NAME}")


def run_model_on_image(
    image_path,
    model_name,
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

    all_flakes = {}
    name = os.path.basename(image_path)


    if image_path.endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
        image = cv2.imread(image_path)
    else: 
        message = f"Unsupported image format for {name}. Skipping."
        print(message)
        return

    # Remove vignette if necessary
    if use_flatfield:
        image = remove_vignette(image, flatfield)
    
        # Check if the image background is not the substrate color (requires a flatfield)
        flatfield_color = calculate_background_color(flatfield, 10)
        if not check_median_background(image, flatfield_color):
            print(f"Image {name} background color does not match flatfield. Skipping.")
            return


    flakes = model.detect_flakes(image)
    for flake in flakes:
        all_flakes[flake] = name  # Store the flake with its image name

    if len(flakes) == 0:
        print(f"No flakes detected in {name}. Skipping.")
        return
        
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
        run_detector_on_image(params)
    except Exception as e:
        print(f"Failed to load or process parameter file: {e}", file=sys.stderr)
        sys.exit(1)