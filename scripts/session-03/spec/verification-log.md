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
| M0 | Spec 確定・作業環境準備 | 完了 | 2026-08-08 | 0.1〜0.5 完了。0.6 は Q7=新規作成／Q8=Python 3.13 で暫定確定（M3 デプロイ時に再確認） |
| M1 | デバイス側の実装 | 進行中 | — | 1.1〜1.14 実装完了・ユニットテスト 49 件 Pass。**1.15（実機確認）が未実施のため未完了** |
| M2 | 基本経路の構築 | 進行中 | — | 2.1〜2.5（テンプレート実装・静的検証）完了。**2.6〜2.10（実 AWS 環境）が未実施** |
| M3 | アドバンス A（Lambda） | 進行中 | — | 3.1〜3.4（実装・テスト）完了。**3.5〜3.7（実 AWS 環境）が未実施** |
| M4 | アドバンス B（Alarm → Email） | 進行中 | — | 4.1〜4.2（テンプレート実装・静的検証）完了。**4.3〜4.6（実 AWS 環境）が未実施** |
| M5 | ドキュメント・リハーサル | 未着手 | — | `handson.md` / 構成図 / README 更新が未着手。`teardown.sh` のみ先行実装済み（未実行） |

ステータスは `未着手` / `進行中` / `完了` / `保留`。

> **現時点の到達点**: コード・IaC・ユニットテストは揃い、静的検証（pytest 81 件 / cfn-lint 3 本）は全件 Pass。
> ただし **実 AWS 環境および実機 Raspberry Pi での検証は一切未実施**であり、当日運用可能な状態ではない。
> 残る主要作業は「実環境デプロイ検証（2.6〜2.10 / 3.5〜3.7 / 4.3〜4.6）」と「M5 ドキュメント」。

### 2.2 要件別の検証カバレッジ

| 要件 | 検証エントリ | 状態 | 補足 |
| --- | --- | --- | --- |
| R1 デバイス送信 | M1-UT, M1-S, 1.15 | 進行中 | ユニットテストとローカル疎通は Pass。**実機での MQTT 送信（R1-1〜R1-3, R1-7）は未検証** |
| R2 負荷生成／デバイス側確認 | M1-UT, M1-S, 1.15, 2.8, 2.9 | 進行中 | パラメータ検証・上限クランプは Pass。**R2-11 に懸念あり（M1-S 参照）**。R2-7/12 は未検証 |
| R3 Rules → CloudWatch Metrics | M2-0, 2.6, 2.7 | 進行中 | テンプレート構造（R3-2/3/7）は Pass。**R3-6（到達確認）は未検証** |
| R4 Rules → Lambda → Logs | M3-UT, 3.5, 3.6, 3.7 | 進行中 | ハンドラのユニットテスト（R4-2/4/6）は Pass。**実環境連携は未検証** |
| R5 Alarm → SNS → Email | M4-0, 4.3, 4.4, 4.5, 4.6 | 進行中 | テンプレート構造（R5-6/7）は Pass。**メール到達（R5-5）は未検証** |
| R6 CloudFormation | M2-0, M4-0, 2.6, 3.4, 4.2 | 進行中 | R6-9（cfn-lint）は Pass。**R6-7（作成時間）・R6-8 は未検証** |
| R7 TDD | M1-UT, M3-UT, **M2-F1**, 5.11 | **一部 Fail** | R7-2〜R7-9 は Pass。**R7-1（Red → Green の順序）は M1・M3 で未遵守**（M1-UT 備考および 8 章参照）。**M2-F1（F-1 修正）以降は遵守**し、Red ログを証跡として保存 |
| R8 ドキュメント | 5.10, 5.11 | 未検証 | M5 未着手 |
| R9 証跡 | 本文書全体, 5.11 | 進行中 | 本更新で M0〜M4 の静的検証分を記録 |
| NFR-4 所要時間 | 5.10 | 未検証 | |
| NFR-6/7 セキュリティ | M0-1, 5.11 | 進行中 | `certs/` / `.venv/` の ignore は確認済み（M0-1） |
| **NFR-8 再現性** | **M2-F1** | **Pass（静的検証範囲）** | 3 テンプレートの全リソース名が `${DeviceNumber}` を含むことをテストで担保（F-1 で解消）。実環境での並行作成は未検証 |
| NFR-12 品質 | M0-1, M1-UT, M3-UT, M2-0, M2-F1 | Pass（静的検証範囲） | pytest **81 件** / cfn-lint 3 本すべて合格。shellcheck 指摘 0 件 |

状態は `未検証` / `進行中` / `Pass` / `Fail`。

### 2.3 検証環境

初回検証時に記入し、以降変更があれば追記する。

| 項目 | 値 |
| --- | --- |
| 検証者 | リポジトリオーナー（開発機での静的検証のみ） |
| リージョン | `ap-northeast-1`（未接続） |
| Raspberry Pi モデル | _（未実施）_ |
| Raspberry Pi OS | _（未実施）_ |
| CPU コア数 / 総メモリ | _（未実施）_ |
| Python（デバイス側） | _（未実施）_ |
| `paho-mqtt` / `psutil` | _（未実施：デバイス側）_ |
| **開発環境（以下は 2026-08-08 実測）** | |
| OS（開発機） | macOS（darwin）/ CPU 10 コア / 総メモリ 65536 MB |
| Python（開発環境） | 3.11.15 |
| `pytest` | 9.1.1 |
| `cfn-lint` | 1.54.0 |
| `psutil` | 7.2.2 |
| `PyYAML` | 6.0.3 |
| AWS CLI | _（未使用：実環境検証が未実施のため）_ |
| Lambda ランタイム（Q8 の決定） | `python3.13`（テンプレートに記載。**実デプロイでのサポート確認は未実施**） |
| 時刻同期状態（`timedatectl`） | _（未実施：Linux 実機が必要）_ |

> 開発機は macOS のため、`show_metrics.sh`（`/proc` 依存）と `timedatectl` は開発機では実行できない。
> これらは実機 Raspberry Pi での検証（タスク 1.15）に持ち越し。

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

### M0 → **完了**（2026-08-08）

- [x] requirements / design / tasks / verification-log の 4 文書が揃っている
- [x] 要件 ID とタスク ID の対応が取れている（R9-1）
- [x] `pytest` が実行できる（※「0 件で正常終了」は経由せず。M0-1 備考参照）
- [x] `cfn-lint` が実行できる（1.54.0）
- [x] `.gitignore` に `certs/` と `.venv/` を追加済み（既存の記述でカバー済みを確認）
- [x] Q7（構成図）・Q8（Lambda ランタイム）を決定済み（Q8 は暫定・M3 で再確認）

### M1 → **進行中**（実機検証が未実施）

- [x] R1・R2 のユニットテストが全件成功（R7-9）… 49 件 Pass
- [ ] ~~Red の失敗ログを記録済み（代表タスク分）~~ → **未遵守**。M1-UT「TDD 順序の逸脱」に理由を記載
- [ ] 実機で 4 者（`top` / `free -m` / `show_metrics.sh` / publisher 出力）が ±10 ポイント以内で一致（R2-11）
      → **未実施**。加えて M1-S で目標値と実測値に +15.4 ポイントの乖離を観測しており、要確認事項あり
- [ ] `timedatectl` で時刻同期を確認済み（K-1）→ **未実施**（Linux 実機が必要）
- [x] メモリ使用率の定義が D-7 に一致していることをコードとテストで確認

### M2 → **進行中**（実 AWS 環境が未実施）

- [x] テンプレート検証テストが全件成功（`cfn-lint` / アクション数 2 / SQL バージョン / ルール名文字種 / ErrorAction / Outputs）
- [ ] スタック作成が 5 分以内に `CREATE_COMPLETE`（R6-7）→ **未実施**
- [ ] 送信から 3 分以内にメトリクスが表示（R3-6）→ **未実施**
- [ ] メトリクス名が `CpuUtilization-raspi-{n}` になっている（D-1・D-2）→ **未実施**（置換テンプレートの評価は実環境のみで確認可能）
- [ ] ErrorAction ログにエラーがない（D-3 の明示キャストが機能）→ **未実施**
- [ ] 期間 1 分のグラフで負荷の台形が視認でき、平常値との差が 30 ポイント以上（R2-7）→ **未実施**
- [ ] 3 点セットが ±5 ポイント以内で一致（R2-12）→ **未実施**
- [x] スタック削除が成功（2026-08-13。`teardown.sh` の不具合 F-3d / F-3e / F-3f を発見・修正） → **未実施**

### M3 → **進行中**（実 AWS 環境が未実施）

- [x] R4 のユニットテストが全件成功（11 件）
- [x] インライン同期テストが成功（D-10）
- [ ] Logs Insights でレコードを検索できる（R4-6）→ **未実施**
- [ ] ロググループの保持期間が 3 日（R4-5）→ テンプレート上は確認済み。**実環境の反映は未確認**
- [ ] 2 本のルールが独立に動作（片方の失敗が他方に影響しない）（R4-8）→ **未実施**
- [ ] 必須フィールド欠落時に Lambda が WARN で継続（R4-4）→ ユニットテストは Pass。**実環境は未実施**
- [ ] Lambda ランタイム `python3.13` が利用可能であることを確認（Q8）→ **未実施**

### M4 → **進行中**（実 AWS 環境が未実施）

- [x] テンプレート検証テストが全件成功（`TreatMissingData` / `Period` ≥ 60 / メール `AllowedPattern` / Outputs）
- [ ] 確認メールを受信し承認、SNS で `Confirmed` を確認（R5-2）→ **未実施**
- [ ] CFN が承認を待たずに `CREATE_COMPLETE` になることを確認（K-6 の裏付け）→ **未実施**
- [ ] `OK` → `ALARM` 遷移を確認（R5-4）→ **未実施**
- [ ] 5 分以内にメール受信（R5-5）→ **未実施**
- [ ] 復旧通知を受信（R5-7）→ **未実施**
- [ ] 送信停止中に誤発火しない（`TreatMissingData: notBreaching`）（R5-6）→ **未実施**
- [ ] しきい値・期間の既定値を実測に基づいて確定（Q2）→ **未実施**（暫定値のまま）
- [ ] スタック再作成時に再承認が必要であることを確認（K-6）→ **未実施**

### M5 → **ほぼ未着手**（骨格のみ）

- [ ] 手順書・構成図・README が揃っている → 🚧 **`handson.md` は骨格のみ**（5.2・5.3 完了、実測依存の 6 セクションが TODO）。`architecture.drawio.svg` と README は**未作成**
- [ ] `handson.md` の `<!-- TODO -->` と「🚧 執筆ステータス」ブロックがすべて解消されている → **未達成**（公開前チェック項目）
- [ ] 通し実行が 90 分以内で完了（NFR-4）→ **未実施**
- [ ] 基本編が 60 分以内で完了 → **未実施**
- [ ] ハマりポイント表に M1〜M4 で実際に遭遇した事象が反映されている（R8-4）→ **未着手**。反映候補は下記
- [x] `pytest` 全件成功、`cfn-lint` 全テンプレート合格（NFR-12）… 78 件 Pass / 3 本合格
- [ ] `teardown.sh` で全リソースが削除できる（R8-8・R8-9）→ **実装済みだが未実行**
- [x] `evidence/` にアカウント ID・証明書 ID・メールアドレスが残っていない（R9-7）… 現時点の証跡に AWS 情報は含まれない
- [x] `certs/` がコミットされていない（NFR-6）… `git check-ignore` で確認済み（M0-1）

**ハマりポイント表（タスク 5.7）への反映候補**（現時点で実際に遭遇した事象）

| 症状 | 原因 | 対処 | 出典 |
| --- | --- | --- | --- |
| `cfn-lint` が `W1020 'Fn::Sub' isn't needed` で失敗する | 変数を含まない文字列に `!Sub` を使っている | `!Sub` を外す | M2-0 |
| 負荷生成の `--target` 値より実測 CPU 使用率が高く出る | duty cycle 計算がベースライン負荷を考慮していない（目標値＝負荷生成分のみ） | 実機実測後に方針決定（M1-S 参照） | M1-S |
| （テンプレート検証を自作する場合）`yaml.safe_load` が `!Sub` で例外 | CFN の intrinsic function タグは標準 YAML ではない | カスタム Loader を使う | M3-UT |

> 上記は**開発時に遭遇した事象**であり、参加者が当日遭遇する事象（時刻ずれ K-1、`free` との
> 値の差 K-2、メール未承認 K-6 等）は実環境検証（M2〜M4）を経てから追記する。

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

**実際の結果**（2026-08-08 23:54 JST 実施）

| 確認項目 | 結果 |
| --- | --- |
| Python | 3.11.15 |
| `pytest --version` | 9.1.1 ✅ |
| `cfn-lint --version` | 1.54.0 ✅ |
| `psutil` / `PyYAML` | 7.2.2 / 6.0.3 ✅ |
| `certs/` の ignore | `.gitignore:2:certs/` にマッチ ✅ |
| `.venv/` の ignore | `.gitignore:10:.venv/` にマッチ ✅ |
| ディレクトリ作成 | `tests/` `lambda/` `evidence/{m0..m5}/` `cfn/session-03/` を作成 ✅ |
| `requirements-dev.txt` | `pytest` / `psutil` / `cfn-lint` / `pyyaml` を記載 ✅ |

**「collected 0 items」の扱い**: ルート `.gitignore` に既に `certs/` `.venv/` が存在していたため追加不要だった。
`pytest` はテスト実装と同一セッションで進めたため「0 件で正常終了」の状態は経由していない。
代わりに `pytest --collect-only` が正常動作すること（78 件収集）を実行環境の確認とした。

**判定**: **Pass**（環境構築の目的は達成。0 件終了の確認手順のみ実際の進め方と差異あり）

**証跡**: `evidence/m0/0.5-env-setup.txt`

**備考**

- タスク 0.6 の Q7 は「**新規作成**」、Q8 は「**`python3.13`**」で暫定確定。
  Q8 は実デプロイ（タスク 3.5）でサポート状況を確認するまで暫定扱いとする。

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

**実際の結果**（2026-08-08 23:54 JST 実施）

```
49 passed in 0.05s
```

| テストファイル | ケース数 | 結果 |
| --- | --- | --- |
| `tests/test_metrics.py` | 27 | 全件 Pass |
| `tests/test_load_gen.py` | 22 | 全件 Pass |

カバーした関数: `validate_percent` / `build_payload` / `read_cpu_percent` / `read_memory_percent`
（D-7 の定義）/ `format_stdout_line` / `validate_cpu_target` / `validate_memory_target`
（85% クランプ）/ `calculate_duty_cycle` / `memory_percent_to_mb` / `format_jst`

**Red の記録**（代表タスク）

| タスク | Red で失敗したテスト | 失敗理由 |
| --- | --- | --- |
| 1.1 | **未記録** | 下記「TDD 順序の逸脱」参照 |
| 1.4 | **未記録** | 同上 |
| 1.9 | **未記録** | 同上 |
| 1.13 | **未記録** | 同上 |

**判定**: **Pass（テスト結果）／ Fail（R7-1 TDD 順序）**

- ユニットテストの内容と結果（R7-2〜R7-6, R7-8, R7-9）は Pass
- **R7-1（Red → Green → Refactor の順序）は未遵守**

**⚠️ TDD 順序の逸脱（R7-1 / tasks.md 1.1 節）**

本実装パスでは、実装とテストを同一セッション内でまとめて作成した。
「先に失敗するテストを書き、失敗を確認してから実装する」という順序を踏んでおらず、
`tasks.md` 1.1 節が求める Red の失敗ログは**存在しない**。

事後に Red ログを再現・作成すれば形式上は埋まるが、それは実際に行った作業と異なる記録になるため、
**意図的に空欄のまま「未記録」と明記する**。

影響と対処:

| 項目 | 内容 |
| --- | --- |
| 影響 | テストの網羅性そのものには影響しない（49 件が実装の振る舞いを検証している）。ただし「テストが実装を駆動した」証跡がないため、実装に寄せたテストになっている可能性を排除できない |
| 緩和策として実施したこと | `test_templates.py` の骨格作成時（タスク 2.1）はテンプレート未作成の状態で失敗を確認しており、この 1 件のみ Red → Green を経由している |
| 今後の対処 | 未実装の M5 および今後の修正・追加分では Red を先に記録する。既存分の遡及的な Red 再現は行わない |
| 記録先 | 8 章「設計・要件へのフィードバック一覧」に記載 |

**証跡**: `evidence/m1/M1-UT-pytest-result.txt`
（`evidence/m1/M1-UT-red-logs.txt` は**作成しない**。上記のとおり Red を経由していないため）

---

#### M1-S ローカルでのロジック疎通確認（タスク 1.1〜1.13 の補足）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | 2026-08-08 23:55 JST |
| マイルストーン | M1 |
| タスク ID | 1.1〜1.13 の補足（1.15 の代替ではない） |
| 対応要件 | R1-4, R1-5, R2-1, R2-2, R2-4, R2-8 |
| 対応設計 | D-7, D-9 |

**実行コマンド**

```bash
cd scripts/session-03 && source .venv/bin/activate
# ペイロード生成
python3 -c "from metrics import *; ..."   # evidence 参照
# 負荷生成 CLI（短時間）
python3 load_gen.py cpu --target 40 --duration 6
python3 load_gen.py memory --mb 128 --duration 4
```

**期待結果**

- ペイロードが 4.1 節の形式（4 フィールド）で生成される
- `format_stdout_line` が JST 表記で出力される
- 負荷生成 CLI が開始・終了予定・実終了時刻を JST で表示し、リソースを解放して終了する

**実際の結果**

ペイロード生成（開発機 macOS 上）:

```
[SEND] 2026-08-08 23:55:42 JST cpu=28.8% memory=49.9%
  payload: {"deviceId": "raspi-001", "cpu": 28.8, "memory": 49.9, "timestamp": 1786200942}
```

→ 4 フィールドのみ・JST 表記・小数第 1 位丸めを確認 ✅

負荷生成 CLI:

| 項目 | 結果 |
| --- | --- |
| CPU モード起動 | ✅ 10 ワーカー起動、duty 0.40 を表示 |
| 開始・終了予定・実終了時刻（JST）表示（R2-8） | ✅ |
| 進捗表示（R2-3） | ✅ 経過秒数と実測使用率を 1 秒ごとに表示 |
| 終了時のワーカー解放（R2-4） | ✅ プロセス残留なし |
| メモリモード確保・解放 | ✅ 128 MB 確保 → 解放 |
| メモリ安全上限の警告 | ✅（ユニットテストで検証済み） |

**⚠️ 発見事項：目標使用率と実測値の乖離（R2-11 への懸念）**

| 項目 | 値 |
| --- | --- |
| 指定した目標（`--target`） | 40.0 % |
| 実測 CPU 使用率 | **55.4 %** |
| 差分 | **+15.4 ポイント** |

`calculate_duty_cycle` は「duty = target / 100」で計算しており、
**実行時点で既に存在するベースライン負荷を考慮していない**。
そのため「目標値 ＝ 負荷生成分のみ」であり、実測値は「ベースライン ＋ 負荷生成分」になる。

R2-11 は「表示される使用率が目標値とおおむね一致（許容差 **±10 ポイント**）」を求めているため、
**この挙動のままでは R2-11 を満たさない可能性がある**。

ただし本計測は以下の条件下であり、実機での結論とは切り離して扱う。

- 開発機（macOS、10 コア、他プロセス稼働中）での計測
- 継続時間 6 秒（立ち上がり区間が平均に含まれる。設計の推奨は 180 秒）
- ハンズオン当日の実運用値は `--target 90`（90% 付近では天井効果で乖離が縮む見込み）

**判定**: **Pass（CLI の動作）／ 要確認（R2-11 の許容差）**

**証跡**: `evidence/m1/1.15-local-payload-smoke.txt`、`evidence/m1/1.15-load-gen-smoke.txt`

**備考 / 次のアクション**

- 実機（タスク 1.15）で `--target 90 --duration 180` を実測し、定常区間での乖離を確認する
- 乖離が ±10 ポイントを超える場合の選択肢（実機実測後に判断）:
  1. `calculate_duty_cycle` でベースライン負荷を差し引く（`psutil.cpu_percent` で事前計測して補正）
  2. `requirements.md` R2-11 の許容差を実測に基づいて見直す
  3. 「目標値は負荷生成分であり、実測はベースラインを含む」と手順書で明示し、要件の解釈を揃える
- 本件は `tasks.md` 5 章のリスク表「3 点セットが ±5 ポイントに収まらない」とは別事象（あちらは
  デバイス値と CloudWatch 値の一致、こちらは指定値と実測値の一致）

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

#### M2-0 テンプレート静的検証（タスク 2.1、2.5）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | 2026-08-08 23:55 JST |
| マイルストーン | M2 |
| タスク ID | 2.1, 2.5 |
| 対応要件 | R3-2, R3-3, R3-7, R6-5, R6-9, R7-7 |
| 対応設計 | D-1, D-2, D-3, D-8, K-3, K-4 |

**実行コマンド**

```bash
cd scripts/session-03 && source .venv/bin/activate
cfn-lint ../../cfn/session-03/*.yaml
pytest tests/test_templates.py -v
```

**期待結果**

- `cfn-lint` が 3 テンプレートすべてで合格（exit 0）
- ルールが `CloudwatchMetric` アクションを 2 つ持つ（R3-3）
- `AwsIotSqlVersion` が `2016-03-23`（R3-2）
- ルール名が `^[a-zA-Z0-9_]+$` に適合（K-4）
- `ErrorAction` が定義されている（R3-7）
- 必須 Outputs 8 項目が揃っている（R6-5）

**実際の結果**

```
cfn-lint ../../cfn/session-03/*.yaml   → exit 0（出力なし = 3 本すべて合格）
pytest tests/test_templates.py         → 17 passed
```

| 検証項目 | 結果 |
| --- | --- |
| `cfn-lint`（基本 / Lambda / Alarm） | ✅ 3 本合格 |
| `CloudwatchMetric` アクション数 = 2（R3-3） | ✅ |
| `AwsIotSqlVersion` = `2016-03-23`（R3-2） | ✅ |
| ルール名 `jawsug_s3_metrics_to_cw_raspi_001` の文字種（K-4） | ✅ ハイフンなし |
| `ErrorAction`（CloudwatchLogs）の存在（R3-7） | ✅ |
| 必須 Outputs 8 項目（R6-5） | ✅ |
| `DeviceNumber` の `AllowedPattern: ^[0-9]{3}$`（D-8） | ✅ |
| Lambda ロググループ保持 3 日（R4-5） | ✅ |
| Alarm の `TreatMissingData: notBreaching`（R5-6） | ✅ |
| `AlarmPeriodSeconds` の `MinValue >= 60`（4.3 節） | ✅ |
| メール `AllowedPattern` の存在 | ✅ |
| `OkNotificationEnabled` Condition の存在（R5-7） | ✅ |

**Red の記録（タスク 2.1）**

`test_templates.py` の骨格を先に作成した時点でテンプレートが未作成であり、
`cfn-lint` テストがファイル不存在で失敗することを確認した。
**M0〜M4 の中で Red → Green を経由したのはこの 1 件のみ**（M1-UT の備考参照）。

**cfn-lint 指摘への対処**

| 指摘 | 対処 |
| --- | --- |
| `W1020 'Fn::Sub' isn't needed because there are no variables`（基本テンプレート `MetricsConsoleUrl`） | 変数を含まないため `!Sub` を外して素の文字列にした |

**判定**: **Pass**

**証跡**: `evidence/m2/2.5-cfn-lint.txt`、`evidence/m3/M3-UT-pytest-result.txt`（`test_templates.py` を含む）

**備考**

- `aws cloudformation validate-template` は AWS 認証を要するため未実行（タスク 2.6 に持ち越し）
- K-3（`!Sub` と IoT 置換テンプレートの `${...}` 衝突）については、`MetricName` /
  `MetricValue` / `MetricTimestamp` で `!Sub` を使わない実装にしており、`cfn-lint` も通過。
  ただし**置換テンプレートが実際に評価されるかは実環境でしか確認できない**（タスク 2.7）

---

#### M2-F1 リソース名の衝突修正（F-1）— ✅ Red → Green を遵守

| 項目 | 内容 |
| --- | --- |
| 実施日時 | 2026-08-10 07:25 JST |
| マイルストーン | M2 |
| タスク ID | F-1（`next-actions.md` F セクション） |
| 対応要件 | R6-6, R7-1, NFR-8 |
| 対応設計 | D-12 |

**背景**

`iot-rules-cloudwatch.yaml` の `RuleErrorLogGroup` を `/aws/iot/session-03/rule-errors` という
**デバイス番号を含まない固定名**で実装していた。`design.md` 3.4 節の命名規約どおりだったが、
D-12（共有アカウントでも `DeviceNumber` で全リソース名が分離される）と矛盾する。
CloudWatch Logs のロググループ名はアカウント／リージョンで一意なため、
**同一アカウントで 2 人目のスタック作成が `AlreadyExists` で失敗する**。

**⭐ 本件は R7-1（Red → Green → Refactor）の順序を遵守した**

M1・M3 で逸脱していた TDD 順序について「今後の追加・修正分では Red を先に記録する」と
宣言していたため、その最初の適用例となる。

**Red（実装修正の前）**

追加したテスト: `tests/test_templates.py::TestResourceNameIsolation`
3 テンプレートすべてについて、明示的に名前を指定するプロパティ
（`LogGroupName` / `RoleName` / `FunctionName` / `TopicName` / `AlarmName` / `RuleName` /
`ThingName` / `PolicyName`）が `${DeviceNumber}` を含むことを検証する。

```bash
pytest tests/test_templates.py::TestResourceNameIsolation -v
```

```
tests/...::test_all_resource_names_include_device_number[basic]  FAILED
tests/...::test_all_resource_names_include_device_number[lambda] PASSED
tests/...::test_all_resource_names_include_device_number[alarm]  PASSED

E   AssertionError: iot-rules-cloudwatch.yaml: 以下のリソース名が DeviceNumber を含んでいません。
E     同一アカウントで複数の参加者が作成すると衝突します（D-12・NFR-8）。
E       RuleErrorLogGroup.LogGroupName = '/aws/iot/session-03/rule-errors'

1 failed, 2 passed in 0.05s
```

→ **意図したリソース 1 件のみが、意図した理由で失敗**。Lambda・Alarm テンプレートは
既にデバイス番号入りだったため Pass。テストが正しく問題を特定していることを確認。

**Green（修正後）**

```yaml
      LogGroupName: !Sub "/aws/iot/session-03/rule-errors-raspi-${DeviceNumber}"
```

```
3 passed in 0.03s                    # TestResourceNameIsolation
cfn-lint ... exit code: 0            # 3 テンプレート合格
81 passed in 1.92s                   # 全件（78 → 81 に増加）
```

**期待結果**

- [x] Red で基本テンプレートのみが失敗する
- [x] 修正後に 3 テンプレートすべて Pass
- [x] `cfn-lint` が引き続き合格
- [x] 既存 78 件のテストが壊れない

**実際の結果**: 上記のとおり全項目達成。テスト総数 78 → **81 件**。

**判定**: **Pass**

**証跡**: `evidence/m2/F-1-red.txt`、`evidence/m2/F-1-green.txt`

**副次的に対応した項目**

| # | 内容 |
| --- | --- |
| F-3b | `teardown.sh` の残存確認にロググループ 3 件のチェックを追加（ロググループ名が変わったため、あわせて対応） |
| — | `teardown.sh` の `read` に `-r` を付与（shellcheck SC2162）。`teardown.sh` / `show_metrics.sh` ともに shellcheck 指摘 0 件になった |

**更新した文書**

| ファイル | 箇所 |
| --- | --- |
| `cfn/session-03/iot-rules-cloudwatch.yaml` | `RuleErrorLogGroup.LogGroupName`（コメントで理由も記載） |
| `scripts/session-03/tests/test_templates.py` | `TestResourceNameIsolation` を追加（再発防止） |
| `scripts/session-03/teardown.sh` | ロググループの残存確認を追加、`read -r` |
| `spec/design.md` | 3.1 節の構成図、3.4 節の命名規約（＋注記）、5.3 節のリソース表 |
| `docs/session-03/handson.md` | AWS 側設定のリソース名表 |
| `spec/next-actions.md` | C-1 補足、F セクションの状態列 |
| `spec/verification-log.md` | M2-2 の確認コマンド、本エントリ |

**備考**

- 今後、同種の名前衝突はテストで自動検出される。**新しいリソースを追加するときは
  名前に `${DeviceNumber}` を含めること**がテストで強制される
- `RuleErrorLogGroupName` Output は `!Ref RuleErrorLogGroup` のままで正しく新名称を返す

---

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

**実際の結果**（2026-08-13 13:43〜13:47 JST 実施）

| 確認項目 | 結果 |
| --- | --- |
| `validate-template` | ✅ 成功。`CAPABILITY_NAMED_IAM` を要求することも確認 |
| スタック作成 | ✅ `CREATE_COMPLETE` |
| **作成所要時間** | **62 秒**（R6-7 の 300 秒以内 ✅） |
| Outputs | ✅ 必須 8 項目すべて出力（＋ `NextStep`）。R6-5 達成 |
| 作成リソース | ✅ 5 個（`IoTThing` / `IoTPolicy` / `IoTRuleRole` / `RuleErrorLogGroup` / `MetricsToCloudWatchRule`） |
| **F-1 の修正反映** | ✅ ロググループ名が `/aws/iot/session-03/rule-errors-raspi-001`（デバイス番号入り） |
| 証明書の発行 | ✅ `create-keys-and-certificate --set-as-active` で発行、`ACTIVE` を確認 |
| ポリシー／Thing へのアタッチ | ⏸ **未実施**（D-14 によりコンソールで実施する方針に変更） |

**ルール定義の確認（K-3・D-3 の重要な裏付け）**

`aws iot get-topic-rule` で登録済み定義を確認した結果、**置換テンプレートが CloudFormation に
消費されずリテラルとして保持**されていた。

```
SQL             : SELECT * FROM 'jawsug/session-03/+/metrics'
SQL バージョン  : 2016-03-23
アクション数    : cloudwatchMetric × 2（R3-3 ✅）
  [1] metricName = CpuUtilization-${topic(3)}      ← 置換テンプレートが保持されている
      metricValue = ${cast(cpu AS String)}
      metricTimestamp = ${cast(timestamp AS String)}
  [2] metricName = MemoryUtilization-${topic(3)}
      metricValue = ${cast(memory AS String)}
ErrorAction     : cloudwatchLogs → /aws/iot/session-03/rule-errors-raspi-001（R3-7 ✅）
```

→ **K-3（`!Sub` と置換テンプレートの `${...}` 衝突）はテンプレート定義レベルで回避できている**ことを実証。
ただし**実行時に評価されるか（`raspi-001` に展開されるか）はタスク 2.7 で確認**する。

**判定**: **Pass（機能・定義面）／ 未完了（画面手順・アタッチ）**

**⚠️ 実行手段についての注記（D-14）**

本エントリの実行は**すべて AWS CLI** で行った（検証を速く回すため）。
一方 2026-08-13 の方針決定により **手順書は UI 操作を主とする**（D-14 / R8-10〜12）。

リソースの作成手段が CLI かコンソールかで**出来上がるリソースは変わらない**ため、
上記の機能・定義面の検証結果はそのまま有効。ただし
**参加者が辿る画面手順の妥当性は別途コンソールで通す必要がある**（未実施）。

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
aws logs tail /aws/iot/session-03/rule-errors-raspi-001 --region ap-northeast-1
```

**期待結果**

- 送信開始から 3 分以内に 2 メトリクスが `list-metrics` に現れる
- メトリクス名が `CpuUtilization-raspi-001` / `MemoryUtilization-raspi-001`（置換テンプレートが評価されている）
- ErrorAction ログにエラーが出ていない（明示キャストが機能）
- メトリクスのタイムスタンプが送信時刻と一致している（時刻ずれがない）

**実際の結果**（2026-08-13 21:00〜21:03 JST。実機からの送信で確認）

| 確認項目 | 結果 |
| --- | --- |
| メトリクスの出現 | ✅ 送信開始から数分以内に 2 メトリクスが `list-metrics` に出現 |
| **メトリクス名** | ✅ **`CpuUtilization-raspi-001` / `MemoryUtilization-raspi-001`** |
| **置換テンプレートの実行時評価** | ✅ **`${topic(3)}` が `raspi-001` に展開されている**。リテラル `${...}` の残りなし |
| Dimensions | ✅ **なし**（設計どおり。K-5。コンソールでは「ディメンションなし」に入る） |
| ErrorAction ログ | ✅ **ログストリーム数 0** = アクション失敗が 1 件も発生していない |
| 値の一致 | ✅ publisher の `cpu=1.5% memory=30.9%` と CloudWatch の値が一致 |
| サンプル数 | ✅ `SampleCount = 6`（10 秒間隔 × 6 = 1 分。設計 4.3 節どおり） |

**🎯 K-3 / D-3 の実行時検証（本エントリの最重要点）**

タスク 2.6 では「ルール定義に `${topic(3)}` がリテラルで保持されている」ことまでを確認していたが、
**実行時に実際に評価されるかは未検証**だった。本エントリでそれが実証された。

| 段階 | 確認内容 | 結果 |
| --- | --- | --- |
| 定義時（2.6） | CloudFormation の `!Sub` に消費されず、リテラルで登録される | ✅ |
| **実行時（2.7）** | **メッセージ受信時に `raspi-001` へ展開される** | ✅ |
| 値のキャスト（D-3） | `${cast(cpu AS String)}` が機能し、アクションが失敗しない | ✅ ErrorAction ログが空 |

→ **`tasks.md` 5 章のリスク「置換テンプレートが期待どおり評価されない」は解消**。
最終手段として用意していた「`MetricName` を静的名に切り替える」代替案は不要になった。

**判定**: **Pass**

**証跡**: `evidence/m2/2.7-list-metrics.txt`（コンソールのスクリーンショットは未取得）

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

**実際の結果**（2026-08-13 21:08〜21:11 JST 実施。実機 Raspberry Pi 4 コア）

`load_gen.py cpu --target 90 --duration 180` を実行し、`get-metric-statistics`（期間 60 秒）で取得。

| 時刻 (JST) | 1 分平均 | 1 分最大 | サンプル数 | 備考 |
| --- | --- | --- | --- | --- |
| 21:04 | 1.03% | 1.50% | 6 | 平常時 |
| 21:05 | 1.37% | 2.00% | 6 | 平常時 |
| 21:06 | 1.47% | 2.00% | 6 | 平常時 |
| 21:07 | 1.68% | 2.50% | 6 | 平常時 |
| **21:08** | **50.52%** | 90.20% | 6 | **立ち上がり**（負荷開始 21:08:29 のため前半が平常・後半が負荷） |
| **21:09** | **90.07%** | 90.20% | 6 | **負荷が安定** |

| 項目 | 値 |
| --- | --- |
| 平常時 CPU（1 分平均） | **1.44%**（21:00〜21:07 の平均） |
| 負荷時 CPU（1 分平均） | **90.07%** |
| **差分** | **88.62 ポイント**（R2-7 の基準 30 ポイント以上を大幅に達成 ✅） |
| 期間 5 分での負荷時 CPU | _（未取得。コンソールでの目視確認時に記録）_ |

**副次的に実証できたこと**

| 内容 | 裏付け |
| --- | --- |
| 10 秒間隔 → 1 分あたり 6 サンプルに集約（設計 4.3 節） | 全データポイントで `SampleCount = 6` |
| 立ち上がり区間は 1 分平均で中途半端な値になる（4.3 節の注意） | 21:08 が 50.52%（平常 1.68% と負荷 90.07% の中間） |
| **F-2（負荷生成の乖離）は実機では発生しない** | 目標 90.0% に対し実測 90.2%（差 +0.2 ポイント） |

**判定**: **Pass**

**証跡**: `evidence/m2/2.8-graph-1min.png`（コンソールのスクリーンショットは未取得）

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

**実際の結果**（2026-08-13 21:00〜21:14 JST。実機 Raspberry Pi 2GB / 4 コア）

| 取得元 | 取得時刻 | CPU | メモリ |
| --- | --- | --- | --- |
| ① `show_metrics.sh` | 21:14 | 1.70% | 31.10% |
| ② publisher 送信値 `[SEND]` | 21:00 | 1.50% | 30.90% |
| ③ CloudWatch（期間 60 秒・平均） | 21:01 | 1.45% | 30.90% |
| **最大差分** | | **0.25 ポイント** | **0.20 ポイント** |

**判定**: **Pass（ただし条件付き）** — R2-12 の ±5 ポイントを大きく下回る差分。

**負荷区間での突き合わせ（より意味のある比較）**

| 取得元 | 値 |
| --- | --- |
| `load_gen.py` の実測表示（21:09 付近） | 90.2% |
| CloudWatch 1 分平均（21:09） | 90.07% |
| CloudWatch 1 分最大（21:09） | 90.20% |
| **差分** | **0.13〜0.13 ポイント** |

**`show_metrics.sh` の値の検算**

```
(total − available) / total × 100 = (1872 − 1289) / 1872 × 100 = 31.14%
→ 表示値 31.1% と一致 ✅
```

`used`(free 表記) は 507 MB で `total − available` の 583 MB と 76 MB の差がある。
これが buffers/cached の扱いの違い（K-2）で、**手順書に載せる具体例として使える**数字が得られた。

**⚠️ この検証の限界（正直に記録）**

- 3 つの値の**取得時刻が 21:00〜21:14 とばらついており、厳密な同時刻比較ではない**
- メモリは安定していたため比較に意味があるが、**CPU は変動するため参考値**
- 同一時刻で 3 値を揃えるには、負荷区間で `show_metrics.sh` と publisher 出力を同時に記録する必要がある
- **より厳密な突き合わせは M5 のリハーサル（5.10）で再取得する**

**証跡**: `evidence/m2/2.9-three-point-comparison.md`（未作成。上記の表で代替）

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

**実際の結果**（2026-08-13 14:04〜14:20 JST 実施。`teardown.sh` の初回実行）

| 確認項目 | 結果 |
| --- | --- |
| スタック削除 | ✅ `DELETE_COMPLETE` |
| Thing / IoT ポリシー / IoT ルール / IAM ロール / ロググループ | ✅ すべて削除を独立に確認 |
| ローカル `certs/` | ✅ 削除 |
| **証明書** | ❌ **削除されなかった**（下記 F-3d） |
| 空の状態での再実行（冪等性） | ✅ 落ちずに完走（exit 0） |

**判定**: **Fail →（修正後）Pass**

**🔴 発見 1（F-3d）：アタッチしていない証明書を検出できず、孤児として残る**

`teardown.sh` は「✅ 証明書の削除完了」と表示したが、**実際には 1 件も削除していなかった**。
独立検証で、発行した証明書が `ACTIVE` のまま残存していることを確認した。

| 項目 | 内容 |
| --- | --- |
| 原因 | 証明書を `list-thing-principals`（Thing にアタッチ済みの principal）からのみ探していた。今回は証明書を発行したが Thing へのアタッチ前に削除を実行したため、検出できなかった |
| なぜ気づけたか | スクリプトの表示を信用せず、`aws iot list-certificates` で独立に確認したため。**表示だけ見ていたら見逃していた**（F-3c「エラーを握り潰して成功と表示する」が実際に害を出した例） |
| 参加者への影響 | 「証明書を作ったがアタッチを忘れた」というよくある失敗のあと後片付けすると、証明書が残る（課金は無いが不衛生） |
| 対処 | 証明書の探索経路を **2 つ**にした。①Thing の principal ②**ポリシーのターゲット**（`list-targets-for-policy`）。加えて、1 件も見つからない場合は「✅ 完了」ではなく**警告を出し、コンソールでの確認を促す**ようにした |

**🔴 発見 2（F-3e）：UTF-8 ロケールで削除対象一覧が文字化けし、スタック名が消える**

出力に不正バイト（`0xBC`）が混入し、削除対象一覧が
`- ��アドバンス B: 存在する場合）` のように表示されていた（**スタック名が欠落**）。

| 項目 | 内容 |
| --- | --- |
| 原因 | `echo "    - $STACK_ALARM（アドバンス B...）"` のように **`$VAR` の直後に全角文字**が続いていた。UTF-8 ロケールの bash は全角文字の先頭バイトを変数名の一部として解釈し、変数が未定義になって残バイトが不正な出力になる |
| 再現条件 | `LC_ALL=C` では**正常**、`LC_ALL=en_US.UTF-8` で**壊れる**。最小再現で確認済み |
| 参加者への影響 | **大きい**。参加者の環境はほぼ UTF-8 であり、**R8-9（削除対象を事前に表示する）が実質的に機能していなかった**。何が削除されるか読めない状態で `y` を求めていた |
| 対処 | 該当 3 箇所を `${STACK_ALARM}（...` のようにブレース付きへ修正。修正後、UTF-8 ロケールで出力が妥当な UTF-8 になり、スタック名も正しく表示されることを確認 |
| 横展開 | 第1回・第2回の `teardown.sh` / `led_ctrl.sh`、および `show_metrics.sh` を同じパターンで検査 → **該当なし**（第3回のみの問題） |

**修正後の再検証**

```
bash -n teardown.sh        → 構文 OK
shellcheck teardown.sh     → 指摘 0 件
LC_ALL=en_US.UTF-8 で実行  → 出力は妥当な UTF-8。スタック名が正しく表示される
空の状態で再実行            → exit 0（冪等）
```

**あわせて修正した点**

- Thing の削除で、**存在しなくても「✅ 削除完了」と表示**されていた（`aws iot delete-thing` は対象が
  無くても成功扱いになる）。存在確認してからメッセージを出し分けるようにした（F-3c 系の是正）

**証跡**: `evidence/m2/2.10-teardown.txt`

**備考**

- 本エントリは「スタック削除の確認」と「`teardown.sh` の初回実行検証」を兼ねている
- 削除は方針変更（D-14：手順書は UI 操作を主とする）に伴う**やり直しのための削除**でもある。
  スタックは**コンソールから作り直す**（タスク 2.6 を再実施）
- 同一アカウントには別プロジェクトの証明書が 9 件あった。**作成日時（2026-08-13）と
  ポリシー／Thing 未紐付けの 2 条件で自分の証明書 1 件のみを特定**して削除し、他は触っていない

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

**実際の結果**（2026-08-08 23:55 JST 実施）

```
29 passed in 1.86s
```

| テストファイル | ケース数 | 結果 |
| --- | --- | --- |
| `tests/test_metrics_logger.py` | 11 | 全件 Pass |
| `tests/test_lambda_inline_sync.py` | 1 | Pass |
| `tests/test_templates.py` | 17 | 全件 Pass |

`test_metrics_logger.py` でカバーしたケース:

| ケース | 対応要件 | 結果 |
| --- | --- | --- |
| 正常イベントで `level=INFO` / `event=metrics_received` の JSON 1 行 | R4-2 | ✅ |
| `cpu` 欠落時に `level=WARN` で例外を出さない | R4-4 | ✅ |
| `cpu` が文字列（`"high"`）でも異常終了しない | R7-5 | ✅ |
| 出力が `json.loads()` でパースできる | R4-6 | ✅ |
| 空イベント `{}` でも WARN で処理 | R4-4 | ✅ |
| `topic` が INFO ログに含まれる | R4-2 | ✅ |

**インライン同期テスト（D-10）の実装方針**

`lambda/metrics_logger.py` と `advanced-lambda.yaml` の `Code.ZipFile` を比較する際、
docstring・コメント・空行を除いた「機能的な行」のみを抽出して比較する方式にした。
完全一致にしなかった理由は、テンプレート側のインデント調整で差分が出ると
本質的でない失敗が頻発するため。**機能コードの差異は検出できる**ことをテストで担保している。

**Red の記録**

| タスク | Red で失敗したテスト | 失敗理由 |
| --- | --- | --- |
| 3.1 | **未記録** | M1-UT の「TDD 順序の逸脱」と同じ理由。実装とテストを同一セッションで作成した |

**テスト実装時に実際に発生した失敗（参考）**

TDD の Red ではないが、初回実行時に以下 2 件が失敗し、修正して Green にした。
実際に起きた事象なので記録する。

| 失敗したテスト | 原因 | 対処 |
| --- | --- | --- |
| `test_templates.py`（`TestBasicTemplate` 系 11 件が ERROR） | `yaml.safe_load` が CloudFormation の `!Sub` / `!Ref` / `!GetAtt` タグを解釈できず `could not determine a constructor for the tag '!Sub'` | テスト側に `CfnLoader`（`yaml.SafeLoader` を継承し CFN タグを dict に変換）を実装 |
| `test_cfn_lint_passes[basic]` | 基本テンプレートの `MetricsConsoleUrl` が変数なしで `!Sub` を使用しており `W1020` 警告（exit 4） | `!Sub` を外して素の文字列にした |

**判定**: **Pass（テスト結果）／ Fail（R7-1 TDD 順序）**

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

#### M4-0 テンプレート静的検証（タスク 4.1、4.2）

| 項目 | 内容 |
| --- | --- |
| 実施日時 | 2026-08-08 23:55 JST |
| マイルストーン | M4 |
| タスク ID | 4.1, 4.2 |
| 対応要件 | R5-1, R5-3, R5-6, R5-7, R6-4, R6-5, R6-9, R7-7, NFR-7 |
| 対応設計 | D-11, D-13 |

**実行コマンド**

```bash
cd scripts/session-03 && source .venv/bin/activate
cfn-lint ../../cfn/session-03/advanced-alarm.yaml
pytest tests/test_templates.py::TestAlarmTemplate -v
```

**期待結果**

- `cfn-lint` 合格
- `TreatMissingData` が明示されている（R5-6）
- `Period` が 60 以上（4.3 節）
- メールの `AllowedPattern` が存在する
- 必須 Outputs（`AlarmTopicArn` / `AlarmName` / `AlarmConsoleUrl` / 承認リマインド）が揃う

**実際の結果**

| 検証項目 | 結果 |
| --- | --- |
| `cfn-lint` | ✅ 合格 |
| `TreatMissingData: notBreaching`（R5-6） | ✅ |
| `AlarmPeriodSeconds` の `MinValue: 60`（4.3 節） | ✅ |
| `NotificationEmail` の `AllowedPattern`（打ち間違い検出） | ✅ `^[^\s@]+@[^\s@]+\.[^\s@]+$` |
| `NoEcho` を使っていない（D-13 の方針どおり） | ✅ |
| 必須 Outputs 4 項目 | ✅ `ConfirmSubscriptionNote` に承認リマインド文を含む |
| `Conditions: OkNotificationEnabled` + `Fn::If`（R5-7） | ✅ |
| SNS `DisplayName: JAWSUG-IoT-Handson` | ✅ |
| Alarm 対象が CPU のみ（D-11） | ✅ メモリ Alarm は未作成 |
| 既定値（しきい値 80 / 期間 60 / 評価回数 1） | ✅ |

**判定**: **Pass**

**証跡**: `evidence/m2/2.5-cfn-lint.txt`（3 テンプレート分をまとめて記録）

**備考**

- しきい値・期間の既定値は `design.md` D-6 の暫定値のまま。**Q2 の最終確定はタスク 4.5（実環境）待ち**
- Email サブスクリプションの承認フロー（K-6）は**実環境でしか検証できない**ため、
  「CFN が承認を待たずに `CREATE_COMPLETE` になる」ことの裏付けは未取得（タスク 4.3）

---

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
| 2026-08-08 | M1-UT / M3-UT | （文書更新なし・記録のみ） | **R7-1（TDD の Red → Green 順序）を未遵守**。実装とテストを同一セッションで作成したため Red の失敗ログが存在しない。事後に再現した Red ログは実作業と異なる記録になるため作成しない方針とした。今後の追加・修正分では Red を先に記録する |
| 2026-08-08 | M1-S | （要対応・未反映） | 負荷生成の目標値と実測値に乖離（目標 40% に対し実測 55.4%、+15.4 ポイント）。`calculate_duty_cycle` がベースライン負荷を考慮していないため。**R2-11 の許容差 ±10 ポイントを満たさない可能性**があり、実機実測（タスク 1.15）後に「実装の補正」「R2-11 の見直し」「手順書での解釈明示」のいずれかを選択する |
| 2026-08-08 | M0-1 | （文書更新なし・記録のみ） | タスク 0.5 の「`pytest` がテスト 0 件で正常終了することを確認」は、実装とテストを同時に進めたため未経由。`--collect-only` での動作確認に代替した |
| 2026-08-08 | M2-0 | `cfn/session-03/iot-rules-cloudwatch.yaml` | `MetricsConsoleUrl` の `!Sub` を除去（変数を含まないため `cfn-lint W1020`） |
| 2026-08-08 | M3-UT | `scripts/session-03/tests/test_templates.py`、`test_lambda_inline_sync.py` | CFN の intrinsic function を扱うため `CfnLoader`（`yaml.SafeLoader` 継承）を追加 |
| 2026-08-08 | M3-UT | （設計判断・design.md 未更新） | D-10 のインライン同期テストを「完全一致」ではなく「docstring / コメント / 空行を除いた機能行の一致」で実装。インデント調整による本質的でない失敗を避けるため。`design.md` 8.1 節の記述と厳密には異なるが意図（機能コードの差異検出）は満たす |
| 2026-08-08 | 実装時 | （要修正・未反映） | 4 文書のヘッダーが配置先を `scripts/session-03/specs/` と記載しているが、実際のディレクトリは **`scripts/session-03/spec/`**（単数形）。`design.md` 5.1 節のディレクトリ構成図も `specs/` になっている。ドキュメント側の表記を実態に合わせるか、ディレクトリをリネームするかを M5 で統一する |
| 2026-08-08 | 実装レビュー | **`cfn/session-03/iot-rules-cloudwatch.yaml`（要修正・未反映）** | `RuleErrorLogGroup` を `/aws/iot/session-03/rule-errors` という**デバイス番号を含まない固定名**で実装した（`design.md` 3.4 節の命名規約どおり）。しかし D-12（共有アカウントでも `DeviceNumber` で全リソース名が分離される）と矛盾し、**同一アカウントで 2 人目のスタック作成が `AlreadyExists` で失敗する**。`advanced-lambda.yaml` 側はデバイス番号入りにしてあるため不統一でもある。`rule-errors-raspi-${DeviceNumber}` への変更を推奨。`next-actions.md` F-1 |
| 2026-08-08 | 実装レビュー | （要確認・未反映） | `teardown.sh` は `set -e` 下で `aws cloudformation wait stack-delete-complete` を呼ぶため、スタックが `DELETE_FAILED` になるとスクリプト全体が中断し、ローカル `certs/` 削除と残存確認が実行されない。また証明書削除の各呼び出しが `2>/dev/null \|\| true` でエラーを握り潰すため、1 件も削除できなくても「削除完了」と表示される。`next-actions.md` F-3a / F-3c |
| 2026-08-08 | M5 着手 | `docs/session-03/handson.md`（新規）、`scripts/session-03/spec/next-actions.md`（新規） | 実測不要のタスク 5.2・5.3 を先行実施し、手順書の骨格（ゴール / 進め方 / 所要時間 / 学習内容）を作成。実測依存のセクションは `<!-- TODO(タスクID) -->` と「🚧 執筆ステータス」ブロックで明示。あわせて実環境検証の実行手順を `next-actions.md` に整備し、「実行 → `verification-log.md` へ記録 → `handson.md` へ転記」の対応表を用意した |
| **2026-08-10** | **F-1 修正（M2-F1）** | `cfn/session-03/iot-rules-cloudwatch.yaml`、`spec/design.md` 3.1・3.4・5.3 節、`docs/session-03/handson.md`、`scripts/session-03/teardown.sh`、`tests/test_templates.py` | **上記 F-1 の指摘を解消**。`RuleErrorLogGroup` を `/aws/iot/session-03/rule-errors-raspi-${DeviceNumber}` に変更し、`design.md` の命名規約を実態に合わせて更新（「すべての明示的なリソース名にデバイス番号を含める」旨の注記を追加）。再発防止として `TestResourceNameIsolation` を追加し、3 テンプレートの全名前プロパティを機械的に検証。**本件は R7-1（Red → Green）を遵守**し、Red の失敗ログを `evidence/m2/F-1-red.txt` に保存 |
| 2026-08-10 | F-1 の副産物 | `scripts/session-03/teardown.sh` | 残存確認にロググループ 3 件のチェックを追加（F-3b 解消）。`read -r`（shellcheck SC2162）を修正。`teardown.sh` / `show_metrics.sh` ともに shellcheck 指摘 0 件 |
| **2026-08-13** | **構成図レビュー指摘（タスク 5.1）** | `docs/session-03/architecture.drawio`（新規）、`docs/session-03/handson.md` | 当初 SVG を手書きで生成してプロセス図（データフロー）にしていたが、レビューで **「Deployment 図にすべき。どの AWS サービスを利用しているか分からない」**「AWS 公式アイコンを使うこと」と指摘。方針を変更し、①図の種類を Deployment 図へ、②**破線枠 = CloudFormation スタック**でデプロイ単位を表現、③AWS 公式アイコン（draw.io 内蔵 `mxgraph.aws4`）を使用、④SVG 手書きをやめて **`.drawio` を成果物**とし SVG は draw.io から書き出す方式に変更。手書き SVG（`architecture.drawio.svg`）は削除した |
| **2026-08-13** | **ウォークスルーでの発見（メトリクス画面の表記と期間設定）** | `docs/session-03/handson.md` | ①正確なラベルは「**ディメンションなしのメトリクス**」（私の記述は「ディメンションなし」で不正確）。②**「期間」の設定場所を誤記していた**：右上の `⟳ 1 分` は**グラフの自動更新間隔**であり、メトリクスの集計期間ではない。期間は「**グラフ化したメトリクス**」タブの「期間」列で変更する。**どちらも「1 分」と表示されるため混同しやすく**、参加者が「期間を変えたのにグラフが変わらない」と詰まる典型パターン。手順書とハマりポイント表の両方に反映 |
| **2026-08-13** | **グラフの目視確認（R2-7 の裏付け）** | （記録のみ） | コンソールのスクリーンショットで**負荷区間が台形として明確に視認できる**ことを確認（21:07 頃に立ち上がり 21:12 頃に下降、約 1% → 約 90%）。`get-metric-statistics` の数値（差分 88.62 ポイント）と目視の両方で R2-7 を満たすことを確認した |
| **2026-08-13** | **ウォークスルーでの発見（CloudWatch コンソール刷新）** | `docs/session-03/handson.md` | CloudWatch のコンソールが刷新されており、左メニューの「**すべてのメトリクス**」が **「クラシックメトリクス」**に変わっていた（メトリクス配下は「Query Studio」「クラシックメトリクス」「エクスプローラー」「ストリーム」）。ログ配下も「**ログ管理**」「**ログ分析**」（従来の Logs Insights）に変更。手順書の該当箇所を修正し、刷新の経緯を補足として記載。ハマりポイント表にも追加。**ログ配下の 2 箇所は画面未確認のため 🔎 のまま**（Advanced Course1 のウォークスルーで確定させる） |
| **2026-08-13** | **教訓（コンソール表記の陳腐化）** | （記録のみ） | コンソールの UI 名称は予告なく変わる。手順書に画面名を書く方針（D-14）を採るなら、**開催直前に画面名を再確認する工程**が必要。M5 のリハーサル（5.10）でメニュー名の突き合わせを必ず行うこととする |
| **2026-08-13** | **ウォークスルーでの発見（タイムゾーン）** | `scripts/session-03/show_metrics.sh`、`docs/session-03/handson.md` | 実機の `timedatectl` が **`Europe/London (BST, +0100)`** だった（Raspberry Pi OS の初期値。貸出機すべてが該当する可能性が高い）。これを機に **`show_metrics.sh` のバグ（F-8）を発見**：`date` を OS のタイムゾーンで実行しながらラベルは「JST」固定だったため、**8〜9 時間ずれた時刻を JST と表示**していた。`TZ=Asia/Tokyo date` に修正。**送信データ自体は Unix エポック秒なので影響なし**（Python 側は `metrics.py` / `load_gen.py` が明示的に JST 変換しており正しかった）。手順書に「時刻とタイムゾーンの確認」節を新設し、`sudo timedatectl set-timezone Asia/Tokyo` を手順化。ハマりポイント表にも追加 |
| **2026-08-13** | **運営への申し送り（タイムゾーン）** | （要対応・未反映） | 貸出 Raspberry Pi の**タイムゾーンを事前に `Asia/Tokyo` に設定しておく**ことを推奨。当日に全員が `sudo timedatectl set-timezone` を実行すると時間を取られる。事前設定できない場合は手順書の該当節で対応可能 |
| **2026-08-13** | **手順書の全面書き直し（タスク 5.4〜5.8）** | `docs/session-03/handson.md`（782 行に全面改稿）、`tasks.md` | D-14（UI 主体）に沿って **AWS CLI 前提の記述を排し、コンソール操作で全編を書き直した**。第2回の構成・トーンに準拠。**第2回の B ルート（全リソースを手動作成）は設けない**判断とした（第3回は IAM ロール・ロググループ・ルールと重く、90 分に収まらないため）。代わりに **「作られたルールを見てみる」節を新設**し、CFN で作ったルールの SQL・アクション 2 つ・エラーアクション・置換テンプレートを**画面で確認する学習ステップ**を必須手順として組み込んだ（今回の主題が Rules であるため、IaC で作って終わりにしない）。後片付けはスクリプト版とコンソール版の両方を記載。画面名など未確認の 14 箇所に 🔎 を付与し、ウォークスルーで確定する運用にした |
| 2026-08-13 | 同上（検証方法） | （記録のみ） | AWS 公式アイコンのシェイプ名・カテゴリ色を**推測せず**、draw.io の `Sidebar-AWS4.js` 実定義を参照して確認した（`iot_core`/`#7AA116`、`lambda`/`#ED7100`、`cloudwatch_2`・`sns`・`alarm`・`cloudwatch_logs`/`#E7157B`、`group_aws_cloud_alt`・`group_region`・`group_corporate_data_center`、`illustration_devices`・`illustration_notification`）。当初 `cloudwatch_alarm` と推測していたが正しくは `alarm` であり、確認した価値があった |
| 2026-08-13 | 同上（制約） | （解決済み） | ローカルに draw.io / CLI がなく `.drawio` から SVG を書き出せなかった。**リポジトリオーナーが `architecture-v2.drawio` / `architecture-v2.svg` を作成**し、これを正とすることで解決。私が作成した `architecture.drawio` は削除した |
| **2026-08-13** | **構成図の作成者変更（タスク 5.1）** | `docs/session-03/architecture-v2.drawio`、`architecture-v2.svg`（オーナー作成）、`docs/session-03/handson.md` | 私が作成した図はアーキテクチャの粒度が想定と合わなかったため、**オーナーが v2 を作成**。v2 を正とし、私の `architecture.drawio` を削除。v2 は AWS 公式アイコン（`iot_core` / `lambda` / `cloudwatch_2` / `sns` / `alarm` / `logs` / `rule` / `hardware_board`）を使用し、**コース単位（Basic / Advanced Course1 / Advanced Course2）でグルーピング**する粒度。handson.md に SVG を埋め込み、コース名を図に合わせて統一した |
| **2026-08-13** | **前提変更：リモート参加なし・全員が実機を操作** | `requirements.md` 1.3・R1-9・NFR-9・M1 成果物、`design.md` 5.1・5.2・K-8・11 章、`tasks.md` 1.8・成果物一覧、`docs/session-03/handson.md`、`spec/next-actions.md`、`scripts/session-03/simulator.py` | 「リモート参加者・実機なし参加者はシミュレーターで代替」という当初前提を、**全員が会場で貸出 Raspberry Pi を操作する**前提に変更。**R1-9（シミュレーター提供）と NFR-9（可搬性）を削除**（取り消し線で履歴を残す）。`simulator.py` は削除せず**運営用の予備**（当日の実機故障時のバックアップ／実機なしでの AWS 経路検証）に位置付け変更し、**手順書には記載しない**方針とした。K-8（会場 Wi-Fi で 8883 が通らないリスク）は「PC のシミュレーターで代替」という逃げ道が無くなったため、**予備の Raspberry Pi を運営側で用意する**方針を追記 |
