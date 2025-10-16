#!/usr/bin/env python3

#    _       _             
#   /_\  ___| |_ _ __ __ _ 
#  //_\\/ __| __| '__/ _` |
# /  _  \__ \ |_| | | (_| |
# \_/ \_/___/\__|_|  \__,_|

# Astra - Roblox Trade Value Monitor, Outbound Checker, and more.             

import requests
from colorama import init, Fore
init(convert=True)
import json
import sys
from time import sleep
from typing import Optional
import re
import uuid
import subprocess
import datetime
from configparser import ConfigParser
import os
import hashlib
import psutil

if getattr(sys, 'frozen', False):
    _base_dir = os.path.dirname(sys.executable)
else:
    _base_dir = os.path.dirname(os.path.abspath(__file__))
inifile = os.path.join(_base_dir, 'Astra_Settings.ini')
values = os.path.join(_base_dir, 'values')
rolimons_url = "https://www.rolimons.com/itemapi/itemdetails"

# Sensitive endpoints are configured via environment variables. If unset some checks are skipped
whitelistlink = os.getenv('ASTRA_WHITELIST_URL')
version_link = os.getenv('ASTRA_VERSION_URL')
version = "3_04"
settings = {}
op = {}

def get_settings():
	try:
		g = open(inifile,'r')
		g.close()
	except:
		print(f"{Fore.RED}[!] ASTRA CRITICAL ERROR: File {inifile} is missing!")
		print(Fore.YELLOW+"[●] Closing Astra..."+Fore.RESET)
		sleep(40)
		sys.exit()
	else:
		global config
		config = ConfigParser()
		config.read(inifile)
		global Value_Check_Cooldown
		global outbound_settings
		global Automatic_Outbound_Scan
		global Outbound_Scan_Type_Rap_OR_Both_Cooldown
		global Outbound_Loss_Tolerance_Type 
		global Outbound_Scan_Type
		global Outbound_Loss_Tolerance_Rap
		global Outbound_Loss_Tolerance_Value
		global BuyerID
		global Outbound_Cancel_Equals
		try:
			Value_Check_Cooldown = config['ASTRA SETTINGS']['Value_Check_Cooldown']
			outbound_settings = config['OUTBOUND CHECKER SETTINGS']
			Automatic_Outbound_Scan = outbound_settings['Automatic_Outbound_Scan']
			Outbound_Scan_Type_Rap_OR_Both_Cooldown = outbound_settings['Outbound_Scan_Type_Rap_OR_Both_Cooldown']
			Outbound_Loss_Tolerance_Type = outbound_settings['Outbound_Loss_Tolerance_Type']
			Outbound_Loss_Tolerance_Rap = outbound_settings['Outbound_Loss_Tolerance_Rap_Amount']
			Outbound_Loss_Tolerance_Value = outbound_settings['Outbound_Loss_Tolerance_Value_Percent']
			Outbound_Scan_Type = outbound_settings['Outbound_Scan_Type']
			BuyerID = config['ASTRA SETTINGS']['Buyer_ID']
		except Exception as settings_error:
			print(f"{Fore.RED}Your Astra_Settings.ini file is missing a line!")
			print(f"Error code: {settings_error}")
			print(f"Make sure your Astra_Settings.ini file is from the latest version... Exiting Astra...{Fore.RESET}")
			sleep(40)
			sys.exit()
		#print(BuyerID)
		try:
			if int(BuyerID) == 0:
				print(Fore.RED+"[!] Astra: Make sure you put your BuyerID in Astra_Settings.ini! You should have gotten your BuyerID when you did the $buyer command with Astra BOT for the first time.")
				sleep(40)
				sys.exit()
		except:
			print(f"{Fore.RED}[!] ASTRA CRITICAL ERROR: You put your SHOPPY ID instead of BUYER ID! Your Buyer ID is a small number that Astra Bot (discord bot) should have given you when you did the $buyer command! (the number should not be over 3 digits!)")
			sleep(60)
			sys.exit()
		if int(Value_Check_Cooldown) < 180:
			Value_Check_Cooldown = 180
			print(Fore.YELLOW+"[●] Value_Check_Cooldown is too low, setting it too 180 seconds instead...")
		if int(Outbound_Scan_Type_Rap_OR_Both_Cooldown) < 3600:
			Outbound_Scan_Type_Rap_OR_Both_Cooldown = 3600
			print(Fore.YELLOW+"[●] Outbound_Scan_Type_Rap_OR_Both_Cooldown is too low, setting it too 3600 seconds instead...")

def get_windows_uuid() -> Optional[uuid.UUID]:
	try:
		txt = subprocess.check_output("wmic csproduct get uuid").decode()
		match = re.search(r"\bUUID\b[\s\r\n]+([^\s\r\n]+)", txt)
		if match is not None:
			txt = match.group(1)
			if txt is not None:
				txt = re.sub(r"[^0-9A-Fa-f]+", "", txt)
				if len(txt) == 32:
					return uuid.UUID(txt)
	except:
		pass
	return None

def get_url(url,site, max_tries, timer):
	#print(f"{url},{site}, {max_tries}, {timer}")
	for i in range(max_tries):
		try:
			output=requests.get(url)
		except:
			print(f'{Fore.RED}[!] Failed to connect to {site}! Will retry connecting in {timer} seconds...')
			sleep(timer)
			continue
		else:
			return output
	print(f"{Fore.RED}[!] ASTRA CRITICAL ERROR: Could not connect with {site}!")
	print("[!] Closing the outbound checker..."+Fore.RESET)
	sys.exit() 

#CHECK WHITELISTS:
def check_uuid():
	if not whitelistlink:
		print(f"{Fore.YELLOW}[?] Whitelist URL not configured; skipping whitelist check.")
		return
	f=get_url(whitelistlink, "Whitelist authenticator",4,60)
	info = f.text
	lines = info.splitlines()
	whitelisted = False
	try:
		for line in lines:
			if re.match(r'^\s*$', line):
				continue
			line = line.strip('\n')
			array = line.split(':')
			ids = array[0]
			whitelists = array[1]
			unhashed = str(get_windows_uuid())
			hashed_buyer = hashlib.sha256(BuyerID.encode()).hexdigest()
			myuuid = hashlib.sha256(unhashed.encode()).hexdigest()
			if myuuid == whitelists and hashed_buyer == ids:
				whitelisted = True
		if whitelisted:
			print(Fore.GREEN+"[$] Whitelist found!"+Fore.RESET)
			print(f'''{Fore.GREEN}
               _			 
     /\	      | |			
    /  \   ___| |_ _ __ __ _ 
   / /\ \ / __| __| '__/ _` |
  / ____ \\\__ \ |_| | | (_| |
 /_/	\_\___/\__|_|  \__,_|
							 
							 ''')
		else:
			print(f"{Fore.RED}[!] Whitelist not found. Exiting the program...\n(Make sure your BuyerID in Astra_Settings.ini is correct and that this machine is whitelisted) (DM Pepe#8230 if something is wrong){Fore.RESET}")
			sleep(40)
			sys.exit()
	except Exception as error:  
		print(f'{Fore.RED}[!] {error}{Fore.RESET}')

def get_version():
	if not version_link:
		return
	f = get_url(version_link, "Version authenticator",4,60)
	info = f.text
	latest_version = info.split('\r\n')[0]
	if version != latest_version:
		print(Fore.YELLOW+"[●] Update found! Please download the newest version in the Astra discord!"+Fore.RESET)
		sleep(40)
		sys.exit()

def readvalues(filename):
	print(f'{Fore.GREEN}ASTRA: Reading file: "{filename}"...{Fore.RESET}')
	try:
		f = open(values,'r')
	except:
		print(f"{Fore.RED}[!] ASTRA CRITICAL ERROR: File '{filename}' is missing!")
		print(Fore.YELLOW+"[●] Closing the outbound checker..."+Fore.RESET)
		sleep(30)
		sys.exit()
	else:
		lines = f.readlines()[2:]
		f.close()
		return lines

def update_valuefile_from_api (valuefile,api_result):
	start_time=datetime.datetime.utcnow()
	changed_status = 'no'
	value_lines = readvalues(valuefile)
	print(f'{Fore.GREEN}ASTRA: {len(value_lines)} lines read.{Fore.RESET}')
	print(f'{Fore.GREEN}ASTRA: Updating file: "{valuefile}"...{Fore.RESET}')
	new_values=[]
	new_values.append("old")
	new_values.append("")
	for line in value_lines:
		line = line.strip('\n')
		array = line.split(':')
		ID = array[0]
		value_in_file = array[1]
		itemname = api_result['items'][ID][0]
		rap = api_result['items'][ID][2]
		value_in_api = api_result['items'][ID][3]
		if array[3] == "9999999999" and value_in_api == -1:
			print(f"{Fore.YELLOW}Detected de-valued item: ID: {ID}  Name: {itemname}.  Removing from {valuefile}...{Fore.RESET}")
			changed_status = 'yes'
			continue
		if value_in_api != -1:
			array[3] = 9999999999
			if str(value_in_api) != value_in_file:
				print(f"{Fore.LIGHTMAGENTA_EX}ASTRA: {itemname} has changed values from: {value_in_file} to {value_in_api}{Fore.RESET}")
				array[1] = value_in_api
				changed_status = 'yes'
		newline = ':'.join(map(str, array))
		new_values.append(newline)
	try:
		item_num = (len(new_values)) -2
		f = open(valuefile,'w')
		f.write('\n'.join(new_values))
		f.close()
		print(f'{Fore.GREEN}ASTRA: {item_num} lines written.{Fore.RESET}')
		end_time=datetime.datetime.utcnow()
		time_taken = end_time-start_time
		print(Fore.GREEN+"ASTRA: Any value changes: "+changed_status+Fore.RESET)
		print(Fore.GREEN+"ASTRA: Time taken to update "+valuefile+": "+str(time_taken)+Fore.RESET)
	except Exception as error:  
		print(f'{Fore.RED}[!] {error}{Fore.RESET}')
		print(f"{Fore.RED}[!] ASTRA CRITICAL ERROR: Could not update '{valuefile}'!")
		print(Fore.YELLOW+"[●] Closing Astra..."+Fore.RESET)
		sleep(40)
		sys.exit()
	return changed_status


def suddenchange():
	print(Fore.GREEN+"ASTRA: Starting in sudden change mode...")
	sleep(1)
	last_outbound=datetime.datetime.utcnow()
	outbound_time_diff=0
	value_lines = readvalues('values')  # Just a quick test if values file exist
	if Automatic_Outbound_Scan.lower() != "true":
		values_change_status=update_valuefile_from_api('values',json.loads(get_url(rolimons_url, "Rolimons", 4,60).text))
		print(Fore.GREEN+"ASTRA: Automatic_Outbound_Scan is not enabled... (not going to scan trades)"+Fore.RESET)
	if Automatic_Outbound_Scan.lower() == "true":
		last_outbound=outbound_launch()
		#print(f'last_outbound: {last_outbound}')
	sleep(10)
	p=olympian_launch()
	while True:
		sleep(int(Value_Check_Cooldown))
		time_now=datetime.datetime.utcnow()
		values_change_status=update_valuefile_from_api('values',json.loads(get_url(rolimons_url, "Rolimons", 4,60).text))
		if values_change_status == 'yes':
			print(Fore.GREEN+"ASTRA: Killing old Olympian process.."+Fore.RESET)
			p.kill()
			sleep(10)
			p=olympian_launch()
			if Automatic_Outbound_Scan.lower() == "true":
				last_outbound=outbound_launch()
			#print(f'{Fore.GREEN}ASTRA: last_outbound: {last_outbound}.{Fore.RESET}\n')
		else:
			print(Fore.GREEN+"ASTRA: New check in "+str(Value_Check_Cooldown)+" seconds..."+Fore.RESET)
			if Automatic_Outbound_Scan.lower() == "true" and (Outbound_Loss_Tolerance_Type.lower() == "rap" or Outbound_Loss_Tolerance_Type.lower() == "both"):
				outbound_time_diff = int((time_now - last_outbound).total_seconds())
				print(f'{Fore.GREEN}ASTRA: Time since last Outbound Checker launch: {outbound_time_diff} seconds.{Fore.RESET}\n')
				if outbound_time_diff >  int(Outbound_Scan_Type_Rap_OR_Both_Cooldown):
					print(f'{Fore.GREEN}ASTRA: Time to lauch Outbound Checker...{Fore.RESET}')
					last_outbound=outbound_launch()
			
def olympian_launch():
	print(Fore.GREEN+"ASTRA: Starting Olympian..."+Fore.RESET)
	try:
		p = subprocess.Popen("olympian", shell=False)
	except:
		print(Fore.RED+"[!] CRITICAL ASTRA ERROR: olympian.exe is missing from the folder, make its not missing or renamed (Anti-Virus might have deleted it!)")
		print(Fore.YELLOW+"[●] Shutting down Astra..."+Fore.RESET)
		sleep(40)
		sys.exit()
	return p


def get_url(url,site, max_tries, timer):
	#print(f"{url},{site}, {max_tries}, {timer}")
	for i in range(max_tries):
		try:
			output=requests.get(url)
		except:
			print(f'{Fore.RED}[!] Failed to connect to {site}! Will retry connecting in {timer} seconds...')
			sleep(timer)
			continue
		else:
			return output
	print(f"{Fore.RED}[!] ASTRA CRITICAL ERROR: Could not connect with {site}!")
	print("[!] Closing the outbound checker..."+Fore.RESET)
	sys.exit() 


def outbound_launch():
	print(f'{Fore.GREEN}ASTRA: Launching Outbound checker...{Fore.RESET}')
	try:
		flag=0
		for process in psutil.process_iter():
			#print(f'Process: {process}')
			if "outboundChecker".lower() in process.name().lower():
				flag=1
		if flag ==1 :
			print(Fore.YELLOW+"[●] An instance of Outbound Checker is already running..."+Fore.RESET)
			print(Fore.YELLOW+"[●] Killing current process..."+Fore.RESET)
			subprocess.call('taskkill /F /IM "outboundChecker.exe"')
			p = subprocess.Popen("outboundChecker", shell=False)
			return datetime.datetime.utcnow()
		else:
			#print(Fore.GREEN+"ASTRA: Launching Outbound checker..."+Fore.RESET)
			p = subprocess.Popen("outboundChecker", shell=False)
			return datetime.datetime.utcnow()
	except Exception as error:  
		print(f'{Fore.RED}[!] {error}{Fore.RESET}')
		print(Fore.RED+"[!] ASTRA CRITICAL ERROR: outboundChecker.exe is missing or renamed, please make sure 'outboundChecker.exe' is still in the folder")
		print(Fore.YELLOW+"[●] Shutting down Astra..."+Fore.RESET)
		sleep(40)
		sys.exit()


# Main programs starts below
unhashed = str(get_windows_uuid())
print("Launching Astra...")
get_version()
get_settings()
check_uuid()
suddenchange()
