# github_contribution_feed  

[中文](./README.md) | **English**    

**Fill in your past GitHub contribution graph with one click**  
![Show](./picture/show.jpg)

---

## What this project does

This is a lightweight command-line tool that can **fill in missing GitHub contribution records for any year range you specify** in one go (it is not recommended to complete a year that has not yet ended).

**Highlights:**
- Operates on **a single repository only**, and the script automatically performs a `git pull` on that repo before running  
- Starts **January 1st of every year**, commits once per real calendar day (365/366 days), automatically detects leap years  
- Supports multiple runs and incremental appends (it never overwrites existing history)  
- **No temporary files** at any stage, minimizing disk I/O

---

## Getting started

### Prerequisites

- Python ≥ 3.7  
- Git is installed locally and the `git` command is available in your shell  

### 1️⃣ Download the script
```bash
git clone https://github.com/idiomeo/github_contribution_feed.git
cd github_contribution_feed
```

### 2️⃣ Create a new repository  
Create a new repo on GitHub.  
It is best **not** to initialize it with **README**, **.gitignore**, or **License** files, as shown below:  
![Show](./picture/creat_new_repo.png)

The repo can be private.  
If you choose private, you **must** tick **Private Contributions** in your profile’s **Contribution settings**, as shown:  
![Show](./picture/setting_tip.png)

### 3️⃣ One-click run  
Execute in your terminal:
```bash
python main.py
```  


When prompted, enter:
- Git username  
- Git email  
- Start year (cannot be earlier than 2008)  
- End year (cannot be earlier than 2008)  
- GitHub remote URL of the repo you just created  

If you only want to fill in one single year, set **Start year** and **End year** to the same value.

### 4️⃣ Wait for the script to finish  

Since the script needs to repeatedly call `git commit` to fabricate the commit history, you will have to wait for a while (the waiting time is proportional to the length of the chosen year range).  

(If the long runtime makes you worry about security: the entire script is stored in **one single file** containing only **164 lines**, so you can quickly review it at any time—it is **absolutely safe**.)  

When the script finishes, your profile page will be filled with large blocks of green squares!  
![Show](./picture/target_show.png)

---

(Re-running the script on the same repo and same date range will automatically append new commits without overwriting the old ones.)

---  

## Little Surprise & Little Warning  
### Surprise  
If the years you choose to backfill are earlier than your account creation year, you’ll be pleasantly surprised to see those earlier years appear in the year list of your GitHub profile contribution graph.  
(This only affects the earliest year displayed on your profile; your actual account creation date remains unchanged.)

### Warning  
- Do **not** excessively extend the year range shown on your profile, or you risk being banned.  
- The additional years are **permanent and irreversible**—even if you delete the contribution repository, the extra years will still appear on your profile. Think carefully before using this feature.  
- Never add future years (e.g., running the script in 2025 but entering years beyond 2025). Doing so greatly increases the chance of suspension!

---

## Disclaimer
- Usage is governed by the [**GPL 3.0** license](./LICENSE).  
- **GitHub officially prohibits abuse of the contribution graph; using this script may result in account suspension. The author assumes no responsibility for any direct or indirect consequences arising from the use of this script!**

---

**Enjoy your brand-new green wall!**