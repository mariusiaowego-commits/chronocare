import json
from chronocare.services.medical_record import normalize_lab_results

# Extract the raw lab results from the vision_analyze response
raw_results = {
  "tests": [
    {"name": "颜色", "value": "黄色", "unit": "", "reference": "", "status": "normal"},
    {"name": "透明度", "value": "清", "unit": "", "reference": "", "status": "normal"},
    {"name": "比重", "value": "1.010", "unit": "", "reference": "1.003--1.030", "status": "normal"},
    {"name": "亚硝酸盐", "value": "阴性", "unit": "", "reference": "阴性", "status": "normal"},
    {"name": "pH", "value": "7.50", "unit": "", "reference": "5--8", "status": "normal"},
    {"name": "蛋白", "value": "阴性", "unit": "", "reference": "阴性", "status": "normal"},
    {"name": "葡萄糖", "value": "阴性", "unit": "", "reference": "0--0", "status": "normal"},
    {"name": "酮体", "value": "阴性", "unit": "", "reference": "阴性", "status": "normal"},
    {"name": "尿胆原", "value": "正常", "unit": "", "reference": "正常", "status": "normal"},
    {"name": "胆红素", "value": "阴性", "unit": "", "reference": "阴性", "status": "normal"},
    {"name": "尿隐血", "value": "阴性", "unit": "", "reference": "阴性", "status": "normal"},
    {"name": "白细胞酯酶", "value": "+", "unit": "", "reference": "阴性", "status": "high"},
    {"name": "红细胞计数", "value": "7", "unit": "/uL", "reference": "0--25", "status": "normal"},
    {"name": "白细胞计数", "value": "88", "unit": "/uL", "reference": "0--25", "status": "high"},
    {"name": "上皮细胞计数", "value": "10", "unit": "/uL", "reference": "2--10", "status": "normal"},
    {"name": "细菌计数", "value": "11.0", "unit": "/uL", "reference": "0--5000", "status": "normal"},
    {"name": "病理性管型", "value": "阴性", "unit": "", "reference": "阴性", "status": "normal"},
    {"name": "小圆上皮细胞", "value": "8.2", "unit": "", "reference": "0--1", "status": "high"},
    {"name": "酵母菌", "value": "阴性", "unit": "", "reference": "阴性", "status": "normal"},
    {"name": "结晶检查", "value": "阴性", "unit": "", "reference": "阴性", "status": "normal"},
    {"name": "红细胞信息", "value": "阴性", "unit": "", "reference": "阴性", "status": "normal"},
    {"name": "电导率", "value": "9.8", "unit": "mS/cm", "reference": "4--38", "status": "normal"}
  ]
}

# Run normalization
normalized = normalize_lab_results(raw_results)

print("=== 原始数据 ===")
print(f"测试项目数: {len(raw_results['tests'])}")
print("\n=== 规范化后数据 ===")
print(json.dumps(normalized, indent=2, ensure_ascii=False))

# Verify normalization
abnormal_count = sum(1 for t in normalized['tests'] if t['status'] != 'normal')
print(f"\n=== 验证结果 ===")
print(f"异常指标数: {abnormal_count}")
print("Status 均已规范化为模板识别的值: {}".format(
    all(t['status'] in ['normal', 'high', 'low', 'slightly_high', 'slightly_low'] for t in normalized['tests'])
))
