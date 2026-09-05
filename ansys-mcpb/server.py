from mcp.server import MCPServer
import subprocess
from pathlib import Path
import json


mcp = MCPServer(
    "ANSYS AI",
    instructions="""
    You are an AI engineering simulation agent connected to ANSYS Workbench.

    Use the parameters supplied by the user.

    The user can specify:
    geometry shape,
    dimensions,
    material,
    loads,
    load direction,
    supports,
    mesh size,
    analysis type,
    and requested results.

    Never assume fixed engineering dimensions when the user provides different values.
    Never use a hardcoded simulation setup.
    """
)


BASE_DIR = Path(r"C:\ANSYS_AI")

SCRIPTS_DIR = BASE_DIR / "scripts"

RESULTS_DIR = BASE_DIR / "results"

RESULTS_FILE = RESULTS_DIR / "analysis_results.txt"

INPUT_FILE = BASE_DIR / "simulation_input.json"

CREATE_SCRIPT = SCRIPTS_DIR / "create_ansys_project.py"


ANSYS_PATH = Path(
    r"C:\Program Files\ANSYS Inc\ANSYS Student\v261\Framework\bin\Win64\RunWB2.exe"
)


def run_hidden(command, cwd):

    startupinfo = subprocess.STARTUPINFO()

    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    startupinfo.wShowWindow = subprocess.SW_HIDE

    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=str(cwd),
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW
    )


@mcp.tool()
def run_ansys_simulation(
    shape: str,
    length_mm: float = 0,
    diameter_mm: float = 0,
    width_mm: float = 0,
    height_mm: float = 0,
    material: str = "Structural Steel",
    load_n: float = 0,
    load_direction: str = "Z",
    mesh_size_mm: float = 5,
    analysis_type: str = "Static Structural"
) -> str:

    """
    Run an ANSYS simulation using parameters supplied by the AI.

    The AI determines the simulation parameters from the user's
    engineering request.
    """

    if not shape.strip():

        return "ERROR: Geometry shape was not provided."


    if not CREATE_SCRIPT.exists():

        return (
            "ERROR: ANSYS automation script not found.\n"
            f"Expected location:\n{CREATE_SCRIPT}"
        )


    if not ANSYS_PATH.exists():

        return (
            "ERROR: ANSYS Workbench was not found.\n"
            f"Expected location:\n{ANSYS_PATH}"
        )


    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    simulation_input = {

        "shape": shape,

        "length_mm": length_mm,

        "diameter_mm": diameter_mm,

        "width_mm": width_mm,

        "height_mm": height_mm,

        "material": material,

        "load_n": load_n,

        "load_direction": load_direction,

        "mesh_size_mm": mesh_size_mm,

        "analysis_type": analysis_type
    }


    INPUT_FILE.write_text(

        json.dumps(
            simulation_input,
            indent=4
        ),

        encoding="utf-8"
    )


    try:

        result = run_hidden(

            [
                "python",
                str(CREATE_SCRIPT)
            ],

            BASE_DIR
        )


    except Exception as e:

        return (
            "ERROR while starting ANSYS automation:\n"
            f"{e}"
        )


    if result.returncode != 0:

        return (

            "ANSYS automation failed.\n\n"

            f"STDOUT:\n"
            f"{result.stdout}\n\n"

            f"STDERR:\n"
            f"{result.stderr}"
        )


    if not RESULTS_FILE.exists():

        return (

            "ANSYS automation finished, "
            "but the results file was not found.\n\n"

            f"Expected:\n"
            f"{RESULTS_FILE}\n\n"

            f"Automation output:\n"
            f"{result.stdout}"
        )


    return RESULTS_FILE.read_text(
        encoding="utf-8"
    )


@mcp.tool()
def get_ansys_results() -> str:

    """
    Read the latest ANSYS simulation results.
    """

    if not RESULTS_FILE.exists():

        return "No ANSYS results found."


    try:

        return RESULTS_FILE.read_text(
            encoding="utf-8"
        )


    except Exception as e:

        return (
            "ERROR reading ANSYS results:\n"
            f"{e}"
        )


@mcp.tool()
def check_ansys_connection() -> str:

    """
    Check whether ANSYS Workbench is installed
    and available.
    """

    if ANSYS_PATH.exists():

        return (

            "ANSYS connection check passed.\n"

            f"ANSYS Workbench found at:\n"
            f"{ANSYS_PATH}"
        )


    return (

        "ANSYS connection check failed.\n"

        f"ANSYS Workbench was not found at:\n"
        f"{ANSYS_PATH}"
    )


if __name__ == "__main__":

    mcp.run()