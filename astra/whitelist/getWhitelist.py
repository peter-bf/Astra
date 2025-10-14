import sys, subprocess, uuid, re
from typing import Optional
from colorama import init, Fore

init(convert=True, autoreset=True)

def _is_uuid(s: str) -> bool:
    try:
        uuid.UUID(s)
        return True
    except Exception:
        return False

def _try_powershell_uuid() -> Optional[str]:
    cmd = ["powershell", "-NoProfile", "-Command",
           "(Get-CimInstance -Class Win32_ComputerSystemProduct).UUID"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        s = r.stdout.strip()
        return s if r.returncode == 0 and _is_uuid(s) else None
    except Exception:
        return None

def _try_wmic_uuid() -> Optional[str]:
    try:
        r = subprocess.run(["wmic", "csproduct", "get", "uuid"],
                           capture_output=True, text=True, encoding="utf-16le", timeout=5)
        m = re.search(r"(?i)uuid\s*\r?\n\s*([0-9a-fA-F-]{36})", r.stdout or "")
        s = m.group(1) if m else None
        return s if s and _is_uuid(s) else None
    except Exception:
        return None

def get_windows_uuid() -> Optional[str]:
    return _try_powershell_uuid() or _try_wmic_uuid()

def main() -> int:
    print(f"{Fore.GREEN}[>] Starting whitelisting process...\n")
    uid = get_windows_uuid()
    if not uid:
        print(f"{Fore.RED}[!] Could not determine machine UUID. [Windows only]")
        print(f"{Fore.YELLOW}[!] If this persists, please contact support.")
        return 1
    print(
        # f"{Fore.GREEN}[+] Your whitelist code is: {uid}\n\n"
        f"{Fore.GREEN}[>] UUID found!\n"
        f"{Fore.GREEN}[+] Please DM Astra BOT on Discord the following command:\n"
        f"{Fore.YELLOW}$whitelist {uid}\n\n"
        # f"{Fore.YELLOW}[!] (You can change your whitelisted machine every {Fore.RED}5 days!)"
    )
    if sys.stdin.isatty():
        input(f"{Fore.YELLOW}[>] Press Enter to exit...")
    return 0

if __name__ == "__main__":
    sys.exit(main())
