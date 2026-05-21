#!/usr/bin/env python3
"""
合规审查 HTML 报告生成工具

将审查结果 JSON 转为可视化 HTML 报告

用法：
  python generate_report.py <审查结果.json> [--output report.html]
  echo '{"results":[...]}' | python generate_report.py --stdin [--output report.html]

输入格式（JSON）：
  {
    "results": [
      {
        "content_index": 1,
        "content_summary": "内容摘要",
        "source_file": "来源文件名（可选）",
        "is_compliant": true/false,
        "risk_level": "none|low|medium|high",
        "violations": [
          {
            "rule": "违反规则名称",
            "evidence": "原文证据",
            "description": "违规说明",
            "severity": "low|medium|high",
            "suggestion": "修改建议"
          }
        ]
      }
    ]
  }
"""

import sys
import os
import json
from datetime import datetime


def escape_html(s):
    if not s:
        return ''
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace('\n', '<br>')


def generate_html(report_data, meta=None):
    """生成 HTML 报告"""
    meta = meta or {}
    results = report_data.get('results', [])

    # 统计
    total = len(results)
    compliant = sum(1 for r in results if r.get('is_compliant') is True)
    non_compliant = sum(1 for r in results if r.get('is_compliant') is False)
    failed = sum(1 for r in results if r.get('is_compliant') is None)
    total_violations = sum(len(r.get('violations', [])) for r in results)

    risk_levels = {'none': 0, 'low': 0, 'medium': 0, 'high': 0, 'unknown': 0}
    rule_violations = {}
    for r in results:
        rl = r.get('risk_level', 'unknown')
        risk_levels[rl] = risk_levels.get(rl, 0) + 1
        for v in r.get('violations', []):
            rule = v.get('rule', '其他')
            rule_violations[rule] = rule_violations.get(rule, 0) + 1

    report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    source_label = meta.get('source', '')

    risk_labels = {'none': '无风险', 'low': '低风险', 'medium': '中风险', 'high': '高风险', 'unknown': '未知'}
    severity_labels = {'low': '低', 'medium': '中', 'high': '高'}

    violations_list = [r for r in results if r.get('is_compliant') is False]
    compliant_list = [r for r in results if r.get('is_compliant') is True]

    # 按文件分组
    file_groups = {}
    for r in violations_list:
        src = r.get('source_file', '未知来源')
        file_groups.setdefault(src, []).append(r)

    # 违规规则排序
    rule_entries = sorted(rule_violations.items(), key=lambda x: -x[1])

    # 构建 HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>医药合规审查报告</title>
<style>
:root{{--bg:#0f172a;--bg-card:#1e293b;--text:#e2e8f0;--text-muted:#94a3b8;--border:#334155;--primary:#3b82f6;--success:#10b981;--danger:#ef4444;--warning:#f97316;--radius:12px}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;background:var(--bg);color:var(--text);line-height:1.6;min-height:100vh}}
.container{{max-width:1280px;margin:0 auto;padding:32px 24px}}
.header{{text-align:center;padding:48px 24px;border-bottom:1px solid var(--border)}}
.header h1{{font-size:28px;background:linear-gradient(135deg,#e2e8f0,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.header .sub{{color:var(--text-muted);font-size:14px;margin-top:8px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin:32px 0}}
.stat{{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:24px;text-align:center}}
.stat .val{{font-size:36px;font-weight:700}}.stat .lbl{{font-size:13px;color:var(--text-muted);margin-top:4px}}
.stat.total .val{{color:var(--primary)}}.stat.pass .val{{color:var(--success)}}.stat.fail .val{{color:var(--danger)}}.stat.warn .val{{color:var(--warning)}}
.bar-wrap{{margin:24px 0}}.bar-wrap h4{{font-size:14px;color:var(--text-muted);margin-bottom:10px}}
.bar{{height:32px;border-radius:16px;overflow:hidden;display:flex;background:var(--bg-card);border:1px solid var(--border)}}
.bar .seg{{height:100%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;color:#fff}}
.bar .seg-pass{{background:linear-gradient(90deg,#059669,#10b981)}}.bar .seg-fail{{background:linear-gradient(90deg,#dc2626,#ef4444)}}
.section{{margin:40px 0}}
.section-title{{font-size:20px;font-weight:700;margin-bottom:20px;padding-bottom:12px;border-bottom:2px solid var(--border);display:flex;align-items:center;gap:10px}}
.section-title .count{{font-size:14px;color:var(--text-muted);font-weight:400;margin-left:auto}}
.file-group{{margin:24px 0}}.file-group h3{{font-size:16px;color:var(--primary);margin-bottom:12px;padding:8px 12px;background:rgba(59,130,246,0.1);border-radius:8px}}
.card{{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);margin-bottom:16px;overflow:hidden}}
.card.risk-high{{border-left:4px solid var(--danger)}}.card.risk-medium{{border-left:4px solid var(--warning)}}.card.risk-low{{border-left:4px solid #f59e0b}}
.card-head{{display:flex;justify-content:space-between;align-items:center;padding:16px 20px}}
.card-head h4{{font-size:15px;font-weight:600}}
.badge{{font-size:12px;font-weight:600;padding:4px 12px;border-radius:20px}}
.badge-high{{background:rgba(239,68,68,0.1);color:var(--danger)}}.badge-medium{{background:rgba(249,115,22,0.1);color:var(--warning)}}.badge-low{{background:rgba(245,158,11,0.1);color:#f59e0b}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:rgba(51,65,85,0.5);padding:10px 12px;text-align:left;font-weight:600;color:var(--text-muted)}}
td{{padding:10px 12px;border-top:1px solid var(--border);vertical-align:top}}
tr:hover td{{background:rgba(51,65,85,0.3)}}
.evidence{{color:#fbbf24;font-style:italic}}
.rule-tag{{background:rgba(124,58,237,0.15);color:#a78bfa;padding:2px 8px;border-radius:6px;font-size:12px}}
.sev{{padding:2px 10px;border-radius:10px;font-size:11px;font-weight:600}}
.sev-high{{background:rgba(239,68,68,0.1);color:var(--danger)}}.sev-medium{{background:rgba(249,115,22,0.1);color:var(--warning)}}.sev-low{{background:rgba(245,158,11,0.1);color:#f59e0b}}
.comp-table{{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden}}
.chart-row{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:24px 0}}
.chart-card{{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:24px}}
.chart-card h4{{font-size:14px;color:var(--text-muted);margin-bottom:16px}}
.bar-item{{display:flex;align-items:center;gap:12px;margin-bottom:12px}}
.bar-item .bar-label{{width:140px;font-size:13px;text-align:right;flex-shrink:0}}
.bar-item .bar-track{{flex:1;height:24px;background:var(--border);border-radius:12px;overflow:hidden}}
.bar-item .bar-fill{{height:100%;border-radius:12px;display:flex;align-items:center;padding:0 10px;font-size:12px;font-weight:600;color:#fff;min-width:32px}}
.fill-high{{background:linear-gradient(90deg,#dc2626,#ef4444)}}.fill-medium{{background:linear-gradient(90deg,#d97706,#f59e0b)}}
.fill-low{{background:linear-gradient(90deg,#2563eb,#3b82f6)}}.fill-none{{background:linear-gradient(90deg,#059669,#10b981)}}
.fill-rule{{background:linear-gradient(90deg,#7c3aed,#a78bfa)}}
.footer{{text-align:center;padding:32px;margin-top:48px;border-top:1px solid var(--border);color:var(--text-muted);font-size:13px}}
@media(max-width:768px){{.stats{{grid-template-columns:repeat(2,1fr)}}.chart-row{{grid-template-columns:1fr}}}}
@media print{{body{{background:#fff;color:#1a1a1a}}.header{{background:#f8fafc}}}}
</style>
</head>
<body>
<div class="header">
<h1>🏥 医药合规审查报告</h1>
<div class="sub">生成时间：{report_time}{f" | 来源：{escape_html(source_label)}" if source_label else ""}</div>
</div>
<div class="container">

<div class="stats">
<div class="stat total"><div class="val">{total}</div><div class="lbl">审查总数</div></div>
<div class="stat pass"><div class="val">{compliant}</div><div class="lbl">✅ 合规</div></div>
<div class="stat fail"><div class="val">{non_compliant}</div><div class="lbl">❌ 不合规</div></div>
<div class="stat warn"><div class="val">{total_violations}</div><div class="lbl">🚨 违规条目</div></div>
</div>

<div class="bar-wrap"><h4>合规率 {(compliant/total*100):.1f}%</h4>
<div class="bar">
<div class="seg seg-pass" style="width:{compliant/total*100:.1f}%">{f"合规 {compliant}" if compliant else ""}</div>
<div class="seg seg-fail" style="width:{non_compliant/total*100:.1f}%">{f"违规 {non_compliant}" if non_compliant else ""}</div>
</div></div>
'''

    # 图表行
    html += '<div class="chart-row"><div class="chart-card"><h4>风险等级分布</h4>'
    fill_map = {'high': 'fill-high', 'medium': 'fill-medium', 'low': 'fill-low', 'none': 'fill-none', 'unknown': 'fill-low'}
    for level, count in risk_levels.items():
        if count > 0:
            pct = max(count / total * 100, 5)
            html += f'<div class="bar-item"><span class="bar-label">{risk_labels.get(level, level)}</span><div class="bar-track"><div class="bar-fill {fill_map.get(level, "fill-low")}" style="width:{pct:.1f}%">{count}</div></div></div>'
    html += '</div><div class="chart-card"><h4>违规规则分布</h4>'
    if rule_entries:
        for rule, count in rule_entries[:8]:
            pct = max(count / max(total_violations, 1) * 100, 8)
            html += f'<div class="bar-item"><span class="bar-label">{escape_html(rule)}</span><div class="bar-track"><div class="bar-fill fill-rule" style="width:{pct:.1f}%">{count}</div></div></div>'
    else:
        html += '<p style="color:var(--text-muted)">无违规记录</p>'
    html += '</div></div>'

    # 不合规详情
    if violations_list:
        html += f'<div class="section"><div class="section-title">⚠️ 不合规内容详情<span class="count">{len(violations_list)} 项</span></div>'

        if len(file_groups) > 1:
            # 按文件分组显示
            for src_file, items in file_groups.items():
                html += f'<div class="file-group"><h3>📄 {escape_html(src_file)} ({len(items)}项违规)</h3>'
                for v in items:
                    html += _render_violation_card(v, risk_labels, severity_labels)
                html += '</div>'
        else:
            for v in violations_list:
                html += _render_violation_card(v, risk_labels, severity_labels)

        html += '</div>'

    # 合规列表
    if compliant_list:
        html += f'<div class="section"><div class="section-title">✅ 合规内容<span class="count">{len(compliant_list)} 项</span></div>'
        html += '<table class="comp-table"><thead><tr><th>序号</th><th>内容</th><th>来源</th></tr></thead><tbody>'
        for r in compliant_list:
            html += f'<tr><td>{r.get("content_index", "")}</td><td>{escape_html(r.get("content_summary", ""))}</td><td>{escape_html(r.get("source_file", ""))}</td></tr>'
        html += '</tbody></table></div>'

    html += '</div><div class="footer">医药合规审查报告 | 审查标准：医药代表合规逻辑模型 + 黑名单关键词</div></body></html>'

    return html


def _render_violation_card(v, risk_labels, severity_labels):
    rl = v.get('risk_level', 'unknown')
    title = v.get('content_summary', '') or v.get('_source_title', '') or f"内容 #{v.get('content_index', '')}"
    html = f'<div class="card risk-{rl}"><div class="card-head"><h4>#{v.get("content_index", "")} {escape_html(title)}</h4><span class="badge badge-{rl}">{risk_labels.get(rl, rl)}</span></div>'

    violations = v.get('violations', [])
    if violations:
        html += '<table><thead><tr><th>#</th><th>违反规则</th><th>严重性</th><th>违规证据</th><th>说明</th><th>修改建议</th></tr></thead><tbody>'
        for i, vio in enumerate(violations, 1):
            sev = vio.get('severity', 'medium')
            html += f'<tr><td>{i}</td><td><span class="rule-tag">{escape_html(vio.get("rule", ""))}</span></td><td><span class="sev sev-{sev}">{severity_labels.get(sev, "中")}</span></td><td class="evidence">{escape_html(vio.get("evidence", ""))}</td><td>{escape_html(vio.get("description", ""))}</td><td>{escape_html(vio.get("suggestion", ""))}</td></tr>'
        html += '</tbody></table>'

    html += '</div>'
    return html


def main():
    args = sys.argv[1:]
    input_path = None
    output_path = None
    use_stdin = False

    for i, arg in enumerate(args):
        if arg == '--output' and i + 1 < len(args):
            output_path = args[i + 1]
        elif arg == '--stdin':
            use_stdin = True
        elif not arg.startswith('--') and not input_path:
            input_path = arg

    # 读取输入
    if use_stdin:
        data = json.loads(sys.stdin.read())
    elif input_path:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        print('用法: python generate_report.py <审查结果.json> [--output report.html]')
        print('      echo \'{"results":[...]}\' | python generate_report.py --stdin')
        sys.exit(0)

    # 确定输出路径
    if not output_path:
        if input_path:
            output_path = os.path.splitext(input_path)[0] + '.html'
        else:
            output_path = f'compliance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'

    # 生成 HTML
    meta = {'source': data.get('source', '') or os.path.basename(input_path or '')}
    html = generate_html(data, meta)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'✅ HTML 报告已生成: {output_path}', file=sys.stderr)

    # 输出统计
    results = data.get('results', [])
    total = len(results)
    compliant = sum(1 for r in results if r.get('is_compliant') is True)
    non_compliant = sum(1 for r in results if r.get('is_compliant') is False)
    violations = sum(len(r.get('violations', [])) for r in results)
    print(f'   审查: {total} | 合规: {compliant} | 不合规: {non_compliant} | 违规条目: {violations}', file=sys.stderr)


if __name__ == '__main__':
    main()
