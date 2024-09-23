#!/usr/bin/env python3
from time import time
from datetime import datetime as dt
from httpx import AsyncClient as xclient
from aiofiles.os import path as aiopath

from psutil import boot_time, cpu_count, cpu_freq, cpu_percent, disk_usage, swap_memory, virtual_memory, net_io_counters
from pyrogram.filters import command, regex
from pyrogram.handlers import CallbackQueryHandler, MessageHandler

from bot import (Interval, bot, botStartTime, config_dict, download_dict,
                 download_dict_lock, status_reply_dict_lock, LOGGER)
from bot.helper.ext_utils.bot_utils import (cmd_exec, getAllDownload, get_progress_bar_string, get_readable_file_size,
                                            get_readable_time, MirrorStatus, new_task, setInterval, turn_page)
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import (auto_delete_message, deleteMessage, isAdmin, request_limiter,
                                                      sendMessage, sendStatusMessage, update_all_messages)


@new_task
async def mirror_status(_, message):
    async with download_dict_lock:
        count = len(download_dict)
    if count == 0:
        currentTime = get_readable_time(time() - botStartTime)
        free = get_readable_file_size(disk_usage(config_dict['DOWNLOAD_DIR']).free)
        msg = '\n\n💩 No Active Tasks!\n━━━━━━━━━━━━━━━━━━━━'
        msg += f"\n<b>🖥️ CPU</b>: {cpu_percent()}% | <b>📭 Free</b>: {free}" \
               f"\n<b>💽 RAM</b>: {virtual_memory().percent}% | <b>⏰ Uptime</b>: {currentTime}"
        reply_message = await sendMessage(message, msg)
        await auto_delete_message(message, reply_message)
    else:
        await sendStatusMessage(message)
        await deleteMessage(message)
        async with status_reply_dict_lock:
            if Interval:
                Interval[0].cancel()
                Interval.clear()
                Interval.append(setInterval(config_dict['STATUS_UPDATE_INTERVAL'], update_all_messages))

@new_task
async def status_pages(_, query):
    user_id = query.from_user.id
    spam = not await isAdmin(query.message, user_id) and await request_limiter(query=query)
    if spam:
        return
    if not await isAdmin(query.message, user_id) and user_id and not await getAllDownload('all', user_id):
        await query.answer("You don't have any active tasks", show_alert=True)
        return
    data = query.data.split()
    action = data[1]
    if action == "stats":
        bstats = bot_sys_stats()
        await query.answer(bstats, show_alert=True)
    else:
        await turn_page(data)
        await update_all_messages(True)


def bot_sys_stats():
    cpup = cpu_percent(interval=0.1)
    ramp = virtual_memory().percent
    disk = disk_usage(config_dict["DOWNLOAD_DIR"]).percent
    totl = len(download_dict)
    traf = get_readable_file_size(net_io_counters().bytes_sent + net_io_counters().bytes_recv)
    free = max(config_dict['QUEUE_ALL'] - totl, 0) if config_dict['QUEUE_ALL'] else '∞'
    inqu, dwld, upld, splt, arch, extr, seed = [0] * 7
    for download in download_dict.values():
        status = download.status()
        if status in MirrorStatus.STATUS_QUEUEDL or status in MirrorStatus.STATUS_QUEUEUP:
            inqu += 1
        elif status == MirrorStatus.STATUS_DOWNLOADING:
            dwld += 1
        elif status == MirrorStatus.STATUS_UPLOADING:
            upld += 1
        elif status == MirrorStatus.STATUS_SPLITTING:
            splt += 1
        elif status == MirrorStatus.STATUS_ARCHIVING:
            arch += 1
        elif status == MirrorStatus.STATUS_EXTRACTING:
            extr += 1
        elif status == MirrorStatus.STATUS_SEEDING:
            seed += 1
    bmsg = f'📊 𝗔𝗖𝗘 - 𝗦𝘁𝗮𝘁𝗶𝘀𝘁𝗶𝗰𝘀\n\n'
    bmsg += f'🚧 Tasks: {totl}\n'
    bmsg += f'👷‍♂️ Available: {free} | 💤 Queued: {inqu}\n\n'
    bmsg += f'⬇️ DL: {dwld} | ⬆️ UL: {upld}\n'
    bmsg += f'✂️ Split: {splt} | 🌨️ Seed: {seed}\n'
    bmsg += f'🔐 Archive: {arch} | 🗃️ Extract: {extr}\n'
    bmsg += f'📶 Bandwidth: {traf}\n\n'
    bmsg += f'♥️ 𝗣𝗼𝘄𝗲𝗿𝗲𝗱 𝗕𝘆 @𝗔𝗖𝗘_𝗠𝗟'
    return bmsg


async def stats(_, message, edit_mode=False):
    buttons = ButtonMaker()
    sysTime     = get_readable_time(time() - boot_time())
    botTime     = get_readable_time(time() - botStartTime)
    remaining_time = 86400 - (time() - botStartTime)
    res_time = '⚠️ Soon ⚠️' if remaining_time <= 0 else get_readable_time(remaining_time)
    total, used, free, disk = disk_usage('/')
    total       = get_readable_file_size(total)
    used        = get_readable_file_size(used)
    free        = get_readable_file_size(free)
    sent        = get_readable_file_size(net_io_counters().bytes_sent)
    recv        = get_readable_file_size(net_io_counters().bytes_recv)
    tb          = get_readable_file_size(net_io_counters().bytes_sent + net_io_counters().bytes_recv)
    cpuUsage    = cpu_percent(interval=0.1)
    v_core      = cpu_count(logical=True) - cpu_count(logical=False)
    freq_info   = cpu_freq(percpu=False)
    if freq_info is not None:
        frequency = freq_info.current / 1000
    else:
        frequency = '-_-'
    memory      = virtual_memory()
    mem_p       = memory.percent
    swap        = swap_memory()

    bot_stats = f'🤖 <u>𝘽𝙤𝙩 𝙎𝙩𝙖𝙩𝙞𝙨𝙩𝙞𝙘𝙨</u>\n\n'\
                f'<b>┏🖥️ CPU:</b> {cpuUsage}%\n<b>┗[</b>{get_progress_bar_string(cpuUsage)}<b>]</b>\n\n' \
                f'<b>┏💽 RAM:</b> {mem_p}%\n<b>┗[</b>{get_progress_bar_string(mem_p)}<b>]</b>\n\n' \
                f'<b>┏🌀 SWAP:</b> {swap.percent}%\n<b>┗[</b>{get_progress_bar_string(swap.percent)}<b>]</b>\n\n' \
                f'<b>┏📦 DISK:</b> {disk}%\n<b>┗[</b>{get_progress_bar_string(disk)}<b>]</b>\n\n' \
                f'<b>┏⏰ Bot Uptime:</b> <code>{botTime}</code>\n' \
                f'<b>┗🚨 Restarts In:</b> <code>{res_time}</code>\n\n' \
                f'<b>┏📤 Uploaded:</b> <code>{sent}</code>\n' \
                f'<b>┠📥 Downloaded:</b> <code>{recv}</code>\n' \
                f'<b>┗📶 Bandwidth:</b> <code>{tb}</code>\n' \
                f'\n<a href="https://t.me/ACE_ML"><b>♥️ 𝗣𝗼𝘄𝗲𝗿𝗲𝗱 𝗕𝘆 @𝗔𝗖𝗘_𝗠𝗟</b></a>'

    sys_stats = f'🛠 <u>𝙎𝙮𝙨𝙩𝙚𝙢 𝙎𝙩𝙖𝙩𝙞𝙨𝙩𝙞𝙘𝙨</u>\n\n'\
                f'<b>⏰ OS Uptime:</b> <code>{sysTime}</code>\n\n' \
                f'<b>🖥️ CPU:</b> {get_progress_bar_string(cpuUsage)}<code> {cpuUsage}%</code>\n' \
                f'<b>▸ Total Cores:</b> <code>{cpu_count(logical=True)}</code>\n' \
                f'<b>▸ P-Cores:</b> <code>{cpu_count(logical=False)}</code> | ' \
                f'<b>▸ V-Cores:</b> <code>{v_core}</code>\n' \
                f'<b>▸ Frequency:</b> <code>{frequency} GHz</code>\n\n' \
                f'<b>💽 RAM:</b> {get_progress_bar_string(mem_p)}<code> {mem_p}%</code>\n' \
                f'<b>▸ Total:</b> <code>{get_readable_file_size(memory.total)}</code> | ' \
                f'<b>▸ Free:</b> <code>{get_readable_file_size(memory.available)}</code>\n\n' \
                f'<b>🌀 SWAP:</b> {get_progress_bar_string(swap.percent)}<code> {swap.percent}%</code>\n' \
                f'<b>▸ Total</b> <code>{get_readable_file_size(swap.total)}</code> | ' \
                f'<b>▸ Free:</b> <code>{get_readable_file_size(swap.free)}</code>\n\n' \
                f'<b>📦 DISK:</b> {get_progress_bar_string(disk)}<code> {disk}%</code>\n' \
                f'<b>▸ Total:</b> <code>{total}</code> | <b>▸ Free:</b> <code>{free}</code>\n' \
                f'\n<a href="https://t.me/ACE_ML"><b>♥️ 𝗣𝗼𝘄𝗲𝗿𝗲𝗱 𝗕𝘆 @𝗔𝗖𝗘_𝗠𝗟</b></a>'

    buttons.ibutton("🛠️ System",  "show_sys_stats")
    buttons.ibutton("🧑‍💻 Repo", "show_repo_stats")
    buttons.ibutton("❗ Limits", "show_bot_limits")
    buttons.ibutton("❌", "close_signal")
    sbtns = buttons.build_menu(3)
    if not edit_mode:
        await message.reply(bot_stats, reply_markup=sbtns, disable_web_page_preview=True)
    return bot_stats, sys_stats


async def send_bot_stats(_, query):
    buttons = ButtonMaker()
    bot_stats, _ = await stats(_, query.message, edit_mode=True)
    buttons.ibutton("🛠️ System",  "show_sys_stats")
    buttons.ibutton("🧑‍💻 Repo", "show_repo_stats")
    buttons.ibutton("❗ Limits", "show_bot_limits")
    buttons.ibutton("❌",      "close_signal")
    sbtns = buttons.build_menu(3)
    await query.answer()
    await query.message.edit_text(bot_stats, reply_markup=sbtns, disable_web_page_preview=True)


async def send_sys_stats(_, query):
    buttons = ButtonMaker()
    _, sys_stats = await stats(_, query.message, edit_mode=True)
    buttons.ibutton("🤖 Bot",  "show_bot_stats")
    buttons.ibutton("🧑‍💻 Repo", "show_repo_stats")
    buttons.ibutton("❗ Limits", "show_bot_limits")
    buttons.ibutton("❌",      "close_signal")
    sbtns = buttons.build_menu(3)
    await query.answer()
    await query.message.edit_text(sys_stats, reply_markup=sbtns, disable_web_page_preview=True)


async def send_sys_stats(_, query):
    buttons = ButtonMaker()
    _, sys_stats = await stats(_, query.message, edit_mode=True)
    buttons.ibutton("🤖 Bot",  "show_bot_stats")
    buttons.ibutton("🧑‍💻 Repo", "show_repo_stats")
    buttons.ibutton("❗ Limits", "show_bot_limits")
    buttons.ibutton("❌",      "close_signal")
    sbtns = buttons.build_menu(3)
    await query.answer()
    await query.message.edit_text(sys_stats, reply_markup=sbtns, disable_web_page_preview=True)

async def send_repo_stats(_, query):
    buttons = ButtonMaker()
    if await aiopath.exists('.git'):
        last_commit = (await cmd_exec("git log -1 --date=short --pretty=format:'%cr'", True))[0]
        version     = (await cmd_exec("git describe --abbrev=0 --tags", True))[0]
        change_log  = (await cmd_exec("git log -1 --pretty=format:'%s'", True))[0]
    else:
        last_commit = 'No UPSTREAM_REPO'
        version     = 'N/A'
        change_log  = 'N/A'
        
    repo_stats = f'🧑‍💻 <u>𝙍𝙚𝙥𝙤 𝙎𝙩𝙖𝙩𝙞𝙨𝙩𝙞𝙘𝙨</u>\n\n' \
                  f'<b>┏♻️ Updated :</b> <code>{last_commit}</code>\n' \
                  f'<b>┠🆔 Version :</b> <code>{version}</code>\n' \
                  f'<b>┗📝 ChangeLog :</b> <code>{change_log}</code>\n' \
                  f'\n<a href="https://t.me/ACE_ML"><b>♥️ 𝗣𝗼𝘄𝗲𝗿𝗲𝗱 𝗕𝘆 @𝗔𝗖𝗘_𝗠𝗟</b></a>'

    buttons.ibutton("🤖 Bot",  "show_bot_stats")
    buttons.ibutton("🛠️ System",  "show_sys_stats")
    buttons.ibutton("❗ Limits", "show_bot_limits")
    buttons.ibutton("❌", "close_signal")
    sbtns = buttons.build_menu(3)
    await query.answer()
    await query.message.edit_text(repo_stats, reply_markup=sbtns, disable_web_page_preview=True)

async def send_bot_limits(_, query):
    buttons = ButtonMaker()
    TOKEN_TIMEOUT = config_dict['TOKEN_TIMEOUT']
    EXF = 'None' if config_dict['EXTENSION_FILTER']    == '' else config_dict['EXTENSION_FILTER']
    STH = 'None' if config_dict['STORAGE_THRESHOLD']    == '' else config_dict['STORAGE_THRESHOLD']
    TTO = 'Forever' if TOKEN_TIMEOUT  == '' else f'{get_readable_time(int(TOKEN_TIMEOUT))}'
    DIR = 'Unlimited' if config_dict['DIRECT_LIMIT']    == '' else config_dict['DIRECT_LIMIT']
    YTD = 'Unlimited' if config_dict['YTDLP_LIMIT']     == '' else config_dict['YTDLP_LIMIT']
    GDL = 'Unlimited' if config_dict['GDRIVE_LIMIT']    == '' else config_dict['GDRIVE_LIMIT']
    TOR = 'Unlimited' if config_dict['TORRENT_LIMIT']   == '' else config_dict['TORRENT_LIMIT']
    CLL = 'Unlimited' if config_dict['CLONE_LIMIT']     == '' else config_dict['CLONE_LIMIT']
    MGA = 'Unlimited' if config_dict['MEGA_LIMIT']      == '' else config_dict['MEGA_LIMIT']
    TGL = 'Unlimited' if config_dict['LEECH_LIMIT']     == '' else config_dict['LEECH_LIMIT']
    UMT = 'Unlimited' if config_dict['USER_MAX_TASKS']  == '' else config_dict['USER_MAX_TASKS']
    BMT = 'Unlimited' if config_dict['QUEUE_ALL']       == '' else config_dict['QUEUE_ALL']

    bot_limit = f'❗ <u>𝙇𝙞𝙢𝙞𝙩𝙨</u>\n\n' \
                f'<b>┏📂 Leech :</b>  <code>{TGL} GB</code>\n' \
                f'<b>┠🎯 Direct :</b>  <code>{DIR} GB</code>\n' \
                f'<b>┠🧲 Torrent :</b>  <code>{TOR} GB</code>\n' \
                f'<b>┠☁️ GDrive :</b>  <code>{GDL} GB</code>\n' \
                f'<b>┠🎗️ Clone :</b>  <code>{CLL} GB</code>\n' \
                f'<b>┠Ⓜ️ Mega :</b>  <code>{MGA} GB</code>\n' \
                f'<b>┗📺 YT-DLP :</b>  <code>{YTD} GB</code>\n\n' \
                f'<b>┏🗄️ Storage Threshold :</b>  <code>{STH} GB</code>\n' \
                f'<b>┗👾 Blocked Extensions :</b>  <code>{EXF}</code>\n\n' \
                f'<b>┏👤 User Tasks :</b>  <code>{UMT}</code>\n' \
                f'<b>┠🚧 Bot Tasks :</b>  <code>{BMT}</code>\n' \
                f'<b>┗🔑 Token Validity :</b>  <code>{TTO}</code>\n' \
                f'\n<a href="https://t.me/ACE_ML"><b>♥️ 𝗣𝗼𝘄𝗲𝗿𝗲𝗱 𝗕𝘆 @𝗔𝗖𝗘_𝗠𝗟</b></a>'

    buttons.ibutton("🤖 Bot",  "show_bot_stats")
    buttons.ibutton("🛠️ System",  "show_sys_stats")
    buttons.ibutton("🧑‍💻 Repo", "show_repo_stats")
    buttons.ibutton("❌", "close_signal")
    sbtns = buttons.build_menu(3)
    await query.answer()
    await query.message.edit_text(bot_limit, reply_markup=sbtns, disable_web_page_preview=True)


async def send_close_signal(_, query):
    await query.answer()
    try:
        await query.message.reply_to_message.delete()
    except Exception as e:
        LOGGER.error(e)
    await query.message.delete()


bot.add_handler(MessageHandler(mirror_status, filters=command(BotCommands.StatusCommand) & CustomFilters.authorized))
bot.add_handler(MessageHandler(stats,   filters=command(BotCommands.StatsCommand)   & CustomFilters.authorized))
bot.add_handler(CallbackQueryHandler(send_close_signal, filters=regex("^close_signal")))
bot.add_handler(CallbackQueryHandler(send_bot_stats,    filters=regex("^show_bot_stats")))
bot.add_handler(CallbackQueryHandler(send_sys_stats,    filters=regex("^show_sys_stats")))
bot.add_handler(CallbackQueryHandler(send_repo_stats,   filters=regex("^show_repo_stats")))
bot.add_handler(CallbackQueryHandler(send_bot_limits,   filters=regex("^show_bot_limits")))
bot.add_handler(CallbackQueryHandler(status_pages, filters=regex("^status")))
