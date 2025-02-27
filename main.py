import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from time_tracker import TimeTracker
from time_tracker import TimeFormatView
import calendar
from datetime import datetime

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Set up bot with command prefix '!'
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix = '!', intents = intents)

time_tracker = TimeTracker()

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

# Event: Handle errors
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found!")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

@bot.command(name = "ping")
async def ping(ctx):
    await ctx.send("pong")

@bot.command(name="calendar")
async def show_calendar(ctx):
    """Display calendar with time tracking for current month"""
    # Delete previous calendar messages from the bot
    async for message in ctx.channel.history(limit=100):
        if message.author == bot.user and message.embeds:
            await message.delete()
    
    view = TimeFormatView()
    cal_data, total_time = time_tracker.get_month_calendar(ctx.author.id)
    embed = time_tracker.create_calendar_embed(ctx.author.id, cal_data, total_time)
    
    message = await ctx.send(embed=embed, view=view)
    
    # Wait for format selection
    await view.wait()
    
    if view.response:  # Check if format was selected
        cal_data, total_time = time_tracker.get_month_calendar(
            ctx.author.id, 
            time_format=view.format
        )
        new_embed = time_tracker.create_calendar_embed(
            ctx.author.id, 
            cal_data, 
            total_time, 
            time_format=view.format
        )
        await message.edit(embed=new_embed, view=None)
    else:
        # If no format was selected (timeout), remove the view
        await message.edit(view=None)

@bot.command(name="start")
async def start_timer(ctx):
    """Start timing for the user"""
    time_tracker.start_timer(ctx.author.id)
    await ctx.send(f"Timer started for {ctx.author.name}")

@bot.command(name="stop")
async def stop_timer(ctx):
    """Stop timing for the user"""
    duration = time_tracker.stop_timer(ctx.author.id)
    if duration:
        await ctx.send(f"Timer stopped for {ctx.author.name}. Session duration: {duration:.2f} hours")
    else:
        await ctx.send("No active timer found!")

@bot.command(name="today")
async def show_today(ctx):
    """Show total time for today"""
    today = datetime.now().strftime("%Y-%m-%d")
    user_id = str(ctx.author.id)
    
    # Get today's time from time_tracker
    total_hours = 0
    if today in time_tracker.time_data and user_id in time_tracker.time_data[today]:
        total_hours = time_tracker.time_data[today][user_id]
    
    # Check if there's an active timer
    if ctx.author.id in time_tracker.active_timers:
        current_session = (datetime.now() - time_tracker.active_timers[ctx.author.id]).total_seconds() / 3600
        total_hours += current_session
    
    # Create embed for today's time
    embed = discord.Embed(
        title="Today's Time Track",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    embed.add_field(
        name="Total Time",
        value=f"{total_hours:.2f} hours ({int(total_hours * 60)} minutes)"
    )
    embed.set_footer(text=f"Requested by {ctx.author.name}")
    
    await ctx.send(embed=embed)

# Voice channel automation
@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel != after.channel:
        # Replace 'Your Channel Name' with the specific channel name you want to track
        target_channel_name = 'Timer Room'
        
        # User joined the target channel
        if after.channel and after.channel.name == target_channel_name:
            time_tracker.start_timer(member.id)
            channel = member.guild.get_channel(after.channel.id)
            if channel:
                await channel.send(f"Timer started for {member.name}")
        
        # User left the target channel
        if before.channel and before.channel.name == target_channel_name:
            duration = time_tracker.stop_timer(member.id)
            if duration:
                channel = member.guild.get_channel(before.channel.id)
                if channel:
                    await channel.send(f"{member.name}'s session duration: {duration:.2f} hours")

# Run the bot
if __name__ == "__main__":
    bot.run(TOKEN)