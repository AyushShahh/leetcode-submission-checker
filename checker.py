import re
import json
import os
from dotenv import load_dotenv
load_dotenv()

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import gspread
from oauth2client.service_account import ServiceAccountCredentials


class Checker:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument(f"user-data-dir={os.getenv('CHROME_USER_DATA_DIR')}")
        self.options.add_argument(f"profile-directory={os.getenv('CHROME_PROFILE')}")
        self.driver = webdriver.Chrome(options=self.options)

    def check_question(self, url):
        self.driver.get(url)
        try:
            # accepted_element = WebDriverWait(self.driver, 15).until(
            #     EC.presence_of_element_located((By.XPATH, '//span[@data-e2e-locator="submission-result"]'))
            # )
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, '//span[@data-e2e-locator="submission-result"]'))
            )
            profile_link = self.driver.find_element(By.XPATH, '//a[@href and contains(@href, "/u/")]')
            return profile_link.get_attribute('href').replace('https://leetcode.com/u/', '')
            # img_element = profile_link.find_element(By.TAG_NAME, 'img')
            # print(accepted_element.text, profile_link.get_attribute('href').replace('https://leetcode.com/u/', ''), img_element.get_attribute('alt'))
        except (TimeoutException, Exception):
            return None

    @staticmethod
    def check_submission_url(url):
        pattern = r"https:\/\/leetcode\.com\/problems\/[\w-]+\/submissions\/\d+\/?"
        return bool(re.fullmatch(pattern, url))

    def close(self):
        self.driver.close()

    def initialize_google_sheets(self):
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(os.getenv('CREDENTIALS'), scope)
        self.client = gspread.authorize(creds)
        self.tracker = self.client.open("track")

        with open("usernames.json", "r") as file:
            self.usernames = json.load(file)

        print("Initialized google sheets")

    def check_week(self, week):
        self.initialize_google_sheets()

        self.track = self.tracker.worksheet(f"Week {week}")
        self.week = self.client.open(f"Week {week} submissions (Responses)").sheet1
        record = dict()

        print("Initialized week and track sheets")

        self.log = open(f"week{week}.log", 'a')

        data = self.week.get_all_records()
        print("Got records")
        
        for i, row in enumerate(data):
            day, url, name = row['Question'].split('-')[0].rstrip(), row['Submission link for the selection question'], row['Full name']

            if day not in record:
                record[day] = set()

            if not self.check_submission_url(url):
                self.reject(i, name, "Invalid url")
                continue
            
            if username := self.check_question(url):
                if username not in self.usernames:
                    self.reject(i, name, "Username not in record")
                    continue
                if username not in record[day]:
                    self.track.update_cell(self.usernames[username], self.track.find(day).col, 'Yes')
                    record[day].add(username)
                    print(f"Accepted record at index {i}")

        # self.track.update_cell(0 + 2, self.track.find('Day 1').col, 'Yes')
        # print(*[row['Submission link for the selection question'] for row in data], sep="\n")
        self.log.close()

    def reject(self, row, name, message):
        self.log.write(f"{message}: row {row+2}, name: {name}\n")
    