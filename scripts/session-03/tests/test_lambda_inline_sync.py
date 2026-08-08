"""Lambda インラインコードの同期テスト（D-10）。

テンプレートのインラインコードが lambda/metrics_logger.py と一致することを検証する。
"""

import sys
import textwrap
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# パス
LAMBDA_SOURCE = Path(__file__).resolve().parent.parent / "lambda" / "metrics_logger.py"
CFN_DIR = Path(__file__).resolve().parent.parent.parent.parent / "cfn" / "session-03"
LAMBDA_TEMPLATE = CFN_DIR / "advanced-lambda.yaml"


class CfnLoader(yaml.SafeLoader):
    """CloudFormation の intrinsic functions を扱う YAML ローダー。"""
    pass


def _cfn_tag_constructor(loader, tag_suffix, node):
    if isinstance(node, yaml.ScalarNode):
        value = loader.construct_scalar(node)
        if tag_suffix == "Ref":
            return {"Ref": value}
        return {f"Fn::{tag_suffix}": value}
    elif isinstance(node, yaml.SequenceNode):
        value = loader.construct_sequence(node)
        return {f"Fn::{tag_suffix}": value}
    elif isinstance(node, yaml.MappingNode):
        value = loader.construct_mapping(node)
        return {f"Fn::{tag_suffix}": value}
    return {f"Fn::{tag_suffix}": None}


for tag in ["Sub", "Ref", "GetAtt", "If", "Equals", "Select", "Split", "Join"]:
    CfnLoader.add_constructor(
        f"!{tag}",
        lambda loader, node, t=tag: _cfn_tag_constructor(loader, t, node),
    )


class TestLambdaInlineSync:
    """Lambda ソースとテンプレートのインラインコードの同期検証。"""

    def test_inline_code_matches_source(self):
        """テンプレートのインラインコードが lambda/metrics_logger.py と一致する（D-10）。

        完全一致ではなく、docstring とコメントを除いた機能部分が一致することを検証する。
        """
        # ソースファイルを読み込み
        source_content = LAMBDA_SOURCE.read_text()

        # テンプレートからインラインコードを抽出
        with open(LAMBDA_TEMPLATE) as f:
            template = yaml.load(f, Loader=CfnLoader)

        function_resource = template["Resources"]["MetricsLoggerFunction"]
        inline_code = function_resource["Properties"]["Code"]["ZipFile"]

        # 機能的な行（空行・コメント行・docstring を除外）を比較
        def extract_functional_lines(code: str) -> list[str]:
            """コードから機能的な行を抽出する。"""
            lines = []
            in_docstring = False
            for line in code.split("\n"):
                stripped = line.strip()
                # docstring の開始/終了
                if '"""' in stripped:
                    if in_docstring:
                        in_docstring = False
                        continue
                    elif stripped.startswith('"""') or stripped.startswith("'"):
                        # 1 行 docstring
                        if stripped.count('"""') >= 2:
                            continue
                        in_docstring = True
                        continue
                    else:
                        continue
                if in_docstring:
                    continue
                # 空行とコメント行をスキップ
                if not stripped or stripped.startswith("#"):
                    continue
                lines.append(stripped)
            return lines

        source_lines = extract_functional_lines(source_content)
        inline_lines = extract_functional_lines(inline_code)

        assert source_lines == inline_lines, (
            "Lambda ソースとテンプレートのインラインコードが一致しません。\n"
            "lambda/metrics_logger.py を更新した場合は、"
            "cfn/session-03/advanced-lambda.yaml のインラインコードも更新してください。"
        )
