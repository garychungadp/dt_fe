import json
import sys
import html
import os

def sarif_to_html(sarif_path, output_path):
    if not os.path.exists(sarif_path):
        print(f"File not found: {sarif_path}")
        return

    with open(sarif_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    runs = data.get('runs', [])
    results_list = []

    for run in runs:
        tool_name = run.get('tool', {}).get('driver', {}).get('name', 'Scanner')
        rules_by_id = {r.get('id'): r for r in run.get('tool', {}).get('driver', {}).get('rules', [])}
        rules_list = run.get('tool', {}).get('driver', {}).get('rules', [])

        for res in run.get('results', []):
            rule_id = res.get('ruleId')
            rule_index = res.get('ruleIndex')
            rule_info = {}
            if rule_id and rule_id in rules_by_id:
                rule_info = rules_by_id[rule_id]
            elif rule_index is not None and isinstance(rule_index, int) and 0 <= rule_index < len(rules_list):
                rule_info = rules_list[rule_index]
                rule_id = rule_info.get('id', 'N/A')
            elif not rule_id:
                rule_id = 'N/A'

            msg = res.get('message', {}).get('text', '')
            level = res.get('level') or rule_info.get('defaultConfiguration', {}).get('level') or 'warning'
            
            locations = res.get('locations', [])
            loc_str = 'N/A'
            if locations:
                phys = locations[0].get('physicalLocation', {})
                uri = phys.get('artifactLocation', {}).get('uri', '')
                line = phys.get('region', {}).get('startLine', '?')
                loc_str = f"{uri}:{line}"

            results_list.append({
                'tool': tool_name,
                'rule_id': rule_id,
                'name': rule_info.get('name', rule_id),
                'level': level,
                'message': msg,
                'location': loc_str,
                'description': rule_info.get('help', {}).get('text', rule_info.get('shortDescription', {}).get('text', ''))
            })

    total = len(results_list)
    errors = sum(1 for r in results_list if r['level'] == 'error')
    warnings = sum(1 for r in results_list if r['level'] == 'warning')
    notes = sum(1 for r in results_list if r['level'] == 'note')

    rows = ""
    for r in results_list:
        badge_class = "danger" if r['level'] == 'error' else ("warning" if r['level'] == 'warning' else "info")
        rows += f"""
        <tr>
            <td><span class="badge {badge_class}">{html.escape(r['level'].upper())}</span></td>
            <td><b>{html.escape(r['rule_id'])}</b><br><small>{html.escape(r['name'])}</small></td>
            <td><code>{html.escape(r['location'])}</code></td>
            <td>{html.escape(r['message'])}</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>{html.escape(tool_name)} 安全掃描報告</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 30px; background-color: #f6f8fa; color: #24292f; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); }}
        h1 {{ margin-top: 0; border-bottom: 2px solid #eaecef; padding-bottom: 12px; font-size: 24px; }}
        .summary {{ display: flex; gap: 20px; margin-bottom: 25px; }}
        .card {{ flex: 1; padding: 15px 20px; border-radius: 6px; background: #f6f8fa; border: 1px solid #d0d7de; text-align: center; }}
        .card .num {{ font-size: 28px; font-weight: bold; margin-top: 5px; }}
        .card.danger .num {{ color: #cf222e; }}
        .card.warning .num {{ color: #9a6700; }}
        .card.info .num {{ color: #0969da; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px 14px; text-align: left; border-bottom: 1px solid #d0d7de; }}
        th {{ background-color: #f6f8fa; }}
        .badge {{ padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; color: white; display: inline-block; }}
        .badge.danger {{ background-color: #cf222e; }}
        .badge.warning {{ background-color: #bf8700; }}
        .badge.info {{ background-color: #0969da; }}
        code {{ background: #f6f8fa; padding: 2px 6px; border-radius: 4px; font-size: 13px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ {html.escape(tool_name)} 安全掃描報告</h1>
        <div class="summary">
            <div class="card"><div class="label">總風險數</div><div class="num">{total}</div></div>
            <div class="card danger"><div class="label">高風險 (Error)</div><div class="num">{errors}</div></div>
            <div class="card warning"><div class="label">中風險 (Warning)</div><div class="num">{warnings}</div></div>
            <div class="card info"><div class="label">低風險 (Note)</div><div class="num">{notes}</div></div>
        </div>
        <table>
            <thead>
                <tr>
                    <th style="width: 100px;">嚴重等級</th>
                    <th style="width: 250px;">規則代碼 / 弱點類型</th>
                    <th style="width: 250px;">檔案位置</th>
                    <th>詳細說明</th>
                </tr>
            </thead>
            <tbody>
                {rows if rows else '<tr><td colspan="4" style="text-align:center; padding: 30px; color: #57609a;">🎉 太棒了！未發現任何安全弱點。</td></tr>'}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Report generated successfully: {output_path} (Total findings: {total}, Errors: {errors}, Warnings: {warnings})")

if __name__ == '__main__':
    sarif_file = sys.argv[1] if len(sys.argv) > 1 else 'results.sarif'
    out_file = sys.argv[2] if len(sys.argv) > 2 else 'reports/security-report.html'
    sarif_to_html(sarif_file, out_file)
