import json
import os
import sys

PATH_TO_SCOPE_FOUNDRY = ""
FILE_OUTPUT_NAME = "flake_data.json"

def do_sht(params):
    #2dmatgmm

    # Output json with flake data into scope foundry path
    with open(os.path.join(PATH_TO_SCOPE_FOUNDRY, FILE_OUTPUT_NAME)) as file:
        json.dump([1, 2, 3], file)


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
        do_sht(params)
    except Exception as e:
        print(f"Failed to load or process parameter file: {e}", file=sys.stderr)
        sys.exit(1)
    
    