import json
from datetime import datetime, timedelta
import calendar
import os
from discord import Embed, SelectOption, ui
from discord.ext import commands

class TimeFormatView(ui.View):
    def __init__(self, time_tracker, month=None, year=None):
        super().__init__(timeout=30)
        self.format = "hours"
        self.response = None
        self.time_tracker = time_tracker
        self.month = month if month else datetime.now().month
        self.year = year if year else datetime.now().year

    @ui.select(
    placeholder="Select time format",
    options=[
        SelectOption(label="Hours", value="hours", description="Display time in hours"),
        SelectOption(label="Minutes", value="minutes", description="Display time in minutes")
    ])
    async def select_format(self, interaction, select):
        self.format = select.values[0]
        self.response = True
        
        cal_data, total_time = self.time_tracker.get_month_calendar(
            interaction.user.id,
            year=self.year,
            month=self.month,
            time_format=self.format
        )
        new_embed = self.time_tracker.create_calendar_embed(
            interaction.user.id,
            cal_data,
            total_time,
            time_format=self.format,
            month=self.month,
            year=self.year
        )
        await interaction.response.edit_message(embed=new_embed, view=self)

class TimeTracker:
    def __init__(self):
        self.data_file = "time_data.json"
        self.active_timers = {}
        self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                self.time_data = json.load(f)
        else:
            self.time_data = {}

    def save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.time_data, f)

    def start_timer(self, user_id):
        self.active_timers[user_id] = datetime.now()

    def stop_timer(self, user_id):
        if user_id in self.active_timers:
            start_time = self.active_timers[user_id]
            duration = (datetime.now() - start_time).total_seconds() / 3600  # Hours
            
            date_str = start_time.strftime("%Y-%m-%d")
            if date_str not in self.time_data:
                self.time_data[date_str] = {}
            
            if str(user_id) not in self.time_data[date_str]:
                self.time_data[date_str][str(user_id)] = 0
            
            self.time_data[date_str][str(user_id)] += duration
            del self.active_timers[user_id]
            self.save_data()
            return duration
        return None

    def get_month_calendar(self, user_id, year=None, month=None, time_format="hours"):
        if year is None or month is None:
            now = datetime.now()
            year = now.year
            month = now.month

        cal = calendar.monthcalendar(year, month)
        formatted_cal = []
        total_time = 0

        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    week_data.append("   ")
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    hours = 0
                    if date_str in self.time_data and str(user_id) in self.time_data[date_str]:
                        hours = self.time_data[date_str][str(user_id)]
                    
                    total_time += hours
                    if time_format == "minutes":
                        minutes = int(hours * 60)
                        week_data.append(f"{day:2d}:{minutes:3d}")
                    else:
                        week_data.append(f"{day:2d}: {int(hours):2d}")
            formatted_cal.append(week_data)

        if time_format == "minutes":
            total_time = int(total_time * 60)
        else:
            total_time = round(total_time, 1)

        return formatted_cal, total_time

    def get_daily_time(self, user_id, date_str=None):
        """Get total time for a specific date"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        total_hours = 0
        if date_str in self.time_data and str(user_id) in self.time_data[date_str]:
            total_hours = self.time_data[date_str][str(user_id)]
        
        # Add current session if there's an active timer
        if user_id in self.active_timers:
            current_session = (datetime.now() - self.active_timers[user_id]).total_seconds() / 3600
            total_hours += current_session
        
        return total_hours
    
    def create_calendar_embed(self, user_id, cal_data, total_time, time_format="hours", month=None, year=None):
        # Use provided month and year or current date
        if month is None or year is None:
            current_date = datetime.now()
            month = month if month else current_date.month
            year = year if year else current_date.year
        
        month_name = calendar.month_name[month]
        
        embed = Embed(title=f"Time Tracking Calendar - {month_name} {year}", color=0x00ff00)
        
        # Create more compact calendar grid
        calendar_str = "```ansi\n"
        # Header
        calendar_str += "  Mo  |  Tu  |  We  |  Th  |  Fr  |  Sa  |  Su  \n"
        calendar_str += "────────────────────────────────────────────────\n"
        
        # Calendar data
        for week in cal_data:
            line = ""
            for day in week:
                if day == "   ":
                    line += "       "
                else:
                    day_num, time_val = day.split(":")
                    line += f"\u001b[34m{day_num:2}\u001b[0m:{time_val} "
            calendar_str += f"{line.rstrip()}\n"
        
        calendar_str += "```"
        
        embed.add_field(name="Calendar", value=calendar_str, inline=False)
        
        # Add total time field
        unit = "hours" if time_format == "hours" else "minutes"
        embed.add_field(name="Total Time", value=f"{total_time} {unit}", inline=False)
        
        return embed