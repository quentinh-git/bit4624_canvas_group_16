# ==========================================================
# Canvas incident charts (simple version)
# BIT 4624 group project
#
# This file makes 4 charts from the CSV files.
# Put this file in the same folder as the CSV files, then run:
#     python canvas_incident_charts_simple.py
# ==========================================================

import os
import pandas as pd
import matplotlib.pyplot as plt

# Make a folder to save the charts in (does nothing if it already exists)
os.makedirs("figures", exist_ok=True)

# ----------------------------------------------------------
# Step 1: Load the data
# ----------------------------------------------------------
service = pd.read_csv("service_status_checks.csv")
usage = pd.read_csv("canvas_usage_summary.csv")
tickets = pd.read_csv("helpdesk_tickets_summary.csv")
calendar = pd.read_csv("academic_calendar_flags.csv")

# Change the text dates into real dates so charts can use them
service["timestamp"] = pd.to_datetime(service["timestamp"])
calendar["date"] = pd.to_datetime(calendar["date"])

# Find when the incident happened (incident_flag is 1 during the incident)
incident_hours = service[service["incident_flag"] == 1]
print("Incident starts:", incident_hours["timestamp"].min())
print("Incident ends:  ", incident_hours["timestamp"].max())

# ----------------------------------------------------------
# Step 2: CHART 1 - Response time and error rate by hour
# ----------------------------------------------------------

# Each hour has 6 checks (one per service part), so we take the average
hourly = service.groupby("timestamp")[["response_time_ms", "error_rate"]].mean()
hourly["incident"] = service.groupby("timestamp")["incident_flag"].max()

# Keep only May 1 to May 10
hourly = hourly["2026-05-01":"2026-05-10"]

# Two charts stacked on top of each other
fig, (top, bottom) = plt.subplots(2, 1, figsize=(12, 7), sharex=True)

top.plot(hourly.index, hourly["response_time_ms"], color="steelblue")
top.set_title("Chart 1: Response time and error rate by hour (red = incident hours)")
top.set_ylabel("Response time (ms)")

bottom.plot(hourly.index, hourly["error_rate"], color="firebrick")
bottom.set_ylabel("Error rate (0 to 1)")
bottom.set_xlabel("Date")

# Shade each incident hour in red on both charts
for hour in hourly[hourly["incident"] == 1].index:
    top.axvspan(hour, hour + pd.Timedelta(hours=1), color="red", alpha=0.15)
    bottom.axvspan(hour, hour + pd.Timedelta(hours=1), color="red", alpha=0.15)

plt.savefig("figures/chart1_timing.png")
plt.show()

# ----------------------------------------------------------
# Step 3: CHART 2 - Demand (how busy Canvas was)
# Activity = logins + quizzes + submissions + file access
# ----------------------------------------------------------

usage["activity"] = (usage["login_count"] + usage["quiz_exam_attempts"]
                     + usage["assignment_submissions"] + usage["file_accesses"])

# Keep Spring 2026, May 1 to May 10 only
spring = usage[(usage["term"] == "Spring_2026") & (usage["date"] <= "2026-05-10")]

# Add up the three user roles for each date and time block
totals = spring.groupby(["date", "hour_block"])["activity"].sum().reset_index()

# Mark which rows are on the incident days
totals["incident_day"] = totals["date"].isin(["2026-05-07", "2026-05-08"])

# Average activity for each time block, for incident days and other days
block_order = ["00-03", "04-07", "08-11", "12-15", "16-19", "20-23"]
incident_avg = totals[totals["incident_day"]].groupby("hour_block")["activity"].mean()
other_avg = totals[~totals["incident_day"]].groupby("hour_block")["activity"].mean()

compare = pd.DataFrame({"Other days": other_avg, "Incident days": incident_avg})
compare = compare.loc[block_order]

compare.plot(kind="bar", color=["gray", "firebrick"], rot=0, figsize=(10, 6))
plt.title("Chart 2: Average demand per 4-hour block, incident days vs other days")
plt.xlabel("Time of day (local time)")
plt.ylabel("Average activity events per block")

plt.savefig("figures/chart2_demand.png")
plt.show()

# ----------------------------------------------------------
# Step 4: CHART 3 - Help desk tickets per day
# ----------------------------------------------------------

# Add up tickets for each day, separately for incident-related and other
other_tickets = tickets[tickets["incident_related_flag"] == 0].groupby("date")["ticket_count"].sum()
incident_tickets = tickets[tickets["incident_related_flag"] == 1].groupby("date")["ticket_count"].sum()

# Put both into one table. Days with no tickets get a 0.
day_table = pd.DataFrame({"Other": other_tickets, "Incident-related": incident_tickets}).fillna(0)
day_table.index = pd.to_datetime(day_table.index)
day_table = day_table["2026-05-01":"2026-05-15"]

# Finals days from the academic calendar (May only)
finals = calendar[(calendar["finals_period_flag"] == 1)
                  & (calendar["date"] >= "2026-05-01")
                  & (calendar["date"] <= "2026-05-15")]

plt.figure(figsize=(12, 6))

# Stacked bars: other tickets on the bottom, incident-related on top
plt.bar(day_table.index, day_table["Other"], color="gray", label="Other tickets")
plt.bar(day_table.index, day_table["Incident-related"], bottom=day_table["Other"],
        color="firebrick", label="Incident-related tickets")

# Gold shading for finals days
for day in finals["date"]:
    plt.axvspan(day, day + pd.Timedelta(days=1), color="gold", alpha=0.2, zorder=0)

plt.title("Chart 3: Help desk tickets per day, May 1-15 (gold = finals period)")
plt.xlabel("Date")
plt.ylabel("Number of tickets")
plt.legend()

plt.savefig("figures/chart3_tickets.png")
plt.show()

# ----------------------------------------------------------
# Step 5: CHART 4 - Error rate by service part
# ----------------------------------------------------------

# Average error rate for each service part during incident and normal hours
incident_part = service[service["incident_flag"] == 1].groupby("service_component")["error_rate"].mean()
normal_part = service[service["incident_flag"] == 0].groupby("service_component")["error_rate"].mean()

part_table = pd.DataFrame({"Normal hours": normal_part, "Incident hours": incident_part})
part_table = part_table.sort_values("Incident hours")

part_table.plot(kind="barh", color=["gray", "firebrick"], figsize=(10, 6))
plt.title("Chart 4: Average error rate by service part")
plt.xlabel("Average error rate (0 to 1)")
plt.ylabel("Service part")

plt.savefig("figures/chart4_components.png")
plt.show()

# ----------------------------------------------------------
# Step 6: Print a quick number to compare with the charts
# ----------------------------------------------------------
print("Highest average error rate in one hour:", round(hourly["error_rate"].max(), 2))
print("Done! The charts are saved in the figures folder.")
