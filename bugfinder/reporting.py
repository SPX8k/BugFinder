import csv
import html
import json
from pathlib import Path

def export_report(findings, output: Path, fmt: str):
    data = [f.to_dict() if hasattr(f, "to_dict") else f for f in findings]
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fmt = fmt.lower()
    if fmt == "json":
        output.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    elif fmt == "csv":
        fields = list(data[0]) if data else [
            "rule_id", "title", "severity", "confidence", "message",
            "recommendation", "file_path", "line", "column"
        ]
        with output.open("w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)
    elif fmt == "txt":
        blocks = []
        for x in data:
            blocks.append(
                f"[{x['severity'].upper()}] {x['title']} ({x['file_path']}:{x['line']})\n"
                f"Rule: {x['rule_id']} | Confidence: {x['confidence']}\n"
                f"{x['message']}\nRecommendation: {x['recommendation']}"
            )
        output.write_text("\n\n".join(blocks), encoding="utf-8")
    elif fmt == "html":
        blocks = []
        for x in data:
            blocks.append(
                "<article><h2>{}</h2><p><b>{}</b> · {} · {}:{}</p><p>{}</p>"
                "<p><b>Fix:</b> {}</p></article>".format(
                    html.escape(x["title"]), html.escape(x["severity"].upper()),
                    html.escape(x["rule_id"]), html.escape(x["file_path"]), x["line"],
                    html.escape(x["message"]), html.escape(x["recommendation"])
                )
            )
        output.write_text(
            "<!doctype html><html><meta charset='utf-8'><title>BugFinder report</title>"
            "<style>body{font:15px system-ui;max-width:1000px;margin:40px auto;"
            "background:#10151d;color:#e8edf5}article{padding:18px;margin:14px 0;"
            "background:#1a2431;border-radius:12px}h2{color:#7dd3fc}</style>"
            "<h1>BugFinder report</h1>" + "".join(blocks) + "</html>", encoding="utf-8"
        )
    elif fmt == "sarif":
        rules, results = {}, []
        for x in data:
            rules[x["rule_id"]] = {
                "id": x["rule_id"], "shortDescription": {"text": x["title"]}
            }
            results.append({
                "ruleId": x["rule_id"],
                "level": {"high": "error", "medium": "warning", "low": "note",
                          "info": "note"}.get(x["severity"], "warning"),
                "message": {"text": x["message"] + " " + x["recommendation"]},
                "locations": [{"physicalLocation": {
                    "artifactLocation": {"uri": x["file_path"].replace("\\", "/")},
                    "region": {"startLine": x["line"], "startColumn": x["column"]}
                }}]
            })
        payload = {
            "version": "2.1.0",
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "runs": [{"tool": {"driver": {"name": "BugFinder",
                                           "rules": list(rules.values())}},
                      "results": results}]
        }
        output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported report format: {fmt}")
    return output
