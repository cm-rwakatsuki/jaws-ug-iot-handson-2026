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
echo "    - ${STACK_ALARM}（Advanced Course2: 存在する場合）"
echo "    - ${STACK_LAMBDA}（Advanced Course1: 存在する場合）"
echo "    - ${STACK_BASIC}（Basic Course）"
echo "  - ローカル certs/ ディレクトリ"
echo ""
read -r -p "続行しますか？ (y/N): " CONFIRM
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
# 証明書は 2 つの経路で探す。
#   (a) Thing にアタッチ済みの証明書 … 正常に手順を終えた場合
#   (b) ポリシーにアタッチ済みの証明書 … 証明書を作ったが Thing へのアタッチを忘れた場合
# (b) を見ないと「作ったが紐付いていない証明書」が孤児として残る（2026-08-13 に実機検証で判明）
echo "[1/5] 証明書を削除しています..."

CERT_ARNS=$(
  {
    aws iot list-thing-principals --thing-name "$THING_NAME" --region "$REGION" \
      --query "principals[]" --output text 2>/dev/null || true
    aws iot list-targets-for-policy --policy-name "$POLICY_NAME" --region "$REGION" \
      --query "targets[]" --output text 2>/dev/null || true
  } | tr '\t' '\n' | grep -E '^arn:aws:iot:[^:]+:[0-9]+:cert/' | sort -u || true
)

CERT_COUNT=0
if [ -n "$CERT_ARNS" ]; then
  while read -r CERT_ARN; do
    [ -z "$CERT_ARN" ] && continue
    CERT_ID="${CERT_ARN##*/}"
    echo "  証明書 ID: ${CERT_ID:0:8}..."
    CERT_COUNT=$((CERT_COUNT + 1))

    aws iot detach-thing-principal --thing-name "$THING_NAME" --principal "$CERT_ARN" --region "$REGION" 2>/dev/null || true
    aws iot detach-policy --policy-name "$POLICY_NAME" --target "$CERT_ARN" --region "$REGION" 2>/dev/null || true
    aws iot update-certificate --certificate-id "$CERT_ID" --new-status INACTIVE --region "$REGION" 2>/dev/null || true
    if aws iot delete-certificate --certificate-id "$CERT_ID" --region "$REGION" 2>/dev/null; then
      echo "    ✅ 削除しました"
    else
      echo "    ⚠️  削除できませんでした（コンソールで確認してください）"
    fi
  done <<< "$CERT_ARNS"
fi

if [ "$CERT_COUNT" -eq 0 ]; then
  # 紐付く証明書が 0 件になる理由は 2 通りある。スクリプト側では区別できないため
  # 断定せず、両方の可能性を示して確認先だけ案内する。
  #   (a) すでに削除済み（このスクリプトの再実行時など）… 正常
  #   (b) 証明書を発行したが Thing / ポリシーにアタッチしていない … 孤児が残る
  echo "  ℹ️  紐付く証明書は見つかりませんでした（スキップ）"
  echo "     すでに削除済みであれば問題ありません。"
  echo "     証明書を発行したがアタッチしていない場合は、この方法では検出できないため"
  echo "     IoT Core > セキュリティ > 証明書 で紐付けのない証明書が残っていないか確認してください。"
else
  echo "✅ 証明書の削除完了（${CERT_COUNT} 件を処理）"
fi
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
# 注意: aws iot delete-thing は対象が存在しなくても成功扱いになるため、
# 先に存在確認をしてからメッセージを出し分ける（誤って「削除完了」と報告しないため）
echo "[3/5] Thing を確認しています..."
if aws iot describe-thing --thing-name "$THING_NAME" --region "$REGION" > /dev/null 2>&1; then
  if aws iot delete-thing --thing-name "$THING_NAME" --region "$REGION" 2>/dev/null; then
    echo "✅ Thing の削除完了"
  else
    echo "⚠️  Thing を削除できませんでした（証明書がアタッチされたままの可能性があります）"
  fi
else
  echo "⚠️  Thing は存在しません（スタック削除時に消えたか、もともと未作成）"
fi
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

# ロググループ（スタック削除で消えるが、保持期間の課金対象になるため確認する）
for LOG_GROUP in \
  "/aws/iot/session-03/rule-errors-raspi-${DEVICE_NUMBER}" \
  "/aws/iot/session-03/lambda-rule-errors-raspi-${DEVICE_NUMBER}" \
  "/aws/lambda/jawsug-s3-metrics-logger-raspi-${DEVICE_NUMBER}"; do
  FOUND=$(aws logs describe-log-groups \
    --log-group-name-prefix "$LOG_GROUP" \
    --region "$REGION" \
    --query "logGroups[?logGroupName=='${LOG_GROUP}'].logGroupName" \
    --output text 2>/dev/null || echo "")
  if [ -n "$FOUND" ] && [ "$FOUND" != "None" ]; then
    echo "  ⚠️  ロググループが残っています: $LOG_GROUP"
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
