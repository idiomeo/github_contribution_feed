"""
run.py  —— 单仓库多年份贡献图（1 月 1 日起始）
- 每年 365/366 天，不再 371 天
- 所有 commit 追加到同一个目录 contribution_art
"""

import os
import sys
import random
import shutil
import subprocess
import logging
import calendar
from datetime import datetime, timedelta

REPO_NAME = "contribution_art"          # 固定仓库名
WEIGHTS = (30, 20, 15, 15, 5)         # 0-4 权重
LEVELS = {"0": 0, "1": 1, "2": 5, "3": 10, "4": 20}

# ------------------ 工具 ------------------
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

def run_cmd(cmd, cwd, env=None):
    try:
        subprocess.run(cmd, cwd=cwd, check=True, shell=True,
                       text=True, capture_output=True, encoding="utf-8", env=env)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"命令失败: {cmd}\n{e.stderr}")
        return False

def is_git_repo(path):
    return run_cmd("git rev-parse --is-inside-work-tree", path)

# ------------------ 核心 ------------------
def generate_pattern(days):
    """生成长度为 days 的随机级别序列 0-4"""
    rng = random.SystemRandom()
    population = [0, 1, 2, 3, 4]
    return rng.choices(population, weights=WEIGHTS, k=days)

def build_year_in_repo(year, repo_path, user_name, user_email):
    """为某一年追加 commit（1 月 1 日开始）"""
    days = 366 if calendar.isleap(year) else 365
    pattern = generate_pattern(days)

    readme_path = os.path.join(repo_path, "README.md")
    counter = 0
    if os.path.isfile(readme_path):
        import re
        with open(readme_path, encoding="utf-8") as f:
            m = re.findall(r"Commit #(\d+)", f.read())
            counter = int(m[-1]) if m else 0

    start_date = datetime(year, 1, 1)

    for idx, level in enumerate(pattern, 1):
        commits = LEVELS.get(str(level), 0)
        if commits <= 0:
            continue
        cur_date = start_date + timedelta(days=idx - 1)
        for _ in range(commits):
            counter += 1
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(f"Commit #{counter} on {cur_date.date()}\n")
            if not run_cmd("git add README.md", repo_path):
                return False
            env = os.environ.copy()
            env.update({
                "GIT_AUTHOR_DATE": cur_date.isoformat(),
                "GIT_COMMITTER_DATE": cur_date.isoformat(),
            })
            if not run_cmd(f'git commit -m "feat: commit #{counter}"',
                           repo_path, env):
                return False

        # 进度条
        perc = idx / days * 100
        sys.stdout.write(f"\r{year}: {perc:5.1f}% ({idx}/{days})  提交 #{counter}")
        sys.stdout.flush()
    print()
    logging.info(f"{year} 年追加完成，仓库共 {counter} 次提交。")
    return True

# ------------------ 主流程 ------------------
def main():
    logging.basicConfig(level=logging.INFO,
                        format="[%(levelname)s] %(message)s",
                        stream=sys.stdout)

    print("=== 单仓库多年份贡献图（1 月 1 日起始）===")
    user_name = ask("Git 用户名", default="username")
    user_email = ask("Git 邮箱", default="user@mail.com")
    start_year = ask("起始年份", cast=int)
    end_year = ask("结束年份", cast=int)
    remote_url  = ask("GitHub 仓库地址 (https/ssh)", default="https://github.com/username/project_name")

    if start_year > end_year:
        print("\033[31m起始年份必须小于等于结束年份！\033[0m")
        print("\033[31m请重新启动脚本\033[0m")
        sys.exit(1)

    if start_year < 2008 or end_year < 2008:
        print("\033[31m⚠️  GitHub 成立于 2008 年 2 月，"
            "早于 2008 年的贡献伪造有可能被官方封禁！\033[0m")
        print("\033[31m请重新启动脚本\033[0m")
        sys.exit(1)

    

    

    repo_path = os.path.abspath(REPO_NAME)

    # 初始化或更新仓库
    if os.path.exists(repo_path):
        if not is_git_repo(repo_path):
            logging.error(f"{repo_path} 已存在但不是 Git 仓库！")
            sys.exit(1)
        if not run_cmd("git pull --rebase", repo_path):
            sys.exit(1)
    else:
        os.makedirs(repo_path, exist_ok=True)
        cmds = ("git init",
                f'git config user.name "{user_name}"',
                f'git config user.email "{user_email}"')
        for cmd in cmds:
            if not run_cmd(cmd, repo_path):
                sys.exit(1)

    # 逐年追加
    for year in range(start_year, end_year + 1):
        if not build_year_in_repo(year, repo_path, user_name, user_email):
            logging.error(f"{year} 年处理失败，终止。")
            sys.exit(1)

    print("\n\033[32m🎉 全部年份已追加到同一仓库！\033[0m")
    print(f"目录：{repo_path}")

    if remote_url.strip():                       # 用户给了地址才 push
        print("正在自动推送至Github ...")
        cmds = [
            f"git remote get-url origin || git remote add origin {remote_url}",
            "git branch -M main",
            "git push -u origin main"
        ]
        for cmd in cmds:
            if not run_cmd(cmd, repo_path):
                logging.error("自动推送失败，请手动处理！")
                sys.exit(1)
        print("\033[32m已成功推送至 GitHub！\033[0m")
    else:
        print("\033[33m未提供仓库地址，请稍后手动推送！\033[0m")


if __name__ == "__main__":
    main()