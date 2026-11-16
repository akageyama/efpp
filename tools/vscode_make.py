#!/usr/bin/env python3
"""Run a build and mirror gfortran diagnostics onto corresponding .ef files.

Original build output is retained. Additional one-line diagnostics are emitted
only when the .ef counterpart of a generated .F90 file exists.
Intended for the VS Code task problem matcher shown in examples/vscode/tasks.json.
"""

import re
import subprocess
import sys
from pathlib import Path

# Standard free-form gfortran diagnostic location and subsequent severity line.
LOCATION = re.compile(r"^(?P<file>.+\.F90):(?P<line>\d+):(?P<column>\d+):\s*$", re.I)
MESSAGE = re.compile(r"^(?P<severity>Fatal Error|Error|Warning):\s*(?P<message>.+)$", re.I)


def main(argv=None):
    command = list(sys.argv[1:] if argv is None else argv) or ["make"]
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            bufsize=1,
        )
    except OSError as exc:
        print(f"vscode_make: {exc}", file=sys.stderr)
        return 1

    location = None
    age = 0
    assert process.stdout is not None
    for line in process.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        match = LOCATION.match(line.rstrip("\r\n"))
        if match:
            generated = Path(match.group("file"))
            source = generated.with_suffix(".ef")
            location = (source, match.group("line"), match.group("column")) if source.is_file() else None
            age = 0
            continue
        if location:
            age += 1
            msg = MESSAGE.match(line.strip())
            if msg:
                severity = "warning" if msg.group("severity").lower() == "warning" else "error"
                file, number, column = location
                print(f"{file}:{number}:{column}: {severity}: {msg.group('message')}", flush=True)
                location = None
            elif age > 10:
                location = None

    return process.wait()


if __name__ == "__main__":
    sys.exit(main())
