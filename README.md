![ManBot](https://socialify.git.ci/PikriNtr/ManBot/image?custom_description=Discord+Bot+Steam+Manifest+Downloader&description=1&font=KoHo&forks=1&issues=1&language=1&name=1&owner=1&pulls=1&stargazers=1&theme=Dark)

ManBot is a Discord bot that integrates with [Onekey](https://github.com/ikunshare/Onekey) to provide Steam depot manifest downloading capabilities directly through Discord slash commands.

## 🚀 Features

- **Discord Integration**: Use `/manifest <app_id>` command to download manifests
- **Automatic File Management**: Downloads manifests to local storage and sends them via Discord
- **Rate Limit Monitoring**: Shows GitHub API rate limit status 
- **Batch File Handling**: Automatically zips large numbers of manifest files
- **Error Handling**: Comprehensive error handling with user-friendly Discord messages
- **Auto-cleanup**: Clears old manifests before each new download

## 🛠️ Installation

### Prerequisites

- Python 3.10 or higher
- Windows 10 or higher (Onekey requirement)
- Discord Bot Token
- Git for version control
- SteamTools or GreenLuma (required by Onekey)

### Setup Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/PikriNtr/ManBot.git
   cd ManBot
   ```

2. **Install Onekey dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your Discord bot**:
   - Create a Discord application at https://discord.com/developers/applications
   - Create a bot and get the bot token
   - Add the bot token to the code (line in `bot.py` where `token = ""`)

4. **Set up Onekey requirements**:
   - Install SteamTools or GreenLuma as required by Onekey
   - Ensure all Onekey dependencies are properly configured

## 📖 Usage

### Starting the Bot

```bash
python bot.py
```

### Discord Commands

#### `/manifest <app_id>`
Downloads Steam depot manifests for the specified AppID.

**Example:**
```
/manifest 123456
```

**Bot Response:**
- Shows GitHub API rate limit status
- Downloads fresh manifest files
- Sends manifest files directly to Discord (up to 10 files individually, or as a zip for larger batches)
- Confirms successful processing

## 🏗️ Project Structure

```
ManBot/
├── bot.py                 # Main Discord bot implementation
├── manifests/            # Downloaded manifest files (auto-created)
├── src/                  # Onekey source code (same structure as original)
│   ├── main.py          # Onekey main application
│   ├── config.py        # Configuration management
│   ├── logger.py        # Logging utilities
│   ├── utils/           # Utility functions
│   ├── tools/           # SteamTools integration
│   ├── network/         # Network clients
│   └── models/          # Data models
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🔧 Configuration

### Discord Bot Token
Edit the `token` variable in `bot.py`:
```python
token = "YOUR_DISCORD_BOT_TOKEN_HERE"
```

### Onekey Configuration
The bot uses Onekey's existing configuration system:
- Steam installation path detection
- GitHub API settings
- Regional detection for optimal manifest repositories

## 🤖 How It Works

1. **Command Processing**: User runs `/manifest <app_id>` in Discord
2. **Onekey Integration**: Bot creates an `AutoSelectOnekeyApp` instance
3. **Manifest Download**: 
   - Clears old manifests from the `manifests/` directory
   - Uses Onekey to download fresh manifest files
   - Tracks downloaded files for Discord upload
4. **File Delivery**: 
   - Sends individual files (≤10 files) or zipped archive (>10 files)
   - Provides download status and GitHub API rate limit info


## 🤝 Dependencies

### Core Dependencies
- **[Onekey](https://github.com/ikunshare/Onekey)**: Steam depot manifest downloading
- **discord.py**: Discord bot framework
- **aiohttp**: HTTP client (used by Onekey)
- **pathlib**: File system operations

### Onekey Components Used
- `OnekeyApp`: Core application logic
- `ConfigManager`: Configuration handling
- `Logger`: Logging system
- `RegionDetector`: Regional optimization
- `SteamTools`: Steam integration
- `GitHubAPI`: Manifest repository access

## 📄 License

This project is licensed under the GPL-2.0 License - see the [LICENSE](LICENSE) file for details.

### Important License Information
- Built on [Onekey](https://github.com/ikunshare/Onekey) (GPL-2.0 licensed)
- **No modifications** made to original Onekey source code
- ManBot adds Discord integration layer only
- All Onekey license terms apply to the underlying functionality

## ⚠️ Important Notes

### GitHub API Rate Limits
- The bot monitors GitHub API usage
- Default limit: 60 requests per hour (unauthenticated)
- Rate limit status is shown with each command
- Bot will notify users if limits are exceeded


## 🎯 Usage Examples

### Basic Usage
```
User: /manifest 730
Bot: ✅ Successfully processed AppID: 730
     📦 Sent 3 manifest files
     GitHub API Status: 45/60 requests used
```

### Large Batch
```
User: /manifest 271590
Bot: ✅ Successfully processed AppID: 271590
     📦 Sent 15 manifest files (zipped)
     GitHub API Status: 52/60 requests used
```

### Error Handling
```
User: /manifest invalid_id
Bot: ❌ Error processing AppID invalid_id: No manifests found
```



## 🙏 Acknowledgments

- **[ikunshare](https://github.com/ikunshare)**: For creating and maintaining Onekey
- **Onekey Contributors**: For the excellent Steam depot functionality
- **Discord.py Team**: For the Discord bot framework

---

**Note**: This project is not affiliated with Steam, Valve Corporation, or Discord. All trademarks belong to their respective owners.
