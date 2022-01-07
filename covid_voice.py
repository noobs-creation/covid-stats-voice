from logging import captureWarnings
import requests
import json
import threading
import time

class CovidStats:
	
	def __init__(self, api_key, project_token):
		self.api_key = api_key
		self.project_token = project_token
		self.params = {
			"api_key": self.api_key
		}
		self.json_data = self.fetch_stats()

	# getting the whole json data from ParseHub
	def fetch_stats(self):
		res = requests.get(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/last_ready_run/data', params=self.params)
		data = json.loads(res.text)
		return data

	# returns the total number of cases worldwide
	def fetch_worldwide_cases(self):
		fetched_data = self.json_data['total']

		for data in fetched_data:
			if data['name'] == "Coronavirus Cases:":
				return data['value']
		
		return "0"

	# returns the total number of deaths worldwide
	def fetch_worldwide_deaths(self):
		fetched_data = self.json_data['total']

		for data in fetched_data:
			if data['name'] == "Deaths:":
				return data['value']

		return "0"

	# returns the total number of recoveries worldwide
	def fetch_worldwide_recoveries(self):
		fetched_data = self.json_data['total']

		for data in fetched_data:
			if data['name'] == "Recovered:":
				return data['value']
		
		return "0"
 
	# returns all stats country wise
	def fetch_country_stats(self, country):
		fetched_country_data = self.json_data["country"]

		for data in fetched_country_data:
			if data['name'].lower() == country.lower():
				return data

		return "0"

	# returns the list of countries under observation
	def get_list_of_countries(self):
		countries = []
		for country in self.json_data['country']:
			countries.append(country['name'].lower())

		return countries

	# updates the data when called
	def update_data(self):
		
		def poll():
			time.sleep(0.3)
			old_json_data = self.json_data
			while True:
				new_json_data = self.fetch_stats()
				if new_json_data != old_json_data:
					self.json_data = new_json_data
					print("JSON data updated!")
					break
				time.sleep(5)


		t = threading.Thread(target=poll)
		t.start()


# Loading credentials
import os
from dotenv import load_dotenv
load_dotenv('.env')

# Getting credentials from .env file
API_KEY = os.getenv("API_KEY")
PROJECT_TOKEN = os.getenv("PROJECT_TOKEN")
RUN_TOKEN = os.getenv("RUN_TOKEN")

# Testing the ParseHub API
# response = requests.get(f'https://www.parsehub.com/api/v2/projects/{PROJECT_TOKEN}/last_ready_run/data', params={"api_key":API_KEY})
# print(response)
# data = json.loads(response.text)
# print(data)

import pyttsx3
import speech_recognition as sr
import re

# Making the voice engine
def speak(text):
	engine = pyttsx3.init()
	engine.say(text)
	engine.runAndWait()

# Listening to the microphone for commands
def get_command():
	r = sr.Recognizer()
	with sr.Microphone() as source:
		captured_audio = r.listen(source)
		recognized_text = ""

		try:
			recognized_text = r.recognize_google(captured_audio)
		except Exception as e:
			print(e)
			speak("Sorry, I didn't get that")

	return recognized_text.lower()


covid_stats = CovidStats(API_KEY, PROJECT_TOKEN)

fetched_country_list = covid_stats.get_list_of_countries()

END_PHRASE = "stop"

TOTAL_PATTERNS = {
				re.compile("[\w\s]+ total [\w\s]+ cases"):covid_stats.fetch_total_cases_worldwide,
				re.compile("[\w\s]+ total cases"): covid_stats.fetch_total_cases_worldwide,
                re.compile("[\w\s]+ total [\w\s]+ deaths"): covid_stats.fetch_total_deaths_worldwide,
                re.compile("[\w\s]+ total deaths"): covid_stats.fetch_total_deaths_worldwide,
                re.compile("[\w\s]+ total [\w\s]+ recoveries"): covid_stats.fetch_total_recoveries_worldwide,
                re.compile("[\w\s]+ total recoveries"): covid_stats.fetch_total_recoveries_worldwide,
				re.compile("[\w\s]+ total [\w\s]+ recovery"): covid_stats.fetch_total_recoveries_worldwide,
                re.compile("[\w\s]+ total recovery"): covid_stats.fetch_total_recoveries_worldwide
				}

COUNTRY_PATTERNS = {
                re.compile("[\w\s]+ recoveries [\w\s]+"): lambda country: covid_stats.get_country_data(country)['total_recoveries'],
				re.compile("[\w\s]+ recovery [\w\s]+"): lambda country: covid_stats.get_country_data(country)['total_recoveries'],
                re.compile("[\w\s]+ population [\w\s]+"): lambda country: covid_stats.get_country_data(country)['total_population'],
				re.compile("[\w\s]+ cases [\w\s]+"): lambda country: covid_stats.get_country_data(country)['total_cases'],
                re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: covid_stats.get_country_data(country)['total_deaths'],
				}

UPDATE_COMMAND = "update"

while True:
	print("Listening...")
	recognized_text = get_command()
	print(recognized_text)

	result = None
	
	for pattern, func in COUNTRY_PATTERNS.items():
		if pattern.match(recognized_text):
			words = set(recognized_text.split(" "))
			for country in fetched_country_list:
				if country in words:
					result = func(country)
					break
	
	for pattern, func in TOTAL_PATTERNS.items():
		if pattern.match(recognized_text):
			result = func()
			break
	
	if recognized_text == UPDATE_COMMAND:
		result = "Data is being updated. This may take a moment!"
		covid_stats.update_data()
	if result:
		speak(result)
	if recognized_text.find(END_PHRASE) != -1:  # stop loop
		print("Exit")
		break