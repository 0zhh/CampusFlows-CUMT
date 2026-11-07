# 把这个项目传到自己的 GitHub 仓库

> 当前状态：本地已经是 Git 仓库（56 个提交，分支已改为 `main`，工作区干净），**只差一个远程地址**。

---

## 一、先在 GitHub 上建一个空仓库

1. 打开 https://github.com/new
2. Repository name 填 `campusflow`（或你喜欢的名字）
3. 可见性选 **Private** 或 Public，都行
4. **不要**勾选 Add a README / .gitignore / license —— 本地已经有内容了，勾了反而要先 pull
5. 点 Create repository

建好后页面会给你一个地址，形如：

```
https://github.com/<你的用户名>/campusflow.git
```

---

## 二、把本地仓库接上去

在 `D:\java大作业` 里打开 PowerShell：

```powershell
cd D:\java大作业
git remote add origin https://github.com/<你的用户名>/campusflow.git
git remote -v          # 确认一下
```

---

## 三、认证：推荐用 Personal Access Token

GitHub 从 2021 年起**不再接受账号密码**，HTTPS 推送要用 token。

1. 打开 https://github.com/settings/tokens → **Generate new token (classic)**
2. Note 随便写，Expiration 选 90 天，勾选 **repo** 这一项
3. 生成后**立刻复制**（只显示一次）
4. 第一次 `git push` 会弹窗要用户名和密码：
   - Username：你的 GitHub 用户名
   - Password：**粘贴刚才的 token**（不是登录密码）

Windows 上会由 Git Credential Manager 记住，之后不用再输。

> 想用 SSH 也行：`ssh-keygen -t ed25519 -C "你的邮箱"`，把 `~/.ssh/id_ed25519.pub` 贴到
> https://github.com/settings/keys ，然后把远程地址换成 `git`github.com:<用户名>/campusflow.git`。

---

## 四、推上去

```powershell
git push -u origin main
```

`-u` 会把本地 main 和远程 main 绑定，以后直接 `git push`、`git pull` 就行。

推完后刷新仓库页面，应该能看到 56 个提交和全部代码。

---

## 五、之后每次改完怎么提交

```powershell
git add -A
git commit -m "feat: 做了什么"
git push
```

看当前状态用 `git status`，看历史用 `git log --oneline`。

---

## 六、这个仓库里有什么、要注意什么

| 项 | 值 |
|---|---|
| 提交数 | 56 |
| 跟踪文件 | 1,098 个 |
| .git 体积 | 65.9 MB（含历史） |
| 最大单文件 | 9.99 MB（`data/reference/cumt_2024_nanhu_logistics_inspection.jpg`） |

三个提醒：

1. **单文件都在 100 MB 以内**，可以正常推。但整体偏大，第一次 push 可能要等几分钟。
2. **MySQL 密码是明文**：`backend/src/main/resources/application-mysql.yml` 里写的是 `__MYSQL_PASSWORD_REMOVED__`，
   本地演示用的。公开仓库建议改成环境变量 `${MYSQL_PASSWORD}`，或者干脆换一个密码。
3. **离线卫星瓦片 11 MB**（`frontend/public/tiles/`）已经在仓库里。想减小体积可以把它加进 `.gitignore`，
   让别人自己跑 `python data/research/fetch_sat_tiles.py` 下载。

---

## 七、常见报错

| 报错 | 原因 | 处理 |
|---|---|---|
| `remote origin already exists` | 已经加过远程 | `git remote set-url origin <新地址>` |
| `Authentication failed` | 用了登录密码 | 换成 Personal Access Token |
| `failed to push some refs` / `non-fast-forward` | 远程已有提交（建仓库时勾了 README） | `git pull --rebase origin main` 再 push |
| `error: src refspec main does not match any` | 本地没有 main 分支 | 确认 `git branch --show-current` 输出是 main |
| `RPC failed; HTTP 413` | 单次推送体积过大 | `git config http.postBuffer 524288000` 再试 |
