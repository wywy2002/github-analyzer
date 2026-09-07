# GitHub 项目分析器

一个使用 Python 标准库和 GitHub 公开 API 编写的命令行工具。

## 功能

- 查询 GitHub 用户公开信息
- 查询 GitHub 仓库的 Star、Fork 和开放 Issue
- 保存原始 JSON 与整理后的摘要 JSON
- 处理空输入、不存在的资源、网络错误和超时
- 使用标准库 unittest 进行测试

## 环境

- Python 3.13（其他仍受支持的 Python 3 版本也可能适用）
- Windows PowerShell
- 可访问 GitHub API 的网络

## 运行

```powershell
# 启动交互式 GitHub 分析器
python .\github_analyzer.py
```

按照提示选择用户或仓库查询。

## 测试

```powershell
# 运行全部自动化测试并显示每项结果
python -m unittest -v
```

## 输出

程序把原始数据和摘要数据保存到 `outputs`。这些文件由程序生成，不提交到 Git。

## 安全

本项目使用公开 API，不需要 GitHub Token。不要把密码、Token 或 `.env` 文件提交到仓库。

## 已知限制

- GitHub API 数据会实时变化。
- 未认证请求有频率限制。
- `open_issues_count` 的含义以 GitHub API 定义为准。