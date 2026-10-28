"""
Canvas incident visualizations (BIT 4624 group project).

Reads the synthetic CSVs in this folder and builds one dashboard with four panels:
  A. Timing      - hourly response time and error rate, incident hours shaded
  B. Demand      - activity by date and 4-hour block (heatmap), flagged blocks outlined
  C. Impact      - daily help desk tickets, incident-related vs other, finals days shaded
  D. Components  - mean error rate by service component, incident vs baseline

Run it from any folder:
    python incident_visualizations.py

Writes figures/incident_dashboard.png and prints a short summary.
Needs: pandas, matplotlib
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # write to a file; no display needed
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch, Rectangle

DATA_DIR = Path(__file__).resolve().parent
OUT_DIR = DATA_DIR / "figures"
OUT_FILE = OUT_DIR / "incident_dashboard.png"

RED = "#c0392b"
GREY = "#7f8c8d"
BLUE = "#2c7fb8"
GOLD = "#f1c40f"

BLOCKS = ["00-03", "04-07", "08-11", "12-15", "16-19", "20-23"]
DEMAND_COLS = ["login_count", "assignment_submissions", "quiz_exam_attempts", "file_accesses"]
DAYS_BEFORE = 3  # days shown before the incident in the ticket chart
DAYS_AFTER = 8   # days shown after the incident in the ticket chart


# ---------------------------------------------------------------- data

def load_data():
    service = pd.read_csv(DATA_DIR / "service_status_checks.csv", parse_dates=["timestamp"])
    usage = pd.read_csv(DATA_DIR / "canvas_usage_summary.csv")
    tickets = pd.read_csv(DATA_DIR / "helpdesk_tickets_summary.csv")
    calendar = pd.read_csv(DATA_DIR / "academic_calendar_flags.csv", parse_dates=["date"])
    return service, usage, tickets, calendar


def add_time_blocks(service):
    """Add a date string and a 4-hour block label that match the usage file's format."""
    service = service.copy()
    service["date"] = service["timestamp"].dt.strftime("%Y-%m-%d")
    block_start = (service["timestamp"].dt.hour // 4) * 4
    service["hour_block"] = block_start.map(lambda h: f"{h:02d}-{h + 3:02d}")
    return service


def hourly_summary(service):
    """One row per hour, averaged across the six components."""
    return (
        service.groupby("timestamp")
        .agg(
            response_ms=("response_time_ms", "mean"),
            error_rate=("error_rate", "mean"),
            failed=("check_result", lambda s: (s == "failed").sum()),
            incident=("incident_flag", "max"),
        )
        .reset_index()
    )


def demand_by_block(usage):
    """Total activity per date and 4-hour block, summed across user roles."""
    usage = usage.copy()
    usage["demand"] = usage[DEMAND_COLS].sum(axis=1)
    return usage.groupby(["date", "hour_block"], as_index=False)["demand"].sum()


def daily_tickets(tickets):
    """Ticket counts per day, split into incident-related (1) and other (0)."""
    t = tickets.copy()
    t["date"] = pd.to_datetime(t["date"])
    daily = t.pivot_table(
        index="date", columns="incident_related_flag",
        values="ticket_count", aggfunc="sum", fill_value=0,
    )
    return daily.reindex(columns=[0, 1], fill_value=0)


# ---------------------------------------------------------------- panels

def plot_timing(ax, hourly, start, end, incident_start, incident_end):
    w = hourly[hourly["timestamp"].between(start, end)]
    in_incident = w["incident"].eq(1).to_numpy()

    ax.plot(w["timestamp"], w["response_ms"], color=BLUE, lw=1.2, label="Mean response time (ms)")
    ax.fill_between(
        w["timestamp"], 0, 1, where=in_incident,
        transform=ax.get_xaxis_transform(), color=RED, alpha=0.12, label="Incident hours",
    )
    ax.set_ylabel("Response time (ms)")

    ax2 = ax.twinx()
    ax2.plot(w["timestamp"], w["error_rate"], color=RED, lw=1.2, label="Mean error rate")
    ax2.set_ylabel("Error rate")
    ax2.spines["top"].set_visible(False)

    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", frameon=False, fontsize=8)

    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.tick_params(axis="x", labelsize=8)
    ax.set_title("A. Timing: response time and errors by hour", loc="left", fontweight="bold")


def plot_demand(ax, demand, service, dates):
    grid = (
        demand[demand["date"].isin(dates)]
        .pivot(index="date", columns="hour_block", values="demand")
        .reindex(index=dates, columns=BLOCKS)
        .fillna(0)
    )
    im = ax.imshow(grid.to_numpy(), cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(BLOCKS)))
    ax.set_xticklabels(BLOCKS)
    ax.set_yticks(range(len(dates)))
    ax.set_yticklabels([pd.Timestamp(d).strftime("%a %b %d") for d in dates])
    ax.set_xlabel("4-hour block (local time)")

    flagged = service.groupby(["date", "hour_block"])["incident_flag"].max()
    vmax = np.nanmax(grid.to_numpy())
    for i, d in enumerate(dates):
        for j, b in enumerate(BLOCKS):
            val = grid.iloc[i, j]
            ax.text(j, i, f"{int(val):,}", ha="center", va="center", fontsize=7,
                    color="white" if val > 0.6 * vmax else "black")
            if flagged.get((d, b), 0) == 1:
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                       edgecolor=RED, lw=2.5))

    cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Activity events (logins, quizzes, submissions, files)", fontsize=8)
    ax.set_title("B. Demand: activity per block, red outline = service flagged",
                 loc="left", fontweight="bold")


def plot_tickets(ax, daily, calendar, incident_start, incident_end):
    lo = incident_start.normalize() - pd.Timedelta(days=DAYS_BEFORE)
    hi = incident_end.normalize() + pd.Timedelta(days=DAYS_AFTER)
    d = daily.loc[lo:hi]

    finals_days = calendar.loc[
        (calendar["finals_period_flag"] == 1) & calendar["date"].between(lo, hi), "date"
    ]
    for day in finals_days:
        ax.axvspan(day, day + pd.Timedelta(days=1), color=GOLD, alpha=0.18, lw=0)

    ax.bar(d.index, d[0], color=GREY, label="Other tickets")
    ax.bar(d.index, d[1], bottom=d[0], color=RED, label="Incident-related")
    ax.set_xlim(lo - pd.Timedelta(hours=12), hi + pd.Timedelta(hours=12))

    handles, labels = ax.get_legend_handles_labels()
    if len(finals_days):
        handles.append(Patch(color=GOLD, alpha=0.4))
        labels.append("Finals period (calendar)")
    ax.legend(handles, labels, frameon=False, fontsize=8, loc="upper right")

    ax.set_ylabel("Tickets per day")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.set_title("C. Impact: help desk tickets per day", loc="left", fontweight="bold")


def plot_components(ax, service):
    s = service.assign(period=np.where(service["incident_flag"] == 1, "Incident", "Baseline"))
    means = (
        s.groupby(["service_component", "period"])["error_rate"]
        .mean()
        .unstack()
        .sort_values("Incident")
    )
    y = np.arange(len(means))
    ax.barh(y + 0.2, means["Incident"], height=0.4, color=RED, label="Incident hours")
    ax.barh(y - 0.2, means["Baseline"], height=0.4, color=GREY, label="Baseline hours")
    ax.set_yticks(y)
    ax.set_yticklabels(means.index)
    ax.set_xlabel("Mean error rate")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title("D. Impact by component: error rate, incident vs baseline",
                 loc="left", fontweight="bold")


# ---------------------------------------------------------------- summary

def print_summary(service, hourly, demand, tickets, spring_dates, incident_start, incident_end):
    n_hours = int(hourly["incident"].sum())
    print("TIMING")
    print(f"  Incident hours flagged: {n_hours} "
          f"({incident_start:%a %b %d %H:%M} to {incident_end:%a %b %d %H:%M})")
    print(f"  Peak hourly error rate: {hourly['error_rate'].max():.2f}")
    print(f"  Peak failed checks in one hour: {hourly['failed'].max()} (of 6 components)")

    block_flag = (service.groupby(["date", "hour_block"])["incident_flag"].max()
                  .rename("flag").reset_index())
    d = demand.merge(block_flag, on=["date", "hour_block"], how="left")
    d = d[d["date"].isin(spring_dates)]
    print("\nDEMAND (Spring 2026, all roles)")
    print(f"  Avg events per block when flagged: {d.loc[d['flag'] == 1, 'demand'].mean():,.0f}")
    print(f"  Avg events per block otherwise:    {d.loc[d['flag'] == 0, 'demand'].mean():,.0f}")
    busiest = d.loc[d["demand"].idxmax()]
    print(f"  Busiest block: {busiest['date']} {busiest['hour_block']} "
          f"with {busiest['demand']:,.0f} events; flagged: {busiest['flag'] == 1}")

    print("\nIMPACT (help desk)")
    inc = tickets[tickets["incident_related_flag"] == 1]
    print(f"  Incident-related tickets, all dates: {inc['ticket_count'].sum():,}")
    by_cat = inc.groupby("issue_category")["ticket_count"].sum().sort_values(ascending=False)
    for cat, n in by_cat.head(3).items():
        print(f"    {cat}: {n:,}")

    print("\nLABEL CHECK (service file)")
    ok_high = ((service["check_result"] == "ok") & (service["error_rate"] >= 0.05)).sum()
    deg_low = ((service["check_result"] == "degraded") & (service["error_rate"] < 0.05)).sum()
    print(f"  'ok' rows with error_rate >= 0.05: {ok_high}")
    print(f"  'degraded' rows with error_rate < 0.05: {deg_low}")


# ---------------------------------------------------------------- main

def main():
    OUT_DIR.mkdir(exist_ok=True)
    service, usage, tickets, calendar = load_data()
    service = add_time_blocks(service)
    hourly = hourly_summary(service)
    demand = demand_by_block(usage)
    daily = daily_tickets(tickets)

    flagged = hourly.loc[hourly["incident"] == 1, "timestamp"]
    incident_start, incident_end = flagged.min(), flagged.max()

    spring = service[service["term"] == "Spring_2026"]
    spring_start, spring_end = spring["timestamp"].min(), spring["timestamp"].max()
    spring_dates = sorted(spring["date"].unique())

    fig = plt.figure(figsize=(15, 10), layout="constrained")
    gs = fig.add_gridspec(2, 2)

    plot_timing(fig.add_subplot(gs[0, 0]), hourly, spring_start, spring_end,
                incident_start, incident_end)
    plot_demand(fig.add_subplot(gs[0, 1]), demand, service, spring_dates)
    plot_tickets(fig.add_subplot(gs[1, 0]), daily, calendar, incident_start, incident_end)
    plot_components(fig.add_subplot(gs[1, 1]), service)

    fig.suptitle("Canvas service incident, May 2026: timing, demand and impact",
                 fontsize=14, fontweight="bold")
    fig.text(0.01, 0.005,
             "Synthetic teaching data. Demand and tickets are joined to service checks "
             "by date and 4-hour block.", fontsize=8, color="#555")
    fig.savefig(OUT_FILE, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print_summary(service, hourly, demand, tickets, spring_dates, incident_start, incident_end)
    print(f"\nSaved {OUT_FILE}")


if __name__ == "__main__":
    main()
