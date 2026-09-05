# ============================================================
# ANSYS AI CANTILEVER BEAM
# ANSYS MECHANICAL SCRIPT
# ============================================================

import traceback

RESULTS_FILE = r"C:\ANSYS_AI\results\analysis_results.txt"
STATUS_FILE = r"C:\ANSYS_AI\results\simulation_status.txt"
ERROR_FILE = r"C:\ANSYS_AI\results\simulation_error.txt"

try:

    print("==========================================")
    print("CANTILEVER MECHANICAL AUTOMATION")
    print("==========================================")

    # --------------------------------------------------------
    # GET MODEL
    # --------------------------------------------------------

    model = ExtAPI.DataModel.Project.Model

    print("MODEL FOUND")

    if len(model.Analyses) == 0:
        raise Exception("No analysis found.")

    analysis = model.Analyses[0]

    print("ANALYSIS FOUND:", analysis.Name)

    # --------------------------------------------------------
    # GET BODY
    # --------------------------------------------------------

    bodies = model.Geometry.GetChildren(
        DataModelObjectCategory.Body,
        True
    )

    if len(bodies) == 0:
        raise Exception("No body found.")

    body = bodies[0]

    print("BODY FOUND:", body.Name)

    # --------------------------------------------------------
    # GET FACES
    # --------------------------------------------------------

    faces = body.Faces

    if len(faces) == 0:
        raise Exception("No faces found.")

    print("FACE COUNT:", len(faces))

    # --------------------------------------------------------
    # FIND LEFT AND RIGHT END FACES
    # --------------------------------------------------------

    fixed_face = None
    load_face = None

    min_x = 999999999.0
    max_x = -999999999.0

    for face in faces:

        try:
            x = face.Centroid[0]
        except:
            continue

        if x < min_x:
            min_x = x
            fixed_face = face

        if x > max_x:
            max_x = x
            load_face = face

    if fixed_face is None:
        raise Exception("Fixed face not found.")

    if load_face is None:
        raise Exception("Load face not found.")

    print("FIXED FACE ID:", fixed_face.Id)
    print("LOAD FACE ID:", load_face.Id)

    # --------------------------------------------------------
    # FIXED SUPPORT
    # --------------------------------------------------------

    fixed_selection = ExtAPI.SelectionManager.CreateSelectionInfo(
        SelectionTypeEnum.GeometryEntities
    )

    fixed_selection.Ids = [fixed_face.Id]

    fixed_support = analysis.AddFixedSupport()

    fixed_support.Location = fixed_selection

    print("FIXED SUPPORT CREATED")

    # --------------------------------------------------------
    # FORCE
    # --------------------------------------------------------

    load_selection = ExtAPI.SelectionManager.CreateSelectionInfo(
        SelectionTypeEnum.GeometryEntities
    )

    load_selection.Ids = [load_face.Id]

    force = analysis.AddForce()

    force.Location = load_selection

    force.DefineBy = LoadDefineBy.Components

    force.YComponent.Output.DiscreteValues = [
        Quantity("-100 [N]")
    ]

    print("100 N FORCE CREATED")

    # --------------------------------------------------------
    # MESH
    # --------------------------------------------------------

    mesh = model.Mesh

    mesh.ElementSize = Quantity("5 [mm]")

    print("GENERATING MESH...")

    mesh.GenerateMesh()

    print("MESH GENERATED")

    # --------------------------------------------------------
    # CREATE TOTAL DEFORMATION
    # --------------------------------------------------------

    solution = analysis.Solution

    print("CREATING TOTAL DEFORMATION...")

    total_deformation = solution.AddTotalDeformation()

    print("TOTAL DEFORMATION CREATED")

    # --------------------------------------------------------
    # CREATE EQUIVALENT STRESS
    # --------------------------------------------------------

    print("CREATING EQUIVALENT STRESS...")

    equivalent_stress = solution.AddEquivalentStress()

    print("EQUIVALENT STRESS CREATED")

    # --------------------------------------------------------
    # SOLVE
    # --------------------------------------------------------

    print("==========================================")
    print("STARTING SOLVE")
    print("==========================================")

    analysis.Solve(True)

    print("SOLVE COMMAND FINISHED")

    # --------------------------------------------------------
    # EVALUATE TOTAL DEFORMATION
    # --------------------------------------------------------

    print("EVALUATING TOTAL DEFORMATION...")

    total_deformation.EvaluateAllResults()

    print("TOTAL DEFORMATION EVALUATED")

    # --------------------------------------------------------
    # EVALUATE STRESS
    # --------------------------------------------------------

    print("EVALUATING EQUIVALENT STRESS...")

    equivalent_stress.EvaluateAllResults()

    print("EQUIVALENT STRESS EVALUATED")

    # --------------------------------------------------------
    # GET RESULTS
    # --------------------------------------------------------

    maximum_deformation = "Unavailable"
    maximum_stress = "Unavailable"

    try:
        maximum_deformation = str(
            total_deformation.Maximum.Value
        )
    except:
        pass

    try:
        maximum_stress = str(
            equivalent_stress.Maximum.Value
        )
    except:
        pass

    print("==========================================")
    print("MAXIMUM TOTAL DEFORMATION:")
    print(maximum_deformation)

    print("MAXIMUM EQUIVALENT STRESS:")
    print(maximum_stress)
    print("==========================================")

    # --------------------------------------------------------
    # ACTIVATE TOTAL DEFORMATION
    # --------------------------------------------------------

    try:
        total_deformation.Activate()
        print("TOTAL DEFORMATION ACTIVATED")
    except:
        print("Could not activate deformation.")

    # --------------------------------------------------------
    # WRITE RESULT FILE
    # IMPORTANT:
    # NO encoding= parameter
    # --------------------------------------------------------

    result_text = ""

    result_text += "ANSYS AI CANTILEVER BEAM RESULTS\n"
    result_text += "=================================\n"
    result_text += "Status: COMPLETED\n"
    result_text += "Analysis: Static Structural\n"
    result_text += "Geometry: Rectangular Beam\n"
    result_text += "Length: 100 mm\n"
    result_text += "Width: 20 mm\n"
    result_text += "Height: 20 mm\n"
    result_text += "Material: Structural Steel\n"
    result_text += "Fixed Support: Left End\n"
    result_text += "Applied Force: 100 N\n"
    result_text += "Force Direction: -Y\n"
    result_text += "Mesh Size: 5 mm\n"
    result_text += "\n"
    result_text += "Maximum Total Deformation: "
    result_text += maximum_deformation
    result_text += "\n"
    result_text += "Maximum Equivalent Stress: "
    result_text += maximum_stress
    result_text += "\n"

    f = open(RESULTS_FILE, "w")
    f.write(result_text)
    f.close()

    print("RESULT FILE WRITTEN")

    # --------------------------------------------------------
    # STATUS FILE
    # --------------------------------------------------------

    f = open(STATUS_FILE, "w")
    f.write("SUCCESS")
    f.close()

    print("STATUS FILE WRITTEN")

    # --------------------------------------------------------
    # SAVE PROJECT
    # --------------------------------------------------------

    ExtAPI.DataModel.Project.Save()

    print("PROJECT SAVED")

    print("==========================================")
    print("SIMULATION COMPLETED SUCCESSFULLY")
    print("==========================================")

except Exception as e:

    print("==========================================")
    print("MECHANICAL AUTOMATION FAILED")
    print("==========================================")

    error_text = (
        "MECHANICAL AUTOMATION ERROR\n\n"
        + type(e).__name__
        + ": "
        + str(e)
        + "\n\n"
        + traceback.format_exc()
    )

    print(error_text)

    try:
        f = open(ERROR_FILE, "w")
        f.write(error_text)
        f.close()
    except:
        pass

    try:
        f = open(STATUS_FILE, "w")
        f.write("FAILED")
        f.close()
    except:
        pass

    raise