import requests
from time import sleep
import os
import hashlib
import uuid
import subprocess
from typing import Optional
from datetime import datetime, timezone
import json
import re
from configparser import ConfigParser
from colorama import init, Fore

version = "3_04"  # TODO: Bump to 4_00 when 4.0 is ready
rolimons_url = "https://www.rolimons.com/itemapi/itemdetails"
inifile = 'Astra_Settings.ini'

# Sensitive endpoints and secrets are configurable via environment variables
# If not provided, whitelist/version checks will be skipped gracefully
whitelistlink = os.getenv('ASTRA_WHITELIST_URL')
version_link = os.getenv('ASTRA_VERSION_URL')
ENV_COOKIE = os.getenv('ASTRA_ROBLOX_COOKIE')
ENV_WEBHOOK = os.getenv('ASTRA_WEBHOOK_URL')
ENV_BUYER_ID = os.getenv('ASTRA_BUYER_ID')

#Colorama initialization
init(convert=True)
clock = ['-','\\','|','/']
class Astra:
	def get_settings():
		try:
			g = open(inifile,'r')
			g.close()
		except:
			print(f"{Fore.RED}	[!] CRITICAL ERROR: File {inifile} is missing!")
			print(f"{Fore.RED}	[!] Exiting in 60 seconds...{Fore.RESET}")
			sleep(60)
			os._exit(1)
		else:
			config = ConfigParser()
			config.read(inifile)
			try:
				class settings():
					# Allow env vars to override INI values for sensitive data
					Cookie = str(ENV_COOKIE or config['ASTRA SETTINGS']['Cookie'])
					Webhook_url = str(ENV_WEBHOOK or config['ASTRA SETTINGS']['Webhook'])
					Value_Check_Cooldown = config['ASTRA SETTINGS']['Value_Check_Cooldown']
					Outbound_settings = config['OUTBOUND CHECKER SETTINGS']
					Automatic_Outbound_Scan = Outbound_settings['Automatic_Outbound_Scan']
					Outbound_Automatic_Scan_Cooldown = Outbound_settings['Outbound_Automatic_Scan_Cooldown']
					Ratelimit_Timer = Outbound_settings['Ratelimit_Retry_Cooldown']
					Outbound_Scan_Type = Outbound_settings['Outbound_Scan_Type']
					Outbound_Tolerance_RAP = Outbound_settings['Outbound_Tolerance_RAP_Amount']
					Outbound_Tolerance_Value = Outbound_settings['Outbound_Tolerance_Value_Percent']
					Outbound_Cancel_Equals = Outbound_settings['Outbound_Cancel_Equals']
					BuyerID = str(ENV_BUYER_ID or config['ASTRA SETTINGS']['Buyer_ID'])
			except Exception as settings_error:
				print(f"{Fore.RED}[!] Your Astra_Settings.ini file is missing a line! Exiting in 60 seconds... [{settings_error}]{Fore.RESET}")
				sleep(60)
				os._exit(1)
			try:
				if int(settings.Ratelimit_Timer) < 60:
					print(f"{Fore.YELLOW}	[O] 'Ratelimit_Retry_Cooldown' is not recommended to be set to under 60 and may cause worse performance...{Fore.RESET}")
				if settings.Outbound_Scan_Type not in ['rap', 'value', 'both']:
					print(f"{Fore.RED}	[!] Make sure 'Outbound_Scan_Type' is set to either: rap, value, or both")
					print(f"{Fore.RED}	[!] Exiting in 60 seconds...")
					sleep(60)
					os._exit(1)
				try:
					if int(settings.BuyerID) == 0:
						print(f"{Fore.RED}	[!] CRITICAL ERROR: Make sure you put your BuyerID in Astra_Settings.ini!\n	[!] You should have gotten your BuyerID the first time you did $buyer command with Astra BOT on Discord.\n	[!] Exiting in 60 seconds...{Fore.RESET}")
						sleep(60)
						os._exit(1)
				except:
					print(f"{Fore.RED}	[!] CRITICAL ERROR: You put your SHOPPY-ID instead of BUYER ID!\n	[!] Your Buyer ID is a small number that AstraBOT#1030 (Discord Bot) should have given you ($buyer command)\n	(the number should not be over 3 digits!)\n	[!] Exiting in 60 seconds...{Fore.RESET}")
					sleep(60)
					os._exit(1)
				if int(settings.Value_Check_Cooldown) < 180:
					settings.Value_Check_Cooldown = 180
					print(f"{Fore.YELLOW}	[O] 'Value_Check_Cooldown' is too low, setting it too 180 seconds instead...{Fore.RESET}")
				if int(settings.Outbound_Automatic_Scan_Cooldown) < 600:
					print(f"{Fore.YELLOW}	[O] 'Outbound_Automatic_Scan_Cooldown' is TOO low. Reverting it to 4200 would be a good idea.{Fore.RESET}")
				return settings
			except Exception as error:
				print(f"{Fore.RED}	[!] An error occured: [{error}]")
				print(f"{Fore.RED}	[!] Exiting in 60 seconds... [{error}]")
				sleep(60)
				os._exit(1)
	def get_HWID() -> Optional[str]:
		try:
			txt = subprocess.check_output("wmic csproduct get uuid").decode()
			match = re.search(r"\bUUID\b[\s\r\n]+([^\s\r\n]+)", txt)
			if match is not None:
				txt = match.group(1)
				if txt is not None:
					txt = re.sub(r"[^0-9A-Fa-f]+", "", txt)
					if len(txt) == 32:
						return str(uuid.UUID(txt))
		except:
			pass
		return None

	def get_url(url, site, max_tries, timer):
		for i in range(max_tries):
			try:
				output=requests.get(url)
			except:
				print(f'{Fore.RED}[!] ASTRA: Failed to connect to {site}! Retrying in {timer} seconds...')
				sleep(timer)
				continue
			else:
				return output
		print(f"{Fore.RED}[!] ASTRA CRITICAL ERROR: Could not connect with {site}! Exiting in 10 seconds...")
		sleep(10)
		os._exit(1) 
	def check_uuid():
		if not whitelistlink:
			print(f"{Fore.YELLOW}\t[O] Whitelist URL not configured; skipping whitelist check.")
			return
		f = Astra.get_url(whitelistlink, "[Whitelist Authenticator]", 4, 60)
		info = f.text
		lines = info.splitlines()
		whitelisted = False
		try:
			unhashed = Astra.get_HWID()
			print(f"{Fore.GREEN}\t[-] HWID: {unhashed}")
			for line in lines:
				if re.match(r'^\s*$', line):
					continue
				line = line.strip('\n')
				array = line.split(':')
				ids = array[0]
				whitelists = array[1]
				hashed_buyer = hashlib.sha256(settings.BuyerID.encode()).hexdigest()
				myuuid = hashlib.sha256(unhashed.encode()).hexdigest()
				if myuuid == whitelists and hashed_buyer == ids:
					whitelisted = True
			if not whitelisted:
				print(f"{Fore.RED}\t[!] Whitelist not found! Check BUYER_ID and whitelist settings. Exiting in 60 seconds...{Fore.RESET}")
				sleep(60)
				os._exit(1)
		except Exception as error:  
			print(f'{Fore.RED}\t[!] {error}{Fore.RESET}')
			print(f"{Fore.RED}\t[!] Exiting in 60 seconds...{Fore.RESET}")
			sleep(60)
			os._exit(1)
	def get_version():
		if not version_link:
			return None
		f = Astra.get_url(version_link, "[Version Authenticator]", 4, 60)
		info = f.text
		latest_version = info.split('\r\n')[0]
		return latest_version
	def readvalues(filename):
		print(f'{Fore.GREEN}[-] Opening file: {filename}...{Fore.RESET}')
		try:
			f = open(filename,'r')
		except:
			print(f"{Fore.RED}[!] CRITICAL ERROR: File '{filename}' is missing!")
			print(f"{Fore.RED}[!] Exiting in 60 seconds...{Fore.RESET}")
			sleep(60)
			os._exit(1)
		else:
			lines = f.readlines()[2:]
			f.close()
			return lines
	def get_token():
		cookie = {".ROBLOSECURITY": settings.Cookie}
		headers = {"X-CSRF-TOKEN":""}
		x = requests.post('https://auth.roblox.com/v2/login', headers=headers, cookies=cookie, allow_redirects=False)
		return x.headers["X-CSRF-TOKEN"]
	def initialize():
		os.system('cls')
		print(f'\r{Fore.YELLOW}[O] Initializing Astra...', end=" ")
		sleep(1.0)
		os.system('cls')
		print(f'\r{Fore.GREEN}[+] Initialized Astra!')
		latest_version = Astra.get_version()
		if latest_version and version != latest_version:
			print(f"{Fore.YELLOW}	[O] Update found! Please download the newest version in the Astra discord!{Fore.RESET}")
			sleep(60)
			os._exit(1)
		else:
			print(f"{Fore.GREEN}	[-] Version: {version}")
		global settings
		settings = Astra.get_settings()
		print(f"{Fore.GREEN}	[-] BuyerID: {settings.BuyerID}")
		Astra.check_uuid()
		global token
		token = Astra.get_token()
	def send_post(url):
		cookie = {".ROBLOSECURITY": settings.Cookie}
		headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36", "X-CSRF-TOKEN":token}
		r = requests.post(url, allow_redirects=False, headers=headers)
		return r.content
	def get_limiteds(userid):
		their_owned_items = []
		nextPageCursor = ""
		while nextPageCursor is not None:
			collectible_list = Astra.get_url(f'https://inventory.roblox.com/v1/users/{userid}/assets/collectibles?limit=100&cursor={nextPageCursor}', '[ROBLOX API Services]', 4, 10).json()
			nextPageCursor = collectible_list['nextPageCursor']
			for entry in collectible_list['data']:
				their_owned_items.append(entry['assetId'])
		return their_owned_items
	def scan_cache():
		current = datetime.now(timezone.utc)
		items_dict = {}
		old_trades = []
		no_longer_owned_trades = []
		now_unprofitable = {}
		with open('Cache.json') as json_file:
			try:
				cache = json.load(json_file)
				print(f'{Fore.GREEN}	[-] Cached trades: {len(cache)}')
			except:
				print(f'{Fore.GREEN}	[-] There is no cache to read from. Creating file...')
				return
		cookie = {".ROBLOSECURITY": settings.Cookie}
		headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36", "X-CSRF-TOKEN":token}
		checkedpage_api = False
		print(f'{Fore.GREEN}[-] Fetching account info...{Fore.RESET}')
		while not checkedpage_api:
			mobileapi = requests.get('https://www.roblox.com/mobileapi/userinfo', cookies=cookie, headers=headers)
			if mobileapi.status_code == 200:
				checkedpage_api = True
			else:
				sleep(1)
		if '"UserName":' not in mobileapi.text:
			print(f'{Fore.RED}[!] Account cookie is invalid or expired!{Fore.RESET}')
			sleep(60)
			os._exit(1)
		mobileapi_json = mobileapi.json()
		selfuid = mobileapi_json['UserID']
		nextPageCursor = ""
		owned_items = []
		while nextPageCursor is not None:
			checkedpage = False
			while not checkedpage:
				collectible_list = requests.get(f'https://inventory.roblox.com/v1/users/{selfuid}/assets/collectibles?limit=100&cursor={nextPageCursor}')
				if collectible_list.status_code == 200:
					checkedpage = True
					collectible_list_json = collectible_list.json()
					nextPageCursor = collectible_list_json['nextPageCursor']
					for entry in collectible_list_json['data']:
						owned_items.append(entry['assetId'])
		print(f'{Fore.GREEN}[-] Scanning cached trades...')
		api_result = json.loads(Astra.get_url(rolimons_url, "Rolimons", 4,60).text)
		item_values = {}
		item_rap = {}
		values_file = Astra.readvalues('values')
		for line in values_file:
			line = line.strip('\n')
			array = line.split(':')
			item_ID = array[0]
			value_in_file = array[1]
			itemname = api_result['items'][item_ID][0]
			item_values[item_ID] = value_in_file
			item_rap[item_ID] = api_result['items'][item_ID][2]
		for i in cache:
			tradeId = i['tradeID']
			theirID = i['theirID']
			# Parse ISO8601 timestamp; assume UTC if no offset
			try:
				expire_dt = datetime.fromisoformat(i['expire_date'])
			except Exception:
				try:
					expire_dt = datetime.strptime(i['expire_date'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
				except Exception:
					continue
			if current > expire_dt.astimezone(timezone.utc):
				old_trades.append(tradeId)
				#cache.remove(i)
			else:
				#Now scan for un-owned trades:
				owned = True
				for x in i['your_items']:
					if x not in owned_items:
						owned = False
				if owned:
					if theirID in items_dict.keys():
						for x in i['their_items']:
							if x not in list(items_dict[theirID]):
								owned = False
						#print(items_dict)
						#print("USED CACHED THEIR ITEM LIST")
					else:
						their_stuff = Astra.get_limiteds(i['theirID'])
						for x in i['their_items']:
							if x not in their_stuff:
								owned = False
								items_dict.update({theirID: their_stuff})
						#print("CACHING NOW!")
				if not owned:
					no_longer_owned_trades.append(tradeId)
				else:
					your_items = {}
					your_asset_ids = []
					their_items = {}
					their_asset_ids = []
					global value_loss, rap_loss, your_value, their_value, your_rap, their_rap
					your_value = 0
					your_rap = 0
					their_value = 0
					their_rap = 0
					value_loss = False
					rap_loss = False
					#print(item_values)
					for asset in i['your_items']:
						assetID = asset['assetId']
						your_items.update({f"{asset['name']} [{asset['id']}]": [int(item_values[str(assetID)]), item_rap[str(assetID)]]})
						your_asset_ids.append(assetID)
					for asset in i['their_items']:
						assetID = asset['assetId']
						their_items.update({f"{asset['name']} [{asset['id']}]": [int(item_values[str(assetID)]), item_rap[str(assetID)]]})
						their_asset_ids.append(assetID)
					for i in list(your_items.values()):
						your_value += i[0]
					for i in list(their_items.values()):
						their_value += i[0]
					for i in list(your_items.values()):
						your_rap += i[1]
					for i in list(their_items.values()):
						their_rap += i[1]
					if your_value > their_value:
						value_loss = True
					if your_rap > their_rap:
						rap_loss = True
					cancelled = False
					if settings.Outbound_Scan_Type.lower() == "both":
						if value_loss or rap_loss:
							while not cancelled:
								try:
									Astra.send_post(f"https://trades.roblox.com/v1/trades/{tradeId}/decline")
									cancelled = True
								except:
									print(f'{Fore.RED}[!] Could not cancel trade! Trying again in 60 seconds...{Fore.RESET}')
									cancelled = False
									sleep(60)
							now_unprofitable[tradeId] = ["both", your_rap-their_rap]
							Astra.send_webhook(0, 0, "both")
					else:
						if value_loss or rap_loss:
							# CHECKING LOSS TYPE
							if settings.Outbound_Scan_Type.lower() == "rap":
								now_unprofitable[tradeId] = ["rap", your_rap-their_rap]
							if settings.Outbound_Scan_Type.lower() == "value":
								now_unprofitable[tradeId] = ["value", your_rap-their_rap]
		print(f'{Fore.GREEN}[-] Found {len(old_trades)} expired trades to cancel!')
		#print(old_trades)
		print(f'{Fore.GREEN}[-] Found {len(no_longer_owned_trades)} trades that contained no-longer owned items.{Fore.RESET}')
		#print(no_longer_owned_trades)
		for i in cache[:]:
			if i['tradeID'] in old_trades or no_longer_owned_trades:
				cache.remove(i)
		with open ('Cache.json', 'w') as newfile:
			json.dump(cache, newfile, ensure_ascii=False, indent=4)
	def send_webhook(yours, theirs, type_of_loss):
		if settings.Outbound_Scan_Type == "both":
			if rap_loss and value_loss:
				info = {
				"content": "",
				"embeds": [
					{
					"title": "Astra has cancelled a non-profitable trade!",
					"color": 5832549,
					"fields": [
						{
						"name": "Your Value:",
						"value": f"{your_value}",
						"inline": 'true'
						},
						{
						"name": "Their Value:",
						"value": f"{their_value}",
						"inline": 'true'
						},
						{
						"name": "Value saved:",
						"value": f"{your_value-their_value}"
						},
						{
						"name": "Your RAP:",
						"value": f"{your_rap}",
						"inline": 'true'
						},
						{
						"name": "Their RAP:",
						"value": f"{their_rap}",
						"inline": 'true'
						},
						{
						"name": "RAP saved:",
						"value": f"{your_rap-their_rap}"
						}
					],
					"author": {
						"name": "Trade Cancelled"
					},
					"thumbnail": {
						"url": "https://i.imgur.com/nhsuFHL.png"
					}
					}
				],
				"username": "Astra",
				"avatar_url": "https://i.imgur.com/nhsuFHL.png"
				}
			else:
				if rap_loss:
					info = {
						"content": "",
						"embeds": [
							{
							  "title": "Astra has cancelled a non-profitable trade!",
							  "color": 5832549,
							  "fields": [
								{
								  "name": f"Your RAP:",
								  "value": f"{your_rap}",
								  "inline": 'true'
								},
								{
								  "name": f"Their RAP:",
								  "value": f"{their_rap}",
								  "inline": 'true'
								},
								{
								  "name": f"RAP saved:",
								  "value": f"{your_rap-their_rap}"
								}
							  ],
							  "author": {
								"name": "Trade Cancelled"
							  },
							  "thumbnail": {
								"url": "https://i.imgur.com/nhsuFHL.png"
							  }
							}
					  ],
					  "username": "Astra",
					  "avatar_url": "https://i.imgur.com/nhsuFHL.png"
					}
				if value_loss:
					info = {
						"content": "",
						"embeds": [
							{
							  "title": "Astra has cancelled a non-profitable trade!",
							  "color": 5832549,
							  "fields": [
								{
								  "name": f"Your Value:",
								  "value": f"{your_value}",
								  "inline": 'true'
								},
								{
								  "name": f"Their Value:",
								  "value": f"{their_value}",
								  "inline": 'true'
								},
								{
								  "name": f"Value saved:",
								  "value": f"{your_value-their_value}"
								}
							  ],
							  "author": {
								"name": "Trade Cancelled"
							  },
							  "thumbnail": {
								"url": "https://i.imgur.com/nhsuFHL.png"
							  }
							}
					  ],
					  "username": "Astra",
					  "avatar_url": "https://i.imgurimgur.com/nhsuFHL.png"
					}
		else:
			info = {
				"content": "",
				"embeds": [
					{
					  "title": "Astra has cancelled a non-profitable trade!",
					  "color": 5832549,
					  "fields": [
						{
						  "name": f"Your {type_of_loss}:",
						  "value": f"{yours}",
						  "inline": 'true'
						},
						{
						  "name": f"Their {type_of_loss}:",
						  "value": f"{theirs}",
						  "inline": 'true'
						},
						{
						  "name": f"{type_of_loss} saved:",
						  "value": f"{yours-theirs}"
						}
					  ],
					  "author": {
						"name": "Trade Cancelled"
					  },
					  "thumbnail": {
						"url": "https://i.imgur.com/nhsuFHL.png"
					  }
					}
			  ],
			  "username": "Astra",
			  "avatar_url": "https://i.imgur.com/nhsuFHL.png"
			}
		if getattr(settings, 'Webhook_url', None):
			try:
				requests.post(settings.Webhook_url, json=info)
			except:
				print(f"{Fore.YELLOW} [O] Could not send to webhook. Check ASTRA_WEBHOOK_URL or INI settings.{Fore.RESET}")
		else:
			print(f"{Fore.YELLOW} [O] Webhook URL not configured; skipping webhook send.{Fore.RESET}")
	def scan_outbounds():
		file = open('ExampleTrade.json')
		page_100 = json.loads(file.read())
		values_file = Astra.readvalues('values')
		api_result = json.loads(Astra.get_url(rolimons_url, "Rolimons", 4,60).text)
		item_values = {}
		item_rap = {}
		for line in values_file:
			line = line.strip('\n')
			array = line.split(':')
			item_ID = array[0]
			value_in_file = array[1]
			itemname = api_result['items'][item_ID][0]
			item_values[item_ID] = value_in_file
			item_rap[item_ID] = api_result['items'][item_ID][2]
		tradeID = page_100['id']
		print(f"{Fore.GREEN}[-] Scanning trade: {tradeID}")
		your_items = {}
		your_asset_ids = []
		their_items = {}
		their_asset_ids = []
		global value_loss, rap_loss, your_value, their_value, your_rap, their_rap
		your_value = 0
		your_rap = 0
		their_value = 0
		their_rap = 0
		value_loss = False
		rap_loss = False
		for asset in page_100['offers'][0]['userAssets']:
			assetID = asset['assetId']
			your_items.update({f"{asset['name']} [{asset['id']}]": [int(item_values[str(assetID)]), item_rap[str(assetID)]]})
			your_asset_ids.append(assetID)
		for asset in page_100['offers'][1]['userAssets']:
			assetID = asset['assetId']
			their_items.update({f"{asset['name']} [{asset['id']}]": [int(item_values[str(assetID)]), item_rap[str(assetID)]]})
			their_asset_ids.append(assetID)
		for i in list(your_items.values()):
			your_value += i[0]
		for i in list(their_items.values()):
			their_value += i[0]
		for i in list(your_items.values()):
			your_rap += i[1]
		for i in list(their_items.values()):
			their_rap += i[1]
		if your_value > their_value:
			value_loss = True
		if your_rap > their_rap:
			rap_loss = True
		cancelled = False
		if settings.Outbound_Scan_Type.lower() == "both":
			if value_loss or rap_loss:
				while not cancelled:
					try:
						Astra.send_post(f"https://trades.roblox.com/v1/trades/{tradeID}/decline")
						cancelled = True
					except:
						print(f'{Fore.RED}[!] Could not cancel trade! Trying again in 60 seconds...{Fore.RESET}')
						cancelled = False
						sleep(60)
				Astra.send_webhook(0, 0, "both")
		else:
			if value_loss or rap_loss:
				if settings.Outbound_Scan_Type.lower() == "rap":
					print(f"{Fore.YELLOW}[-] {page_100['id']}: CANCELLING {your_rap-their_rap} RAP LOSS")
					while not cancelled:
						try:
							Astra.send_post(f"https://trades.roblox.com/v1/trades/{tradeID}/decline")
							cancelled = True
						except:
							print(f'{Fore.RED}[!] Could not cancel trade! Trying again in 60 seconds...{Fore.RESET}')
							cancelled = False
							sleep(60)
					Astra.send_webhook(your_rap, their_rap, "Rap")
				if settings.Outbound_Scan_Type.lower() == "value":
					print(f"{Fore.YELLOW}[-] {page_100['id']}: CANCELLING {your_value-their_items} VALUE LOSS")
					while not cancelled:
						try:
							Astra.send_post(f"https://trades.roblox.com/v1/trades/{tradeID}/decline")
							cancelled = True
						except:
							print(f'{Fore.RED}[!] Could not cancel trade! Trying again in 60 seconds...{Fore.RESET}')
							cancelled = False
							sleep(60)
					Astra.send_webhook(your_value, their_value, "Value")
		if not value_loss or rap_loss:
			with open('Cache.json') as json_file:
				try:
					cache = json.load(json_file)
				except:
					cache = []
		# Use ISO8601 with timezone (replace Z with +00:00)
		expire = datetime.fromisoformat(page_100['expiration'].replace('Z', '+00:00'))
		cache_format = {
			"expire_date": expire.isoformat(),
			"cancelled": False,
			"tradeID": f"{tradeID}",
			"yourID": f"{page_100['offers'][0]['user']['id']}",
			"theirID": f"{page_100['offers'][1]['user']['id']}",
			"your_items": your_asset_ids,
			"their_items": their_asset_ids
			}
		cache.append(cache_format)
		with open ('Cache.json', 'w') as newfile:
			json.dump(cache, newfile, ensure_ascii=False, indent=4)


Astra.initialize()
Astra.scan_cache()
Astra.scan_outbounds()
