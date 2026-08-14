import json, subprocess, os, sys

# Paths are derived, not hardcoded: this test is copied between repos and a stale
# absolute path makes it silently exercise another checkout's hook.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOOK = os.path.join(ROOT, ".claude", "hooks", "backlog-guard.py")
env = dict(os.environ, CLAUDE_PROJECT_DIR=ROOT)

# Assembled from fragments so this file's own text does not contain the literal
# flags the hook denies — otherwise the hook blocks the command that runs it.
N = "--" + "notes"
P = "--" + "plan"

cases = [
    ("bare notes flag",      {"tool_name": "Bash", "tool_input": {"command": f"backlog task edit fsg-0001 {N} hi"}}, 2),
    ("bare plan flag",       {"tool_name": "Bash", "tool_input": {"command": f"backlog task edit fsg-0001 {P} hi"}}, 2),
    ("equals form",          {"tool_name": "Bash", "tool_input": {"command": f"backlog task edit fsg-0001 {N}=hi"}}, 2),
    ("flag at end of line",  {"tool_name": "Bash", "tool_input": {"command": f"backlog task edit fsg-0001 {N}"}}, 2),
    ("append-notes allowed", {"tool_name": "Bash", "tool_input": {"command": "backlog task edit fsg-0001 --append-notes hi"}}, 0),
    ("append-plan allowed",  {"tool_name": "Bash", "tool_input": {"command": "backlog task edit fsg-0001 --append-plan hi"}}, 0),
    ("task list allowed",    {"tool_name": "Bash", "tool_input": {"command": "backlog task list --plain"}}, 0),
    ("doc update allowed",   {"tool_name": "Bash", "tool_input": {"command": "backlog doc update doc-0002 --content x"}}, 0),
    ("non-backlog cmd",      {"tool_name": "Bash", "tool_input": {"command": f"mytool {N} foo"}}, 0),
    ("edit task md",         {"tool_name": "Edit",  "tool_input": {"file_path": f"{ROOT}/backlog/tasks/fsg-0001 - x.md"}}, 2),
    ("write doc md",         {"tool_name": "Write", "tool_input": {"file_path": f"{ROOT}/backlog/docs/doc-0002 - y.md"}}, 2),
    ("edit completed md",    {"tool_name": "Edit",  "tool_input": {"file_path": f"{ROOT}/backlog/completed/fsg-0009 - z.md"}}, 2),
    ("config.yml allowed",   {"tool_name": "Edit",  "tool_input": {"file_path": f"{ROOT}/backlog/config.yml"}}, 0),
    ("source file allowed",  {"tool_name": "Edit",  "tool_input": {"file_path": f"{ROOT}/sagemcom_f3896_client/exporter.py"}}, 0),
    ("test file allowed",    {"tool_name": "Write", "tool_input": {"file_path": f"{ROOT}/tests/test_exporter.py"}}, 0),
    ("AGENTS.md allowed",    {"tool_name": "Write", "tool_input": {"file_path": f"{ROOT}/AGENTS.md"}}, 0),
]

fails = 0
for name, payload, want in cases:
    r = subprocess.run([sys.executable, HOOK], input=json.dumps(payload),
                       capture_output=True, text=True, env=env)
    ok = r.returncode == want
    fails += not ok
    print(f"{'PASS' if ok else 'FAIL'}  exit={r.returncode} want={want}  {name}")

# garbage stdin must never block
r = subprocess.run([sys.executable, HOOK], input="not json", capture_output=True, text=True, env=env)
ok = r.returncode == 0
fails += not ok
print(f"{'PASS' if ok else 'FAIL'}  exit={r.returncode} want=0  garbage stdin never blocks")

print(f"\n{len(cases)+1 - fails}/{len(cases)+1} passed")
sys.exit(1 if fails else 0)
