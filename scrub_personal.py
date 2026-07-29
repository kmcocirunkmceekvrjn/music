#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
پاکسازی اطلاعات شخصی سازندهٔ اول از main.py

این اسکریپت را *بعد از* patch_for_railway.py اجرا کنید:

    python3 patch_for_railway.py main.py
    python3 scrub_personal.py main.py

چه کار می‌کند:
  1. import بی‌استفادهٔ `from ntpath import join` را حدف می‌کند
     (فقط اگر مطمئن شود هیچ join( در کد نیست)
  2. لینک کانال واقعی را به متغیر محیطی CHANNEL_LINK منتقل می‌کند
  3. دو شماره کارت بانکی و نام صاحب حساب را به متغیر محیطی منتقل می‌کند

متغیرهای جدید (در .env.example هم هستند):
  CHANNEL_LINK, CARD_NUMBER_1, CARD_NUMBER_2, CARD_HOLDER, BANK_NAME_1, BANK_NAME_2

اگر چیزی خراب شد:
    cp main.py.scrub.bak main.py
"""
import os
import py_compile
import re
import shutil
import sys

MARKER = "# ---- اطلاعات قابل شخصی‌سازی"
PATCH_END = "# ================== END RAILWAY / DOCKER PATCH =================="

ENV_BLOCK = '''

# ---- اطلاعات قابل شخصی‌سازی (از متغیر محیطی، با مقدار پیش‌فرض خنسی) ----
_CHANNEL_LINK = _env_str("CHANNEL_LINK", "https://t.me/your_channel_link")
_CARD_1 = _env_str("CARD_NUMBER_1", "0000-0000-0000-0000")
_CARD_2 = _env_str("CARD_NUMBER_2", "0000-0000-0000-0000")
_CARD_HOLDER = _env_str("CARD_HOLDER", "نام شما")
_BANK_1 = _env_str("BANK_NAME_1", "بانک شما")
_BANK_2 = _env_str("BANK_NAME_2", "بانک_شما")'''


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "main.py"
    if not os.path.exists(target):
        raise SystemExit(f"[!] فایل پیدا نشد: {target}")

    src = open(target, encoding="utf-8", errors="surrogateescape").read()

    if MARKER in src:
        raise SystemExit("[i] این فایل قبلاً پاکسازی شده — کاری لازم نیست")
    if PATCH_END not in src:
        raise SystemExit(
            "[!] اول patch_for_railway.py را اجرا کنید، بعد این اسکریپت را"
        )

    bak = target + ".scrub.bak"
    if not os.path.exists(bak):
        shutil.copy2(target, bak)
        print(f"[+] پشتیبان ساخته شد: {bak}")

    log = []

    # ---- 1) حدف import بی‌استفاده ----
    if "from ntpath import join\n" in src:
        if re.search(r"(?<![\w.])join\s*\(", src):
            log.append("ntpath دست نخورد (join( در کد استفاده شده)")
        else:
            src = src.replace("from ntpath import join\n", "", 1)
            log.append("import بی‌استفادهٔ ntpath حدف شد")

    # ---- 2) تزریق بلوک متغیرها ----
    src = src.replace(PATCH_END, PATCH_END + ENV_BLOCK, 1)
    log.append("بلوک متغیرهای شخصی‌سازی تزریق شد")

    # ---- 3) لینک کانال ----
    n = len(re.findall(r"kirsag\s*=\s*'https://t\.me/[^']*'", src))
    src = re.sub(r"kirsag\s*=\s*'https://t\.me/[^']*'", "kirsag = _CHANNEL_LINK", src)
    log.append(f"لینک کانال به env منتقل شد ({n} مورد)")

    # ---- 4) کارت‌های بانکی — خط‌به‌خط ----
    lines = src.split("\n")
    cards = 0
    for i, ln in enumerate(lines):
        digits = re.findall(r"\b\d{16}\b", ln)
        if not digits or "m.reply(" not in ln:
            continue
        new = ln
        # تبدیل به f-string
        new = new.replace('m.reply("', 'm.reply(f"', 1)
        # نام بانک لاتین (مانند **My sepah Bank :**)
        new = re.sub(r"\*\*My [A-Za-z ]*Bank :\*\*", "**{_BANK_1} :**", new)
        # هشتگ نام بانک فارسی
        new = re.sub(r"#بانک_[^\\ ]+", "#{_BANK_2}", new)
        # نام صاحب حساب: هر چه بین "به نام :" و ایموجی/خط بعدی
        new = re.sub(r"(به نام : )[^\\\U0001f500-\U0001f9ff]*",
                     r"\1{_CARD_HOLDER} ", new)
        # شماره‌های کارت
        for d in digits:
            cards += 1
            new = new.replace(d, "{_CARD_%d}" % (1 if cards == 1 else 2))
        lines[i] = new
    src = "\n".join(lines)
    log.append(f"{cards} شماره کارت بانکی و نام صاحب حساب پاک شد")

    open(target, "w", encoding="utf-8", errors="surrogateescape").write(src)

    print("[خلاصه تغییرات]")
    for item in log:
        print("  -", item)

    try:
        py_compile.compile(target, doraise=True, cfile="/tmp/_scrub_chk.pyc")
        print("[+] بررسی سینتکس: سالم ✓")
    except py_compile.PyCompileError as e:
        print("[!] خطای سینتکس — بازگردانی کنید:")
        print(f"    cp {bak} {target}")
        raise SystemExit(str(e))


if __name__ == "__main__":
    main()
