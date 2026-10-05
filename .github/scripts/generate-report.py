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

def license_to_html(json_path, output_path):
    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total = len(data)
    permissive_count = 0
    copyleft_count = 0
    other_count = 0

    rows = ""
    for pkg_name, info in sorted(data.items()):
        lic = info.get('licenses', 'Unknown')
        lic_str = ', '.join(lic) if isinstance(lic, list) else str(lic)

        lic_upper = lic_str.upper()
        if any(p in lic_upper for p in ['MIT', 'APACHE', 'BSD', 'ISC', '0BSD', 'UNLICENSE', 'CC0']):
            badge_class = "info"
            permissive_count += 1
        elif any(c in lic_upper for c in ['GPL', 'AGPL', 'LGPL', 'MPL', 'EPL']):
            badge_class = "warning"
            copyleft_count += 1
        else:
            badge_class = "secondary"
            other_count += 1

        repo = info.get('repository', '')
        repo_link = f'<a href="{html.escape(repo)}" target="_blank" rel="noopener noreferrer">{html.escape(repo)}</a>' if repo else '-'
        publisher = info.get('publisher', '-') or '-'

        rows += f"""
        <tr>
            <td><b>{html.escape(pkg_name)}</b></td>
            <td><span class="badge {badge_class}">{html.escape(lic_str)}</span></td>
            <td>{html.escape(str(publisher))}</td>
            <td style="word-break: break-all;">{repo_link}</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>📜 依賴套件授權報告</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 30px; background-color: #f6f8fa; color: #24292f; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); }}
        h1 {{ margin-top: 0; border-bottom: 2px solid #eaecef; padding-bottom: 12px; font-size: 24px; }}
        .summary {{ display: flex; gap: 20px; margin-bottom: 25px; }}
        .card {{ flex: 1; padding: 15px 20px; border-radius: 6px; background: #f6f8fa; border: 1px solid #d0d7de; text-align: center; }}
        .card .num {{ font-size: 28px; font-weight: bold; margin-top: 5px; }}
        .card.info .num {{ color: #0969da; }}
        .card.warning .num {{ color: #bf8700; }}
        .card.secondary .num {{ color: #57606a; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px 14px; text-align: left; border-bottom: 1px solid #d0d7de; }}
        th {{ background-color: #f6f8fa; }}
        .badge {{ padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; color: white; display: inline-block; }}
        .badge.info {{ background-color: #0969da; }}
        .badge.warning {{ background-color: #bf8700; }}
        .badge.secondary {{ background-color: #6e7781; }}
        a {{ color: #0969da; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📜 依賴套件授權報告 (Dependency License Report)</h1>
        <div class="summary">
            <div class="card"><div class="label">總套件數</div><div class="num">{total}</div></div>
            <div class="card info"><div class="label">寬鬆授權 (MIT/Apache/BSD)</div><div class="num">{permissive_count}</div></div>
            <div class="card warning"><div class="label">互惠/Copyleft (GPL/MPL)</div><div class="num">{copyleft_count}</div></div>
            <div class="card secondary"><div class="label">其他 / 未知</div><div class="num">{other_count}</div></div>
        </div>
        <table>
            <thead>
                <tr>
                    <th style="width: 320px;">套件名稱與版本</th>
                    <th style="width: 180px;">授權類型</th>
                    <th style="width: 200px;">發行者</th>
                    <th>原始碼庫 (Repository)</th>
                </tr>
            </thead>
            <tbody>
                {rows if rows else '<tr><td colspan="4" style="text-align:center; padding: 30px; color: #57609a;">無套件資訊</td></tr>'}
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
    print(f"License report generated successfully: {output_path} (Total packages: {total})")

if __name__ == '__main__':
    in_file = sys.argv[1] if len(sys.argv) > 1 else 'results.sarif'
    out_file = sys.argv[2] if len(sys.argv) > 2 else 'reports/security-report.html'

    if os.path.exists(in_file):
        try:
            with open(in_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict) and 'runs' in data:
                sarif_to_html(in_file, out_file)
            else:
                license_to_html(in_file, out_file)
        except Exception as e:
            sarif_to_html(in_file, out_file)
    else:
        sarif_to_html(in_file, out_file)
