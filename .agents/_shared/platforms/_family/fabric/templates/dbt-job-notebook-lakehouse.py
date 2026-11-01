# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "jupyter",
# META     "jupyter_kernel_name": "python3.11"
# META   }
# META }

# MARKDOWN ********************

# # Vibedata dbt job — <job_name>
#
# Runs this job's dbt commands on the Domain's dbt project, delivered to
# `Files/<domain_slug>/transformation` in the attached Lakehouse. Production builds with
# the project's own `prod` profile; an Intent's upload delivers its own profile beside
# it, `ephemeral_platform`, and the run defers to production.
#
# `DBT_OUTPUT_DIR` names this run's folder, `Files/<domain_slug>/runs/<DBT_OUTPUT_DIR>/`,
# where dbt writes `target/` and `dbt.log`; the invoking activity passes its run id.

# PARAMETERS CELL ********************

DBT_OUTPUT_DIR = "manual"

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ## 1. Install

# CELL ********************

# MAGIC %%sh
# MAGIC cat > /tmp/managed-constraints.txt <<'EOF'
# MAGIC <managed-constraints>
# MAGIC EOF
# MAGIC pip install -q -c /tmp/managed-constraints.txt vibedata-dbt-fabric-notebook dbt-core dbt-fabricspark

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ## 2. Prerequisites

# CELL ********************

from vibedata.dbt.fabric import (
    enable_defer_if_not_prod, set_dbt_env_vars, stage_dbt_project_locally, use_intent_profile_if_present,
)

project = stage_dbt_project_locally(domain_slug="<domain_slug>")
set_dbt_env_vars(project, domain_slug="<domain_slug>", output_dir=DBT_OUTPUT_DIR)
use_intent_profile_if_present(domain_slug="<domain_slug>")
enable_defer_if_not_prod(project, manifest_dir="prod-target")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ## 3. Run

# CELL ********************

# MAGIC %%sh
# MAGIC set -e
# MAGIC cd "$DBT_PROJECT_DIR"
# MAGIC dbt deps
# MAGIC dbt build --select <selector>

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }
