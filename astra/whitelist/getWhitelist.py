import subprocess, sys
from time import sleep
from typing import Optional
from colorama import init, Fore, Back, Style
init(convert=True)
import re, uuid

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

data = get_windows_uuid()
print(f'{Fore.YELLOW}[●] Starting whitelisting process...\n')
print(f"{Fore.GREEN}Your whitelist code is: {data}\n{Fore.YELLOW}[●] Please DM Astra BOT on Discord with the following line to whitelist this machine:\n{Fore.GREEN}$whitelist {data}\n{Fore.RED}(Be careful, you can only change your whitelisted machine every 5 days!)")
sleep(500)
sys.exit()