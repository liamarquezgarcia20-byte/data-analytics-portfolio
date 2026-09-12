from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


DATA_DIR = Path("data")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


def load_and_clean():
    trips_2019 = pd.read_csv(DATA_DIR / "Divvy_Trips_2019_Q1.csv")
    trips_2020 = pd.read_csv(DATA_DIR / "Divvy_Trips_2020_Q1.csv")

    trips_2019 = trips_2019.rename(
        columns={
            "trip_id": "ride_id",
            "start_time": "started_at",
            "end_time": "ended_at",
            "from_station_name": "start_station_name",
            "to_station_name": "end_station_name",
            "usertype": "member_casual",
        }
    )
    trips_2019["member_casual"] = trips_2019["member_casual"].replace(
        {"Subscriber": "member", "Customer": "casual"}
    )

    columns = [
        "ride_id",
        "started_at",
        "ended_at",
        "start_station_name",
        "end_station_name",
        "member_casual",
    ]
    trips = pd.concat(
        [trips_2019[columns], trips_2020[columns]], ignore_index=True
    )
    trips = trips.drop_duplicates(subset="ride_id").dropna(subset=columns)
    trips["started_at"] = pd.to_datetime(trips["started_at"])
    trips["ended_at"] = pd.to_datetime(trips["ended_at"])
    trips["ride_minutes"] = (
        trips["ended_at"] - trips["started_at"]
    ).dt.total_seconds() / 60
    trips = trips[trips["ride_minutes"].between(1, 1440)].copy()
    trips["day_of_week"] = trips["started_at"].dt.day_name()
    trips["hour"] = trips["started_at"].dt.hour
    return trips


def style_chart(title, subtitle, ylabel, show_legend=True):
    ax = plt.gca()
    ax.set_title(title, fontsize=16, weight="bold", loc="left", pad=30)
    ax.text(
        0, 1.015, subtitle, transform=ax.transAxes,
        fontsize=10, ha="left", va="bottom", color="#555555",
    )
    ax.set_ylabel(ylabel)
    ax.set_xlabel("")
    ax.grid(axis="y", alpha=0.2)
    if show_legend:
        ax.legend(frameon=False)
    elif ax.get_legend() is not None:
        ax.get_legend().remove()
    plt.tight_layout()


def create_outputs(trips):
    colors = {"casual": "#F28E2B", "member": "#2A9D8F"}
    day_order = [
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday",
    ]

    overall = trips.groupby("member_casual").agg(
        rides=("ride_id", "count"),
        average_ride_minutes=("ride_minutes", "mean"),
        median_ride_minutes=("ride_minutes", "median"),
    ).round(2)
    overall.to_csv(OUTPUT_DIR / "overall_summary.csv")

    by_day = trips.groupby(["day_of_week", "member_casual"]).agg(
        rides=("ride_id", "count"),
        average_ride_minutes=("ride_minutes", "mean"),
    ).reset_index()
    by_day.to_csv(OUTPUT_DIR / "summary_by_day.csv", index=False)

    ride_counts = trips.groupby(["day_of_week", "member_casual"]).size().unstack()
    ride_counts = ride_counts.reindex(day_order)
    ride_counts.plot(
        kind="bar", figsize=(10, 6),
        color=[colors.get(column) for column in ride_counts.columns],
    )
    style_chart(
        "Rides by day of week",
        "Members ride most on weekdays; casual riders concentrate more trips on weekends.",
        "Number of rides",
    )
    plt.xticks(rotation=30, ha="right")
    plt.savefig(OUTPUT_DIR / "rides_by_day.png", dpi=180, bbox_inches="tight")
    plt.close()

    duration = trips.groupby("member_casual")["ride_minutes"].mean().reindex(["casual", "member"])
    duration.plot(kind="bar", figsize=(8, 5), color=[colors[x] for x in duration.index])
    style_chart(
        "Average ride duration",
        "Casual rides last more than three times as long as member rides.",
        "Average minutes",
        show_legend=False,
    )
    plt.xticks(rotation=0)
    plt.savefig(OUTPUT_DIR / "average_ride_duration.png", dpi=180, bbox_inches="tight")
    plt.close()

    hourly = trips.groupby(["hour", "member_casual"]).size().unstack(fill_value=0)
    hourly.plot(
        kind="line", figsize=(10, 6), linewidth=2.5,
        color=[colors.get(column) for column in hourly.columns],
    )
    style_chart(
        "Rides by hour of day",
        "Member trips peak near commuting hours; casual trips peak during the afternoon.",
        "Number of rides",
    )
    plt.xticks(range(0, 24, 2))
    plt.savefig(OUTPUT_DIR / "rides_by_hour.png", dpi=180, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    create_outputs(load_and_clean())
