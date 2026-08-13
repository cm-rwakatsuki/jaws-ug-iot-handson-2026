"""リポジトリに機微情報が混入していないことを検証する。

ハンズオンのスクリプトは「参加者が冒頭の設定値を書き換える」方式のため、
検証者や参加者が**実際の値を書いたままコミットしてしまう**事故が起きやすい。
実際に 2026-08-14 の点検で、実 IoT エンドポイントがコミットされていたことが判明した（F-13）。

コミット前にこのテストで気づけるようにする。
"""

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

# 設定値を書き換える方式のスクリプト（実値が混入しやすい）
CONFIG_SCRIPTS = [
    "scripts/session-01/device.py",
    "scripts/session-01/simulator.py",
    "scripts/session-02/shadow_led.py",
    "scripts/session-03/metrics_publisher.py",
    "scripts/session-03/simulator.py",
]

# placeholder は x の並びのみ許可する
PLACEHOLDER_ENDPOINT = re.compile(r'^x+-ats\.iot\.[a-z0-9-]+\.amazonaws\.com$')
REAL_ENDPOINT = re.compile(r'\b([a-z0-9]{8,})-ats\.iot\.[a-z0-9-]+\.amazonaws\.com\b')

SECRET_PATTERNS = [
    ("秘密鍵ブロック", re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
    ("証明書ブロック", re.compile(r'-----BEGIN CERTIFICATE-----')),
    ("AWS アクセスキー ID", re.compile(r'\b(?:AKIA|ASIA|AIDA|AROA)[0-9A-Z]{12,}\b')),
    ("AWS アカウント ID（12 桁）", re.compile(r'(?<!\d)\d{12}(?!\d)')),
]


def tracked_files():
    """git 管理対象（＝公開されうる）ファイルの一覧。"""
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True
    ).stdout.split()
    return [REPO_ROOT / f for f in out]


@pytest.mark.parametrize("rel_path", CONFIG_SCRIPTS)
def test_endpoint_is_placeholder(rel_path):
    """設定スクリプトの Endpoint がプレースホルダのままであること。"""
    path = REPO_ROOT / rel_path
    if not path.exists():
        pytest.skip(f"{rel_path} が存在しない")

    found = REAL_ENDPOINT.findall(path.read_text(encoding="utf-8"))
    real = [f for f in found if not PLACEHOLDER_ENDPOINT.match(f"{f}-ats.iot.ap-northeast-1.amazonaws.com")]
    assert not real, (
        f"{rel_path} に実際の IoT エンドポイントらしき値が含まれています。\n"
        f"  検出: {[r[:4] + '...' for r in real]}\n"
        "  プレースホルダ（xxxxxx-ats.iot....）に戻すか、環境変数で渡してください"
    )


def test_no_secrets_in_tracked_files():
    """git 管理対象のファイルに秘密鍵・アクセスキー・アカウント ID がないこと。"""
    violations = []
    for path in tracked_files():
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(REPO_ROOT)
        for name, rx in SECRET_PATTERNS:
            if rx.search(text):
                violations.append(f"{rel}: {name}")

    assert not violations, "機微情報が混入しています:\n  " + "\n  ".join(violations)


def test_certs_directories_are_ignored():
    """証明書ディレクトリが git 管理対象に含まれていないこと（NFR-6）。"""
    tracked = [str(p.relative_to(REPO_ROOT)) for p in tracked_files()]
    leaked = [
        t for t in tracked
        if "/certs/" in t and not t.endswith(".gitignore")
    ]
    assert not leaked, f"証明書ディレクトリのファイルが管理対象です: {leaked}"
