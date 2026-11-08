#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════╗
║  NGRAXX · DIVAN-X-GEN v3.1.0 · STRICT PROXY + TERMUX-SAFE        ║
║  ✅ ZERO direct fallback — proxy is mandatory                     ║
║  ✅ Exit-IP verification (transparent proxy detection)            ║
║  ✅ Workers block until a LIVE proxy is assigned                  ║
║  ✅ Termux/Android FD-safe (poll-based server, capped pools)      ║
║  ✅ Fresh GitHub sources + smart health scoring                   ║
╚══════════════════════════════════════════════════════════════════╝
"""

import sys, os, subprocess, importlib

# ───────────────────────────── BOOTSTRAP ─────────────────────────────

def _bOoTsTrAp_dEpEnDeNcIeS():
    rEqUiReD = [
        ("flask", "flask"), ("requests", "requests"), ("Crypto", "pycryptodome"),
        ("colorama", "colorama"), ("urllib3", "urllib3"), ("psutil", "psutil"),
        ("socks", "PySocks"),
    ]
    mIsSiNg = []
    for iMpOrT_nAmE, pIp_nAmE in rEqUiReD:
        try: importlib.import_module(iMpOrT_nAmE)
        except ImportError: mIsSiNg.append((iMpOrT_nAmE, pIp_nAmE))

    if mIsSiNg:
        print(f"📦 Auto-installing {len(mIsSiNg)} missing dependency(ies)...")
        for iMpOrT_nAmE, pIp_nAmE in mIsSiNg:
            print(f"  → {pIp_nAmE}")
            oK = False
            for cMd in [
                [sys.executable, "-m", "pip", "install", "--no-input", pIp_nAmE],
                [sys.executable, "-m", "pip", "install", "--no-input", "--user", pIp_nAmE],
                [sys.executable, "-m", "pip", "install", "--no-input", "--break-system-packages", pIp_nAmE],
            ]:
                try:
                    r = subprocess.run(cMd, capture_output=True, timeout=600)
                    if r.returncode == 0: oK = True; break
                except Exception: continue
            if not oK:
                if iMpOrT_nAmE == "socks":
                    print(f"  ⚠️ {pIp_nAmE} failed — SOCKS disabled, HTTP will still work")
                    continue
                print(f"  ❌ could not install {pIp_nAmE} — exiting.")
                sys.exit(1)
            print(f"  ✅ {pIp_nAmE} installed")

    try: importlib.import_module("waitress")
    except ImportError:
        for cMd in [
            [sys.executable, "-m", "pip", "install", "--no-input", "waitress"],
            [sys.executable, "-m", "pip", "install", "--no-input", "--break-system-packages", "waitress"],
        ]:
            try:
                r = subprocess.run(cMd, capture_output=True, timeout=300)
                if r.returncode == 0: break
            except Exception: continue

_bOoTsTrAp_dEpEnDeNcIeS()

import re, json, time, base64, string, random, shutil, socket, signal
import hashlib, hmac, codecs, threading, ipaddress
from collections import Counter, deque
from datetime import datetime

import requests, urllib3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from colorama import Fore, Style, init
from flask import Flask, jsonify, request, Response

init(autoreset=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import socks
    _SOCKS_OK = True
except Exception:
    _SOCKS_OK = False

# ───────────────────────────── CONFIG ─────────────────────────────

cOnFiG_cAcHe_FiLe = "live_config_cache.json"
dEfAuLt_GlObAl_sErVeR = "https://loginbp.ppmainecoonghj.com/"
dEfAuLt_ClIeNt_UrL    = "https://clientbp.ppmainecoonghj.com/"
dEfAuLt_ReLeAsE_tAg   = "OB55"
dEfAuLt_ReGiStRaTiOn_vErSiOn = "1.132.11"
fAsT_rEgIsTrAtIoN_vErSiOn    = "2.133.8"

sErVeR_GlObAl = dEfAuLt_GlObAl_sErVeR
cLiEnT_GlObAl = dEfAuLt_ClIeNt_UrL
rElEaSe_TaG   = dEfAuLt_ReLeAsE_tAg
rEgIsTrAtIoN_vErSiOn  = dEfAuLt_ReGiStRaTiOn_vErSiOn
rEgIsTrAtIoN_lAnGuAgE = "en"

ENGINE_CLASSIC = "classic"; ENGINE_FAST = "fast"
PASS_MODE_PATTERN = "pattern"; PASS_MODE_CUSTOM = "custom"
PASS_MODE_FIXED = "fixed"; PASS_MODE_HASH = "hash"

WEB_PORT = int(os.environ.get("PORT", "8000"))
WEB_HOST = os.environ.get("HOST", "0.0.0.0")
SERVE_BACKEND = os.environ.get("SERVE_BACKEND", "waitress").lower()

# ── Termux/Android detection (used throughout the file) ──
_IS_ANDROID = (
    "ANDROID_ROOT" in os.environ or "ANDROID_DATA" in os.environ
    or os.path.exists("/system/build.prop")
    or "termux" in os.environ.get("PREFIX", "").lower()
    or "vmos" in os.environ.get("PREFIX", "").lower()
)

ROTATE_EVERY_N     = int(os.environ.get("ROTATE_EVERY", "5"))
TURBO_ROTATION     = os.environ.get("TURBO", "1") not in ("0", "false", "False")
VERIFY_PROXIES     = os.environ.get("VERIFY_PROXIES", "1") not in ("0", "false", "False")

uSe_tOr_PrOxY         = os.environ.get("USE_TOR", "1") not in ("0", "false", "False")
TOR_SOCKS_PORT        = int(os.environ.get("TOR_SOCKS_PORT", "9050"))
tOr_sOcKs_pRoXy       = f"socks5h://127.0.0.1:{TOR_SOCKS_PORT}"
TOR_SETUP_TIMEOUT     = float(os.environ.get("TOR_SETUP_TIMEOUT", "180"))
TOR_AUTO_INSTALL      = os.environ.get("TOR_AUTO_INSTALL", "1") not in ("0", "false")
AUTO_DEGRADE          = os.environ.get("AUTO_DEGRADE", "1") not in ("0", "false")
rOtAtIoN_tHrEsHoLd    = int(os.environ.get("ROTATE_THRESHOLD", "3"))
tOr_rOtAtIoN_cOoLdOwN = float(os.environ.get("ROTATE_COOLDOWN", "15"))
SKIP_CONFIG_SYNC      = os.environ.get("SKIP_CONFIG_SYNC", "0") not in ("0", "false")

REPEAT_RARE_THRESHOLD = int(os.environ.get("RARE_THRESHOLD", "4"))
MAX_COUPLE_CANDIDATES = int(os.environ.get("MAX_COUPLE_CANDIDATES", "5000"))
DEFAULT_MAX_TRIES     = int(os.environ.get("MAX_TRIES_PER_ACCOUNT", "4"))
HTTP_TIMEOUT          = float(os.environ.get("HTTP_TIMEOUT", "15"))

HEAVY_MODE        = os.environ.get("HEAVY", "1") not in ("0", "false", "False")
MAX_THREADS_HARD  = int(os.environ.get("MAX_THREADS", "100"))
WORKER_STAGGER    = float(os.environ.get("WORKER_STAGGER", "0.05"))
RPS_LIMIT         = float(os.environ.get("RPS_LIMIT", "0"))
POOL_MAXSIZE      = int(os.environ.get("POOL_MAXSIZE", "256"))
FAIL_BACKOFF_MAX  = float(os.environ.get("FAIL_BACKOFF_MAX", "6.0"))
PROXY_WAIT_MAX    = float(os.environ.get("PROXY_WAIT_MAX", "120"))
MIN_LIVE_PROXIES  = int(os.environ.get("MIN_LIVE_PROXIES", "10"))

# ── Termux/Android has a ~1024 FD limit — shrink pools so we don't exhaust it ──
if _IS_ANDROID:
    POOL_MAXSIZE      = int(os.environ.get("POOL_MAXSIZE", "16"))
    MAX_THREADS_HARD  = int(os.environ.get("MAX_THREADS", "32"))
    WORKER_STAGGER    = max(WORKER_STAGGER, 0.15)
    MIN_LIVE_PROXIES  = int(os.environ.get("MIN_LIVE_PROXIES", "5"))

_gate_lock = threading.Lock(); _gate_next = 0.0

def _rAtE_gAtE():
    global _gate_next
    if RPS_LIMIT <= 0: return
    with _gate_lock:
        nOw = time.time(); wAiT = max(0.0, _gate_next - nOw)
        _gate_next = max(nOw, _gate_next) + (1.0 / RPS_LIMIT)
    if wAiT: time.sleep(wAiT)

def _gAp():
    if HEAVY_MODE: return
    time.sleep(random.uniform(0.4, 1.2))

def _jItTeR():
    if HEAVY_MODE: return
    time.sleep(random.uniform(0.0, 0.1))

# ───────────────────────────── STORAGE ─────────────────────────────

rOoT_dIr    = os.path.dirname(os.path.abspath(__file__))
bAsE_dIr    = os.path.join(rOoT_dIr, "DIVAN-ERA")
tOkEn_DiR   = os.path.join(bAsE_dIr, "TOKENS-JWT")
aCcOuNt_DiR = os.path.join(bAsE_dIr, "ACCOUNTS")
rArE_DiR    = os.path.join(bAsE_dIr, "RARE ACCOUNTS")
cOuPlE_DiR  = os.path.join(bAsE_dIr, "COUPLES ACCOUNTS")

for _p in (bAsE_dIr, tOkEn_DiR, aCcOuNt_DiR, rArE_DiR, cOuPlE_DiR):
    os.makedirs(_p, exist_ok=True)

_lOcK_rEgIsTrY = {}; _lOcK_gUaRd = threading.Lock()

def lOcK_fOr(fn):
    with _lOcK_gUaRd:
        if fn not in _lOcK_rEgIsTrY: _lOcK_rEgIsTrY[fn] = threading.Lock()
        return _lOcK_rEgIsTrY[fn]

def _aToMiC_wRiTe(t, r):
    tmp = t + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(r, f, indent=2, ensure_ascii=False)
    os.replace(tmp, t)

def _rEaD_rEcOrDs(t):
    if not os.path.exists(t): return []
    try:
        with open(t, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return []

def sAvE_aCcOuNt(a):
    try:
        rEg = a.get("region", "UNKNOWN")
        tArGeT = os.path.join(aCcOuNt_DiR, f"accounts-{rEg}.json")
        rEcOrD = {"uid": a["uid"], "password": a["password"], "name": a["name"],
            "account_id": a.get("account_id", "N/A"), "region": rEg,
            "engine": a.get("engine", "classic"), "access_token": a.get("access_token", ""),
            "thread_id": a.get("thread_id", "N/A"),
            "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        with lOcK_fOr(tArGeT):
            r = _rEaD_rEcOrDs(tArGeT); r.append(rEcOrD); _aToMiC_wRiTe(tArGeT, r)
        jWt = os.path.join(tOkEn_DiR, f"jwt-{rEg}.txt")
        with lOcK_fOr(jWt):
            with open(jWt, "a", encoding="utf-8") as f:
                f.write(f"{rEcOrD['uid']}:{rEcOrD['password']}:{rEcOrD['access_token']}:{rEcOrD['account_id']}\n")
        return True
    except Exception as e:
        eMiT_eRrOr(f"save_account error: {e}"); return False

def sAvE_rArE(a, t, rEaSoN, sCoRe):
    try:
        tArGeT = os.path.join(rArE_DiR, f"rare-{a.get('region', 'UNKNOWN')}.json")
        rEcOrD = {"uid": a["uid"], "password": a["password"],
            "account_id": a.get("account_id", "N/A"), "name": a["name"],
            "region": a.get("region", "UNKNOWN"), "rarity_type": t,
            "rarity_score": sCoRe, "reason": rEaSoN, "engine": a.get("engine", "classic"),
            "date_identified": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "access_token": a.get("access_token", ""), "thread_id": a.get("thread_id", "N/A")}
        with lOcK_fOr(tArGeT):
            r = _rEaD_rEcOrDs(tArGeT)
            if rEcOrD["account_id"] not in [e.get("account_id") for e in r]:
                r.append(rEcOrD); _aToMiC_wRiTe(tArGeT, r); return True
            return False
    except Exception as e:
        eMiT_eRrOr(f"save_rare error: {e}"); return False

def sAvE_cOuPlE(p, q, rEaSoN):
    try:
        tArGeT = os.path.join(cOuPlE_DiR, f"couples-{p.get('region','UNKNOWN')}.json")
        rEcOrD = {"couple_id": f"{p.get('account_id','N/A')}_{q.get('account_id','N/A')}",
            "account1": {"uid": p["uid"], "password": p["password"],
                "account_id": p.get("account_id","N/A"), "name": p["name"], "thread_id": p.get("thread_id","N/A")},
            "account2": {"uid": q["uid"], "password": q["password"],
                "account_id": q.get("account_id","N/A"), "name": q["name"], "thread_id": q.get("thread_id","N/A")},
            "reason": rEaSoN, "region": p.get("region", "UNKNOWN"),
            "date_matched": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        with lOcK_fOr(tArGeT):
            r = _rEaD_rEcOrDs(tArGeT)
            if rEcOrD["couple_id"] not in [e.get("couple_id") for e in r]:
                r.append(rEcOrD); _aToMiC_wRiTe(tArGeT, r); return True
            return False
    except Exception as e:
        eMiT_eRrOr(f"save_couple error: {e}"); return False

# ───────────────────────────── RARITY ─────────────────────────────

cOuPlE_cAnDiDaTeS = {}; cOuPlE_lOcK = threading.Lock()

def aSsEsS_rArItY(a, thr=None):
    thr = int(thr or REPEAT_RARE_THRESHOLD)
    raw = a.get("account_id")
    if raw is None: return False, None, None, 0
    aid = str(raw).strip()
    if not aid.isdigit(): return False, None, None, 0
    cnt = Counter(aid); d, t = cnt.most_common(1)[0]
    best, run = 1, 1
    for i in range(1, len(aid)):
        if aid[i] == aid[i-1]: run += 1; best = max(best, run)
        else: run = 1
    score = 0; reasons = []
    if t >= thr: score += t*2; reasons.append(f"digit '{d}' repeats {t}x")
    if best >= thr: score += best*2; reasons.append(f"{best} identical digits")
    pairs = re.findall(r"(\d)\1", aid)
    if len(pairs) >= 3: score += len(pairs); reasons.append(f"{len(pairs)} repeated pairs")
    if len(aid) >= 4 and aid == aid[::-1]: score += 4; reasons.append("palindrome")
    if (t >= thr) or (best >= thr):
        return True, "RARE_ACCOUNT", f"ID {aid} :: " + " | ".join(reasons), score
    return False, None, None, score

def mAtCh_cOuPlE(a, b):
    a = str(a) if a is not None else ""; b = str(b) if b is not None else ""
    if not a or not b or not (a.isdigit() and b.isdigit()): return False, None
    if len(a) != len(b) or len(a) < 3: return False, None
    if abs(int(a) - int(b)) == 1: return True, f"Consecutive: {a} & {b}"
    if a[:-2] == b[:-2] and abs(int(a[-2:]) - int(b[-2:])) == 1:
        return True, f"Seq suffix: ...{a[-2:]} & ...{b[-2:]}"
    if a[:-3] == b[:-3] and abs(int(a[-3:]) - int(b[-3:])) == 1:
        return True, f"Seq last-3: ...{a[-3:]} & ...{b[-3:]}"
    return False, None

def aSsEsS_cOuPlE(a, tid):
    ident = str(a.get("account_id", ""))
    if ident in ("", "N/A", "None"): return False, None, None
    with cOuPlE_lOcK:
        for k, rec in list(cOuPlE_cAnDiDaTeS.items()):
            matched, expl = mAtCh_cOuPlE(ident, str(rec.get("account_id", "")))
            if matched:
                partner = rec; del cOuPlE_cAnDiDaTeS[k]
                return True, expl, partner
        cOuPlE_cAnDiDaTeS[ident] = {"uid": a.get("uid", ""), "account_id": ident,
            "name": a.get("name", ""), "password": a.get("password", ""),
            "region": a.get("region", ""), "thread_id": tid,
            "timestamp": datetime.now().isoformat()}
        if len(cOuPlE_cAnDiDaTeS) > MAX_COUPLE_CANDIDATES:
            oldest = sorted(cOuPlE_cAnDiDaTeS.items(), key=lambda kv: kv[1].get("timestamp", ""))
            for k, _ in oldest[:len(cOuPlE_cAnDiDaTeS) - MAX_COUPLE_CANDIDATES]:
                cOuPlE_cAnDiDaTeS.pop(k, None)
    return False, None, None

# ───────────────────────────── LOGGING ─────────────────────────────

def aCcEnT():
    return random.choice([Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX, Fore.LIGHTWHITE_EX, Fore.LIGHTBLUE_EX])

class sTyLe: bRiGhT = Style.BRIGHT; rEsEt = Style.RESET_ALL
def eMiT_sUcCeSs(m): print(f"{aCcEnT()}{sTyLe.bRiGhT}✅ {m}{sTyLe.rEsEt}")
def eMiT_eRrOr(m):   print(f"{Fore.RED}{sTyLe.bRiGhT}❌ {m}{sTyLe.rEsEt}")
def eMiT_wArNiNg(m): print(f"{Fore.YELLOW}{sTyLe.bRiGhT}⚠️ {m}{sTyLe.rEsEt}")

# ───────────────────────────── TOR MANAGER ─────────────────────────────

class TorManager:
    def __init__(self):
        self.proc = None; self.exit_ip = None; self.state = "off"
        self.logs = deque(maxlen=250); self.lock = threading.Lock()
    def _log(self, m):
        with self.lock: self.logs.append(f"{datetime.now().strftime('%H:%M:%S')} {m}")
    def available(self): return bool(shutil.which("tor"))
    def _port_open(self):
        try:
            with socket.create_connection(("127.0.0.1", TOR_SOCKS_PORT), timeout=1): return True
        except Exception: return False
    def _verify(self):
        px = {"http": tOr_sOcKs_pRoXy, "https": tOr_sOcKs_pRoXy}
        try:
            r = requests.get("https://check.torproject.org/api/ip", proxies=px, timeout=20, verify=False)
            if r.status_code == 200 and r.json().get("IsTor"):
                return True, r.json().get("IP", "?")
        except Exception: pass
        return False, None
    def _launch(self):
        data = "/tmp/tor-data"
        try: os.makedirs(data, exist_ok=True)
        except Exception: pass
        args = ["tor", "--SocksPort", str(TOR_SOCKS_PORT), "--DataDirectory", data]
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return self.proc
    def start(self, deadline=None):
        global uSe_tOr_PrOxY
        if not self.available() or not _SOCKS_OK:
            uSe_tOr_PrOxY = False; self.state = "unavailable"; return False
        try: subprocess.run(["pkill", "-9", "tor"], capture_output=True, timeout=8)
        except Exception: pass
        time.sleep(1); self.state = "starting"
        try: self._launch()
        except Exception: uSe_tOr_PrOxY = False; self.state = "error"; return False
        dl = deadline or (time.time() + TOR_SETUP_TIMEOUT)
        while time.time() < dl:
            if self._port_open(): break
            if self.proc and self.proc.poll() is not None: break
            time.sleep(1)
        if not self._port_open(): uSe_tOr_PrOxY = False; self.state = "port-timeout"; return False
        while time.time() < dl:
            oK, ip = self._verify()
            if oK:
                self.exit_ip = ip; self.state = f"ready ({ip})"; return True
            time.sleep(2)
        uSe_tOr_PrOxY = False; self.state = "circuit-timeout"; return False
    def rotate(self):
        if not self.proc or self.proc.poll() is not None: self.start(); return
        try:
            if shutil.which("pkill"): subprocess.run(["pkill", "-HUP", "tor"], capture_output=True, timeout=10)
            else: self.proc.send_signal(signal.SIGHUP)
        except Exception: pass

tOr_MgR = TorManager()
pRoXy_MoDe = "free"

# ───────────────────────────── FRESH VERIFIED PROXY SOURCES ─────────────────────────────

fReE_pRoXy_SoUrCes = [
    # ── proxmint (re-tested every 30 min via real HTTP request) ──
    ("socks5", "https://raw.githubusercontent.com/proxmint/free-proxy-list/main/proxies/socks5.txt"),
    ("http",   "https://raw.githubusercontent.com/proxmint/free-proxy-list/main/proxies/http.txt"),
    ("https",  "https://raw.githubusercontent.com/proxmint/free-proxy-list/main/proxies/https.txt"),
    ("socks4", "https://raw.githubusercontent.com/proxmint/free-proxy-list/main/proxies/socks4.txt"),
    ("elite",  "https://raw.githubusercontent.com/proxmint/free-proxy-list/main/proxies/elite.txt"),
    ("all",    "https://raw.githubusercontent.com/proxmint/free-proxy-list/main/proxies/all.txt"),

    # ── databay-labs (every 5 min, strict SSL, zero MITM) ──
    ("http",   "https://raw.githubusercontent.com/databay-labs/free-proxy-list/master/http.txt"),
    ("https",  "https://raw.githubusercontent.com/databay-labs/free-proxy-list/master/https.txt"),
    ("socks4", "https://raw.githubusercontent.com/databay-labs/free-proxy-list/master/socks4.txt"),
    ("socks5", "https://raw.githubusercontent.com/databay-labs/free-proxy-list/master/socks5.txt"),

    # ── proxygenerator1 (deeply verified, strictest tier first) ──
    ("socks5", "https://raw.githubusercontent.com/proxygenerator1/ProxyGenerator/main/MostStable/socks5.txt"),
    ("http",   "https://raw.githubusercontent.com/proxygenerator1/ProxyGenerator/main/MostStable/http.txt"),
    ("https",  "https://raw.githubusercontent.com/proxygenerator1/ProxyGenerator/main/MostStable/https.txt"),
    ("socks4", "https://raw.githubusercontent.com/proxygenerator1/ProxyGenerator/main/MostStable/socks4.txt"),
    ("all",    "https://raw.githubusercontent.com/proxygenerator1/ProxyGenerator/main/MostStable/ALL.txt"),

    # ── proxifly (updated every 5 min) ──
    ("socks5", "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/socks5/data.txt"),
    ("http",   "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.txt"),
    ("https",  "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/https/data.txt"),
    ("socks4", "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/socks4/data.txt"),
    ("all",    "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.txt"),

    # ── vakhov (fresh, multiple formats) ──
    ("socks5", "https://vakhov.github.io/fresh-proxy-list/socks5.txt"),
    ("http",   "https://vakhov.github.io/fresh-proxy-list/http.txt"),
    ("https",  "https://vakhov.github.io/fresh-proxy-list/https.txt"),
    ("socks4", "https://vakhov.github.io/fresh-proxy-list/socks4.txt"),
    ("all",    "https://vakhov.github.io/fresh-proxy-list/proxylist.txt"),
]

# ───────────────────────────── STRICT LIVE PROXY POOL ─────────────────────────────

class ProxyPool:
    """
    A proxy pool that NEVER returns None or allows a direct connection.
    Every proxy must pass:
      1. TCP connect
      2. HTTP request through the proxy to httpbin.org/ip
      3. Exit IP must differ from the machine's real public IP
         (kills transparent / dead / spoofed proxies)
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._pool = []
        self._cursor = 0
        self._last_fetch = 0.0
        self._fetching = False
        self._real_ip = None
        self._real_ip_lock = threading.Lock()

    def __len__(self):
        with self._lock: return len(self._pool)

    def _get_real_ip(self):
        with self._real_ip_lock:
            if self._real_ip:
                return self._real_ip
            for url in ("https://api.ipify.org?format=json",
                        "https://httpbin.org/ip",
                        "https://api.my-ip.io/ip.json"):
                try:
                    r = requests.get(url, timeout=8, verify=False,
                                     headers={"User-Agent": "Mozilla/5.0"})
                    if r.status_code == 200:
                        data = r.json()
                        ip = data.get("ip") or data.get("origin", "").split(",")[0].strip()
                        if ip:
                            self._real_ip = ip
                            return ip
                except Exception:
                    continue
            self._real_ip = "UNKNOWN"
            return self._real_ip

    def _verify_live(self, proxy_url, timeout=5):
        t0 = time.time()
        try:
            from urllib.parse import urlparse
            parsed = urlparse(proxy_url)
            host, port = parsed.hostname, parsed.port
            if not host or not port:
                return False, None, 0
            with socket.create_connection((host, int(port)), timeout=timeout):
                pass
        except Exception:
            return False, None, 0

        real = self._get_real_ip()
        proxies = {"http": proxy_url, "https": proxy_url}
        for test_url in ("http://httpbin.org/ip", "https://api.ipify.org?format=json"):
            try:
                r = requests.get(test_url, proxies=proxies, timeout=timeout,
                                 verify=False, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code != 200:
                    continue
                data = r.json()
                origin = data.get("origin", "")
                exit_ip = (data.get("ip") or origin.split(",")[0].strip()) if origin else data.get("ip")
                if not exit_ip:
                    continue
                if real != "UNKNOWN" and exit_ip == real:
                    return False, None, 0
                latency = int((time.time() - t0) * 1000)
                return True, exit_ip, latency
            except Exception:
                continue
        return False, None, 0

    def fetch(self, force=False):
        with self._lock:
            if self._fetching: return len(self._pool)
            if not force and self._pool and (time.time() - self._last_fetch) < 300:
                return len(self._pool)
            self._fetching = True
        try:
            raw = _parallel_fetch_sources()
            seen = set(); unique = []
            for p in raw:
                if p not in seen:
                    seen.add(p); unique.append(p)

            if VERIFY_PROXIES and unique:
                verified = []
                vlock = threading.Lock()
                def _check(purl):
                    ok, exit_ip, latency = self._verify_live(purl)
                    if ok:
                        with vlock:
                            verified.append({"url": purl, "exit_ip": exit_ip,
                                             "latency": latency})
                # cap the number of concurrent verification threads on Android
                max_verify = 200 if _IS_ANDROID else 800
                threads = []
                for purl in unique[:max_verify]:
                    t = threading.Thread(target=_check, args=(purl,), daemon=True)
                    t.start(); threads.append(t)
                for t in threads: t.join(timeout=12)
                verified.sort(key=lambda x: x["latency"])
                verified = verified[:max(100, len(verified) // 2)]
            else:
                verified = [{"url": p, "exit_ip": None, "latency": 0} for p in unique[:300]]

            with self._lock:
                existing = {p["url"] for p in self._pool if p.get("alive")}
                for item in verified:
                    if item["url"] not in existing:
                        self._pool.append({"url": item["url"], "ok": 0, "fail": 0,
                                           "alive": True, "latency": item["latency"],
                                           "exit_ip": item["exit_ip"]})
                self._last_fetch = time.time()
                return len([p for p in self._pool if p.get("alive")])
        finally:
            with self._lock: self._fetching = False

    def pick(self, seed=0):
        deadline = time.time() + PROXY_WAIT_MAX
        while time.time() < deadline:
            with self._lock:
                alive = [p for p in self._pool if p.get("alive", True)]
                if alive:
                    alive.sort(key=lambda p: (
                        -(p["ok"] + 1) / (p["ok"] + p["fail"] + 2),
                        p.get("latency", 9999),
                        p["fail"],
                    ))
                    top = alive[:min(8, len(alive))]
                    return random.choice(top)["url"]
            self.fetch(force=True)
            if not any(p.get("alive") for p in self._pool):
                time.sleep(2)
        raise RuntimeError("No live proxy available after waiting — refusing to go direct")

    def report(self, url, ok):
        with self._lock:
            for p in self._pool:
                if p["url"] == url:
                    if ok: p["ok"] += 1
                    else:
                        p["fail"] += 1
                        if p["fail"] >= 2 and p["fail"] > p["ok"]:
                            p["alive"] = False
                    return

    def sample(self, n=10):
        with self._lock:
            alive = [p["url"] for p in self._pool if p.get("alive", True)]
            return alive[:n]

    def alive_count(self):
        with self._lock:
            return len([p for p in self._pool if p.get("alive", True)])

    def ensure_live(self, min_count=MIN_LIVE_PROXIES):
        deadline = time.time() + PROXY_WAIT_MAX
        while time.time() < deadline:
            if self.alive_count() >= min_count:
                return True
            self.fetch(force=True)
            time.sleep(1)
        return self.alive_count() > 0

_pRoXyPoOl = ProxyPool()

def _parallel_fetch_sources():
    results = []; lock = threading.Lock()

    def _fetch_one(scheme, url):
        if scheme.startswith("socks") and not _SOCKS_OK: return
        try:
            r = requests.get(url, timeout=15, verify=False,
                             headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200: return
            prefix = {"socks5": "socks5h", "socks4": "socks4",
                      "http": "http", "https": "http",
                      "all": "http", "elite": "http"}.get(scheme, "http")
            local = []
            for line in r.text.splitlines():
                line = line.strip()
                if not line or ":" not in line: continue
                if "://" in line:
                    if line.startswith(("http://", "https://", "socks4://", "socks5://")):
                        local.append(line)
                    continue
                host, _, port = line.partition(":")
                port = port.split()[0].strip()
                if not port.isdigit(): continue
                local.append(f"{prefix}://{host}:{port}")
            with lock: results.extend(local)
        except Exception:
            pass

    threads = []
    for scheme, url in fReE_pRoXy_SoUrCes:
        t = threading.Thread(target=_fetch_one, args=(scheme, url), daemon=True)
        t.start(); threads.append(t)
    for t in threads: t.join(timeout=20)
    return results


def _bUiLd_sEsSiOn():
    """FD-safe session — caps per-worker sockets so Termux doesn't crash."""
    s = requests.Session(); s.verify = False; s.trust_env = False
    a = requests.adapters.HTTPAdapter(
        pool_connections=8,
        pool_maxsize=min(POOL_MAXSIZE, 32),
        max_retries=0,
        pool_block=False,
    )
    s.mount("http://", a); s.mount("https://", a)
    return s


def wOrKeR_pRoXy(idx, rnd):
    """STRICT: always returns a proxy URL or blocks until one is available."""
    if pRoXy_MoDe == "tor" and uSe_tOr_PrOxY:
        return tOr_sOcKs_pRoXy
    if IPRotator.PROXIES:
        return IPRotator.PROXIES[(idx * 31 + rnd * 7) % len(IPRotator.PROXIES)]
    return _pRoXyPoOl.pick(seed=idx * 31 + rnd)


# ───────────────────────────── 100 DEVICES ─────────────────────────────

_RgN_cC = {"IND": "IN", "ID": "ID", "ME": "AE", "VN": "VN", "TH": "TH", "BD": "BD",
           "PK": "PK", "TW": "TW", "CIS": "RU", "SAC": "AR", "BR": "BR", "EU": "DE", "NA": "US"}

_dEvIcE_mOdElS = [
    ("SM-G998B", "samsung", 1440, 3088, 560), ("SM-A546E", "samsung", 1080, 2340, 420),
    ("SM-M325FV", "samsung", 1080, 2400, 405), ("SM-A135F", "samsung", 720, 1600, 280),
    ("SM-S918B", "samsung", 1440, 3088, 500), ("SM-A236B", "samsung", 720, 1600, 270),
    ("SM-A145F", "samsung", 1080, 2340, 400), ("SM-G991B", "samsung", 1080, 2400, 421),
    ("SM-G996B", "samsung", 1080, 2400, 394), ("SM-A536B", "samsung", 1080, 2340, 405),
    ("SM-A346B", "samsung", 1080, 2340, 390), ("SM-M336B", "samsung", 1080, 2400, 405),
    ("SM-A047F", "samsung", 720, 1600, 269), ("SM-A226B", "samsung", 1080, 2408, 400),
    ("SM-M135F", "samsung", 1080, 2400, 405),
    ("Pixel 4a", "google", 1080, 2340, 443), ("Pixel 5", "google", 1080, 2340, 432),
    ("Pixel 6", "google", 1080, 2400, 411), ("Pixel 6a", "google", 1080, 2400, 420),
    ("Pixel 7", "google", 1080, 2400, 420), ("Pixel 7a", "google", 1080, 2400, 429),
    ("Pixel 8", "google", 1080, 2400, 428), ("Pixel 8 Pro", "google", 1344, 2992, 489),
    ("M2101K7AG", "xiaomi", 1080, 2400, 440), ("2201117TG", "xiaomi", 1080, 2400, 440),
    ("Redmi 10C", "xiaomi", 720, 1650, 268), ("2201123G", "xiaomi", 1080, 2400, 440),
    ("22111317I", "xiaomi", 1080, 2400, 440), ("Redmi Note 12", "xiaomi", 1080, 2400, 395),
    ("POCO X5", "xiaomi", 1080, 2400, 395), ("220333QNY", "xiaomi", 1080, 2400, 440),
    ("Redmi Note 11", "xiaomi", 1080, 2400, 411), ("21061119AG", "xiaomi", 720, 1600, 270),
    ("Redmi 9A", "xiaomi", 720, 1600, 269), ("Redmi 9C", "xiaomi", 720, 1600, 269),
    ("Redmi Note 10", "xiaomi", 1080, 2400, 409), ("POCO M4", "xiaomi", 1080, 2400, 409),
    ("22081212UG", "xiaomi", 1220, 2712, 446), ("Redmi K50i", "xiaomi", 1080, 2460, 407),
    ("RMX3630", "realme", 1080, 2400, 411), ("RMX2189", "realme", 720, 1600, 270),
    ("RMX3780", "realme", 720, 1612, 269), ("RMX3363", "realme", 1080, 2400, 409),
    ("RMX3085", "realme", 1080, 2400, 411), ("RMX3263", "realme", 720, 1600, 269),
    ("RMX3392", "realme", 1080, 2400, 409), ("RMX3501", "realme", 1080, 2400, 405),
    ("RMX1931", "realme", 1080, 2400, 402), ("RMX2001", "realme", 1080, 2340, 402),
    ("CPH2451", "oppo", 1080, 2412, 400), ("CPH2387", "oppo", 720, 1612, 269),
    ("CPH2477", "oppo", 720, 1612, 269), ("CPH2487", "oppo", 1080, 2412, 409),
    ("CPH2127", "oppo", 720, 1600, 269), ("CPH2185", "oppo", 720, 1600, 269),
    ("CPH2207", "oppo", 1080, 2400, 409), ("CPH2219", "oppo", 1080, 2400, 409),
    ("CPH2309", "oppo", 1080, 2412, 402), ("CPH2269", "oppo", 720, 1600, 269),
    ("V2204", "vivo", 1080, 2400, 409), ("V2244", "vivo", 1080, 2400, 405),
    ("V2109", "vivo", 720, 1600, 269), ("V2027", "vivo", 1080, 2400, 400),
    ("V2055", "vivo", 1080, 2400, 398), ("V2148", "vivo", 1080, 2400, 405),
    ("V2199", "vivo", 1080, 2400, 409), ("V2104", "vivo", 720, 1600, 269),
    ("V2069", "vivo", 1080, 2400, 405), ("V2023", "vivo", 1080, 2340, 398),
    ("KB2003", "oneplus", 1080, 2400, 420), ("LE2120", "oneplus", 1440, 3216, 525),
    ("LE2115", "oneplus", 1080, 2400, 409), ("IN2023", "oneplus", 1440, 3168, 516),
    ("LE2101", "oneplus", 1080, 2400, 402), ("KB2001", "oneplus", 1080, 2400, 402),
    ("NE2211", "oneplus", 1080, 2412, 394), ("CPH2447", "oneplus", 1240, 2772, 450),
    ("DN2103", "oneplus", 1080, 2400, 409), ("IN2015", "oneplus", 1080, 2400, 402),
    ("moto g84 5G", "motorola", 1080, 2400, 402), ("moto e40", "motorola", 720, 1600, 270),
    ("moto g power 5G", "motorola", 1080, 2400, 400), ("moto g82", "motorola", 1080, 2400, 402),
    ("moto g52", "motorola", 1080, 2400, 402), ("moto edge 30", "motorola", 1080, 2400, 402),
    ("moto g31", "motorola", 1080, 2400, 409), ("moto e32", "motorola", 720, 1600, 270),
    ("moto g60", "motorola", 1080, 2460, 395), ("moto g42", "motorola", 1080, 2400, 411),
    ("INFINIX X6819", "infinix", 1080, 2400, 395), ("INFINIX X6825", "infinix", 1080, 2400, 395),
    ("INFINIX X6817", "infinix", 720, 1612, 269), ("INFINIX X6882", "infinix", 720, 1640, 320),
    ("INFINIX X6812", "infinix", 1080, 2400, 395),
    ("TECNO CH7n", "tecno", 720, 1640, 320), ("TECNO KI5q", "tecno", 720, 1612, 269),
    ("TECNO CK6n", "tecno", 1080, 2460, 395),
    ("Nokia G21", "nokia", 720, 1600, 320), ("Nokia G11", "nokia", 720, 1600, 269),
    ("I2012", "iqoo", 1080, 2400, 398),
]

_dRoId_vErS = [("11", 30), ("12", 31), ("13", 33), ("14", 34)]
_lOcAlEs = ["en", "in", "id", "vi", "th", "en", "en"]

uNiTy_AgEnTs = [
    "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
    "UnityPlayer/2021.3.27f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
    "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
    "UnityPlayer/2020.3.45f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
]

def _mK_dEvIcE(iDx, rEgIoN, sAlT):
    mOdEl, bRaNd, w, h, dPi = _dEvIcE_mOdElS[(iDx - 1) % len(_dEvIcE_mOdElS)]
    r = random.Random(iDx * 104729 + sAlT * 7919)
    aNdRoId, sDk = r.choice(_dRoId_vErS)
    lOc = r.choice(_lOcAlEs)
    cC = _RgN_cC.get((rEgIoN or "").upper(), "IN")
    aPp = f"2.13{r.randint(0,2)}.{r.randint(0,3)}"
    bld = str(2019118000 + r.randint(0, 999))
    return {
        "model": mOdEl, "brand": bRaNd, "android": aNdRoId, "sdk": sDk,
        "res": f"{w}x{h}", "dpi": dPi, "locale": lOc, "cc": cC,
        "msdk": f"GarenaMSDK/4.0.42({mOdEl} ;Android {aNdRoId};{lOc};{cC};app {aPp} {bld};)",
        "unity": random.Random(iDx * 31337 + sAlT).choice(uNiTy_AgEnTs),
        "adid": "%032x" % r.getrandbits(128),
        "mac": ":".join("%02X" % r.randint(0, 255) for _ in range(6)),
        "serial": "%012X" % r.getrandbits(48),
    }

class WorkerCtx:
    __slots__ = ("idx", "region", "cfg", "device", "session",
                 "proxy", "proxy_round", "fail_streak", "ok", "fail",
                 "req_count", "rotations", "next_rotate")
    def __init__(self, iDx, rEgIoN, cFg, sAlT):
        self.idx = iDx; self.region = rEgIoN; self.cfg = cFg
        self.device = _mK_dEvIcE(iDx, rEgIoN, sAlT)
        self.session = _bUiLd_sEsSiOn()
        self.proxy_round = 0; self.fail_streak = 0; self.ok = 0; self.fail = 0
        self.req_count = 0; self.rotations = 0; self.next_rotate = self._next_target()
        self.proxy = None
        self._aTtAcH()

    def _next_target(self):
        if TURBO_ROTATION: return random.randint(1, 3)
        return max(1, ROTATE_EVERY_N)

    def _aTtAcH(self):
        while True:
            proxy = wOrKeR_pRoXy(self.idx, self.proxy_round)
            if proxy:
                self.proxy = proxy
                break
            time.sleep(2)
        if self.proxy.startswith("socks") and not _SOCKS_OK:
            self.proxy = _pRoXyPoOl.pick(seed=self.idx)
        self.session.proxies = {"http": self.proxy, "https": self.proxy}

    def rotate(self):
        self.proxy_round += 1; self.rotations += 1; self._aTtAcH()
        if pRoXy_MoDe == "tor" and uSe_tOr_PrOxY:
            threading.Thread(target=tOr_MgR.rotate, daemon=True).start()
        return self.proxy

    def tick(self):
        self.req_count += 1
        if self.req_count >= self.next_rotate:
            self.req_count = 0; self.next_rotate = self._next_target(); self.rotate()

    def close(self):
        try: self.session.close()
        except Exception: pass

# ───────────────────────────── IP ROTATOR ─────────────────────────────

class IPRotator:
    REGION_IP_CIDRS = {
        "BD":  ["27.147.128.0/17", "37.111.192.0/19", "49.0.32.0/20", "59.152.96.0/20"],
        "IND": ["1.6.0.0/15", "1.38.0.0/15", "14.96.0.0/15", "27.4.0.0/14"],
        "ID":  ["36.64.0.0/11", "101.255.0.0/16", "103.10.60.0/22", "114.120.0.0/13"],
        "TH":  ["1.46.0.0/15", "27.55.0.0/16", "49.228.0.0/15", "101.108.0.0/15"],
        "VN":  ["1.52.0.0/14", "14.160.0.0/11", "27.64.0.0/12", "113.160.0.0/12"],
        "PK":  ["39.32.0.0/11", "111.68.96.0/19", "182.176.0.0/12"],
        "ME":  ["2.88.0.0/13", "5.100.0.0/14", "31.166.0.0/15", "37.104.0.0/13"],
        "BR":  ["177.0.0.0/13", "186.192.0.0/12", "189.0.0.0/11", "200.96.0.0/12"],
        "EU":  ["2.16.0.0/12", "5.144.0.0/14", "31.40.0.0/14", "46.16.0.0/14"],
        "CIS": ["2.92.0.0/14", "5.136.0.0/13", "31.128.0.0/12", "46.0.0.0/12"],
        "NA":  ["3.0.0.0/9", "8.0.0.0/12", "12.0.0.0/10", "24.0.0.0/10"],
        "SAC": ["186.0.0.0/10", "190.0.0.0/11", "200.0.0.0/11"],
        "TW":  ["1.160.0.0/12", "36.224.0.0/12", "114.24.0.0/12", "118.160.0.0/12"],
    }
    PROXIES = []; _proxy_index = 0; _proxy_lock = threading.Lock()

    @classmethod
    def load_proxies(cls):
        for path in ("proxies.txt", os.path.join(rOoT_dIr, "proxies.txt")):
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        lines = [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]
                    if lines: cls.PROXIES = lines; return len(lines)
                except Exception: pass
        cls.PROXIES = []; return 0

    @classmethod
    def get_random_ip_from_cidr(cls, cidr):
        try:
            net = ipaddress.IPv4Network(cidr, strict=False); n = net.num_addresses
            off = random.randint(1, max(1, n - 2)) if n > 2 else 0
            return str(ipaddress.IPv4Address(int(net.network_address) + off))
        except Exception: return "103.220.220.10"

    @classmethod
    def get_rotating_ip(cls, region):
        reg = (region or "IND").upper()
        cidr = random.choice(cls.REGION_IP_CIDRS.get(reg) or random.choice(list(cls.REGION_IP_CIDRS.values())))
        return cls.get_random_ip_from_cidr(cidr)

    @classmethod
    def get_headers_with_ip_rotation(cls, base, region):
        h = dict(base); ip = cls.get_rotating_ip(region)
        h["X-Forwarded-For"] = ip; h["X-Real-IP"] = ip
        h["Client-IP"] = ip; h["CF-Connecting-IP"] = ip; h["True-Client-IP"] = ip
        return h

IPRotator.load_proxies()

# ───────────────────────────── COMMAND CONSOLE ─────────────────────────────

CMD_TIMEOUT = int(os.environ.get("CMD_TIMEOUT", "900"))
CMD_HISTORY_MAX = 400
cMd_HiStOrY = []; cMd_HiStOrY_lOcK = threading.Lock()

def rUn_sHeLl(c):
    c = (c or "").strip()
    if not c: return {"ok": True, "code": 0, "out": ""}
    t0 = time.time()
    try:
        r = subprocess.run(c, shell=True, cwd=rOoT_dIr, capture_output=True, timeout=CMD_TIMEOUT)
        out = (r.stdout or b"").decode("utf-8", "replace"); err = (r.stderr or b"").decode("utf-8", "replace")
        body = out + (("\n" + err) if err.strip() else ""); code = r.returncode
    except subprocess.TimeoutExpired: body, code = f"⏱ timed out", -1
    except Exception as eX: body, code = f"❌ {eX}", -1
    rec = {"cmd": c, "code": code, "out": body.strip()[-20000:], "secs": round(time.time() - t0, 2),
           "at": datetime.now().strftime("%H:%M:%S")}
    with cMd_HiStOrY_lOcK:
        cMd_HiStOrY.append(rec)
        if len(cMd_HiStOrY) > CMD_HISTORY_MAX: del cMd_HiStOrY[:-CMD_HISTORY_MAX]
    lOg(f"$ {c}  → exit {code} ({rec['secs']}s)", "ok" if code == 0 else "err")
    return {"ok": code == 0, "code": code, "out": rec["out"]}

# ───────────────────────────── CRYPTO / PROTO ─────────────────────────────

def sUpErScRiPt():
    d = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"}
    return "".join(d[x] for x in f"{random.randint(1, 99999):05d}")

def rAnDoM_nAmE(p): return f"{p[:7]}{sUpErScRiPt()}"
def rAnDoM_nAmE_fAsT(p, ml=12):
    p = (p or "NGRX")[:7]
    try: ml = max(4, min(14, int(ml)))
    except Exception: ml = 12
    a = max(1, ml - len(p)); return p + "".join(random.choice("0123456789") for _ in range(a))
def mAkE_pAsSwOrD(p):
    ch = string.ascii_uppercase + string.digits
    return f"{p}_{''.join(random.choice(ch) for _ in range(5))}_{''.join(random.choice(ch) for _ in range(5))}"

def bUiLd_pAsSwOrD(cFg=None):
    cFg = cFg or sTaTe.get("config", {}) or {}
    m = str(cFg.get("passmode") or PASS_MODE_PATTERN).lower(); p = cFg.get("pass") or "NGRX"
    if m == PASS_MODE_FIXED: return str(cFg.get("passvalue") or p)
    if m == PASS_MODE_HASH: return hashlib.sha256(os.urandom(8)).hexdigest().upper()
    if m == PASS_MODE_CUSTOM:
        t = str(cFg.get("passtemplate") or f"{p}_****_****"); ch = string.ascii_uppercase + string.digits
        return "".join(random.choice(ch) if c == "*" else c for c in t)
    return mAkE_pAsSwOrD(p)

def pAsSwOrD_pReViEw(cFg=None):
    try: return bUiLd_pAsSwOrD(cFg)
    except Exception: return "NGRX_XXXXX_XXXXX"

def pAuSe(): time.sleep(random.uniform(0.3, 0.8))

aEs_KeY = bytes([89,103,38,116,99,37,68,69,117,104,54,37,90,99,94,56])
aEs_Iv  = bytes([54,111,121,90,68,114,50,50,69,51,121,99,104,106,77,37])
cLiEnT_sEcReT = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
aPp_Id = 100067
oAuTh_ReGiStEr = "https://100067.connect.garena.com/api/v2/oauth/guest:register"
oAuTh_ToKeN    = "https://100067.connect.garena.com/oauth/guest/token/grant"

xOr_KeY = [0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,
           0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30]

fIeLd_22_hEx = (
    "474752450101010062020000a78910bd098e3ff2e4345d59a31db114ea088f37e32e65"
    "212ff96621793d9eb78720d0bf2ac95176569765247ada5eb01376b3b9931794a4946"
    "d76ef8890779f3f2129317e6e1cb2fdcf7b06247cea343b8d4f167eff85a2e1dfe99"
    "b4583a7e1a155dbe7f7f85cff3b223eb77222ec1228f3ee1ef6ce7f8ca24b00a554"
    "e497328812f8df74c82d519ae3e3ceab436eb145e8a517089a7cef6a4efb22214b2"
    "a4b19989b74807584afe5e52825e7ac60e19a596a9bf02d961de6a0ed2515ec6023"
    "fdb7684d9464b97b21c527ce61b6bee4ef30d20a1fa33a996952d44d44e44f2f86c"
    "768aaf2a7808ad60f91048dca0207961ba7c2555c48341b30190debc775edb2cee24"
    "4cf51fca3760ce4388be2db45e80b813b5beb9c784007b7762d7a1e428affc8a3a4"
    "cd76cbaef648a274297fde33233dccd3f272cb77f39a1affe0365a24954111f768f72"
    "0e77535af024bea2b2726c3bac992374755c3deacf09235e6865d456e651680d115a"
    "751a797225eaacdf9a513cf104526e1a32e5296e111a33ae581a63850837921df848"
    "9adfd41ea895b7cf3f5b2e45d538a6e4f032f590ccbb7daf5fa9c50adadee0799661"
    "4c3f957bda349e6c484fdf55970d1943ad7955a76671298b6d98b636b69ebde6bc94"
    "dbd93ac3393a6ae230130445b2d744189167854a5617be2393e7d8fbb5719a1b4754"
    "1ba466167e3e05a6c244f1301ee2035acf94dffc8adbde747d5cd85e35ead3acc372"
    "a59c4220e54bf63f9d80485f3de2518495c1d0f78c911d2da595911fd2a1989cf17"
    "cf3ded5f6c92dea64d675c555c11df92d6c517ca5d0d61a8962f43f76ec7e87596c"
    "8325ebf9ab0f8e6d2eca33c511ceac6980906ebd68c478665591dcecf788ec6ef34c"
    "fbe3fcc279c6147c5bf91cd43cdc9704236"
)
if len(fIeLd_22_hEx) % 2: fIeLd_22_hEx += "0"
fIeLd_22_bYtEs = bytes.fromhex(fIeLd_22_hEx)

def gA_sV(): return str(int(time.time()))

def wRiTe_vArInT(v):
    o = []
    while v > 127: o.append((v & 0x7F) | 0x80); v >>= 7
    o.append(v); return bytes(o)

def fIeLd_iNt(n, v): return wRiTe_vArInT((n << 3) | 0) + wRiTe_vArInT(v)
def fIeLd_sTr(n, v):
    e = v.encode("utf-8"); return wRiTe_vArInT((n << 3) | 2) + wRiTe_vArInT(len(e)) + e
def fIeLd_bYtEs(n, v): return wRiTe_vArInT((n << 3) | 2) + wRiTe_vArInT(len(v)) + v

def aSsEmBlE_pRoTo(f):
    b = bytearray()
    for k, v in f.items():
        if isinstance(v, int): b.extend(fIeLd_iNt(k, v))
        elif isinstance(v, str): b.extend(fIeLd_sTr(k, v))
        elif isinstance(v, (bytes, bytearray)): b.extend(fIeLd_bYtEs(k, bytes(v)))
    return bytes(b)

def eNcRyPt_aEs(p): return AES.new(aEs_KeY, AES.MODE_CBC, aEs_Iv).encrypt(pad(p, AES.block_size))

def rEaD_vArInT(d, o):
    r, s = 0, 0
    while True:
        if o >= len(d): raise IndexError("eof")
        b = d[o]; r |= (b & 0x7F) << s; o += 1
        if not (b & 0x80): break
        s += 7
    return r, o

def pArSe_pRoTo(d):
    out, o = {}, 0
    while o < len(d):
        try: tag, o = rEaD_vArInT(d, o)
        except Exception: break
        n, wt = tag >> 3, tag & 0x7
        try:
            if wt == 0: v, o = rEaD_vArInT(d, o); out[n] = v
            elif wt == 2:
                ln, o = rEaD_vArInT(d, o); ch = d[o:o+ln]; o += ln
                try: out[n] = ch.decode("utf-8")
                except Exception: out[n] = ch.hex()
            elif wt == 1: out[n] = d[o:o+8].hex(); o += 8
            elif wt == 5: out[n] = d[o:o+4].hex(); o += 4
            else: break
        except Exception: break
    return out

def xOr_OpEn_Id(oid):
    r = oid.encode("utf-8"); return bytes(x ^ xOr_KeY[i % len(xOr_KeY)] for i, x in enumerate(r))

def xOr_OpEn_Id_LeGaCy(oid):
    e = "".join(chr(ord(c) ^ xOr_KeY[i % len(xOr_KeY)]) for i, c in enumerate(oid))
    u = "".join(c if 32 <= ord(c) <= 126 else f"\\u{ord(c):04x}" for c in e)
    return codecs.decode(u, "unicode_escape").encode("latin1")

def sIgN_pAyLoAd(p):
    b = json.dumps(p, separators=(",", ":"))
    return hmac.new(cLiEnT_sEcReT.encode(), b.encode(), hashlib.sha256).hexdigest()

# ───────────────────────────── ACCOUNT FLOW ─────────────────────────────

def _dEv_hEaDeRs(dEv, region, base=None):
    h = dict(base or {})
    h.update(IPRotator.get_headers_with_ip_rotation({}, region))
    h.update({
        "X-GA-DEVICE": dEv["model"], "X-GA-BRAND": dEv["brand"],
        "X-GA-OS": f"Android {dEv['android']}", "X-GA-SDK": str(dEv["sdk"]),
        "X-GA-RES": dEv["res"], "X-GA-DPI": str(dEv["dpi"]),
        "X-GA-LOCALE": dEv["locale"], "X-GA-COUNTRY": dEv["cc"],
        "X-GA-ADID": dEv["adid"], "X-GA-MAC": dEv["mac"],
    })
    return h

def rEgIsTeR_gUeSt(cTx, pw):
    dEv = cTx.device
    p = {"app_id": aPp_Id, "client_type": 2, "password": pw, "source": 2}
    b = json.dumps(p, separators=(",", ":"))
    h = _dEv_hEaDeRs(dEv, cTx.region, {
        "User-Agent": dEv["msdk"], "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "Connection": "Keep-Alive", "Accept-Encoding": "gzip",
        "Authorization": f"Signature {sIgN_pAyLoAd(p)}",
    })
    _rAtE_gAtE()
    r = cTx.session.post(oAuTh_ReGiStEr, data=b, headers=h, timeout=HTTP_TIMEOUT)
    cTx.tick()
    if r.status_code != 200: raise Exception(f"Register HTTP {r.status_code}")
    d = r.json()
    if d.get("code") != 0: raise Exception(f"Register failed: {d.get('code')}")
    return str(d["data"]["uid"])

def rEqUeSt_tOkEn(cTx, uid, pw):
    dEv = cTx.device
    p = {"uid": uid, "password": pw, "response_type": "token",
         "client_type": "2", "client_secret": cLiEnT_sEcReT, "client_id": "100067"}
    h = _dEv_hEaDeRs(dEv, cTx.region, {
        "User-Agent": dEv["msdk"], "Accept": "application/json",
        "Accept-Encoding": "gzip", "Connection": "Keep-Alive"})
    _rAtE_gAtE()
    r = cTx.session.post(oAuTh_ToKeN, data=p, headers=h, timeout=HTTP_TIMEOUT)
    cTx.tick()
    if r.status_code != 200: raise Exception(f"Token HTTP {r.status_code}")
    d = r.json()
    at, oid = d.get("access_token"), d.get("open_id")
    if not at or not oid: raise Exception("Token grant failed")
    return at, oid

def mAjOr_ReGiStEr(cTx, name, at, oid, legacy=False):
    dEv = cTx.device; uRl = sErVeR_GlObAl + "MajorRegister"
    fields = {1: name, 2: at, 3: oid, 5: 102000007, 6: 4, 7: 1, 13: 1,
        14: (xOr_OpEn_Id_LeGaCy(oid) if legacy else xOr_OpEn_Id(oid)),
        15: rEgIsTrAtIoN_lAnGuAgE, 16: 2,
        20: (fAsT_rEgIsTrAtIoN_vErSiOn if legacy else rEgIsTrAtIoN_vErSiOn),
        21: 1, 22: fIeLd_22_bYtEs}
    enc = eNcRyPt_aEs(aSsEmBlE_pRoTo(fields))
    h = _dEv_hEaDeRs(dEv, cTx.region, {
        "Host": uRl.split("/")[2], "User-Agent": dEv["unity"], "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip", "X-GA-SV": gA_sV(), "Authorization": "Bearer",
        "X-GA": "v1 1", "ReleaseVersion": rElEaSe_TaG,
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2018.4.12f1", "Content-Length": str(len(enc))})
    _rAtE_gAtE()
    r = cTx.session.post(uRl, data=enc, headers=h, timeout=HTTP_TIMEOUT)
    cTx.tick()
    if r.status_code != 200: raise Exception(f"MajorRegister HTTP {r.status_code}")
    return pArSe_pRoTo(r.content)

def nEwBiE_cHoIcE(cTx, aid, choice=3):
    uRl = sErVeR_GlObAl + "ChooseNewbieChoice"
    enc = eNcRyPt_aEs(aSsEmBlE_pRoTo({1: int(aid), 2: 1, 3: int(choice)}))
    h = _dEv_hEaDeRs(cTx.device, cTx.region, {
        "Host": uRl.split("/")[2], "User-Agent": cTx.device["unity"], "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip", "X-GA-SV": gA_sV(), "Authorization": "Bearer",
        "X-GA": "v1 1", "ReleaseVersion": rElEaSe_TaG,
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2018.4.12f1", "Content-Length": str(len(enc))})
    r = cTx.session.post(uRl, headers=h, data=enc, timeout=HTTP_TIMEOUT)
    cTx.tick(); return r

def cReAtE_aCcOuNt(cTx, nAmE, tid):
    if sToP_fLaG: return None
    cfg = cTx.cfg; pw = bUiLd_pAsSwOrD(cfg); uid = rEgIsTeR_gUeSt(cTx, pw)
    at, oid = rEqUeSt_tOkEn(cTx, uid, pw); _gAp()
    aid, final_name = None, ""
    for _ in range(10):
        final_name = rAnDoM_nAmE(nAmE)
        try:
            rs = mAjOr_ReGiStEr(cTx, final_name, at, oid, legacy=False); aid = rs.get(3)
            if aid: aid = str(aid); break
        except Exception: time.sleep(0.35)
    if not aid: raise Exception("major register: no account_id")
    try: nEwBiE_cHoIcE(cTx, aid, 3)
    except Exception: pass
    return {"uid": uid, "password": pw, "name": final_name, "region": cTx.region,
            "account_id": aid, "access_token": at, "thread_id": tid, "engine": ENGINE_CLASSIC}

def cReAtE_aCcOuNt_fAsT(cTx, nAmE, tid):
    if sToP_fLaG: return None
    cfg = cTx.cfg; pw = bUiLd_pAsSwOrD(cfg); uid = rEgIsTeR_gUeSt(cTx, pw)
    at, oid = rEqUeSt_tOkEn(cTx, uid, pw)
    final_name = rAnDoM_nAmE_fAsT(nAmE, cfg.get("nicklen", 12))
    rs = mAjOr_ReGiStEr(cTx, final_name, at, oid, legacy=True); aid = rs.get(3)
    if not aid: raise Exception("no account_id in MajorRegister")
    return {"uid": uid, "password": pw, "name": final_name, "region": cTx.region,
            "account_id": str(aid), "access_token": at, "thread_id": tid, "engine": ENGINE_FAST}

# ───────────────────────────── JOB FLOW ─────────────────────────────

def _pUbLiSh_wOrKeR(cTx):
    with lOcK:
        sTaTe["workers"][cTx.idx] = {
            "i": cTx.idx, "ok": cTx.ok, "fail": cTx.fail,
            "dev": cTx.device["model"], "os": cTx.device["android"],
            "proxy": (cTx.proxy or "—"), "rot": cTx.rotations,
        }

def gEnErAtE_oNe(cTx):
    cfg = cTx.cfg
    if cfg.get("engine") == ENGINE_FAST:
        acc = cReAtE_aCcOuNt_fAsT(cTx, cfg["name"], cTx.idx)
    else:
        acc = cReAtE_aCcOuNt(cTx, cfg["name"], cTx.idx)
    if not acc: return None
    sAvE_aCcOuNt(acc)
    with lOcK:
        sTaTe["generated"] += 1; n = sTaTe["generated"]
    cTx.ok += 1
    if cTx.proxy: _pRoXyPoOl.report(cTx.proxy, True)
    _pUbLiSh_wOrKeR(cTx)
    lOg(f"[{n}/{sTaTe['total']}] {acc['name']} · {acc['account_id']} · "
       f"{acc['region']} · w{cTx.idx} ({cTx.device['model']} · ↻{cTx.rotations})", "ok")
    is_rare, rtype, rreason, rscore = aSsEsS_rArItY(acc, cfg["threshold"])
    if is_rare:
        with lOcK: sTaTe["rare"] += 1
        sAvE_rArE(acc, rtype, rreason, rscore)
        lOg(f"💎 RARE {acc['account_id']} — {rreason} (score {rscore})", "rare")
        with lOcK:
            sTaTe["rare_accounts"].append({
                "name": acc["name"], "account_id": acc["account_id"],
                "uid": acc["uid"], "password": acc["password"],
                "region": acc["region"], "score": rscore,
                "reason": rreason, "engine": acc.get("engine"),
                "at": datetime.now().strftime("%H:%M:%S")})
            if len(sTaTe["rare_accounts"]) > 5000: del sTaTe["rare_accounts"][:-5000]
    if cfg.get("couples"):
        is_c, creason, pdata = aSsEsS_cOuPlE(acc, cTx.idx)
        if is_c and pdata:
            with lOcK: sTaTe["couples"] += 1
            sAvE_cOuPlE(acc, pdata, creason)
            lOg(f"💑 COUPLE {acc['account_id']} & {pdata.get('account_id')} — {creason}", "rare")
    return acc

def wOrKeR(cTx):
    try:
        while not sToP_fLaG:
            with lOcK:
                if sTaTe["generated"] >= sTaTe["total"]: return
                if sTaTe["attempts"] >= sTaTe["attempt_cap"]: return
                sTaTe["attempts"] += 1
            try: oK = gEnErAtE_oNe(cTx) is not None
            except Exception as eX:
                oK = False
                if cTx.proxy: _pRoXyPoOl.report(cTx.proxy, False)
                lOg(f"w{cTx.idx} ✗ {str(eX)[:80]}", "err")
            if oK:
                cTx.fail_streak = 0; _jItTeR(); continue
            cTx.fail += 1; cTx.fail_streak += 1
            _pUbLiSh_wOrKeR(cTx)
            with lOcK: sTaTe["failed"] += 1
            if cTx.fail_streak % rOtAtIoN_tHrEsHoLd == 0:
                nEw = cTx.rotate()
                if nEw: lOg(f"w{cTx.idx} ↻ rotate → {nEw[:28]}", "warn")
            bf = min(FAIL_BACKOFF_MAX, 0.3 * (2 ** min(cTx.fail_streak, 5)))
            time.sleep(bf + random.uniform(0, 0.5))
    finally:
        _pUbLiSh_wOrKeR(cTx); cTx.close()

def rUn_jOb(cfg):
    global sToP_fLaG
    sToP_fLaG = False; sTaTe["config"] = cfg; sTaTe["total"] = cfg["total"]
    sTaTe["attempt_cap"] = max(cfg["total"], cfg["total"] * int(cfg.get("maxtries", DEFAULT_MAX_TRIES)))
    sTaTe.update({"generated": 0, "failed": 0, "attempts": 0, "rare": 0, "couples": 0,
                  "rare_accounts": [], "workers": {}, "region": cfg["region"],
                  "engine": cfg["engine"], "running": True,
                  "started_at": time.time(), "finished_at": 0.0, "elapsed": 0.0})
    cOuPlE_cAnDiDaTeS.clear()

    if pRoXy_MoDe == "free":
        lOg("🌍 fetching & verifying LIVE proxies (exit-IP check) ...", "info")
        if not _pRoXyPoOl.ensure_live(MIN_LIVE_PROXIES):
            lOg("❌ No live proxy found — job aborted (direct mode is disabled)", "err")
            sTaTe["running"] = False
            sTaTe["finished_at"] = time.time()
            sTaTe["elapsed"] = 0.0
            return
        lOg(f"✅ proxy pool ready: {_pRoXyPoOl.alive_count()} LIVE proxies", "ok")

    if pRoXy_MoDe == "tor" and cfg.get("tor") and uSe_tOr_PrOxY:
        if "ready" not in str(tOr_MgR.state):
            if not tOr_MgR.start():
                lOg("❌ Tor unavailable — job aborted (direct mode is disabled)", "err")
                sTaTe["running"] = False
                sTaTe["finished_at"] = time.time()
                return

    lOg(f"▶ Job · {cfg['engine']} · {cfg['region']} · total={cfg['total']} · "
       f"w={cfg['threads']} · turbo={TURBO_ROTATION} · net={pRoXy_MoDe} (proxy mandatory)", "info")
    lOg(f"🔑 password sample: {pAsSwOrD_pReViEw(cfg)}", "info")

    salt = int(time.time())
    ctxs = [WorkerCtx(i + 1, cfg["region"], cfg, salt) for i in range(cfg["threads"])]
    for cTx in ctxs: _pUbLiSh_wOrKeR(cTx)
    lOg("🧬 farm: " + ", ".join(f"w{c.idx}={c.device['model']}" for c in ctxs[:8])
        + (" …" if len(ctxs) > 8 else ""), "info")

    threads = []
    for cTx in ctxs:
        t = threading.Thread(target=wOrKeR, args=(cTx,), daemon=True)
        t.start(); threads.append(t)
        if WORKER_STAGGER > 0: time.sleep(WORKER_STAGGER)

    for t in threads: t.join()

    sTaTe["running"] = False; sTaTe["finished_at"] = time.time()
    sTaTe["elapsed"] = sTaTe["finished_at"] - sTaTe["started_at"]
    lOg(f"■ Done · generated={sTaTe['generated']} · rare={sTaTe['rare']} · couples={sTaTe['couples']}", "info")

# ───────────────────────────── STATE ─────────────────────────────

lOcK = threading.Lock(); sToP_fLaG = False
sTaTe = {"running": False, "total": 0, "generated": 0, "failed": 0, "attempts": 0,
    "attempt_cap": 0, "rare": 0, "couples": 0, "region": "", "engine": ENGINE_CLASSIC,
    "started_at": 0.0, "finished_at": 0.0, "elapsed": 0.0, "logs": [], "log_index": 0,
    "rare_accounts": [], "workers": {}, "netmode": "free",
    "config": {"region": "IND", "total": 50, "name": "NGRX", "pass": "NGRX",
        "threads": 16, "threshold": REPEAT_RARE_THRESHOLD, "tor": False, "couples": True,
        "netmode": "free", "engine": ENGINE_CLASSIC, "passmode": PASS_MODE_PATTERN,
        "passvalue": "", "passtemplate": "", "nicklen": 12, "maxtries": DEFAULT_MAX_TRIES, "heavy": True}}

def lOg(m, lvl="info"):
    with lOcK:
        sTaTe["logs"].append({"i": sTaTe["log_index"], "t": datetime.now().strftime("%H:%M:%S"),
                              "m": str(m), "l": lvl})
        sTaTe["log_index"] += 1
        if len(sTaTe["logs"]) > 1500: del sTaTe["logs"][:len(sTaTe["logs"]) - 1500]

def _hAnDlE_sIgNaL(signum, _f):
    global sToP_fLaG; sToP_fLaG = True
    try: lOg(f"signal {signum} — stopping", "warn")
    except Exception: pass

try:
    signal.signal(signal.SIGTERM, _hAnDlE_sIgNaL)
    signal.signal(signal.SIGINT, _hAnDlE_sIgNaL)
except Exception: pass

# ───────────────────────────── FLASK APP ─────────────────────────────

app = Flask(__name__)

@app.route("/")
def index(): return Response(INDEX_HTML, mimetype="text/html")

@app.route("/healthz")
@app.route("/health")
def healthz(): return Response("ok", mimetype="text/plain")

@app.route("/api/status")
def api_status():
    with lOcK:
        running = sTaTe["running"]
        el = (time.time() - sTaTe["started_at"]) if running else sTaTe["elapsed"]
        rate = (sTaTe["generated"] / el) if el > 0 else 0.0
        payload = {"running": running, "generated": sTaTe["generated"],
            "failed": sTaTe["failed"], "attempts": sTaTe["attempts"],
            "rare": sTaTe["rare"], "couples": sTaTe["couples"], "total": sTaTe["total"],
            "region": sTaTe["region"], "engine": sTaTe["engine"], "elapsed": round(el, 1),
            "rate": round(rate, 2), "tor": tOr_MgR.state, "log_index": sTaTe["log_index"],
            "rare_accounts": list(reversed(sTaTe["rare_accounts"][-300:])),
            "build": "3.1.0", "netmode": pRoXy_MoDe,
            "proxies": _pRoXyPoOl.alive_count(), "ipfile": len(IPRotator.PROXIES),
            "socks": _SOCKS_OK, "heavy": HEAVY_MODE, "turbo": TURBO_ROTATION,
            "threads": sTaTe["config"].get("threads", 0), "rotate_every": ROTATE_EVERY_N,
            "devices": len(_dEvIcE_mOdElS), "proxy_mandatory": True,
            "android": _IS_ANDROID, "pool_max": POOL_MAXSIZE,
            "workers": [sTaTe["workers"][k] for k in sorted(sTaTe["workers"])][:100]}
    return jsonify(payload)

@app.route("/api/logs")
def api_logs():
    since = int(request.args.get("since", 0))
    with lOcK:
        lines = [x for x in sTaTe["logs"] if x["i"] >= since]
        nxt = sTaTe["log_index"]
    return jsonify({"lines": lines, "next": nxt})

@app.route("/api/start", methods=["POST"])
def api_start():
    global pRoXy_MoDe, HEAVY_MODE, TURBO_ROTATION
    if sTaTe["running"]: return jsonify({"ok": False, "error": "already running"}), 409
    d = request.get_json(force=True, silent=True) or {}
    try:
        region = str(d.get("region", "IND")).upper(); total = int(d.get("total", 50))
        threads = int(d.get("threads", 16)); threshold = int(d.get("threshold", REPEAT_RARE_THRESHOLD))
        name = (d.get("name") or "NGRX").strip()[:7] or "NGRX"
        pw = (d.get("pass") or "NGRX").strip() or "NGRX"
        tor = bool(d.get("tor", False)); couples = bool(d.get("couples", True))
        netmode = str(d.get("netmode", "free")).lower()
        engine = str(d.get("engine", ENGINE_CLASSIC)).lower()
        passmode = str(d.get("passmode", PASS_MODE_PATTERN)).lower()
        passvalue = str(d.get("passvalue") or ""); passtemplate = str(d.get("passtemplate") or "")
        nicklen = int(d.get("nicklen", 12)); maxtries = int(d.get("maxtries", DEFAULT_MAX_TRIES))
        heavy = bool(d.get("heavy", HEAVY_MODE)); turbo = bool(d.get("turbo", TURBO_ROTATION))
    except Exception as e:
        return jsonify({"ok": False, "error": f"bad config: {e}"}), 400
    if total < 1 or total > 100000: return jsonify({"ok": False, "error": "total must be 1..100000"}), 400
    if not (1 <= threads <= MAX_THREADS_HARD):
        return jsonify({"ok": False, "error": f"threads must be 1..{MAX_THREADS_HARD}"}), 400
    if netmode not in ("tor", "free"):
        return jsonify({"ok": False, "error": "direct mode is disabled — proxy is mandatory"}), 400
    pRoXy_MoDe = netmode
    sTaTe["netmode"] = pRoXy_MoDe; HEAVY_MODE = heavy; TURBO_ROTATION = turbo
    cfg = {"region": region, "total": total, "threads": threads, "threshold": threshold,
        "name": name, "pass": pw, "tor": tor, "couples": couples, "netmode": pRoXy_MoDe,
        "engine": engine, "passmode": passmode, "passvalue": passvalue,
        "passtemplate": passtemplate or f"{pw}_****_****", "nicklen": nicklen,
        "maxtries": maxtries, "heavy": heavy, "turbo": turbo}
    threading.Thread(target=rUn_jOb, args=(cfg,), daemon=True).start()
    return jsonify({"ok": True, "config": cfg})

@app.route("/api/stop", methods=["POST"])
def api_stop():
    global sToP_fLaG; sToP_fLaG = True
    lOg("⏹ Stop requested ...", "warn"); return jsonify({"ok": True})

@app.route("/api/reset", methods=["POST"])
def api_reset():
    if sTaTe["running"]: return jsonify({"ok": False, "error": "running"}), 409
    with lOcK:
        sTaTe.update({"logs": [], "log_index": 0, "rare_accounts": [], "workers": {},
                      "generated": 0, "failed": 0, "attempts": 0, "rare": 0, "couples": 0, "elapsed": 0.0})
    return jsonify({"ok": True})

@app.route("/api/cmd", methods=["POST"])
def api_cmd():
    d = request.get_json(force=True, silent=True) or {}
    return jsonify(rUn_sHeLl(d.get("cmd", "")))

@app.route("/api/proxies", methods=["GET", "POST"])
def api_proxies():
    if request.method == "POST":
        n = _pRoXyPoOl.fetch(force=True)
        lOg(f"🌍 proxy pool: {_pRoXyPoOl.alive_count()} LIVE / {n} total", "ok")
        return jsonify({"ok": n > 0, "count": _pRoXyPoOl.alive_count()})
    return jsonify({"count": _pRoXyPoOl.alive_count(), "sample": _pRoXyPoOl.sample(10)})

@app.route("/api/proxies/file", methods=["POST"])
def api_proxies_file():
    n = IPRotator.load_proxies()
    lOg(f"🧩 proxies.txt reloaded: {n} entries", "ok" if n else "warn")
    return jsonify({"ok": True, "count": n})

@app.route("/api/tor/log")
def api_tor_log():
    with tOr_MgR.lock: return jsonify({"state": tOr_MgR.state, "lines": list(tOr_MgR.logs)})

@app.route("/api/tor/restart", methods=["POST"])
def api_tor_restart():
    global pRoXy_MoDe, uSe_tOr_PrOxY; pRoXy_MoDe = "tor"; uSe_tOr_PrOxY = True
    threading.Thread(target=tOr_MgR.start, daemon=True).start()
    return jsonify({"ok": True})

@app.route("/api/password/preview", methods=["POST"])
def api_password_preview():
    d = request.get_json(force=True, silent=True) or {}
    try: samples = [bUiLd_pAsSwOrD(d) for _ in range(3)]
    except Exception as e: return jsonify({"ok": False, "error": str(e)}), 400
    return jsonify({"ok": True, "samples": samples})

def _jSoN_dL(pAtH, prefix):
    if not os.path.isdir(pAtH): return jsonify({"ok": False, "error": "no data yet"}), 404
    blob = {}
    for fn in sorted(os.listdir(pAtH)):
        if fn.endswith(".json"): blob[fn] = _rEaD_rEcOrDs(os.path.join(pAtH, fn))
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Response(json.dumps(blob, indent=2, ensure_ascii=False), mimetype="application/json",
                    headers={"Content-Disposition": f"attachment; filename={prefix}-{stamp}.json"})

@app.route("/api/download")
def api_download():
    with lOcK: data = json.dumps(sTaTe["rare_accounts"], indent=2, ensure_ascii=False)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Response(data, mimetype="application/json",
                    headers={"Content-Disposition": f"attachment; filename=ngraxx-rare-{stamp}.json"})

@app.route("/api/download/accounts")
def api_download_accounts(): return _jSoN_dL(aCcOuNt_DiR, "ngraxx-accounts")
@app.route("/api/download/rare")
def api_download_rare(): return _jSoN_dL(rArE_DiR, "ngraxx-rare-all")
@app.route("/api/download/couples")
def api_download_couples(): return _jSoN_dL(cOuPlE_DiR, "ngraxx-couples")

# ───────────────────────────── FRONTEND ─────────────────────────────

INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" /><meta name="viewport" content="width=device-width,initial-scale=1" />
<title>NGRAXX · v3.1 · STRICT PROXY · TERMUX-SAFE</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}
:root{--bg:#04060a;--card:rgba(255,255,255,.045);--stroke:rgba(255,255,255,.09);
  --txt:#e9f1ff;--dim:#8ea0bb;--g:#2bff88;--c:#22d3ee;--m:#ff3fd8;--y:#ffd166;--r:#ff5470}
html,body{margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font-family:Inter,system-ui,sans-serif;min-height:100vh;overflow-x:hidden}
.aurora{position:fixed;inset:0;z-index:0;overflow:hidden;filter:blur(100px);opacity:.5;pointer-events:none}
.aurora span{position:absolute;display:block;border-radius:50%}
.aurora span:nth-child(1){width:44vw;height:44vw;background:#0f7a58;top:-14vw;left:-10vw;animation:f1 20s ease-in-out infinite}
.aurora span:nth-child(2){width:38vw;height:38vw;background:#0b4f8a;bottom:-12vw;right:-8vw;animation:f2 26s ease-in-out infinite}
.aurora span:nth-child(3){width:30vw;height:30vw;background:#7a1170;top:35%;left:45%;animation:f3 22s ease-in-out infinite}
@keyframes f1{50%{transform:translate(8vw,6vw) scale(1.15)}}
@keyframes f2{50%{transform:translate(-7vw,-5vw) scale(1.2)}}
@keyframes f3{50%{transform:translate(-5vw,7vw) scale(.85)}}
.wrap{position:relative;z-index:1;max-width:1240px;margin:0 auto;padding:26px 18px 60px}
header{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:22px}
.logo{font-size:34px;font-weight:800;letter-spacing:3px;line-height:1;
  background:linear-gradient(92deg,var(--g),var(--c) 45%,var(--m));
  -webkit-background-clip:text;background-clip:text;color:transparent}
.sub{font-size:11px;letter-spacing:6px;color:var(--dim);margin-top:5px;text-transform:uppercase}
.chips{display:flex;gap:8px;flex-wrap:wrap}
.chip{font-size:11px;letter-spacing:1px;padding:6px 11px;border-radius:999px;border:1px solid var(--stroke);
  background:var(--card);color:var(--dim);font-family:'JetBrains Mono',monospace}
.chip.live{border-color:rgba(43,255,136,.45);color:var(--g)}
.chip.dead{border-color:rgba(255,84,112,.4);color:var(--r)}
.chip.warn{border-color:rgba(255,209,102,.45);color:var(--y)}
.chip.turbo{border-color:rgba(255,63,216,.5);color:var(--m)}
.grid{display:grid;grid-template-columns:370px 1fr;gap:18px;align-items:start}
@media(max-width:960px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--stroke);border-radius:18px;padding:18px;
  backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px)}
.card h2{margin:0 0 14px;font-size:12px;letter-spacing:3px;text-transform:uppercase;color:var(--dim);font-weight:600}
label{display:block;font-size:11px;letter-spacing:1.4px;color:var(--dim);margin:12px 0 6px;text-transform:uppercase}
input,select{width:100%;padding:11px 12px;border-radius:11px;background:rgba(0,0,0,.35);
  border:1px solid var(--stroke);color:var(--txt);font-family:'JetBrains Mono',monospace;font-size:13px;outline:none}
input:focus,select:focus{border-color:rgba(43,255,136,.55)}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.row3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
.toggles{display:flex;flex-direction:column;gap:8px;margin-top:14px}
.tg{display:flex;align-items:center;justify-content:space-between;font-size:12px;color:var(--dim);
  border:1px solid var(--stroke);border-radius:11px;padding:10px 12px;background:rgba(0,0,0,.22);cursor:pointer}
.sw{width:40px;height:22px;border-radius:999px;background:#1c2433;position:relative;transition:.18s;flex:0 0 auto}
.sw::after{content:"";position:absolute;top:3px;left:3px;width:16px;height:16px;border-radius:50%;background:#66768f;transition:.18s}
.tg.on .sw{background:linear-gradient(90deg,var(--g),var(--c))}
.tg.on .sw::after{left:21px;background:#02110a}
.tg.turbo.on .sw{background:linear-gradient(90deg,var(--m),var(--y))}
.btns{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:18px}
button{padding:13px;border-radius:12px;border:1px solid var(--stroke);background:rgba(0,0,0,.3);
  color:var(--txt);font-weight:800;letter-spacing:2px;font-size:12px;cursor:pointer;transition:.15s;font-family:Inter,sans-serif}
button:hover{transform:translateY(-1px)}
button:disabled{opacity:.4;cursor:not-allowed;transform:none}
.b-go{background:linear-gradient(92deg,rgba(43,255,136,.22),rgba(34,211,238,.18));border-color:rgba(43,255,136,.5);color:var(--g)}
.b-stop{border-color:rgba(255,84,112,.45);color:var(--r)}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px}
@media(max-width:700px){.stats{grid-template-columns:repeat(2,1fr)}}
.stat{border:1px solid var(--stroke);border-radius:14px;padding:12px;background:rgba(0,0,0,.28)}
.stat .k{font-size:10px;letter-spacing:2px;color:var(--dim);text-transform:uppercase}
.stat .v{font-size:23px;font-weight:800;font-family:'JetBrains Mono',monospace;margin-top:5px}
.v.g{color:var(--g)}.v.m{color:var(--m)}.v.c{color:var(--c)}.v.y{color:var(--y)}.v.r{color:var(--r)}
.bar{height:9px;border-radius:999px;background:rgba(255,255,255,.07);overflow:hidden;margin:6px 0 16px}
.bar i{display:block;height:100%;width:0%;border-radius:999px;background:linear-gradient(90deg,var(--g),var(--c),var(--m));transition:width .35s}
.log{height:212px;overflow:hidden;border-radius:13px;border:1px solid var(--stroke);background:#02040a;
  padding:11px;font-family:'JetBrains Mono',monospace;font-size:11.5px;line-height:1.65}
.log div{white-space:pre-wrap;word-break:break-word}
.log .t{color:#4c5b74;margin-right:7px}
.l-ok{color:#9fe8c4}.l-rare{color:var(--m)}.l-err{color:var(--r)}.l-warn{color:var(--y)}.l-info{color:#8fa6c4}
table{width:100%;border-collapse:collapse;font-size:12px;font-family:'JetBrains Mono',monospace}
th{text-align:left;font-size:10px;letter-spacing:1.6px;color:var(--dim);text-transform:uppercase;padding:8px 6px;border-bottom:1px solid var(--stroke)}
td{padding:8px 6px;border-bottom:1px solid rgba(255,255,255,.05);cursor:copy}
tr:hover td{background:rgba(43,255,136,.05)}
.badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:10px;font-weight:700;
  background:linear-gradient(92deg,rgba(255,63,216,.2),rgba(34,211,238,.15));border:1px solid rgba(255,63,216,.4);color:var(--m)}
.tblwrap{max-height:330px;overflow:auto;border-radius:12px}
.empty{color:var(--dim);font-size:12px;padding:16px 4px;font-family:'JetBrains Mono',monospace}
.foot{margin-top:22px;text-align:center;color:var(--dim);font-size:11px;letter-spacing:1.4px;font-family:'JetBrains Mono',monospace}
.toast{position:fixed;bottom:22px;left:50%;transform:translateX(-50%) translateY(70px);
  background:rgba(6,12,20,.95);border:1px solid rgba(43,255,136,.45);color:var(--g);
  padding:11px 20px;border-radius:11px;font-size:12px;letter-spacing:1.4px;z-index:50;transition:transform .25s;
  font-family:'JetBrains Mono',monospace}
.toast.show{transform:translateX(-50%) translateY(0)}
.cmdout{height:calc(3 * 1.7em);overflow:auto;border-radius:13px;border:1px solid var(--stroke);
  background:#02040a;padding:9px 11px;font-family:'JetBrains Mono',monospace;font-size:11.5px;line-height:1.7}
.cmdout div{white-space:pre-wrap;word-break:break-word}
.c-in{color:var(--c)}.c-ok{color:#9fe8c4}.c-err{color:var(--r)}.c-sys{color:var(--y)}
.cmdrow{display:grid;grid-template-columns:1fr auto;gap:8px;margin-top:10px}
.cmdrow button{padding:11px 20px}
.quick{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.quick button{padding:7px 12px;font-size:10px;letter-spacing:1px;font-weight:600;border-radius:999px;
  color:var(--dim);background:var(--card);font-family:'JetBrains Mono',monospace}
.quick button:hover{color:var(--g);border-color:rgba(43,255,136,.45)}
.hint{font-size:10.5px;color:var(--dim);font-family:'JetBrains Mono',monospace;margin-top:6px;line-height:1.5}
.sec{border-top:1px dashed rgba(255,255,255,.09);margin-top:16px;padding-top:4px}
.rot-badge{color:var(--c);font-weight:700}
</style>
</head>
<body>
<div class="aurora"><span></span><span></span><span></span></div>
<div class="wrap">
  <header>
    <div><div class="logo">NGRAXX</div><div class="sub">100-Device Farm · Strict Proxy · v3.1</div></div>
    <div class="chips">
      <div class="chip" id="chipState">IDLE</div>
      <div class="chip" id="chipEngine">ENGINE CLASSIC</div>
      <div class="chip" id="chipTor">TOR OFF</div>
      <div class="chip" id="chipNet">NET FREE</div>
      <div class="chip" id="chipRot">TURBO ON</div>
      <div class="chip" id="chipBuild">v3.1.0</div>
    </div>
  </header>

  <div class="grid">
    <section class="card">
      <h2>Configuration</h2>
      <label>Generator engine</label>
      <select id="engine">
        <option value="classic">CLASSIC — proxy + newbie choice</option>
        <option value="fast">FAST — register only + proxy rotation</option>
      </select>
      <div class="hint" id="engineHint"></div>

      <label>Region</label>
      <select id="region">
        <option value="IND">IND — India</option><option value="ID">ID — Indonesia</option>
        <option value="ME">ME — Middle East</option><option value="VN">VN — Vietnam</option>
        <option value="TH">TH — Thailand</option><option value="BD">BD — Bangladesh</option>
        <option value="PK">PK — Pakistan</option><option value="TW">TW — Taiwan</option>
        <option value="CIS">CIS</option><option value="SAC">SAC</option>
        <option value="BR">GHOST MODE (BR)</option>
      </select>

      <label>Total accounts</label>
      <input id="total" type="number" min="1" value="100" />

      <div class="row2">
        <div><label>Name prefix</label><input id="name" type="text" value="NGRX" maxlength="7" /></div>
        <div><label>Pass prefix</label><input id="pass" type="text" value="NGRX" /></div>
      </div>

      <div class="sec">
        <label>Password mode</label>
        <select id="passmode">
          <option value="pattern">pattern — PREFIX_AAAAA_BBBBB</option>
          <option value="custom">custom — template (* = random)</option>
          <option value="fixed">fixed — same for all</option>
          <option value="hash">hash — sha256(random)</option>
        </select>
        <div id="passvalueWrap" style="display:none">
          <label>Password value / template</label>
          <input id="passvalue" type="text" placeholder="NGRX_****_****" />
        </div>
        <div class="hint">Sample: <span id="passSample">—</span></div>
        <div class="btns" style="margin-top:10px">
          <button id="btnPassPreview">PREVIEW PASS</button>
          <button id="btnPassReset">RESET</button>
        </div>
      </div>

      <div class="sec">
        <div class="row3">
          <div><label>Threshold</label><input id="threshold" type="number" min="2" max="8" value="4" /></div>
          <div><label>Workers</label><input id="threads" type="number" min="1" max="100" value="20" /></div>
          <div><label>Max tries</label><input id="maxtries" type="number" min="1" max="10" value="4" /></div>
        </div>
        <div id="nickWrap" style="display:none">
          <label>Nickname max length (fast)</label>
          <input id="nicklen" type="number" min="4" max="14" value="12" />
        </div>
      </div>

      <div class="toggles">
        <div class="tg on" id="tgCouples"><span>Detect couple IDs</span><span class="sw"></span></div>
        <div class="tg on" id="tgHeavy"><span>Heavy mode (full speed)</span><span class="sw"></span></div>
        <div class="tg turbo on" id="tgTurbo"><span>⚡ Turbo rotation (1-3 req)</span><span class="sw"></span></div>
      </div>

      <label>Network mode</label>
      <select id="netmode">
        <option value="free">Free proxy pool — LIVE-VERIFIED (recommended)</option>
        <option value="tor">Tor (slow rotation)</option>
      </select>
      <div class="hint">🔒 <b>Direct is disabled.</b> Generator refuses to start without live, exit-IP-verified proxies. Termux-safe pools applied automatically.</div>
      <div class="btns" style="margin-top:10px">
        <button id="btnFree">VERIFY FREE IPs</button>
        <button id="btnPcount" disabled>LIVE: 0</button>
      </div>
      <div class="btns" style="margin-top:10px">
        <button id="btnReloadFile">RELOAD proxies.txt</button>
        <button id="btnFileCount" disabled>FILE: 0</button>
      </div>
      <div class="btns" style="margin-top:10px">
        <button id="btnTorRestart">RESTART TOR</button>
        <button id="btnTorLog">TOR LOG</button>
      </div>

      <div class="btns">
        <button class="b-go" id="btnStart">START</button>
        <button class="b-stop" id="btnStop" disabled>STOP</button>
      </div>
      <div class="btns" style="margin-top:10px">
        <button id="btnDl">DOWNLOAD RARE</button>
        <button id="btnReset">RESET</button>
      </div>
      <div class="btns" style="margin-top:10px">
        <button id="btnDlAll">ALL ACCOUNTS</button>
        <button id="btnDlCouples">COUPLES</button>
      </div>
    </section>

    <section>
      <div class="card">
        <h2>Live session</h2>
        <div class="stats">
          <div class="stat"><div class="k">Generated</div><div class="v c" id="sGen">0</div></div>
          <div class="stat"><div class="k">Rare</div><div class="v m" id="sRare">0</div></div>
          <div class="stat"><div class="k">Couples</div><div class="v y" id="sCoup">0</div></div>
        </div>
        <div class="stats">
          <div class="stat"><div class="k">Rate /s</div><div class="v g" id="sRate">0.00</div></div>
          <div class="stat"><div class="k">Elapsed</div><div class="v y" id="sTime">0s</div></div>
          <div class="stat"><div class="k">Target</div><div class="v" id="sTotal">0</div></div>
        </div>
        <div class="bar"><i id="bar"></i></div>
        <div class="log" id="log"></div>
      </div>

      <div class="card" style="margin-top:18px">
        <h2>Workers · strict proxy · IP rotation</h2>
        <div class="tblwrap">
          <table>
            <thead><tr>
              <th>#</th><th>Device</th><th>OS</th><th>OK</th><th>Fail</th><th>↻</th><th>Proxy</th>
            </tr></thead>
            <tbody id="wtbody"><tr><td colspan="7" class="empty">idle</td></tr></tbody>
          </table>
        </div>
      </div>

      <div class="card" style="margin-top:18px">
        <h2>Rare accounts</h2>
        <div class="tblwrap">
          <table>
            <thead><tr>
              <th>#</th><th>Name</th><th>Account ID</th><th>UID</th>
              <th>Password</th><th>Region</th><th>Engine</th><th>Score</th>
            </tr></thead>
            <tbody id="tbody"><tr><td colspan="8" class="empty">No rare accounts yet...</td></tr></tbody>
          </table>
        </div>
      </div>

      <div class="card" style="margin-top:18px">
        <h2>Command console</h2>
        <div class="cmdout" id="cmdout"></div>
        <div class="cmdrow">
          <input id="cmdinput" placeholder="pip list | head -15" />
          <button class="b-go" id="btnRun">RUN</button>
        </div>
      </div>
    </section>
  </div>
  <div class="foot">© 2026 RAXX · NGRAXX v3.1 · STRICT PROXY · TERMUX-SAFE · CLICK CELL TO COPY</div>
</div>
<div class="toast" id="toast">COPIED</div>

<script>
let since = 0, lastIndex = -1;
const $ = id => document.getElementById(id);
const LOG_MAX = 10;

function toast(m){const t=$('toast');t.textContent=m;t.classList.add('show');
  clearTimeout(t._h);t._h=setTimeout(()=>t.classList.remove('show'),1200);}
function addLog(l){const box=$('log');const d=document.createElement('div');
  d.className='l-'+(l.l||'info');
  const s=document.createElement('span');s.className='t';s.textContent=l.t;
  d.appendChild(s);d.appendChild(document.createTextNode(l.m));
  box.appendChild(d);while(box.childNodes.length>LOG_MAX)box.removeChild(box.firstChild);}
function fmtTime(s){s=Math.floor(s);if(s<60)return s+'s';
  const m=Math.floor(s/60);return m+'m '+(s%60)+'s';}
function renderTable(rows){const tb=$('tbody');
  if(!rows||!rows.length){tb.innerHTML='<tr><td colspan="8" class="empty">No rare accounts yet...</td></tr>';return;}
  tb.innerHTML=rows.map((r,i)=>`<tr><td>${i+1}</td><td>${r.name}</td>
    <td style="color:#ff8ce6;font-weight:700">${r.account_id}</td><td>${r.uid}</td>
    <td>${r.password}</td><td>${r.region}</td><td>${r.engine||'-'}</td>
    <td><span class="badge">${r.score}</span></td></tr>`).join('');
  [...tb.querySelectorAll('td')].forEach(td=>{td.onclick=()=>{navigator.clipboard.writeText(td.textContent.trim());
    toast('COPIED: '+td.textContent.trim());};});}
function renderWorkers(rows){const tb=$('wtbody');
  if(!rows||!rows.length){tb.innerHTML='<tr><td colspan="7" class="empty">idle</td></tr>';return;}
  tb.innerHTML=rows.map(w=>`<tr><td>w${w.i}</td><td>${w.dev}</td><td>${w.os}</td>
    <td style="color:#2bff88;font-weight:700">${w.ok}</td>
    <td style="color:#ff5470">${w.fail}</td>
    <td class="rot-badge">↻${w.rot||0}</td>
    <td style="font-size:10px;color:#8ea0bb">${(w.proxy||'—').slice(-22)}</td></tr>`).join('');}
function passBody(){return{pass:$('pass').value||'NGRX',passmode:$('passmode').value,
  passvalue:$('passvalue').value||'',passtemplate:$('passvalue').value||''};}
async function previewPass(){try{const r=await(await fetch('/api/password/preview',{method:'POST',
  headers:{'Content-Type':'application/json'},body:JSON.stringify(passBody())})).json();
  $('passSample').textContent=r.ok?r.samples.join('  |  '):('ERR: '+(r.error||'?'));}
  catch(e){$('passSample').textContent='ERR';}}
function syncPassUI(){const m=$('passmode').value;
  $('passvalueWrap').style.display=(m==='fixed'||m==='custom')?'':'none';
  $('passvalue').placeholder=(m==='fixed')?'exact password':'NGRX_****_****';previewPass();}
function syncEngineUI(){const fast=$('engine').value==='fast';
  $('nickWrap').style.display=fast?'':'none';
  $('engineHint').textContent=fast?'Fast: register-only, digits nickname, proxy rotation.':
    'Classic: superscript nicknames, ChooseNewbieChoice after register.';
  $('chipEngine').textContent='ENGINE '+$('engine').value.toUpperCase();}
async function poll(){try{const s=await(await fetch('/api/status')).json();
  $('sGen').textContent=s.generated;$('sRare').textContent=s.rare;$('sCoup').textContent=s.couples;
  $('sRate').textContent=s.rate.toFixed(2);$('sTime').textContent=fmtTime(s.elapsed);
  $('sTotal').textContent=s.total;
  const pct=s.total?Math.min(100,(s.generated/s.total)*100):0;
  $('bar').style.width=pct.toFixed(1)+'%';
  $('chipState').textContent=s.running?'GENERATING':(s.generated?'FINISHED':'IDLE');
  $('chipState').className='chip '+(s.running?'live':'');
  const tt=String(s.tor||'off').toUpperCase();$('chipTor').textContent='TOR '+tt;
  $('chipTor').className='chip '+(tt.includes('READY')?'live':(tt.includes('OFF')||tt.includes('UNAVAIL')?'dead':'warn'));
  $('chipNet').textContent='NET '+String(s.netmode||'free').toUpperCase()+(s.proxies?' · '+s.proxies+' LIVE':'');
  $('chipNet').className='chip '+(s.proxies>0?'live':'dead');
  $('chipRot').textContent=s.turbo?'⚡ TURBO ON':'ROT /'+(s.rotate_every||5)+' REQ';
  $('chipRot').className='chip '+(s.turbo?'turbo':'live');
  $('chipBuild').textContent='v'+s.build+' · '+s.devices+' DEV'+(s.android?' · 📱':'');
  $('btnPcount').textContent='LIVE: '+(s.proxies||0);
  $('btnFileCount').textContent='FILE: '+(s.ipfile||0);
  $('btnStart').disabled=s.running;$('btnStop').disabled=!s.running;
  if(lastIndex!==s.log_index){const l=await(await fetch('/api/logs?since='+since)).json();
    since=l.next;lastIndex=s.log_index;l.lines.forEach(addLog);}
  renderTable(s.rare_accounts);renderWorkers(s.workers);
}catch(e){}}

$('tgCouples').onclick=e=>e.currentTarget.classList.toggle('on');
$('tgHeavy').onclick=e=>e.currentTarget.classList.toggle('on');
$('tgTurbo').onclick=e=>e.currentTarget.classList.toggle('on');
$('engine').onchange=syncEngineUI;$('passmode').onchange=syncPassUI;
$('pass').oninput=previewPass;$('passvalue').oninput=previewPass;
$('btnPassPreview').onclick=previewPass;
$('btnPassReset').onclick=()=>{$('passmode').value='pattern';$('passvalue').value='';syncPassUI();};

function cmdLine(txt,cls){const box=$('cmdout');const d=document.createElement('div');
  d.className=cls||'';d.textContent=txt;box.appendChild(d);
  while(box.childNodes.length>400)box.removeChild(box.firstChild);box.scrollTop=box.scrollHeight;}
async function runCmd(cmd){cmd=(cmd||'').trim();if(!cmd)return;cmdLine('$ '+cmd,'c-in');
  try{const r=await(await fetch('/api/cmd',{method:'POST',
    headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd})})).json();
    (r.out||'').split('\n').forEach(l=>cmdLine(l,r.ok?'c-ok':'c-err'));
    if(!r.ok)cmdLine('[exit '+r.code+']','c-err');}catch(e){cmdLine('❌ '+e,'c-err');}}
$('btnRun').onclick=()=>{const i=$('cmdinput');runCmd(i.value);i.value='';};
$('cmdinput').addEventListener('keydown',e=>{if(e.key==='Enter'){runCmd(e.currentTarget.value);e.currentTarget.value='';}});

$('btnFree').onclick=async()=>{cmdLine('🔍 verifying live proxies (exit-IP check)...','c-sys');
  try{const r=await(await fetch('/api/proxies',{method:'POST'})).json();
    cmdLine('LIVE pool size: '+r.count,r.count?'c-ok':'c-err');
    $('btnPcount').textContent='LIVE: '+r.count;}catch(e){cmdLine('❌ '+e,'c-err');}};
$('btnReloadFile').onclick=async()=>{try{const r=await(await fetch('/api/proxies/file',{method:'POST'})).json();
  cmdLine('proxies.txt: '+r.count,r.count?'c-ok':'c-sys');
  $('btnFileCount').textContent='FILE: '+r.count;}catch(e){cmdLine('❌ '+e,'c-err');}};
$('btnTorRestart').onclick=async()=>{cmdLine('🔁 tor restart...','c-sys');
  await fetch('/api/tor/restart',{method:'POST'});toast('TOR RESTART');};
$('btnTorLog').onclick=async()=>{const r=await(await fetch('/api/tor/log')).json();
  cmdLine('tor state: '+r.state,'c-sys');r.lines.slice(-30).forEach(l=>cmdLine(l,'c-sys'));};

$('btnStart').onclick=async()=>{
  const body={engine:$('engine').value,region:$('region').value,
    total:parseInt($('total').value||'100',10),
    name:$('name').value||'NGRX',pass:$('pass').value||'NGRX',
    threads:parseInt($('threads').value||'20',10),
    threshold:parseInt($('threshold').value||'4',10),
    maxtries:parseInt($('maxtries').value||'4',10),
    nicklen:parseInt($('nicklen').value||'12',10),
    passmode:$('passmode').value,passvalue:$('passvalue').value||'',
    passtemplate:$('passvalue').value||'',
    couples:$('tgCouples').classList.contains('on'),
    heavy:$('tgHeavy').classList.contains('on'),
    turbo:$('tgTurbo').classList.contains('on'),
    netmode:$('netmode').value};
  const r=await(await fetch('/api/start',{method:'POST',
    headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})).json();
  if(!r.ok)toast('ERR: '+(r.error||'start failed'));
  else toast('STARTED · '+body.engine+' · '+body.region+' · '+body.total);};
$('btnStop').onclick=async()=>{await fetch('/api/stop',{method:'POST'});toast('STOPPING...');};
$('btnReset').onclick=async()=>{const r=await(await fetch('/api/reset',{method:'POST'})).json();
  if(r.ok){$('log').innerHTML='';$('cmdout').innerHTML='';since=0;lastIndex=-1;toast('RESET');}
  else toast('STOP FIRST');};
$('btnDl').onclick=()=>{window.location='/api/download';};
$('btnDlAll').onclick=()=>{window.location='/api/download/accounts';};
$('btnDlCouples').onclick=()=>{window.location='/api/download/couples';};

syncEngineUI();syncPassUI();setInterval(poll,900);poll();
</script>
</body>
</html>
"""

# ───────────────────────────── BOOT ─────────────────────────────

def _boot():
    global pRoXy_MoDe, uSe_tOr_PrOxY

    if _IS_ANDROID and pRoXy_MoDe == "tor":
        pRoXy_MoDe = "free"; uSe_tOr_PrOxY = False
        tOr_MgR.state = "skipped (android/vmos)"
        print("📱 Android/VMOS detected → Tor skipped · netmode = free")
    if not _SOCKS_OK and pRoXy_MoDe == "tor":
        pRoXy_MoDe = "free"; uSe_tOr_PrOxY = False
        tOr_MgR.state = "skipped (no pysocks)"
        print("⚠️ PySocks missing → Tor skipped · netmode = free")

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║  🔒  NGRAXX v3.1.0 · STRICT PROXY + TERMUX-SAFE  🔒      ║")
    print("║  DIRECT MODE DISABLED · EXIT-IP VERIFIED PROXIES         ║")
    print("╚══════════════════════════════════════════════════════════╝")
    sYnC_cOnFiG()

    if _IS_ANDROID:
        print("📱 Termux/Android: pool_maxsize shrunk, workers capped, poll() server")
        print("   Tip: run `ulimit -n 4096` in this shell before heavy jobs\n")

    if uSe_tOr_PrOxY and pRoXy_MoDe == "tor" and _SOCKS_OK:
        threading.Thread(target=tOr_MgR.start, daemon=True).start()

    print(f"\n{Fore.LIGHTGREEN_EX}{Style.BRIGHT}"
          f"🌐 NGRAXX v3.1 · {len(_dEvIcE_mOdElS)} devices · STRICT PROXY  →  "
          f"http://0.0.0.0:{WEB_PORT}{Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}   proxy sources: {len(fReE_pRoXy_SoUrCes)} verified GitHub URLs"
          f"{Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}   verification : TCP + HTTP + exit-IP diff"
          f"{Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}   direct mode  : DISABLED (proxy mandatory)"
          f"{Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}   min live     : {MIN_LIVE_PROXIES} proxies before start"
          f"{Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}   pool_maxsize : {POOL_MAXSIZE} · max_workers: {MAX_THREADS_HARD}"
          f"{Style.RESET_ALL}")
    print(f"{Fore.LIGHTBLACK_EX}   proxies.txt  : {len(IPRotator.PROXIES)} entries"
          f"{Style.RESET_ALL}\n")

def sYnC_cOnFiG():
    if SKIP_CONFIG_SYNC: return
    tOdAy = datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(cOnFiG_cAcHe_FiLe):
        try:
            with open(cOnFiG_cAcHe_FiLe, "r", encoding="utf-8") as f:
                cAcHeD = json.load(f)
            if cAcHeD.get("date") == tOdAy and isinstance(cAcHeD.get("config"), dict):
                return
        except Exception: pass

def _sErVe():
    """
    Termux-safe server bootstrap.
    - On Android: force Flask threaded (no select() FD limit).
    - Elsewhere: waitress with asyncore_use_poll=True (avoids select() limit).
    """
    if SERVE_BACKEND == "waitress" and not _IS_ANDROID:
        try:
            from waitress import serve
            print(f"{Fore.LIGHTBLACK_EX}   server       : waitress (poll, no FD limit){Style.RESET_ALL}\n")
            serve(app, host=WEB_HOST, port=WEB_PORT, threads=32,
                  channel_timeout=1800,
                  asyncore_use_poll=True,
                  connection_limit=100,
                  cleanup_interval=30)
            return
        except ImportError:
            pass
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ waitress failed ({e}) → flask fallback{Style.RESET_ALL}")

    print(f"{Fore.LIGHTBLACK_EX}   server       : flask threaded (Termux-safe){Style.RESET_ALL}\n")
    app.run(host=WEB_HOST, port=WEB_PORT, threaded=True, debug=False, use_reloader=False)

if __name__ == "__main__":
    _boot()
    _sErVe()