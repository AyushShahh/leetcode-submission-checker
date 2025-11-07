# leetcode-submission-checker
Selenium based LeetCode submission checker which checks if the submissions by usernames are valid.

You will need to download Selenium, gspread and oauth2client. Also you will need the sheets api credentials `.json` file. This requires you to have a spreadsheet which has usernames to check. You should have a `.json` file having key as the leetcode username and value as the row number of the username in the spreadsheet. Also we had a question for each day to check so we had day number as column.
