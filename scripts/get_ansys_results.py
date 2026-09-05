from pathlib import Path
import re

RESULT_FILE = Path(
    r"C:\ANSYS_AI\results\analysis_results.txt"
)

if not RESULT_FILE.exists():
    print("ERROR: ANSYS result file not found.")
    raise SystemExit(1)

text = RESULT_FILE.read_text()

deformation_match = re.search(
    r"Maximum Total Deformation:\s*([0-9.eE+-]+)",
    text
)

stress_match = re.search(
    r"Maximum Equivalent Stress:\s*([0-9.eE+-]+)",
    text
)

if not deformation_match:
    print("ERROR: Deformation result not found.")
    raise SystemExit(1)

if not stress_match:
    print("ERROR: Stress result not found.")
    raise SystemExit(1)

deformation_m = float(deformation_match.group(1))
stress_pa = float(stress_match.group(1))

deformation_mm = deformation_m * 1000
stress_mpa = stress_pa / 1_000_000

print()
print("ANSYS AUTOMATION RESULTS")
print("========================")
print(f"Maximum Total Deformation: {deformation_mm:.6f} mm")
print(f"Maximum Equivalent Stress: {stress_mpa:.6f} MPa")