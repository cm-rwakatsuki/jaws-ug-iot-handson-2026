# 第3回ハンズオン 次アクション実行手順（next-actions.md）

- **プロジェクト**: JAWS-UG IoT 専門支部 IoT Core ハンズオン 2026 / 第3回
- **配置先**: `scripts/session-03/spec/next-actions.md`
- **前提文書**: `requirements.md` / `design.md` / `tasks.md` / `verification-log.md`
- **作成日**: 2026-08-08

---

## 0. この文書の目的

実装（コード・IaC・ユニットテスト）は完了しているが、**実 AWS 環境と実機での検証が未実施**であり、
その結果がないと `docs/session-03/handson.md` の手順を書けない。

本書は次の 3 つを一枚でつなぐ。

```
①実行する（本書のコマンド・操作）
      ↓
②記録する（verification-log.md の該当エントリ）
      ↓
③手順書へ転記する（handson.md の該当セクション）
```

各ステップに「**📝 記録先**」と「**📄 転記先**」を明記してある。
**実行しながら記録する**こと。後追いでまとめて書くと、画面の細部やエラー文言が失われる。

### 進める順序

```
A. 先行タスク（実環境不要・今すぐ着手可）
      ↓
B. M1 実機検証 ──┐
      ↓          │ B と C は同じ実機セッション内で連続実施すると効率が良い
C. M2 実環境検証 ┘
      ↓
D. M3 / M4 実環境検証（並行可）
      ↓
E. M5 仕上げ（手順書の穴埋め・リハーサル）
```

### 必要なもの

| 項目 | 用途 | 必須か |
| --- | --- | --- |
| AWS アカウント（`ap-northeast-1`） | C・D | **必須** |
| AWS CLI（認証済み） | C・D | **必須** |
| Raspberry Pi（Bookworm 以降） | B | **必須**（全員が実機を使う前提。無い場合の検証は運営用 `simulator.py` で代替可） |
| メールアドレス（フィルタの緩いもの） | D（アドバンス B） | アドバンス B のみ |

---

## A. 先行タスク（実環境不要・今すぐ着手可）

`handson.md` は骨格を作成済み（ゴール / 進め方 / 所要時間 / 学習内容は記述完了）。
残る実環境不要のタスクは次の 2 つ。

### A-1. 構成図の作成（タスク 5.1、Q7）→ 🚧 **元ファイルは作成済み。SVG 書き出しのみ残**

**完了した内容**

- `docs/session-03/architecture.drawio` を作成（**Deployment 図**）
- レビュー指摘によりプロセス図から Deployment 図へ変更（「どの AWS サービスを利用しているか分からない」）
- AWS 公式アイコン（draw.io 内蔵 `mxgraph.aws4`）を使用。シェイプ名・カテゴリ色は
  draw.io の `Sidebar-AWS4.js` の実定義で確認済み（推測していない）
- **破線枠を CloudFormation スタック（デプロイ単位）**として、3 スタックがどのリソースを作るかを表現

**残作業（要 draw.io。ローカルには draw.io / CLI がないため実施できていない）**

1. draw.io（デスクトップ版または <https://app.diagrams.net>）で `docs/session-03/architecture.drawio` を開く
2. レイアウト・矢印の取り回しを目視で調整（エッジは draw.io の自動ルーティングに任せている）
3. 「ファイル」→「形式を指定してエクスポート」→「SVG」
   - **「図を編集可能にする」にチェック**（第2回と同じ、編集可能 SVG にする）
   - 背景は透過のままで可
4. `docs/session-03/architecture.drawio.svg` として保存
5. `handson.md`「今回の 3 つの経路」の `<!-- TODO(5.1) -->` を画像参照に置き換える

**📄 転記先**: `handson.md`「今回の 3 つの経路」

> 図の構成は `design.md` 3.1 節のデータフローと整合させてある。
> 手順書側の ASCII 図は「データの流れ」、`architecture.drawio` は「デプロイ構成」という役割分担。

### A-2. ルート README の更新（タスク 5.9）

**やること**

- 第3回の行を `T.B.D.` から `docs/session-03/handson.md` へのリンクに変更
- ディレクトリ構成図に `scripts/session-03/` 配下と `cfn/session-03/` 配下のファイルを追記
- connpass の URL は未確定なので `T.B.D.` のまま残す

> ⚠️ `handson.md` が未完成のうちにリンクを張ると、参加者が途中の文書を読む可能性がある。
> **M5 の仕上げ（E）と同時に実施する**か、リンクだけ先に張って冒頭の執筆ステータスブロックを残しておく。

---

## B. M1 実機検証（タスク 1.15）

実機 Raspberry Pi が必要。**C（M2）と同じセッションで続けて実施するのが効率的**（送信先が必要なため、
厳密には C のスタック作成を先に済ませてから B の送信確認を行う）。

### B-0. 事前確認：時刻同期（K-1）

```bash
timedatectl
```

**期待結果**: `System clock synchronized: yes` / `NTP service: active`

> ここがずれていると、CloudWatch がタイムスタンプを拒否してメトリクスが表示されない。
> 最初に潰しておく。

**📝 記録先**: `verification-log.md` → M1-2 の「実際の結果」

### B-1. セットアップ

```bash
# Raspberry Pi 側
mkdir -p ~/session-03/certs
cd ~/session-03
python3 -m venv venv
source venv/bin/activate
pip install paho-mqtt psutil
chmod +x show_metrics.sh
```

```bash
# PC 側（リポジトリのルートから）
cd scripts/session-03
scp metrics.py metrics_publisher.py load_gen.py show_metrics.sh jawsug-user@raspi.local:~/session-03/
scp certs/* jawsug-user@raspi.local:~/session-03/certs/
```

> ⚠️ `metrics_publisher.py` は `metrics.py` を import する。**両方を転送する**こと。
> 第1回・第2回はスクリプト 1 枚だったので、ここは手順書で明示的に注意する必要がある。

**📄 転記先**: `handson.md`「実装（Raspberry Pi）」の `<!-- TODO(1.15) -->`
（実行したコマンドをそのまま手順として使える）

### B-2. `show_metrics.sh` の動作確認（未実行のため要確認）

```bash
cd ~/session-03
./show_metrics.sh
```

**期待結果**: CPU / Memory の値と `total` / `available` / `used` が表示される

**確認すべき点**

- [ ] `/proc/stat` からの CPU 計算が破綻していないか（0.0% や 100.0% に張り付かないか）
- [ ] `free -m` の `available` と `show_metrics.sh` の `available` が一致するか
- [ ] `Cached:` の grep が `SwapCached:` を誤って拾っていないか（`awk '/^Cached:/'` で先頭一致にしてあるが実機で確認）

> ⚠️ このスクリプトは開発機（macOS）では `/proc` がないため一度も実行できていない。
> **バグが残っている可能性がある前提で確認する**こと。

**📝 記録先**: `verification-log.md` → M1-2

### B-3. 🔴 負荷生成の目標値と実測値の乖離を切り分ける（最重要）

開発機で **目標 40% に対し実測 55.4%（+15.4 ポイント）** の乖離を観測している。
`calculate_duty_cycle` がベースライン負荷を考慮していないため。R2-11（許容差 ±10 ポイント）に関わる。

**測定手順**

```bash
# ① ベースライン（負荷なし）を測る
./show_metrics.sh          # 数回実行して平常値を把握
# ② 本番相当のパラメータで負荷をかける
python3 load_gen.py cpu --target 90 --duration 180
# ③ 別セッションで定常区間（開始 60 秒後以降）の実測値を取る
./show_metrics.sh
top                        # 1 キーでコア別表示
```

**記録する値**

| 項目 | 実測値 |
| --- | --- |
| ベースライン CPU（負荷なし） | |
| `--target` 指定値 | 90 |
| 定常区間の実測 CPU（`show_metrics.sh`） | |
| 定常区間の実測 CPU（`top`） | |
| 差分（実測 − 指定値） | |

**判断基準と対応**

| 実測結果 | 判断 | 対応 |
| --- | --- | --- |
| 差分が ±10 ポイント以内 | R2-11 を満たす | 対応不要。開発機での乖離は環境差と結論づけて記録 |
| 差分が +10 ポイント超だが実測が 95% 以上 | 天井に張り付いている | 実用上問題なし。手順書で「実測はベースラインを含む」と明示（下記 3 案の c） |
| 差分が +10 ポイント超で実測に余裕がある | **要修正** | 下記 3 案から選択 |

**修正 3 案**

| 案 | 内容 | メリット / デメリット |
| --- | --- | --- |
| a. 実装補正 | `calculate_duty_cycle` に事前計測したベースラインを渡し `duty = (target − baseline) / 100` にする | 直感どおりの挙動になる / テストとコードの変更が必要。ベースライン自体が揺れる |
| b. 要件見直し | `requirements.md` R2-11 の許容差を実測に基づいて広げる | 変更が小さい / 要件を実装に合わせる形になる |
| c. 手順書で明示 | 「`--target` は負荷生成分の指定値であり、実測はベースラインを含む」と説明する | 実装変更なし。教材としても正確 / 参加者が一瞬戸惑う |

> 推奨は **c を基本線に、実測の乖離が大きければ a を併用**。
> ハンズオンの目的は「グラフが動くこと」なので、目標値の厳密な再現よりも
> 「負荷区間が明確に立つこと」を優先して判断する。

**📝 記録先**: `verification-log.md` → M1-S の「次のアクション」に結論を追記
＋ 8 章のフィードバック一覧を更新

### B-4. 4 者の値の突き合わせ（R2-11）

負荷生成中、定常区間で 4 つの値を同時刻に記録する。

| 取得元 | CPU (%) | メモリ (%) | 取得時刻 (JST) |
| --- | --- | --- | --- |
| `top` | | | |
| `free -m` から計算 | — | | |
| `show_metrics.sh` | | | |
| `metrics_publisher.py` 標準出力 | | | |
| **最大差分** | | | |

**期待結果**: ±10 ポイント以内で一致

**📝 記録先**: `verification-log.md` → M1-2 の 4 者比較表
**📄 転記先**: `handson.md`「デバイス側での確認」（実測値を例として掲載）

---

## C. M2 実環境検証（タスク 2.6〜2.10）— 最優先

**ここが最大の未検証リスク**。置換テンプレート `${topic(3)}` / `${cast(cpu AS String)}` が
実際に評価されるかは実環境でしか確認できない（K-3・D-3）。ここが崩れると設計の作り直しになる。

### C-1. テンプレート検証とスタック作成（タスク 2.6）

```bash
cd /path/to/jaws-ug-iot-handson-2026

aws cloudformation validate-template \
  --template-body file://cfn/session-03/iot-rules-cloudwatch.yaml \
  --region ap-northeast-1

# 作成開始時刻を記録する（R6-7: 5 分以内に CREATE_COMPLETE）
date "+%Y-%m-%d %H:%M:%S %Z"

aws cloudformation create-stack \
  --stack-name jawsug-iot-handson-s3-001 \
  --template-body file://cfn/session-03/iot-rules-cloudwatch.yaml \
  --parameters ParameterKey=DeviceNumber,ParameterValue=001 \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-northeast-1

aws cloudformation wait stack-create-complete \
  --stack-name jawsug-iot-handson-s3-001 --region ap-northeast-1
date "+%Y-%m-%d %H:%M:%S %Z"

# Outputs を取得（8 項目そろっているか）
aws cloudformation describe-stacks \
  --stack-name jawsug-iot-handson-s3-001 \
  --query 'Stacks[0].Outputs' --output table --region ap-northeast-1
```

**期待結果**

- [ ] `validate-template` が成功
- [ ] 5 分以内に `CREATE_COMPLETE`（R6-7）
- [ ] Outputs 8 項目 ＋ `NextStep` が出力される
- [ ] `MetricsConsoleUrl` のリンクが実際に開ける（手打ちで組んだ URL なので要確認）

**⚠️ 失敗しそうな箇所（事前に想定しておく）**

| 想定エラー | 原因 | 対処 |
| --- | --- | --- |
| ルール作成で構文エラー | 置換テンプレートが CFN 側で解釈された（K-3） | `MetricName` の `${topic(3)}` に `!Sub` が付いていないか確認 |
| ロググループが既存 | 前回のスタックのロググループが残っている | ~~固定名による衝突~~ は **F-1 で解消済み**（下記補足）。前回分が残っている場合は手動削除 |
| IAM ロール名の重複 | 同名ロールが残っている | 前回のスタックを削除する |

> ### ✅ C-1 補足：ロググループ名の衝突リスク（F-1・2026-08-10 解消）
>
> `iot-rules-cloudwatch.yaml` の `RuleErrorLogGroup` が `/aws/iot/session-03/rule-errors` という
> **デバイス番号を含まない固定名**だったため、共有アカウントで 2 人目のスタック作成が
> `AlreadyExists` で失敗する問題があった（D-12 との矛盾）。
>
> **対応済み**: `/aws/iot/session-03/rule-errors-raspi-${DeviceNumber}` に変更。
> あわせて `tests/test_templates.py::TestResourceNameIsolation` を追加し、
> **3 テンプレートすべての明示的なリソース名が `${DeviceNumber}` を含むこと**を機械的に検証する
> ようにした（同種の抜けを今後は自動検出できる）。`design.md` 3.4 節にも注記を追加済み。

### C-2. 証明書の発行（タスク 2.6）

コンソール操作。第2回の手順に準拠する。

1. IoT Core →「管理」→「すべてのデバイス」→「モノ」→ `jawsug-raspi-001`
2. 「証明書」タブ →「証明書を作成」
3. 4 ファイルをダウンロード（後から再取得不可）
4. ダイアログ内で「証明書をアクティブ化」
5. 証明書詳細 →「ポリシー」タブ →「ポリシーをアタッチ」→ `jawsug-s3-policy-raspi-001`
6. Endpoint を取得（「接続」→「ドメイン設定」→ `iot:Data-ATS`）

**⚠️ 今回は IoT ポリシーを最小権限に絞っている**（第2回はワイルドカード）。
`iot:Connect` はクライアント ID `jawsug-raspi-001` に限定、`iot:Publish` は自トピックのみ。
**クライアント ID が一致しないと接続が拒否される**。`metrics_publisher.py` は
`client_id=f"jawsug-{DEVICE_ID}"` としているので整合しているが、実際に接続できるか要確認。

**📝 記録先**: `verification-log.md` → M2-1
**📄 転記先**: `handson.md`「AWS 側設定」の `<!-- TODO(2.6) -->`

### C-3. メトリクスの到達確認（タスク 2.7）— 置換テンプレートの検証

```bash
# デバイス側（実機がまだ無い段階では運営用 simulator.py でも代替可）
cd ~/session-03 && source venv/bin/activate
python3 metrics_publisher.py
```

```bash
# 確認側（3 分待ってから）
aws cloudwatch list-metrics --namespace JAWSUG/IoTHandson --region ap-northeast-1

# ErrorAction ログにエラーが出ていないか（空であることが期待値）
aws logs tail /aws/iot/session-03/rule-errors-raspi-001 --region ap-northeast-1
```

**期待結果**

- [ ] 送信開始から 3 分以内に 2 メトリクスが現れる（R3-6）
- [ ] メトリクス名が **`CpuUtilization-raspi-001`**（`${topic(3)}` が評価されている ← **最重要**）
- [ ] メトリクス名が `CpuUtilization-${topic(3)}` のような**リテラル文字列になっていない**
- [ ] ErrorAction ログが空（`${cast(cpu AS String)}` が機能している）
- [ ] メトリクスのタイムスタンプが送信時刻と一致（時刻ずれがない）

**もし置換テンプレートが評価されなかった場合の切り分け**

```bash
# ルール定義が意図どおり登録されているかを確認
aws iot get-topic-rule --rule-name jawsug_s3_metrics_to_cw_raspi_001 \
  --region ap-northeast-1 --query 'rule.actions'

# 手動 publish で切り分ける（デバイス側の問題と切り離す）
aws iot-data publish --topic 'jawsug/session-03/raspi-001/metrics' \
  --cli-binary-format raw-in-base64-out \
  --payload '{"deviceId":"raspi-001","cpu":92.4,"memory":41.8,"timestamp":'$(date +%s)'}' \
  --region ap-northeast-1
```

**最終手段**（`tasks.md` 5 章のリスク表より）:
`MetricName` を `!Sub "CpuUtilization-raspi-${DeviceNumber}"` による静的名に切り替える。
デバイス分離は `DeviceNumber` で担保されるので設計は成立する（D-2 の「トピックを識別子に使う」
という教育的価値は失われるため、手順書の説明を調整する）。

**📝 記録先**: `verification-log.md` → M2-2

### C-4. 負荷生成でグラフを動かす（タスク 2.8）

```bash
python3 load_gen.py cpu --target 90 --duration 180
```

コンソール操作: CloudWatch → メトリクス → `JAWSUG/IoTHandson` → 対象メトリクスを選択 →
**期間を 1 分、統計を平均に設定**

**期待結果**

- [ ] 負荷区間が台形として視認できる
- [ ] 平常値との差が 30 ポイント以上（R2-7）
- [ ] 期間 5 分では差が縮むことも確認（4.3 節の裏付け・手順書のコラム素材になる）

**記録する値**

| 項目 | 値 |
| --- | --- |
| 平常時 CPU（1 分平均） | |
| 負荷時 CPU（1 分平均） | |
| 差分 | |
| 期間 5 分での負荷時 CPU | |

**📝 記録先**: `verification-log.md` → M2-3
**証跡**: `evidence/m2/2.8-graph-1min.png` / `2.8-graph-5min.png`
**📄 転記先**: `handson.md`「動作確認」の `<!-- TODO(2.8) -->`

### C-5. 3 点セットの突き合わせ（タスク 2.9）

負荷開始から **1 分以上経過した定常区間**で、同一時刻の 3 値を比較する。

| 時刻 (JST) | ① `show_metrics.sh` | ② publisher 送信値 | ③ CloudWatch（1 分平均） | 最大差分 | 判定 |
| --- | --- | --- | --- | --- | --- |
| | | | | | |
| | | | | | |
| | | | | | |

**期待結果**: ±5 ポイント以内（R2-12）

> 立ち上がり・立ち下がり区間は平均化の影響で乖離する。**定常区間で比較する**こと。

**📝 記録先**: `verification-log.md` → M2-4（CPU とメモリの 2 表）

### C-6. スタック削除の確認（タスク 2.10）

```bash
# 証明書のデタッチ → 無効化 → 削除 → スタック削除
# teardown.sh の元ネタになるので、手順と所要時間を記録する
DEVICE_NUMBER=001 bash scripts/session-03/teardown.sh
```

**期待結果**

- [ ] 削除対象一覧が表示され `y/N` で確認される
- [ ] `DELETE_COMPLETE` になる
- [ ] 残存確認で 0 件と報告される

> ⚠️ `teardown.sh` は一度も実行していない。**シェルスクリプトのバグが残っている可能性が高い**。
> 特に `list-thing-principals` の結果を `while read` で回す部分（サブシェルになるため
> 変数が外に出ない構造）と、`describe-log-groups` を使っていない残存確認は要確認。
> D・E に進む前に、ここで一度通しておくと後が楽になる。

**📝 記録先**: `verification-log.md` → M2-5
**📄 転記先**: `handson.md`「後片付け」

---

## D. M3 / M4 実環境検証（並行可）

### D-1. アドバンス A：Lambda 連携（タスク 3.5〜3.7）

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

- [ ] **ランタイム `python3.13` が利用可能**（Q8 の確定 ← 失敗したら `python3.12` に落とす）
- [ ] 構造化ログ（`"event":"metrics_received"`）が出力される
- [ ] 保持期間が 3 日（R4-5）
- [ ] Logs Insights のクエリでレコードが取れる（R4-6）

```
fields @timestamp, deviceId, cpu, memory
| filter event = "metrics_received"
| sort @timestamp desc
| limit 20
```

**独立動作の確認（タスク 3.6、R4-8）**

1. 両ルール有効で、同一メッセージが Metrics と Logs の両方に反映されることを確認
2. Lambda の呼び出し権限を一時的に外して失敗させる
3. その間も CloudWatch Metrics への送信が継続していることを確認
4. 権限を戻す

**欠落フィールドの確認（タスク 3.7、R4-4）**

```bash
aws iot-data publish --topic 'jawsug/session-03/raspi-001/metrics' \
  --cli-binary-format raw-in-base64-out \
  --payload '{"deviceId":"raspi-001","memory":41.8,"timestamp":'$(date +%s)'}' \
  --region ap-northeast-1
```

→ Lambda が `level=WARN` で継続し、例外で落ちないこと

**📝 記録先**: `verification-log.md` → M3-2 / M3-3 / M3-4
**📄 転記先**: `handson.md`「アドバンス A」

### D-2. アドバンス B：アラーム通知（タスク 4.3〜4.6）

> ⚠️ **順序厳守**: スタック作成 → **承認** → `Confirmed` 確認 → **その後に**負荷生成。
> 承認前に負荷をかけると「アラームは鳴ったのにメールが来ない」という切り分けの難しい状態になる（K-6）。

```bash
aws cloudformation create-stack \
  --stack-name jawsug-iot-handson-s3-alarm-001 \
  --template-body file://cfn/session-03/advanced-alarm.yaml \
  --parameters ParameterKey=DeviceNumber,ParameterValue=001 \
               ParameterKey=NotificationEmail,ParameterValue=<自分のメールアドレス> \
  --region ap-northeast-1

# 承認前の状態を確認（K-6 の裏付けを取る）
aws cloudformation describe-stacks --stack-name jawsug-iot-handson-s3-alarm-001 \
  --query 'Stacks[0].StackStatus' --region ap-northeast-1
aws sns list-subscriptions-by-topic --topic-arn <TOPIC_ARN> --region ap-northeast-1
```

**記録すること（タスク 4.3）**

| 確認項目 | 結果 |
| --- | --- |
| 確認メール到着までの時間 | |
| 迷惑メールフォルダに入ったか | |
| **承認前のスタック状態**（`CREATE_COMPLETE` になるか） | |
| 承認前の `SubscriptionArn` | `PendingConfirmation` か |
| 承認後のステータス | `Confirmed` か |

**アラーム発火（タスク 4.4）**

```bash
python3 load_gen.py cpu --target 90 --duration 180
```

| 計測項目 | 値 |
| --- | --- |
| 負荷開始時刻 | |
| ALARM 遷移時刻 | |
| 発火までの所要時間 | |
| アラームメール受信時刻 | |
| 負荷終了時刻 | |
| OK 復帰時刻 | |
| 復旧メール受信時刻 | |

**しきい値の最終確定（タスク 4.5、Q2）**

- 送信を止めた状態で誤発火しないこと（`TreatMissingData: notBreaching` の効果）を確認
- 確実に発火し、かつ誤発火しない値を確定 → 必要なら `design.md` / `requirements.md` R5-3 を更新

**再作成時の再承認（タスク 4.6）**

- スタック削除 → 同一アドレスで再作成 → 確認メールが再送されることを確認
- ハマりポイント表に載せる文言を確定

**📝 記録先**: `verification-log.md` → M4-1 / M4-2 / M4-3 / M4-4
**📄 転記先**: `handson.md`「アドバンス B」

---

## E. M5 仕上げ（タスク 5.2〜5.11）

B〜D の結果が揃ってから実施する。

| # | やること | 材料 |
| --- | --- | --- |
| E-1 | `handson.md` の TODO を埋める（`<!-- TODO(...) -->` を全削除） | B〜D の記録 |
| E-2 | ハマりポイント表を実績で書き換える（タスク 5.7） | B〜D で遭遇した事象 ＋ `verification-log.md` 4 章の反映候補 |
| E-3 | 冒頭の「🚧 執筆ステータス」ブロックを削除 | — |
| E-4 | README を更新（タスク 5.9） | A-2 |
| E-5 | 通し実行リハーサル（タスク 5.10） | 手順書だけを見て、まっさらな状態から実行。所要時間を計測 |
| E-6 | 最終確認（タスク 5.11） | `pytest` / `cfn-lint` / マスキング確認 / `certs/` 未コミット確認 |

### E-6 の実行コマンド

```bash
cd scripts/session-03 && source .venv/bin/activate
pytest
cfn-lint ../../cfn/session-03/*.yaml
grep -rniE "[0-9]{12}|@[a-z0-9.-]+\.(com|jp|net)" evidence/ || echo "マスキング漏れなし"
git ls-files | grep -i "certs/" || echo "certs は未コミット"
grep -rn "TODO\|🚧" ../../docs/session-03/handson.md || echo "TODO 残りなし"
```

---

## F. 実装レビューで見つかった要修正候補

実環境検証の前に、コードを読み返して気づいた点。**未検証の推測を含む**ので、
実環境で挙動を確認してから直すか、先に直すかを判断すること。

| # | 箇所 | 内容 | 優先度 | 状態 |
| --- | --- | --- | --- | --- |
| F-1 | `iot-rules-cloudwatch.yaml` | `RuleErrorLogGroup` がデバイス番号を含まない固定名。共有アカウントで衝突する | **高** | ✅ **解消**（2026-08-10。テストで再発防止） |
| F-2 | `load_gen.py` | duty cycle がベースライン負荷を考慮しない | ~~**高**~~ | ✅ **解消（実装変更なし）**：実機実測で**目標 90.0% に対し実測 90.2%（差 +0.2 ポイント）**。ラズパイのアイドル CPU が 1〜2% と低いため乖離しない。開発機（macOS・多コア・高ベースライン）特有の事象だった。手順書に実測値を反映して対応完了 |
| **F-3d** | `teardown.sh` | **アタッチしていない証明書を検出できず孤児として残る**のに「✅ 削除完了」と表示していた。2026-08-13 の実行で実害を確認 | **高** | ✅ **解消**：ポリシーのターゲットからも探索し、0 件なら警告表示に変更 |
| **F-3e** | `teardown.sh` | **UTF-8 ロケールで削除対象一覧が文字化けしスタック名が消える**（`$VAR` の直後に全角文字）。R8-9 が実質機能していなかった | **高** | ✅ **解消**：`${VAR}` ブレース付きに修正。第1回・第2回は該当なし |
| F-3a | `teardown.sh` | `set -e` と `aws cloudformation wait stack-delete-complete` の組み合わせ。スタックが `DELETE_FAILED` になると `wait` が非ゼロを返し、**ステップ 3〜5（ローカル `certs/` 削除・残存確認）が実行されない** | 中 | 🔴 未対応（正常系の完走は 2026-08-13 に確認済み） |
| F-3c | `teardown.sh` | 各 AWS 呼び出しが `2>/dev/null \|\| true` でエラーを握り潰し、**失敗しても成功と表示される** | **高に格上げ** | 🟡 **一部解消**（F-3d / F-3f）。**この誤表示が実際に害を出した**ため、以後スクリプトの表示は独立検証で裏取りする |
| F-3f | `teardown.sh` | Thing が存在しなくても「✅ Thing の削除完了」と表示していた | 低 | ✅ **解消**：存在確認してから出し分け |
| F-3b | ~~`teardown.sh`~~ | 残存確認でロググループをチェックしていない | 低 | ✅ **解消**（2026-08-10） |
| F-4 | `show_metrics.sh` | 一度も実行していない（`/proc` 依存）。`awk '/^Cached:/'` の誤検出や CPU 計算の破綻を実機で確認 | 中 | ✅ **解消（2026-08-13 実機実行）**：CPU 1.7%・Memory 31.1% と妥当。`(1872−1289)/1872=31.14%` と表示値が一致。`SwapCached:` の誤検出なし（`used` が妥当な値） |
| **F-9** | `load_gen.py` | **CPU 負荷の終了時に大量のトレースバック**（`AssertionError: can only test a child process`）。`multiprocessing` の fork で**子が親のシグナルハンドラを継承**し、`terminate()` の SIGTERM で親用クリーンアップが子で走っていた。「実終了」も二重表示 | **高** | ✅ **解消（2026-08-13）**：ワーカー先頭で SIGINT/SIGTERM を解除。親側のクリーンアップを冪等化。**Red → Green を遵守**（回帰テスト 2 件追加） |
| **F-8** | `show_metrics.sh` | **OS のタイムゾーンで時刻を取得しているのにラベルは「JST」固定**。貸出機が `Europe/London` だと 8〜9 時間ずれた時刻を JST と表示し、突き合わせ（R2-12）で混乱する | **高** | ✅ **解消**（2026-08-13。`TZ=Asia/Tokyo date` に変更） |
| F-5 | `metrics_publisher.py` | 送信間隔が publish/ネットワーク時間の分だけ少しずつ後ろにずれる（ハンズオン時間なら実用上問題ない見込み） | 低 | 🔴 未対応 |
| F-6 | `simulator.py` | `--spike-level` は CPU のみに効き、メモリは固定値 45%。Alarm は CPU 対象（D-11）なので実用上問題ない | 低 | ✅ **対応不要**（運営用の予備に降格し手順書に載せないため） |
| **F-12** | 手順書 / 運営 | **SNS サブスクリプションが意図せず解除されることがある**（メール末尾の解除リンクがクライアントに先読みされる等）。アラームは鳴るのに通知が来ない状態になり切り分けが難しい | **中** | 🟡 **文書化で対応**（復旧手順・予防策を手順書に追記）。**再現条件は未特定**。リハーサルで再発を観察 |
| **F-13** | `scripts/session-03/metrics_publisher.py` | **実 IoT エンドポイントがコミットされ、公開リポジトリに push されていた**（`f5c9ddc`）。手順書が「ファイルの設定値を書き換える」方式のため起きた | **高** | 🟡 **作業ツリーは修正済み**（プレースホルダに戻し、環境変数対応を追加。回帰テスト 7 件追加）。**履歴に残っている件はオーナー判断待ち** |
| F-7 | 4 文書のヘッダー | 配置先を `specs/` と記載しているが実体は `spec/` | 低 | 🔴 未対応 |

> **教訓（2026-08-13）**：`teardown.sh` は静的検証（`bash -n` / `shellcheck`）を通っていたが、
> **一度も実行していなかったため重大な不具合 2 件（F-3d / F-3e）を見逃していた**。
> しかも片方は「✅ 完了」と表示しながら何もしていない類のもので、**出力を信じると気づけない**。
> スクリプトは「実行する」だけでなく「**結果を別の手段で確認する**」ところまでを検証とする。

---

## G. 記録先の対応表（早見）

| 実行した作業 | `verification-log.md` のエントリ | `handson.md` のセクション |
| --- | --- | --- |
| B-0〜B-4 実機確認 | M1-2 / M1-S に追記 | 実装（Raspberry Pi）、デバイス側での確認 |
| C-1〜C-2 スタック作成・証明書 | M2-1 | AWS 側設定 |
| C-3 メトリクス到達 | M2-2 | 動作確認 |
| C-4 グラフ変化 | M2-3 | 動作確認 |
| C-5 3 点セット | M2-4 | デバイス側での確認 |
| C-6 スタック削除 | M2-5 | 後片付け |
| D-1 Lambda | M3-2 / M3-3 / M3-4 | アドバンス A |
| D-2 Alarm・Email | M4-1 / M4-2 / M4-3 / M4-4 | アドバンス B |
| E-5 リハーサル | M5-1 | 所要時間（実測に更新） |
| E-6 最終確認 | M5-2 | — |

証跡ファイルは `evidence/{m1..m5}/{タスクID}-{内容}.{拡張子}` に保存し、
**AWS アカウント ID・証明書 ID・メールアドレスをマスクしてから**コミットする（R9-7）。
