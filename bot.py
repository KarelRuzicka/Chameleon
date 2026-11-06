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

    if interaction.guild is None or isinstance(interaction.user, discord.User):
        logger.warning("Rejected removenamecolor request outside a server from user %s.", interaction.user.id)
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    
    await add_color(interaction.user, interaction.guild, interaction.response, hex)
    
    await interaction.response.send_message(f"Successfully changed your name color to **{hex}**!", ephemeral=True)
    logger.info("Updated name color role for user %s in guild %s.", interaction.user.id, interaction.guild.id)



@bot.tree.command(name="removenamecolor", description="Remove your displayed name color.")
async def removenamecolor(interaction: discord.Interaction):

    if interaction.guild is None or isinstance(interaction.user, discord.User):
        logger.warning("Rejected removenamecolor request outside a server from user %s.", interaction.user.id)
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return
    
    await remove_color(interaction.user, interaction.guild)
    
    await interaction.response.send_message(f"Successfully removed your name color!", ephemeral=True)
    logger.info("Removed name color role for user %s in guild %s.", interaction.user.id, interaction.guild.id)

    
########### Server events ##########
    
@bot.event
async def on_member_remove(member: discord.Member):
    logger.info("Cleaning up name color for departing member %s in guild %s.", member.id, member.guild.id)
    await remove_color(member, member.guild)
    

########## Functions ##########

async def add_color(user: discord.Member, guild: discord.Guild, response: discord.InteractionResponse, hex: str):

    # Remove the '#' if present
    hex_code = hex.lstrip('#')

    if len(hex_code) != 6 or not all(c in '0123456789ABCDEFabcdef' for c in hex_code):
        logger.warning("Rejected invalid color format from user %s.", user.id)
        await response.send_message("Invalid color format! Valid format is a 6-digit hex code (e.g., #FF0000).", ephemeral=True)
        return
    
    # Get role color instance
    try:
        role_color = discord.Color.from_str(f"#{hex_code}")
    except ValueError:
        logger.warning("Could not parse color for user %s.", user.id)
        await response.send_message("Error when reading the color.", ephemeral=True)
        return
    
    
    # Create/update the role
    try:
        
        if guild is None or isinstance(user, discord.User):
            logger.warning("Rejected namecolor request outside a server from user %s.", user.id)
            await response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        
        role_name = f"Color-{user.id}"
        
        existing_role = discord.utils.get(guild.roles, name=role_name) 
        # existing_role = next((role for role in interaction.guild.roles if role.name == role_name), None)
        if existing_role is None: 
            # Create
            new_role = await guild.create_role(
                name=role_name,
                color=role_color,
                reason=f"Role created via bot by {user}" 
            )
            await user.add_roles(new_role, reason=f"Role assigned via bot by {user}")
            
            new_role = discord.utils.get(guild.roles, name=role_name)
            if new_role is None:
                logger.error("Failed to retrieve the newly created role for user %s.", user.id)
                await response.send_message("Error when assigning color.", ephemeral=True)
                return
            
            await new_role.edit(position=guild.me.top_role.position - 1, reason=f"Role position adjusted via bot by {user}")
        else: 
            # Edit
            await existing_role.edit(
                color=role_color, 
                reason=f"Role color updated via bot by {user}")
            
        
    except discord.Forbidden:
        logger.exception("Missing permissions while updating name color for user %s.", user.id)
        await response.send_message("I don't have the 'Manage Roles' permission!", ephemeral=True)



async def remove_color(member: discord.Member, guild: discord.Guild):
    role_name = f"Color-{member.id}"
    
    existing_role = discord.utils.get(guild.roles, name=role_name)
    
    # If the role exists, delete it
    if existing_role:
        try:
            await existing_role.delete(reason=f"Auto-cleanup: {member.name} left the server.")
            logger.info("Successfully deleted %s for %s.", role_name, member.id)
        except discord.Forbidden:
            logger.exception("Missing 'Manage Roles' permission to delete %s.", role_name)
        except discord.HTTPException:
            logger.exception("Failed to delete %s due to a Discord API error.", role_name)


# Run the bot
bot.run(TOKEN)