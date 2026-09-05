from mcp.server import MCPServer
import subprocess
import sys
from pathlib import Path
import json

mcp = MCPServer(
    "ANSYS AI",
    instructions="""
You are an engineering simulation agent connected to ANSYS Workbench.

When the user requests an ANSYS simulation, extract the required
geometry, dimensions, material, loads, supports, mesh settings,
analysis type, and requested results from the user's prompt.

Never use fixed engineering values.
Pass the user's requested values to the ANSYS automation.
"""
)

BASE_DIR = Path(r"C:\ANSYS_AI")
SCRIPTS_DIR = BASE_DIR / "scripts"
INPUT_FILE = BASE_DIR / "simulation_input.json"
RESULTS_FILE = BASE_DIR / "results" / "analysis_results.txt"


@mcp.tool()
def run_ansys_simulation(
    shape: str,
    dimensions: dict,
    material: str,
    loads: list,
    supports: list,
    analysis_type: str = "Static Structural",
    mesh_size: float = 5,
    requested_results: list = None
) -> str:
    """
    Create and run an ANSYS simulation from user supplied
    engineering parameters.

    No geometry, load, material or dimension is fixed.
    """

    simulation = {
        "shape": shape,
        "dimensions": dimensions,
        "material": material,
        "loads": loads,
        "supports": supports,
        "analysis_type": analysis_type,
        "mesh_size": mesh_size,
        "requested_results": requested_results or [
            "Total Deformation",
            "Equivalent Stress"
        ]
    }

    INPUT_FILE.write_text(
        json.dumps(simulation, indent=4),
        encoding="utf-8"
    )

    script = SCRIPTS_DIR / "create_ansys_project.py"

    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        cwd=str(BASE_DIR)
    )

    if result.returncode != 0:
        return (
            "ANSYS automation failed.\n\n"
            + result.stderr
        )

    if not RESULTS_FILE.exists():
        return (
            "ANSYS started, but the results file "
            "was not found."
        )

    return RESULTS_FILE.read_text(
        encoding="utf-8"
    )


@mcp.tool()
def get_ansys_results() -> str:
    """Read the latest ANSYS simulation results."""

    if not RESULTS_FILE.exists():
        return "No ANSYS results found."

    return RESULTS_FILE.read_text(
        encoding="utf-8"
    )


if __name__ == "__main__":
    mcp.run()