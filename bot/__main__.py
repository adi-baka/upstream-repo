#!/usr/bin/env python3
from asyncio import create_subprocess_exec, gather
from os import execl as osexecl
from signal import SIGINT, signal
from sys import executable
from time import time, monotonic
from uuid import uuid4

from aiofiles import open as aiopen
from aiofiles.os import path as aiopath
from aiofiles.os import remove as aioremove
from pyrogram.filters import command
from pyrogram.handlers import MessageHandler

from bot import (DATABASE_URL, INCOMPLETE_TASK_NOTIFIER, LOGGER,
                 STOP_DUPLICATE_TASKS, Interval, QbInterval, botStartTime, bot,
                 config_dict, scheduler, user_data)
from bot.helper.listeners.aria2_listener import start_aria2_listener

from .helper.ext_utils.bot_utils import get_readable_time, new_thread, set_commands, sync_to_async
from .helper.ext_utils.db_handler import DbManager
from .helper.ext_utils.fs_utils import clean_all, exit_clean_up, start_cleanup
from .helper.telegram_helper.bot_commands import BotCommands
from .helper.telegram_helper.filters import CustomFilters
from .helper.telegram_helper.message_utils import editMessage, sendFile, sendMessage, auto_delete_message
from .modules import (anonymous, authorize, bot_settings, cancel_mirror,
                      category_select, clone, eval, gd_count, gd_delete,
                      gd_search, leech_del, mirror_leech, rmdb, rss,
                      shell, status, torrent_search,
                      torrent_select, users_settings, ytdlp)


async def start(_, message):
    if len(message.command) > 1 and len(message.command[1]) == 36:
        userid = message.from_user.id
        input_token = message.command[1]
        if DATABASE_URL:
            stored_token = await DbManager().get_user_token(userid)
            if stored_token is None:
                return await sendMessage(message, '❗ This Token Is Not Associated With Your Account')
            if input_token != stored_token:
                return await sendMessage(message, '❗ Invalid Token')
        if userid not in user_data:
            return await sendMessage(message, '❗ This Token Is Not Yours')
        data = user_data[userid]
        if 'token' not in data or data['token'] != input_token:
            return await sendMessage(message, '❗ Token Already Used')
        token = str(uuid4())
        ttime = time()
        data['token'] = token
        data['time'] = ttime
        user_data[userid].update(data)
        if DATABASE_URL:
            await DbManager().update_user_tdata(userid, token, ttime)
        msg = '<b>✅ Token Activated Successfully</b>\n\n'
        msg += f'<b>⌛ Validity:</b> <code>{get_readable_time(int(config_dict["TOKEN_TIMEOUT"]))}</code>'
        return await sendMessage(message, msg)
    elif config_dict['DM_MODE'] and message.chat.type != message.chat.type.SUPERGROUP:
        start_string = '<b>🎉 Welcome to 𝗔𝗖𝗘</b>\n' \
                       '<i>🤖 I am a Mirror Leech Bot with 69K+ awesome features.</i>\n\n<b>ℹ Use Me:</b> @ACE_Mirror_Leech\n' \
                       '♥️ 𝗣𝗼𝘄𝗲𝗿𝗲𝗱 𝗕𝘆: @ACE_ML'
    elif not config_dict['DM_MODE'] and message.chat.type != message.chat.type.SUPERGROUP:
        start_string = '<b>🎉 Welcome to 𝗔𝗖𝗘</b>\n' \
                       '<i>🤖 I am a Mirror Leech Bot with 69K+ awesome features.</i>\n\n<b>ℹ Use Me:</b> @ACE_Mirror_Leech\n' \
                       '♥️ 𝗣𝗼𝘄𝗲𝗿𝗲𝗱 𝗕𝘆: @ACE_ML'
    else:
        tag = message.from_user.mention
        start_string = '<b><i>🕵️ Start Me In DM!</i></b>' \
                       f'\n<b>👤 User:</b> {tag}'
    await sendMessage(message, start_string)

async def restart(_, message):
    restart_message = await sendMessage(message, "<i><b>🔄 Restarting...</b></i>")
    if scheduler.running:
        scheduler.shutdown(wait=False)
    for interval in [QbInterval, Interval]:
        if interval:
            interval[0].cancel()
    await sync_to_async(clean_all)
    proc1 = await create_subprocess_exec('pkill', '-9', '-f', '-e', 'gunicorn|buffet|openstack|render|zcl')
    proc2 = await create_subprocess_exec('python3', 'update.py')
    await gather(proc1.wait(), proc2.wait())
    async with aiopen(".restartmsg", "w") as f:
        await f.write(f"{restart_message.chat.id}\n{restart_message.id}\n")
    osexecl(executable, executable, "-m", "bot")

async def ping(_, message):
    start_time = monotonic()
    reply = await sendMessage(message, "Pinging...")
    end_time = monotonic()
    ping_time = int((end_time - start_time) * 1000)
    botTime = get_readable_time(time() - botStartTime)
    remaining_time = 86400 - (time() - botStartTime)
    res_time = 'Soon' if remaining_time <= 0 else get_readable_time(remaining_time)
    await editMessage(reply, f'<b>🏓 Pong:</b> <code>{ping_time}ms</code>\n\n<b>⏰ Bot Uptime:</b> <code>{botTime}</code>\n<b>❗ Bot Restarts In:</b> <code>{res_time}</code>')

async def log(_, message):
    await sendFile(message, 'Z_Logs.txt')

help_string = f'''
<b>NOTE: Click on any CMD to see more detalis.</b>

/{BotCommands.MirrorCommand[0]} or /{BotCommands.MirrorCommand[1]}: Upload to Cloud Drive.

<b>Use qBit commands for torrents only:</b>
/{BotCommands.QbMirrorCommand[0]} or /{BotCommands.QbMirrorCommand[1]}: Download using qBittorrent and Upload to Cloud Drive.

/{BotCommands.BtSelectCommand}: Select files from torrents by gid or reply.
/{BotCommands.CategorySelect}: Change upload category for Google Drive.

<b>Use Yt-Dlp commands for YouTube or any videos:</b>
/{BotCommands.YtdlCommand[0]} or /{BotCommands.YtdlCommand[1]}: Mirror yt-dlp supported link.

<b>Use Leech commands for upload to Telegram:</b>
/{BotCommands.LeechCommand[0]} or /{BotCommands.LeechCommand[1]}: Upload to Telegram.
/{BotCommands.QbLeechCommand[0]} or /{BotCommands.QbLeechCommand[1]}: Download using qBittorrent and upload to Telegram(For torrents only).
/{BotCommands.YtdlLeechCommand[0]} or /{BotCommands.YtdlLeechCommand[1]}: Download using Yt-Dlp(supported link) and upload to telegram.

/leech{BotCommands.DeleteCommand} [telegram_link]: Delete replies from telegram (Only Owner & Sudo).

<b>G-Drive commands:</b>
/{BotCommands.CloneCommand}: Copy file/folder to Cloud Drive.
/{BotCommands.CountCommand} [drive_url]: Count file/folder of Google Drive.
/{BotCommands.DeleteCommand} [drive_url]: Delete file/folder from Google Drive (Only Owner & Sudo).

<b>Cancel Tasks:</b>
/{BotCommands.CancelMirror}: Cancel task by gid or reply.
/{BotCommands.CancelAllCommand[0]} : Cancel all tasks which added by you.
/{BotCommands.CancelAllCommand[1]} : Cancel your all tasks in all bots.

<b>Torrent/Drive Search:</b>
/{BotCommands.ListCommand} [query]: Search in Google Drive(s).
/{BotCommands.SearchCommand} [query]: Search for torrents with API.

<b>Bot Settings:</b>
/{BotCommands.UserSetCommand}: Open User settings.
/{BotCommands.UsersCommand}: show users settings (Only Owner & Sudo).
/{BotCommands.BotSetCommand}: Open Bot settings (Only Owner & Sudo).

<b>Authentication:</b>
/{BotCommands.AuthorizeCommand}: Authorize a chat or a user to use the bot (Only Owner & Sudo).
/{BotCommands.UnAuthorizeCommand}: Unauthorize a chat or a user to use the bot (Only Owner & Sudo).
/{BotCommands.AddSudoCommand}: Add sudo user (Only Owner).
/{BotCommands.RmSudoCommand}: Remove sudo users (Only Owner).

<b>Bot Stats:</b>
/{BotCommands.StatusCommand[0]} or /{BotCommands.StatusCommand[1]}: Shows a status of all active tasks.
/{BotCommands.StatsCommand[0]} or /{BotCommands.StatsCommand[1]}: Show server stats.
/{BotCommands.PingCommand[0]} or /{BotCommands.PingCommand[1]}: Check how long it takes to Ping the Bot.

<b>Database Management:</b>
/{BotCommands.RmdbCommand}: To remove active tasks from database (Only Owner & Sudo).
/{BotCommands.RmalltokensCommand}: To remove all access tokens from database (Only Owner & Sudo).

<b>Maintainance:</b>
/{BotCommands.RestartCommand[0]}: Restart and update the bot (Only Owner & Sudo).
/{BotCommands.RestartCommand[1]}: Restart and update all bots (Only Owner & Sudo).
/{BotCommands.LogCommand}: Get a log file of the bot. Handy for getting crash reports (Only Owner & Sudo).

<b>Extras:</b>
/{BotCommands.ShellCommand}: Run shell commands (Only Owner).
/{BotCommands.EvalCommand}: Run Python Code Line | Lines (Only Owner).
/{BotCommands.ExecCommand}: Run Commands In Exec (Only Owner).
/{BotCommands.ClearLocalsCommand}: Clear {BotCommands.EvalCommand} or {BotCommands.ExecCommand} locals (Only Owner).

<b>RSS Feed:</b>
/{BotCommands.RssCommand}: Open RSS Menu.

<b>Attention: Read the first line again!</b>
'''

@new_thread
async def bot_help(_, message):
    hmsg = await sendMessage(message, help_string)
    await auto_delete_message(message, hmsg)


async def restart_notification():
    if await aiopath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
    else:
        chat_id, msg_id = 0, 0

    async def send_incompelete_task_message(cid, msg):
        try:
            if msg.startswith('<i><b>✅ #Restarted Successfully</b></i>'):
                await bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text='<i><b>✅ #Restarted Successfully</b></i>')
                await bot.send_message(chat_id, msg, disable_web_page_preview=True, reply_to_message_id=msg_id)
                await aioremove(".restartmsg")
            else:
                await bot.send_message(chat_id=cid, text=msg, disable_web_page_preview=True,
                                       disable_notification=True)
        except Exception as e:
            LOGGER.error(e)
    if DATABASE_URL:
        if INCOMPLETE_TASK_NOTIFIER and (notifier_dict := await DbManager().get_incomplete_tasks()):
            for cid, data in notifier_dict.items():
                msg = '<i><b>✅ #Restarted Successfully</b></i>' if cid == chat_id else '<i><b>❗ Bot #Restarted</b></i>'
                for tag, links in data.items():
                    msg += f"\n\n<b>👤 User:</b> {tag}\nAdd Your Tasks Again!\n"
                    for index, link in enumerate(links, start=1):
                        msg += f" {index}: {link} \n"
                        if len(msg.encode()) > 4000:
                            await send_incompelete_task_message(cid, msg)
                            msg = ''
                if msg:
                    await send_incompelete_task_message(cid, msg)

        if STOP_DUPLICATE_TASKS:
            await DbManager().clear_download_links()


    if await aiopath.isfile(".restartmsg"):
        try:
            await bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text='<i><b>✅ #Restarted Successfully</b></i>')
        except:
            pass
        await aioremove(".restartmsg")


async def main():
    await gather(start_cleanup(), torrent_search.initiate_search_tools(), restart_notification(), set_commands(bot))
    await sync_to_async(start_aria2_listener, wait=False)

    bot.add_handler(MessageHandler(start,   filters=command(BotCommands.StartCommand)))
    bot.add_handler(MessageHandler(log,     filters=command(BotCommands.LogCommand)     & CustomFilters.sudo))
    bot.add_handler(MessageHandler(restart, filters=command(BotCommands.RestartCommand) & CustomFilters.sudo))
    bot.add_handler(MessageHandler(ping,    filters=command(BotCommands.PingCommand)    & CustomFilters.authorized))
    bot.add_handler(MessageHandler(bot_help,filters=command(BotCommands.HelpCommand)    & CustomFilters.authorized))
    LOGGER.info("Bot Started Successfully!")
    signal(SIGINT, exit_clean_up)

bot.loop.run_until_complete(main())
bot.loop.run_forever()
