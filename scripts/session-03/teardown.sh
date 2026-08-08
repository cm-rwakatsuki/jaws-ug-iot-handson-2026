#!/bin/bash
# 後片付けスクリプト（第3回）
# 証明書の無効化・削除、3 つの CloudFormation スタック削除、ローカルファイル削除を行います。
# 使い方: DEVICE_NUMBER=001 bash teardown.sh

set -e

DEVICE_NUMBER="${DEVICE_NUMBER:-001}"
THING_NAME="jawsug-raspi-${DEVICE_NUMBER}"
POLICY_NAME="jawsug-s3-policy-raspi-${DEVICE_NUMBER}"
STACK_BASIC="jawsug-iot-handson-s3-${DEVICE_NUMBER}"
STACK_LAMBDA="jawsug-iot-handson-s3-lambda-${DEVICE_NUMBER}"
STACK_ALARM="jawsug-iot-handson-s3-alarm-${DEVICE_NUMBER}"
REGION="${AWS_DEFAULT_REGION:-ap-northeast-1}"

echo "=== JAWS-UG IoT Handson 第3回 - 後片付け ==="
echo "Device Number: $DEVICE_NUMBER"
echo "Thing: $THING_NAME  /  Region: $REGION"
echo ""

# --- 削除対象の表示と確認（R8-9） ---
echo "以下のリソースを削除します:"
echo "  - IoT Thing: $THING_NAME"
echo "  - IoT Policy: $POLICY_NAME"
echo "  - Thing にアタッチされた証明書"
echo "  - CloudFormation スタック:"
echo "    - $STACK_ALARM（アドバンス B: 存在する場合）"
echo "    - $STACK_LAMBDA（アドバンス A: 存在する場合）"
echo "    - $STACK_BASIC（基本編）"
echo "  - ローカル certs/ ディレクトリ"
echo ""
read -p "続行しますか？ (y/N): " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
  echo "中止しました。"
  exit 0
fi
echo ""

# --- AWS 認証情報の確認 ---
echo "[0/5] AWS 認証情報を確認しています..."
if ! aws sts get-caller-identity --region "$REGION" > /dev/null 2>&1; then
  echo "❌ AWS 認証情報が取得できません。aws configure または assume-role の設定を確認してください。"
  exit 1
fi
echo "✅ AWS 認証情報確認済み"
echo ""

# --- 1. 証明書のデタッチ・無効化・削除 ---
echo "[1/5] 証明書を削除しています..."
PRINCIPALS=$(aws iot list-thing-principals \
  --thing-name "$THING_NAME" \
  --region "$REGION" \
  --query "principals" \
  --output json 2>/dev/null || echo "[]")

echo "$PRINCIPALS" | python3 -c "
import sys, json
for p in json.load(sys.stdin):
    print(p)
" 2>/dev/null | while read -r CERT_ARN; do
  CERT_ID=$(echo "$CERT_ARN" | cut -d: -f6 | cut -d/ -f2)
  echo "  証明書 ID: ${CERT_ID:0:8}..."

  aws iot detach-thing-principal --thing-name "$THING_NAME" --principal "$CERT_ARN" --region "$REGION" 2>/dev/null || true
  aws iot detach-policy --policy-name "$POLICY_NAME" --target "$CERT_ARN" --region "$REGION" 2>/dev/null || true
  aws iot update-certificate --certificate-id "$CERT_ID" --new-status INACTIVE --region "$REGION" 2>/dev/null || true
  aws iot delete-certificate --certificate-id "$CERT_ID" --region "$REGION" 2>/dev/null || true
done
echo "✅ 証明書の削除完了"
echo ""

# --- 2. CloudFormation スタックの削除（アドバンス B → A → 基本の順） ---
echo "[2/5] CloudFormation スタックを削除しています..."

delete_stack_if_exists() {
  local STACK_NAME=$1
  if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" > /dev/null 2>&1; then
    echo "  $STACK_NAME を削除中..."
    aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$REGION"
    aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$REGION"
    echo "  ✅ $STACK_NAME 削除完了"
  else
    echo "  ⚠️  $STACK_NAME は存在しません（スキップ）"
  fi
}

delete_stack_if_exists "$STACK_ALARM"
delete_stack_if_exists "$STACK_LAMBDA"
delete_stack_if_exists "$STACK_BASIC"
echo ""

# --- 3. Thing の削除（スタックで作成されなかった場合の保険） ---
echo "[3/5] Thing を確認しています..."
aws iot delete-thing --thing-name "$THING_NAME" --region "$REGION" 2>/dev/null && \
  echo "✅ Thing の削除完了" || \
  echo "⚠️  Thing は存在しないかすでに削除済みです（スキップ）"
echo ""

# --- 4. ローカル証明書ファイルの削除 ---
echo "[4/5] ローカルの証明書ファイルを削除しています..."
if [ -d "./certs" ]; then
  rm -rf ./certs
  echo "✅ certs/ を削除しました"
else
  echo "⚠️  certs/ は存在しません（スキップ）"
fi
echo ""

# --- 5. 残存確認（R8-9） ---
echo "[5/5] 残存リソースを確認しています..."
echo ""

REMAINING=0

# Thing
if aws iot describe-thing --thing-name "$THING_NAME" --region "$REGION" > /dev/null 2>&1; then
  echo "  ⚠️  Thing が残っています: $THING_NAME"
  REMAINING=$((REMAINING + 1))
else
  echo "  ✅ Thing: なし"
fi

# ルール
for RULE_NAME in "jawsug_s3_metrics_to_cw_raspi_${DEVICE_NUMBER}" "jawsug_s3_metrics_to_lambda_raspi_${DEVICE_NUMBER}"; do
  if aws iot describe-topic-rule --rule-name "$RULE_NAME" --region "$REGION" > /dev/null 2>&1; then
    echo "  ⚠️  ルールが残っています: $RULE_NAME"
    REMAINING=$((REMAINING + 1))
  fi
done

# スタック
for STACK in "$STACK_BASIC" "$STACK_LAMBDA" "$STACK_ALARM"; do
  if aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" > /dev/null 2>&1; then
    echo "  ⚠️  スタックが残っています: $STACK"
    REMAINING=$((REMAINING + 1))
  fi
done

# SNS トピック（名前で検索）
SNS_TOPIC_NAME="jawsug-s3-alarm-raspi-${DEVICE_NUMBER}"
SNS_ARNS=$(aws sns list-topics --region "$REGION" --query "Topics[?contains(TopicArn, '${SNS_TOPIC_NAME}')].TopicArn" --output text 2>/dev/null || echo "")
if [ -n "$SNS_ARNS" ] && [ "$SNS_ARNS" != "None" ]; then
  echo "  ⚠️  SNS トピックが残っています: $SNS_TOPIC_NAME"
  REMAINING=$((REMAINING + 1))
fi

echo ""
if [ $REMAINING -eq 0 ]; then
  echo "✅ 後片付け完了！すべてのリソースが削除されました。"
else
  echo "⚠️  $REMAINING 件のリソースが残っています。手動で確認してください。"
fi

echo ""
echo "📝 注意: CloudWatch Metrics（カスタムメトリクス）には削除 API がありません。"
echo "   保持期間が経過すると自動的に消えます（アクティビティなしで 3 時間後にリストから消え、"
echo "   データポイントは 15 日後に期限切れになります）。"
echo "   CloudWatch Alarm はスタック削除で消えるため、月額課金は停止しています。"
