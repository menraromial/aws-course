#!/usr/bin/env python3
"""Extrait du paquet officiel « AWS Architecture Icons » les icônes utilisées
par les figures et les convertit en PDF (figures/icones/<nom>.pdf).

Le paquet se télécharge sur https://aws.amazon.com/architecture/icons/ et se
décompresse dans figures/icones-aws-source/ (non versionné). AWS autorise
l'usage de ces icônes dans des schémas d'architecture et des supports.
Usage : python3 icones.py   (ne reconvertit que les icônes manquantes)
"""
import glob, pathlib, re, subprocess, sys, tempfile

SRC = pathlib.Path(__file__).parent / "icones-aws-source"
OUT = pathlib.Path(__file__).parent / "icones"

# nom court -> motif de fichier dans le paquet
ICONES = {
    # calcul
    "ec2": "Arch_Amazon-EC2_48.svg", "lambda": "Arch_AWS-Lambda_48.svg",
    "ecs": "Arch_Amazon-Elastic-Container-Service_48.svg",
    "eks": "Arch_Amazon-Elastic-Kubernetes-Service_48.svg",
    "beanstalk": "Arch_AWS-Elastic-Beanstalk_48.svg",
    # stockage
    "s3": "Arch_Amazon-Simple-Storage-Service_48.svg",
    "glacier": "Arch_Amazon-Simple-Storage-Service-Glacier_48.svg",
    "ebs": "Arch_Amazon-Elastic-Block-Store_48.svg", "efs": "Arch_Amazon-EFS_48.svg",
    "backup": "Arch_AWS-Backup_48.svg",
    # bases de données
    "rds": "Arch_Amazon-RDS_48.svg", "aurora": "Arch_Amazon-Aurora_48.svg",
    "dynamodb": "Arch_Amazon-DynamoDB_48.svg", "elasticache": "Arch_Amazon-ElastiCache_48.svg",
    # réseau
    "vpc": "Arch_Amazon-Virtual-Private-Cloud_48.svg", "cloudfront": "Arch_Amazon-CloudFront_48.svg",
    "route53": "Arch_Amazon-Route-53_48.svg", "elb": "Arch_Elastic-Load-Balancing_48.svg",
    "apigateway": "Arch_Amazon-API-Gateway_48.svg",
    # sécurité
    "iam": "Arch_AWS-Identity-and-Access-Management_48.svg",
    "identitycenter": "Arch_AWS-IAM-Identity-Center_48.svg",
    "kms": "Arch_AWS-Key-Management-Service_48.svg", "waf": "Arch_AWS-WAF_48.svg",
    "guardduty": "Arch_Amazon-GuardDuty_48.svg", "secrets": "Arch_AWS-Secrets-Manager_48.svg",
    # gestion
    "cloudwatch": "Arch_Amazon-CloudWatch_48.svg", "cloudtrail": "Arch_AWS-CloudTrail_48.svg",
    "cloudformation": "Arch_AWS-CloudFormation_48.svg", "ssm": "Arch_AWS-Systems-Manager_48.svg",
    "console": "Arch_AWS-Management-Console_48.svg", "organizations": "Arch_AWS-Organizations_48.svg",
    # intégration
    "sqs": "Arch_Amazon-Simple-Queue-Service_48.svg", "sns": "Arch_Amazon-Simple-Notification-Service_48.svg",
    "eventbridge": "Arch_Amazon-EventBridge_48.svg", "stepfunctions": "Arch_AWS-Step-Functions_48.svg",
    # analytique, IA
    "athena": "Arch_Amazon-Athena_48.svg", "redshift": "Arch_Amazon-Redshift_48.svg",
    "kinesis": "Arch_Amazon-Kinesis_48.svg", "glue": "Arch_AWS-Glue_48.svg",
    "bedrock": "Arch_Amazon-Bedrock_48.svg", "sagemaker": "Arch_Amazon-SageMaker-AI_48.svg",
    "rekognition": "Arch_Amazon-Rekognition_48.svg", "translate": "Arch_Amazon-Translate_48.svg",
    # outils, coûts, applications
    "cli": "Arch_AWS-Command-Line-Interface_48.svg", "sdk": "Arch_AWS-Tools-and-SDKs_48.svg",
    "cloudshell": "Arch_AWS-CloudShell_48.svg", "budgets": "Arch_AWS-Budgets_48.svg",
    "costexplorer": "Arch_AWS-Cost-Explorer_48.svg", "amplify": "Arch_AWS-Amplify_48.svg",
    "ses": "Arch_Amazon-Simple-Email-Service_48.svg", "workmail": "Arch_Amazon-WorkMail_48.svg",
    "connect": "Arch_Amazon-Connect_48.svg", "workspaces": "Arch_Amazon-WorkSpaces_48.svg",
    # ressources
    "r-instance": "Res_Amazon-EC2_Instance_48.svg", "r-role": "Res_AWS-Identity-Access-Management_Role_48.svg",
    "r-bucket": "Res_Amazon-Simple-Storage-Service_Bucket-With-Objects_48.svg",
    "r-tempcred": "Res_AWS-Identity-Access-Management_Temporary-Security-Credential_48.svg",
    "r-users": "Res_Users_48_Light.svg", "r-user": "Res_User_48_Light.svg",
    "r-client": "Res_Client_48_Light.svg", "r-internet": "Res_Internet_48_Light.svg",
    "r-json": "Res_JSON-Script_48_Light.svg", "r-firewall": "Res_Firewall_48_Light.svg",
    "r-logs": "Res_Logs_48_Light.svg", "r-dc": "Corporate-data-center_32.svg",
    "r-permissions": "Res_AWS-Identity-Access-Management_Permissions_48.svg",
    "r-longcred": "Res_AWS-Identity-Access-Management_Long-Term-Security-Credential_48.svg",
    "r-sts": "Res_AWS-Identity-Access-Management_AWS-STS_48.svg",
    "r-mfa": "Res_AWS-Identity-Access-Management_MFA-Token_48.svg",
    "r-authuser": "Res_Authenticated-User_48_Light.svg", "r-server": "Res_Server_48_Light.svg",
    "r-document": "Res_Document_48_Light.svg", "r-padlock": "Res_SSL-padlock_48_Light.svg",
    "r-git": "Res_Git-Repository_48_Light.svg",
    "r-ami": "Res_Amazon-EC2_AMI_48.svg", "r-volume": "Res_Amazon-Elastic-Block-Store_Volume-gp3_48.svg",
    "r-snapshot": "Res_Amazon-Elastic-Block-Store_Snapshot_48.svg", "r-igw": "Res_Amazon-VPC_Internet-Gateway_48.svg",
    "r-eip": "Res_Amazon-EC2_Elastic-IP-Address_48.svg", "r-instances": "Res_Amazon-EC2_Instances_48.svg",
    "r-queue": "Res_Amazon-Simple-Queue-Service_Queue_48.svg", "r-message": "Res_Amazon-Simple-Queue-Service_Message_48.svg",
    "r-rdsinst": "Res_Amazon-Aurora_Amazon-RDS-Instance_48.svg", "r-ddbitems": "Res_Amazon-DynamoDB_Items_48.svg",
    "r-object": "Res_Amazon-Simple-Storage-Service_Object_48.svg", "r-bucketempty": "Res_Amazon-Simple-Storage-Service_Bucket_48.svg",
    # groupes (conventions des schémas AWS)
    "g-cloud": "AWS-Cloud_32.svg", "g-region": "Region_32.svg", "g-vpc": "Virtual-private-cloud-VPC_32.svg",
    "g-public": "Public-subnet_32.svg", "g-account": "AWS-Account_32.svg",
}

def main() -> int:
    OUT.mkdir(exist_ok=True)
    manquants = []
    for nom, motif in ICONES.items():
        cible = OUT / f"{nom}.pdf"
        if cible.exists():
            continue
        trouves = [p for p in glob.glob(str(SRC / "**" / motif), recursive=True) if "__MACOSX" not in p]
        if not trouves:
            manquants.append(f"{nom} ({motif})")
            continue
        # le blanc des pictogrammes devient #FEFEFE : une couleur fixe de la
        # palette, distincte du fond de figure (#FFFFFF) qui, lui, suit le thème
        svg = pathlib.Path(trouves[0]).read_text()
        svg = re.sub(r'#(?:FFFFFF|ffffff|FFF|fff)\b', '#FEFEFE', svg)
        svg = re.sub(r'(fill|stroke)="white"', r'\1="#FEFEFE"', svg)
        with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as tmp:
            tmp.write(svg)
        subprocess.run(["inkscape", "--export-type=pdf", f"--export-filename={cible}", tmp.name],
                       check=True, capture_output=True)
        pathlib.Path(tmp.name).unlink()
        print("PDF ", cible.name)
    if manquants:
        print("INTROUVABLES :", ", ".join(manquants), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
