# 第3回ハンズオン 要件定義書（requirements.md）

- **プロジェクト**: JAWS-UG IoT 専門支部 IoT Core ハンズオン 2026 / 第3回
- **テーマ**: IoT Rules Engine で他の AWS サービスと連携し、データを自動処理・分析してみよう
- **配置先**: `scripts/session-03/specs/requirements.md`
- **リポジトリ**: https://github.com/cm-rwakatsuki/jaws-ug-iot-handson-2026
- **ステータス**: Draft（レビュー待ち）

---

## 1. Introduction

第3回ハンズオンでは、AWS IoT Core の **Rules Engine（ルールエンジン）** を主題とする。

第1回（MQTT でのデータ送信）、第2回（Device Shadow による双方向制御）に続き、本回は「**IoT Core に届いたデータを、SQL で選別して他の AWS サービスへ自動で流す**」という Rules の役割を体験する。

参加者は Raspberry Pi から CPU 使用率・メモリ使用率を MQTT で送信し、Rules 経由で CloudWatch Metrics に格納してグラフで可視化する。さらに負荷生成スクリプトで意図的に使用率を変動させ、**自分の操作がクラウド上のグラフに反映される**ことを体感する。

アドバンス課題では、同一のメッセージを Rules から Lambda / SNS 側へ分岐させ、「Rules は接続先を差し替えるだけで多様な AWS サービスと連携できる」ことを示す。

### 1.1 学習ゴール

| # | ゴール |
| --- | --- |
| G1 | Rules の構成要素（SQL ステートメント・トピックフィルター・アクション）を説明できる |
| G2 | Rules から CloudWatch Metrics へデータを送り、グラフで可視化できる |
| G3 | 1 つのメッセージを複数アクションへ分岐できることを理解する |
| G4 | Rules から Lambda を起動し、CloudWatch Logs にログを残せる（アドバンス） |
| G5 | CloudWatch Alarm → SNS → Email の通知経路を構築できる（アドバンス） |

### 1.2 対象アーキテクチャ

**基本（必須）**

```
Raspberry Pi ──MQTT/TLS──▶ AWS IoT Core ──▶ Rules ──▶ CloudWatch Metrics ──▶ メトリクスグラフ
```

**アドバンス A：Lambda 連携**

```
Raspberry Pi ──▶ AWS IoT Core ──▶ Rules ──▶ Lambda ──▶ CloudWatch Logs
```

**アドバンス B：アラーム通知**

```
Raspberry Pi ──▶ AWS IoT Core ──▶ Rules ──▶ CloudWatch Metrics
                                              └─▶ CloudWatch Alarm ──▶ SNS Topic ──▶ Email Subscription ──▶ 参加者のメール
```

### 1.3 想定参加者・前提

- AWS アカウントを自身で操作できる（東京リージョン `ap-northeast-1` を使用）
- **参加者は全員が会場に来場し、貸出 Raspberry Pi（Raspberry Pi OS Bookworm 以降、`jawsug-user`）の実機を操作する**
- **リモート参加は想定しない。実機なしでの参加も想定しない**（2026-08-13 に前提を確定）
- 第1回・第2回の受講は**前提としない**（手順書単体で完結させる）

> **前提変更の記録（2026-08-13）**: 当初は「リモート参加者・実機なし参加者はシミュレーターで代替」を
> 想定していたが、**全員が会場で実機を触る**前提に確定した。これに伴い R1-9 と NFR-9 を削除し、
> `simulator.py` は参加者向けの提供物ではなく**運営用の予備手段**に位置付けを変更した（下記 R1-9 参照）。

---

## 2. 用語定義

| 用語 | 定義 |
| --- | --- |
| Rules | AWS IoT Core のルールエンジン。MQTT メッセージを SQL で選択し、アクションへ渡す |
| SQL ステートメント | `SELECT ... FROM 'topic' WHERE ...` 形式のルール定義 |
| アクション | ルールがマッチしたときに実行される連携先（CloudWatch / Lambda / SNS 等） |
| エラーアクション | アクション失敗時に実行される代替アクション |
| 名前空間（Namespace） | CloudWatch Metrics のメトリクスをグループ化する単位 |
| 負荷生成スクリプト | CPU / メモリ使用率を意図的に変動させるスクリプト |
| セッション ID | 参加者ごとのリソース識別子（例：`raspi-001`） |

---

## 3. 機能要件

要件は EARS 形式（`WHEN <条件> THEN <主体> SHALL <振る舞い>`）で記述する。「システム」はハンズオン成果物（スクリプト・CloudFormation テンプレート・手順書）を指す。

---

### Requirement 1：デバイスからのメトリクス送信

**User Story**: ハンズオン参加者として、Raspberry Pi の CPU 使用率とメモリ使用率を AWS IoT Core に送信したい。クラウド側で処理する元データを用意するためである。

#### Acceptance Criteria

1. WHEN 参加者がデバイススクリプトを起動する THEN システム SHALL X.509 証明書による TLS 相互認証で AWS IoT Core（ポート 8883）へ接続する。
2. WHEN 接続が確立している THEN システム SHALL 一定間隔（既定 10 秒、環境変数で変更可能）で CPU 使用率とメモリ使用率を取得し、MQTT で Publish する。
3. WHEN メッセージを Publish する THEN システム SHALL トピック `jawsug/session-03/{deviceId}/metrics` を使用する。
4. WHEN メッセージを構築する THEN システム SHALL 以下のフィールドを含む JSON ペイロードを送信する。
   - `deviceId`（string）
   - `cpu`（number、0〜100、単位 %、小数第 1 位まで）
   - `memory`（number、0〜100、単位 %、小数第 1 位まで）
   - `timestamp`（number、Unix epoch 秒）
5. WHEN メッセージを Publish する THEN システム SHALL 送信した `cpu` / `memory` / `timestamp` を標準出力に表示する（デバイス側の実測値と CloudWatch 上の値を突き合わせられるようにするため）。
6. WHEN 使用率の取得に失敗する THEN システム SHALL 標準出力にエラーを記録し、次の周期で再試行する（プロセスを異常終了させない）。
7. WHEN 接続が切断される THEN システム SHALL 自動再接続を試行する。
8. WHEN 参加者が `Ctrl+C` を入力する THEN システム SHALL MQTT を正常に切断し、終了メッセージを出力して終了する。
9. ~~WHEN 参加者が実機を持たない THEN システム SHALL 同一のトピック・同一ペイロード形式で送信するシミュレーターを提供する。~~
   → **削除（2026-08-13）**。全員が会場で実機を操作する前提に確定したため、参加者向けの要件ではなくなった。
   実装済みの `simulator.py` は**運営用の予備手段**として残す（当日の実機故障時のバックアップ、および
   実機を用意できない開発・検証環境での動作確認用）。**手順書には記載しない。**

---

### Requirement 2：負荷生成スクリプトによる使用率の変動と、デバイス側での状態確認

**User Story**: ハンズオン参加者として、CPU 使用率とメモリ使用率を任意に変動させ、**その値をデバイス側でも確認**したい。CloudWatch のグラフが自分の操作に反応していること、およびデバイスの実測値とクラウド側の値が同期していることを確認するためである。

#### Acceptance Criteria

**負荷生成**

1. WHEN 参加者が負荷生成スクリプトを CPU モードで実行する THEN システム SHALL 指定された目標使用率（%）と継続時間（秒）に従って CPU 負荷を生成する。
2. WHEN 参加者が負荷生成スクリプトをメモリモードで実行する THEN システム SHALL 指定された容量（MB）を確保し、指定された継続時間だけ保持する。
3. WHEN 負荷生成が実行中である THEN システム SHALL 経過時間と現在の使用率を標準出力に表示する。
4. WHEN 指定された継続時間が経過する THEN システム SHALL 負荷を解放し、リソースを元の状態に戻して終了する。
5. WHEN 参加者が実行中に `Ctrl+C` を入力する THEN システム SHALL 確保したリソース（プロセス・メモリ）を確実に解放して終了する。
6. WHEN 負荷パラメータが Raspberry Pi の物理上限を超える THEN システム SHALL 実行前に警告を表示し、安全な上限値に丸めるか実行を中止する。
7. WHEN CloudWatch グラフで確認する THEN 負荷生成の開始・終了 SHALL グラフ上で識別可能な変化として現れる（推奨：目標値と平常値の差が 30 ポイント以上）。
8. WHEN 負荷生成スクリプトを実行する THEN システム SHALL 実行開始時刻・終了時刻（JST）を標準出力に表示する（CloudWatch グラフの時間軸と突き合わせるため）。

**デバイス側での状態確認**

9. WHEN 参加者が負荷の効果をデバイス側で確認したい THEN システム SHALL OS 標準コマンドによる CPU 使用率・メモリ使用率の確認手順を手順書に整理して提供する（下記「確認コマンド一覧」を参照）。
10. WHEN 確認コマンドを提供する THEN システム SHALL 追加インストールを必要としないコマンド（`top` / `free` / `vmstat` / `uptime` / `/proc` 参照）を第一選択とし、追加インストールが必要なもの（`htop` / `mpstat` 等）は任意扱いとして明確に区別する。
11. WHEN 参加者が負荷生成中にデバイス側で確認する THEN 表示される使用率 SHALL 負荷生成スクリプトが目標とした値とおおむね一致する（許容差 ±10 ポイント）。
12. WHEN デバイス側の実測値と CloudWatch Metrics 上の値を比較する THEN 同一時刻（±1 データポイント）の両者の値 SHALL 許容差 ±5 ポイント以内で一致する。
13. WHEN 手順書に確認手順を記載する THEN システム SHALL 「負荷をかける → デバイス側で確認 → CloudWatch で確認 → 値を突き合わせる」という一連の流れとして記述する。
14. WHEN SSH セッションが 1 本しかない参加者がいる THEN システム SHALL 送信スクリプト・負荷生成・確認コマンドを並行実行するための手段（複数 SSH セッション、`tmux`、バックグラウンド実行のいずれか）を手順書に記載する。

#### 確認コマンド一覧（手順書に整理する対象）

| 用途 | コマンド例 | 追加インストール |
| --- | --- | --- |
| CPU / メモリの全体をリアルタイム確認 | `top`（`1` キーでコア別表示、`q` で終了） | 不要 |
| メモリ使用量を人間可読で確認 | `free -h` | 不要 |
| CPU / メモリの推移を一定間隔で確認 | `vmstat 1` | 不要 |
| ロードアベレージの確認 | `uptime` / `cat /proc/loadavg` | 不要 |
| CPU 使用率上位のプロセス確認 | `ps aux --sort=-%cpu \| head` | 不要 |
| メモリ使用率上位のプロセス確認 | `ps aux --sort=-%mem \| head` | 不要 |
| メモリの詳細内訳 | `cat /proc/meminfo` | 不要 |
| 対話的な可視化 | `htop` | 必要（`sudo apt install htop`、任意） |
| CPU 使用率の統計取得 | `mpstat 1` | 必要（`sudo apt install sysstat`、任意） |
| デバイススクリプトが送信中の値 | `metrics_publisher.py` の標準出力（R1-5） | 不要 |

> 手順書では **`top`（CPU）** と **`free -h`（メモリ）** を主軸として案内し、その他は補足として扱う。

---

### Requirement 3：Rules から CloudWatch Metrics への連携（基本・必須）

**User Story**: ハンズオン参加者として、IoT Core に届いたデータを Rules 経由で CloudWatch Metrics に送りたい。コードを書かずにデータを可視化する流れを理解するためである。

#### Acceptance Criteria

1. WHEN CloudFormation スタックが作成される THEN システム SHALL トピックフィルター `jawsug/session-03/+/metrics` を対象とする IoT ルールを作成する。
2. WHEN ルールの SQL を定義する THEN システム SHALL SQL バージョン `2016-03-23` を使用する。
3. WHEN メトリクス送信対象のメッセージが届く THEN システム SHALL **単一のルール内に 2 つの `cloudwatchMetric` アクション**を定義し、CPU 使用率とメモリ使用率を送信する（1 ルールにアクションは 10 個まで定義可能であり、同一メッセージ由来の 2 メトリクスは 1 ルールにまとめるのが自然なため）。
4. WHEN メトリクスを送信する THEN システム SHALL 以下の属性を設定する。
   - 名前空間：`JAWSUG/IoTHandson`
   - メトリクス名：CPU 使用率・メモリ使用率をそれぞれ識別できる名称
   - 単位：`Percent`
   - 値：ペイロードの `cpu` / `memory`（文字列としてキャストして渡す）
   - タイムスタンプ：ペイロードの `timestamp`
5. WHEN 複数の参加者が同一 AWS アカウント／同一名前空間を使用する可能性がある THEN システム SHALL デバイスごとにメトリクスを識別できる設計とする（`cloudwatchMetric` アクションは Dimension を指定できないため、名前空間またはメトリクス名で分離する）。
6. WHEN 参加者がマネジメントコンソールで CloudWatch → メトリクスを開く THEN 送信から 3 分以内に該当メトリクスが表示 SHALL される。
7. WHEN アクションが失敗する THEN システム SHALL エラーアクションとして CloudWatch Logs にエラー内容を記録する。
8. WHEN ルールが IAM 権限を必要とする THEN システム SHALL 必要最小限の権限（`cloudwatch:PutMetricData` 等）のみを付与した IAM ロールを作成する。

---

### Requirement 4：Rules から Lambda への連携（アドバンス A）

**User Story**: ハンズオン参加者として、Rules から Lambda を起動して受信データをログに残したい。Rules が任意の AWS サービスへ橋渡しできることを実感するためである。

#### Acceptance Criteria

1. WHEN アドバンス用 CloudFormation スタックが作成される THEN システム SHALL 同一トピックフィルターを対象とする Lambda アクション付き IoT ルールを追加作成する。
2. WHEN Lambda 関数が呼び出される THEN システム SHALL 受信ペイロードから `deviceId` / `cpu` / `memory` / `timestamp` を抽出し、構造化ログ（JSON 形式）として出力する。
3. WHEN Lambda がログを出力する THEN システム SHALL CloudWatch Logs ロググループ（保持期間を設定済み）に記録する。
4. WHEN ペイロードに必須フィールドが欠落している THEN システム SHALL 例外で異常終了せず、警告レベルでログを記録する。
5. WHEN ロググループの保持期間を設定する THEN システム SHALL ハンズオン後のコスト発生を抑えるため短期間（推奨 1〜7 日）とする。
6. WHEN 参加者が CloudWatch Logs Insights で検索する THEN 受信レコードが取得可能な形式で記録 SHALL されている。
7. WHEN Lambda に IAM 権限を付与する THEN システム SHALL ログ出力に必要な権限のみを付与する。
8. WHEN 基本ルール（Requirement 3）と本ルールが同時に有効である THEN システム SHALL 双方が独立して動作する（一方の失敗が他方に影響しない）。

---

### Requirement 5：CloudWatch Alarm から Email 通知（アドバンス B）

**User Story**: ハンズオン参加者として、使用率がしきい値を超えたときに自分のメールへ通知を受け取りたい。IoT データを運用アラートにつなげる流れを理解するためである。

#### Acceptance Criteria

1. WHEN アドバンス用 CloudFormation スタックが作成される THEN システム SHALL SNS トピックと、パラメータで指定されたメールアドレスへの Email サブスクリプションを作成する。
2. WHEN サブスクリプションが作成される THEN システム SHALL 参加者に確認メール（Subscription Confirmation）の承認が必要であることを手順書で明示する。
3. WHEN CloudWatch Alarm を作成する THEN システム SHALL CPU 使用率メトリクスを対象とし、しきい値・評価期間をパラメータ化する（既定：しきい値 80%、期間 60 秒、評価回数 1）。
4. WHEN メトリクス値がしきい値を超える THEN Alarm SHALL `ALARM` 状態に遷移し、SNS トピックへ通知する。
5. WHEN SNS トピックが通知を受け取る THEN 承認済みの Email アドレスへ 5 分以内にメールが配信 SHALL される。
6. WHEN データが送信されていない期間がある THEN システム SHALL 欠損データの扱い（`TreatMissingData`）を明示的に指定する。
7. WHEN 状態が `OK` に復帰する THEN システム SHALL 復旧通知を送信する設定を提供する（有効／無効を選択可能とする）。
8. WHEN 参加者が負荷生成スクリプトを実行する THEN 手順書に記載のパラメータで Alarm が発火 SHALL する（再現性を担保する）。

---

### Requirement 6：CloudFormation によるインフラ構築

**User Story**: ハンズオン運営者として、AWS リソースを CloudFormation で構築したい。参加者全員が短時間で同じ環境を再現できるようにするためである。

#### Acceptance Criteria

1. WHEN インフラを定義する THEN システム SHALL すべての AWS リソースを CloudFormation テンプレート（YAML）で定義する（コンソール手作業を必須手順にしない）。
2. WHEN テンプレートを配置する THEN システム SHALL `cfn/session-03/` 配下に配置する。
3. WHEN 参加者がスタックを作成する THEN システム SHALL 基本編とアドバンス編を分離したテンプレート構成とし、基本編のみで動作を完結できるようにする。
4. WHEN テンプレートがパラメータを受け取る THEN システム SHALL 少なくとも `DeviceId`、通知先メールアドレス、Alarm しきい値をパラメータ化する。
5. WHEN スタックが作成される THEN システム SHALL `Outputs` にトピック名・ルール名・メトリクス名前空間・SNS トピック ARN 等の後続手順で必要な値を出力する。
6. WHEN リソース名を決定する THEN システム SHALL `DeviceId` を含めることで、同一アカウント内での衝突を回避する。
7. WHEN スタック作成を実行する THEN 5 分以内に `CREATE_COMPLETE` へ到達 SHALL する。
8. WHEN 参加者が第2回と同様に証明書を扱う THEN システム SHALL 秘密鍵を CloudFormation で取得できない制約を手順書で明示し、手動発行手順を提供する。
9. WHEN テンプレートを変更する THEN システム SHALL `cfn-lint` による静的検証に合格させる。

---

### Requirement 7：テスト駆動開発（TDD）

**User Story**: ハンズオン運営者として、TDD でスクリプトと IaC を実装したい。本番当日の不具合リスクを下げ、検証証跡を残すためである。

#### Acceptance Criteria

1. WHEN 新しい機能を実装する THEN 開発者 SHALL 先に失敗するテストを書き（Red）、実装で合格させ（Green）、リファクタリングする（Refactor）順序で進める。
2. WHEN テストを配置する THEN システム SHALL `scripts/session-03/tests/` 配下に配置する。
3. WHEN Python コードをテストする THEN システム SHALL `pytest` を使用する。
4. WHEN AWS API に依存するコードをテストする THEN システム SHALL モック（`moto` または `unittest.mock`）を使用し、実 AWS アカウントへのアクセスなしでテストを完結させる。
5. WHEN Lambda 関数を実装する THEN システム SHALL 正常系・必須フィールド欠落・不正な型の各ケースに対するユニットテストを備える。
6. WHEN 負荷生成スクリプトを実装する THEN システム SHALL パラメータ検証・上限値の丸め・シグナル受信時のクリーンアップに対するテストを備える。
7. WHEN CloudFormation テンプレートを検証する THEN システム SHALL `cfn-lint` と `aws cloudformation validate-template` による検証をテスト工程に含める。
8. WHEN テストを実行する THEN システム SHALL 単一コマンド（例：`pytest`）で全ユニットテストを実行できる。
9. WHEN すべてのマイルストーンを完了する THEN ユニットテストは全件成功 SHALL する。
10. WHEN 実 AWS 環境での結合検証を行う THEN システム SHALL その結果を `verification-log.md` に記録する（Requirement 9）。

---

### Requirement 8：ドキュメントとリポジトリ整備

**User Story**: ハンズオン参加者として、手順書だけを見て最後まで進めたい。当日の詰まりを最小化するためである。

#### Acceptance Criteria

1. WHEN 手順書を作成する THEN システム SHALL `docs/session-03/handson.md` に配置し、`docs/session-02/handson.md` の構成（ゴール／進め方／所要時間／学習内容／AWS 側設定／実装／動作確認／ハマりポイント／発展課題／後片付け）に準拠する。
2. WHEN 構成図を作成する THEN システム SHALL `docs/session-03/architecture.drawio.svg` として配置し、基本・アドバンス A・アドバンス B の 3 経路を表現する。
3. WHEN 所要時間を記載する THEN システム SHALL パート別の内訳と合計 90 分を明示する。
4. WHEN ハマりポイントを記載する THEN システム SHALL 症状・原因・対処の 3 列表形式で記述する。
5. WHEN 手順書に画面操作を記載する THEN システム SHALL 東京リージョン（`ap-northeast-1`）を前提として統一する。
6. WHEN 手順書に動作確認を記載する THEN システム SHALL Requirement 2 の「確認コマンド一覧」を独立した節として掲載し、デバイス側実測値と CloudWatch Metrics の値を突き合わせる手順を含める。
7. WHEN リポジトリのルート `README.md` を更新する THEN システム SHALL 第3回の行を `T.B.D.` から実際のリンクへ更新し、ディレクトリ構成図に session-03 の各ファイルを追記する。
8. WHEN ハンズオンが終了する THEN システム SHALL `scripts/session-03/teardown.sh` により、作成した全リソース（スタック・証明書・Thing・ローカル証明書）を削除できる。
9. WHEN 後片付けスクリプトを実行する THEN システム SHALL 削除対象を事前に表示し、削除後に残存リソースの有無を報告する。
10. WHEN 手順書に AWS リソースの作成・設定・確認手順を記載する THEN システム SHALL **マネジメントコンソール（UI）の操作を主たる手順**として記述する（2026-08-13 決定）。
11. WHEN 手順書に AWS CLI のコマンドを併記する THEN システム SHALL それが**必須手順ではない補足**であることを明示する（自動化したい人向け、または値の確認用）。
12. WHEN UI 操作を記載する THEN システム SHALL 画面遷移（左メニュー名 → タブ名 → ボタン名）を、参加者が迷わない粒度で順に記述する。

---

### Requirement 9：マイルストーンと検証証跡

**User Story**: ハンズオン運営者として、各マイルストーンの検証結果を証跡として残したい。当日までに何が確認済みかを明確にするためである。

#### Acceptance Criteria

1. WHEN 実装を計画する THEN システム SHALL `tasks.md` のタスクをマイルストーン（M0〜M5）に紐付ける。
2. WHEN 検証記録を作成する THEN システム SHALL `scripts/session-03/specs/verification-log.md` に配置する。
3. WHEN 検証を記録する THEN システム SHALL 各エントリに以下を含める。
   - 実施日時（JST）
   - マイルストーン ID / タスク ID
   - 対応する要件 ID（本書の Requirement 番号）
   - 実行コマンドまたは操作手順
   - 期待結果と実際の結果
   - 判定（Pass / Fail / Blocked）
   - 証跡（ログ出力・スクリーンショットのファイルパス）
4. WHEN Requirement 2 の値の突き合わせを検証する THEN システム SHALL デバイス側実測値・スクリプト送信値・CloudWatch Metrics 上の値を同一時刻の 3 点セットで記録し、差分が許容範囲内であることを判定する。
5. WHEN 検証が Fail になる THEN システム SHALL 原因と対処、再検証の結果を追記する。
6. WHEN マイルストーンが完了する THEN システム SHALL そのマイルストーンの受け入れ基準がすべて Pass であることを記録する。
7. WHEN 証跡を記録する THEN システム SHALL AWS アカウント ID・証明書・秘密鍵・参加者メールアドレスをマスクする。
8. WHEN リハーサルを実施する THEN システム SHALL 手順書どおりに通し実行した結果と所要時間を記録する。

---

## 4. 非機能要件

| ID | 分類 | 要件 |
| --- | --- | --- |
| NFR-1 | 開発手法 | TDD（Red → Green → Refactor）で実装する（Requirement 7） |
| NFR-2 | IaC | AWS リソースは CloudFormation で構築する（Requirement 6） |
| NFR-3 | リージョン | `ap-northeast-1`（東京）を使用する |
| NFR-4 | 所要時間 | 基本編は 60 分以内、アドバンス編を含めて 90 分以内で完了できる |
| NFR-5 | コスト | 参加者 1 名あたりのハンズオン当日コストが少額（数十円規模）に収まる。ログ保持期間を短期に設定し、後片付けで全リソースを削除できる |
| NFR-6 | セキュリティ | IAM は最小権限。秘密鍵・証明書はリポジトリにコミットしない（`.gitignore` で除外） |
| NFR-7 | セキュリティ | 参加者のメールアドレスはリポジトリ・証跡に記録しない（CloudFormation パラメータとして当日入力） |
| NFR-8 | 再現性 | 同一手順で複数参加者が並行実行しても、リソース名・メトリクスが衝突しない |
| ~~NFR-9~~ | ~~可搬性~~ | ~~実機がない参加者もシミュレーターで基本編を完了できる~~ → **削除（2026-08-13）**：全員が会場で実機を操作する前提に確定 |
| NFR-10 | 保守性 | 言語は Python 3（デバイス側・Lambda）で統一し、依存を最小限にする |
| NFR-11 | ドキュメント | 参加者向けドキュメントは日本語で記述する |
| NFR-12 | 品質 | `cfn-lint` および全ユニットテストの合格を実装完了条件とする |

---

## 5. マイルストーン

| ID | マイルストーン | 主な成果物 | 完了条件（Exit Criteria） |
| --- | --- | --- | --- |
| M0 | Spec 確定 | `requirements.md` / `design.md` / `tasks.md` / `verification-log.md`（雛形） | 3 ドキュメントのレビュー完了、要件 ID とタスクのトレーサビリティが取れている |
| M1 | デバイス側の実装 | `metrics_publisher.py`、`load_gen.py`、`show_metrics.sh`、ユニットテスト（＋運営用予備の `simulator.py`） | Requirement 1・2 のテストが全件 Pass、ローカルでペイロード生成を検証済み |
| M2 | 基本経路の構築 | `cfn/session-03/iot-rules-cloudwatch.yaml` | Requirement 3・6 を満たし、実環境で CloudWatch グラフに使用率の変動が描画されること、および R2-12 の値の突き合わせ（デバイス実測値 ≒ CloudWatch 値）を確認 |
| M3 | アドバンス A（Lambda） | Lambda ハンドラ、`cfn/session-03/advanced-lambda.yaml`、ユニットテスト | Requirement 4 のテストが全件 Pass、CloudWatch Logs にレコードが記録される |
| M4 | アドバンス B（Alarm → Email） | `cfn/session-03/advanced-alarm.yaml` | Requirement 5 を満たし、負荷生成により実際にメールが届くことを確認 |
| M5 | ドキュメント・リハーサル | `docs/session-03/handson.md`、`architecture.drawio.svg`、ルート `README.md`、`teardown.sh` | Requirement 8・9 を満たし、手順書どおりの通し実行が 90 分以内に完了、`verification-log.md` に全証跡を記録 |

---

## 6. スコープ外

- Rules から S3 / DynamoDB / Kinesis / Timestream / IoT Analytics への連携（時間の都合上、手順書内で紹介のみ）
- 複数デバイス間の集計処理、IoT Events / SiteWise の利用
- 本番運用相当の監視ダッシュボード、コスト最適化設計
- Raspberry Pi の OS セットアップ・Wi-Fi 設定（運営が事前準備済み）
- GPIO を用いた外付けセンサーの利用

---

## 7. 未確定事項（Open Questions）

| # | 内容 | 確認先 / 期限 |
| --- | --- | --- |
| Q1 | メトリクス名前空間・メトリクス名の命名規則（デバイス分離を名前空間側で行うか、メトリクス名側で行うか） | design.md で決定 |
| Q2 | Alarm のしきい値・評価期間の既定値（当日確実に発火し、かつ誤発火しない値） | M4 のリハーサルで確定 |
| Q3 | メール通知の確認（Subscription Confirmation）を事前案内にするか、当日実施にするか | 運営判断 |
| Q4 | 基本編とアドバンス編のテンプレートを 1 スタックにまとめるか、分離のままにするか | design.md で決定 |
| ~~Q6~~ | ~~CPU / メモリを 1 ルールにまとめるか 2 ルールに分けるか~~ | **決定済み：1 ルール内に 2 つの `cloudwatchMetric` アクション（R3-3）** |
| Q5 | 参加者の AWS アカウントが共有か個別か（共有の場合は命名衝突対策を強化） | 運営判断 |

---

## 8. 要件トレーサビリティ（サマリ）

| Requirement | 対応マイルストーン | 主な検証方法 |
| --- | --- | --- |
| R1 デバイス送信 | M1 | ユニットテスト、MQTT テストクライアントでの受信確認 |
| R2 負荷生成／デバイス側確認 | M1・M2 | ユニットテスト、実機での `top` / `free -h` による使用率観測、CloudWatch 値との突き合わせ |
| R3 Rules → CloudWatch Metrics | M2 | `cfn-lint`、実環境でのメトリクスグラフ確認 |
| R4 Rules → Lambda → Logs | M3 | ユニットテスト、CloudWatch Logs Insights での検索 |
| R5 Alarm → SNS → Email | M4 | 実環境でのアラーム発火・メール受信確認 |
| R6 CloudFormation | M2〜M4 | `cfn-lint`、スタック作成・削除の実行 |
| R7 TDD | M1〜M4 | `pytest` の実行結果 |
| R8 ドキュメント | M5 | 通し実行によるレビュー |
| R9 証跡 | M0〜M5 | `verification-log.md` の記載完全性チェック |
