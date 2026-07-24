#!/usr/bin/env python3
"""Demonstration: run a Validex audit on a sample table."""
from pathlib import Path
from validex.audit import audit_dataframe
import pandas as pd

demo_csv = Path(__file__).parent / "demo_standard_table.csv"
df = pd.read_csv(demo_csv)
result = audit_dataframe(df)

print(f"Detected fields: {result['detected']}")
print(f"Audit confidence: {result['audit_confidence']}")
print(f"Findings: {len(result['flags'])}")
for flag in result['flags']:
    print(f"  [{flag['severity']}] {flag['title']}")
