import json
import subprocess
import time
import traceback
from pathlib import Path


BASE_DIR = Path(r"C:\ANSYS_AI")

INPUT_FILE = BASE_DIR / "simulation_input.json"

SCRIPTS_DIR = BASE_DIR / "scripts"

RESULTS_DIR = BASE_DIR / "results"

RESULTS_FILE = RESULTS_DIR / "analysis_results.txt"

STATUS_FILE = RESULTS_DIR / "simulation_status.txt"

ERROR_FILE = RESULTS_DIR / "simulation_error.txt"

WB_SCRIPT = SCRIPTS_DIR / "dynamic_simulation.wbjn"

ANSYS_WORKBENCH = Path(
    r"C:\Program Files\ANSYS Inc\ANSYS Student\v261\Framework\bin\Win64\RunWB2.exe"
)


# ============================================================
# INPUT
# ============================================================

def load_input():

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Simulation input not found: {INPUT_FILE}"
        )

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ============================================================
# VALIDATION
# ============================================================

def validate_input(data):

    required = [
        "shape",
        "length_mm",
        "material",
        "mesh_size_mm",
        "analysis_type"
    ]

    for key in required:

        if key not in data:

            raise ValueError(
                f"Required parameter missing: {key}"
            )


    shape = str(
        data["shape"]
    ).strip().lower()


    length = float(
        data["length_mm"]
    )


    mesh = float(
        data["mesh_size_mm"]
    )


    if not shape:

        raise ValueError(
            "Geometry shape cannot be empty."
        )


    if length <= 0:

        raise ValueError(
            "Length must be greater than zero."
        )


    if mesh <= 0:

        raise ValueError(
            "Mesh size must be greater than zero."
        )


    if shape in [
        "cylinder",
        "rod",
        "cylindrical rod"
    ]:

        if "diameter_mm" not in data:

            raise ValueError(
                "diameter_mm is required for cylindrical geometry."
            )


        diameter = float(
            data["diameter_mm"]
        )


        if diameter <= 0:

            raise ValueError(
                "Diameter must be greater than zero."
            )


    elif shape in [
        "beam",
        "box",
        "block",
        "rectangular",
        "rectangular beam"
    ]:

        if "width_mm" not in data:

            raise ValueError(
                "width_mm is required for rectangular geometry."
            )


        if "height_mm" not in data:

            raise ValueError(
                "height_mm is required for rectangular geometry."
            )


        width = float(
            data["width_mm"]
        )

        height = float(
            data["height_mm"]
        )


        if width <= 0:

            raise ValueError(
                "Width must be greater than zero."
            )


        if height <= 0:

            raise ValueError(
                "Height must be greater than zero."
            )


    else:

        raise ValueError(
            f"Unsupported geometry shape: {data['shape']}"
        )


    analysis_type = str(
        data["analysis_type"]
    ).strip().lower()


    if "thermal" in analysis_type:

        if (
            "temperature_c" not in data
            and
            "temperature_difference_c" not in data
        ):

            raise ValueError(
                "Thermal analysis requires temperature_c "
                "or temperature_difference_c."
            )


        if (
            "temperature_difference_c" in data
            and
            "reference_temperature_c" not in data
        ):

            raise ValueError(
                "temperature_difference_c requires "
                "reference_temperature_c."
            )


        if "temperature_c" in data:

            float(
                data["temperature_c"]
            )


        if "reference_temperature_c" not in data:

            raise ValueError(
                "Thermal stress analysis requires "
                "reference_temperature_c."
            )


        float(
            data["reference_temperature_c"]
        )


    return True


# ============================================================
# SAFE STRING FOR WORKBENCH JOURNAL
# ============================================================

def wb_string(value):

    return repr(
        str(value)
    )


# ============================================================
# CREATE GEOMETRY COMMAND
# ============================================================

def create_geometry_code(data):

    shape = str(
        data["shape"]
    ).strip().lower()


    length = float(
        data["length_mm"]
    )


    diameter = float(
        data.get(
            "diameter_mm",
            0
        )
    )


    width = float(
        data.get(
            "width_mm",
            0
        )
    )


    height = float(
        data.get(
            "height_mm",
            0
        )
    )


    if shape in [
        "cylinder",
        "rod",
        "cylindrical rod"
    ]:

        radius = diameter / 2.0


        return f"""
ClearAll()

start_point = Point.Create(
    MM(0),
    MM(0),
    MM(0)
)

end_point = Point.Create(
    MM({length}),
    MM(0),
    MM(0)
)

radius_point = Point.Create(
    MM({length}),
    MM({radius}),
    MM(0)
)

result = CylinderBody.Create(
    start_point,
    end_point,
    radius_point,
    ExtrudeType.ForceIndependent
)

body = result.CreatedBodies[0]

body.SetName("AI_Cylinder")

ViewHelper.ZoomToEntity()
"""


    if shape in [
        "beam",
        "box",
        "block",
        "rectangular",
        "rectangular beam"
    ]:

        return f"""
ClearAll()

point1 = Point.Create(
    MM(0),
    MM(0),
    MM(0)
)

point2 = Point.Create(
    MM({length}),
    MM({width}),
    MM({height})
)

result = BlockBody.Create(
    point1,
    point2,
    ExtrudeType.ForceIndependent
)

body = result.CreatedBodies[0]

body.SetName("AI_Rectangular_Body")

ViewHelper.ZoomToEntity()
"""


    raise ValueError(
        f"Unsupported geometry shape: {shape}"
    )


# ============================================================
# MECHANICAL THERMAL CODE
# ============================================================

def create_thermal_mechanical_code(data):

    material = str(
        data["material"]
    )

    mesh = float(
        data["mesh_size_mm"]
    )

    fixed_support = bool(
        data.get(
            "fixed_support",
            False
        )
    )

    temperature = data.get(
        "temperature_c",
        None
    )

    temperature_difference = data.get(
        "temperature_difference_c",
        None
    )

    reference_temperature = data.get(
        "reference_temperature_c",
        None
    )


    if temperature is not None:

        applied_temperature = float(
            temperature
        )

    else:

        applied_temperature = (
            float(reference_temperature)
            +
            float(temperature_difference)
        )


    material_q = wb_string(
        material
    )


    return f"""
import traceback

try:

    print("======================================")
    print("THERMAL MECHANICAL AUTOMATION STARTED")
    print("======================================")


    model = ExtAPI.DataModel.Project.Model

    analysis = model.Analyses[0]


    # --------------------------------------------------------
    # GET BODY
    # --------------------------------------------------------

    geo = ExtAPI.DataModel.GeoData

    body = geo.Assemblies[0].Parts[0].Bodies[0]


    print(
        "BODY FOUND:",
        body.Name
    )


    # --------------------------------------------------------
    # MATERIAL
    # --------------------------------------------------------

    body.Material = {material_q}

    print(
        "MATERIAL:",
        body.Material
    )


    # --------------------------------------------------------
    # END FACES
    # --------------------------------------------------------

    faces = body.Faces

    fixed_face = None

    heated_face = None

    minimum_x = 1.0e30

    maximum_x = -1.0e30


    for face in faces:

        x = float(
            face.Centroid[0]
        )


        if x < minimum_x:

            minimum_x = x

            fixed_face = face


        if x > maximum_x:

            maximum_x = x

            heated_face = face


    if fixed_face is None:

        raise Exception(
            "Could not find fixed end face."
        )


    if heated_face is None:

        raise Exception(
            "Could not find heated end face."
        )


    print(
        "FIXED FACE ID:",
        fixed_face.Id
    )


    print(
        "HEATED FACE ID:",
        heated_face.Id
    )


    # --------------------------------------------------------
    # MESH
    # --------------------------------------------------------

    mesh_object = model.Mesh

    mesh_object.ElementSize = Quantity(
        "{mesh} [mm]"
    )

    mesh_object.GenerateMesh()


    print(
        "MESH GENERATED:",
        "{mesh} mm"
    )


    # --------------------------------------------------------
    # TEMPERATURE
    # --------------------------------------------------------

    temperature_selection = (
        ExtAPI.SelectionManager.CreateSelectionInfo(
            SelectionTypeEnum.GeometryEntities
        )
    )


    temperature_selection.Ids = [
        heated_face.Id
    ]


    thermal_temperature = analysis.AddTemperature()

    thermal_temperature.Location = (
        temperature_selection
    )


    thermal_temperature.Magnitude.Output.DiscreteValues = [
        Quantity(
            "{applied_temperature} [C]"
        )
    ]


    print(
        "TEMPERATURE APPLIED:",
        "{applied_temperature} C"
    )


    # --------------------------------------------------------
    # THERMAL RESULT
    # --------------------------------------------------------

    thermal_solution = analysis.Solution

    temperature_result = (
        thermal_solution.AddTemperature()
    )


    # --------------------------------------------------------
    # SOLVE THERMAL
    # --------------------------------------------------------

    print(
        "STARTING THERMAL SOLVE..."
    )


    analysis.Solve(
        True
    )


    print(
        "THERMAL SOLVE COMPLETED."
    )


    temperature_result.EvaluateAllResults()


    thermal_max = (
        temperature_result.Maximum.Value
    )


    print(
        "MAXIMUM TEMPERATURE:",
        thermal_max
    )


    # --------------------------------------------------------
    # SAVE THERMAL PROJECT
    # --------------------------------------------------------

    ExtAPI.DataModel.Project.Save()


    print(
        "THERMAL ANALYSIS FINISHED."
    )


    with open(
        "C:/ANSYS_AI/results/thermal_status.txt",
        "w"
    ) as f:

        f.write(
            "THERMAL SOLVE COMPLETED\\\\n"
        )

        f.write(
            "Maximum Temperature: "
            + str(thermal_max)
            + "\\\\n"
        )


except Exception as e:

    error_text = (
        "THERMAL MECHANICAL ERROR\\\\n\\\\n"
        +
        str(e)
        +
        "\\\\n\\\\n"
        +
        traceback.format_exc()
    )


    with open(
        "C:/ANSYS_AI/results/simulation_error.txt",
        "w"
    ) as f:

        f.write(
            error_text
        )


    print(
        error_text
    )

    raise
"""


# ============================================================
# MECHANICAL STRUCTURAL CODE
# ============================================================

def create_structural_mechanical_code(data):

    material = str(
        data["material"]
    )

    mesh = float(
        data["mesh_size_mm"]
    )

    fixed_support = bool(
        data.get(
            "fixed_support",
            False
        )
    )

    load = float(
        data.get(
            "load_n",
            0
        )
    )

    direction = str(
        data.get(
            "load_direction",
            "Z"
        )
    ).upper()

    reference_temperature = float(
        data["reference_temperature_c"]
    )


    material_q = wb_string(
        material
    )


    return f"""
import traceback

try:

    print("======================================")
    print("STRUCTURAL MECHANICAL AUTOMATION START")
    print("======================================")


    model = ExtAPI.DataModel.Project.Model

    analysis = model.Analyses[0]


    # --------------------------------------------------------
    # BODY
    # --------------------------------------------------------

    geo = ExtAPI.DataModel.GeoData

    body = geo.Assemblies[0].Parts[0].Bodies[0]


    print(
        "STRUCTURAL BODY:",
        body.Name
    )


    # --------------------------------------------------------
    # MATERIAL
    # --------------------------------------------------------

    body.Material = {material_q}

    body.ThermalStrainEffects = True

    body.UseReferenceTemperatureByBody = True

    body.ReferenceTemperatureValue = Quantity(
        "{reference_temperature} [C]"
    )


    print(
        "STRUCTURAL MATERIAL:",
        body.Material
    )


    print(
        "REFERENCE TEMPERATURE:",
        "{reference_temperature} C"
    )


    # --------------------------------------------------------
    # FACES
    # --------------------------------------------------------

    faces = body.Faces

    fixed_face = None

    load_face = None

    minimum_x = 1.0e30

    maximum_x = -1.0e30


    for face in faces:

        x = float(
            face.Centroid[0]
        )


        if x < minimum_x:

            minimum_x = x

            fixed_face = face


        if x > maximum_x:

            maximum_x = x

            load_face = face


    if fixed_face is None:

        raise Exception(
            "Could not identify fixed face."
        )


    if load_face is None:

        raise Exception(
            "Could not identify load face."
        )


    # --------------------------------------------------------
    # FIXED SUPPORT
    # --------------------------------------------------------

    if {str(fixed_support)}:

        fixed_selection = (
            ExtAPI.SelectionManager.CreateSelectionInfo(
                SelectionTypeEnum.GeometryEntities
            )
        )


        fixed_selection.Ids = [
            fixed_face.Id
        ]


        fixed_support_object = (
            analysis.AddFixedSupport()
        )


        fixed_support_object.Location = (
            fixed_selection
        )


        print(
            "FIXED SUPPORT APPLIED."
        )


    # --------------------------------------------------------
    # OPTIONAL MECHANICAL LOAD
    # --------------------------------------------------------

    if {load} != 0:

        load_selection = (
            ExtAPI.SelectionManager.CreateSelectionInfo(
                SelectionTypeEnum.GeometryEntities
            )
        )


        load_selection.Ids = [
            load_face.Id
        ]


        force = analysis.AddForce()

        force.Location = load_selection

        force.DefineBy = LoadDefineBy.Components


        if "{direction}" == "X":

            force.XComponent.Output.DiscreteValues = [
                Quantity(
                    "{load} [N]"
                )
            ]


        elif "{direction}" == "Y":

            force.YComponent.Output.DiscreteValues = [
                Quantity(
                    "{load} [N]"
                )
            ]


        else:

            force.ZComponent.Output.DiscreteValues = [
                Quantity(
                    "{load} [N]"
                )
            ]


        print(
            "MECHANICAL LOAD:",
            "{load} N",
            "DIRECTION:",
            "{direction}"
        )


    else:

        print(
            "NO MECHANICAL FORCE APPLIED."
        )


    # --------------------------------------------------------
    # MESH
    # --------------------------------------------------------

    mesh_object = model.Mesh

    mesh_object.ElementSize = Quantity(
        "{mesh} [mm]"
    )

    mesh_object.GenerateMesh()


    print(
        "STRUCTURAL MESH GENERATED:",
        "{mesh} mm"
    )


    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    solution = analysis.Solution


    total_deformation = (
        solution.AddTotalDeformation()
    )


    equivalent_stress = (
        solution.AddEquivalentStress()
    )


    thermal_strain = (
        solution.AddThermalStrain()
    )


    # --------------------------------------------------------
    # SOLVE
    # --------------------------------------------------------

    print(
        "STARTING STRUCTURAL SOLVE..."
    )


    analysis.Solve(
        True
    )


    print(
        "STRUCTURAL SOLVE COMPLETED."
    )


    # --------------------------------------------------------
    # EVALUATE
    # --------------------------------------------------------

    total_deformation.EvaluateAllResults()

    equivalent_stress.EvaluateAllResults()

    thermal_strain.EvaluateAllResults()


    maximum_deformation = (
        total_deformation.Maximum.Value
    )


    maximum_stress = (
        equivalent_stress.Maximum.Value
    )


    maximum_thermal_strain = (
        thermal_strain.Maximum.Value
    )


    print(
        "MAXIMUM TOTAL DEFORMATION:",
        maximum_deformation
    )


    print(
        "MAXIMUM EQUIVALENT STRESS:",
        maximum_stress
    )


    print(
        "MAXIMUM THERMAL STRAIN:",
        maximum_thermal_strain
    )


    # --------------------------------------------------------
    # WRITE RESULTS
    # --------------------------------------------------------

    with open(
        "C:/ANSYS_AI/results/analysis_results.txt",
        "w"
    ) as f:


        f.write(
            "ANSYS AI AUTOMATION RESULTS\\\\n"
        )


        f.write(
            "===========================\\\\n"
        )


        f.write(
            "Analysis Type: Thermal-Stress\\\\n"
        )


        f.write(
            "Material: {material}\\\\n"
        )


        f.write(
            "Mesh Size: {mesh} mm\\\\n"
        )


        f.write(
            "Reference Temperature: "
            + str({reference_temperature})
            + " C\\\\n"
        )


        f.write(
            "Mechanical Load: "
            + str({load})
            + " N\\\\n"
        )


        f.write(
            "Load Direction: "
            + "{direction}"
            + "\\\\n"
        )


        f.write(
            "Maximum Total Deformation: "
            + str(maximum_deformation)
            + "\\\\n"
        )


        f.write(
            "Maximum Equivalent Stress: "
            + str(maximum_stress)
            + "\\\\n"
        )


        f.write(
            "Maximum Thermal Strain: "
            + str(maximum_thermal_strain)
            + "\\\\n"
        )


    ExtAPI.DataModel.Project.Save()


    with open(
        "C:/ANSYS_AI/results/simulation_status.txt",
        "w"
    ) as f:

        f.write(
            "SIMULATION COMPLETED\\\\n"
        )


        f.write(
            "Maximum Total Deformation: "
            + str(maximum_deformation)
            + "\\\\n"
        )


        f.write(
            "Maximum Equivalent Stress: "
            + str(maximum_stress)
            + "\\\\n"
        )


    print(
        "STRUCTURAL RESULTS SAVED."
    )


except Exception as e:

    error_text = (
        "STRUCTURAL MECHANICAL ERROR\\\\n\\\\n"
        +
        str(e)
        +
        "\\\\n\\\\n"
        +
        traceback.format_exc()
    )


    with open(
        "C:/ANSYS_AI/results/simulation_error.txt",
        "w"
    ) as f:

        f.write(
            error_text
        )


    print(
        error_text
    )

    raise
"""


# ============================================================
# CREATE WORKBENCH JOURNAL
# ============================================================

def create_workbench_script(data):

    analysis_type = str(
        data["analysis_type"]
    ).strip().lower()


    is_thermal = (
        "thermal" in analysis_type
    )


    geometry_code = create_geometry_code(
        data
    )


    geometry_command = repr(
        geometry_code
    )


    if is_thermal:

        thermal_code = (
            create_thermal_mechanical_code(
                data
            )
        )


        structural_code = (
            create_structural_mechanical_code(
                data
            )
        )


        thermal_command = repr(
            thermal_code
        )


        structural_command = repr(
            structural_code
        )


        return f'''# encoding: utf-8

SetScriptVersion(
    Version="26.1"
)

Reset()


# ============================================================
# CREATE THERMAL-STRESS PROJECT
# ============================================================

project_template = GetProjectTemplate(
    Name="Thermal-Stress"
)

project_template.CreateProject()


# ============================================================
# GET THERMAL SYSTEM
# ============================================================

thermal_system = GetSystem(
    Name="Steady-State Thermal (ANSYS)"
)


# ============================================================
# GET STRUCTURAL SYSTEM
# ============================================================

structural_system = GetSystem(
    Name="Static Structural (ANSYS)"
)


# ============================================================
# CREATE GEOMETRY IN THERMAL SYSTEM
# ============================================================

thermal_geometry = thermal_system.GetContainer(
    ComponentName="Geometry"
)

thermal_geometry.Edit(
    IsSpaceClaimGeometry=True
)

thermal_geometry.SendCommand(
    Language="Python",
    Command={geometry_command}
)

thermal_geometry.Exit()


# ============================================================
# REFRESH SHARED MODEL
# ============================================================

thermal_model_component = thermal_system.GetComponent(
    Name="Model"
)

thermal_model_component.Refresh()


structural_model_component = structural_system.GetComponent(
    Name="Model"
)

structural_model_component.Refresh()


# ============================================================
# THERMAL MECHANICAL SETUP
# ============================================================

thermal_model = thermal_system.GetContainer(
    ComponentName="Model"
)

thermal_model.Edit(
    Interactive=True
)

thermal_model.SendCommand(
    Language="Python",
    Command={thermal_command}
)


# ============================================================
# REFRESH STRUCTURAL SETUP
# ============================================================

structural_setup = structural_system.GetComponent(
    Name="Setup"
)

structural_setup.Refresh()


# ============================================================
# STRUCTURAL MECHANICAL SETUP
# ============================================================

structural_model = structural_system.GetContainer(
    ComponentName="Model"
)

structural_model.Edit(
    Interactive=True
)

structural_model.SendCommand(
    Language="Python",
    Command={structural_command}
)


# ============================================================
# SAVE PROJECT
# ============================================================

Save(
    FilePath="C:/ANSYS_AI/results/ansys_ai_dynamic.wbpj",
    Overwrite=True
)

print(
    "THERMAL-STRESS WORKFLOW COMPLETED."
)
'''


    else:

        structural_code = (
            create_structural_mechanical_code(
                data
            )
        )


        structural_command = repr(
            structural_code
        )


        return f'''# encoding: utf-8

SetScriptVersion(
    Version="26.1"
)

Reset()


# ============================================================
# CREATE STATIC STRUCTURAL SYSTEM
# ============================================================

template = GetTemplate(
    TemplateName="Static Structural",
    Solver="ANSYS"
)

system = template.CreateSystem()


# ============================================================
# ENGINEERING DATA
# ============================================================

engineering_data = system.GetContainer(
    ComponentName="Engineering Data"
)

engineering_data.ImportMaterial(
    Name={wb_string(data["material"])},
    Source="General_Materials.xml"
)


# ============================================================
# GEOMETRY
# ============================================================

geometry = system.GetContainer(
    ComponentName="Geometry"
)

geometry.Edit(
    IsSpaceClaimGeometry=True
)

geometry.SendCommand(
    Language="Python",
    Command={repr(geometry_code)}
)

geometry.Exit()


# ============================================================
# MODEL
# ============================================================

model_component = system.GetComponent(
    Name="Model"
)

model_component.Refresh()


model = system.GetContainer(
    ComponentName="Model"
)

model.Edit(
    Interactive=True
)

model.SendCommand(
    Language="Python",
    Command={structural_command}
)


# ============================================================
# SAVE
# ============================================================

Save(
    FilePath="C:/ANSYS_AI/results/ansys_ai_dynamic.wbpj",
    Overwrite=True
)

print(
    "STATIC STRUCTURAL WORKFLOW COMPLETED."
)
'''


# ============================================================
# RUN WORKBENCH
# ============================================================

def start_workbench():

    startupinfo = subprocess.STARTUPINFO()

    startupinfo.dwFlags |= (
        subprocess.STARTF_USESHOWWINDOW
    )

    startupinfo.wShowWindow = (
        subprocess.SW_HIDE
    )


    process = subprocess.Popen(
        [
            str(ANSYS_WORKBENCH),
            "-I",
            "-R",
            str(WB_SCRIPT)
        ],
        cwd=str(
            ANSYS_WORKBENCH.parent
        ),
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW
    )


    return process


# ============================================================
# WAIT FOR RESULT
# ============================================================

def wait_for_result(process):

    print(
        f"ANSYS Workbench started. PID: {process.pid}"
    )

    print(
        "Waiting for ANSYS simulation to finish..."
    )


    timeout_seconds = 1800

    start_time = time.time()


    while True:

        if ERROR_FILE.exists():

            print(
                "ANSYS simulation reported an error."
            )

            return False


        if RESULTS_FILE.exists():

            print(
                "ANSYS results file created."
            )

            return True


        if STATUS_FILE.exists():

            print(
                STATUS_FILE.read_text(
                    encoding="utf-8"
                )
            )


        if process.poll() is not None:

            if RESULTS_FILE.exists():

                return True


            if ERROR_FILE.exists():

                return False


        elapsed = (
            time.time()
            -
            start_time
        )


        if elapsed > timeout_seconds:

            print(
                "ANSYS simulation timeout."
            )

            return False


        time.sleep(2)


# ============================================================
# MAIN
# ============================================================

def main():

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    RESULTS_FILE.unlink(
        missing_ok=True
    )


    STATUS_FILE.unlink(
        missing_ok=True
    )


    ERROR_FILE.unlink(
        missing_ok=True
    )


    try:

        data = load_input()


        validate_input(
            data
        )


        print(
            "Input validated."
        )


        print(
            json.dumps(
                data,
                indent=4
            )
        )


        script = create_workbench_script(
            data
        )


        WB_SCRIPT.write_text(
            script,
            encoding="utf-8"
        )


        print(
            "Workbench journal created:"
        )


        print(
            WB_SCRIPT
        )


        if not ANSYS_WORKBENCH.exists():

            raise FileNotFoundError(
                f"ANSYS Workbench not found: "
                f"{ANSYS_WORKBENCH}"
            )


        process = start_workbench()


        success = wait_for_result(
            process
        )


        if not success:

            print(
                "ANSYS simulation failed."
            )


            if ERROR_FILE.exists():

                print(
                    ERROR_FILE.read_text(
                        encoding="utf-8"
                    )
                )

            return


        print(
            "======================================"
        )

        print(
            "ANSYS SIMULATION COMPLETED"
        )

        print(
            "======================================"
        )


        print(
            RESULTS_FILE.read_text(
                encoding="utf-8"
            )
        )


    except Exception:

        error_text = (
            "PYTHON AUTOMATION ERROR\n\n"
            +
            traceback.format_exc()
        )


        ERROR_FILE.write_text(
            error_text,
            encoding="utf-8"
        )


        print(
            error_text
        )


if __name__ == "__main__":

    main()