#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_for_railway.py

فایل main.py اصلی را برای اجرا در کانتینر (Railway / Docker) اصلاح می‌کند.

اجرا:
    python3 patch_for_railway.py main.py

خروجی:
    main.py            <- ویرایش‌شده
    main.py.bak        <- نسخه پشتیبان از فایل اصلی

تغییرات:
  1) API_ID / API_HASH / mersad / sudo / path85 از environment variables خوانده می‌شوند
  2) کلاینت ربات با bot_token و کلاینت هلپر با session_string لاگین می‌کنند (حذف input تعاملی)
  3) مسیر database.sqlite قابل تنظیم می‌شود تا روی Volume بنشیند
  4) تمام os.system('sudo fuser -k ...') حذف می‌شوند (در کانتینر sudo وجود ندارد)
  5) os.system('rm -rf downloads/*') با یک تابع ایمن پایتون جایگزین می‌شود
  6) os.system('rm ./*.jpg') و ('rm ./*.mp4') ایمن می‌شوند تا mersad.jpg و mersad.mp4 حذف نشوند
  7) youtube-dl -> yt-dlp
  8) اسکپ کوتیشن در کوئری‌های SQL متنی (کاهش SQL Injection)
"""

import re
import shutil
import sys
from pathlib import Path


HEADER_BLOCK = '''
# ==================== RAILWAY / DOCKER PATCH ====================
import os as _os


def _env_int(key, default=0):
    """خواندن متغیر محیطی عددی با مقدار پیش\u200cفرض."""
    raw = _os.environ.get(key, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        raise SystemExit(f"[!] متغیر {key} باید عدد باشد (مقدار فعلی: {raw!r})")


def _env_str(key, default="", required=False):
    """خواندن متغیر محیطی متنی."""
    val = _os.environ.get(key, default).strip()
    if required and not val:
        raise SystemExit(f"[!] متغیر محیطی {key} تنظیم نشده است.")
    return val


def sq(value):
    """اسکپ کردن کوتیشن برای درج در کوئری\u200cهای SQL متنی.

    راه\u200cحل اصولی parameterized query است، این فقط کاهش ریسک است.
    """
    if value is None:
        return ""
    return str(value).replace("\\\\", "\\\\\\\\").replace('"', '""').replace("'", "''")


def _safe_clear_downloads():
    """پاک\u200cسازی پوشه دانلودها بدون rm -rf."""
    import shutil as _shutil
    base = _os.environ.get("DOWNLOAD_PATH", "./downloads/")
    if not _os.path.isdir(base):
        return
    for entry in _os.listdir(base):
        target = _os.path.join(base, entry)
        try:
            if _os.path.isdir(target):
                _shutil.rmtree(target, ignore_errors=True)
            else:
                _os.remove(target)
        except OSError:
            pass


def _safe_clear_media(ext):
    """حذف فایل\u200cهای موقت با پسوند داده\u200cشده در پوشه جاری.

    فایل\u200cهای دارایی ربات (mersad.jpg / mersad.mp4) هرگز حذف نمی\u200cشوند.
    """
    protected = {"mersad.jpg", "mersad.mp4"}
    try:
        entries = _os.listdir(".")
    except OSError:
        return
    for entry in entries:
        if not entry.lower().endswith(ext):
            continue
        if entry in protected:
            continue
        if not _os.path.isfile(entry):
            continue
        try:
            _os.remove(entry)
        except OSError:
            pass


_BOT_TOKEN = _env_str("BOT_TOKEN", required=True)
_CLI_SESSION = _env_str("CLI_SESSION", required=True)
_DB_PATH = _env_str("DB_PATH", "./data/database.sqlite")
_os.makedirs(_os.path.dirname(_os.path.abspath(_DB_PATH)), exist_ok=True)
_os.makedirs(_env_str("DOWNLOAD_PATH", "./downloads/"), exist_ok=True)
# ================== END RAILWAY / DOCKER PATCH ==================
'''


def patch(source: str) -> tuple[str, list[str]]:
    log: list[str] = []
    original = source

    # ---- 1) تزریق بلوک کمکی قبل از تعریف mersad ----
    anchor = re.search(r"^mersad\s*=", source, flags=re.M)
    if anchor is None:
        raise SystemExit("[!] خط 'mersad = ...' پیدا نشد. فایل مورد انتظار نیست.")
    if "RAILWAY / DOCKER PATCH" in source:
        raise SystemExit("[!] این فایل قبلاً پچ شده است.")
    source = source[: anchor.start()] + HEADER_BLOCK + "\n" + source[anchor.start() :]
    log.append("بلوک توابع کمکی و خواندن env تزریق شد")

    # ---- 2) شناسه‌ها و مسیرها ----
    replacements = [
        (r"^mersad\s*=\s*\d+.*$", 'mersad = _env_int("OWNER_ID")'),
        (r"^sudo\s*=\s*\d+.*$", 'sudo = _env_int("SUDO_ID")'),
        (r"^path85\s*=\s*['\"][^'\"]*['\"].*$",
         'path85 = _env_str("DOWNLOAD_PATH", "./downloads/")'),
        (r"^API_ID\s*=\s*\d+.*$", 'API_ID = _env_int("API_ID")'),
        (r"^API_HASH\s*=\s*['\"][^'\"]*['\"].*$",
         'API_HASH = _env_str("API_HASH", required=True)'),
    ]
    for pattern, new in replacements:
        source, n = re.subn(pattern, new, source, count=1, flags=re.M)
        if n:
            log.append(f"جایگزین شد: {new}")
        else:
            log.append(f"[هشدار] الگو پیدا نشد: {pattern}")

    # ---- 3) حذف print تعاملی اولیه ----
    source, n = re.subn(
        r"^print\('Please Insert a Token First.*$",
        "print('[*] Starting in non-interactive mode (bot_token + session_string)')",
        source,
        count=1,
        flags=re.M,
    )
    if n:
        log.append("پیام لاگین تعاملی حذف شد")

    # ---- 4) کلاینت ربات: bot_token ----
    api_pattern = re.compile(
        r"api\s*=\s*Client\(\s*\n?\s*name\s*=\s*[\"']MusicPlayer[\"'],?\s*\n?"
        r"\s*api_id\s*=\s*API_ID,?\s*\n?\s*api_hash\s*=\s*API_HASH,?\s*\n?\s*\)",
        re.M,
    )
    api_new = (
        'api = Client(\n'
        '    name="MusicPlayer",\n'
        '    api_id=API_ID,\n'
        '    api_hash=API_HASH,\n'
        '    bot_token=_BOT_TOKEN,\n'
        '    in_memory=True,\n'
        ')'
    )
    source, n = api_pattern.subn(api_new, source, count=1)
    log.append(
        "کلاینت ربات به bot_token تغییر کرد" if n
        else "[هشدار] کلاینت api پیدا نشد — دستی اصلاح کنید"
    )

    # ---- 5) کلاینت هلپر: session_string ----
    cli_pattern = re.compile(
        r"cli\s*=\s*Client\(\s*\n?\s*name\s*=\s*[\"']Cli[\"'],?\s*\n?"
        r"\s*api_id\s*=\s*API_ID,?\s*\n?\s*api_hash\s*=\s*API_HASH,?\s*\n?"
        r"\s*device_model\s*=\s*[\"'][^\"']*[\"'],?\s*\n?\s*\)",
        re.M,
    )
    cli_new = (
        'cli = Client(\n'
        '    name="Cli",\n'
        '    api_id=API_ID,\n'
        '    api_hash=API_HASH,\n'
        '    session_string=_CLI_SESSION,\n'
        '    device_model=_env_str("DEVICE_MODEL", "MusicPlayerHelper"),\n'
        ')'
    )
    source, n = cli_pattern.subn(cli_new, source, count=1)
    log.append(
        "کلاینت هلپر به session_string تغییر کرد" if n
        else "[هشدار] کلاینت cli پیدا نشد — دستی اصلاح کنید"
    )

    # ---- 6) مسیر دیتابیس روی Volume ----
    source, n = re.subn(
        r"sqlite3\.connect\(\s*['\"]database\.sqlite['\"]\s*\)",
        "sqlite3.connect(_DB_PATH, check_same_thread=False)",
        source,
    )
    if n:
        log.append(f"مسیر دیتابیس قابل تنظیم شد ({n} مورد)")

    # ---- 7) حذف تمام fuser -k ----
    source, n = re.subn(
        r"os\.system\(\s*['\"](?:sudo\s+)?fuser\s+-k\s+[^'\"]*['\"]\s*\)",
        "pass  # patched: fuser/sudo not available in container",
        source,
    )
    log.append(f"{n} مورد fuser -k حذف شد")

    # ---- 8) rm -rf downloads ----
    source, n = re.subn(
        r"os\.system\(\s*['\"]rm\s+-rf\s+downloads/\*['\"]\s*\)",
        "_safe_clear_downloads()",
        source,
    )
    log.append(f"{n} مورد rm -rf با تابع ایمن جایگزین شد")

    # ---- 8b) rm ./*.jpg و rm ./*.mp4 — حفاظت از mersad.jpg / mersad.mp4 ----
    source, n = re.subn(
        r"os\.system\(\s*['\"]rm\s+\.?/?\*\.(jpg|jpeg|png|mp4)['\"]\s*\)",
        lambda m: f'_safe_clear_media(".{m.group(1)}")',
        source,
    )
    log.append(f"{n} مورد rm ./*.jpg|mp4 ایمن شد (حفاظت از mersad.jpg/mp4)")

    # ---- 9) youtube-dl -> yt-dlp ----
    source, n = re.subn(r"(['\"])youtube-dl\1", r"\1yt-dlp\1", source)
    log.append(f"{n} مورد youtube-dl به yt-dlp تغییر کرد")

    # ---- 10) کاهش SQL Injection در فیلدهای متنی ----
    sql_fixes = 0
    out_lines = []
    for line in source.split("\n"):
        if "cur.execute(f" in line and '="{' in line:
            new_line, cnt = re.subn(r'="\{(?!sq\()([^{}]+)\}"', r'="{sq(\1)}"', line)
            sql_fixes += cnt
            out_lines.append(new_line)
        else:
            out_lines.append(line)
    source = "\n".join(out_lines)
    log.append(f"{sql_fixes} کوئری SQL متنی اسکپ شد")

    if source == original:
        raise SystemExit("[!] هیچ تغییری اعمال نشد.")

    return source, log


def main() -> None:
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "main.py")
    if not target.is_file():
        raise SystemExit(f"[!] فایل پیدا نشد: {target}")

    source = target.read_text(encoding="utf-8", errors="surrogateescape")
    patched, log = patch(source)

    backup = target.with_suffix(target.suffix + ".bak")
    if not backup.exists():
        shutil.copy2(target, backup)
        print(f"[+] پشتیبان ساخته شد: {backup}")

    target.write_text(patched, encoding="utf-8", errors="surrogateescape")

    print("\n[خلاصه تغییرات]")
    for item in log:
        print(f"  - {item}")

    # بررسی سینتکس
    import py_compile
    try:
        py_compile.compile(str(target), doraise=True, cfile="/tmp/_chk.pyc")
        print("\n[+] بررسی سینتکس: سالم ✓")
    except py_compile.PyCompileError as exc:
        print(f"\n[!] خطای سینتکس پس از پچ:\n{exc}")
        print(f"[!] برای بازگردانی: cp {backup} {target}")
        sys.exit(1)


if __name__ == "__main__":
    main()
