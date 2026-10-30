"""
单仓库按年月范围生成贡献图。
- 起止年月使用 YYYYMM，包含首尾月份。
- 所有 commit 追加到 contribution_art，每个月完成后推送一次。
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
            print("不能为空，请重新输入！")
            continue
        try:
            return cast(value)
        except ValueError:
            print("格式无效，请重新输入！")


def parse_month(value):
    if len(value) != 6 or not value.isascii() or not value.isdigit():
        raise ValueError("年月必须为六位 YYYYMM")
    return datetime.strptime(value, "%Y%m")


def run_cmd(cmd, cwd, env=None):
    try:
        subprocess.run(cmd, cwd=cwd, check=True, shell=True,
                       text=True, capture_output=True, encoding="utf-8", env=env)
        return True
    except subprocess.CalledProcessError as error:
        logging.error(f"命令失败: {cmd}\n{error.stderr}")
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
        sys.stdout.write(f"\r{year}-{month:02d}: {percent:5.1f}% ({day_index}/{days})  提交 #{counter}")
        sys.stdout.flush()

    print()
    logging.info(f"{year}-{month:02d} 完成，新增 {counter - initial_counter} 次提交。")
    if push_monthly and counter > initial_counter:
        if not run_cmd("git push -u origin main", repo_path):
            logging.error(f"{year}-{month:02d} 推送失败，停止后续月份。")
            return False
        logging.info(f"{year}-{month:02d} 已推送至 GitHub。")
    return True


def main():
    logging.basicConfig(level=logging.INFO,
                        format="[%(levelname)s] %(message)s",
                        stream=sys.stdout)

    print("=== 单仓库贡献图（按年月范围生成）===")
    user_name = ask("Git 用户名", default="username")
    user_email = ask("Git 邮箱", default="user@mail.com")
    start_month = ask("起始年月（YYYYMM）", cast=parse_month)
    end_month = ask("结束年月（YYYYMM）", cast=parse_month)
    remote_url = ask("GitHub 仓库地址 (https/ssh)", default="https://github.com/username/project_name")

    if start_month > end_month:
        print("\033[31m起始年月必须小于等于结束年月！\033[0m")
        sys.exit(1)
    if start_month.year < 2008 or end_month.year < 2008:
        print("\033[31m年份不可早于 2008 年！\033[0m")
        sys.exit(1)

    repo_path = os.path.abspath(REPO_NAME)
    if os.path.exists(repo_path):
        if not is_git_repo(repo_path):
            logging.error(f"{repo_path} 已存在但不是 Git 仓库！")
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
                logging.error("远程仓库或分支设置失败，终止。")
                sys.exit(1)

    for month_index in range(start_month.year * 12 + start_month.month - 1,
                             end_month.year * 12 + end_month.month):
        year, month_offset = divmod(month_index, 12)
        month = month_offset + 1
        if not build_month_in_repo(year, month, repo_path, user_name, user_email, push_monthly):
            logging.error(f"{year}-{month:02d} 处理失败，终止。")
            sys.exit(1)

    print("\n\033[32m所选月份已追加到同一仓库！\033[0m")
    print(f"目录：{repo_path}")
    if push_monthly:
        print("\033[32m已按月推送至 GitHub！\033[0m")
    else:
        print("\033[33m未提供仓库地址，请稍后手动推送！\033[0m")


if __name__ == "__main__":
    main()