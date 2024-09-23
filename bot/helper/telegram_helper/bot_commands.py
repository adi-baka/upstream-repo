#!/usr/bin/env python3
from bot import CMD_SUFFIX


class _BotCommands:
    def __init__(self):
        self.StartCommand       = 'start'
        self.MirrorCommand      = [f'mirror{CMD_SUFFIX}',    f'm{CMD_SUFFIX}']
        self.QbMirrorCommand    = [f'qbmirror{CMD_SUFFIX}',  f'qbm{CMD_SUFFIX}', f'qm{CMD_SUFFIX}']
        self.YtdlCommand        = [f'ytdl{CMD_SUFFIX}',      f'yt{CMD_SUFFIX}', f'ym{CMD_SUFFIX}']
        self.LeechCommand       = [f'leech{CMD_SUFFIX}',     f'l{CMD_SUFFIX}']
        self.QbLeechCommand     = [f'qbleech{CMD_SUFFIX}',   f'qbl{CMD_SUFFIX}', f'ql{CMD_SUFFIX}']
        self.YtdlLeechCommand   = [f'ytdlleech{CMD_SUFFIX}', f'ytl{CMD_SUFFIX}', f'yl{CMD_SUFFIX}']
        self.CancelAllCommand   = [f'cancelall{CMD_SUFFIX}', 'cancelallbot']
        self.RestartCommand     = [f'r{CMD_SUFFIX}',   'rall']
        self.StatusCommand      = [f'status{CMD_SUFFIX}',     f's{CMD_SUFFIX}', 'ace']
        self.PingCommand        = [f'ping{CMD_SUFFIX}',      'p', f'p{CMD_SUFFIX}']
        self.StatsCommand       = [f'stats{CMD_SUFFIX}',     'statsall']
        self.CloneCommand       = f'clone{CMD_SUFFIX}'
        self.CountCommand       = f'count{CMD_SUFFIX}'
        self.DeleteCommand      = f'del{CMD_SUFFIX}'
        self.CancelMirror       = f'abort{CMD_SUFFIX}'
        self.ListCommand        = f'list{CMD_SUFFIX}'
        self.SearchCommand      = f'ts{CMD_SUFFIX}'
        self.UsersCommand       = [f'users{CMD_SUFFIX}', 'usersall']
        self.AuthorizeCommand   = [f'authorize{CMD_SUFFIX}', f'auth{CMD_SUFFIX}', 'authall']
        self.UnAuthorizeCommand = [f'unauthorize{CMD_SUFFIX}', f'unauth{CMD_SUFFIX}', 'unauthall']
        self.AddSudoCommand     = f'addsudo{CMD_SUFFIX}'
        self.RmSudoCommand      = f'rmsudo{CMD_SUFFIX}'
        self.HelpCommand        = f'help{CMD_SUFFIX}'
        self.LogCommand         = [f'log{CMD_SUFFIX}', 'logall']
        self.ShellCommand       = [f'shell{CMD_SUFFIX}', 'shellall']
        self.EvalCommand        = [f'eval{CMD_SUFFIX}', 'evalall']
        self.ExecCommand        = [f'exec{CMD_SUFFIX}', 'execall']
        self.ClearLocalsCommand = [f'clearlocals{CMD_SUFFIX}', 'clearlocalsall']
        self.BotSetCommand      = [f'bsetting{CMD_SUFFIX}', f'bs{CMD_SUFFIX}', 'bsall']
        self.UserSetCommand     = [f'usetting{CMD_SUFFIX}', f'us{CMD_SUFFIX}', 'usall']
        self.BtSelectCommand    = f'btsel{CMD_SUFFIX}'
        self.RssCommand         = f'rss{CMD_SUFFIX}'
        self.CategorySelect     = f'catsel{CMD_SUFFIX}'
        self.RmdbCommand        = [f'rmdb{CMD_SUFFIX}', 'rmdball']
        self.RmalltokensCommand = [f'rmtk{CMD_SUFFIX}', 'rmtkall']

BotCommands = _BotCommands()
