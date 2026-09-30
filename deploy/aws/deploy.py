"""Run from the local project after AWS CLI login in us-east-1.

Uses temporary CLI credentials; never prints database or Django secrets.
"""

import os
import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError


REGION = "us-east-1"
STACK = "tecnostock-lab7"
ARCHIVE = Path(__file__).with_name("app.zip")


def main():
    os.environ.setdefault("AWS_DEFAULT_REGION", REGION)
    if not ARCHIVE.is_file():
        raise SystemExit(f"Falta {ARCHIVE}. Ejecuta package.ps1 antes de este script.")
    session = boto3.Session(region_name=REGION)
    cfn = session.client("cloudformation")
    s3 = session.client("s3")
    ssm = session.client("ssm")
    stack = cfn.describe_stacks(StackName=STACK)["Stacks"][0]
    outputs = {item["OutputKey"]: item["OutputValue"] for item in stack["Outputs"]}
    bucket = outputs["ArtifactBucketName"]
    https_domain = outputs.get("HttpsDomain")
    allowed_hosts = outputs["ALBDNS"] + (f",{https_domain}" if https_domain else "")
    trusted_origins = f"http://{outputs['ALBDNS']}" + (f",https://{https_domain}" if https_domain else "")
    https_setting = "1" if https_domain else "0"
    print(f"Subiendo paquete privado al bucket {bucket}...", flush=True)
    s3.upload_file(str(ARCHIVE), bucket, "app.zip")

    for key, label in (("WebServer1Id", "web-server-1"), ("WebServer2Id", "web-server-2")):
        instance_id = outputs[key]
        for _ in range(60):
            online = ssm.describe_instance_information(
                Filters=[{"Key": "InstanceIds", "Values": [instance_id]}]
            )["InstanceInformationList"]
            if online and online[0]["PingStatus"] == "Online":
                break
            time.sleep(10)
        else:
            raise SystemExit(f"SSM no está disponible en {label} ({instance_id}).")
        commands = [
            "set -eu",
            "install -d -m 700 /opt/tecnostock",
            f"aws s3 cp s3://{bucket}/app.zip /opt/tecnostock/app.zip --region {REGION}",
            "python3 -m zipfile -e /opt/tecnostock/app.zip /opt/tecnostock/source",
            f"DB_SECRET=$(aws secretsmanager get-secret-value --secret-id '{outputs['DatabaseSecretArn']}' --region {REGION} --query SecretString --output text)",
            f"DJANGO_KEY=$(aws secretsmanager get-secret-value --secret-id '{outputs['DjangoSecretArn']}' --region {REGION} --query SecretString --output text)",
            "DB_PASSWORD=$(printf '%s' \"$DB_SECRET\" | python3 -c 'import json,sys,urllib.parse; print(urllib.parse.quote(json.load(sys.stdin)[\"password\"], safe=\"\"))')",
            "TOKEN=$(curl -fsS -X PUT http://169.254.169.254/latest/api/token -H 'X-aws-ec2-metadata-token-ttl-seconds: 60')",
            "PRIVATE_IP=$(curl -fsS -H \"X-aws-ec2-metadata-token: $TOKEN\" http://169.254.169.254/latest/meta-data/local-ipv4)",
            "umask 077",
            f"printf 'DATABASE_URL=postgres://tecnostock:%s@{outputs['DatabaseEndpoint']}:5432/tecnostock\\nDJANGO_SECRET_KEY=%s\\nDJANGO_DEBUG=0\\nDJANGO_ALLOWED_HOSTS={allowed_hosts},%s\\nDJANGO_CSRF_TRUSTED_ORIGINS={trusted_origins}\\nDJANGO_HTTPS={https_setting}\\n' \"$DB_PASSWORD\" \"$DJANGO_KEY\" \"$PRIVATE_IP\" > /opt/tecnostock/app.env",
            f"bash /opt/tecnostock/source/deploy/aws/install-app.sh {label}",
        ]
        print(f"Instalando {label} ({instance_id})...", flush=True)
        result = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": commands},
            TimeoutSeconds=3600,
            Comment=f"TecnoStock Lab 7 deployment on {label}",
        )
        command_id = result["Command"]["CommandId"]
        for _ in range(180):
            time.sleep(10)
            try:
                invocation = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
            except ClientError as exc:
                if exc.response.get("Error", {}).get("Code") == "InvocationDoesNotExist":
                    continue
                raise
            status = invocation["Status"]
            if status in ("Success", "Failed", "Cancelled", "TimedOut"):
                print(f"{label}: {status}", flush=True)
                if status != "Success":
                    print(invocation.get("StandardErrorContent", "")[-3000:], file=sys.stderr)
                    raise SystemExit(1)
                break
        else:
            raise SystemExit(f"La instalación de {label} excedió 30 minutos. Comando SSM: {command_id}")
    if https_domain:
        print(f"Aplicación segura: https://{https_domain}/login/", flush=True)
    print(f"ALB del laboratorio: http://{outputs['ALBDNS']}/login/", flush=True)
    print(f"Distribución: http://{outputs['ALBDNS']}/instance/", flush=True)


if __name__ == "__main__":
    main()
