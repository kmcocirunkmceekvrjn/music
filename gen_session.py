#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_session.py  --  Session String Generator

این اسکریپت را روی کامپیوتر خودتان اجرا کنید، نه روی Railway.
چون برای وارد کردن شماره و کد تلگرام به ترمینال تعاملی نیاز دارد.

نصب پیش‌نیاز:
    pip install pyrogram==2.0.106 tgcrypto==1.2.5

اجرا:
    python3 gen_session.py

خروجی: یک رشته بلند که باید در Railway به عنوان CLI_SESSION ذخیره شود.
"""

import asyncio
import sys

try:
    from pyrogram import Client
except ImportError:
    print("[!] Pyrogram نصب نیست. اجرا کنید:")
    print("    pip install pyrogram==2.0.106 tgcrypto==1.2.5")
    sys.exit(1)


BANNER = """
==================================================
   Session String Generator  --  Music Player Bot
==================================================

نکته امنیتی: رشته سشن معادل دسترسی کامل به اکانت شماست.
هرگز آن را در گروه، گیت‌هاب یا جای عمومی قرار ندهید.
"""


async def main():
    print(BANNER)

    try:
        api_id = int(input("API_ID  (از my.telegram.org) : ").strip())
    except ValueError:
        print("[!] API_ID باید فقط عدد باشد.")
        sys.exit(1)

    api_hash = input("API_HASH (از my.telegram.org) : ").strip()
    if not api_hash:
        print("[!] API_HASH خالی است.")
        sys.exit(1)

    print("\n[*] در حال اتصال... شماره هلپر را با کد کشور وارد کنید (مثال: +989121234567)")
    print("[*] سپس کدی که تلگرام می‌فرستد را وارد کنید.\n")

    # in_memory=True یعنی هیچ فایل .session روی دیسک ساخته نمی‌شود
    async with Client(
        name="session_generator",
        api_id=api_id,
        api_hash=api_hash,
        in_memory=True,
        device_model="MusicPlayerHelper",
    ) as app:
        me = await app.get_me()
        session_string = await app.export_session_string()

        print("\n" + "=" * 50)
        print("[+] لاگین موفق: %s (@%s)" % (me.first_name, me.username or "no-username"))
        print("[+] User ID   : %s" % me.id)
        print("=" * 50)
        print("\nمقدار CLI_SESSION خود را کپی کنید (کل خط زیر):\n")
        print(session_string)
        print("\n" + "=" * 50)

        with open("cli_session.txt", "w", encoding="utf-8") as f:
            f.write(session_string)
        print("[+] در فایل cli_session.txt هم ذخیره شد.")
        print("[!] بعد از کپی کردن در Railway، این فایل را پاک کنید.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] لغو شد.")
