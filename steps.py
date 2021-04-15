#!/usr/bin/env python3


from googleapiclient.discovery import build
from datetime import datetime
import pandas as pd
from gsheet import get_credentials


STEP_SPREADSHEET_ID = "id-of-spreadsheet"
# I chose a large range
STEP_RANGE_NAME = "Sheet1!A1:M1000"

# the columns in the spreadsheet we care about
OUR_COLS = {"Date": 0, "Steps": 1, "Distance": 6, "Active Mins": 12}
DATE_STAMP = "%B %d, %Y"


def build_data(values):
    for row in values:
        if not row[OUR_COLS["Date"]]:
            continue

        yield build_entry(row)


def build_entry(row):

    record_date = datetime.strptime(row[OUR_COLS["Date"]], DATE_STAMP)
    day = record_date.date()
    weekday = record_date.strftime("%A")
    week_number = ":".join((str(record_date.year), str(record_date.isocalendar()[1])))

    return (
        day,
        weekday,
        week_number,
        float(row[OUR_COLS["Distance"]]),
        sum([int(x) for x in row[-3:]]),
    )


def build_weekly(df):

    weekly = []
    for v in df.week_number.unique():

        week = [
            v,
        ]
        week.append(df.query(f"week_number == '{v}'")["distance"].astype("int64").sum())
        week.append(
            df.query(f"week_number == '{v}'")["active_mins"].astype("int64").sum()
        )
        weekly.append(week)

    weekly_df = pd.DataFrame(weekly, columns=["week_number", "distance", "active_mins"])
    return weekly_df


def main():
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=STEP_SPREADSHEET_ID, range=STEP_RANGE_NAME)
        .execute()
    )

    values = result.get("values", None)

    if not values:
        print("no data found")
        return []

    entries = build_data(values)

    df = pd.DataFrame(
        entries, columns=["day", "weekday", "week_number", "distance", "active_mins",]
    )

    total_dis = df["distance"].astype("int64").sum()

    print(f"Walked {total_dis} miles from {df.day.iloc[0]} to {df.day.iloc[-1]}\n")

    print(df["distance"].describe())
    print("\n")
    max_day = df.query("distance == distance.max()")
    print(f"biggest day was {max_day.day.iloc[0]} with {max_day.distance.iloc[0]}")

    min_day = df.query("distance == distance.min()")
    print(f"worst day was {min_day.day.iloc[0]} with {min_day.distance.iloc[0]}")

    weekly_df = build_weekly(df)

    print(weekly_df)

    df.to_csv("../jupyter-notebook-docker-compose/datasets/fitbit-steps.csv")


if __name__ == "__main__":
    main()
