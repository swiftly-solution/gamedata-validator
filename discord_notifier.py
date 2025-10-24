import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def send_discord_webhook(title, description, fields=None, color=None, files=None):
    webhook_url = os.getenv('DISCORD_WEBHOOK')

    if not webhook_url:
        print("Warning: DISCORD_WEBHOOK environment variable not set")
        return

    if color is None:
        color = 5814783

    embed = {
        "title": title,
        "description": description,
        "color": color,
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {
            "text": "GameData Validator"
        }
    }

    if fields:
        embed["fields"] = fields

    payload = {
        "embeds": [embed]
    }

    try:
        if files:
            import json as json_lib
            files_to_upload = {}
            for i, file_info in enumerate(files):
                files_to_upload[f'file{i}'] = (
                    file_info['filename'],
                    file_info['content'],
                    'application/json'
                )

            response = requests.post(
                webhook_url,
                data={'payload_json': json_lib.dumps(payload)},
                files=files_to_upload
            )
        else:
            response = requests.post(webhook_url, json=payload)

        response.raise_for_status()
        print(f"Discord notification sent: {title}")
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")


def notify_vfunc_results(vfunc_results, signature):
    windows_results = {r['class_name']: r for r in vfunc_results.get('windows', [])}
    linux_results = {r['class_name']: r for r in vfunc_results.get('linux', [])}

    all_classes = set(windows_results.keys()) | set(linux_results.keys())

    total_classes = len(all_classes)
    windows_success = sum(1 for r in windows_results.values() if r.get('vfunc_count', 0) > 0)
    linux_success = sum(1 for r in linux_results.values() if r.get('vfunc_count', 0) > 0)

    fields = [
        {
            "name": "Build Signature",
            "value": signature,
            "inline": False
        },
        {
            "name": "Total VTables",
            "value": str(total_classes),
            "inline": True
        },
        {
            "name": "Windows Success",
            "value": str(windows_success),
            "inline": True
        },
        {
            "name": "Linux Success",
            "value": str(linux_success),
            "inline": True
        }
    ]

    binary_groups = {}
    for class_name in all_classes:
        win_result = windows_results.get(class_name)
        lin_result = linux_results.get(class_name)

        binary = (win_result or lin_result).get('binary', 'Unknown')

        if binary not in binary_groups:
            binary_groups[binary] = []

        win_count = win_result['vfunc_count'] if win_result else 0
        lin_count = lin_result['vfunc_count'] if lin_result else 0

        binary_groups[binary].append(
            f"`{class_name}` → Windows `[{win_count}]`, Linux `[{lin_count}]`"
        )

    for binary in sorted(binary_groups.keys()):
        vtables = binary_groups[binary]

        max_field_length = 1024
        current_field = []
        current_length = 0
        field_index = 0

        for vtable_line in vtables:
            line_length = len(vtable_line) + 1
            if current_length + line_length > max_field_length:
                field_name = binary if field_index == 0 else f"{binary} (cont.)"
                fields.append({
                    "name": field_name,
                    "value": "\n".join(current_field),
                    "inline": False
                })
                current_field = [vtable_line]
                current_length = line_length
                field_index += 1
            else:
                current_field.append(vtable_line)
                current_length += line_length

        if current_field:
            field_name = binary if field_index == 0 else f"{binary} (cont.)"
            fields.append({
                "name": field_name,
                "value": "\n".join(current_field),
                "inline": False
            })

    import json as json_lib
    files_to_upload = [
        {
            'filename': f'vfunc_counts_windows_{signature}.json',
            'content': json_lib.dumps(vfunc_results.get('windows', []), indent=4)
        },
        {
            'filename': f'vfunc_counts_linux_{signature}.json',
            'content': json_lib.dumps(vfunc_results.get('linux', []), indent=4)
        }
    ]

    send_discord_webhook(
        title="VFunc Offsets - Windows & Linux",
        description=f"Virtual function offset analysis completed for both platforms",
        fields=fields,
        color=3066993,
        files=files_to_upload
    )


def notify_pattern_scan_results(scan_results, signature):
    def get_circle(count):
        if count == 0:
            return "🔴"
        elif count == 1:
            return "🟢"
        else:
            return "🟡"

    windows_results = {r['signature']: r for r in scan_results.get('windows', [])}
    linux_results = {r['signature']: r for r in scan_results.get('linux', [])}

    all_signatures = set(windows_results.keys()) | set(linux_results.keys())

    total_signatures = len(all_signatures)
    windows_success = sum(1 for r in windows_results.values() if r.get('count', 0) > 0)
    linux_success = sum(1 for r in linux_results.values() if r.get('count', 0) > 0)
    windows_failed = len(windows_results) - windows_success
    linux_failed = len(linux_results) - linux_success

    fields = [
        {
            "name": "Build Signature",
            "value": signature,
            "inline": False
        },
        {
            "name": "Total Signatures",
            "value": str(total_signatures),
            "inline": True
        },
        {
            "name": "Windows Success/Failed",
            "value": f"{windows_success}/{windows_failed}",
            "inline": True
        },
        {
            "name": "Linux Success/Failed",
            "value": f"{linux_success}/{linux_failed}",
            "inline": True
        }
    ]

    results_lines = []
    for sig_name in sorted(all_signatures):
        win_result = windows_results.get(sig_name)
        lin_result = linux_results.get(sig_name)

        win_count = win_result['count'] if win_result else 0
        lin_count = lin_result['count'] if lin_result else 0

        win_circle = get_circle(win_count)
        lin_circle = get_circle(lin_count)

        results_lines.append(
            f"`{sig_name}` → Windows `[{win_count}]` {win_circle}, Linux `[{lin_count}]` {lin_circle}"
        )

    max_field_length = 1024
    current_field = []
    current_length = 0

    for line in results_lines:
        line_length = len(line) + 1
        if current_length + line_length > max_field_length:
            fields.append({
                "name": "Results" if len([f for f in fields if f['name'].startswith('Results')]) == 0 else "Results (cont.)",
                "value": "\n".join(current_field),
                "inline": False
            })
            current_field = [line]
            current_length = line_length
        else:
            current_field.append(line)
            current_length += line_length

    if current_field:
        fields.append({
            "name": "Results" if len([f for f in fields if f['name'].startswith('Results')]) == 0 else "Results (cont.)",
            "value": "\n".join(current_field),
            "inline": False
        })

    total_failed = windows_failed + linux_failed
    total_checks = len(windows_results) + len(linux_results)

    if total_failed == 0:
        color = 3066993
    elif total_failed < total_checks / 2:
        color = 16776960
    else:
        color = 15158332

    import json as json_lib
    files_to_upload = [
        {
            'filename': f'signatures_windows_{signature}.json',
            'content': json_lib.dumps(scan_results.get('windows', []), indent=4)
        },
        {
            'filename': f'signatures_linux_{signature}.json',
            'content': json_lib.dumps(scan_results.get('linux', []), indent=4)
        }
    ]

    send_discord_webhook(
        title="Pattern Scan Results - Windows & Linux",
        description=f"Pattern scanning completed for both platforms",
        fields=fields,
        color=color,
        files=files_to_upload
    )
