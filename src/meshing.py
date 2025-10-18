from __future__ import annotations
import os
from .config import MeshingConfig

def _set_units(meshing, cfg: MeshingConfig):
    try:
        meshing.meshing.GlobalSettings.LengthUnit.set_state(cfg.length_unit)
    except Exception:
        try:
            meshing.workflow.TaskObject["Units"].Arguments.set_state({"LengthUnit": cfg.length_unit})
            meshing.workflow.TaskObject["Units"].Execute()
        except Exception:
            print("[warn] Could not set length unit programmatically; using CAD default.")

def _apply_surface_mesh_controls(tasks, cfg: MeshingConfig):
    surf = tasks["Generate the Surface Mesh"]
    surf.Arguments.set_state({"CFDSurfaceMeshControls": {"MaxSize": cfg.surf_max, "MinSize": cfg.surf_min}})
    surf.Execute()

def _apply_boundary_layers(tasks, cfg: MeshingConfig):
    add_bl = tasks["Add Boundary Layers"]
    args = {"NumberOfLayers": cfg.bl_n_layers}
    try:
        args["GrowthRate"] = cfg.bl_growth
    except Exception:
        pass
    add_bl.Arguments.set_state(args)
    add_bl.AddChildAndUpdate()
    if cfg.first_layer_height is not None:
        try:
            child_names = getattr(add_bl, "Children", [])
            child_name = child_names[0] if child_names else None
            if child_name:
                child = add_bl.GetChildObject(child_name)
                child.Arguments.set_state({
                    "BoundaryLayerControls": {
                        "UseAbsoluteFirstLayerHeight": True,
                        "FirstLayerHeight": cfg.first_layer_height,
                        "NumberOfLayers": cfg.bl_n_layers,
                        "GrowthRate": cfg.bl_growth,
                    }
                })
                child.Execute()
        except Exception as e:
            print(f"[warn] Could not set FirstLayerHeight: {e}")

def _write_mesh(meshing, filename: str = "wing_auto.msh.h5") -> str:
    try:
        meshing.meshing.File.WriteMesh(FileName=filename)
    except Exception:
        meshing.tui.file.write_mesh(filename)
    return os.path.abspath(filename)

def mesh_watertight(cfg: MeshingConfig):
    # Lazy import so the module is importable without Ansys installed
    import ansys.fluent.core as pyfluent

    meshing = pyfluent.launch_fluent(mode="meshing", precision=cfg.precision, processor_count=cfg.processors)
    wf = meshing.workflow
    wf.InitializeWorkflow(WorkflowType="Watertight Geometry")
    tasks = wf.TaskObject

    _set_units(meshing, cfg)

    meshing.upload(cfg.cad_file)
    imp = tasks["Import Geometry"]
    imp.Arguments.set_state({"FileName": cfg.cad_file, "LengthUnit": cfg.length_unit})
    imp.Execute()

    _apply_surface_mesh_controls(tasks, cfg)

    describe = tasks["Describe Geometry"]
    describe.Arguments.set_state({"SetupType": "The geometry consists of only fluid regions with no voids"})
    describe.UpdateChildTasks(SetupTypeChanged=True)
    describe.Execute()

    tasks["Update Boundaries"].Execute()
    tasks["Update Regions"].Execute()

    _apply_boundary_layers(tasks, cfg)

    vol = tasks["Generate the Volume Mesh"]
    vol.Arguments.set_state({
        "VolumeFill": cfg.volume_fill,
        "VolumeFillControls": {"HexMaxCellLength": cfg.hex_max_cell_length},
    })
    vol.Execute()

    meshing.tui.mesh.check_mesh()
    _write_mesh(meshing)
    return meshing

def mesh_fault_tolerant(cfg: MeshingConfig):
    import ansys.fluent.core as pyfluent

    meshing = pyfluent.launch_fluent(mode="meshing", precision=cfg.precision, processor_count=cfg.processors)
    wf = meshing.workflow
    wf.InitializeWorkflow(WorkflowType="Fault-tolerant Meshing")
    tasks = wf.TaskObject

    _set_units(meshing, cfg)

    pm = meshing.PartManagement
    fm = meshing.PMFileManagement
    pm.InputFileChanged(FilePath=cfg.cad_file, IgnoreSolidNames=False, PartPerBody=True)
    meshing.upload(cfg.cad_file)
    fm.FileManager.LoadFiles()

    imp = tasks["Import CAD and Part Management"]
    imp.Arguments.set_state({
        "Context": 0,
        "CreateObjectPer": "Custom",
        "FMDFileName": cfg.cad_file,
        "FileLoaded": "yes",
        "ObjectSetting": "DefaultObjectSetting",
    })
    imp.Execute()

    dgf = tasks["Describe Geometry and Flow"]
    dgf.Arguments.set_state({
        "FlowType": "External flow around an object",
        "AddEnclosure": "Yes" if cfg.create_enclosure else "No",
        "LocalRefinementRegions": "No",
    })
    dgf.UpdateChildTasks(SetupTypeChanged=False)
    dgf.Execute()

    if cfg.create_enclosure:
        ext = tasks["Create External Flow Boundaries"]
        r = cfg.bbox_ratio
        ext.Arguments.set_state({
            "ExternalBoundariesName": cfg.enclosure_name,
            "CreationMethod": "Bounding Box",
            "ExtractionMethod": "surface-mesh",
            "BoundingBoxObject": {
                "SizeRelativeLength": "ratio",
                "XminRatio": -r["x_minus"], "XmaxRatio": r["x_plus"],
                "YminRatio": -r["y_minus"], "YmaxRatio": r["y_plus"],
                "ZminRatio": -r["z_minus"], "ZmaxRatio": r["z_plus"],
            },
        })
        ext.Execute()

    _apply_surface_mesh_controls(tasks, cfg)
    tasks["Update Boundaries"].Execute()
    tasks["Update Regions"].Execute()
    _apply_boundary_layers(tasks, cfg)

    vol = tasks["Generate the Volume Mesh"]
    vol.Arguments.set_state({
        "VolumeFill": cfg.volume_fill,
        "VolumeFillControls": {"HexMaxCellLength": cfg.hex_max_cell_length},
        "VolumeMeshPreferences": {"ShowVolumeMeshPreferences": True, "CheckSelfProximity": "yes"},
    })
    vol.Execute()

    meshing.tui.mesh.check_mesh()
    _write_mesh(meshing)
    return meshing

def build_mesh(cfg: MeshingConfig):
    if cfg.workflow.lower() == "watertight":
        return mesh_watertight(cfg)
    return mesh_fault_tolerant(cfg)
