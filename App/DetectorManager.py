import os
import json
import cv2

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QProgressBar, QHBoxLayout, QWidget

from GMMDetector import MaterialDetector
from Parameters import Parameters
from demo_functions import visualise_flakes, remove_vignette


MODEL_DIR = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "Models")

class DetectorManager(QWidget):

    def __init__(self, parent = None):
        super().__init__(parent)

        self.progress_text = QLabel()
        self.progress_bar = QProgressBar()
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(self.progress_text)
        progress_layout.addWidget(self.progress_bar)
        self.setLayout(progress_layout)
        self.setVisible(False)


    def run_detector(self, gmm_file_name, images_dir, parameters: Parameters):
        """ Calls the 2DMatGMM detector as shown in the demo. Runs in a seperate thread so the UI can update.\n

        gmm_file_name: name of the constrast model parameters json file. Should be stored in the Models folder.\n
        images_dir: Directory path to the folder containing the images to be run through the model. Should be in __png__ format.\n
        parameters: an instance of the Parameters class, which stores all the parameters that can be adjusted when running the detector.
        """

        self.setVisible(True)
        self.gmm_file_name = gmm_file_name
        self.images_dir = images_dir
        self.parameters = parameters

        # Load the trained parameters
        gmm_file_path = os.path.join(MODEL_DIR, gmm_file_name)
        if not os.path.exists(gmm_file_path):
            raise FileNotFoundError(f"Parameter file {gmm_file_name} does not exist in {MODEL_DIR}")
        contrast_dict = json.load(open(gmm_file_path, "r"))
        
        # TODO: add options to change the size threshold
        self.model: MaterialDetector = None
        try:
            model = MaterialDetector(
                contrast_dict=contrast_dict,
                size_threshold=parameters.get_size(),
                standard_deviation_threshold=5,
                used_channels="BGR",
            )
        except Exception as e:
            print(f"Failed to initialize MaterialDetector: {e}")
            return

        # TODO: add options to change the confidence threshold

        # TODO: add flatfield correction option
        if parameters.use_flatfield:
            flatfield = cv2.imread(parameters.flatfield_path)
            if flatfield is None:
                raise ValueError(f"Could not load flatfield image from: {parameters.flatfield_path}")

        self.image_names = os.listdir(images_dir)

        # Update Progress Bar Maximum
        self.total_idx = len(self.image_names)
        self.curr_idx = 0
        self.total_images = self.total_idx

        if ".DS_Store" in self.image_names:
            self.total_images -= 1
        self.progress_text.setText(str(0) + " / " + str(self.total_images) + " images processed")
        self.progress_bar.setRange(0, self.total_images)
        self.progress_bar.setValue(0)
            

    def run_image(self):
        if self.curr_idx > self.total_idx:
            return

        image_name = self.image_names[self.curr_idx]


        if image_name == ".DS_Store":  # If it's the .DS_store file, we skip this file and continue with the next images
            return
        image_path = os.path.join(self.images_dir, image_name)
        image = cv2.imread(image_path)
        
        # Remove vignette if necessary
        if self.parameters.use_flatfield:
            image = remove_vignette(image, self.flatfield)

        flakes = self.model.detect_flakes(image)

        image = visualise_flakes(
            flakes,
            image,
            confidence_threshold=self.parameters.min_confidence,
        )
        # Save the processed image with detected flakes
        try:
            cv2.imwrite(os.path.join(self.images_dir, "detected_" + image_name), image)
        except Exception as e:
            print(f"OpenCV write failed: {e}")

        print(f"Processed {image_name} with {len(flakes)} flakes detected.")
        print(os.path.join(self.images_dir, "detected_" + image_name))

        # Update progress
        self.curr_idx += 1

        self.progress_text.setText(str(self.curr_idx) + " / " + str(self.total_images) + " images processed")
        self.progress_bar.setValue(self.curr_idx)
        QTimer.singleShot(0, self.run_image)


