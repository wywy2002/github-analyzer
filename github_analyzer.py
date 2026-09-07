import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

# 冲突合并
API_ROOT = "https://api.github.com"
OUTPUT_DIR = Path("outputs")

# 冲突22
# ---------- API 请求与错误转换 ----------
def request_json(url, timeout=10):
    """请求一个 JSON API，并返回 Python 分支合并。"""

    # 请求头声明期望 GitHub JSON，并为本程序提供可识别的 User-Agent
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "stage-0-github-analyzer",
        },
    )

    try:
        # 使用超时防止网络异常时长时间卡住；离开 with 后连接自动关闭
        with urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except HTTPError as error:
        # 将不同 HTTP 状态码转换成更容易理解的业务错误
        if error.code == 404:
            # from error 保留原始异常链，调试时仍能找到真实原因
            raise ValueError("GitHub 上没有找到该资源") from error
        if error.code == 403:
            raise RuntimeError("请求被拒绝，可能触发了 GitHub API 频率限制") from error
        raise RuntimeError(f"GitHub API 返回 HTTP {error.code}") from error
    except URLError as error:
        raise ConnectionError(f"网络连接失败：{error.reason}") from error
    except TimeoutError as error:
        raise TimeoutError("请求超时，请检查网络后重试") from error
    except json.JSONDecodeError as error:
        raise RuntimeError("服务器返回的内容不是有效 JSON") from error


# ---------- 数据清理与摘要整理 ----------
def normalize_text(value, fallback="未提供"):
    """把 None 或空字符串转成适合展示的文字。"""
    if value is None or value == "":
        return fallback
    return value


def build_user_summary(profile):
    """从完整用户数据中挑选需要展示的字段。"""

    # 必填和计数字段也提供默认值，使字段偶尔缺失时程序仍可展示结果
    return {
        "type": "user",
        "login": profile.get("login"),
        "name": normalize_text(profile.get("name")),
        "company": normalize_text(profile.get("company")),
        "location": normalize_text(profile.get("location")),
        "public_repos": profile.get("public_repos", 0),
        "followers": profile.get("followers", 0),
        "html_url": profile.get("html_url"),
    }

def build_repo_summary(repo):
    """从完整仓库数据中挑选需要展示的字段。"""

    # owner 和 license 本身是嵌套对象，也可能为 None
    # 使用 or {} 后，即使缺失也可以继续安全调用 .get()
    owner = repo.get("owner") or {}
    license_data = repo.get("license") or {}

    # 将 GitHub 字段名转换为程序更容易展示和测试的摘要结构
    return {
        "type": "repository",
        "full_name": repo.get("full_name"),
        "description": normalize_text(repo.get("description")),
        "owner": owner.get("login"),
        "language": normalize_text(repo.get("language")),
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "open_issues": repo.get("open_issues_count", 0),
        "license": normalize_text(license_data.get("spdx_id")),
        "html_url": repo.get("html_url"),
    }

def print_repo_summary(summary):
    """将仓库摘要以易读格式显示在终端。"""

    print("\nGitHub 仓库信息")
    print(f"仓库：{summary['full_name']}")
    print(f"简介：{summary['description']}")
    print(f"所有者：{summary['owner']}")
    print(f"主要语言：{summary['language']}")
    print(f"Star：{summary['stars']}")
    print(f"Fork：{summary['forks']}")
    print(f"开放 Issue：{summary['open_issues']}")
    print(f"许可证：{summary['license']}")
    print(f"地址：{summary['html_url']}")


def query_repository(repo_name):
    """校验 owner/repository，查询 API，并保存原始与摘要数据。"""

    # split("/") 后必须刚好得到所有者和仓库名两部分，且都不能为空
    parts = [part.strip() for part in repo_name.split("/")]
    if len(parts) != 2 or not all(parts):
        raise ValueError("仓库必须使用 owner/repository 格式")

    owner, repository = parts

    # 分别编码两个 URL 路径片段，避免特殊字符改变请求地址结构
    safe_owner = quote(owner, safe="")
    safe_repository = quote(repository, safe="")
    url = f"{API_ROOT}/repos/{safe_owner}/{safe_repository}"

    # 数据流与用户查询一致：请求 → 摘要 → 保存 → 展示
    repo = request_json(url)
    summary = build_repo_summary(repo)
    raw_path = save_json(repo, "repo_raw.json")
    summary_path = save_json(summary, "repo_summary.json")
    print_repo_summary(summary)
    print(f"原始数据：{raw_path.resolve()}")
    print(f"整理结果：{summary_path.resolve()}")



# ---------- 文件保存 ----------
def save_json(data, filename):
    """将数据以 UTF-8 JSON 保存到 outputs 目录。"""

    # exist_ok=True 允许目录已存在，程序可以反复运行
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / filename
    output_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # 返回 Path，让调用方决定是否显示或继续处理文件位置
    return output_file


# ---------- 终端展示 ----------
def print_user_summary(summary):
    """将用户摘要以易读格式显示在终端。"""

    print("\nGitHub 用户信息")
    print(f"账号：{summary['login']}")
    print(f"姓名：{summary['name']}")
    print(f"公司：{summary['company']}")
    print(f"位置：{summary['location']}")
    print(f"公开仓库：{summary['public_repos']}")
    print(f"关注者：{summary['followers']}")
    print(f"主页：{summary['html_url']}")


# ---------- 用户查询流程 ----------
def query_user(username):
    """请求用户数据，生成摘要，保存两份 JSON 并展示结果。"""

    # quote() 对可能影响 URL 的特殊字符编码，safe="" 表示全部按需转义
    safe_username = quote(username, safe="")
    url = f"{API_ROOT}/users/{safe_username}"

    # 数据流：API 原始字典 → 摘要字典 → 两份 JSON → 终端输出
    profile = request_json(url)
    summary = build_user_summary(profile)
    raw_path = save_json(profile, "user_raw.json")
    summary_path = save_json(summary, "user_summary.json")
    print_user_summary(summary)
    print(f"原始数据：{raw_path.resolve()}")
    print(f"整理结果：{summary_path.resolve()}")


# ---------- 输入校验与统一错误出口 ----------
def main():
    """让用户选择查询类型，并把两条查询流程汇总到同一入口。"""

    print("请选择查询类型：")
    print("1. GitHub 用户")
    print("2. GitHub 仓库")
    choice = input("请输入 1 或 2：").strip()

    try:
        # 每个分支只负责收集和校验对应输入，实际查询交给专用函数
        if choice == "1":
            username = input("请输入 GitHub 用户名：").strip()
            if not username:
                raise ValueError("用户名不能为空")
            query_user(username)
        elif choice == "2":
            repo_name = input("请输入 owner/repository：").strip()
            query_repository(repo_name)
        else:
            raise ValueError("查询类型只能是 1 或 2")
    except (ValueError, RuntimeError, ConnectionError, TimeoutError) as error:
        # 在程序最外层统一显示可预期错误，避免用户看到冗长 Traceback
        print(f"运行失败：{error}")
        return 1

    return 0


# 直接运行本文件时才调用 main()；被测试文件导入时不会自动询问输入
if __name__ == "__main__":
    # 把 main() 的 0/1 返回值交给操作系统作为进程退出码
    sys.exit(main())