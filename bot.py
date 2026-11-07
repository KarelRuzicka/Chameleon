import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class BotException(Exception):
    """Exception raised during bot operations."""
    def __init__(self, user_message: str, log_message: str | None = None):
        self.user_message = user_message
        # If no custom log message is provided, just fallback to the user message
        self.log_message = log_message or user_message
        super().__init__(self.user_message)



TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN environment variable not set.")




# Initialize bot with default intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!",intents=intents)

@bot.event
async def on_ready():
    logger.info("Logged in as %s.", bot.user)
    
    # Sync the slash commands to Discord
    try:
        synced = await bot.tree.sync()
        logger.info("Synced %d slash command(s).", len(synced))
    except Exception:
        logger.exception("Failed to sync slash commands.")




########### Slash Commands ##########

@bot.tree.command(name="namecolor", description="Set your displayed name color.")
@app_commands.describe(hex="The hex value of the color you want to set (e.g., #FF0000)")
async def namecolor(interaction: discord.Interaction, hex: str):

    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        logger.warning(f"Rejected removenamecolor request outside a server. | User: {interaction.user.id}")
        return
    
    try:            
        color = await parse_hex_color(hex)
        await add_color(interaction.user, interaction.guild, color)
    except BotException as e:
        logger.warning(f"{e.log_message} | User: {interaction.user.id} | Guild: {interaction.guild.id}")
        await interaction.response.send_message(e.user_message, ephemeral=True)
        return

    await interaction.response.send_message(f"Successfully changed your name color to **{hex}**!", ephemeral=True)
    logger.info(f"Updated name color. | User: {interaction.user.id} | Guild: {interaction.guild.id}")




@bot.tree.command(name="removenamecolor", description="Remove your displayed name color.")
async def removenamecolor(interaction: discord.Interaction):

    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        logger.warning(f"Rejected removenamecolor request outside a server. | User: {interaction.user.id}")
        return

    try:        
        await remove_color(interaction.user, interaction.guild)
    except BotException as e:
        logger.warning(f"{e.log_message} | User: {interaction.user.id} | Guild: {interaction.guild.id}")
        await interaction.response.send_message(e.user_message, ephemeral=True)
        return
    
    await interaction.response.send_message(f"Successfully removed your name color!", ephemeral=True)
    logger.info(f"Removed name color. | User: {interaction.user.id} | Guild: {interaction.guild.id}")



    
########### Server events ##########
    
@bot.event
async def on_member_remove(member: discord.Member):
    try:
        await remove_color(member, member.guild)
    except BotException as e:
        logger.warning(f"{e.log_message} | User: {member.id} | Guild: {member.guild.id}")
    logger.info(f"Completed cleanup for departing member {member.id} in guild {member.guild.id}")




########## Functions ##########  
        

async def parse_hex_color(hex: str) -> discord.Color:
    # Remove the '#' if present
    hex_code = hex.lstrip('#')

    if len(hex_code) != 6 or not all(c in '0123456789ABCDEFabcdef' for c in hex_code):
        raise BotException(
            user_message = f"Invalid color format! Valid format is a 6-digit hex code (e.g., #FF0000).",
            log_message = f"Invalid color format: {hex_code}"              
        )
    
    # Get a discord color instance
    try:
        color = discord.Color.from_str(f"#{hex_code}")
    except ValueError:
        raise BotException(
            user_message = f"Error when reading the color.",
            log_message = f"Discord could not parse color: {hex_code}"
        )

    return color




async def add_color(user: discord.Member, guild: discord.Guild, color: discord.Color):
        
    # Create/update the role
    try:
        role_name = f"Color-{user.id}"
        
        existing_role = discord.utils.get(guild.roles, name=role_name) 
        # existing_role = next((role for role in interaction.guild.roles if role.name == role_name), None)
        if existing_role is None: 
            # Create
            new_role = await guild.create_role(
                name=role_name,
                color=color,
                reason=f"Role created via bot by {user}" 
            )
            await user.add_roles(new_role, reason=f"Role assigned via bot by {user}")
            
            await guild.fetch_roles() # Refresh the guild's role cache to remove a race condition where the role might not be immediately available after creation
            refreshed_role = guild.get_role(new_role.id)
            
            if refreshed_role is None:
                raise BotException(
                    user_message = "Error when assigning color.",
                    log_message = f"Failed to retrieve the newly created role."
                )
            
            await refreshed_role.edit(position=guild.me.top_role.position - 1, reason=f"Role position adjusted via bot by {user}")
        else: 
            # Update
            await existing_role.edit(
                color=color, 
                reason=f"Role color updated via bot by {user}")
            
        
    except discord.Forbidden:
        raise BotException(
            user_message = "I don't have the 'Manage Roles' permission!",
            log_message = f"Missing permissions while updating name color."
        )
    except discord.HTTPException:
        raise BotException(
            user_message = "Failed to change your name color.",
            log_message = f"HTTP error while creating/updating name color role."
        )




async def remove_color(member: discord.Member, guild: discord.Guild):
    role_name = f"Color-{member.id}"
    
    existing_role = discord.utils.get(guild.roles, name=role_name)
    
    # If the role exists, delete it
    if existing_role:
        try:
            await existing_role.delete(reason=f"Auto-cleanup: {member.name} left the server.")
        except discord.Forbidden:
            raise BotException(
                user_message = "I don't have the 'Manage Roles' permission!",
                log_message = f"Missing permissions while deleting name color role."
            )
        except discord.HTTPException:
            raise BotException(
                user_message = "Failed to remove your name color role.",
                log_message = f"HTTP error while deleting name color role."
            )


# Run the bot
bot.run(TOKEN)