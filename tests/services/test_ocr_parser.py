"""Tests for ocr_parser service."""

import json

from chronocare.services.ocr_parser import (
    VALID_RECORD_TYPES,
    _parse_json_robust,
    _strip_code_fences,
)


class TestStripCodeFences:
    def test_with_json_fence(self) -> None:
        text = '```json\n{"a": 1}\n```'
        assert _strip_code_fences(text) == '{"a": 1}'

    def test_with_plain_json(self) -> None:
        assert _strip_code_fences('{"a": 1}') == '{"a": 1}'

    def test_with_code_fence_no_lang(self) -> None:
        text = '```\n{"a": 1}\n```'
        assert _strip_code_fences(text) == '{"a": 1}'

    def test_whitespace_stripped(self) -> None:
        text = '  ```json  \n{"a":1}  \n  ```  '
        assert _strip_code_fences(text) == '{"a":1}'


class TestParseJsonRobust:
    def test_plain_json(self) -> None:
        assert _parse_json_robust('{"a": 1}') == {"a": 1}

    def test_with_code_fences(self) -> None:
        data = {"name": "空腹血糖", "value": "6.2", "unit": "mmol/L",
                "reference": "3.9-6.1", "status": "slightly_high"}
        text = f'```json\n{{"tests": [{json.dumps(data, ensure_ascii=False)}]}}\n```'
        result = _parse_json_robust(text)
        assert result["tests"][0]["name"] == "空腹血糖"
        assert result["tests"][0]["status"] == "slightly_high"

    def test_with_trailing_text(self) -> None:
        result = _parse_json_robust('some text before{"a":1}and text after')
        assert result == {"a": 1}

    def test_nested_json(self) -> None:
        data = {"name": "血糖", "value": "6.2", "unit": "mmol/L",
                "reference": "3.9-6.1", "status": "slightly_high"}
        text = f'```json\n{{"diagnosis": ["糖尿病"], "tests": [{json.dumps(data, ensure_ascii=False)}]}}\n```'
        result = _parse_json_robust(text)
        assert result["diagnosis"] == ["糖尿病"]


class TestValidRecordTypes:
    def test_all_four_types_defined(self) -> None:
        expected = {"medical_record", "lab_report", "prescription", "doctor_order"}
        assert VALID_RECORD_TYPES == expected
