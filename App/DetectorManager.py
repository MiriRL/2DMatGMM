import os
import json
import cv2
import time
import numpy as np

from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QProgressBar, QHBoxLayout, QWidget, QLabel, QPushButton

from GMMDetector import MaterialDetector
from Parameters import Parameters
from App.image_processing import visualise_flakes, remove_vignette, calculate_background_color, check_median_background


MODEL_DIR = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "Models")

class DetectorManager(QWidget):

    def __init__(self, debugging_label: QLabel, run_button: QPushButton, parent = None):
        super().__init__(parent)

        self.progress_text = QLabel()
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(500)
        self.debugging_label = debugging_label
        self.run_button = run_button

        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.debugging_label)
        progress_layout.addWidget(self.progress_text)
        progress_layout.addWidget(self.progress_bar)
        self.setLayout(progress_layout)
        self.setVisible(False)


    def run_detector(self, gmm_file_name, images_dir, parameters: Parameters, current_user):
        """ Calls the 2DMatGMM detector as shown in the demo.\n

        gmm_file_name: name of the constrast model parameters json file. Should be stored in the Models folder.\n
        images_dir: Directory path to the folder containing the images to be run through the model. Should be in __png__ format.\n
        parameters: an instance of the Parameters class, which stores all the parameters that can be adjusted when running the detector.
        """

        self.setVisible(True)
        self.run_button.setEnabled(False)
        self.gmm_file_name = gmm_file_name
        self.images_dir = images_dir
        self.parameters = parameters
        self.curr_user = current_user
        self.all_flakes = {} # A dictionary to store all the flakes detected in the images, with their file names as values.

        # Create a folder to save the images in
        database_dir = Path(os.path.join(self.images_dir, "..", "2DMatGMMoutput"))
        if self.parameters.save_to_database:
            database_dir = Path.home() / "Box" / "Quantum Device Lab" / "External Optical Cataloger"
            if not database_dir.exists():
                message = f"{database_dir} not found. Defaulting to local directory."
                self.debugging_label.setText(message)
                database_dir = Path(os.path.join(self.images_dir, "..", "2DMatGMMoutput"))
                raise ModuleNotFoundError(message)
            
        # Make a folder name based off the current date/time and model/material
        # If no user is selected, use only the current date/time as the folder name
        if self.curr_user is None:
            new_folder_name = time.strftime("%Y-%m-%d_%H-%M-%S")
        else:
            new_folder_name = f"{self.curr_user}_{time.strftime('%Y-%m-%d_%H-%M-%S')}"
        self.folder_path = database_dir / new_folder_name
        self.folder_path.mkdir(parents=True, exist_ok=True)

        # Load the trained parameters
        gmm_file_path = os.path.join(MODEL_DIR, gmm_file_name)
        if not os.path.exists(gmm_file_path):
            message = f"Parameter file {gmm_file_name} does not exist in {MODEL_DIR}"
            self.debugging_label.setText(message)
            raise FileNotFoundError(message)
        contrast_dict = json.load(open(gmm_file_path, "r"))
        
        self.model: MaterialDetector = None
        try:
            self.model = MaterialDetector(
                contrast_dict=contrast_dict,
                size_threshold=parameters.get_size(),
                standard_deviation_threshold=5,
                used_channels="BGR",
            )
        except Exception as e:
            message = f"Failed to initialize MaterialDetector: {e}"
            self.debugging_label.setText(message)
            print(message)
            return

        if parameters.use_flatfield:
            self.flatfield = cv2.imread(parameters.flatfield_path)
            if self.flatfield is None:
                message = f"Could not load flatfield image from: {parameters.flatfield_path}"
                self.debugging_label.setText(message)
                raise ValueError(message)

        self.image_file_names = os.listdir(images_dir)
        self.images = []
        self.image_names = []

        if ".DS_Store" in self.image_file_names:
            self.image_file_names.remove(".DS_Store")
            print("Removed .DS_Store from image names list.")
        
        self.total_images = len(self.image_file_names)
        self.curr_idx = 0

        self.progress_text.setText(str(0) + " / " + str(self.total_images) + " images prepared")
        self.progress_bar.setRange(0, self.total_images)
        self.progress_bar.setValue(0)
        self.debugging_label.setText("Unpacking and preparing images.")

        QTimer.singleShot(0, self.prepare_images)
            

    def prepare_images(self):
        if self.curr_idx >= len(self.image_file_names):
            self.curr_idx = 0
            self.total_images = len(self.images)

            self.debugging_label.setText("Processing images.")
            self.progress_text.setText(str(0) + " / " + str(self.total_images) + " images processed")
            self.progress_bar.setRange(0, self.total_images)
            self.progress_bar.setValue(0)

            QTimer.singleShot(0, self.run_image)
            return

        image_name = self.image_file_names[self.curr_idx]
        image_path = os.path.join(self.images_dir, image_name)

        match image_path:
            case str() if image_path.endswith((".png", ".jpg", ".jpeg")):
                image = cv2.imread(image_path)
                self.images.append(image)
                self.image_names.append(image_name)
            case str() if image_path.endswith((".tif", ".tiff")):
                message = f"Reading TIFF image {image_name}..."
                print(message)
                self.debugging_label.setText(message)
                # Use cv2.imreadmulti to read multi-page TIFF images
                success, images_list = cv2.imreadmulti(image_path, [])
                img_count = 0
                if success:
                    for img in images_list:
                        self.images.append(img)
                        self.image_names.append(f"{img_count}_" + image_name)
                        img_count += 1
                else:
                    message = f"Failed to read TIFF image {image_name}. Skipping."
                    self.debugging_label.setText(message)
                    print(message)
            case _:
                message = f"Unsupported image format for {image_name}. Skipping."
                self.debugging_label.setText(message)
                print(message)
        
        self.curr_idx += 1
        self.progress_text.setText(str(self.curr_idx) + " / " + str(self.total_images) + " images processed")
        self.progress_bar.setValue(self.curr_idx)
        QTimer.singleShot(0, self.prepare_images)



    def run_image(self):
        if self.curr_idx >= self.total_images:
            self.save_flake_data()
            self.run_button.setEnabled(True)
            self.debugging_label.setText("")
            self.progress_text.setText("Process complete.")
            self.progress_bar.setValue(self.total_images)
            print("Finished")
            return
        
        image = self.images[self.curr_idx]
        image_name = self.image_names[self.curr_idx]

        # Remove vignette if necessary
        if self.parameters.use_flatfield:
            image = remove_vignette(image, self.flatfield)
        
            # Check if the image background is not the substrate color (requires a flatfield)
            flatfield_color = calculate_background_color(self.flatfield, 10)
            if not check_median_background(image, flatfield_color, radius=10):
                print(f"Image {image_name} background color does not match flatfield. Skipping.")

                # For debugging purposes, you can save the image and see what is skipped
                # cv2.imwrite(os.path.join(self.folder_path, "skipped_" + image_name), image)
                
                # Move to the next image
                self.curr_idx += 1
                self.progress_text.setText(str(self.curr_idx) + " / " + str(self.total_images) + " images processed")
                self.progress_bar.setValue(self.curr_idx)
                QTimer.singleShot(0, self.run_image)
                return


        flakes = self.model.detect_flakes(image)
        for flake in flakes:
            self.all_flakes[flake] = image_name  # Store the flake with its image name
        # blank_image = image.copy()

        if len(flakes) == 0:
            print(f"No flakes detected in {image_name}. Skipping.")
        else:
            image = visualise_flakes(
                flakes,
                image,
                confidence_threshold=self.parameters.min_confidence,
            )
            # Save the processed image with detected flakes
            
            try:
                cv2.imwrite(os.path.join(self.folder_path, "detected_" + image_name), image)
            except Exception as e:
                message = f"OpenCV write failed: {e}"
                self.debugging_label.setText(message)
                print(message)

            print(f"Processed {image_name} with {len(flakes)} flakes detected.")

        # Update progress
        self.curr_idx += 1

        self.progress_text.setText(str(self.curr_idx) + " / " + str(self.total_images) + " images processed")
        self.progress_bar.setValue(self.curr_idx)
        QTimer.singleShot(0, self.run_image)


    def save_flake_data(self):
        """ Saves the detected flakes to a JSON file in the output folder. """
        if not self.all_flakes:
            message = "No flakes detected. Skipping saving."
            self.debugging_label.setText(message)
            print(message)
            return
        
        #TODO: Add another method to check material
        flake_data: dict = {
            "flakes": [flake.to_database_dict(self.all_flakes[flake], "Graphene") for flake in self.all_flakes],
            "parameters": self.parameters.to_dict(),
        }

        output_file_path = self.folder_path / "flakes_data.json"
        with open(output_file_path, "w") as f:
            json.dump(flake_data, f, indent=4)

        print(f"Saved flake data to {output_file_path}")