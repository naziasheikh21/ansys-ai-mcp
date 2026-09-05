import subprocess
from pathlib import Path

ANSYS_WORKBENCH = Path(
    r"C:\Program Files\ANSYS Inc\ANSYS Student\v261\Framework\bin\Win64\RunWB2.exe"
)

if not ANSYS_WORKBENCH.exists():
    print("ERROR: ANSYS Workbench was not found.")
    print(ANSYS_WORKBENCH)
    raise SystemExit(1)

print("ANSYS Workbench found.")
print(f"Path: {ANSYS_WORKBENCH}")

print("Starting ANSYS Workbench...")

subprocess.Popen([str(ANSYS_WORKBENCH)])

print("ANSYS Workbench launch command sent successfully.")