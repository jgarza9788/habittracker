# !/bin/env python

"""\
My Habit Tracker 
The Black Pearl Newsletter Generator

"""
__author__ = "Justin Garza"
__copyright__ = "Copyright 2026, Justin Garza"
__credits__ = ["Justin Garza"]
__license__ = "FSL"
__version__ = "0.1"
__maintainer__ = "Justin Garza"
__email__ = "Justin Garza"
__status__ = "Development"

# standard imports
import os
import math
import re
import datetime
import requests
import pandas as pd
pd.set_option("future.no_silent_downcasting", True)


# data stuff
import gspread
from oauth2client.service_account import ServiceAccountCredentials

import plotly.express as px

# logging
from io import StringIO
from logging import Logger
from utils.logMan import createLogger

# data manager
from utils.dataMan import DataManager as DM

# email stuff
from email.message import EmailMessage
import ssl
import smtplib

class HabitTracker:
    """ Main Habit Tracker Class """

    def __init__(self, 
                 config_file: str = 'config.json',
                 credentials_file: str = 'credentials.json',
                 logger: Logger = None
                 ) -> None:

        self.dir = os.path.dirname(os.path.abspath(__file__))

        self.logger = logger
        if self.logger == None:
            self.logger = createLogger(
                root=os.path.join(self.dir,'log'),
                useStreamHandler=True
                )
        self.logger.info("Starting Habit Tracker")

        self.config_file = os.path.join(self.dir,config_file)
        self.config = DM(config_file,default={})

        self.credentials_file = os.path.join(self.dir,credentials_file)
        self.credentials = DM(credentials_file,default={})

        self.gsheet_key = os.path.join(self.dir, 'jgarza-1609029185640-e61af0876b7e.json')
        self.gsheet_id = "1gT_m6xnpEQ3YEIE44bwokKZJgsLn66nMo3MifTa4GGc"

        self.data = self.get_sheet_data()
        self.habit_cols = [c for c in self.data.columns if c != "Timestamp"]

        self.data = self.process_data(self.data)

        self.year_bars = self.data[self.habit_cols].sum().reset_index()
        self.year_bars.columns = ["Habit", "Sum"]
        self.year_bars['Percent'] = self.year_bars['Sum'].apply(lambda x: f'{x/len(self.data):.2f}%')
        # self.year_bars['Bars'] = self.year_bars['Sum'].apply(lambda x: '█' * math.ceil((x/len(self.data))*25.0) + '░' * math.floor((1.0 - (x/len(self.data)))*25.0))
        self.year_bars['Bars'] = self.year_bars['Sum'].apply(lambda x: '🟩' * math.ceil((x/len(self.data))*20.0) + '🟥' * math.floor((1.0 - (x/len(self.data)))*20.0))


        # self.data.to_csv(os.path.join(self.dir, 'habit_data_processed.csv'), index=False)

        last_7 = pd.Timestamp.now().normalize() - pd.Timedelta(days=6)
        self.data_last_week = self.data[self.data["Timestamp"] >= last_7]

        self.last_week_bars = self.data_last_week[self.habit_cols].sum().reset_index()
        self.last_week_bars.columns = ["Habit", "Sum"]
        self.last_week_bars['Percent'] = self.last_week_bars['Sum'].apply(lambda x: f'{x/7:.2f}%')
        # self.last_week_bars['Bars'] = self.last_week_bars['Sum'].apply(lambda x: '█' * math.ceil((x/7.0)*25.0) + '░'* math.floor((1.0 - (x/7.0))*25.0))
        self.last_week_bars['Bars'] = self.last_week_bars['Sum'].apply(lambda x: '🟩' * math.ceil((x/7.0)*25.0) + '🟥'* math.floor((1.0 - (x/7.0))*25.0))


        self.message = self.create_message()

        self.send_email()

        # self.logger.info(f"{self.message=}")
        # with open(os.path.join(self.dir,'message.html'), 'w', encoding='utf8') as f:
        #     f.write(self.message)
        #     f.close
    
    def get_sheet_data(self):
        """ Get raw data from URL """
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(self.gsheet_key, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(self.gsheet_id).sheet1
        # print(sheet.get_all_values())

        return pd.DataFrame(sheet.get_all_records())

    def process_data(self, df):
        """Process raw data into useful information.

        - Parses Timestamp
        - Coerces habit columns to 0/1 ints
        - Dedups to the "best" row per day (max # of 1s; tie -> latest Timestamp)
        - Fills missing days between min/max with 0s across all habit columns
        """
        if df is None or df.empty:
            # Return an empty, well-formed frame if nothing came in
            self.logger.error("No data to process.")
            return pd.DataFrame()

        df = df.copy()

        # ---- Timestamp -> datetime ----
        if "Timestamp" not in df.columns:
            self.logger.error("Expected a 'Timestamp' column in df")
            raise ValueError("Expected a 'Timestamp' column in df")


        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df = df.dropna(subset=["Timestamp"]).reset_index(drop=True)

        if df.empty:
            self.logger.error("No data to process.")
            return pd.DataFrame(columns=["Timestamp"])

        # ---- Identify habit columns (everything except Timestamp) ----
        

        # ---- Coerce habits to 0/1 ints (handles blanks, 'TRUE', 'FALSE', etc.) ----
        if self.habit_cols:
            # Normalize common truthy/falsey representations
            normalized = (
                df[self.habit_cols]
                .replace(
                    {
                        "": 0,
                        None: 0,
                        "TRUE": 1,
                        "True": 1,
                        True: 1,
                        "FALSE": 0,
                        "False": 0,
                        False: 0,
                    }
                )
                .infer_objects(copy=False)  # ✅ Removes the FutureWarning

            )

            # Numeric coercion + clip to [0,1]
            normalized = normalized.apply(pd.to_numeric, errors="coerce").fillna(0)
            df[self.habit_cols] = normalized.clip(lower=0, upper=1).astype(int)

        # ---- Dedup by day (best row per day) ----
        df["Day"] = df["Timestamp"].dt.normalize()

        # Habit columns must be strict 0/1 ints first
        df[self.habit_cols] = (
            df[self.habit_cols]
            .replace({"": 0, None: 0, True: 1, False: 0})
            .infer_objects(copy=False)
            .apply(pd.to_numeric, errors="coerce")
            .fillna(0)
            .clip(0, 1)
            .astype(int)
        )

        # Aggregate by day → keep 1 if it ever appeared that day
        dedup = df.groupby("Day", as_index=False).agg({
            **{c: "max" for c in self.habit_cols}  # max each habit column
        })

        # ---- Fill missing days with 0s ----
        start = dedup["Day"].min()
        end = dedup["Day"].max()
        all_days = pd.date_range(start, end, freq="D")

        dedup = dedup.set_index("Day").reindex(all_days)
        dedup.index.name = "Day"

        # Fill missing habit values with 0
        if self.habit_cols:
            dedup[self.habit_cols] = dedup[self.habit_cols].fillna(0).astype(int)

        # Restore Timestamp column (midnight for each day)
        dedup["Timestamp"] = dedup.index

        # Final column order: Timestamp first, then habits
        dedup = dedup.reset_index(drop=True)
        if self.habit_cols:
            dedup = dedup[["Timestamp"] + self.habit_cols]
        else:
            dedup = dedup[["Timestamp"]]

        return dedup

    def create_message(self):
        template = ''
        with open(os.path.join(self.dir,self.config.data['TEMPLATE_PATH']), 'r', encoding='utf8') as f:
            template = f.read()

        content = ''

        content += '<h2>Habit Data (Last 7 Days)</h2>'

        content += self.last_week_bars[["Habit", "Percent","Bars"]].to_html(
                                classes='table table-striped table-hover table-bordered table-responsive', 
                                index=False,
                                border=0
                                )

        # content += px.bar(
        #     self.last_week_scores,
        #     x='Habit',
        #     y='Sum',
        #     range_y=[0,7],
        #     title='Habit Completion Counts (Last 7 Days)',
        #     labels={'Sum':'Number of Completions', 'Habit':'Habit'},
        #     text_auto=True
        # ).to_html(full_html=False, include_plotlyjs='cdn')

        content += '<hr>'
        temp = self.data_last_week.to_html(
                                classes='table table-striped table-hover table-bordered table-responsive', 
                                index=False,
                                border=0
                                ) 
        temp = temp.replace('>0<','>🟥<')
        temp = temp.replace('>1<','>🟩<')
        content += temp
        content += '<hr>'

        content += '<h2>Habit Percents</h2>'
        content += self.year_bars[["Habit", "Percent","Bars"]].to_html(
                                classes='table table-striped table-hover table-bordered table-responsive', 
                                index=False,
                                border=0
                                )
        content += '<hr>'
        temp = self.data.to_html(
                                classes='table table-striped table-hover table-bordered table-responsive', 
                                index=False,
                                border=0
                                ) 
        temp = temp.replace('>0<','>🟥<')
        temp = temp.replace('>1<','>🟩<')
        content += temp
        content += '<hr>'

        message = template.replace('{{content}}', content)
        return message

    def send_email(self):
        em = EmailMessage()
        em['From'] = self.config.data["from_email"]
        em['To'] = ",".join(self.config.data["to_emails"])
        em['Subject'] = self.config.data["email_subject"]

        body = self.message
        # body = str(self.data)
        em.set_content(body, subtype='html')

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com',465,context=context) as smtp:
            smtp.login(self.credentials.data['Email_USER'],
                       self.credentials.data['Email_PWD']
                       )
            smtp.send_message(em) 

if __name__ == '__main__':
    HT = HabitTracker()
    
