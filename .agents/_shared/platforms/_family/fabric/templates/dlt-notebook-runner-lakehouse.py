# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "jupyter",
# META     "jupyter_kernel_name": "python3.12"
# META   }
# META }

# MARKDOWN ********************

# # Vibedata dlt runner — Fabric Lakehouse
#
# Runs one committed dlt pipeline against the Lakehouse its `.dlt/config.toml` names.
# A Warehouse Domain uses its own runner; nothing here inspects the config to decide
# which it is.
#
# **This notebook has a default Lakehouse attached, and that attachment is the code
# path.** `/lakehouse/default/Files/<DOMAIN_SLUG>/ingestion` is where the Domain's
# published pipeline lives. The deployer binds the attachment per workspace; the first
# cell refuses to run if it points somewhere else, because a wrong one reads another
# Domain's code and succeeds.
#
# Parameters (set by the invoking DataPipeline activity):
# - `DOMAIN_SLUG`: the Domain slug; names the OneLake code folder.
# - `PIPELINE`: the pipeline script inside `ingestion/`, e.g. `sf_prod_pipeline.py`.

# PARAMETERS CELL ********************

DOMAIN_SLUG = ""
PIPELINE = ""

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

import os
import re
import runpy
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import notebookutils  # provided by the Fabric kernel; not a pip package

# The execution unit this runner installs.
UNITS = ("vibedata-dlt-fabric-notebook", "vibedata-dlt-core", "dlt")
# The versions are not named here: the materializer embeds the managed constraints for this
# platform, and every install below runs under them, so a connector that asks for another
# version of a managed package fails here instead of moving it.
MANAGED_CONSTRAINTS = """<managed-constraints>"""
CONSTRAINTS_FILE = Path("/tmp/managed-constraints.txt")

for name, value in (("DOMAIN_SLUG", DOMAIN_SLUG), ("PIPELINE", PIPELINE)):
    if not value:
        raise SystemExit(f"Notebook parameter {name} is empty; the invoking pipeline activity must set it.")

# Both parameters are committed strings that become path segments under a mount shared
# by every Domain in the workspace. A `DOMAIN_SLUG` of `../other-domain` reads another
# Domain's code and the run succeeds, which is the same silent-wrong-code failure the
# attachment check below exists for — so neither may carry a separator or a traversal.
SAFE_SEGMENT = re.compile(r"[A-Za-z0-9_.-]{1,255}\Z")
if not SAFE_SEGMENT.fullmatch(DOMAIN_SLUG) or DOMAIN_SLUG in (".", ".."):
    raise SystemExit(f"DOMAIN_SLUG {DOMAIN_SLUG!r} is not a single path segment.")
if not PIPELINE.endswith("_pipeline.py") or not SAFE_SEGMENT.fullmatch(PIPELINE):
    raise SystemExit(f"PIPELINE {PIPELINE!r} must name a committed ingestion/<name>_pipeline.py.")

# A Lakehouse attached from another workspace mounts that workspace's Files area and
# reads its code, with no error anywhere. The runtime context carries both ids, so the
# mismatch is answerable here rather than in whatever the wrong pipeline then loads.
context = notebookutils.runtime.context
if context.get("defaultLakehouseId") is None:
    raise SystemExit(
        "No default Lakehouse is attached, so there is no code path. Attach the Domain's "
        "Lakehouse to this notebook item in this workspace and re-deploy."
    )
if str(context.get("defaultLakehouseWorkspaceId")).lower() != str(context.get("currentWorkspaceId")).lower():
    raise SystemExit(
        f"The attached Lakehouse lives in {context.get('defaultLakehouseWorkspaceName')}, not in "
        f"this workspace. A run would read that workspace's code and report success. Re-bind the "
        "attachment to this workspace's Lakehouse."
    )

# Copy out of the mount before reading. The mount is shared and writable, so a file that
# changes between the first read and the last would run half of one revision and half of
# another; a private copy cannot.
source = Path(f"/lakehouse/default/Files/{DOMAIN_SLUG}/ingestion")
if not source.is_dir():
    raise SystemExit(
        f"{source} does not exist. The Domain publishes its pipeline there; check DOMAIN_SLUG "
        "and that the code has been uploaded to this workspace's Lakehouse."
    )

work = Path("/tmp/vd-dlt-runner/ingestion")
shutil.rmtree(work.parent, ignore_errors=True)
shutil.copytree(source, work)

if not (work / PIPELINE).is_file():
    raise SystemExit(
        f"{PIPELINE} is not in {source}; the PIPELINE parameter must name a committed "
        "ingestion/<name>_pipeline.py. Do not embed the pipeline code in the notebook."
    )

# dlt names its own staging schema by appending a suffix to the dataset, and its
# `%s_staging` default is byte-identical to dbt's derivation for a custom schema. Left
# at the default, one schema holds dlt's scratch and the modelled staging layer
# together. Renaming the scratch is the only side that can move.
os.environ["DESTINATION__STAGING_DATASET_NAME_LAYOUT"] = "%s_dlt_staging"

os.chdir(work)
sys.path.insert(0, str(work))

print("=" * 72)
print(f"vd-dlt-runner: FABRIC LAKEHOUSE   pipeline={PIPELINE}")
print(f"vd-dlt-runner: source={source}")
print("=" * 72)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

# The execution unit and dlt itself, which a Fabric kernel does not carry and
# `requirements.txt` does not name — that file holds the project's own toolchain and
# connector pins, and the unit is installed at provisioning in every other venue.
CONSTRAINTS_FILE.write_text(MANAGED_CONSTRAINTS)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-c", str(CONSTRAINTS_FILE), *UNITS], check=True)

# The project's own requirements, plus each vendored connector's
# (`sources/<connector>/requirements.txt`, the dlt verified-source convention). A
# pipeline whose connector cannot import fails before its first request.
for requirements in sorted([work / "requirements.txt", *work.glob("sources/*/requirements.txt")]):
    if requirements.is_file():
        print(f"vd-dlt-runner: installing {requirements.relative_to(work)}")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-c", str(CONSTRAINTS_FILE), "-r", str(requirements)],
            check=True,
        )

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

# ---- The load, in this kernel --------------------------------------------------------
#
# In-process, unlike the Warehouse runner. That one needs a child because dlt's staging
# wants an adlfs newer than the one the kernel imported before the first cell ran. On the
# Python 3.12 kernel, Fabric's own OneLake filesystem signs this load in.

config = tomllib.loads((work / ".dlt" / "config.toml").read_text())
filesystem = config["destination"]["filesystem"]
workspace_id = notebookutils.runtime.context["currentWorkspaceId"]

if str(filesystem.get("workspace_id", "")).lower() != str(workspace_id).lower():
    raise SystemExit(
        f"config.toml names workspace {filesystem.get('workspace_id')} but this runner runs in "
        f"{workspace_id}: the uploaded copy was not retargeted. Re-upload ingestion/ with "
        "upload-to-onelake.py; never edit the repo config."
    )

runpy.run_path(str(work / PIPELINE), run_name="__main__")
print("vd-dlt-runner: completed")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }
