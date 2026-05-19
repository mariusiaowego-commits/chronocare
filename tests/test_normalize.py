"""Tests for medical record output normalization functions."""

from chronocare.services.medical_record import (
    normalize_doctor_orders,
    normalize_lab_results,
    normalize_structured_data,
)


class TestNormalizeLabResults:
    """Test lab_results normalization."""

    def test_already_correct_format_passthrough(self):
        data = {
            "tests": [
                {"name": "WBC", "value": "8.5", "unit": "10^9/L", "reference": "4-10", "status": "normal"}
            ],
            "summary": "正常"
        }
        result = normalize_lab_results(data)
        assert result["tests"][0]["name"] == "WBC"
        assert result["tests"][0]["status"] == "normal"

    def test_vision_analyze_format_conversion(self):
        """Convert vision_analyze lab_items format to tests format."""
        data = {
            "lab_items": [
                {
                    "item_name": "白细胞计数",
                    "result": "88",
                    "reference_range": "0-15",
                    "is_abnormal": True
                },
                {
                    "item_name": "尿比重",
                    "result": "1.015",
                    "reference_range": "1.005-1.030",
                    "is_abnormal": False
                }
            ]
        }
        result = normalize_lab_results(data)
        assert "tests" in result
        assert len(result["tests"]) == 2
        assert result["tests"][0]["name"] == "白细胞计数"
        assert result["tests"][0]["value"] == "88"
        assert result["tests"][0]["reference"] == "0-15"
        assert result["tests"][0]["status"] == "high"  # is_abnormal=True → high
        assert result["tests"][1]["status"] == "normal"  # is_abnormal=False → normal

    def test_chinese_field_names(self):
        data = {
            "lab_items": [
                {"项目": "血糖", "结果": "6.5", "单位": "mmol/L", "参考范围": "3.9-6.1"}
            ]
        }
        result = normalize_lab_results(data)
        assert result["tests"][0]["name"] == "血糖"
        assert result["tests"][0]["value"] == "6.5"
        assert result["tests"][0]["unit"] == "mmol/L"
        assert result["tests"][0]["reference"] == "3.9-6.1"

    def test_status_normalization(self):
        """Various status strings should normalize correctly."""
        cases = [
            ("high", "high"),
            ("偏高", "high"),
            ("elevated", "high"),
            ("↑", "high"),
            ("low", "low"),
            ("偏低", "low"),
            ("slightly_high", "slightly_high"),
            ("略高", "slightly_high"),
            ("slightly_low", "slightly_low"),
            ("normal", "normal"),
            ("正常", "normal"),
            ("unknown_value", "normal"),  # fallback
            (None, "normal"),  # missing
        ]
        for raw, expected in cases:
            data = {"tests": [{"name": "x", "value": "1", "unit": "", "reference": "", "status": raw}]}
            result = normalize_lab_results(data)
            assert result["tests"][0]["status"] == expected, f"Failed for {raw!r}"

    def test_error_dict_passthrough(self):
        data = {"error": "something failed"}
        assert normalize_lab_results(data) == data

    def test_none_passthrough(self):
        assert normalize_lab_results(None) is None

    def test_top_level_array(self):
        data = [{"name": "WBC", "value": "8.5", "unit": "10^9/L", "reference": "4-10"}]
        result = normalize_lab_results(data)
        assert "tests" in result
        assert len(result["tests"]) == 1

    def test_items_key(self):
        data = {"items": [{"name": "GLU", "value": "5.5", "unit": "mmol/L", "reference": "3.9-6.1"}]}
        result = normalize_lab_results(data)
        assert "tests" in result


class TestNormalizeDoctorOrders:
    def test_correct_format_passthrough(self):
        data = {
            "medications": [{
                "name": "阿莫西林",
                "dosage": "500mg",
                "frequency": "每日3次",
                "duration": "7天",
                "notes": "饭后"
            }],
            "lifestyle": ["多喝水"],
            "followup": "一周后复诊",
            "special_instructions": "未提及"
        }
        result = normalize_doctor_orders(data)
        assert result["medications"][0]["name"] == "阿莫西林"

    def test_missing_keys_filled(self):
        data = {"medications": []}
        result = normalize_doctor_orders(data)
        assert result["lifestyle"] == []
        assert result["followup"] == "未提及"
        assert result["special_instructions"] == "未提及"

    def test_error_passthrough(self):
        data = {"error": "parse failed"}
        assert normalize_doctor_orders(data) == data


class TestNormalizeStructuredData:
    def test_correct_format_passthrough(self):
        data = {"diagnosis": ["糖尿病"], "symptoms": ["多饮"], "treatment": "口服降糖药", "followup": "3个月"}
        result = normalize_structured_data(data)
        assert result["diagnosis"] == ["糖尿病"]

    def test_missing_keys_filled(self):
        data = {}
        result = normalize_structured_data(data)
        assert result["diagnosis"] == []
        assert result["treatment"] == "未提及"

    def test_error_passthrough(self):
        data = {"error": "failed"}
        assert normalize_structured_data(data) == data
