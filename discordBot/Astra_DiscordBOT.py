#!/usr/bin/env python3

import hashlib
import json
import os
import shutil
import uuid
from time import sleep
import discord
import requests
from datetime import datetime
from pathlib import Path
from threading import Thread, Lock
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration / Setup
SHOPPY_API_KEY = os.getenv('SHOPPY_API_KEY')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID', '0')) # Change to your server ID
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', '0')) # Change to your log channel ID in your server

DATABASE_FILE = Path('database.json')
WHITELIST_FILE = Path('WhitelistsSerialNumbers.txt')

DB_BACKUPS = Path('db_backups')
DB_BACKUPS.mkdir(exist_ok=True)

WHITELIST_BACKUPS = Path('whitelist_backups')
WHITELIST_BACKUPS.mkdir(exist_ok=True)

IMAGES_DIR = Path('images')
IMAGES_DIR.mkdir(exist_ok=True)

WHITELIST_UPDATE_COOLDOWN = 5  # days
REQUEST_TIMEOUT = 15  # seconds
ROLE_NAME = "Astra"

# Simple lock to avoid DB write races between thread and commands
DB_LOCK = Lock()

# Discord Bot Setup
intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix='$', case_insensitive=True, intents=intents)
client.remove_command('help')


def now_ts():
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def load_database():
    """Load DB safely. Returns [] if missing/invalid."""
    try:
        with DB_LOCK:
            if not DATABASE_FILE.exists():
                return []
            with open(DATABASE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"DB load error: {e}")
        return []


def update_database(db_json: list):
    """Write DB atomically-ish with a lock."""
    try:
        with DB_LOCK:
            with open(DATABASE_FILE, "w") as outfile:
                json.dump(db_json, outfile, indent=4)
    except Exception as e:
        print(f"DB write error: {e}")

def generate_whitelist(json_list: list):
    """(Re)build the whitelist file from DB entries."""
    timestamp = now_ts()

    try:
        if WHITELIST_FILE.exists():
            shutil.copyfile(WHITELIST_FILE, WHITELIST_BACKUPS / f"{WHITELIST_FILE.name}.{timestamp}.backup")

        with open(WHITELIST_FILE, "w") as out:
            for entry in json_list:
                key = entry['details'].get('whitelist_key')
                if key:
                    line = f"{hashlib.sha256(str(entry['id']).encode()).hexdigest()}:{key}\n"
                    out.write(line)

        web_dir = "/var/www/html/whitelists"
        if os.path.exists(web_dir):
            shutil.copyfile(WHITELIST_FILE, f"{web_dir}/digits.txt")
        else:
            raise RuntimeError("Web server is not set up! Missing /var/www/html/whitelists directory")

    except Exception as e:
        print(f"Whitelist generation error: {e}")


@client.event
async def on_ready():
    """Event triggered when bot is ready."""
    print(f'Logged in as {client.user}')
    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Astra | $help (DMs)"
        )
    )


@client.command()
@commands.dm_only()
async def help(ctx):
    """Display help information."""
    help_text = """What could I help you with?
---------
(DO THIS ONE FIRST)
$buyer (shoppy.gg order-id) | ex: $buyer 8418f3a1-3fcd-46de-ba92-f5b6ce5ccdac
```css
You can get your ORDER ID by checking the emails of the email you used to purchase Astra.
```"""

    await ctx.send(help_text)
    await ctx.send(file=discord.File('ExampeOrderID.png'))
    
    whitelist_text = """(DO THIS ONE SECOND)
$whitelist (whitelist_code) | ex: $whitelist 00000000-0000-0000-0000-000000000000
```css
You can get your whitelist code by running Whitelist.exe in the Astra download.
```
https://i.gyazo.com/b9dfe1427b900e6f0f52d382b0d32859.mp4"""
    
    await ctx.send(whitelist_text)


@client.command()
@commands.dm_only()
async def buyer(ctx, order_id):
    """Handle buyer role assignment."""
    await ctx.send("Checking for your order... (might take up to **10 minutes** to appear valid!)")
    await ctx.send(file=discord.File('Loading.gif'))
    
    server = client.get_guild(GUILD_ID)
    channel = client.get_channel(LOG_CHANNEL_ID)
    user_id = ctx.message.author.id
    role = discord.utils.get(server.roles, name=ROLE_NAME)
    member = server.get_member(user_id)
    
    try:
        print(f"User {member.id} is trying to redeem buyer role for: `{order_id}`")
    except:
        print(f"User {user_id} is trying to redeem buyer role for: `{order_id}`")
    
    if len(order_id) != 36:
        await ctx.send("Invalid order ID, if you think this is a mistake, please contact support :no_entry_sign:")
        await ctx.send(file=discord.File('ExampeOrderID.png'))
        return
    
    # Load database
    db_json = load_database()
    
    order_found = False
    for entry in db_json:
        if order_id == entry['details']['order_id']:
            order_found = True
            
            # Check if order is already claimed by this user
            if entry['details']['discordID'] == str(user_id):
                try:
                    await member.add_roles(role)
                    await ctx.send("Congrats, you should now have your role again! :white_check_mark:")
                    await channel.send(f"User <@{user_id}> (`{user_id}`) SUCCESSFULLY RE-CLAIMED buyer role for order ID: `{order_id}`! :white_check_mark:")
                except Exception as error:
                    await ctx.send("You are not in the Astra server. Make sure to join the server to re-claim your role. :no_entry_sign:")
                    await channel.send(f"User <@{user_id}> (`{user_id}`) TRIED to RECLAIM buyer role for order ID: `{order_id}` but is not in the server! :no_entry_sign:")
            
            # Check if order is already claimed by someone else
            elif entry['details']['discordID'] != "":
                await ctx.send("This order ID is already being used! :no_entry_sign:")
                await channel.send(f"User <@{user_id}> (`{user_id}`) TRIED to claim buyer role for order ID: `{order_id}` but it is already taken :no_entry_sign:")
            
            # Claim the order
            else:
                await ctx.send("Updating database...")
                entry['details']['discordID'] = str(user_id)
                
                try:
                    await member.add_roles(role)
                    update_database(db_json)
                    await channel.send(f"User <@{user_id}> (`{user_id}`) SUCCESSFULLY claimed buyer role for order ID: `{order_id}`! :white_check_mark:")
                    await ctx.send("Congrats, you should now have access to `#astra-updates`, head over there for the download, make sure to read the README file in the download! :tada: :white_check_mark:")
                    await ctx.send(f"Your Buyer ID is: `{entry['id']}` (DO NOT FORGET THIS, YOU WILL NEED TO PUT IT IN ASTRA_SETTINGS.ini which can be found in the download! :warning:)")
                except Exception as error:
                    await ctx.send("You are not in the Astra server. Make sure to join the server to claim your role. :no_entry_sign:")
                    await channel.send(f"User <@{user_id}> (`{user_id}`) TRIED to claim buyer role for order ID: `{order_id}` but is not in the server! :no_entry_sign:")
            break
    
    if not order_found:
        await ctx.send("Invalid order ID, if you think this is a mistake, please contact support :no_entry_sign:")
        await ctx.send(file=discord.File('ExampeOrderID.png'))
        await channel.send(f"User <@{user_id}> (`{user_id}`) TRIED to claim buyer role for order ID: `{order_id}` but it doesn't exist :no_entry_sign:")


@client.command()
@commands.dm_only()
async def whitelist(ctx, whitelist_key):
    """Handle whitelisting process."""
    await ctx.send("Whitelisting you...")
    await ctx.send(file=discord.File('Loading.gif'))
    
    server = client.get_guild(GUILD_ID)
    user_id = ctx.message.author.id
    channel = client.get_channel(LOG_CHANNEL_ID)
    member = server.get_member(user_id)
    
    if len(whitelist_key) != 36:
        print(f"Invalid whitelist format: {whitelist_key}")
        await ctx.send("This whitelist code is invalid, make sure it looks like a UUID (36 chars). :no_entry_sign:")
        await ctx.send(file=discord.File(IMAGES_DIR / 'ExampleOrderID.png'))
        return
    
    print(f"User {member.id} is trying to whitelist key: `{whitelist_key}`")
    
    # Load database
    db_json = load_database()
    
    user_found = False
    for entry in db_json:
        if str(member.id) == entry['details']['discordID']:
            user_found = True
            print("User owns a whitelist!")
            
            old_host_key = entry['details'].get('host_key', '')
            
            # First time whitelisting
            if not entry['details']['last_update']:
                entry['details']['host_key'] = whitelist_key
                entry['details']['whitelist_key'] = hashlib.sha256(whitelist_key.encode()).hexdigest()
                entry['details']['last_update'] = now_ts()
                
                update_database(db_json)
                generate_whitelist(db_json)
                
                await channel.send(f"User <@{user_id}> (`{user_id}`) SUCCESSFULLY set their whitelist to `{whitelist_key}` :computer: :wrench:")
                await ctx.send(f"Congrats, your whitelist has successfully been set to `{whitelist_key}` :tada: :white_check_mark:")
            
            # Update existing whitelist
            else:
                now = datetime.now()
                past = datetime.strptime(entry['details']['last_update'], '%Y%m%d_%H%M%S')
                time_diff = now - past
                
                if time_diff.days < WHITELIST_UPDATE_COOLDOWN:
                    await ctx.send("Whitelist changed too recently, you must wait before trying to update your whitelist :alarm_clock:")
                    await channel.send(f"User <@{user_id}> (`{user_id}`) tried to change their whitelist from `{old_host_key}` → `{whitelist_key}` but has changed it too recently :alarm_clock:")
                else:
                    entry['details']['host_key'] = whitelist_key
                    entry['details']['whitelist_key'] = hashlib.sha256(whitelist_key.encode()).hexdigest()
                    entry['details']['last_update'] = now_ts()
                    
                    update_database(db_json)
                    generate_whitelist(db_json)
                    
                    if old_host_key == "":
                        old_host_key = " "
                    
                    await channel.send(f"User <@{user_id}> (`{user_id}`) SUCCESSFULLY changed their whitelist from `{old_host_key}` → `{whitelist_key}` :computer: :wrench:")
                    await ctx.send(f"Congrats, your whitelist has successfully been changed from `{old_host_key}` → `{whitelist_key}` :tada: :white_check_mark:")
            break
    
    if not user_found:
        await ctx.send("You are not a registered buyer! If you think this is a mistake, make sure that you have done $buyer command beforehand (If you need help do $help) :warning:")


@client.event
async def on_message(message: discord.Message):
    """Handle direct messages."""
    if message.guild is None and not message.author.bot:
        print(f"{message.channel}: {message.author}: {message.author.name}: {message.content}")
        ctx = await client.get_context(message)
        if ctx.valid:
            await client.process_commands(message)
        else:
            await ctx.send("Hello! How may I help you? :sunglasses:\nType $help to get you started!")


def get_served_orders(db_file):
    """Load existing orders from database."""
    try:
        with DB_LOCK:
            with open(db_file, 'r') as database_file:
                served_orders = json.load(database_file)
        print(f'Number of already served orders: {len(served_orders)}')
        return served_orders
    except FileNotFoundError:
        print('Database file not found; starting with empty list')
        return []
    except Exception as e:
        print(f'DB read error: {e}')
        return []


def get_all_orders():
    """Fetch all orders from Shoppy API."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
        "Authorization": SHOPPY_API_KEY,
        "Content-type": "application/json",
        "Connection": "keep-alive"
    }
    
    json_list = []
    page_num = 0
    
    with requests.Session() as session:
        while True:
            page_num += 1
            sleep(2.5)
            
            try:
                response = session.get(
                    f"https://shoppy.gg/api/v1/orders/?page={page_num}",
                    headers=headers,
                    allow_redirects=False,
                    timeout=REQUEST_TIMEOUT
                )
                print(f'Parsing API page number: {page_num}')
                if response.status_code != 200:
                    print(f"API non-200 ({response.status_code})")
                    break
                try:
                    output = response.json()
                except Exception:
                    output = json.loads(response.content or b"[]")

                if not output:
                    print("Empty page")
                    break

                for order in output:
                    if order.get("paid_at"):
                        order_data = {
                            'order_id': order['id'],
                            'email': order['email'],
                            'purchase_date': order['paid_at']
                        }
                        json_list.append(order_data)
                        
            except Exception as error:
                print(f"API Error: {error}")
                sleep(60)
                break
    
    return json_list


def compare_orders(orders_all, orders_served, db_file_in, db_file_out):
    """Compare and update orders in database."""
    orders_served_updated = orders_served.copy()
    new_orders = []
    
    if orders_served:
        max_id = max([entry["id"] for entry in orders_served])
    else:
        max_id = 0
    
    print(f'Max ID: {max_id}')
    
    for order in orders_all:
        order_exists = any(
            order['order_id'] == served['details']['order_id']
            for served in orders_served
        )
        
        if not order_exists:
            max_id += 1
            print("=" * 60)
            print(f'New order from Shoppy: {order}')
            
            new_order = {
                'id': max_id,
                'details': {
                    'order_id': order['order_id'],
                    'email': order['email'],
                    'purchase_date': order["purchase_date"],
                    'discordID': "",
                    'host_key': "",
                    'whitelist_key': "",
                    'last_update': ""
                }
            }
            
            print(f'New order to insert: {new_order}')
            new_orders.append(new_order)
            orders_served_updated.append(new_order)
    
    if new_orders:
        # Backup + write with a lock
        timestamp = now_ts()
        try:
            with DB_LOCK:
                if Path(db_file_in).exists():
                    shutil.copyfile(db_file_in, DB_BACKUPS / f"{db_file_in}.{timestamp}.backup")

                print("#" * 90)
                print(f'The {len(new_orders)} new orders will be inserted:\n')
                for new_order in new_orders:
                    print(new_order)

                with open(db_file_out, 'w') as new_file:
                    json.dump(orders_served_updated, new_file, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"DB compare/write error: {e}")


def order_monitoring_loop():
    """Main order monitoring loop."""
    while True:
        try:
            orders_served = get_served_orders(DATABASE_FILE)
            orders_all = get_all_orders()
            
            if not orders_all:
                print("No orders returned from API!")
            else:
                compare_orders(orders_all, orders_served, DATABASE_FILE, DATABASE_FILE)
                print('Checking again in 6 minutes!')
            
            sleep(360)  # 6 minutes
        except Exception as e:
            print(f"Error in order monitoring loop: {e}")
            sleep(60)


def thread_monitor():
    """Monitor and restart the order checking thread if needed."""
    order_checker = Thread(target=order_monitoring_loop, daemon=True)
    order_checker.start()
    
    while True:
        print("Starting thread checker...")
        sleep(10)
        
        try:
            status = order_checker.is_alive()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            print(f"{timestamp} Thread Status: {status}")
            
            if not status:
                print("THREAD DIED, RESTARTING IN 6 MINUTES!")
                sleep(360)
                print("RESTARTING ORDER MONITORING THREAD...")
                order_checker = Thread(target=order_monitoring_loop, daemon=True)
                order_checker.start()
            else:
                print("Thread Status: Everything is fine")
                
        except Exception as error:
            print(f"Thread Checker Error: {error}")
        
        sleep(350)


if __name__ == "__main__":
    missing = []

    if not DISCORD_TOKEN:
        missing.append("DISCORD_TOKEN")
    if not SHOPPY_API_KEY:
        missing.append("SHOPPY_API_KEY")

    if missing:
        print(f"Error: {', '.join(missing)} {'is' if len(missing)==1 else 'are'} not set")
        exit(1)
    else:
        print("All environment variables are set, starting Astra BOT...")
        thread_monitor_thread = Thread(target=thread_monitor, daemon=True)
        thread_monitor_thread.start()
        client.run(DISCORD_TOKEN)
