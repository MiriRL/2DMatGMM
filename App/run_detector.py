import os

from GMMDetector import MaterialDetector
# from demo.demo_functions import visualise_flakes

MODEL_DIR = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "Model")

def run_algorithm(parameter_file_name, images_dir):
    print(os.path.join(MODEL_DIR, parameter_file_name))
    print(images_dir)