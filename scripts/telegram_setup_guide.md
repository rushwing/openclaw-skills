# Telegram Bot 配置指南

本指南说明如何获取 `openclaw_sync.yaml` 中 `telegram` 节所需的两个值：
- `bot_token` — 机器人的身份凭证
- `chat_id` — 消息要发送到的目标对话 ID

---

## 第一步：创建 Bot，获取 `bot_token`

1. 在 Telegram 中搜索并打开 **@BotFather**
2. 发送命令：
   ```
   /newbot
   ```
3. 按提示输入：
   - Bot 的显示名称（如 `OpenClaw Notifier`）
   - Bot 的用户名（必须以 `bot` 结尾，如 `openclaw_sync_bot`）
4. BotFather 返回类似以下内容：
   ```
   Done! Congratulations on your new bot.
   ...
   Use this token to access the HTTP API:
   7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
5. 复制该 token，填入 `openclaw_sync.yaml`：
   ```yaml
   telegram:
     bot_token: "7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   ```

> **安全提示**：`bot_token` 等同于密码，不要提交到公开仓库。
> 建议将 `openclaw_sync.yaml` 中含 token 的部分通过环境变量或本地覆盖文件管理。

---

## 第二步：获取 `chat_id`

`chat_id` 是 Telegram 内部标识一个对话（个人 / 群组 / 频道）的数字 ID。

### 方式 A：发私信给自己（最常用）

1. 在 Telegram 中搜索你刚创建的 Bot，点击 **Start**（或发送任意消息）
2. 浏览器访问：
   ```
   https://api.telegram.org/bot<你的token>/getUpdates
   ```
   示例：
   ```
   https://api.telegram.org/bot7123456789:AAFxxxx/getUpdates
   ```
3. 返回 JSON 中找 `message.chat.id`：
   ```json
   {
     "result": [{
       "message": {
         "chat": {
           "id": 123456789,
           "type": "private"
         }
       }
     }]
   }
   ```
4. 该数字即为你的 `chat_id`，填入配置：
   ```yaml
   telegram:
     chat_id: "123456789"
   ```

### 方式 B：使用 @userinfobot 查询个人 ID

1. Telegram 中搜索 **@userinfobot**，发送 `/start`
2. 它会直接回复你的账号 ID：
   ```
   Id: 123456789
   First: Daniel
   ...
   ```
3. 将该 ID 填入 `chat_id`

### 方式 C：发送到群组

1. 将 Bot 添加到目标群组（群组设置 → 添加成员 → 搜索 Bot 名称）
2. 在群组中发送任意消息
3. 同样访问 `getUpdates` 接口，找 `message.chat.id`
   - 群组的 `chat_id` 通常为**负数**，如 `-1001234567890`

---

## 第三步：验证配置

修改 `openclaw_sync.yaml`：

```yaml
telegram:
  enabled: true
  bot_token: "7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  chat_id: "123456789"
```

运行一次测试（dry-run 不会产生 PR，但可验证 Telegram 通知）：

```bash
# 先用 dry-run 验证文件检测逻辑
~/.tutor-venv/bin/python scripts/openclaw_sync.py --dry-run

# 真实运行一次（会创建 PR 并 merge，然后发 Telegram 通知）
~/.tutor-venv/bin/python scripts/openclaw_sync.py
```

收到 Telegram 消息说明配置成功：
```
✅ OpenClaw Sync — PR Merged
Repository: everything_openclaw
PR: https://github.com/.../pull/N
Synced files (2):
  • SOUL.md
  • memory/
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `getUpdates` 返回空数组 | Bot 未收到任何消息 | 先在 Telegram 对 Bot 发一条消息，再刷新 |
| 发送失败 `chat not found` | `chat_id` 填错或 Bot 未被添加 | 重新获取 `chat_id`，群组需确认 Bot 已加入 |
| Token 报 `Unauthorized` | Token 填写有误或已失效 | 在 @BotFather 发 `/mybots` 重新查看 |
| 通知不发但脚本正常运行 | `enabled: false` | 改为 `enabled: true` |
