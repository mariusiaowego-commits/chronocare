#!/usr/bin/env python3
"""tjh 病例汇总分析:医生分布、诊断一致性、病情变化"""
import sqlite3, re, json
from collections import defaultdict, Counter
from datetime import date

conn = sqlite3.connect('data/chronocare.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

# 工具函数(提前定义)
def parse_diagnosis(diag_str):
    if not diag_str: return []
    diag_str = diag_str.replace('西医诊断:','').replace('中医诊断:','').strip()
    parts = re.split(r'\d+\.', diag_str)
    return [p.strip() for p in parts if p.strip() and p.strip() != '西医诊断：']

def normalize_diag(s):
    s = s.strip()
    if '失眠' in s or '睡眠' in s: return '失眠'
    return s

# ========== 1. 重新提取每个 PDF 的医生签名 ==========
def extract_doctor(text, known_doctors=None):
    """严格规则: 医生签名 = 页码 '1/N' 之前一行(2-3 字姓名)
    known_doctors: 已确认的医生集合,优先从中匹配(避免 OCR 噪声)"""
    if not text: return None
    parts = re.split(r'\b\d+/\d+\b', text)
    sig_page = None
    for p in parts:
        if p.strip(): sig_page = p; break
    if not sig_page: return None
    after_xz = re.split(r'随访[,，]', sig_page)
    candidate_text = after_xz[-1] if len(after_xz) > 1 else sig_page
    blacklist = {'随访','复查','继续','治疗','方案','定期','相关','指标','如有','不适','及时','就诊',
                 '完善','疾病','药物','宣教','密切','注意','休息','保暖','规律','作息','饮食','避免',
                 '劳累','情绪','激动','建议','心外','高血压','心房','颤动','二尖','关闭','不全',
                 '慢性','失眠','眼痒','病人','主诉','病史','体格','检查','诊断','处理','科室','医院',
                 '上海市','医学中心','门诊','处方','检验','动态','观察','全程','基础','心动','次数',
                 '心室','平均','单个','未见','缺血','型','左眼','结膜','炎','结石','造影','出凝血',
                 '一般可','壁增厚','临检','带药','静注','速尿','每日','每晚','每次','华法令','侧位',
                 '陶建华','上海市','医学','中心','反流','脱垂','中重度','增大','室壁','增厚','室早',
                 '心动过速','心动过缓','心律','绝对','不齐','律不齐','律齐','口服','滴眼','测定',
                 '出凝','随访','完善','密切','避免','规律','饮食','呼出气','支气管','哮喘','顺尔宁','爬楼梯',
                 '胸闷','气促','动脉','瓣','脱垂','反流','测定','测出','黄绿','绿','吸入','气雾','喷雾',
                 '信必可','都保','粉吸入','替卡松','沙美特罗','沙丁胺醇','异丙托','溴铵',
                 '希刻劳','头孢','克洛','分散片','颗粒','阿莫','西林','克拉','维酸',
                 '胸膜炎','胸膜','肺炎','慢支','肺心病','肺气肿','老慢支','五分法','分法'}
    cands = re.findall(r'(?<![\u4e00-\u9fff])([\u4e00-\u9fff]{2,3})(?![\u4e00-\u9fff])', candidate_text)
    # 优先匹配已知医生
    if known_doctors:
        for x in reversed(cands):
            if x in known_doctors: return x
    # 否则用黑名单过滤
    for x in reversed(cands):
        if x in blacklist: continue
        if re.search(r'科|院|部|室|门|诊|病|医|师|士|生|号|路|区', x): continue
        return x
    return None

# 拉 visits + medical_records
c.execute("""SELECT id, visit_date, hospital, department, doctor,
                    chief_complaint, diagnosis, prescription
             FROM visits WHERE person_id=2 ORDER BY visit_date""")
visits = [dict(r) for r in c.fetchall()]

c.execute("""SELECT id, visit_date, hospital, department, doctor,
                    ocr_text, structured_data
             FROM medical_records WHERE person_id=2 ORDER BY visit_date""")
mrs = [dict(r) for r in c.fetchall()]

# 用 (visit_date, hospital) 把 visits 与 medical_records 配对
mr_by_key = defaultdict(list)
for m in mrs:
    if m['visit_date']:
        mr_by_key[(m['visit_date'], m['hospital'])].append(m)

print("="*80)
print("【数据规模】")
print(f"  visits: {len(visits)} | medical_records: {len(mrs)}")
print(f"  时间跨度: {visits[0]['visit_date']} -> {visits[-1]['visit_date']}")
print()

# ========== 2. 医生频次统计 ==========
print("="*80)
print("【问题 1: 看哪个医生更多?】")

# 两轮策略: 第一轮无已知列表(高置信 = 黑名单过滤后保留)
# 第二轮把高置信医生作为 known_doctors 再过一遍(召回)
ROUND1 = []
for v in visits:
    key = (v['visit_date'], v['hospital'])
    mlist = mr_by_key.get(key, [])
    for m in mlist:
        d = extract_doctor(m.get('ocr_text'))
        ROUND1.append((v['visit_date'], v['hospital'], m.get('department'), v['diagnosis'], d))

# 高置信: count >= 2 视为医生
high_conf = Counter([d for _,_,_,_,d in ROUND1 if d])
known_doctors = set()
for name, cnt in high_conf.most_common():
    if cnt >= 2: known_doctors.add(name)
# 单次出现的候选医生(可能真名也可能 OCR 噪声)
single_hits = [n for n,c in high_conf.most_common() if c == 1]
print(f"高频医生(>=2 次): {sorted(known_doctors)}")
print(f"单次出现(可能是医生或 OCR 噪声): {single_hits}")
print()

# 第二轮: 用 known_doctors 重跑
# 按 PDF 统计(不是 visit)—— 因为同一天可能有 2 个 PDF = 2 个医生
doctor_counter = Counter()  # 医生 -> 含其签名的 PDF 数
doctor_patients = defaultdict(set)  # 医生 -> 出现的 visit_date 集合
doctor_diagnoses = defaultdict(set)  # 医生 -> 诊断集合(归一化)
no_doctor_pdfs = 0
for v in visits:
    key = (v['visit_date'], v['hospital'])
    mlist = mr_by_key.get(key, [])
    # 取这个 visit 所有 PDF,识别医生
    docs_this_visit = []
    for m in mlist:
        d = extract_doctor(m.get('ocr_text'), known_doctors=known_doctors)
        if d:
            docs_this_visit.append(d)
            doctor_counter[d] += 1
            for x in parse_diagnosis(v['diagnosis']):
                doctor_diagnoses[d].add(normalize_diag(x))
        else:
            no_doctor_pdfs += 1
    for d in docs_this_visit:
        doctor_patients[d].add(v['visit_date'])

print("【最终结果】按 PDF 签名统计:")
for d, cnt in doctor_counter.most_common():
    days = len(doctor_patients[d])
    print(f"  {d}: {cnt} 张 PDF(覆盖 {days} 个就诊日)")
print(f"\n无法识别医生的 PDF: {no_doctor_pdfs} 张")
print(f"原因: 2025-04 后 PDF OCR 文本不再包含签名(可能换模板/电子签章为图片)")
print()

# 各医生负责的就诊日明细
print("=== 各医生出诊时间表 ===")
for d in sorted(doctor_counter.keys(), key=lambda x: -doctor_counter[x]):
    dates = sorted(doctor_patients[d])
    print(f"\n【{d}】({len(dates)} 次)")
    for dt in dates:
        print(f"  {dt}")
print()

# ========== 3. 各医生诊断一致性 ==========
print("="*80)
print("【问题 2: 不同医生诊断是否一致?】")

# 全集
all_diags = set()
for v in visits:
    for d in parse_diagnosis(v['diagnosis']):
        all_diags.add(normalize_diag(d))
print(f"全部诊断种类({len(all_diags)}):")
for d in sorted(all_diags): print(f"  - {d}")
print()

# 按医生 → 诊断
print("按医生 → 诊断(2024-03 ~ 2025-02):")
print(f"{'医生':6} {'PDF':4} {'天数':4} 诊断集合")
print('-'*80)
all_doc_diags_norm = {}
for d in sorted(doctor_diagnoses.keys()):
    diags = doctor_diagnoses[d]
    all_doc_diags_norm[d] = diags
    print(f"{d:6} {doctor_counter[d]:4} {len(doctor_patients[d]):4} {sorted(diags)}")

print()
print("=== 一致点(所有医生都提的诊断) ===")
common = set.intersection(*all_doc_diags_norm.values()) if all_doc_diags_norm else set()
print(f"  {sorted(common) if common else '(无)'}")
print()

print("=== 各医生差异点 ===")
for d, diags in all_doc_diags_norm.items():
    others = set.union(*[s for k,s in all_doc_diags_norm.items() if k!=d]) if len(all_doc_diags_norm)>1 else set()
    only_this = diags - others
    only_others = others - diags
    print(f"  {d}:")
    print(f"    仅该医生提: {sorted(only_this) if only_this else '(无)'}")
    if only_others:
        print(f"    其他医生提、本医生未提: {sorted(only_others)}")
    print()

# ========== 4. 病情变化时间轴 ==========
print("="*80)
print("【问题 3: 病情变化情况】")
print()

# 按阶段分组
phases = [
    ("2024-03-13", "2024-03-27", "初诊期(胸闷)", "反复胸闷1年 → 心超/动态心电图确诊:心房颤动 + 二尖瓣脱垂中重度反流 + 双房左室增大;心外科建议"),
    ("2024-04-18", "2024-10-15", "调整期(心内科随访)", "开始诺欣妥 + 络活喜降压 + 思诺思助眠;华法林维持"),
    ("2024-11-19", "2025-03-17", "稳定期", "四联方案固定:诺欣妥+络活喜+思诺思+华法林;建议心外科手术评估"),
    ("2025-03-17", "2025-06-19", "检查期", "完成冠脉CT、心超复查;INR 偏低调整华法林1.5#qd"),
    ("2025-06-19", "2026-03-04", "长程维持期", "INR 持续监测,华法林剂量调整;睡眠药延长(2盒→4盒/月)"),
    ("2026-05-09", "2026-05-27", "再次建议手术", "建议心外科手术;INR 稳定"),
]

for s, e, title, summary in phases:
    in_phase = [v for v in visits if s <= v['visit_date'] <= e]
    diags_in = set()
    for v in in_phase:
        for x in parse_diagnosis(v['diagnosis']): diags_in.add(x)
    print(f"【{s} ~ {e}】 {title}({len(in_phase)} 次)")
    print(f"  诊断: {sorted(diags_in) if diags_in else '(无)'}")
    print(f"  概要: {summary}")
    print()

# 关键指标变化(从 OCR 抽)
print("=== 关键指标(从 OCR 抽取的 INR/心超) ===")
c.execute("""SELECT visit_date, ocr_text FROM medical_records
             WHERE person_id=2 AND ocr_text LIKE '%国际标准化比值%'
             ORDER BY visit_date""")
inr_records = c.fetchall()
for d, t in inr_records:
    m = re.search(r'国际标准化比值[:：]\s*([\d.]+)', t)
    if m: print(f"  {d}: INR = {m.group(1)}")
print()

print("=== 心超关键发现 ===")
c.execute("""SELECT visit_date, ocr_text FROM medical_records
             WHERE person_id=2 AND (ocr_text LIKE '%二尖瓣%' OR ocr_text LIKE '%左室%' OR ocr_text LIKE '%射血%')
             ORDER BY visit_date""")
for d, t in c.fetchall():
    # 提取关键短句
    for kw in ['二尖瓣','左室','射血','左房','EF']:
        m = re.search(rf'{kw}[^。\n]{{0,40}}[。\n]', t)
        if m:
            print(f"  {d} [{kw}]: {m.group(0).strip()[:80]}")
            break