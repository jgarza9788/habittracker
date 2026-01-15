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

from matplotlib.colors import LinearSegmentedColormap

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
        # self.gsheet_id = "1gT_m6xnpEQ3YEIE44bwokKZJgsLn66nMo3MifTa4GGc"
        self.gsheet_id = "1-b4xkSDxGgpuiPN-xBg4dkJ9HeA9iGba6kx9MsiieCQ"

        self.data = self.get_sheet_data()
        self.data.drop(columns=['Month','Week','Year','📶'], inplace=True)
        self.data["Date"] = pd.to_datetime(self.data["Date"], errors="coerce")
        self.data = self.data.sort_values(by="Date", ascending=False)

        # print(self.data)

        self.habits = self.get_habits(self.data)
        # self.convert_to_int()

        # print(self.data)

        #convert Date to datetime
        self.data["Date"] = pd.to_datetime(self.data["Date"], errors="coerce")


        #filter 
        today = pd.Timestamp.now().normalize()
        # today = pd.Timestamp.now().normalize() + pd.Timedelta(days=14)
        self.data = self.data[self.data["Date"] <= today]

        last_7 = pd.Timestamp.now().normalize() - pd.Timedelta(days=6)
        self.data_week = self.data[self.data["Date"] >= last_7]

        #year bars
        # self.bars_year = self.data[self.habits].sum().reset_index()
        # self.bars_year.columns = ["Habit", "Sum"]
        # self.bars_year["pSum"] = self.bars_year["Sum"].apply(lambda x: max(x,0))
        # self.bars_year['Percent'] = self.bars_year['Sum'].apply(lambda x: f'{ max(x/len(self.data),0):.2f}%')
        # self.bars_year['Bars'] = self.bars_year['pSum'].apply(lambda x: '|' + '█' * math.ceil((x/len(self.data))*25.0) + '░' * math.floor((1.0 - (x/len(self.data)))*25.0) + '|')


        

        self.data_summary = []
        for habit in self.habits:
            percent = max(self.data.loc[self.data[habit] == 1, habit].count()/len(self.data),0)

            filled = '█' * int(percent*25.0)
            empty = '░' * (25 - len(filled))

            self.data_summary.append( {
                "Habit": habit,
                "Percent": f'{ percent*100.0:.2f}%',
                "Bar": filled + empty,
                "✅": int(self.data.loc[self.data[habit] == 1, habit].count()),
                "⛔": int(self.data.loc[self.data[habit] == -1, habit].count()),
                "🔲": int(self.data.loc[self.data[habit] == 0, habit].count()),
            } )
        self.data_summary = pd.DataFrame(self.data_summary)

        #last week bars
        # self.bars_week = self.data_week[self.habits].sum().reset_index()
        # self.bars_week.columns = ["Habit", "Sum"]
        # self.bars_week["pSum"] = self.bars_week["Sum"].apply(lambda x: max(x,0))
        # week = min(7.0, len(self.data_week))
        # self.bars_week['Percent'] = self.bars_week['Sum'].apply(lambda x: f'{ x/week:.2f}%')
        # self.bars_week['Bars'] = self.bars_week['pSum'].apply(lambda x: '|' + '█' * math.ceil((x/week)*25.0) + '░'* math.floor((1.0 - (x/week))*25.0) + '|')   



        self.data_week_summary = []
        for habit in self.habits:
            percent = max(self.data_week.loc[self.data_week[habit] == 1, habit].count()/len(self.data_week),0)

            filled = '█' * int(percent*25.0)
            empty = '░' * (25 - len(filled))
            
            self.data_week_summary.append( {
                "Habit": habit,
                "Percent": f'{ percent*100.0:.2f}%',
                "Bar": filled + empty,
                "✅": int(self.data_week.loc[self.data_week[habit] == 1, habit].count()),
                "⛔": int(self.data_week.loc[self.data_week[habit] == -1, habit].count()),
                "🔲": int(self.data_week.loc[self.data_week[habit] == 0, habit].count()),
            } )
        self.data_week_summary = pd.DataFrame(self.data_week_summary)

        # streaks
        self.streaks = []
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
                if streak >= 30:
                    tier = '⭐⭐⭐ '
                self.streaks.append((habit, streak, tier))

        #negative streaks
        self.neg_streaks = []
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
                if neg_streak >= 30:
                    tier = '💀💀💀 '
                self.neg_streaks.append((habit, neg_streak, tier))


        # self.data.to_csv(os.path.join(self.dir,'data_year.csv'), index=False)

        # print(self.data_summary)
        # print(self.data_week_summary)

        # print(self.data)
        # print(self.habits)
        # print(self.data_week)
        # print(self.bars_year)
        # print(self.bars_week)

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
    
    def get_habits(self, df):
        """ Get list of habits from data frame """
        habits = df.columns.tolist()
        habits.remove("Date")
        # habits.remove("Month")
        # habits.remove("Year")
        return habits

    
    # def convert_to_int(self):
    #     """ Convert habit columns to int """
    #     for habit in self.habits:
    #         # self.data[habit] = self.data[habit].astype(int)
    #         # self.data[habit] = self.data[habit].map({"TRUE":1, "FALSE":0})
    #         self.data[habit] = self.data[habit].map({"TRUE":1, "FALSE":0})



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
            if val == -1:
                streak += 1
            else:
                break
        return streak
    

    
    def table_style(self, df):

        html_temp = (
                    df
                    .to_html(
                        classes='table table-striped table-hover table-bordered table-responsive', 
                        index=False,
                        border=0
                    )
                )

        # html_temp = html_temp.replace(
        #     "<table ",
        #     "<table style='font-family: 'Roboto Mono', ui-monospace, monospace;' "
        #     )
        
        return  html_temp

    def table_style_summary(self, df):
        cmap_wg = LinearSegmentedColormap.from_list("white_green", ["white",  "#4dff88"])
        cmap_wr = LinearSegmentedColormap.from_list("white_red", ["white",  "#ff4d4d"])
        html_temp = (
                    df.style
                    .background_gradient(cmap=cmap_wg, subset=["Passed" ])
                    .background_gradient(cmap=cmap_wr, subset=["Failed" ])
                    .to_html(
                        classes='table table-striped table-hover table-bordered table-responsive', 
                        index=False,
                        border=0
                    )
                )
        
        return html_temp

    def create_message(self):
        template = ''
        with open(os.path.join(self.dir,self.config.data['TEMPLATE_PATH']), 'r', encoding='utf8') as f:
            template = f.read()

        content = ''


        if len(self.streaks) > 0:
            content += '<h2>**Streaks**</h2>'
            content += '<table style="font-size: 18px;"  class="dataframe table table-striped table-hover table-bordered table-responsive">'
            for habit, streak, tier in self.streaks:
                content += f'''
                <tr>
                    <td><b>{habit}</b></td>
                    <td style="text-align:left">{streak} days   {tier}</td>
                </tr>
                '''
            content += '</table>'
            content += '<hr>'


        if len(self.neg_streaks) > 0:
            content += '<div class=".text-danger">'
            content += '<h2>!!Negative Streaks!!</h2>'
            content += '<table style="font-size: 18px;"  class="dataframe table table-striped table-hover table-bordered table-responsive">'
            for habit, streak, tier in self.neg_streaks:
                content += f'''
                <tr>
                    <td><b>{habit}</b></td>
                    <td style="text-align:left">-{streak} days   {tier}</td>
                </tr>
                '''
            content += '</table>'
            content += '</div>'
            content += '<hr>'

        content += '<h2>Habit - Last 7 Days</h2>'

        # content += self.bars_week[["Habit","Sum", "Percent","Bars"]].to_html(
        #                         classes='table table-striped table-hover table-bordered table-responsive', 
        #                         index=False,
        #                         border=0
        #                         )
        # content += self.bars_week[["Habit","Sum"]].to_html(
        #                         classes='table table-striped table-hover table-bordered table-responsive', 
        #                         index=False,
        #                         border=0
        #                         )


        content += self.table_style(self.data_week_summary)
        content += '<hr>'
        temp = self.table_style(self.data_week)
        temp = temp.replace('>-1</td>'," style=\"background-color:#ff4d4d;color:white;\">-1</td>")
        temp = temp.replace('>0</td>',"  style=\"background-color:#eeeeee;color:black;\">0</td>")
        temp = temp.replace('>1</td>',"  style=\"background-color:#4dff88;color:black;\">1</td>")

        content += temp
        content += '<hr>'

        content += '<h2>Habit - All Data</h2>'
        # content += self.bars_year[["Habit","Sum", "Percent","Bars"]].to_html(
        #                         classes='table table-striped table-hover table-bordered table-responsive', 
        #                         index=False,
        #                         border=0
        #                         )
        # content += self.bars_year[["Habit","Sum"]].to_html(
        #                         classes='table table-striped table-hover table-bordered table-responsive', 
        #                         index=False,
        #                         border=0
        #                         )

        content += self.table_style(self.data_summary)
        content += '<hr>'
        temp = self.table_style(self.data)

        temp = temp.replace('>-1</td>'," style=\"background-color:#ff4d4d;color:white;\">-1</td>")
        temp = temp.replace('>0</td>',"  style=\"background-color:#eeeeee;color:black;\">0</td>")
        temp = temp.replace('>1</td>',"  style=\"background-color:#4dff88;color:black;\">1</td>")

        content += temp
        content += '<hr>'

        message = template.replace('{{content}}', content)
        return message

    def send_email(self):
        
        today = datetime.datetime.now().strftime("%Y.%m.%d")

        em = EmailMessage()
        em['From'] = self.config.data["from_email"]
        em['To'] = ",".join(self.config.data["to_emails"])
        em['Subject'] = self.config.data["email_subject"].replace("YYYY.MM.DD", today)

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
    
