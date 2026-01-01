# !/bin/env python

"""
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

        self.data, self.habits = self.process_data(self.data)
        self.data = self.data.sort_values(by="date", ascending=False)

        # self.data.to_csv(os.path.join(self.dir, 'habit_data_processed.csv'), index=False)


        self.year_bars = self.data[self.habits].sum().reset_index()
        self.year_bars.columns = ["Habit", "Sum"]
        self.year_bars['Percent'] = self.year_bars['Sum'].apply(lambda x: f'{x/len(self.data):.2f}%')
        self.year_bars['Bars'] = self.year_bars['Sum'].apply(lambda x: '|' + '█' * math.ceil((x/len(self.data))*25.0) + '░' * math.floor((1.0 - (x/len(self.data)))*25.0) + '|')
        # self.year_bars['Bars'] = self.year_bars['Sum'].apply(lambda x: '🟩' * math.ceil((x/len(self.data))*20.0) + '🟥' * math.floor((1.0 - (x/len(self.data)))*20.0))


        # self.data.to_csv(os.path.join(self.dir, 'habit_data_processed.csv'), index=False)

        last_7 = pd.Timestamp.now().normalize() - pd.Timedelta(days=6)
        self.data_last_week = self.data[self.data["date"] >= last_7]
        self.data_last_week = self.data_last_week.sort_values(by="date", ascending=False)

        self.last_week_bars = self.data_last_week[self.habits].sum().reset_index()
        self.last_week_bars.columns = ["Habit", "Sum"]

        week = max(7.0, len(self.data_last_week))
        self.last_week_bars['Percent'] = self.last_week_bars['Sum'].apply(lambda x: f'{x/week:.2f}%')
        self.last_week_bars['Bars'] = self.last_week_bars['Sum'].apply(lambda x: '|' + '█' * math.ceil((x/week)*25.0) + '░'* math.floor((1.0 - (x/week))*25.0) + '|')
        # self.last_week_bars['Bars'] = self.last_week_bars['Sum'].apply(lambda x: '🟩' * math.ceil((x/7.0)*25.0) + '🟥'* math.floor((1.0 - (x/7.0))*25.0))


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
            return None, None
        
        df["date"] = df["Timestamp"].dt.normalize()

        df = df.groupby("date", as_index=False)["Habits"].agg(lambda x: " ".join(x))

        habits = df["Habits"].str.split(" ", expand=True).stack().reset_index(level=1, drop=True)
        habits.name = "Habit"
        habits = habits.unique().tolist()
        habits = [habit.replace(",", "").replace(" ", "").strip() for habit in habits ]
        habits = list(set(habits))
        habits = [habit for habit in habits if habit != ""]
        # habits = sorted(habits)
        
        for habit in habits:
            # print(f'|{habit}|')
            df[habit] = df["Habits"].apply(lambda x: 1 if habit in x else 0)
            df[habit] = df[habit].fillna(0).astype(int)

        df = df.drop(columns=["Habits"])

        # ---- Fill missing days with 0s ----
        start = df["date"].min()
        end = df["date"].max()
        all_days = pd.date_range(start, end, freq="D")

        df = df.set_index("date").reindex(all_days)
        df.index.name = "date"
        df = df.reset_index(drop=False)
        df = df.fillna(0)

        return df, habits

    def get_streak(self, series: pd.Series) -> int:
        """ Get current streak for a habit series (1s and 0s) """
        streak = 0
        for val in series:
            if val == 1:
                streak += 1
            else:
                break
        return streak

    def get_neg_streak(self, series: pd.Series) -> int:
        """ Get current streak for a habit series (1s and 0s) """
        streak = 0
        for val in series:
            if val == 0:
                streak += 1
            else:
                break
        return streak

    def create_message(self):
        template = ''
        with open(os.path.join(self.dir,self.config.data['TEMPLATE_PATH']), 'r', encoding='utf8') as f:
            template = f.read()

        content = ''

        habit_streaks = []
        for habit in self.habits:
            streak = self.get_streak(self.data[habit])
            if streak > 1:
                tier = ''
                if streak >= 3:
                    tier = '🔥 '
                if streak >= 6:
                    tier = '🌟 '
                if streak >= 12:
                    tier = '🏆 '
                if streak >= 15:
                    tier = '🚀 '
                habit_streaks.append((habit, streak, tier))

        if len(habit_streaks) > 0:
            content += '<h2>**Streaks**</h2>'
            content += '<table style="font-size: 18px;"  class="dataframe table table-striped table-hover table-bordered table-responsive">'
            for habit, streak, tier in habit_streaks:
                content += f'''
                <tr>
                    <td><b>{habit}</b></td>
                    <td style="text-align:center">{tier}</td>
                    <td style="text-align:left">{streak} days</td>
                </tr>
                '''
            content += '</table>'
            content += '<hr>'

        negative_streaks = []
        for habit in self.habits:
            neg_streak = self.get_neg_streak(self.data[habit])
            if neg_streak > 1:
                tier = ''
                if neg_streak >= 3:
                    tier = '⚠️ '
                if neg_streak >= 6:
                    tier = '⛔ '
                if neg_streak >= 12:
                    tier = '❌ '
                if neg_streak >= 15:
                    tier = '💀 '
                negative_streaks.append((habit, neg_streak, tier))

        if len(negative_streaks) > 0:
            content += '<div class=".text-danger">'
            content += '<h2>!!Negative Streaks!!</h2>'
            content += '<table style="font-size: 18px;"  class="dataframe table table-striped table-hover table-bordered table-responsive">'
            for habit, streak, tier in negative_streaks:
                content += f'''
                <tr>
                    <td><b>{habit}</b></td>
                    <td style="text-align:center">{tier}</td>
                    <td style="text-align:left">-{streak} days</td>
                </tr>
                '''
            content += '</table>'
            content += '</div>'
            content += '<hr>'

        content += '<h2>Habit Data (Last 7 Days)</h2>'

        content += self.last_week_bars[["Habit", "Percent","Bars"]].to_html(
                                classes='table table-striped table-hover table-bordered table-responsive', 
                                index=False,
                                border=0
                                )

        content += '<hr>'
        temp = self.data_last_week.to_html(
                                classes='table table-striped table-hover table-bordered table-responsive', 
                                index=False,
                                border=0
                                ) 
        temp = temp.replace('>0.0<','>🟥<')
        temp = temp.replace('>1.0<','>🟩<')
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
        temp = temp.replace('>0.0<','>🟥<')
        temp = temp.replace('>1.0<','>🟩<')
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
    
