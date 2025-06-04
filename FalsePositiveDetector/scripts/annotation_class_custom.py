import os

import cv2
import numpy as np
import json


class false_positive_annotator:
    def __init__(self, annotated_image_directory, model_directory):
        self.marks_updated = False

        self.annotated_image_directory = annotated_image_directory
        self.model_directory = model_directory
        self.annotated_image_names = [
            name
            for name in os.listdir(self.annotated_image_directory)
            if (name.endswith(".png") or name.endswith(".jpg"))
        ]
        self.annotated_image_paths = [
            os.path.join(self.annotated_image_directory, name) for name in self.annotated_image_names
        ]

        self.annotations = []  # dictionary that will be converted to the annotations json

        assert os.path.exists(
            self.annotated_image_directory
        ), "Mask directory does not exist or the path is incorrect."
        assert os.path.exists(
            self.model_directory
        ), "Model directory does not exist or the path is incorrect."

    def run(self, current_idx=0):
        self.current_idx = current_idx

        self.current_mask_path = self.annotated_image_paths[current_idx]
        self.current_mask = cv2.imread(self.current_mask_path)

        # Clears the current flake from the annotations list
        def clear_annotation():
            self.annotations.pop(self.current_mask_path)

        def update_current_image():
            self.current_image = cv2.imread(self.current_mask_path)

        cv2.namedWindow("Annotator", cv2.WINDOW_NORMAL)

        cv2.setWindowTitle("Annotator", self.current_mask_path)

        while True:
            # Check if a mask already exists for the current image
            is_annotated = os.path.exists(
                os.path.join(self.annotated_image_directory, self.annotated_image_names[current_idx])
            )
            window_title = f"{self.current_mask_path} | {current_idx + 1 }/{len(self.image_paths)}"

            if is_annotated:
                window_title += (" | Mask exists")

            cv2.imshow("Annotator", self.current_image_display)
            cv2.setWindowTitle(
                "Annotator",
                window_title,
            )

            key = cv2.waitKey(10)

            if key == 27:
                break

            elif key == ord("c"):
                clear_marks()

            if key == ord("s"):
                mask = np.zeros(self.current_image.shape[:2], dtype=np.uint8)
                mask[marker_image_copy == 1] = 255
                cv2.imwrite(
                    os.path.join(self.annotated_image_directory, self.image_names[current_idx]),
                    mask,
                )

            if key == ord("d"):
                if current_idx < len(self.image_paths) - 1:
                    current_idx += 1
                    update_current_image()

            if key == ord("a"):
                if current_idx > 0:
                    current_idx -= 1
                    update_current_image()

            # If we clicked somewhere, call the watershed algorithm on our chosen markers
            if self.marks_updated:
                self.current_image_display = self.current_image_marked.copy()
                marker_image_copy = self.marker_image.copy()

                # run the watershed algorithm with the chosen markers
                cv2.watershed(self.current_image, marker_image_copy)

                # create a mask of the watershed segments
                self.watershed_segments = np.zeros(
                    self.current_image.shape, dtype=np.uint8
                )
                self.watershed_segments[marker_image_copy == 1] = [0, 0, 255]
                self.watershed_segments[marker_image_copy == 2] = 0

                self.watershed_segments = cv2.morphologyEx(
                    self.watershed_segments,
                    cv2.MORPH_GRADIENT,
                    np.ones((3, 3), dtype=np.uint8),
                )

                self.current_image_display = cv2.addWeighted(
                    self.current_image_display, 1, self.watershed_segments, 1, 0
                )

                self.marks_updated = False

        cv2.destroyAllWindows()
