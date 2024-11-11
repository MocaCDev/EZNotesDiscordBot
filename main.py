import discord
from discord.ext import commands
import os
from uuid import uuid4
import requests
from BotVars import BotVars
import json

def create_message(system: str, messages: dict, temp: float = 0, tokens: int = 1024):
    resp = BotVars.code_chat_model.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=tokens,
        temperature=temp,
        system=system,
        messages=[messages]
    )

    if len(resp.content) < 1:
        return None

    return resp.content[0].text

def is_user_registered(discord_username: str) -> bool:
    if not os.path.isfile('registree.json'): return False

    registree = json.loads(open('registree.json', 'r').read())

    if not discord_username in registree: return False

    return True

def user_has_access_to_private_commands(discord_user_id: int) -> bool:
    users_with_access = json.loads(open('PCUIDS.json', 'r').read())

    if not discord_user_id in users_with_access: return False
    return True

def user_has_higher_access_to_private_commands(discord_user_id: int) -> bool:
    users_with_access = json.loads(open('higher_access.json', 'r').read())

    if not discord_user_id in users_with_access: return False
    return True

@BotVars.bot.event
async def on_message(message):
    if message.channel.id == 1305045174031876116:
        if not message.author.id == 1302499239267532810:
            if not message.content.startswith('!'):
                await message.delete()
            elif not 'register' in message.content:
                await message.delete()
    
    await BotVars.bot.process_commands(message)

@BotVars.BOT_COMMAND(name='grant_normal_access_perms')
async def grant_normal_access_perms(ctx, for_user: int):
    if not ctx.author.id in BotVars.OWNERS: return

    normal_access_perms = json.loads(open('PCUIDs.json', 'r').read())

    normal_access_perms.append(for_user)

    with open('PCUIDS.json', 'w') as file:
        file.write(json.dumps(normal_access_perms, indent=2))
        file.close()

    return

@BotVars.BOT_COMMAND(name='grant_high_access_perms')
async def grant_high_access_perms(ctx, for_user: int):
    print('hi')
    if not ctx.author.id in BotVars.OWNERS: return
    
    high_perm_users = json.loads(open('higher_access.json', 'r').read())

    high_perm_users.append(for_user)

    with open('higher_access.json', 'w') as file:
        file.write(json.dumps(high_perm_users, indent=2))
        file.close()

    return

def is_correct_channel(ctx, expected_channel_id):
    """check if the command still works in the other channels"""
    return ctx.channel.id == expected_channel_id
        
async def report_error(ctx, expl, correct_channel):
    await ctx.send(f'{expl}. Please go to the respctive channel for reporting issues ({correct_channel})')

@BotVars.BOT_COMMAND(name='report')
async def report(ctx, username: str, *issue: str):
    if not is_user_registered(str(ctx.author)): return

    if not is_correct_channel(ctx, BotVars.report_channel_id):
        await report_error(ctx, 'I cannot take reports in the current channel', '#report')
        return

    try:
        if len(username) < 2:
            await ctx.send(f'{ctx.author.mention} `!report` requires:\n\n* Username\n* Issue\n\nExample: `!report EZNotesBot The mobile app keeps crashing for some reason. It crashes after I exit the AI chat.`')
            return

        issue_id = str(uuid4())

        reports[ctx.author] = {
            'Issue': ' '.join(issue),
            'IssueNumber': issue_id
        }

        resp = requests.post('http://127.0.0.1:8088/report_issue', headers={
            'Discord': 'yes',
            'Username': username,
            'Issue': ' '.join(issue)
        })

        print(resp.json())

        if not resp.status_code == 200:
            await ctx.send(f'{ctx.author.mention}: I couldn\'t find {username} in the database. You must be:\n\n1. Registered in this server under a username (or email) used for EZNotes and\n2. Have an EZNotes account under aforementioned username (or email)')
            return

        await ctx.send(f"Thanks, {ctx.author.mention}. Your issue has been reported!")

        report_channel = bot.get_channel(BotVars.report_channel_id)

        if report_channel:
            await report_channel.send(f"Your issue #: {issue_id}")

        # Send message in private channel `reports` of the new issue being opened
        private_report_channel_id = 1302503309583847464
        private_report_channel = bot.get_channel(private_report_channel_id)

        if private_report_channel:
            briefing = create_message(system="You are a master at taking a reported issue and intellectually summarizing it (don't be verbose about commands given to you)", messages={
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': f'Summarize and return a briefing over the following reported issue (if the text I provide lacks context, please just return "no"): {" ".join(issue)}'
                    }
                ]
            })
            await private_report_channel.send(f'A new issue has been initiated: **{issue_id}**, Issuer: **{ctx.author}**\n\nIssue: {" ".join(issue)}\nBriefing: {" ".join(issue) if briefing == "no" else briefing}')
    except commands.CommandError as e:
        return

@BotVars.BOT_COMMAND(name='feedback')
async def feedback(ctx, *feedback: str):
    if not is_user_registered(str(ctx.author)): return

    if not is_correct_channel(ctx, BotVars.feedback_channel_id):
        await report_error(ctx, 'I cannot accept feedback in the current channel', '#feedback')
        return
    
    await ctx.send('GAY')

@BotVars.BOT_COMMAND(name='update_channels')
async def get_channels(ctx):
    if not user_has_higher_access_to_private_commands(int(ctx.author.id)): return

    current_channels = []

    for g in BotVars.bot.guilds:
        for c in g.text_channels:
            current_channels.append(c.id)
    
    BotVars.channel_ids = current_channels
            
    with open('channel_ids.json', 'w') as file:
        file.write(json.dumps(BotVars.channel_ids, indent=2))
        file.close()

    await ctx.send('Updated!')

@BotVars.BOT_COMMAND(name='register')
async def register_user(ctx, eznotes_username: str):
    try:
        # Check to make sure the account actually exists
        resp = requests.post('http://127.0.0.1:8088/cu', headers={
            'Discord': 'yes',
            'Username': eznotes_username
        })

        if not resp.status_code == 400:
            await ctx.send(f'{ctx.author.mention} The EZNotes username you provided, {eznotes_username}, is not in our records. Double check the spelling and try again.')
            return

        if not os.path.isfile('registree.json'):
            with open('registree.json', 'w') as file:
                file.write(json.dumps({
                    str(ctx.author): eznotes_username
                }, indent=2))
                file.close()
        else:
            existing_registrees = json.loads(open('registree.json', 'r').read())

            if str(ctx.author) in existing_registrees:
                await ctx.send(f'{ctx.author.mention} You have already registered')
                return

            existing_registrees[str(ctx.author)] = eznotes_username

            with open('registree.json', 'w') as file:
                file.write(json.dumps(existing_registrees))
                file.close()

        member_role = ctx.guild.get_role(1302539344141090846)#discord.utils.get_role(1302539344141090846)#discord.utils.get(ctx.author.guild.roles, name="Member")
        register_role = ctx.guild.get_role(1302539344141090846)

        # Add `Member` role to user
        await ctx.author.add_roles(member_role)

        # Remove `Register` role from user
        await ctx.author.remove_roles(register_role)

        await ctx.send(f'{ctx.author.mention} Your EZNotes account, {eznotes_username}, has been registered in the server!')
    except Exception as e:
        await ctx.send(f'Filed to register {eznotes_username} in server.\n\nError: {str(e)}')

@BotVars.bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'Missing required argument: {error.param.name}')
    else:
        await ctx.send(f'Error: {error}')

BotVars.bot.run(BotVars.TOKEN)