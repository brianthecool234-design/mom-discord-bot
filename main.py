import os
import sqlite3
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

# =====================================================
# M.O.M. - MANAGEMENT OF MISSING ASSIGNMENTS
# Version 1.0
# =====================================================

# ---------------- CONFIGURATION ----------------

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

MYANMAR_TZ = timezone(timedelta(hours=6, minutes=30))

DB_PATH = "database/homework.db"

os.makedirs("database", exist_ok=True)

# ---------------- DATABASE ----------------

def init_database():
      with sqlite3.connect(DB_PATH) as db:
                db.execute("""
                            CREATE TABLE IF NOT EXISTS homework (
                                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                            subject TEXT NOT NULL,
                                                                            description TEXT NOT NULL,
                                                                                            deadline TEXT NOT NULL,
                                                                                                            channel_id INTEGER NOT NULL,
                                                                                                                            reminder_sent INTEGER DEFAULT 0,
                                                                                                                                            due_sent INTEGER DEFAULT 0,
                                                                                                                                                            completed INTEGER DEFAULT 0
                                                                                                                                                                        )
                                                                                                                                                                                """)

  # ---------------- BOT SETUP ----------------

intents = discord.Intents.default()

class MOMBot(commands.Bot):

      async def setup_hook(self):
                init_database()

          if GUILD_ID:
              guild = discord.Object(id=GUILD_ID)

            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)

            print("Guild slash commands synchronized.")

else:
            await self.tree.sync()
              print("Global slash commands synchronized.")

bot = MOMBot(
      command_prefix="!",
      intents=intents
)

# ---------------- SECURITY ----------------

def owner_only(interaction: discord.Interaction):
      return (
                OWNER_ID != 0
                and interaction.user.id == OWNER_ID
      )

# ---------------- STARTUP ----------------

@bot.event
async def on_ready():

      print("------------------------------------")
    print("       M.O.M. SYSTEM ONLINE")
    print("------------------------------------")
    print(f"Bot: {bot.user}")
    print("Management Of Missing Assignments")
    print("Status: Operational")
    print("------------------------------------")

    if not reminder_scheduler.is_running():
              reminder_scheduler.start()

# =====================================================
# COMMAND 1: ADD HOMEWORK
# =====================================================

@bot.tree.command(
      name="addhomework",
      description="Register a new homework assignment."
)
@app_commands.check(owner_only)
@app_commands.describe(
      subject="Subject name",
      description="Homework instructions",
      deadline="YYYY-MM-DD HH:MM (Myanmar time)"
)
async def addhomework(
      interaction: discord.Interaction,
      subject: str,
      description: str,
      deadline: str
):

      try:
                due = datetime.strptime(
                              deadline,
                              "%Y-%m-%d %H:%M"
                ).replace(tzinfo=MYANMAR_TZ)

except ValueError:

        await interaction.response.send_message(
                      "Invalid date format. Use YYYY-MM-DD HH:MM.",
                      ephemeral=True
        )
        return

    if due <= datetime.now(MYANMAR_TZ):

              await interaction.response.send_message(
                            "That deadline has already passed. "
                            "Time travel is not currently supported.",
                            ephemeral=True
              )
              return

    if not interaction.guild or not interaction.channel:

              await interaction.response.send_message(
                            "Please use this command inside the class server.",
                            ephemeral=True
              )
              return

    with sqlite3.connect(DB_PATH) as db:

              cursor = db.execute("""
                          INSERT INTO homework
                                      (subject, description, deadline, channel_id)
                                                  VALUES (?, ?, ?, ?)
                                                          """, (
                            subject,
                            description,
                            due.isoformat(),
                            interaction.channel.id
              ))

        assignment_id = cursor.lastrowid

    embed = discord.Embed(
              title="NEW HOMEWORK ASSIGNMENT",
              description=description,
              color=discord.Color.blue()
    )

    embed.add_field(
              name="Subject",
              value=subject,
              inline=True
    )

    embed.add_field(
              name="Deadline",
              value=due.strftime("%d %B %Y, %I:%M %p"),
              inline=True
    )

    embed.add_field(
              name="Assignment ID",
              value=str(assignment_id),
              inline=False
    )

    embed.set_footer(
              text="M.O.M. | Management Of Missing Assignments"
    )

    await interaction.channel.send(embed=embed)

    await interaction.response.send_message(
              f"Assignment #{assignment_id} successfully registered.",
              ephemeral=True
    )

# =====================================================
# COMMAND 2: VIEW HOMEWORK
# =====================================================

@bot.tree.command(
      name="homework",
      description="View all unfinished homework."
)
async def homework(interaction: discord.Interaction):

      with sqlite3.connect(DB_PATH) as db:

                rows = db.execute("""
                            SELECT id, subject, description, deadline
                                        FROM homework
                                                    WHERE completed = 0
                                                                ORDER BY deadline ASC
                                                                        """).fetchall()

    if not rows:

              await interaction.response.send_message(
                            "No unfinished homework found.\n"
                            "Either everyone is productive or something is wrong.",
              )
              return

    embed = discord.Embed(
              title="M.O.M. | HOMEWORK REGISTER",
              color=discord.Color.blue()
    )

    for row in rows[:10]:

              assignment_id, subject, description, deadline = row

        due = datetime.fromisoformat(deadline)

        embed.add_field(
                      name=f"#{assignment_id} | {subject}",
                      value=(
                                        f"{description[:300]}\n"
                                        f"Deadline: {due.strftime('%d %b %Y, %I:%M %p')}"
                      ),
                      inline=False
        )

    embed.set_footer(
              text=f"Showing {min(len(rows), 10)} of {len(rows)} assignments."
    )

    await interaction.response.send_message(embed=embed)

# =====================================================
# COMMAND 3: UPCOMING DEADLINES
# =====================================================

@bot.tree.command(
      name="upcoming",
      description="View upcoming homework deadlines."
)
async def upcoming(interaction: discord.Interaction):

      with sqlite3.connect(DB_PATH) as db:

                rows = db.execute("""
                            SELECT id, subject, deadline
                                        FROM homework
                                                    WHERE completed = 0
                                                                ORDER BY deadline ASC
                                                                            LIMIT 10
                                                                                    """).fetchall()

    if not rows:

              await interaction.response.send_message(
                            "No upcoming deadlines. Enjoy the peace while it lasts."
              )
              return

    embed = discord.Embed(
              title="UPCOMING DEADLINES",
              color=discord.Color.orange()
    )

    for assignment_id, subject, deadline in rows:

              due = datetime.fromisoformat(deadline)

        embed.add_field(
                      name=f"#{assignment_id} | {subject}",
                      value=due.strftime("%d %B %Y, %I:%M %p"),
                      inline=False
        )

    await interaction.response.send_message(embed=embed)

# =====================================================
# COMMAND 4: MARK HOMEWORK COMPLETED
# =====================================================

@bot.tree.command(
      name="completed",
      description="Mark homework as completed."
)
@app_commands.check(owner_only)
async def completed(
      interaction: discord.Interaction,
      assignment_id: int
):

      with sqlite3.connect(DB_PATH) as db:

                cursor = db.execute("""
                            UPDATE homework
                                        SET completed = 1
                                                    WHERE id = ? AND completed = 0
                                                            """, (assignment_id,))

    if cursor.rowcount:

              message = (
                            f"Assignment #{assignment_id} marked as completed.\n"
                            "M.O.M. is temporarily impressed."
              )

else:

        message = (
                      "Assignment not found or already completed."
        )

    await interaction.response.send_message(
              message,
              ephemeral=True
    )

# =====================================================
# COMMAND 5: DELETE HOMEWORK
# =====================================================

@bot.tree.command(
      name="deletehomework",
      description="Delete a homework assignment."
)
@app_commands.check(owner_only)
async def deletehomework(
      interaction: discord.Interaction,
      assignment_id: int
):

      with sqlite3.connect(DB_PATH) as db:

                cursor = db.execute("""
                            DELETE FROM homework
                                        WHERE id = ?
                                                """, (assignment_id,))

    if cursor.rowcount:

              message = f"Assignment #{assignment_id} deleted."

else:

        message = "Assignment not found."

    await interaction.response.send_message(
              message,
              ephemeral=True
    )

# =====================================================
# AUTOMATIC REMINDER SYSTEM
# =====================================================

@tasks.loop(seconds=60)
async def reminder_scheduler():

      now = datetime.now(MYANMAR_TZ)

    with sqlite3.connect(DB_PATH) as db:

              rows = db.execute("""
                          SELECT id, subject, deadline, channel_id,
                                             reminder_sent, due_sent
                                                         FROM homework
                                                                     WHERE completed = 0
                                                                             """).fetchall()

    for row in rows:

              (
                            assignment_id,
                            subject,
                            deadline,
                            channel_id,
                            reminder_sent,
                            due_sent
              ) = row

        due = datetime.fromisoformat(deadline)

        channel = bot.get_channel(channel_id)

        if channel is None:

                      try:
                                        channel = await bot.fetch_channel(channel_id)

                      except discord.HTTPException:
                                        continue

                  # 24-HOUR REMINDER

        if (
                      not reminder_sent
                      and now >= due - timedelta(hours=24)
                      and now < due
        ):

                      try:

                                        await channel.send(
                                                              f"**M.O.M. | 24-HOUR WARNING**\n\n"
                                                              f"Subject: {subject}\n"
                                                              f"Assignment: #{assignment_id}\n"
                                                              f"Deadline: {due.strftime('%d %B %Y, %I:%M %p')}\n\n"
                                                              "Your homework is due within 24 hours.\n"
                                                              "Procrastination is not a submission method."
                                        )

                          with sqlite3
