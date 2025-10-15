# 🤖 Astra Discord Bot

The **Astra Discord Bot** automates user management, purchase validation, and whitelist synchronization between **Shoppy.gg**, **Astra servers**, and the **Astra Discord community**.

---

## 🧩 Core Functionality

- **Automated Shoppy.gg Integration**  
  Continuously monitors the Shoppy API for new orders and automatically adds new buyers to the Astra database.  
  Each order is assigned a unique internal ID and securely stored with timestamped backups.

- **Discord Role Assignment**  
  Buyers can link their purchase to their Discord account using `$buyer <order_id>`.  
  Once verified, the bot automatically grants the **Astra** role and access to member-only channels.

- **Whitelist Management System**  
  Users can register or update their machine whitelist via `$whitelist <whitelist_code>`.  
  The bot validates the request, enforces cooldowns (default: 5 days), and rebuilds the whitelist file after every valid change.

- **Whitelist Synchronization**  
  After every update, the bot regenerates and uploads the latest whitelist to the Astra server:  
  ```
  /var/www/html/whitelists/digits.txt
  ```  
  ensuring that authorized users are instantly reflected in Astra’s systems.

- **Buyer Assistance via DM Commands**  
  The bot provides step-by-step help in DMs with `$help`, including visuals and examples:  
  - `$buyer` — Claim or re-claim your buyer role.  
  - `$whitelist` — Register or update your whitelist key.  
  - `$help` — Display all available commands and guidance.

- **Database Integrity & Backups**  
  - Maintains JSON-based database (`database.json`) with automatic timestamped backups in `db_backups/`.  
  - Atomic writes protected by threading locks to prevent race conditions between bot commands and background tasks.

- **Automated Thread Monitoring**  
  Runs a continuous background thread that monitors Shoppy orders and restarts automatically if a failure occurs — ensuring 24/7 stability.

- **Logging and Transparency**  
  All major actions are logged in the configured `LOG_CHANNEL_ID` for staff visibility — including successful claims, whitelist changes, and invalid attempts.

---

## ⚙️ Internal Workflow

1. **Shoppy Polling Loop**  
   Every few minutes, the bot fetches new orders and updates the local database.
2. **User Commands (DM Only)**  
   Buyers interact privately via `$buyer`, `$whitelist`, and `$help`.
3. **Database + Whitelist Sync**  
   Each valid update triggers regeneration of:
   - `database.json`
   - `WhitelistsSerialNumbers.txt`
   - `digits.txt` (web sync)
4. **Automatic Cooldown Enforcement**  
   Prevents users from re-whitelisting too frequently by comparing timestamps.
5. **Fail-Safe Thread Watchdog**  
   Detects thread crashes and restarts the monitoring loop autonomously.

---

## 🪄 Highlights

- Full integration between **Astra Discord**, **Astra Server**, and **Shoppy.gg**.
- Handles user verification, whitelist syncing, and access control with minimal manual oversight.
- Built-in resiliency through multi-threaded architecture and watchdog recovery.
- Generates and secures all critical data with timestamped backups.

---

This bot forms the **operational backbone of Astra’s customer and access management**, ensuring a smooth, automated experience from purchase to activation.
