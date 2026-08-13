"""CloudFormation テンプレートのユニットテスト。

テスト対象:
- cfn-lint による静的検証（R6-9、R7-7）
- テンプレート構造の検証（アクション数、SQL バージョン、ルール名文字種など）
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

# テンプレートのパス
CFN_DIR = Path(__file__).resolve().parent.parent.parent.parent / "cfn" / "session-03"
BASIC_TEMPLATE = CFN_DIR / "iot-rules-cloudwatch.yaml"
LAMBDA_TEMPLATE = CFN_DIR / "advanced-lambda.yaml"
ALARM_TEMPLATE = CFN_DIR / "advanced-alarm.yaml"


class CfnLoader(yaml.SafeLoader):
    """CloudFormation の intrinsic functions を扱う YAML ローダー。"""
    pass


# CloudFormation の ! タグを処理するコンストラクタを登録
def _cfn_tag_constructor(loader, tag_suffix, node):
    """CloudFormation タグをそのまま dict として返す。"""
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


# よく使う CloudFormation タグを登録
for tag in ["Sub", "Ref", "GetAtt", "If", "Equals", "Select", "Split", "Join"]:
    CfnLoader.add_constructor(
        f"!{tag}",
        lambda loader, node, t=tag: _cfn_tag_constructor(loader, t, node),
    )


def load_template(path: Path) -> dict:
    """YAML テンプレートを CloudFormation intrinsic functions 対応で読み込む。"""
    with open(path) as f:
        return yaml.load(f, Loader=CfnLoader)


# ============================================================
# cfn-lint 検証（R6-9、R7-7）
# ============================================================


class TestCfnLint:
    """cfn-lint による静的検証。"""

    @pytest.mark.parametrize(
        "template_path",
        [BASIC_TEMPLATE, LAMBDA_TEMPLATE, ALARM_TEMPLATE],
        ids=["basic", "lambda", "alarm"],
    )
    def test_cfn_lint_passes(self, template_path):
        """テンプレートが cfn-lint に合格する。"""
        result = subprocess.run(
            ["cfn-lint", str(template_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"cfn-lint failed for {template_path.name}:\n{result.stdout}\n{result.stderr}"
        )


# ============================================================
# リソース名の分離検証（D-12 / R6-6）
# ============================================================

# 明示的に名前を指定するプロパティ（すべて DeviceNumber を含む必要がある）
NAME_PROPERTIES = [
    "LogGroupName",
    "RoleName",
    "FunctionName",
    "TopicName",
    "AlarmName",
    "RuleName",
    "ThingName",
    "PolicyName",
]


def as_name_string(value):
    """名前プロパティの値を文字列として取り出す。

    CfnLoader により !Sub は {"Fn::Sub": "..."} になる。
    """
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and "Fn::Sub" in value:
        sub = value["Fn::Sub"]
        if isinstance(sub, str):
            return sub
    return None


def collect_named_resources(template: dict):
    """テンプレートから (論理ID, プロパティ名, 名前文字列) を集める。"""
    found = []
    for logical_id, resource in template.get("Resources", {}).items():
        props = resource.get("Properties", {})
        if not isinstance(props, dict):
            continue
        for prop in NAME_PROPERTIES:
            if prop in props:
                name = as_name_string(props[prop])
                if name is not None:
                    found.append((logical_id, prop, name))
    return found


class TestResourceNameIsolation:
    """すべての明示的なリソース名が DeviceNumber を含むこと（D-12・R6-6）。

    同一 AWS アカウントで複数の参加者が並行してスタックを作成しても
    名前が衝突しないことを担保する（NFR-8）。
    """

    @pytest.mark.parametrize(
        "template_path",
        [BASIC_TEMPLATE, LAMBDA_TEMPLATE, ALARM_TEMPLATE],
        ids=["basic", "lambda", "alarm"],
    )
    def test_all_resource_names_include_device_number(self, template_path):
        """明示的に名前を付けた全リソースが ${DeviceNumber} を含む。"""
        template = load_template(template_path)
        named = collect_named_resources(template)

        # 名前を明示しているリソースが 1 つ以上あること（テスト自体の妥当性確認）
        assert named, f"{template_path.name} に名前付きリソースが見つかりません"

        violations = [
            f"{logical_id}.{prop} = {name!r}"
            for logical_id, prop, name in named
            if "${DeviceNumber}" not in name
        ]

        assert not violations, (
            f"{template_path.name}: 以下のリソース名が DeviceNumber を含んでいません。\n"
            "同一アカウントで複数の参加者が作成すると衝突します（D-12・NFR-8）。\n  "
            + "\n  ".join(violations)
        )


# ============================================================
# 基本テンプレートの構造検証
# ============================================================


class TestBasicTemplate:
    """iot-rules-cloudwatch.yaml の構造検証。"""

    @pytest.fixture
    def template(self):
        return load_template(BASIC_TEMPLATE)

    def test_has_two_cloudwatch_metric_actions(self, template):
        """ルールが CloudwatchMetric アクションを 2 つ持つ（R3-3）。"""
        rule = template["Resources"]["MetricsToCloudWatchRule"]
        actions = rule["Properties"]["TopicRulePayload"]["Actions"]
        cw_actions = [a for a in actions if "CloudwatchMetric" in a]
        assert len(cw_actions) == 2

    def test_sql_version_2016(self, template):
        """AwsIotSqlVersion が 2016-03-23（R3-2）。"""
        rule = template["Resources"]["MetricsToCloudWatchRule"]
        version = rule["Properties"]["TopicRulePayload"]["AwsIotSqlVersion"]
        assert version == "2016-03-23"

    def test_rule_name_valid_chars(self, template):
        """ルール名が [a-zA-Z0-9_] のみ（K-4）。"""
        rule = template["Resources"]["MetricsToCloudWatchRule"]
        rule_name_pattern = rule["Properties"]["RuleName"]
        # CfnLoader では !Sub が {"Fn::Sub": "..."} として返る
        if isinstance(rule_name_pattern, dict) and "Fn::Sub" in rule_name_pattern:
            rule_name = rule_name_pattern["Fn::Sub"].replace("${DeviceNumber}", "001")
        elif isinstance(rule_name_pattern, str):
            rule_name = rule_name_pattern.replace("${DeviceNumber}", "001")
        else:
            pytest.skip("Complex intrinsic function, validated by cfn-lint")
            return

        assert re.match(r"^[a-zA-Z0-9_]+$", rule_name), (
            f"ルール名に無効な文字が含まれています: {rule_name}"
        )

    def test_has_error_action(self, template):
        """ErrorAction が定義されている（R3-7）。"""
        rule = template["Resources"]["MetricsToCloudWatchRule"]
        error_action = rule["Properties"]["TopicRulePayload"].get("ErrorAction")
        assert error_action is not None

    def test_required_outputs(self, template):
        """必須 Outputs が揃っている（R6-5）。"""
        outputs = template.get("Outputs", {})
        required = [
            "ThingName",
            "MetricsTopic",
            "RuleName",
            "MetricNamespace",
            "CpuMetricName",
            "MemoryMetricName",
            "MetricsConsoleUrl",
            "RuleErrorLogGroupName",
        ]
        for key in required:
            assert key in outputs, f"Output '{key}' が見つかりません"

    def test_device_number_pattern(self, template):
        """DeviceNumber パラメータが 3 桁数字制約を持つ（D-8）。"""
        param = template["Parameters"]["DeviceNumber"]
        assert param.get("AllowedPattern") == "^[0-9]{3}$"


# ============================================================
# Lambda テンプレートの構造検証
# ============================================================


class TestLambdaTemplate:
    """advanced-lambda.yaml の構造検証。"""

    @pytest.fixture
    def template(self):
        return load_template(LAMBDA_TEMPLATE)

    def test_has_lambda_permission(self, template):
        """Lambda::Permission が定義されている。"""
        assert "LambdaInvokePermission" in template["Resources"]

    def test_log_retention_3_days(self, template):
        """ロググループの保持期間が 3 日（R4-5）。"""
        log_group = template["Resources"]["MetricsLoggerLogGroup"]
        assert log_group["Properties"]["RetentionInDays"] == 3

    def test_has_error_action(self, template):
        """ErrorAction が定義されている。"""
        rule = template["Resources"]["MetricsToLambdaRule"]
        error_action = rule["Properties"]["TopicRulePayload"].get("ErrorAction")
        assert error_action is not None


# ============================================================
# Alarm テンプレートの構造検証
# ============================================================


class TestAlarmTemplate:
    """advanced-alarm.yaml の構造検証。"""

    @pytest.fixture
    def template(self):
        return load_template(ALARM_TEMPLATE)

    def test_treat_missing_data_specified(self, template):
        """TreatMissingData が明示されている（R5-6）。"""
        alarm = template["Resources"]["CpuHighAlarm"]
        assert "TreatMissingData" in alarm["Properties"]
        assert alarm["Properties"]["TreatMissingData"] == "notBreaching"

    def test_period_at_least_60(self, template):
        """Period パラメータが 60 以上（4.3 節）。"""
        param = template["Parameters"]["AlarmPeriodSeconds"]
        assert param.get("MinValue", 0) >= 60

    def test_email_allowed_pattern(self, template):
        """NotificationEmail に AllowedPattern がある。"""
        param = template["Parameters"]["NotificationEmail"]
        assert "AllowedPattern" in param

    def test_required_outputs(self, template):
        """必須 Outputs が揃っている。"""
        outputs = template.get("Outputs", {})
        required = ["AlarmTopicArn", "AlarmName", "AlarmConsoleUrl", "ConfirmSubscriptionNote"]
        for key in required:
            assert key in outputs, f"Output '{key}' が見つかりません"

    def test_has_condition_for_ok_actions(self, template):
        """EnableOkNotification の Condition が定義されている。"""
        conditions = template.get("Conditions", {})
        assert "OkNotificationEnabled" in conditions
