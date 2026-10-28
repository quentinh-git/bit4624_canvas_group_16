# ==========================================================================
# Canvas incident: timing, demand, and impact
# BIT 4624 group project
#
# WHAT THIS FILE DOES
#   1. Loads the CSV files in this folder.
#   2. Finds the incident window (the hours marked incident_flag = 1).
#   3. Makes four labeled charts and saves them into a "figures" folder.
#
# HOW TO RUN IT
#   - In a terminal:          python canvas_incident_charts.py
#   - In Jupyter or VS Code:  open this file. Each "# %%" line starts a new
#                             cell, so you can run one step at a time.
#
# Run it from the folder that holds the CSV files.
# Each chart pops up in its own window. Close a window to see the next one.
# ==========================================================================

# %%
# STEP 1: Import the tools we need
#   pandas              -> tables of data (called DataFrames)
#   matplotlib.pyplot   -> drawing charts
#   matplotlib.dates    -> nicer date labels on the x-axis
#   Patch               -> custom legend entries
#   Path                -> file paths that work on any computer

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch
from pathlib import Path

# %%
# STEP 2: Set up folders and settings

# The folder we are running from. This should be the folder with the CSVs.
data_folder = Path.cwd()

# A folder for the saved chart images. It is created if it does not exist yet.
output_folder = data_folder / "figures"
output_folder.mkdir(exist_ok=True)

# The two days the incident happened
INCIDENT_DAYS = ["2026-05-07", "2026-05-08"]

# The 4-hour blocks used in the usage file, in time-of-day order
BLOCK_ORDER = ["00-03", "04-07", "08-11", "12-15", "16-19", "20-23"]

# %%
# STEP 3: Load the CSV files into tables

service = pd.read_csv(data_folder / "service_status_checks.csv")
usage = pd.read_csv(data_folder / "canvas_usage_summary.csv")
tickets = pd.read_csv(data_folder / "helpdesk_tickets_summary.csv")
calendar = pd.read_csv(data_folder / "academic_calendar_flags.csv")

# Text like "2026-05-07T09:00:00" becomes a real date and time that Python understands.
service["timestamp"] = pd.to_datetime(service["timestamp"])
tickets["date"] = pd.to_datetime(tickets["date"])
calendar["date"] = pd.to_datetime(calendar["date"])

# Print how many rows each table has, to check that everything loaded
print("Service checks:    ", len(service), "rows")
print("Usage summary:     ", len(usage), "rows")
print("Help desk tickets: ", len(tickets), "rows")
print("Academic calendar: ", len(calendar), "rows")

# %%
# STEP 4: Find when the incident happened

# The data marks incident hours with incident_flag = 1.
# Keep only those rows, then look at the first and last time.
incident_rows = service[service["incident_flag"] == 1]
incident_start = incident_rows["timestamp"].min()
incident_end = incident_rows["timestamp"].max()

print("Incident started:", incident_start)
print("Incident ended:  ", incident_end)
print("Incident hours:  ", incident_rows["timestamp"].nunique())

# %%
# STEP 5: Add two columns so the tables can be matched up
# The usage and ticket files use a text date ("2026-05-07") and a 4-hour
# block label ("08-11"). We add the same two columns to the service table.

service["date"] = service["timestamp"].dt.strftime("%Y-%m-%d")


def make_block_label(hour):
    """Turn an hour from 0 to 23 into a 4-hour block label like '08-11'."""
    start = (hour // 4) * 4
    end = start + 3
    return f"{start:02d}-{end:02d}"


service["hour_block"] = service["timestamp"].dt.hour.apply(make_block_label)

# %%
# STEP 6: Average the six service checks for each hour
# Each hour has six checks, one per part of the service. We average them so
# the chart shows one point per hour.

hourly = service.groupby("timestamp").agg(
    avg_response_ms=("response_time_ms", "mean"),
    avg_error_rate=("error_rate", "mean"),
    incident_flag=("incident_flag", "max"),
).reset_index()

# Keep only May 1 to May 10 for the timing chart
hourly = hourly[(hourly["timestamp"] >= "2026-05-01") & (hourly["timestamp"] < "2026-05-11")]

# %%
# STEP 7: CHART 1 - Timing
# Top panel: response time. Bottom panel: error rate.
# Red shading marks the incident hours.

fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(12, 7), sharex=True)

# Top panel: response time
ax_top.plot(hourly["timestamp"], hourly["avg_response_ms"], color="steelblue", linewidth=1.2)
ax_top.set_ylabel("Response time (milliseconds)")
ax_top.set_title("Chart 1: Canvas response time and error rate by hour (May 1-10, 2026)",
                 fontweight="bold")

# Bottom panel: error rate
ax_bottom.plot(hourly["timestamp"], hourly["avg_error_rate"], color="firebrick", linewidth=1.2)
ax_bottom.set_ylabel("Error rate (0 to 1)")
ax_bottom.set_xlabel("Date")

# Shade every incident hour in red, in both panels
flagged_hours = hourly[hourly["incident_flag"] == 1]["timestamp"]
for hour in flagged_hours:
    ax_top.axvspan(hour, hour + pd.Timedelta(hours=1), color="red", alpha=0.12)
    ax_bottom.axvspan(hour, hour + pd.Timedelta(hours=1), color="red", alpha=0.12)

# One date label every 2 days, so the labels do not overlap
ax_bottom.xaxis.set_major_locator(mdates.DayLocator(interval=2))
ax_bottom.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

# Legend that explains the red shading
ax_top.legend(handles=[Patch(color="red", alpha=0.12, label="Incident hours")], loc="upper left")

plt.tight_layout()
fig.savefig(output_folder / "chart1_timing.png", dpi=150)
plt.show()

# %%
# STEP 8: Demand = how busy Canvas was
# "Activity" = logins + quiz attempts + assignment submissions + file access.
# First, add the four counts together for each row.

usage["total_activity"] = (
    usage["login_count"]
    + usage["quiz_exam_attempts"]
    + usage["assignment_submissions"]
    + usage["file_accesses"]
)

# Keep Spring 2026, May 1-10 only (the same days as the service data)
spring_usage = usage[(usage["term"] == "Spring_2026") & (usage["date"] <= "2026-05-10")]

# Add up the three user roles (student, faculty, staff) so each date and block has one total
day_block = spring_usage.groupby(["date", "hour_block"], as_index=False)["total_activity"].sum()

# Mark each row as an incident day or not
day_block["incident_day"] = day_block["date"].isin(INCIDENT_DAYS)

# Average the activity for each block, split into incident days and other days
avg_activity = (
    day_block.groupby(["hour_block", "incident_day"])["total_activity"]
    .mean()
    .unstack()
    .reindex(BLOCK_ORDER)
)
avg_activity.columns = ["Other days (May 1-10)", "Incident days (May 7-8)"]

# %%
# STEP 9: CHART 2 - Demand by time of day
# Side-by-side bars: for each 4-hour block, how busy was a typical incident
# day compared with a typical other day?

fig, ax = plt.subplots(figsize=(10, 6))
avg_activity.plot(kind="bar", ax=ax, color=["gray", "firebrick"], width=0.8, rot=0)

ax.set_title("Chart 2: Average demand per 4-hour block, incident days vs other days",
             fontweight="bold")
ax.set_xlabel("Time of day (4-hour block, local time)")
ax.set_ylabel("Average activity events per block")
ax.legend(title="Day type")

plt.tight_layout()
fig.savefig(output_folder / "chart2_demand.png", dpi=150)
plt.show()

# %%
# STEP 10: CHART 3 - Impact on the help desk
# Each day's tickets, split into incident-related (red) and other (gray).
# Gold shading marks the finals period from the academic calendar.

# Count tickets per date, split by incident_related_flag (0 = other, 1 = incident-related)
daily_tickets = (
    tickets.groupby(["date", "incident_related_flag"])["ticket_count"]
    .sum()
    .unstack(fill_value=0)
)
daily_tickets.columns = ["Other tickets", "Incident-related tickets"]

# Show May 1 to May 15 only
daily_tickets = daily_tickets.loc["2026-05-01":"2026-05-15"]

# The days the academic calendar marks as finals, limited to May 1-15
# (the calendar also has December finals, which are not on this chart)
is_finals = calendar["finals_period_flag"] == 1
in_may = calendar["date"].between("2026-05-01", "2026-05-15")
finals_days = calendar[is_finals & in_may]["date"]

fig, ax = plt.subplots(figsize=(12, 6))

# Gold shading for finals days
for day in finals_days:
    ax.axvspan(day, day + pd.Timedelta(days=1), color="gold", alpha=0.2)

# Stacked bars: "other" at the bottom, "incident-related" on top
ax.bar(daily_tickets.index, daily_tickets["Other tickets"],
       color="gray", width=0.8, label="Other tickets")
ax.bar(daily_tickets.index, daily_tickets["Incident-related tickets"],
       bottom=daily_tickets["Other tickets"], color="firebrick", width=0.8,
       label="Incident-related tickets")

ax.set_title("Chart 3: Help desk tickets per day, May 1-15, 2026", fontweight="bold")
ax.set_xlabel("Date")
ax.set_ylabel("Number of tickets")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

# Legend, with an extra entry for the gold finals shading
handles, labels = ax.get_legend_handles_labels()
handles.append(Patch(color="gold", alpha=0.2))
labels.append("Finals period (academic calendar)")
ax.legend(handles, labels, loc="upper left")

plt.tight_layout()
fig.savefig(output_folder / "chart3_tickets.png", dpi=150)
plt.show()

# %%
# STEP 11: CHART 4 - Impact on each part of the service
# Average error rate for each part, during incident hours vs normal hours.

service["period"] = service["incident_flag"].map({1: "Incident hours", 0: "Normal hours"})

error_by_part = (
    service.groupby(["service_component", "period"])["error_rate"]
    .mean()
    .unstack()
)

# Sort so the worst part is at the top, then put the columns in a fixed order
error_by_part = error_by_part.sort_values("Incident hours")
error_by_part = error_by_part[["Normal hours", "Incident hours"]]

fig, ax = plt.subplots(figsize=(10, 6))
error_by_part.plot(kind="barh", ax=ax, color=["gray", "firebrick"], width=0.8)

ax.set_title("Chart 4: Average error rate by service part, incident hours vs normal hours",
             fontweight="bold")
ax.set_xlabel("Average error rate (0 to 1)")
ax.set_ylabel("Service part")
ax.legend(title="Period")

plt.tight_layout()
fig.savefig(output_folder / "chart4_components.png", dpi=150)
plt.show()

# %%
# STEP 12: Key numbers to compare with the charts

worst_hour_error = hourly["avg_error_rate"].max()
print("Highest average error rate in one hour:", round(worst_hour_error, 2))

# The busiest block in May 1-10. Check the service data: this block was NOT
# an incident block, so high demand by itself did not trigger the incident.
busiest = day_block.loc[day_block["total_activity"].idxmax()]
print("Busiest block:", busiest["date"], busiest["hour_block"],
      "with", int(busiest["total_activity"]), "activity events")

# Data-quality check: some "ok" checks have high error rates
ok_but_high = ((service["check_result"] == "ok") & (service["error_rate"] >= 0.05)).sum()
print("'ok' checks with an error rate of 5% or higher:", ok_but_high)

print("\nDone. Charts saved in:", output_folder)
