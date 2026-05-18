#!/bin/bash
# 後片付けスクリプト
# 証明書の無効化・削除と CloudFormation スタックの削除を行います

set -e

DEVICE_ID="${DEVICE_ID:-raspi-001}"
STACK_NAME="jawsug-iot-handson-${DEVICE_ID##*-}"
THING_NAME="jawsug-${DEVICE_ID}"
POLICY_NAME="jawsug-handson-policy-${DEVICE_ID}"
REGION="${AWS_DEFAULT_REGION:-ap-northeast-1}"

echo "=== JAWS-UG IoT Handson - 後片付け ==="
echo "Thing: $THING_NAME  /  Region: $REGION"
echo ""

# AWS 認証情報の確認
echo "[0/4] AWS 認証情報を確認しています..."
if ! aws sts get-caller-identity --region "$REGION" > /dev/null 2>&1; then
  echo "❌ AWS 認証情報が取得できません。aws configure または assume-role の設定を確認してください。"
  exit 1
fi
echo "✅ AWS 認証情報確認済み"
echo ""

# 1. Thing にアタッチされた証明書を取得・デタッチ・削除
echo "[1/4] 証明書を削除しています..."
PRINCIPALS=$(aws iot list-thing-principals \
  --thing-name "$THING_NAME" \
  --region "$REGION" \
  --query "principals" \
  --output json 2>/dev/null || echo "[]")

echo "$PRINCIPALS" | python3 -c "
import sys, json
for p in json.load(sys.stdin):
    print(p)
" | while read -r CERT_ARN; do
  CERT_ID=$(echo "$CERT_ARN" | cut -d: -f6 | cut -d/ -f2)
  echo "  証明書 ID: ${CERT_ID:0:8}..."

  aws iot detach-thing-principal --thing-name "$THING_NAME" --principal "$CERT_ARN" --region "$REGION" || true
  aws iot detach-policy --policy-name "$POLICY_NAME" --target "$CERT_ARN" --region "$REGION" || true
  aws iot update-certificate --certificate-id "$CERT_ID" --new-status INACTIVE --region "$REGION" || true
  aws iot delete-certificate --certificate-id "$CERT_ID" --region "$REGION" || true
done
echo "✅ 証明書の削除完了"
echo ""

# 2. Thing の削除
echo "[2/4] Thing を削除しています..."
aws iot delete-thing --thing-name "$THING_NAME" --region "$REGION" 2>/dev/null && echo "✅ Thing の削除完了" || echo "⚠️  Thing は存在しないかすでに削除済みです（スキップ）"
echo ""

# 3. CloudFormation スタックの削除
echo "[3/4] CloudFormation スタックを削除しています..."
aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$REGION"
aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$REGION"
echo "✅ CloudFormation スタックの削除完了"
echo ""

# 4. ローカル証明書ファイルを削除
echo "[4/4] ローカルの証明書ファイルを削除しています..."
rm -rf ./certs
echo "✅ ローカルファイルの削除完了"
echo ""

echo "✅ 後片付け完了！"
