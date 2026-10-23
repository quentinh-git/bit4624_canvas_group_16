import pandas as pd

repo = "https://raw.githubusercontent.com/quentinh-git/bit4624_canvas_group_16/main/"

files = [
    "academic_calendar_flags.csv",
    "canvas_usage_summary.csv",
    "helpdesk_tickets_summary.csv",
    "service_status_checks.csv",
]

for i, f in enumerate(files, 1):
    print(i, f)

pick = int(input("Pick a file number: "))
df = pd.read_csv(repo + files[pick - 1])
print(df.head())
