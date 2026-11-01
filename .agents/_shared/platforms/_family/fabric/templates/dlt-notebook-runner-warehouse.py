# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "jupyter",
# META     "jupyter_kernel_name": "python3.11"
# META   }
# META }

# MARKDOWN ********************

# # Vibedata dlt runner — Fabric Warehouse
#
# Runs one committed dlt pipeline against the Warehouse its `.dlt/config.toml` names.
# A Lakehouse Domain uses its own runner; nothing here inspects the config to decide
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
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import notebookutils  # provided by the Fabric kernel; not a pip package

# The execution units this runner installs. The Warehouse unit registers no secret
# provider of its own, so the notebook unit comes too — that is where the one this
# venue can use lives. `adlfs` and `fsspec` are named outright rather than left to the
# unit's own metadata: the child interpreter below exists to pick up an adlfs newer
# than the one the kernel imported, and nothing picks up what nothing installs.
UNITS = (
    "vibedata-dlt-fabric-warehouse-studio",
    "vibedata-dlt-fabric-notebook",
    "vibedata-dlt-core",
    "dlt[fabric,filesystem]",
    "adlfs>=2026.8.0",
    "fsspec>=2026.7.0",
)
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
print(f"vd-dlt-runner: FABRIC WAREHOUSE   pipeline={PIPELINE}")
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

# ---- The load, in a child interpreter ------------------------------------------------
#
# A child, not this kernel, for one reason: the kernel imported adlfs 2023.x before the
# first cell ran, Python serves that cached module for the session, and dlt's staging
# needs what pip just wrote to disk. A process started after the install sees it; this
# one never will. Everything else a notebook can do, a child can also do — it imports
# `notebookutils`, mints its own tokens, and reads Key Vault — so nothing is handed to it
# beyond the coordinates below.

WAREHOUSE_BOOTSTRAP = r'''
"""Child-side: the Warehouse unit's seams under the notebook identity, then the pipeline."""
import os
import runpy
import sys
import time

import notebookutils
from azure.core.credentials import AccessToken

SQL_SCOPE = "https://database.windows.net/.default"


class NotebookStorageCredential:
    """azure-core TokenCredential over the notebook identity, for adlfs.

    Minted per request rather than captured once: adlfs re-requests on expiry, and a
    token frozen at start would be handed back expired part-way through a long load.
    """

    def get_token(self, *scopes, **kwargs):
        return AccessToken(notebookutils.credentials.getToken("storage"), int(time.time()) + 3000)


def install_token_provider():
    from vibedata.dlt.fabric_warehouse import set_token_provider

    set_token_provider(lambda scope: notebookutils.credentials.getToken(scope or SQL_SCOPE))


def install_staging_credential():
    """The unit resolves the staging location itself; only the credential has nowhere to
    come from, because what a notebook holds is a token and not a broker to ask.

    Both import paths are bound because a pipeline imports the name from the package.
    """
    import vibedata.dlt.fabric_warehouse as unit
    from vibedata.dlt.fabric_warehouse import staging

    original = staging.onelake_staging

    def onelake_staging(credential=None, **kwargs):
        return original(credential=credential or NotebookStorageCredential(), **kwargs)

    staging.onelake_staging = onelake_staging
    unit.onelake_staging = onelake_staging


def guard_adlfs_directory_probes():
    """OneLake answers a trailing-slash blob HEAD with 403 AuthenticationFailed for a
    notebook-minted token, while every other request on the same token succeeds. dlt's
    staging client asks adlfs `isdir(<dataset>/)` before truncating, and the 403 would end
    the load. Reproduced on adlfs 2026.8.0, so this is current, not historical."""
    from adlfs import AzureBlobFileSystem
    from azure.core.exceptions import ClientAuthenticationError

    original_exists, original_isfile = AzureBlobFileSystem._exists, AzureBlobFileSystem._isfile

    async def _exists(self, path, **kwargs):
        try:
            return await original_exists(self, path, **kwargs)
        except ClientAuthenticationError:
            if not str(path).endswith("/"):
                raise
            container, blob_path, _ = self.split_path(path)
            return await self._dir_exists(container, blob_path)

    async def _isfile(self, path, **kwargs):
        try:
            return await original_isfile(self, path, **kwargs)
        except ClientAuthenticationError:
            if not str(path).endswith("/"):
                raise
            return False

    AzureBlobFileSystem._exists, AzureBlobFileSystem._isfile = _exists, _isfile


def register_secrets():
    """The Domain's Key Vault, read as the notebook identity.

    The unit installed here is the Studio one, whose secret provider authenticates
    through a credential broker that exists beside the agent and not in Fabric. The
    notebook unit ships a provider for this venue; installing it is what selects it.

    The vault itself is not passed in: the provider resolves it from
    `[providers.azure_key_vault]` in the pipeline's own config, so the Domain states its
    vault once, where it states the rest of its destination.
    """
    from vibedata.dlt.fabric.providers.akv import register_akv_provider

    register_akv_provider()


def main(pipeline_file):
    register_secrets()
    install_token_provider()
    install_staging_credential()
    guard_adlfs_directory_probes()
    sys.path.insert(0, os.getcwd())
    runpy.run_path(pipeline_file, run_name="__main__")


if __name__ == "__main__":
    main(sys.argv[1])
'''

config = tomllib.loads((work / ".dlt" / "config.toml").read_text())
fabric = config["destination"]["fabric"]
workspace_id = notebookutils.runtime.context["currentWorkspaceId"]

if str(fabric.get("workspace_id", "")).lower() != str(workspace_id).lower():
    raise SystemExit(
        f"config.toml names workspace {fabric.get('workspace_id')} but this runner runs in "
        f"{workspace_id}: the uploaded copy was not retargeted. Re-upload ingestion/ with "
        "upload-to-onelake.py; never edit the repo config."
    )

staging_url = config.get("destination", {}).get("filesystem", {}).get("bucket_url")
print(f"vd-dlt-runner: staging={staging_url or 'none — loading row by row'}")

bootstrap = work / "_vd_dlt_runner_bootstrap.py"
bootstrap.write_text(WAREHOUSE_BOOTSTRAP)
try:
    # Streams the pipeline's own output into the notebook log; a non-zero exit fails the
    # activity with the child's traceback already printed above it.
    subprocess.run([sys.executable, str(bootstrap), PIPELINE], cwd=work, check=True)
finally:
    bootstrap.unlink(missing_ok=True)
print("vd-dlt-runner: completed")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }
