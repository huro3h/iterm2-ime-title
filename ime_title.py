#!/usr/bin/env python3
# 現在の入力モード(かな/英字)を、iTerm2 の各セッションのタイトルの先頭に出す。
# プロファイルの General > Title で「入力モード付きタイトル」を選んでおく。
# (API からセッションごとに Title Function を設定すると REQUEST_MALFORMED で拒否されるため、設定画面で選ぶ)
# Scripts/AutoLaunch に置くと iTerm2 の起動時に自動で動く。
import asyncio
import ctypes
import ctypes.util
import os
import time

import iterm2

POLL_SECONDS = 0.03
# Karabiner で⌘の単押しを英数(左)・かな(右)キーにしている場合に、同じ判定で入力ソースの切り替えを待たずに表示を変える。
# その設定がない環境では、⌘を単独で押すたびに表示が一瞬だけ変わってしまうので False にする
COMMAND_TAP_ENABLED = True
COMMAND_TAP_LABELS = {iterm2.Keycode.COMMAND: "A", iterm2.Keycode.RIGHT_COMMAND: "あ"}
COMMAND_TAP_SECONDS = 1.0  # Karabiner の to_if_alone の既定のタイムアウト
# 先に変えた表示を、入力ソースが追いつくまでポーリングで戻さないための猶予
TAP_HOLD_SECONDS = 0.5
TITLE_FUNCTION_ID = "com.huro3h.ime-title"
# タイトルの文字には色を付けられないので、入力モードごとに色付きの絵文字を前に置く
IME_MARKS = {"あ": "⚪", "ア": "⚪", "A": "🔵"}
HOME = os.path.expanduser("~")

carbon = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/Carbon.framework/Carbon")
cf = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreFoundation"))
carbon.TISCopyCurrentKeyboardInputSource.restype = ctypes.c_void_p
carbon.TISGetInputSourceProperty.restype = ctypes.c_void_p
carbon.TISGetInputSourceProperty.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
cf.CFStringGetCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_uint32]
cf.CFRelease.argtypes = [ctypes.c_void_p]
cf.CFRunLoopRunInMode.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_bool]
INPUT_SOURCE_ID = ctypes.c_void_p.in_dll(carbon, "kTISPropertyInputSourceID")
DEFAULT_MODE = ctypes.c_void_p.in_dll(cf, "kCFRunLoopDefaultMode")
UTF8 = 0x08000100


def current_input_source_id():
    # 長く動くプロセスでは、run loop を回さないと切り替えの通知が届かず古い値のままになる
    cf.CFRunLoopRunInMode(DEFAULT_MODE, 0, True)
    src = carbon.TISCopyCurrentKeyboardInputSource()
    buf = ctypes.create_string_buffer(256)
    cf.CFStringGetCString(carbon.TISGetInputSourceProperty(src, INPUT_SOURCE_ID), buf, len(buf), UTF8)
    cf.CFRelease(src)
    return buf.value.decode()


def label_for(source_id):
    if "Katakana" in source_id:
        return "ア"
    if "Japanese" in source_id and "Roman" not in source_id:
        return "あ"
    return "A"


@iterm2.TitleProviderRPC
async def ime_title(
    ime=iterm2.Reference("user.ime?"),
    path=iterm2.Reference("path?"),
):
    # 入力モードのあとに現在のディレクトリを出す。ホーム以下は ~ に縮める
    title = path or ""
    if title == HOME or title.startswith(HOME + "/"):
        title = "~" + title[len(HOME):]
    return f"{IME_MARKS.get(ime, '')}{ime} {title}" if ime else title


async def set_label(session, label):
    await session.async_set_variable("user.ime", label)


def all_sessions(app):
    return [session for window in app.terminal_windows for tab in window.tabs for session in tab.sessions]


async def main(connection):
    app = await iterm2.async_get_app(connection)
    await ime_title.async_register(connection, "入力モード付きタイトル", TITLE_FUNCTION_ID)
    label = label_for(current_input_source_id())
    await asyncio.gather(*(set_label(session, label) for session in all_sessions(app)))

    async def watch_new_sessions():
        async with iterm2.NewSessionMonitor(connection) as monitor:
            while True:
                session = app.get_session_by_id(await monitor.async_get())
                if session:
                    await set_label(session, label)

    shown = label
    hold_until = 0.0

    async def show(new_label):
        nonlocal label, shown
        label = new_label
        if label != shown:
            shown = label
            await asyncio.gather(*(set_label(session, label) for session in all_sessions(app)))

    async def watch_command_taps():
        nonlocal hold_until
        pressed = None  # 単押しの候補になっている⌘のキーコードと、押した時刻
        async with iterm2.KeystrokeMonitor(connection, advanced=True) as monitor:
            while True:
                keystroke = await monitor.async_get()
                if keystroke.action == iterm2.Keystroke.Action.KEY_DOWN:
                    pressed = None
                elif keystroke.action == iterm2.Keystroke.Action.FLAGS_CHANGED:
                    # 英数・かなキーは Keycode に定義がなく例外になるので、keycode は修飾キーの変化のときだけ読む
                    command_down = iterm2.Modifier.COMMAND in keystroke.modifiers
                    if command_down and keystroke.keycode in COMMAND_TAP_LABELS and pressed is None:
                        pressed = (keystroke.keycode, time.monotonic())
                    elif not command_down and pressed:
                        keycode, pressed_at = pressed
                        pressed = None
                        if time.monotonic() - pressed_at < COMMAND_TAP_SECONDS:
                            hold_until = time.monotonic() + TAP_HOLD_SECONDS
                            await show(COMMAND_TAP_LABELS[keycode])
                    else:
                        pressed = None

    asyncio.create_task(watch_new_sessions())
    if COMMAND_TAP_ENABLED:
        asyncio.create_task(watch_command_taps())
    while True:
        polled = label_for(current_input_source_id())
        if polled == shown or time.monotonic() >= hold_until:
            hold_until = 0.0
            await show(polled)
        await asyncio.sleep(POLL_SECONDS)


iterm2.run_forever(main)
