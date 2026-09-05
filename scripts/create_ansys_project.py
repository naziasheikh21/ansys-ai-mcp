import json
import subprocess
import time
import traceback
from pathlib import Path


BASE_DIR = Path(r"C:\ANSYS_AI")

INPUT_FILE = BASE_DIR / "simulation_input.json"
RESULTS_DIR = BASE_DIR / "results"

STATUS_FILE = RESULTS_DIR / "simulation_status.txt"
ERROR_FILE = RESULTS_DIR / "simulation_error.txt"

WB_SCRIPT = BASE_DIR / "scripts" / "cantilever_beam.wbjn"

ANSYS_WORKBENCH = Path(
    r"C:\Program Files\ANSYS Inc\ANSYS Student\v261\Framework\bin\Win64\RunWB2.exe"
)


def write_file(path, text):

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    path.write_text(
        str(text),
        encoding="utf-8"
    )


def load_input():

    with INPUT_FILE.open(
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def main():

    try:

        print()
        print("==========================================")
        print("ANSYS AI CANTILEVER BEAM")
        print("==========================================")
        print()

        RESULTS_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        write_file(
            STATUS_FILE,
            "STARTING"
        )

        data = load_input()

        print("INPUT:")
        print(
            json.dumps(
                data,
                indent=4
            )
        )

        print()
        print("Starting ANSYS Workbench...")
        print()

        process = subprocess.Popen(
            [
                str(ANSYS_WORKBENCH),
                "-I",
                "-R",
                str(WB_SCRIPT)
            ],
            cwd=str(
                ANSYS_WORKBENCH.parent
            )
        )

        print(
            "Workbench PID:",
            process.pid
        )

        write_file(
            STATUS_FILE,
            "WORKBENCH_RUNNING"
        )

        print()
        print("ANSYS Workbench launched.")
        print()
        print("Mechanical should open from Workbench.")
        print()
        print("DO NOT CLOSE ANSYS.")
        print()
        print("Your ANSYS result tab will be handled inside Mechanical.")
        print()

        while True:

            if process.poll() is not None:

                print()
                print(
                    "Workbench process ended."
                )

                break

            time.sleep(2)

    except KeyboardInterrupt:

        print()
        print("Controller stopped.")

    except Exception as error:

        error_text = (
            "PYTHON AUTOMATION ERROR\n\n"
            + type(error).__name__
            + ": "
            + str(error)
            + "\n\n"
            + traceback.format_exc()
        )

        write_file(
            ERROR_FILE,
            error_text
        )

        write_file(
            STATUS_FILE,
            "FAILED"
        )

        print(error_text)


if __name__ == "__main__":
    main()