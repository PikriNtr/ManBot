import discord
from discord.ext import commands
import asyncio
import os
import traceback
from pathlib import Path
from typing import List, Tuple, Dict, Set
import zipfile
import io
import re
from src.utils.steam import parse_key_file, parse_manifest_filename

# Import Onekey components
from src.main import OnekeyApp
from src.constants import BANNER, REPO_LIST
from src.logger import Logger
from src.config import ConfigManager
from src.utils.region import RegionDetector
from src.tools.steamtools import SteamTools
from src.network.github import GitHubAPI
from src.network.client import HttpClient
from src.models import DepotInfo

class AutoSelectOnekeyApp(OnekeyApp):
    """Modified version that tracks downloaded files"""
    
    def __init__(self):
        super().__init__()
        self._should_close_client = False
        self.downloaded_files = set()  # Track downloaded files
        
    async def run(self, app_id: str) -> Tuple[bool, List[Path]]:
        """Run with auto-selected options and return manifest files"""
        try:
            self.downloaded_files.clear()  # Reset for each run
            
            # 1. Region detection
            detector = RegionDetector(self.client, self.logger)
            is_cn, country = await detector.check_cn()
            self.github.is_cn = is_cn
            await self.github.check_rate_limit()

            # 2. Get manifests and keys
            self.logger.info(f"Processing game {app_id}...")
            depot_data, depot_map = await self.handle_depot_files(app_id)
            
            if not depot_data:
                self.logger.error("No manifests found for this game")
                return False, []

            # 3. Auto-configure SteamTools
            tool = SteamTools(self.config.steam_path)
            success = await tool.setup(
                depot_data,
                app_id,
                depot_map=depot_map,
                version_lock=False
            )

            # 4. Get files we tracked as downloaded
            manifest_dir = Path("manifests")
            manifest_files = []
            for filename in self.downloaded_files:
                file_path = manifest_dir / filename
                if file_path.exists():
                    manifest_files.append(file_path)
            
            return success, manifest_files

        except Exception as e:
            self.logger.error(f"Error: {traceback.format_exc()}")
            return False, []
            
    async def handle_depot_files(self, app_id: str) -> Tuple[List[DepotInfo], Dict[str, List[str]]]:
        """Save manifests to project root and track downloads"""
        depot_list = []
        depot_map = {}
        
        # Create manifests directory
        manifest_dir = Path("manifests")
        manifest_dir.mkdir(exist_ok=True, parents=True)

        repo_info = await self.github.get_latest_repo_info(REPO_LIST, app_id)
        if not repo_info:
            return depot_list, depot_map

        self.logger.info(f"Selected manifest repository: https://github.com/{repo_info.name}")
        self.logger.info(f"Last update: {repo_info.last_update}")

        branch_url = f"https://api.github.com/repos/{repo_info.name}/branches/{app_id}"
        branch_res = await self.client.get(branch_url, headers=self.config.github_headers)
        branch_res.raise_for_status()

        tree_url = branch_res.json()["commit"]["commit"]["tree"]["url"]
        tree_res = await self.client.get(tree_url)
        tree_res.raise_for_status()

        for item in tree_res.json()["tree"]:
            file_path = item["path"]

            if file_path.endswith(".manifest"):
                save_path = manifest_dir / file_path
                if save_path.exists():
                    self.logger.warning(f"Manifest already exists: {save_path}")
                else:
                    content = await self.github.fetch_file(repo_info.name, repo_info.sha, file_path)
                    save_path.write_bytes(content)
                    self.logger.info(f"Manifest downloaded: {file_path}")
                    self.downloaded_files.add(file_path)  # Track downloaded file

                depot_id, manifest_id = parse_manifest_filename(file_path)
                if depot_id and manifest_id:
                    depot_map.setdefault(depot_id, []).append(manifest_id)

            elif "key.vdf" in file_path.lower():
                key_content = await self.github.fetch_file(repo_info.name, repo_info.sha, file_path)
                depot_list.extend(parse_key_file(key_content))

        for depot_id in depot_map:
            depot_map[depot_id].sort(key=lambda x: int(x), reverse=True)

        return depot_list, depot_map
        
    async def close(self):
        """Close client only when we're done with it"""
        if self._should_close_client:
            await self.client.close()

class OnekeyDiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        
        # Setup Onekey components
        self.config = ConfigManager()
        self.logger = Logger(
            "OnekeyBot",
            debug_mode=self.config.app_config.debug_mode,
            log_file=self.config.app_config.logging_files
        )
        self.onekey = AutoSelectOnekeyApp()
        
    async def on_ready(self):
        self.logger.info(f"Bot ready: {self.user}")
        self.logger.info(BANNER)
        
    async def setup_hook(self):
        await self.tree.sync()
        
    async def send_manifests(self, interaction: discord.Interaction, files: List[Path]):
        """Send manifest files with verification"""
        try:
            if not files:
                await interaction.followup.send("ℹ️ No manifest files found")
                return
                
            # Verify files exist and are readable
            valid_files = []
            for file_path in files:
                try:
                    if file_path.exists() and file_path.stat().st_size > 0:
                        with open(file_path, 'rb') as f:
                            if f.read(1):  # Test read
                                valid_files.append(file_path)
                except Exception as e:
                    self.logger.warning(f"Invalid file {file_path}: {e}")
            
            if not valid_files:
                await interaction.followup.send("⚠️ No valid manifest files found")
                return

            # Send files
            if len(valid_files) <= 10:
                await interaction.followup.send(
                    "Here are your manifest files:",
                    files=[discord.File(f) for f in valid_files]
                )
            else:
                # Create zip for large batches
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w') as zf:
                    for f in valid_files:
                        zf.write(f, f.name)
                zip_buffer.seek(0)
                
                await interaction.followup.send(
                    "Here are your manifest files (zipped):",
                    file=discord.File(zip_buffer, "manifests.zip")
                )
                
            self.logger.info(f"Sent {len(valid_files)} manifest files")
            
        except Exception as e:
            self.logger.error(f"Failed to send files: {e}")
            await interaction.followup.send("⚠️ Couldn't send manifest files")

    async def close(self):
        """Clean up when bot is closing"""
        await self.onekey.close()
        await super().close()

# Initialize bot
bot = OnekeyDiscordBot()

@bot.tree.command(name="manifest", description="Download Steam depot manifests")
async def cmd_manifest(interaction: discord.Interaction, app_id: str):
    """Handle /manifest command"""
    try:
        await interaction.response.defer()
        
        # Clear manifests directory before processing
        manifest_dir = Path("manifests")
        if manifest_dir.exists():
            for file in manifest_dir.glob("*"):
                try:
                    file.unlink()
                    bot.logger.info(f"Deleted existing manifest: {file.name}")
                except Exception as e:
                    bot.logger.warning(f"Failed to delete {file.name}: {e}")
        
        # Check rate limits
        rate_info = await bot.onekey.github.check_rate_limit()
        
        if "error" in rate_info:
            limit_msg = "⚠️ Could not check GitHub API limits\n\n"
        else:
            limit_msg = (
                f"GitHub API Status:\n"
                f"• Used: {rate_info['used']}/{rate_info['limit']} requests\n"
                f"• Remaining: {rate_info['remaining']}\n"
                f"• Resets: {rate_info['reset_relative']} ({rate_info['reset_formatted']})\n\n"
            )
            if rate_info['remaining'] == 0:
                limit_msg += "⛔ You've exhausted your GitHub API limits!\n\n"
        
        # Process the AppID - this will download fresh manifests
        success, manifest_files = await bot.onekey.run(app_id)
        
        if not manifest_files:
            await interaction.followup.send(f"{limit_msg}ℹ️ No manifest files were found for AppID {app_id}")
            return
        
        # Send the files
        await bot.send_manifests(interaction, manifest_files)
        
        # Send status
        status_msg = (f"{limit_msg}✅ Successfully processed AppID: {app_id}\n"
                     f"📦 Sent {len(manifest_files)} manifest files")
        await interaction.followup.send(status_msg)
            
    except Exception as e:
        bot.logger.error(f"Error processing {app_id}: {traceback.format_exc()}")
        await interaction.followup.send(f"❌ Error processing AppID {app_id}: {str(e)}")

def run():
    """Start the bot"""
    token = ""
    if not token:
        print("Error: Missing DISCORD_BOT_TOKEN environment variable")
        return
        
    try:
        asyncio.run(bot.start(token))
    except KeyboardInterrupt:
        print("\nBot stopped")
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    run()