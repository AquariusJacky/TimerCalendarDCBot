import json
from datetime import datetime, timedelta
import calendar
import os
from discord import Embed, SelectOption, ui
from discord.ext import commands

class TimeFormatView(ui.View):
    def __init__(self):
        super().__init__(timeout=30)  # Add timeout
        self.format = "hours"
        self.response = None

    @ui.select(
        placeholder="Select time format",
        options=[
            SelectOption(label="Hours", value="hours", description="Display time in hours"),
            SelectOption(label="Minutes", value="minutes", description="Display time in minutes")
        ]
    )
    async def select_format(self, interaction, select):
        self.format = select.values[0]
        self.response = interaction
        await interaction.response.defer()
        self.stop()  # Stop waiting after selection

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
                        week_data.append(f"{day:2d}:{hours:3.1f}")
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
    
    def create_calendar_embed(self, user_id, cal_data, total_time, time_format="hours"):
        month_name = calendar.month_name[datetime.now().month]
        year = datetime.now().year
        
        embed = Embed(title=f"Time Tracking Calendar - {month_name} {year}", color=0x00ff00)
        
        # Create calendar grid with formatted spacing
        calendar_str = "```\nMo  Tu  We  Th  Fr  Sa  Su\n"
        for week in cal_data:
            calendar_str += " ".join(f"{day:6}" for day in week) + "\n"
        calendar_str += "```"
        
        embed.add_field(name="Calendar", value=calendar_str, inline=False)
        
        unit = "hours" if time_format == "hours" else "minutes"
        embed.add_field(name="Total Time", value=f"{total_time} {unit}", inline=False)
        
        return embed