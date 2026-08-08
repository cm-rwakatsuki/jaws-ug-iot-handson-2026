# 第3回ハンズオン 検証記録（verification-log.md）

- **プロジェクト**: JAWS-UG IoT 専門支部 IoT Core ハンズオン 2026 / 第3回
- **配置先**: `scripts/session-03/specs/verification-log.md`
- **前提文書**: `requirements.md`（R1〜R9）、`design.md`（D-1〜D-13、K-1〜K-10）、`tasks.md`（0.1〜5.11）
- **証跡の保存先**: `scripts/session-03/evidence/{m0..m5}/`

---

## 1. この文書の目的と使い方

実装の各段階で「何を、どう確かめて、どういう結果だったか」を証跡として残す。当日までに何が検証済みで何が未確認かを、この 1 枚で判断できる状態を保つ。

### 1.1 記録のタイミング（`tasks.md` 1.2）

| 対象 | 記録単位 |
| --- | --- |
| ユニットテストで完結するタスク | マイルストーン単位で 1 エントリ（`pytest` 実行結果） |
| 実 AWS 環境を伴うタスク | **タスクごとに 1 エントリ** |
| 通し実行リハーサル | 1 エントリ（所要時間の内訳表を含む） |

後追いでまとめて書かない。記録はタスクの一部。

### 1.2 記入ルール

- 実施日時は **JST**、`YYYY-MM-DD HH:MM` 形式
- 実行コマンドはコピー&ペーストで再現できる形で記載する
- 「期待結果」は検証**前**に書く（後から書くと結果に引きずられる）
- 判定は `Pass` / `Fail` / `Blocked` のいずれか。`Blocked` は外部要因で実施できなかった場合
- `Fail` の場合は 6 章のテンプレートで原因・対処・再検証を追記し、元エントリは**書き換えずに残す**

### 1.3 マスキング規則（R9-7）

証跡をコミットする前に、以下を必ず置換する。

| 対象 | 置換後 |
| --- | --- |
| AWS アカウント ID | `<ACCOUNT_ID>` |
| IoT エンドポイント | `<ENDPOINT>-ats.iot.ap-northeast-1.amazonaws.com` |
| 証明書 ID / ARN | `<CERT_ID>` |
| 参加者・検証者のメールアドレス | `<EMAIL>` |
| アクセスキー・トークン類 | そもそも記録しない |

スクリーンショットは該当箇所を塗りつぶす。`5.11` でマスキング漏れの最終確認を行う。

### 1.4 証跡ファイルの命名

```
scripts/session-03/evidence/m2/2.7-metrics-console.png
scripts/session-03/evidence/m2/2.9-three-point-comparison.md
scripts/session-03/evidence/m1/1.15-pytest-result.txt
```

形式: `{タスクID}-{内容}.{拡張子}`

---

## 2. サマリ

### 2.1 マイルストーン別ステータス

| ID | マイルストーン | ステータス | 完了日 | 備考 |
| --- | --- | --- | --- | --- |
| M0 | Spec 確定・作業環境準備 | 進行中 | — | 0.1〜0.3 完了、0.4〜0.6 未着手 |
| M1 | デバイス側の実装 | 未着手 | — | |
| M2 | 基本経路の構築 | 未着手 | — | |
| M3 | アドバンス A（Lambda） | 未着手 | — | |
| M4 | アドバンス B（Alarm → Email） | 未着手 | — | |
| M5 | ドキュメント・リハーサル | 未着手 | — | |

ステータスは `未着手` / `進行中` / `完了` / `保留`。

### 2.2 要件別の検証カバレッジ

| 要件 | 検証エントリ | 状態 |
| --- | --- | --- |
| R1 デバイス送信 | M1-UT, 1.15 | 未検証 |
| R2 負荷生成／デバイス側確認 | 1.15, 2.8, 2.9 | 未検証 |
| R3 Rules → CloudWatch Metrics | 2.5, 2.6, 2.7 | 未検証 |
| R4 Rules → Lambda → Logs | M3-UT, 3.5, 3.6, 3.7 | 未検証 |
| R5 Alarm → SNS → Email | 4.2, 4.3, 4.4, 4.5, 4.6 | 未検証 |
| R6 CloudFormation | 2.5, 2.6, 3.4, 4.2 | 未検証 |
| R7 TDD | M1-UT, M3-UT, 5.11 | 未検証 |
| R8 ドキュメント | 5.10, 5.11 | 未検証 |
| R9 証跡 | 本文書全体, 5.11 | 進行中 |
| NFR-4 所要時間 | 5.10 | 未検証 |
| NFR-6/7 セキュリティ | 5.11 | 未検証 |

状態は `未検証` / `進行中` / `Pass` / `Fail`。

### 2.3 検証環境

初回検証時に記入し、以降変更があれば追記する。

| 項目 | 値 |
| --- | --- |
| 検証者 | _（未記入）_ |
| リージョン | `ap-northeast-1` |
| Raspberry Pi モデル | _（未記入）_ |
| Raspberry Pi OS | _（未記入）_ |
| CPU コア数 / 総メモリ | _（未記入）_ |
| Python（デバイス側） | _（未記入）_ |
| `paho-mqtt` / `psutil` | _（未記入）_ |
| Python（開発環境） | _（未記入）_ |
| `pytest` / `cfn-lint` | _（未記入）_ |
| AWS CLI | _（未記入）_ |
| Lambda ランタイム（Q8 の決定） | _（未記入）_ |
| 時刻同期状態（`timedatectl`） | _（未記入）_ |

---

## 3. エントリテンプレート（コピー用）

```markdown
### {タスクID} {タスク名}

| 項目 | 内容 |
| --- | --- |
| 実施日時 | YYYY-MM-DD HH:MM JST |
| マイルストーン | M_ |
| タスク ID | _._ |
| 対応要件 | R_-_, ... |
| 対応設計 | D-_, K-_ |

**実行コマンド / 操作手順**

```bash
（再現できる形で記載）
```

**期待結果**（検証前に記入）

- 

**実際の結果**

- 

**判定**: Pass / Fail / Blocked

**証跡**: `evidence/m_/....`

**備考**

- 
```

---

## 4. マイルストーン別 受け入れ基準チェックリスト

`tasks.md` の Definition of Done に対応する。全項目が埋まった時点でマイルストーン完了とする（R9-5）。

### M0

- [ ] requirements / design / tasks / verification-log の 4 文書が揃っている
- [ ] 要件 ID とタスク ID の対応が取れている（R9-1）
- [ ] `pytest` が実行できる（テスト 0 件で正常終了）
- [ ] `cfn-lint` が実行できる
- [ ] `.gitignore` に `certs/` と `.venv/` を追加済み
- [ ] Q7（構成図）・Q8（Lambda ランタイム）を決定済み

### M1

- [ ] R1・R2 のユニットテストが全件成功（R7-9）
- [ ] Red の失敗ログを記録済み（代表タスク分）
- [ ] 実機で 4 者（`top` / `free -m` / `show_metrics.sh` / publisher 出力）が ±10 ポイント以内で一致（R2-11）
- [ ] `timedatectl` で時刻同期を確認済み（K-1）
- [ ] メモリ使用率の定義が D-7 に一致していることをコードとテストで確認

### M2

- [ ] テンプレート検証テストが全件成功（`cfn-lint` / アクション数 2 / SQL バージョン / ルール名文字種 / ErrorAction / Outputs）
- [ ] スタック作成が 5 分以内に `CREATE_COMPLETE`（R6-7）
- [ ] 送信から 3 分以内にメトリクスが表示（R3-6）
- [ ] メトリクス名が `CpuUtilization-raspi-{n}` になっている（D-1・D-2）
- [ ] ErrorAction ログにエラーがない（D-3 の明示キャストが機能）
- [ ] 期間 1 分のグラフで負荷の台形が視認でき、平常値との差が 30 ポイント以上（R2-7）
- [ ] 3 点セットが ±5 ポイント以内で一致（R2-12）
- [ ] スタック削除が成功

### M3

- [ ] R4 のユニットテストが全件成功
- [ ] インライン同期テストが成功（D-10）
- [ ] Logs Insights でレコードを検索できる（R4-6）
- [ ] ロググループの保持期間が 3 日（R4-5）
- [ ] 2 本のルールが独立に動作（片方の失敗が他方に影響しない）（R4-8）
- [ ] 必須フィールド欠落時に Lambda が WARN で継続（R4-4）

### M4

- [ ] テンプレート検証テストが全件成功（`TreatMissingData` / `Period` ≥ 60 / メール `AllowedPattern` / Outputs）
- [ ] 確認メールを受信し承認、SNS で `Confirmed` を確認（R5-2）
- [ ] CFN が承認を待たずに `CREATE_COMPLETE` になることを確認（K-6 の裏付け）
- [ ] `OK` → `ALARM` 遷移を確認（R5-4）
- [ ] 5 分以内にメール受信（R5-5）
- [ ] 復旧通知を受信（R5-7）
- [ ] 送信停止中に誤発火しない（`TreatMissingData: notBreaching`）（R5-6）
- [ ] しきい値・期間の既定値を実測に基づいて確定（Q2）
- [ ] スタック再作成時に再承認が必要であることを確認（K-6）

### M5

- [ ] 手順書・構成図・README が揃っている
- [ ] 通し実行が 90 分以内で完了（NFR-4）
- [ ] 基本編が 60 分以内で完了
- [ ] ハマりポイント表に M1〜M4 で実際に遭遇した事象が反映されている（R8-4）
- [ ] `teardown.sh` で全リソースが削除できる（R8-8・R8-9）
- [ ] `pytest` 全件成功、`cfn-lint` 全テンプレート合格（NFR-12）
- [ ] `evidence/` にアカウント ID・証明書 ID・メールアドレスが残っていない（R9-7）
- [ ] `certs/` がコミットされていない（NFR-6）

---

## 5. 検証エントリ

以下は `tasks.md` の記録対象タスクに対応した記入枠。実施のたびに埋める。

---

### M0

#### M0-1 開発環境の初期確認（タスク 0.5）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | _（未実施）_ |
| 対応要件 | R7-2, R7-8, NFR-6 |

**実行コマンド**

```bash
cd scripts/session-03
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest --version && cfn-lint --version
pytest
git check-ignore -v scripts/session-03/certs/dummy
```

**期待結果**

- `pytest` / `cfn-lint` のバージョンが表示される
- `pytest` が「collected 0 items」で正常終了する
- `certs/` が `.gitignore` にマッチする

**実際の結果**: _（未記入）_

**判定**: _（未実施）_

**証跡**: `evidence/m0/0.5-env-setup.txt`

---

### M1

#### M1-UT ユニットテスト（タスク 1.1〜1.13）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | _（未実施）_ |
| 対応要件 | R1-2, R1-4, R1-5, R2-1〜R2-6, R2-8, R7-1, R7-9 |
| 対応設計 | D-7, D-9 |

**実行コマンド**

```bash
cd scripts/session-03 && source .venv/bin/activate
pytest tests/test_metrics.py tests/test_load_gen.py -v
```

**期待結果**

- 全ケース Pass
- 各タスクの Red 段階で、意図したテストのみが失敗していた

**実際の結果**: _（未記入）_

**Red の記録**（代表タスク）

| タスク | Red で失敗したテスト | 失敗理由 |
| --- | --- | --- |
| 1.1 | _（未記入）_ | |
| 1.4 | _（未記入）_ | |
| 1.9 | _（未記入）_ | |
| 1.13 | _（未記入）_ | |

**判定**: _（未実施）_

**証跡**: `evidence/m1/M1-UT-pytest-result.txt`、`evidence/m1/M1-UT-red-logs.txt`

---

#### M1-2 実機での動作確認と値の一致（タスク 1.15）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | _（未実施）_ |
| 対応要件 | R2-11, R9-3 |
| 対応設計 | D-7, K-1, K-2 |

**実行コマンド**

```bash
# セッション1
timedatectl
cd ~/session-03 && source venv/bin/activate && python3 metrics_publisher.py
# セッション2
cd ~/session-03 && python3 load_gen.py cpu --target 90 --duration 180
# セッション3
cd ~/session-03 && ./show_metrics.sh   # 数回実行
top      # 別途確認
free -m  # 別途確認
```

**期待結果**

- `timedatectl` が `System clock synchronized: yes` を示す
- 負荷の定常区間で 4 者の値が ±10 ポイント以内で一致する
- `free -m` の `used` と `show_metrics.sh` の値の差が説明できる（K-2）

**実際の結果**: _（未記入）_

**4 者比較**（定常区間の任意の 1 時点）

| 取得元 | CPU (%) | メモリ (%) | 取得時刻 (JST) |
| --- | --- | --- | --- |
| `top` | | | |
| `free -m` から計算 | — | | |
| `show_metrics.sh` | | | |
| publisher 標準出力 | | | |
| 最大差分 | | | |

**判定**: _（未実施）_

**証跡**: `evidence/m1/1.15-device-comparison.txt`

---

### M2

#### M2-1 スタック作成と証明書発行（タスク 2.6）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | _（未実施）_ |
| 対応要件 | R6-7, R6-8 |

**実行コマンド**

```bash
aws cloudformation validate-template \
  --template-body file://cfn/session-03/iot-rules-cloudwatch.yaml \
  --region ap-northeast-1
aws cloudformation create-stack \
  --stack-name jawsug-iot-handson-s3-001 \
  --template-body file://cfn/session-03/iot-rules-cloudwatch.yaml \
  --parameters ParameterKey=DeviceNumber,ParameterValue=001 \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-northeast-1
# 証明書はコンソールから手動発行 → ポリシーアタッチ
```

**期待結果**

- `validate-template` が成功する
- 5 分以内に `CREATE_COMPLETE` になる
- Outputs に 8 項目が出力される
- 証明書を発行しポリシーをアタッチできる

**実際の結果**: _（未記入）_

**スタック作成所要時間**: _（未記入）_

**判定**: _（未実施）_

**証跡**: `evidence/m2/2.6-stack-outputs.txt`

---

#### M2-2 メトリクスの到達確認（タスク 2.7）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | _（未実施）_ |
| 対応要件 | R3-6 |
| 対応設計 | D-1, D-2, D-3, K-1 |

**実行コマンド**

```bash
# デバイス側
python3 metrics_publisher.py
# 確認側
aws cloudwatch list-metrics --namespace JAWSUG/IoTHandson --region ap-northeast-1
aws logs tail /aws/iot/session-03/rule-errors --region ap-northeast-1
```

**期待結果**

- 送信開始から 3 分以内に 2 メトリクスが `list-metrics` に現れる
- メトリクス名が `CpuUtilization-raspi-001` / `MemoryUtilization-raspi-001`（置換テンプレートが評価されている）
- ErrorAction ログにエラーが出ていない（明示キャストが機能）
- メトリクスのタイムスタンプが送信時刻と一致している（時刻ずれがない）

**実際の結果**: _（未記入）_

**判定**: _（未実施）_

**証跡**: `evidence/m2/2.7-list-metrics.txt`、`evidence/m2/2.7-metrics-console.png`

---

#### M2-3 負荷生成によるグラフ変化の確認（タスク 2.8）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | _（未実施）_ |
| 対応要件 | R2-7 |
| 対応設計 | 4.3, D-6 |

**実行コマンド**

```bash
python3 load_gen.py cpu --target 90 --duration 180
# CloudWatch コンソール → メトリクス → 期間を 1 分、統計を平均に設定
```

**期待結果**

- 負荷区間が台形として視認できる
- 平常値との差が 30 ポイント以上
- 期間 5 分では平均化されて差が縮むことも併せて確認（4.3 節の裏付け）

**実際の結果**: _（未記入）_

| 項目 | 値 |
| --- | --- |
| 平常時 CPU（1 分平均） | |
| 負荷時 CPU（1 分平均） | |
| 差分 | |
| 期間 5 分での負荷時 CPU | |

**判定**: _（未実施）_

**証跡**: `evidence/m2/2.8-graph-1min.png`、`evidence/m2/2.8-graph-5min.png`

---

#### M2-4 3 点セットの突き合わせ（タスク 2.9）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | _（未実施）_ |
| 対応要件 | R2-12, R9-4 |
| 対応設計 | 4.3 |

**手順**

1. `load_gen.py cpu --target 90 --duration 180` を開始
2. 開始から 1 分以上経過した定常区間で、同一時刻の 3 値を記録
3. CloudWatch は期間 1 分・統計平均で読む

**期待結果**: 3 値の差分が ±5 ポイント以内

**実際の結果**（CPU）

| 時刻 (JST) | ① デバイス実測（`show_metrics.sh`） | ② publisher 送信値 | ③ CloudWatch（1 分平均） | 最大差分 | 判定 |
| --- | --- | --- | --- | --- | --- |
| | | | | | |
| | | | | | |
| | | | | | |

**実際の結果**（メモリ）

| 時刻 (JST) | ① デバイス実測 | ② publisher 送信値 | ③ CloudWatch | 最大差分 | 判定 |
| --- | --- | --- | --- | --- | --- |
| | | | | | |
| | | | | | |

**判定**: _（未実施）_

**証跡**: `evidence/m2/2.9-three-point-comparison.md`

---

#### M2-5 スタック削除の確認（タスク 2.10）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | _（未実施）_ |
| 対応要件 | R8-8 |

**期待結果**

- 証明書のデタッチ → 無効化 → 削除の順で削除できる
- スタックが `DELETE_COMPLETE` になる
- Thing・ルール・ロググループが残らない

**実際の結果**: _（未記入）_

**判定**: _（未実施）_

**証跡**: `evidence/m2/2.10-teardown.txt`

---

### M3

#### M3-UT ユニットテストとインライン同期（タスク 3.1、3.2、3.4）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | _（未実施）_ |
| 対応要件 | R4-2, R4-4, R4-6, R6-9, R7-5, R7-7 |
| 対応設計 | D-10 |

**実行コマンド**

```bash
pytest tests/test_metrics_logger.py tests/test_lambda_inline_sync.py tests/test_templates.py -v
```

**期待結果**: 全ケース Pass

**実際の結果**: _（未記入）_

**Red の記録**

| タスク | Red で失敗したテスト | 失敗理由 |
| --- | --- | --- |
| 3.1 | _（未記入）_ | |

**判定**: _（未実施）_

**証跡**: `evidence/m3/M3-UT-pytest-result.txt`

---

#### M3-2 Lambda 連携と Logs 確認（タスク 3.5）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | _（未実施）_ |
| 対応要件 | R4-3, R4-5, R4-6 |

**実行コマンド**

```bash
aws cloudformation create-stack \
  --stack-name jawsug-iot-handson-s3-lambda-001 \
  --template-body file://cfn/session-03/advanced-lambda.yaml \
  --parameters ParameterKey=DeviceNumber,ParameterValue=001 \
  --capabilities CAPABILITY_NAMED_IAM --region ap-northeast-1
aws logs tail /aws/lambda/jawsug-s3-metrics-logger-raspi-001 --follow --region ap-northeast-1
aws logs describe-log-groups \
  --log-group-name-prefix /aws/lambda/jawsug-s3-metrics-logger-raspi-001 \
  --query 'logGroups[].retentionInDays' --region ap-northeast-1
```

**期待結果**

- 構造化ログ（`event: metrics_received`）が出力される
- Logs Insights のクエリでレコードが取得できる
- 保持期間が 3 日

**実際の結果**: _（未記入）_

**判定**: _（未実施）_

**証跡**: `evidence/m3/3.5-lambda-logs.txt`、`evidence/m3/3.5-logs-insights.png`

---

#### M3-3 2 本のルールの独立動作（タスク 3.6）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | _（未実施）_ |
| 対応要件 | R4-8 |
| 対応設計 | 7 |

**手順**

1. 両ルール有効の状態で、同一メッセージが Metrics と Logs の両方に反映されることを確認
2. Lambda の呼び出し権限を一時的に外し、Lambda 側が失敗する状態を作る
3. その間も CloudWatch Metrics への送信が継続していることを確認
4. 権限を戻す

**期待結果**: Lambda 側の失敗が基本ルールに影響しない。失敗は ErrorAction ログに記録される

**実際の結果**: _（未記入）_

**判定**: _（未実施）_

**証跡**: `evidence/m3/3.6-rule-independence.txt`

---

#### M3-4 欠落フィールドの挙動（タスク 3.7）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | _（未実施）_ |
| 対応要件 | R4-4 |

**手順**: MQTT テストクライアントから `cpu` を含まないメッセージを publish する

**期待結果**: Lambda が `level=WARN` でログを記録し、例外で終了しない

**実際の結果**: _（未記入）_

**判定**: _（未実施）_

**証跡**: `evidence/m3/3.7-missing-field.txt`

---

### M4

#### M4-1 サブスクリプション作成と承認（タスク 4.3）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | _（未実施）_ |
| 対応要件 | R5-2, R9-7 |
| 対応設計 | D-13, K-6 |

**実行コマンド**

```bash
aws cloudformation create-stack \
  --stack-name jawsug-iot-handson-s3-alarm-001 \
  --template-body file://cfn/session-03/advanced-alarm.yaml \
  --parameters ParameterKey=DeviceNumber,ParameterValue=001 \
               ParameterKey=NotificationEmail,ParameterValue=<EMAIL> \
  --region ap-northeast-1
aws sns list-subscriptions-by-topic --topic-arn <TOPIC_ARN> --region ap-northeast-1
```

**期待結果**

- スタック作成中に確認メールが届く（差出人 `no-reply@sns.amazonaws.com`）
- **承認前でもスタックが `CREATE_COMPLETE` になる**（K-6 の裏付け）
- 承認前の `SubscriptionArn` が `PendingConfirmation`
- 承認後、SNS コンソールのステータスが `Confirmed`

**実際の結果**: _（未記入）_

| 確認項目 | 結果 |
| --- | --- |
| 確認メール到着までの時間 | |
| 迷惑メールフォルダに入ったか | |
| 承認前のスタック状態 | |
| 承認前の SubscriptionArn | |
| 承認後のステータス | |

**判定**: _（未実施）_

**証跡**: `evidence/m4/4.3-subscription.txt`（メールアドレスはマスク）

---

#### M4-2 アラーム発火とメール受信（タスク 4.4）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | _（未実施）_ |
| 対応要件 | R5-4, R5-5, R5-7, R5-8 |

**手順**

1. `Confirmed` を確認済みの状態から開始
2. `load_gen.py cpu --target 90 --duration 180` を実行
3. Alarm の履歴タブで状態遷移を確認
4. メールの到着を確認
5. 負荷終了後に `OK` へ復帰し、復旧通知が届くことを確認

**期待結果**

- `OK` → `ALARM` に遷移する
- 5 分以内にアラームメールが届く
- 負荷終了後に `ALARM` → `OK` に戻り、復旧通知が届く

**実際の結果**: _（未記入）_

| 計測項目 | 値 |
| --- | --- |
| 負荷開始時刻 | |
| ALARM 遷移時刻 | |
| 発火までの所要時間 | |
| アラームメール受信時刻 | |
| 負荷終了時刻 | |
| OK 復帰時刻 | |
| 復旧メール受信時刻 | |

**判定**: _（未実施）_

**証跡**: `evidence/m4/4.4-alarm-history.png`、`evidence/m4/4.4-email.png`（アドレスはマスク）

---

#### M4-3 しきい値・期間の最終確定（タスク 4.5、Q2）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | _（未実施）_ |
| 対応要件 | R5-3, R5-6, R5-8 |

**期待結果**

- 手順書記載のパラメータで確実に発火する（再現性がある）
- 送信スクリプトを停止した状態で誤発火しない（`TreatMissingData: notBreaching` の効果）

**実際の結果**: _（未記入）_

| 項目 | 検証値 | 最終決定値 |
| --- | --- | --- |
| しきい値 | 80 | |
| 期間（秒） | 60 | |
| 評価回数 | 1 | |
| 負荷生成の推奨継続時間（秒） | 180 | |
| 送信停止時の誤発火 | — | |

**`requirements.md` / `design.md` の更新が必要か**: _（未記入）_

**判定**: _（未実施）_

**証跡**: `evidence/m4/4.5-threshold-tuning.md`

---

#### M4-4 スタック再作成時の再承認（タスク 4.6）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | _（未実施）_ |
| 対応設計 | K-6 |

**手順**: アラームスタックを削除 → 同一メールアドレスで再作成

**期待結果**: 確認メールが再送され、承認しないと通知が届かない

**実際の結果**: _（未記入）_

**ハマりポイント表に載せる文言**: _（未記入）_

**判定**: _（未実施）_

**証跡**: `evidence/m4/4.6-resubscribe.txt`

---

### M5

#### M5-1 通し実行リハーサル（タスク 5.10）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | _（未実施）_ |
| 対応要件 | NFR-4, R9-8 |

**手順**: 手順書（`docs/session-03/handson.md`）だけを見て、まっさらな状態から通し実行する

**期待結果**

- 基本編が 60 分以内、全体が 90 分以内で完了する
- 手順書の記述だけで詰まらずに進める

**実際の結果**: _（未記入）_

**所要時間の内訳**

| パート | 想定 | 実測 | 差 | 備考 |
| --- | --- | --- | --- | --- |
| Wi-Fi / SSH 接続 | 10 分 | | | |
| AWS 側設定（スタック作成・証明書） | 20 分 | | | |
| デバイス側実装・転送・実行 | 20 分 | | | |
| 動作確認（負荷生成・グラフ・突き合わせ） | 15 分 | | | |
| アドバンス A（Lambda） | 10 分 | | | |
| アドバンス B（Alarm → Email） | 10 分 | | | |
| 応用・質疑 | 5 分 | | | |
| **合計** | **90 分** | | | |

**詰まった箇所と手順書への反映**

| 箇所 | 内容 | 反映先 | 反映済み |
| --- | --- | --- | --- |
| | | | [ ] |

**判定**: _（未実施）_

**証跡**: `evidence/m5/5.10-rehearsal.md`

---

#### M5-2 最終確認（タスク 5.11）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | _（未実施）_ |
| 対応要件 | R7-9, R9-5, R9-7, NFR-6, NFR-12 |

**実行コマンド**

```bash
cd scripts/session-03 && source .venv/bin/activate
pytest
cfn-lint ../../cfn/session-03/*.yaml
grep -rniE "[0-9]{12}|@[a-z0-9.-]+\.(com|jp|net)" evidence/ || echo "マスキング漏れなし"
git ls-files | grep -i "certs/" || echo "certs は未コミット"
```

**期待結果**

- `pytest` 全件成功
- `cfn-lint` が 3 テンプレートすべてで合格
- `evidence/` にアカウント ID・メールアドレスが残っていない
- `certs/` がコミットされていない
- 本文書の全マイルストーンが Pass

**実際の結果**: _（未記入）_

**判定**: _（未実施）_

**証跡**: `evidence/m5/5.11-final-check.txt`

---

## 6. Fail の記録テンプレート

`Fail` が出た場合は元エントリを残したまま、以下を追記する（R9-4）。

```markdown
### {タスクID}-F{連番} {事象の要約}

| 項目 | 内容 |
| --- | --- |
| 発生日時 | YYYY-MM-DD HH:MM JST |
| 元エントリ | {タスクID} |
| 対応要件 | R_-_ |

**症状**

- 

**調査した内容**

- 

**原因**

- 

**対処**

- 

**再検証**

| 実施日時 | 結果 | 判定 |
| --- | --- | --- |
| | | |

**設計・要件へのフィードバック**

- （`design.md` の K-_ に追記した／`requirements.md` の R_-_ を更新した／`handson.md` のハマりポイント表に追加した など）

**証跡**: `evidence/m_/....`
```

---

## 7. Fail 記録

（発生時に 6 章のテンプレートで追記する。現時点で該当なし）

---

## 8. 設計・要件へのフィードバック一覧

検証を通じて `requirements.md` / `design.md` を更新した場合、ここに履歴を残す。

| 日付 | 発端 | 更新した文書・箇所 | 内容 |
| --- | --- | --- | --- |
| | | | |
