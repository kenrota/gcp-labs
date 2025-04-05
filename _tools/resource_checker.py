import json
import subprocess
import pandas as pd
import argparse
from tabulate import tabulate


def list_vm_instances(project_id: str) -> list[dict]:
    cmd = f"gcloud compute instances list --project={project_id} --format=json"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    instances = json.loads(result.stdout)

    resources = []
    for instance in instances:
        internal_ips = []
        external_ips = []
        for interface in instance.get("networkInterfaces", []):
            internal_ips.append(interface["networkIP"])
            access_configs = interface.get("accessConfigs", [])
            external_ips += list(map(lambda x: x["natIP"], access_configs))

        resources.append(
            {
                "Type": "VM",
                "Name": instance["name"],
                "Endpoint": ", ".join(internal_ips + external_ips),
            }
        )

    return resources


def list_cloud_run_services(project_id: str) -> list[dict]:
    cmd = f"gcloud run services list --project={project_id} --format=json"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    services = json.loads(result.stdout)

    resources = []
    for service in services:
        resource_type = (
            "Cloud Run Functions"
            if service["metadata"]["labels"].get("goog-managed-by") == "cloudfunctions"
            else "Cloud Run Services"
        )

        resources.append(
            {
                "Type": resource_type,
                "Name": service["metadata"]["name"],
                "Endpoint": service["status"]["url"],
            }
        )

    return resources


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id")
    args = parser.parse_args()
    project_id = args.project_id

    vms = list_vm_instances(project_id)
    cloud_run_services = list_cloud_run_services(project_id)
    resources = vms + cloud_run_services

    if len(resources) > 0:
        df = pd.DataFrame(resources)
        print(tabulate(df, headers="keys", showindex=False))
    else:
        print("Resource not found.")


if __name__ == "__main__":
    main()
