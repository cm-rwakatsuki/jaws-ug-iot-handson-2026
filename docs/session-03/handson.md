# 第3回：IoT Rules Engine で他の AWS サービスと連携し、データを自動処理・分析してみよう

> ## 🚧 執筆ステータス（公開前に必ずこのブロックを削除する）
>
> 本手順書は **作成途中** です。実 AWS 環境・実機での検証（`spec/tasks.md` の M2〜M4）が
> 未完了のため、以下のセクションは未確定です。
>
> | セクション | 状態 | 埋めるための作業 |
> | --- | --- | --- |
> | ゴール / 進め方 / 所要時間 / 学習内容 | ✅ 記述済み（実測不要） | — |
> | 構成図 | ✅ 完成（`architecture-v2.svg` / 元ファイル `architecture-v2.drawio`） | — |
> | AWS 側設定 | 🚧 骨格のみ | タスク 2.6（画面操作の確認） |
> | 実装（Raspberry Pi） | 🚧 骨格のみ | タスク 1.15 |
> | 動作確認 | 🚧 骨格のみ | タスク 2.7〜2.9 |
> | デバイス側での確認 | 🚧 骨格のみ | タスク 1.15 |
> | Advanced Course1 / 2 | ❌ 未着手 | タスク 3.5〜3.7 / 4.3〜4.6 |
> | ハマりポイント | 🚧 設計時の想定のみ | タスク 5.7（M1〜M4 の実績を反映） |
> | 後片付け | 🚧 骨格のみ | タスク 5.8 |
>
> 検証の実行手順は [`../../scripts/session-03/spec/next-actions.md`](../../scripts/session-03/spec/next-actions.md) にまとめてあります。

## ゴール

- Rules の構成要素（SQL ステートメント・トピックフィルター・アクション）を説明できる
- Rules から CloudWatch Metrics へデータを送り、グラフで可視化できる
- 1 つのメッセージを複数のアクションへ分岐できることを理解する
- （Advanced Course1）Rules から Lambda を起動し、CloudWatch Logs にログを残せる
- （Advanced Course2）CloudWatch Alarm → SNS → Email の通知経路を構築できる

第1回ではデバイスからクラウドへデータを「送り」、第2回では Device Shadow でクラウドからデバイスを「制御」しました。今回はその先、**届いたデータをクラウド側で自動的に処理する**部分を扱います。

主役は **Rules Engine（ルールエンジン）** です。SQL を書くだけで、コードを一行も書かずに他の AWS サービスへデータを流せます。

---

## 進め方

Raspberry Pi から CPU 使用率とメモリ使用率を送信し、Rules 経由で CloudWatch Metrics に格納してグラフで可視化します。さらに負荷生成スクリプトで意図的に使用率を上下させ、**自分の操作がクラウドのグラフに現れる**ことを確認します。

AWS 側の設定から動作確認まで、**この手順書だけで完結**します。第1回・第2回の受講は前提としません。

今回は**参加者全員が会場で貸出 Raspberry Pi（実機）を操作**します。自分が動かした負荷が、そのままクラウドのグラフに現れるところまでを手を動かして確認します。

---

## 所要時間（目安）

| パート | 時間 |
|---|---|
| Wi-Fi 接続と SSH 接続 | 10分 |
| AWS 側設定（スタック作成・証明書発行） | 20分 |
| デバイス側実装（転送・セットアップ・実行） | 20分 |
| 動作確認（負荷生成・グラフ確認・値の突き合わせ） | 15分 |
| Advanced Course1（Lambda 連携） | 10分 |
| Advanced Course2（アラーム通知） | 10分 |
| 応用・質疑 | 5分 |
| **合計** | **90分** |

> **Basic Course**（AWS 側設定〜動作確認）だけで **60 分**で完結します。Advanced Course1・2 は時間に余裕がある方向けです。

---

## 学習内容

### Rules Engine とは

AWS IoT Core に届いた MQTT メッセージを **SQL で選別し、他の AWS サービスへ渡す**仕組みです。デバイスとクラウドサービスの間に立つ「振り分け係」と考えると分かりやすいです。

```
デバイス ──MQTT──▶ IoT Core ──▶ Rules ──▶ CloudWatch / Lambda / S3 / DynamoDB / ...
                                  ▲
                          ここで SQL で選別する
```

### Rules の 3 つの構成要素

| 要素 | 役割 | 今回の例 |
|---|---|---|
| **トピックフィルター** | どのトピックのメッセージを対象にするか | `jawsug/session-03/+/metrics` |
| **SQL ステートメント** | メッセージから何を取り出すか、どう絞り込むか | `SELECT * FROM 'jawsug/session-03/+/metrics'` |
| **アクション** | 取り出した結果をどこへ渡すか（1 ルールに最大 10 個） | `cloudwatchMetric` × 2 |

これに加えて、アクションが失敗したときの逃げ道として **エラーアクション**を設定できます。今回は CloudWatch Logs にエラーを記録します。

### トピックフィルターのワイルドカード

| 記号 | 意味 | 例 |
|---|---|---|
| `+` | 1 階層だけの任意一致 | `jawsug/session-03/+/metrics` は `.../raspi-001/metrics` にも `.../raspi-002/metrics` にもマッチ |
| `#` | 以降すべての階層に一致 | `jawsug/#` は `jawsug/` 配下すべてにマッチ |

今回は `+` を使い、**デバイス番号の部分だけをワイルドカードにします**。これで参加者全員が同じルール定義を使えます。

### 置換テンプレート

SQL の中では `${...}` の形で値を差し込めます。今回使うのは次の 2 つです。

| 書き方 | 意味 |
|---|---|
| `${topic(3)}` | トピックの 3 番目のセグメント。`jawsug/session-03/raspi-001/metrics` なら `raspi-001` |
| `${cast(cpu AS String)}` | ペイロードの `cpu` を文字列に変換 |

**デバイスの識別にペイロードの `deviceId` ではなくトピックを使う**のがポイントです。ペイロードは中身を書き換えられますが、トピックは IoT ポリシーで縛れるため、識別子として信頼できます。「トピック設計がそのまま識別子になる」という IoT の基本的な考え方です。

### 今回のコース構成

今回は 3 つのコースに分かれています。**Basic Course だけで完結**します。

![第3回 構成図：IoT Rules Engine から他の AWS サービスへの連携](./architecture-v2.svg)

| コース | ねらい | 経路 |
|---|---|---|
| **Basic Course** | CloudWatch Metrics でデバイスの振る舞いを確認する | Raspberry Pi → IoT Core → Rules → CloudWatch |
| **Advanced Course1** | 様々な AWS サービスと連携する | Rules → Lambda → CloudWatch Logs |
| **Advanced Course2** | 自動連携する | CloudWatch → Alarm → SNS → メール |

図の中心にある **Rules** が今回の主役です。ここから先を差し替えるだけで、CloudWatch にも Lambda にも
つながることが図から読み取れます。Advanced Course1 と Advanced Course2 は、どちらも
**Basic Course で作ったものをそのまま使い、Rules の先を増やしているだけ**です。

### この回の核心：アクションによって SQL の効き方が変わる

同じトピック・同じペイロードに対して、**2 本のルールを並走させます**。ここで面白いのは、アクションの種類によって SQL の `SELECT` の意味が変わることです。

| アクション | `SELECT` の内容が結果に影響するか |
|---|---|
| `cloudwatchMetric` | **しない**。どの列を選んでも、アクション側で指定した `MetricValue` などが使われる |
| `lambda` | **する**。`SELECT` の出力がそのまま Lambda のイベントになる |

だから Basic Course の SQL は `SELECT *` で十分ですが、Advanced Course1 では次のように整形します。

```sql
SELECT deviceId, cpu, memory, timestamp,
       topic() AS topic, timestamp() AS receivedAtMs
FROM 'jawsug/session-03/+/metrics'
```

「Rules は接続先を差し替えるだけで多様な AWS サービスと連携できる」ことと同時に、「アクションごとに作りが違う」ことも押さえておくと、実務で設計するときに迷いません。

### 知っておくと得する制約

#### CloudWatch メトリクスアクションは Dimension を指定できない

CloudWatch では通常、`DeviceId=raspi-001` のような **Dimension**（次元）でメトリクスを分類します。ところが Rules の `cloudwatchMetric` アクションは Dimension を指定できません。

そこで今回は **メトリクス名の末尾にデバイス名を入れて**分離します。

| 項目 | 値 |
|---|---|
| 名前空間 | `JAWSUG/IoTHandson`（全員共通） |
| メトリクス名 | `CpuUtilization-raspi-001` / `MemoryUtilization-raspi-001` |

> Dimension を使いたい場合は、Lambda を経由して自分で `PutMetricData` を呼ぶという選択肢があります。これが Advanced Course1 のもう一つの動機です。制約を知ると、なぜ Lambda を挟む構成が世の中に多いのかが見えてきます。

#### メトリクスは 60 秒粒度で保存される

`cloudwatchMetric` アクションは分解能を指定できないため、メトリクスは**標準分解能（60 秒粒度）**で保存されます。10 秒間隔で送信すると、1 分あたり 6 サンプルが同じ分に集約されます。

このため、グラフを見るときは **期間を 1 分に変更**してください。既定の 5 分のままだと負荷の変化が平均化されて埋もれてしまいます。

| 設定 | 値 | 理由 |
|---|---|---|
| 期間（Period） | **1 分** | 5 分では負荷区間が平均化される |
| 統計（Statistic） | 平均（Average） | 瞬間値を見たいときは最大（Maximum） |
| 負荷の継続時間 | **180 秒以上** | 1 分平均のデータポイントが 2〜3 点得られ、台形として見える |

---

## AWS 側設定

> 🚧 **このセクションは骨格のみです**（タスク 2.6 で実画面を確認して記述します）。

デバイスを AWS IoT Core に接続し、Rules で CloudWatch Metrics へ流すための構成を作ります。

- CloudFormation テンプレート：[cfn/session-03/iot-rules-cloudwatch.yaml](../../cfn/session-03/iot-rules-cloudwatch.yaml)
- スタック名：`jawsug-iot-handson-s3-001`
- パラメータ：`DeviceNumber` = `001`（3 桁数字）

作成されるリソース：

| リソース | 名前 |
|---|---|
| IoT Thing | `jawsug-raspi-001` |
| IoT ポリシー | `jawsug-s3-policy-raspi-001` |
| IoT ルール | `jawsug_s3_metrics_to_cw_raspi_001` |
| ルールエラー用ロググループ | `/aws/iot/session-03/rule-errors-raspi-001` |

証明書は CloudFormation では発行できないため、第2回と同様に手動で発行してポリシーをアタッチします。

<!-- TODO(2.6): 以下を実画面で確認して記述
  - スタック作成の画面手順（第2回の A ルートに準拠）
  - Outputs の確認（8 項目のうち控えるべきもの）
  - 証明書の発行・アクティブ化・ポリシーアタッチ
  - Endpoint の取得
-->

---

## 実装（Raspberry Pi）

> 🚧 **このセクションは骨格のみです**（タスク 1.15 で実機確認して記述します）。

使用するファイル：

| ファイル | 役割 |
|---|---|
| [metrics.py](../../scripts/session-03/metrics.py) | CPU / メモリ取得とペイロード組み立て |
| [metrics_publisher.py](../../scripts/session-03/metrics_publisher.py) | MQTT で送信するメインスクリプト |
| [load_gen.py](../../scripts/session-03/load_gen.py) | 負荷生成（CPU / メモリ） |
| [show_metrics.sh](../../scripts/session-03/show_metrics.sh) | デバイス側の使用率確認ヘルパー |


書き換える設定：

```python
ENDPOINT  = "xxxxxx-ats.iot.ap-northeast-1.amazonaws.com"  # 取得した Endpoint に書き換える
DEVICE_ID = "raspi-001"  # 割り当てられた番号に書き換える
```

<!-- TODO(1.15): 以下を実機で確認して記述
  - 証明書のリネームと配置（第2回と同じ 3 ファイル）
  - scp での転送手順
  - venv セットアップ（paho-mqtt, psutil のインストール）
  - 実行と出力例（実際の標準出力を貼る）
  - 並行実行の手段（SSH 2 セッション / tmux / nohup）
-->

---

## 動作確認

> 🚧 **このセクションは骨格のみです**（タスク 2.7〜2.9 で確認して記述します）。

<!-- TODO(2.7): メトリクスの到達確認
  - CloudWatch → メトリクス → JAWSUG/IoTHandson を開く
  - CpuUtilization-raspi-001 / MemoryUtilization-raspi-001 が現れることを確認
  - 期間を 1 分に変更する操作を明示（重要）
-->

<!-- TODO(2.8): 負荷生成でグラフを動かす
  - load_gen.py cpu --target 90 --duration 180
  - 台形が視認できることをスクリーンショットで示す
  - 期間 5 分と 1 分の見え方の違いも示す
-->

<!-- TODO(2.9): 3 点セットの突き合わせ
  - show_metrics.sh / publisher 出力 / CloudWatch の 3 値を比較
  - 負荷開始から 1 分以上経過した定常区間で比較すること
-->

---

## デバイス側での確認

> 🚧 **このセクションは骨格のみです**（タスク 1.15 で実機の値を確認して記述します）。

クラウド側のグラフだけを見ていると「本当にこの値が送られているのか」が分かりません。デバイス側でも実測値を確認し、両者を突き合わせます。

### 確認コマンド一覧

追加インストールなしで使えるものを主軸にします。

| 用途 | コマンド | 追加インストール |
|---|---|---|
| CPU / メモリをリアルタイム確認 | `top`（`1` でコア別表示、`q` で終了） | 不要 |
| メモリ使用量を人間可読で確認 | `free -h` / `free -m` | 不要 |
| CPU / メモリの推移を一定間隔で確認 | `vmstat 1` | 不要 |
| ロードアベレージ | `uptime` / `cat /proc/loadavg` | 不要 |
| CPU 使用率上位のプロセス | `ps aux --sort=-%cpu \| head` | 不要 |
| メモリ使用率上位のプロセス | `ps aux --sort=-%mem \| head` | 不要 |
| メモリの詳細内訳 | `cat /proc/meminfo` | 不要 |
| 送信中の値 | `metrics_publisher.py` の標準出力 | 不要 |
| 対話的な可視化 | `htop` | 必要（`sudo apt install htop`、任意） |
| CPU 使用率の統計 | `mpstat 1` | 必要（`sudo apt install sysstat`、任意） |

**`top`（CPU）** と **`free -m`（メモリ）** を主軸に使ってください。

### ⚠️ `free` の `used` と CloudWatch の値は一致しません

これは仕様です。定義が違います。

| 見ている場所 | 定義 |
|---|---|
| `metrics_publisher.py` が送る値 / CloudWatch | `(total − available) / total × 100` |
| `free` コマンドの `used` 列 | buff/cache を**除外**した使用量 |

`free -m` を見るときは **`available` 列**に注目してください。`show_metrics.sh` を使うと、送信値と同じ定義の値に加えて `total` / `available` / `used` を並べて表示するので、違いが目で分かります。

<!-- TODO(1.15): 以下を実機で確認して記述
  - show_metrics.sh の実行結果（実際の出力を貼る）
  - 「負荷をかける → デバイス側で確認 → CloudWatch で確認 → 突き合わせる」の流れ
  - 4 者の値の比較表（実測値）
  - 並行実行の手段
-->

---

## Advanced Course1：様々な AWS サービスと連携する（Rules → Lambda）

> ❌ **未着手**（タスク 3.5〜3.7）

- CloudFormation テンプレート：[cfn/session-03/advanced-lambda.yaml](../../cfn/session-03/advanced-lambda.yaml)
- スタック名：`jawsug-iot-handson-s3-lambda-001`

<!-- TODO(3.5-3.7): スタック作成 → 送信 → Logs Insights でのクエリ確認 -->

---

## Advanced Course2：自動連携する（Alarm → SNS → メール）

> ❌ **未着手**（タスク 4.3〜4.6）

- CloudFormation テンプレート：[cfn/session-03/advanced-alarm.yaml](../../cfn/session-03/advanced-alarm.yaml)
- スタック名：`jawsug-iot-handson-s3-alarm-001`

> ⚠️ **順序が重要です**。スタック作成 → **確認メールを承認** → SNS でステータスが `Confirmed` になったことを確認 → **その後に**負荷生成でアラームを発火させてください。承認前はアラームが鳴ってもメールは届きません。

<!-- TODO(4.3-4.6): 承認フローと発火確認の手順、企業メールのフィルタ注意（個人アドレス推奨） -->

---

## ハマりポイントと対処法

> 🚧 現時点では**設計時に想定した項目**のみです。タスク 5.7 で M1〜M4 の実績を反映します。

| 症状 | 原因 | 対処 |
|---|---|---|
| メトリクスが表示されない | グラフの期間が既定の 5 分のまま | 期間を 1 分に変更する |
| メトリクスが表示されない | Raspberry Pi の時刻がずれている（CloudWatch は 2 時間以上未来／2 週間以上過去の時刻を拒否） | `timedatectl` で `System clock synchronized: yes` を確認 |
| `free` の値と CloudWatch の値が合わない | 定義が違う（`used` は buff/cache を除外） | `available` 列を見る。`show_metrics.sh` で同一定義の値を確認 |
| スタック作成が失敗する（ルール名） | IoT ルール名にハイフンは使えない（`[a-zA-Z0-9_]` のみ） | `DeviceNumber` は 3 桁数字で指定する |
| メールが届かない | サブスクリプション未承認 | SNS コンソールでステータスが `Confirmed` か確認 |
| メールが届かない | 迷惑メールフォルダに入っている | 差出人 `no-reply@sns.amazonaws.com` で検索 |
| メールが届かない | スタックを再作成した | 再作成すると再承認が必要。前回承認済みでも届かない |
| `pip install` が失敗する | `error: externally-managed-environment` | venv を作ってからインストールする |
| 接続できるが Publish が拒否される | 証明書の有効化・ポリシー未アタッチ | 証明書タブでステータスとポリシーを確認 |
| 証明書エラー | ファイル名・パスのミス | `certs/` の 3 ファイル名を確認 |

<!-- TODO(5.7): M1〜M4 の実績を反映する -->

---

## 発展課題（時間が余ったら）

Rules は今回扱った CloudWatch / Lambda / SNS 以外にも、多くのサービスへ連携できます。

| 連携先 | 用途の例 |
|---|---|
| S3 | 生データを長期保管する |
| DynamoDB | 最新値を高速に読み書きする |
| Kinesis Data Streams | 大量データをストリーム処理する |
| Timestream | 時系列データを分析する |
| SQS | 後続処理をキューで疎結合にする |

「アクションを差し替えるだけで連携先が変わる」ことを、今回の 2 本のルールで体験できたはずです。

---

## 後片付け

> 🚧 **未検証**（タスク 5.8）

```bash
cd scripts/session-03
DEVICE_NUMBER=001 bash teardown.sh
```

削除対象を表示して確認を求めたうえで、証明書 → Advanced Course2 → Advanced Course1 → Basic Course のスタック → ローカル `certs/` の順に削除し、最後に残存確認の結果を表示します。

> 💡 **CloudWatch Metrics（カスタムメトリクス）には削除 API がありません**。保持期間の経過で自動的に消えます。課金対象の CloudWatch Alarm はスタック削除で消えるので、後片付けを実行すれば月額課金は止まります。

> 💡 実行前に `aws sts get-caller-identity` で AWS 認証が通っているか確認してください。
