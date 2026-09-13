"""v1.0.2 | 2026-09-13 | 运行全部或指定案例，失败会返回非零退出码。"""

from pathlib import Path
import sys, subprocess, json, time

root = Path(__file__).parent
results = []
selected = {int(x) for x in sys.argv[1:]}
for script in sorted((root / "cases").glob("case_*.py")):
    n = int(script.name.split("_")[1])
    if selected and n not in selected:
        continue
    start = time.time()
    try:
        p = subprocess.run(
            [sys.executable, "-X", "utf8", str(script)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=180,
        )
        result = {
            "case": n,
            "exit_code": p.returncode,
            "seconds": round(time.time() - start, 2),
            "stdout": p.stdout,
            "stderr": p.stderr,
        }
    except subprocess.TimeoutExpired:
        result = {
            "case": n,
            "exit_code": 124,
            "seconds": 180,
            "stdout": "",
            "stderr": "timeout",
        }
    results.append(result)
    print(
        f"{n:02d}: {'PASS' if result['exit_code']==0 else 'FAIL'} {result['seconds']}s",
        flush=True,
    )
    if result["exit_code"] or result["stderr"]:
        print(result["stderr"][:1500], flush=True)
report = root / (
    "运行检查_v1.0.2.json"
    if not selected
    else "定向运行检查_v1.0.2.json"
)
report.write_text(
    json.dumps(results, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
sys.exit(int(any(r["exit_code"] for r in results)))
