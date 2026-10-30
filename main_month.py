"""
Single-repository contribution graph for a month range.
- Enter YYYYMM boundaries; both endpoint months are included.
- Append commits to contribution_art and push after each month.
"""

import os
import sys
import random
import subprocess
import logging
import calendar
from datetime import datetime, timedelta

REPO_NAME = "contribution_art"
WEIGHTS = (30, 20, 15, 15, 5)
LEVELS = {"0": 0, "1": 1, "2": 5, "3": 10, "4": 20}


def ask(prompt, default=None, cast=str):
    while True:
        value = input(f"{prompt} [{default}]: ").strip()
        if not value:
            value = default
        if value is None:
            print("Value cannot be empty, please re-enter!")
            continue
        try:
            return cast(value)
        except ValueError:
            print("Invalid format, please re-enter!")


def parse_month(value):
    if len(value) != 6 or not value.isascii() or not value.isdigit():
        raise ValueError("Enter a six-digit month in YYYYMM format")
    return datetime.strptime(value, "%Y%m")


def run_cmd(cmd, cwd, env=None):
    try:
        subprocess.run(cmd, cwd=cwd, check=True, shell=True,
                       text=True, capture_output=True, encoding="utf-8", env=env)
        return True
    except subprocess.CalledProcessError as error:
        logging.error(f"Command failed: {cmd}\n{error.stderr}")
        return False


def is_git_repo(path):
    return run_cmd("git rev-parse --is-inside-work-tree", path)


def generate_pattern(days):
    rng = random.SystemRandom()
    return rng.choices([0, 1, 2, 3, 4], weights=WEIGHTS, k=days)


def build_month_in_repo(year, month, repo_path, user_name, user_email, push_monthly=False):
    days = calendar.monthrange(year, month)[1]
    pattern = generate_pattern(days)
    readme_path = os.path.join(repo_path, "README.md")
    counter = 0
    if os.path.isfile(readme_path):
        import re
        with open(readme_path, encoding="utf-8") as readme:
            matches = re.findall(r"Commit #(\d+)", readme.read())
            counter = int(matches[-1]) if matches else 0

    initial_counter = counter
    start_date = datetime(year, month, 1)
    for day_index, level in enumerate(pattern, 1):
        commits = LEVELS.get(str(level), 0)
        current_date = start_date + timedelta(days=day_index - 1)
        for _ in range(commits):
            counter += 1
            with open(readme_path, "w", encoding="utf-8") as readme:
                readme.write(f"Commit #{counter} on {current_date.date()}\n")
            if not run_cmd("git add README.md", repo_path):
                return False
            env = os.environ.copy()
            env.update({
                "GIT_AUTHOR_DATE": current_date.isoformat(),
                "GIT_COMMITTER_DATE": current_date.isoformat(),
            })
            if not run_cmd(f'git commit -m "feat: commit #{counter}"', repo_path, env):
                return False
        percent = day_index / days * 100
        sys.stdout.write(f"\r{year}-{month:02d}: {percent:5.1f}% ({day_index}/{days})  commit #{counter}")
        sys.stdout.flush()

    print()
    logging.info(f"{year}-{month:02d} completed, added {counter - initial_counter} commits.")
    if push_monthly and counter > initial_counter:
        if not run_cmd("git push -u origin main", repo_path):
            logging.error(f"Push failed for {year}-{month:02d}; stopping subsequent months.")
            return False
        logging.info(f"{year}-{month:02d} pushed to GitHub.")
    return True


def main():
    logging.basicConfig(level=logging.INFO,
                        format="[%(levelname)s] %(message)s",
                        stream=sys.stdout)

    print("=== Single-repo contribution graph (month range) ===")
    user_name = ask("Git username", default="username")
    user_email = ask("Git email", default="user@mail.com")
    start_month = ask("Start month (YYYYMM)", cast=parse_month)
    end_month = ask("End month (YYYYMM)", cast=parse_month)
    remote_url = ask("GitHub repository URL (https/ssh)", default="https://github.com/username/project_name")

    if start_month > end_month:
        print("\033[31mStart month must be less than or equal to end month!\033[0m")
        sys.exit(1)
    if start_month.year < 2008 or end_month.year < 2008:
        print("\033[31mYears before 2008 are not supported!\033[0m")
        sys.exit(1)

    repo_path = os.path.abspath(REPO_NAME)
    if os.path.exists(repo_path):
        if not is_git_repo(repo_path):
            logging.error(f"{repo_path} exists but is not a Git repository!")
            sys.exit(1)
        if not run_cmd("git pull --rebase", repo_path):
            sys.exit(1)
    else:
        os.makedirs(repo_path, exist_ok=True)
        for cmd in ("git init",
                    f'git config user.name "{user_name}"',
                    f'git config user.email "{user_email}"'):
            if not run_cmd(cmd, repo_path):
                sys.exit(1)

    push_monthly = bool(remote_url.strip())
    if push_monthly:
        for cmd in (f"git remote get-url origin || git remote add origin {remote_url}",
                    "git branch -M main"):
            if not run_cmd(cmd, repo_path):
                logging.error("Remote or branch setup failed, aborting.")
                sys.exit(1)

    for month_index in range(start_month.year * 12 + start_month.month - 1,
                             end_month.year * 12 + end_month.month):
        year, month_offset = divmod(month_index, 12)
        month = month_offset + 1
        if not build_month_in_repo(year, month, repo_path, user_name, user_email, push_monthly):
            logging.error(f"Processing {year}-{month:02d} failed, aborting.")
            sys.exit(1)

    print("\n\033[32mSelected months have been appended to the same repository!\033[0m")
    print(f"Directory: {repo_path}")
    if push_monthly:
        print("\033[32mPushed to GitHub month by month!\033[0m")
    else:
        print("\033[33mNo repository URL provided, please push manually later!\033[0m")


if __name__ == "__main__":
    main()