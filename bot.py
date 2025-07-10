import discord
from discord.ext import commands
from auth import *
from config import DISCORD_BOT_TOKEN

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot is ready as {bot.user}")

@bot.command()
async def create(ctx, username, password, expiry):
    if create_user(username, password, expiry):
        await ctx.send(f"✅ Created `{username}` with expiry `{expiry}`.")
    else:
        await ctx.send("❌ Username already exists.")

@bot.command()
async def delete(ctx, username):
    if delete_user(username):
        await ctx.send(f"🗑️ Deleted `{username}`.")
    else:
        await ctx.send("❌ User not found.")

@bot.command()
async def pause(ctx, username):
    if pause_user(username, True):
        await ctx.send(f"⏸️ Paused `{username}`.")
    else:
        await ctx.send("❌ User not found.")

@bot.command()
async def unpause(ctx, username):
    if pause_user(username, False):
        await ctx.send(f"▶️ Unpaused `{username}`.")
    else:
        await ctx.send("❌ User not found.")

@bot.command()
async def reset_hwid(ctx, username):
    if reset_hwid(username):
        await ctx.send(f"🔁 HWID reset for `{username}`.")
    else:
        await ctx.send("❌ User not found.")

@bot.command()
async def sendmsg(ctx, username, *, message):
    if send_message(username, message):
        await ctx.send(f"📩 Sent message to `{username}`.")
    else:
        await ctx.send("❌ User not found.")

@bot.command()
async def info(ctx, username):
    user = get_user_info(username)
    if user:
        embed = discord.Embed(title=f"👤 Info for `{username}`", color=0x00ff00)
        embed.add_field(name="Password", value=user['password'], inline=True)
        embed.add_field(name="Expiry", value=user['expiry'], inline=True)
        embed.add_field(name="Paused", value=str(user['paused']), inline=True)
        embed.add_field(name="HWID", value=user['hwid'], inline=False)
        embed.add_field(name="Message", value=user['message'], inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ User not found.")

@bot.command()
async def all_users(ctx):
    users = get_all_users()
    await ctx.send("📋 All users:\n" + ", ".join(users.keys()))

@bot.command()
async def export(ctx):
    data = export_users()
    with open("exported_users.json", "w") as f:
        f.write(data)
    await ctx.send(file=discord.File("exported_users.json"))

bot.run(DISCORD_BOT_TOKEN)
