#!/bin/bash
# Déploie la fonction « une seule instance en marche par étudiant » dans
# eu-west-3 : rôle d'exécution, fonction Lambda, règle EventBridge.
# À lancer dans CloudShell avec un compte administrateur, depuis ce dossier.
# Relançable : les éléments déjà présents sont mis à jour.
set -euo pipefail

REGION=eu-west-3
NOM=une-instance-par-etudiant
COMPTE=$(aws sts get-caller-identity --query Account --output text)
cd "$(dirname "$0")"

echo "1/4 Rôle d'exécution $NOM"
if ! aws iam get-role --role-name "$NOM" >/dev/null 2>&1; then
  aws iam create-role --role-name "$NOM" --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]
  }' >/dev/null
  aws iam attach-role-policy --role-name "$NOM" \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
  sleep 10  # le temps que le nouveau rôle soit visible par Lambda
fi
aws iam put-role-policy --role-name "$NOM" --policy-name arreter-les-instances-en-trop --policy-document "{
  \"Version\": \"2012-10-17\",
  \"Statement\": [
    {\"Effect\": \"Allow\", \"Action\": \"ec2:DescribeInstances\", \"Resource\": \"*\"},
    {\"Effect\": \"Allow\", \"Action\": [\"ec2:StopInstances\", \"ec2:CreateTags\"],
     \"Resource\": \"arn:aws:ec2:$REGION:$COMPTE:instance/*\"}
  ]
}"

echo "2/4 Fonction Lambda $NOM"
rm -f /tmp/$NOM.zip
zip -q -j /tmp/$NOM.zip lambda_function.py
if aws lambda get-function --region $REGION --function-name "$NOM" >/dev/null 2>&1; then
  aws lambda update-function-code --region $REGION --function-name "$NOM" \
    --zip-file fileb:///tmp/$NOM.zip >/dev/null
else
  for essai in 1 2 3 4 5; do
    aws lambda create-function --region $REGION --function-name "$NOM" \
      --runtime python3.13 --handler lambda_function.lambda_handler --timeout 30 \
      --role arn:aws:iam::$COMPTE:role/$NOM --zip-file fileb:///tmp/$NOM.zip >/dev/null && break
    echo "   rôle pas encore prêt, nouvel essai dans 10 s"; sleep 10
  done
fi
FONCTION=$(aws lambda get-function --region $REGION --function-name "$NOM" --query Configuration.FunctionArn --output text)

echo "3/4 Règle EventBridge $NOM"
REGLE=$(aws events put-rule --region $REGION --name "$NOM" --query RuleArn --output text --event-pattern '{
  "source": ["aws.ec2"],
  "detail-type": ["EC2 Instance State-change Notification"],
  "detail": {"state": ["running"]}
}')
aws lambda add-permission --region $REGION --function-name "$NOM" --statement-id eventbridge \
  --action lambda:InvokeFunction --principal events.amazonaws.com --source-arn "$REGLE" >/dev/null 2>&1 || true

echo "4/4 Raccordement de la règle à la fonction"
aws events put-targets --region $REGION --rule "$NOM" --targets "Id=1,Arn=$FONCTION" >/dev/null

echo "Terminé. Journaux de la fonction : CloudWatch › Log groups › /aws/lambda/$NOM"
