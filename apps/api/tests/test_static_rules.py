from app.code.rules import StaticRuleAnalyzer


def test_static_rules_find_hardcoded_secret_with_line_evidence():
    findings = StaticRuleAnalyzer().analyze_chunk(
        {
            "path": "app/security.py",
            "start_line": 10,
            "end_line": 12,
            "content": "API_KEY = 'secret-token'\nprint(API_KEY)\n",
        }
    )

    assert findings[0].title == "Hardcoded secret candidate"
    assert findings[0].evidence[0].path == "app/security.py"
    assert findings[0].evidence[0].start_line == 10


def test_static_rules_find_bare_except():
    findings = StaticRuleAnalyzer().analyze_chunk(
        {
            "path": "app/main.py",
            "start_line": 40,
            "end_line": 44,
            "content": "try:\n    work()\nexcept:\n    pass\n",
        }
    )

    assert findings[0].title == "Bare except hides failures"
    assert findings[0].severity == "medium"
