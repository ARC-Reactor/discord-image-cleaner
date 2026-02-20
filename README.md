# discord-image-cleaner

Downloads images older than a configurable number of days, archives them locally, and removes the messages from Discord.

---

## 📦 Environment variables

You can set these in a `.env` file or directly in the environment.  Required
values are marked with **(required)**; defaults are shown where applicable.

| Variable              | Description                                                                 | Default                       |
|-----------------------|-----------------------------------------------------------------------------|-------------------------------|
| `DISCORD_TOKEN`       | Your bot token                                                              | *(required)*                  |
| `GUILD_ID`            | ID of the guild/server to operate on                                        | *(required)*                  |
| `TARGET_CHANNELS`     | Comma-separated channel IDs to process                                     | *(required)*                  |
| `DAYS_OLD`            | Number of days old to consider                                              | `7`                           |
| `CHECK_INTERVAL_HOURS`| Scheduled interval in hours                                                 | `12`                          |
| `ARCHIVE_FOLDER`      | Where to store archived images                                              | `archive` next to repo        |
| `DATABASE_FILE`       | SQLite file path                                                            | `image_tracker.db` next to repo |
| `TEST_MODE`           | If truthy, do *not* delete messages (`true/1/yes/on`); falsy enables real deletions (`false/0/no/off`). Quotes are stripped (`"false"` works). | `true`                        |
| `DISABLE_TEST_MODE`   | If set to a truthy value (`true/1/yes`), same as `TEST_MODE=false` (enables real deletions). Use this if `TEST_MODE=false` is not applied. | —                             |
| `MANAGED_FILE_TYPES`  | Comma-separated file type categories to archive (e.g., `images`)            | all available types           |
| `MAX_ARCHIVE_SIZE_MB` | Maximum archive size in megabytes (0 = no limit)                           | `0`                           |
| `LOG_FILE`            | Path to logfile                                                             | —                             |
| `LOG_MAX_BYTES`       | Rotation size (bytes)                                                       | `5242880`                     |
| `LOG_BACKUP_COUNT`    | Number of rotated log files to keep                                        | `5`                           |

---

## 🚀 Quick start

**On the host:** create a `.env` file in the project root with at least `DISCORD_TOKEN`, `GUILD_ID`, and `TARGET_CHANNELS` (see [Environment variables](#-environment-variables) and [Adding this application as a Discord bot](#-adding-this-application-as-a-discord-bot)).

```bash
pip install -r requirements.txt
python bot.py
```

The bot will read the environment, connect to Discord, and perform an initial
pass over the configured channels.  Subsequent cleanups happen on the schedule
specified by `CHECK_INTERVAL_HOURS`.

---

## ⚙️ How it works

- Connects to a single guild and scans the configured channels for messages
  older than `DAYS_OLD`.
- Downloads recognized image attachments (`png`, `jpg`, `jpeg`, `webp`) to
  an archive folder structured by channel ID and date.
- Records each saved image in a local SQLite database so deletions can be
  tracked and messages are not processed twice.
- Uses incremental scanning: tracks the last processed message ID per channel
  to avoid re-processing messages on subsequent runs.
- If `TEST_MODE` is enabled the bot will download images and log deletion
  attempts but will not delete messages or update the channel state cursor.
  This allows safe testing—when you switch to `TEST_MODE=false`, the bot will
  re-scan and delete those messages.

### Configuring file types

By default, the bot archives all supported image types. You can narrow this by
setting `MANAGED_FILE_TYPES` to a comma-separated list of file type categories.

**Available categories:**
- `images` – PNG, JPG, JPEG, WebP (default)

Example:
```ini
# Only process image types
MANAGED_FILE_TYPES=images
```

If `MANAGED_FILE_TYPES` is not set, all available types are archived.

---

## 🛡️ Initiation & safety

- The bot requires the `DISCORD_TOKEN` and appropriate permissions in the
  target guild and channels (read message history, read message content, and
  manage messages) to function.
- Always start in `TEST_MODE=true` (or leave it unset) while configuring to avoid accidental removals.

### Disabling test mode (enabling real deletions)

To turn off test mode so the bot actually deletes messages, use **one** of these in `.env`:

- **Option A:** `TEST_MODE=false` (or `TEST_MODE=0`, `TEST_MODE=no`, `TEST_MODE=off`)
- **Option B:** `DISABLE_TEST_MODE=true` (or `DISABLE_TEST_MODE=1`, `DISABLE_TEST_MODE=yes`)

Use the exact key `TEST_MODE` or `DISABLE_TEST_MODE` (case-sensitive in the env). Values can be quoted or unquoted (`TEST_MODE=false` or `TEST_MODE="false"` both work). Restart the bot or container after changing; the startup log will show `(TEST_MODE=False)` when deletions are enabled.
- Archive and database paths can be overridden via environment variables; the
  defaults are relative to the repository root.

---

## 🔧 Adding this application as a Discord bot

Follow the steps below to create a bot account, invite it to your server, and
obtain the necessary identifiers.

### 1. Create a Discord Application
1. Visit <https://discord.com/developers/applications> and click **New
   Application**.
2. Give it a name (e.g. *Image Cleanup Bot*) and click **Create**.

### 2. Create the Bot User
1. In the sidebar select **Bot**.
2. Click **Add Bot** and confirm.

### 3. Enable Privileged Gateway Intents
1. In the **Bot** section scroll to **Privileged Gateway Intents**.
2. Enable **Message Content Intent** and click **Save Changes**.

### 4. Copy the Bot Token
1. Click **Reset Token** (or **Copy Token**).
2. Store it securely—**never** commit it to source control. Add it to your
   `.env` file:
   ```ini
   DISCORD_TOKEN=YOUR_TOKEN_HERE
   ```

### 5. Generate the Invite URL
1. Navigate to **OAuth2 → URL Generator** in the sidebar.
2. Under **SCOPES** select `bot`.
3. Under **BOT PERMISSIONS** choose:
   - View Channels
   - Read Message History
   - Manage Messages
   - Attach Files (optional but recommended)
4. Copy the generated URL and use it to invite the bot to your server.

### 6. Collect IDs
1. **Enable Developer Mode** in Discord under **User Settings → Advanced**.
2. Right-click the server name and select **Copy Server ID** → add to `.env` as
   `GUILD_ID`.
3. Right-click each target channel, choose **Copy Channel ID**, and put the
   comma-separated list into `TARGET_CHANNELS`.

### 7. Verify Permissions
- Ensure the bot’s role has the required permissions at the server and channel
  level.
- Role hierarchy matters: the bot cannot delete messages from users whose
  highest role is above the bot’s role.

### 8. Initial Test Run
1. Set `TEST_MODE=true`.
2. Start the bot and verify log messages such as:
   ```
   [TEST MODE] Would delete message 123456789
   ```
3. **Important:** When running in `TEST_MODE=true`, the bot downloads and archives images but does not update the channel state cursor. This means when you switch to `TEST_MODE=false`, the bot will re-scan those messages and actually delete them. This is intentional so you can safely test without losing messages.
4. Switch to `TEST_MODE=false` and restart when ready to perform deletions.

#### ✅ Checklist
- [ ] Application created
- [ ] Bot user created
- [ ] Message Content Intent enabled
- [ ] Token copied into `.env`
- [ ] Bot invited with correct permissions
- [ ] Role hierarchy verified
- [ ] `GUILD_ID` added
- [ ] `TARGET_CHANNELS` added
- [ ] `TEST_MODE` validated

---

## 🐞 Common setup errors

| Problem                                | Likely cause                                          |
|----------------------------------------|-------------------------------------------------------|
| Bot online but does nothing            | Message Content Intent not enabled                    |
| Bot cannot delete messages             | Role hierarchy issue                                  |
| Bot cannot see a channel               | Channel permission override blocking access           |
| 403 Forbidden when deleting messages   | Bot role below target user’s role                     |

---

## 📄 Logs & troubleshooting

### Viewing logs

**Local installation:**
- Logs are written to stdout/stderr by default. If `LOG_FILE` is set, logs are also written to that file.
- To view log files: `tail -f /path/to/logfile.log`

**Docker container:**
- View logs in real-time:
  ```bash
  docker logs -f discord-image-cleaner
  ```
- View last 100 lines:
  ```bash
  docker logs --tail 100 discord-image-cleaner
  ```
- View logs with timestamps:
  ```bash
  docker logs -f -t discord-image-cleaner
  ```

**Docker Compose:**
- Follow logs:
  ```bash
  docker-compose logs -f bot
  ```
- View last 100 lines:
  ```bash
  docker-compose logs --tail 100 bot
  ```

**If `LOG_FILE` is configured:**
- View log file inside container:
  ```bash
  docker exec discord-image-cleaner cat /path/to/logfile.log
  ```
- Or mount the log directory as a volume to access logs from the host.

### Troubleshooting

**Docker: "unable to open database file"**
- If you previously mounted a single file (`-v .../image_tracker.db:/app/image_tracker.db`) and the file didn't exist on the host, Docker created a *directory* there, which breaks SQLite. Use a data directory instead: mount `-v "$PWD/data":/app/data` and set `DATABASE_FILE=/app/data/image_tracker.db`. The app will create the file inside the mounted directory. You can remove any mistaken `image_tracker.db` directory on the host and switch to the `./data` layout above.

**Docker: "Permission denied" creating files in `/app/archive` or `/app/data`**
- The container runs as user UID 1000. The bind-mounted `./archive` and `./data` on the host must be writable by that user. From the project root run: `sudo chown -R 1000:1000 archive data`. Then restart the container. If you created these dirs as root or another user, fix ownership before starting the bot.

- **Startup failures:** Verify environment variables are set correctly. Check logs for missing required variables.
- **Bot not processing:** Ensure Message Content Intent is enabled in Discord Developer Portal.
- **Permission errors:** Verify bot role hierarchy and channel permissions.
- **Database issues:** Check that the database file is writable and not corrupted.
- **Archive full:** Monitor disk usage; configure `MAX_ARCHIVE_SIZE_MB` to enable automatic pruning.

---

## 🐳 Container deployment

This project supports running inside Docker (Ubuntu-based image). You need **Docker** (and optionally **Docker Compose**) installed on the host.

### Host setup before first run (Docker)

Do these steps on your machine before building or running the container:

1. **Create a `.env` file** in the project root with at least `DISCORD_TOKEN`, `GUILD_ID`, and `TARGET_CHANNELS`. You can copy `.env.example` to `.env` and edit it (see [Environment variables](#-environment-variables)).
2. **Create the volume directories** that will be bind-mounted:
   ```bash
   mkdir -p archive data
   ```
3. **Make them writable by the container user (UID 1000).** On Linux you typically need `sudo`:
   ```bash
   sudo chown -R 1000:1000 archive data
   ```
   If your host user is already UID 1000, `mkdir -p archive data` may be enough (you own the dirs). If you see permission errors from the container, run the `chown` above and restart the container.

**Docker host checklist:**
- [ ] `.env` created with `DISCORD_TOKEN`, `GUILD_ID`, `TARGET_CHANNELS`
- [ ] `mkdir -p archive data` run in project root
- [ ] `sudo chown -R 1000:1000 archive data` run (or ensure dirs are writable by UID 1000)

After that, build and run as below.

### Build and run

1. **Build the image**
   ```bash
   docker build -t discord-image-cleaner .
   ```

2. **Run with Docker**
   ```bash
   docker run -d \
     --name discord-image-cleaner \
     --env-file .env \
     -e DATABASE_FILE=/app/data/image_tracker.db \
     -v "$PWD/archive":/app/archive \
     -v "$PWD/data":/app/data \
     discord-image-cleaner:latest
   ```
   The app creates `data/image_tracker.db` and `archive/<channel_id>/<date>/` on first run. Add `--restart unless-stopped` as needed.

3. **Or use Docker Compose**
   ```bash
   docker compose up -d
   ```
   The compose file uses `./archive` and `./data`; ensure you’ve created and chown’d them as in [Host setup before first run](#host-setup-before-first-run-docker) above.

If you see `Permission denied` when creating files in `archive/` or `data/`, fix ownership: `sudo chown -R 1000:1000 archive data` (or `chmod -R 777 archive data` for testing only), then restart the container.

### Viewing container logs

- **Follow logs in real-time:**
  ```bash
  docker logs -f discord-image-cleaner
  ```
  Or with docker-compose:
  ```bash
  docker-compose logs -f bot
  ```

- **View recent logs:**
  ```bash
  docker logs --tail 100 discord-image-cleaner
  ```

- **View logs with timestamps:**
  ```bash
  docker logs -f -t discord-image-cleaner
  ```

See the [Logs & troubleshooting](#-logs--troubleshooting) section for more details.

### Container management

- **Stop the container:**
  ```bash
  docker stop discord-image-cleaner
  ```
  Or: `docker-compose stop bot`

- **Start the container:**
  ```bash
  docker start discord-image-cleaner
  ```
  Or: `docker-compose start bot`

- **Restart the container:**
  ```bash
  docker restart discord-image-cleaner
  ```
  Or: `docker-compose restart bot`

- **Check if container is running:**
  ```bash
  docker ps | grep discord-image-cleaner
  ```

- **Update the container** (after pulling code changes):
  ```bash
  docker-compose down
  docker-compose build
  docker-compose up -d
  ```

### Notes
- Base image: Ubuntu 24.04 slim with Python 3.12.
- `PYTHONUNBUFFERED=1` ensures real-time logging to stdout/stderr.
- Works on any Docker‑capable OS (instructions are Ubuntu‑centric).
- The container runs as a non-root user (`appuser`) for security.

## 🔍 Monitoring & maintenance

### Checking archive size

- **Local installation:**
  ```bash
  du -sh archive/
  ```

- **Docker container:**
  ```bash
  docker exec discord-image-cleaner du -sh /app/archive
  ```

### Database inspection

- **View database contents** (requires sqlite3). Use `image_tracker.db` for local runs, or `data/image_tracker.db` when using Docker/docker-compose:
  ```bash
  sqlite3 image_tracker.db "SELECT COUNT(*) FROM tracked_images;"
  sqlite3 image_tracker.db "SELECT channel_id, COUNT(*) FROM tracked_images GROUP BY channel_id;"
  ```

- **Check channel state:**
  ```bash
  sqlite3 image_tracker.db "SELECT * FROM channel_state;"
  ```

### Archive cleanup

- Set `MAX_ARCHIVE_SIZE_MB` to enable automatic pruning of oldest files when the archive exceeds the limit.
- Manually prune old files if needed:
  ```bash
  # Example: remove files older than 90 days
  find archive/ -type f -mtime +90 -delete
  ```

### Health checks

- **Verify bot is connected:**
  - Check logs for "Logged in as ..." message.
  - Bot should appear online in Discord.

- **Verify processing is working:**
  - Look for log messages like "Processed batch for channel ..."
  - Check that archive folder is growing (if there are images to process).
  - In `TEST_MODE=true`, verify "[TEST MODE] Would delete message ..." appears.

## 🐍 Requirements

- **Python 3.12+** (3.11 may work but is not tested)
- discord.py 2.x
- See `requirements.txt` for full dependencies

### Local installation

**On the host:** ensure you have a `.env` file with `DISCORD_TOKEN`, `GUILD_ID`, and `TARGET_CHANNELS`. The process must be able to write to the project directory (for default `archive/` and `image_tracker.db`) or to the paths set in `ARCHIVE_FOLDER` and `DATABASE_FILE`.

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```
