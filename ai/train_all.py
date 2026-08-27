import subprocess
import sys

commands = [
    [sys.executable, "simulator/generate_dataset.py"],
    [sys.executable, "simulator/generate_rul_dataset.py"],
    [sys.executable, "-m", "ai.train_anomaly"],
    [sys.executable, "-m", "ai.train_fault"],
    [sys.executable, "-m", "ai.train_rul"],
]

for command in commands:
    print("\n>", " ".join(command))
    subprocess.run(command, check=True)

print("\nAll synthetic MVP models trained. Restart backend or POST /models/reload.")
