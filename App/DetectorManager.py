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
            self.model = MaterialDetector(
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
            self.flatfield = cv2.imread(parameters.flatfield_path)
            if self.flatfield is None:
                raise ValueError(f"Could not load flatfield image from: {parameters.flatfield_path}")

        self.image_file_names = os.listdir(images_dir)
        self.images = []
        self.image_names = []

        # Update Progress Bar Maximum
        if ".DS_Store" in self.image_file_names:
            self.image_file_names.remove(".DS_Store")
            print("Removed .DS_Store from image names list.")
        

        for image_name in self.image_file_names:
            image_path = os.path.join(self.images_dir, image_name)
            if image_path.endswith(".png" or ".jpg" or ".jpeg"):
                image = cv2.imread(image_path)
                self.images.append(image)
                self.image_names.append(image_name)
            elif image_path.endswith(".tif" or ".tiff"):
                print(f"Reading multi-page TIFF image {image_name}...")
                # Use cv2.imreadmulti to read multi-page TIFF images
                success, images_list = cv2.imreadmulti(image_path, [])
                img_count = 0
                if success:
                    for img in images_list:
                        self.images.append(img)
                        self.image_names.append(f"{img_count}_" + image_name)
                        img_count += 1
                else:
                    print(f"Failed to read TIFF image {image_name}. Skipping.")
            else:
                print(f"Unsupported image format for {image_name}. Skipping.")
        
        self.total_images = len(self.images)
        self.curr_idx = 0

        self.progress_text.setText(str(0) + " / " + str(self.total_images) + " images processed")
        self.progress_bar.setRange(0, self.total_images)
        self.progress_bar.setValue(0)

        QTimer.singleShot(0, self.run_image)
            

    def run_image(self):
        if self.curr_idx >= self.total_images:
            self.progress_text.setText("Process complete.")
            print("Finished")
            return
        
        image = self.images[self.curr_idx]
        image_name = self.image_names[self.curr_idx]

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
            cv2.imwrite(os.path.join(self.images_dir, "..", "output", "detected_" + image_name), image)
        except Exception as e:
            print(f"OpenCV write failed: {e}")

        print(f"Processed {image_name} with {len(flakes)} flakes detected.")
        print(os.path.join(self.images_dir, "detected_" + image_name))

        # Update progress
        self.curr_idx += 1

        self.progress_text.setText(str(self.curr_idx) + " / " + str(self.total_images) + " images processed")
        self.progress_bar.setValue(self.curr_idx)
        QTimer.singleShot(0, self.run_image)


