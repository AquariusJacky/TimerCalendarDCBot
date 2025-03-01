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
bot.remove_command('help')  # Add this line to remove default help command

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
async def show_calendar(ctx, month: int = None):
    """Display calendar with time tracking for specified month (or current month if not specified)"""
    # ...existing deletion code...
    
    current_date = datetime.now()
    year = current_date.year
    month = month if month else current_date.month
    
    # Validate month input
    if month not in range(1, 13):
        await ctx.send("Please enter a valid month (1-12)")
        return
    
    # Pass month and year to TimeFormatView
    view = TimeFormatView(time_tracker, month=month, year=year)
    cal_data, total_time = time_tracker.get_month_calendar(ctx.author.id, year=year, month=month)
    embed = time_tracker.create_calendar_embed(
        ctx.author.id, 
        cal_data, 
        total_time,
        month=month,
        year=year
    )
    
    await ctx.send(embed=embed, view=view)

@bot.command(name="start")
async def start_timer(ctx):
    """Start timer for the user"""
    time_tracker.start_timer(ctx.author.id)
    await ctx.send(f"Timer started for {ctx.author.name}")

@bot.command(name="stop")
async def stop_timer(ctx):
    """Stop timer for the user"""
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

@bot.command(name="help")
async def show_help(ctx):
    """Show all available commands and their usage"""
    embed = discord.Embed(
        title="Timer Calendar Bot - Help Guide",
        description="Track your time with these commands:",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )

    commands_info = {
        "`!start`": "Start tracking your time",
        "`!stop`": "Stop tracking your time and see session duration",
        "`!today`": "View your total tracked time for today",
        "`!calendar [month]`": "Display monthly calendar with daily time tracking\n"
                    "• Optional: specify month number (1-12)\n"
                    "• Use the dropdown menu to switch between hours/minutes view\n"
                    "• Format: day:time (e.g., 15:3 means 3 hours on the 15th)",
        "`!help`": "Show this help message",
        "`!ping`": "Check if bot is responsive"
    }

    for cmd, desc in commands_info.items():
        embed.add_field(name=cmd, value=desc, inline=False)

    embed.set_footer(text=f"Requested by {ctx.author.name}")
    await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    bot.run(TOKEN)