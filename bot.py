# -*- coding: utf-8 -*-
import asyncio
import json
import os
import re
import time
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions

# ----------------- কনফিগারেশন ও ডেটা সংরক্ষণ -----------------
BOT_TOKEN = "8879708023:AAHXoRntXfHB0PqkTbMbBiQ3ZE8raib-N4o"
ADMIN_ID = 1958884768
TARGET_GROUP_ID = None
DATA_FILE = "bot_data.json"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ডিফল্ট কনফিগারেশন
default_config = {
    "mode": "join_request",  # "join_request" অথবা "ad_link"
    "target_channel": "@romantic_video900",
    "target_channel_link": "https://t.me/romantic_video900",
    "ad_link": "https://google.com",
    "ad_wait_seconds": 15,
    "require_verification": True,     # লিংক শেয়ারে ভেরিফিকেশন অন/অফ
    "allow_only_tg_links": True,      # শুধুমাত্র টেলিগ্রাম লিংক অনুমোদন
    "delete_non_links": True,         # লিংক ছাড়া সাধারণ চ্যাট অটো ডিলিট
    "welcome_enabled": True,          # ওয়েলকাম মেসেজ অন/অফ
    "welcome_text": "👋 স্বাগতম {name}!\nআমাদের এই গ্রুপে শুধুমাত্র টেলিগ্রাম লিংক শেয়ার করতে পারবেন।",
    "clean_service_msgs": True,       # Join/Left সার্ভিস মেসেজ ডিলিট অন/অফ
    "promo_enabled": True,            # প্রোমো অটো ব্রডকাস্ট অন/অফ
    "promo_text": "🔥 সেরা টেলিগ্রাম কনটেন্টের জন্য আমাদের মেইন চ্যানেলে জয়েন করুন!",
    "promo_btn_text": "🚀 চ্যানেলে জয়েন করুন",
    "promo_btn_link": "https://t.me/romantic_video900",
    "broadcast_interval": 3600,       # প্রতি ১ ঘণ্টায় প্রোমো
    "current_version": 1,
    "target_group_id": None           # সংরক্ষিত গ্রুপ আইডি
}

# চব্বিশ ঘণ্টা অটো-শাটডাউন ও ৫ ঘণ্টা রিনিউয়াল সিস্টেম স্টেট
default_shutdown_state = {
    "is_shutdown": False,             # গ্রুপ বন্ধ কি না
    "active_expiry": time.time() + (24 * 3600), # কখন ২৪ ঘণ্টা শেষ হয়ে বন্ধ হবে
    "last_renew_time": time.time(),   # সর্বশেষ কখন কনফার্ম/রিনিউ করা হয়েছিল
    "last_prompt_time": time.time(),  # সর্বশেষ কখন ইনবক্সে রিনিউ প্রম্পট পাঠানো হয়েছে
    "prompt_count": 0,                # মোট কতবার প্রম্পট পাঠানো হয়েছে
    "shutdown_timestamp": 0           # কখন বন্ধ হয়েছিল
}

config = default_config.copy()
shutdown_state = default_shutdown_state.copy()
verified_users = {}      # {str(user_id): {"version": int, "time": float, "name": str, "username": str}}
all_known_users = {}     # {str(user_id): {"name": str, "username": str, "joined_at": float, "links_shared": int}}
admin_input_state = {}   # {user_id: {"action": str, "step": str}}
GROUP_MESSAGES = {}      # {chat_id: [(msg_id, timestamp)]}

def load_data():
    global config, shutdown_state, verified_users, all_known_users, TARGET_GROUP_ID
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                config.update(data.get("config", {}))
                shutdown_state.update(data.get("shutdown_state", {}))
                verified_users = data.get("verified_users", {})
                all_known_users = data.get("all_known_users", {})
                if config.get("target_group_id"):
                    TARGET_GROUP_ID = config["target_group_id"]
        except Exception as e:
            print("Error loading data:", e)

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "config": config,
                "shutdown_state": shutdown_state,
                "verified_users": verified_users,
                "all_known_users": all_known_users
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Error saving data:", e)

load_data()

# ----------------- হেল্পার ফাংশনসমূহ -----------------
async def auto_delete(msg: types.Message, delay: int = 15):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass

def record_msg(chat_id: int, msg_id: int):
    if chat_id not in GROUP_MESSAGES:
        GROUP_MESSAGES[chat_id] = []
    GROUP_MESSAGES[chat_id].append((msg_id, time.time()))
    cutoff = time.time() - (48 * 3600)
    GROUP_MESSAGES[chat_id] = [m for m in GROUP_MESSAGES[chat_id] if m[1] >= cutoff]

def track_user(user: types.User):
    uid = str(user.id)
    if uid not in all_known_users:
        all_known_users[uid] = {
            "name": user.full_name or user.first_name,
            "username": f"@{user.username}" if user.username else "নেই",
            "first_seen": time.time(),
            "links_shared": 0
        }
    else:
        all_known_users[uid]["name"] = user.full_name or user.first_name
        if user.username:
            all_known_users[uid]["username"] = f"@{user.username}"

def format_time_remaining(seconds: float) -> str:
    if seconds <= 0:
        return "০ মিনিট"
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    if hrs > 0:
        return f"{hrs} ঘণ্টা {mins} মিনিট"
    return f"{mins} মিনিট"

# লিংক ডিটেকশন রেজেক্স
TG_LINK_REGEX = re.compile(
    r'(https?:\/\/)?([a-zA-Z0-9-]+\.)*(t\.me|telegram\.me|telegram\.dog)\/[a-zA-Z0-9_+/?=&#%-]+',
    re.IGNORECASE
)
ANY_LINK_REGEX = re.compile(
    r'(https?:\/\/|www\.)[a-zA-Z0-9_\-\.]+\.[a-zA-Z]{2,}(\/[a-zA-Z0-9_+/?=&#%-]*)?',
    re.IGNORECASE
)

# ==================== ১. গ্রুপ শাটডাউন ও আনলক মেকানিজম ====================

async def apply_group_lock(chat_id: int):
    """গ্রুপের সকল মেম্বারের পারমিশন সম্পূর্ণ অফ করে ডেড মোডে নিয়ে যায়"""
    try:
        locked_perms = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )
        await bot.set_chat_permissions(chat_id=chat_id, permissions=locked_perms)
        print(f"Group {chat_id} successfully locked/shutdown via API!")
    except Exception as e:
        print(f"Error locking group permissions: {e}")

async def apply_group_unlock(chat_id: int):
    """গ্রুপের মেম্বারদের পারমিশন স্বাভাবিক করে পুনরায় চালু করে"""
    try:
        unlocked_perms = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_invite_users=True
        )
        await bot.set_chat_permissions(chat_id=chat_id, permissions=unlocked_perms)
        print(f"Group {chat_id} successfully unlocked via API!")
    except Exception as e:
        print(f"Error unlocking group permissions: {e}")

async def trigger_group_shutdown(source="timer"):
    """গ্রুপ শাটডাউন কার্যকর করে"""
    global shutdown_state, TARGET_GROUP_ID
    shutdown_state["is_shutdown"] = True
    shutdown_state["shutdown_timestamp"] = time.time()
    save_data()

    gid = TARGET_GROUP_ID or config.get("target_group_id")
    if gid:
        await apply_group_lock(gid)
        try:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👑 অ্যাডমিন প্যানেল", url=f"https://t.me/{(await bot.get_me()).username}")]
            ])
            lock_msg = await bot.send_message(
                chat_id=gid,
                text="⛔ **গ্রুপ সাময়িকভাবে শাটডাউন ও স্থগিত করা হয়েছে!**\n"
                     "━━━━━━━━━━━━━━━━━━━━\n"
                     "নির্ধারিত ২৪ ঘণ্টার মেয়াদ শেষ হয়েছে অথবা অ্যাডমিন কর্তৃক গ্রুপ অফ করা হয়েছে। "
                     "বর্তমানে কোনো সাধারণ সদস্য মেসেজ বা লিংক পাঠাতে পারবেন না। "
                     "অ্যাডমিন কনফার্মেশন ও রিনিউ করলে গ্রুপ পুনরায় চালু হবে।",
                parse_mode="Markdown",
                reply_markup=kb
            )
            record_msg(gid, lock_msg.message_id)
        except Exception as e:
            print("Error notifying group shutdown:", e)

    # অ্যাডমিনের ইনবক্সে আর্জেন্ট নোটিশ পাঠানো
    try:
        kb_renew = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ গ্রুপ পুনরায় চালু করুন (২৪ ঘণ্টা)", callback_data="renew_confirm")],
            [InlineKeyboardButton(text="👑 অ্যাডমিন প্যানেল", callback_data="br_main")]
        ])
        await bot.send_message(
            chat_id=ADMIN_ID,
            text="🚨 **সতর্কতা: গ্রুপ সম্পূর্ণ শাটডাউন হয়ে গেছে!**\n"
                 "━━━━━━━━━━━━━━━━━━━━\n"
                 "আপনার অনুমোদিত ২৪ ঘণ্টার সময়সীমা শেষ হওয়ায় গ্রুপটির সমস্ত মেসেজ ও লিংক কার্যক্রম স্থগিত (Dead Mode) করা হয়েছে।\n\n"
                 "গ্রুপ ও বটের কার্যক্রম এখনই পুনরায় সচল করতে নিচের **'গ্রুপ পুনরায় চালু করুন'** বাটনে চাপ দিন:",
            parse_mode="Markdown",
            reply_markup=kb_renew
        )
    except Exception as e:
        print("Error notifying admin about shutdown:", e)

async def trigger_group_revive():
    """গ্রুপ পুনরায় সচল করে ২৪ ঘণ্টা নতুন লাইফটাইম শুরু করে"""
    global shutdown_state, TARGET_GROUP_ID
    now = time.time()
    shutdown_state["is_shutdown"] = False
    shutdown_state["active_expiry"] = now + (24 * 3600)
    shutdown_state["last_renew_time"] = now
    shutdown_state["last_prompt_time"] = now
    save_data()

    gid = TARGET_GROUP_ID or config.get("target_group_id")
    if gid:
        await apply_group_unlock(gid)
        try:
            unlock_msg = await bot.send_message(
                chat_id=gid,
                text="🟢 **গ্রুপ ও বট সার্ভিস পুনরায় সফলভাবে চালু করা হয়েছে!**\n"
                     "মেম্বাররা এখন আগের নিয়ম অনুযায়ী লিংক শেয়ার করতে পারবেন।",
                parse_mode="Markdown"
            )
            record_msg(gid, unlock_msg.message_id)
            asyncio.create_task(auto_delete(unlock_msg, 30))
        except Exception as e:
            print("Error notifying group revival:", e)

# ==================== ২. কমান্ড হ্যান্ডলারস ====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    track_user(message.from_user)
    if message.chat.type == "private":
        if message.from_user.id == ADMIN_ID:
            await cmd_admin_main(message)
        else:
            await message.reply(
                "👋 স্বাগতম! আমি গ্রুপ লিংক ফিল্টারিং ও ম্যানেজমেন্ট বট।\n\n"
                "📌 আপনি আমাদের গ্রুপে গিয়ে শুধুমাত্র অনুমোদিত টেলিগ্রাম লিংক শেয়ার করতে পারবেন।",
                parse_mode="Markdown"
            )
    else:
        record_msg(message.chat.id, message.message_id)
        w = await message.reply(
            "👋 বট সক্রিয় ও চালু রয়েছে! সকল কমান্ড দেখতে লিখুন: `/help`",
            parse_mode="Markdown"
        )
        asyncio.create_task(auto_delete(w, 15))

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    track_user(message.from_user)
    record_msg(message.chat.id, message.message_id)

    help_text = (
        "📖 *বটের সমস্ত কমান্ড ও পূর্ণ নির্দেশিকা তালিকা:*\n\n"
        "👑 *অ্যাডমিন কমান্ডসমূহ (ইনবক্স / গ্রুপ):*\n"
        "▫️ `/admin` বা `/panel` - পূর্ণাঙ্গ কন্ট্রোল প্যানেল (ইনবক্সে বোতাম ভিত্তিক মেনু)\n"
        "▫️ `/renew` - গ্রুপ লাইফটাইম চব্বিশ ঘণ্টার জন্য তাৎক্ষণিক রিনিউ করুন\n"
        "▫️ `/clean` - গ্রুপে কত ঘণ্টার চ্যাট ডিলিট করবেন তার বাটন মেনু আসবে\n"
        "▫️ `/clean <ঘণ্টা>` - সরাসরি নির্দিষ্ট ঘণ্টার মেসেজ সাফ করুন (যেমন: `/clean 2`)\n"
        "▫️ `/myid` - আপনার টেলিগ্রাম ইউজার আইডি ও স্ট্যাটাস প্রদর্শন\n\n"
        "⚙️ *ইনস্ট্যান্ট সেটিংস কমান্ড (শর্টকাট):*\n"
        "▫️ `/setchannel <@username>` - টার্গেট চ্যানেল পরিবর্তন\n"
        "▫️ `/setlink <url>` - চ্যানেলের জয়েন রিকোয়েস্ট লিংক সেট\n"
        "▫️ `/setad <url>` - অ্যাড ওয়েবসাইটের লিংক পরিবর্তন\n"
        "▫️ `/setwait <সেকেন্ড>` - অ্যাড দেখার অপেক্ষার সময় সেট\n\n"
        "🛡️ *বটের বিশেষ অটো-সিকিউরিটি ফিচার:*\n"
        "1️⃣ **২৪ ঘণ্টা অটো শাটডাউন:** প্রতি ২৪ ঘণ্টা পর পর বট ও গ্রুপ স্বয়ংক্রিয়ভাবে লক হয়ে যাবে যদি না আপনি রিনিউ করেন।\n"
        "2️⃣ **৫ ঘণ্টা রিনিউ নোটিশ:** প্রতি ৫ ঘণ্টা পর পর অ্যাডমিনের ইনবক্সে রিনিউ করার কনফার্ম ও বাতিল বোতাম আসবে।\n"
        "3️⃣ **স্মার্ট লাইফটাইম ট্র্যাকিং:** কনফার্ম করলে ওই মুহূর্ত থেকে আবার ২৪ ঘণ্টা যোগ হবে, বাতিল করলে পূর্বের অবশিষ্ট সময় চালু থাকবে।"
    )
    m = await message.reply(help_text, parse_mode="Markdown")
    if message.chat.type != "private":
        asyncio.create_task(auto_delete(m, 45))

@dp.message(Command("renew"))
async def cmd_renew_direct(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await trigger_group_revive()
    await message.reply(
        "✅ **সফলভাবে রিনিউ সম্পন্ন হয়েছে!**\n"
        f"এখন থেকে পরবর্তী ২৪ ঘণ্টা গ্রুপটি সক্রিয় থাকবে।\n"
        f"⏳ বর্তমান মেয়াদ শেষ হবে: {time.strftime('%I:%M %p, %d %b', time.localtime(shutdown_state['active_expiry']))}",
        parse_mode="Markdown"
    )

@dp.message(Command("myid"))
async def cmd_myid(message: types.Message):
    track_user(message.from_user)
    record_msg(message.chat.id, message.message_id)
    is_adm = (message.from_user.id == ADMIN_ID)
    res = await message.reply(
        f"🆔 *ইউজার তথ্য:*\n\n"
        f"• আপনার নাম: `{message.from_user.full_name}`\n"
        f"• আপনার আইডি: `{message.from_user.id}`\n"
        f"• ভূমিকা: `{'👑 মূল অ্যাডমিন (Owner)' if is_adm else '👤 সাধারণ সদস্য'}`\n"
        f"• ভেরিফিকেশন স্ট্যাটাস: `{'✅ ভেরিফাইড' if str(message.from_user.id) in verified_users else '❌ নন-ভেরিফাইড'}`",
        parse_mode="Markdown"
    )
    if message.chat.type != "private":
        asyncio.create_task(auto_delete(res, 20))

# ==================== ৩. ক্লিনআপ কমান্ড ====================

@dp.message(Command("clean"))
async def cmd_clean(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        w = await message.reply("❌ এটি শুধুমাত্র অ্যাডমিনের জন্য অনুমোদিত!")
        asyncio.create_task(auto_delete(w, 10))
        return

    record_msg(message.chat.id, message.message_id)
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        hours = int(args[1])
        await run_bulk_clean(message.chat.id, hours, message)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏱️ ১ ঘণ্টা", callback_data="clean_1"),
            InlineKeyboardButton(text="⏱️ ২ ঘণ্টা", callback_data="clean_2"),
            InlineKeyboardButton(text="⏱️ ৬ ঘণ্টা", callback_data="clean_6")
        ],
        [
            InlineKeyboardButton(text="⏱️ ১২ ঘণ্টা", callback_data="clean_12"),
            InlineKeyboardButton(text="⏱️ ২৪ ঘণ্টা", callback_data="clean_24"),
            InlineKeyboardButton(text="⏱️ ৪৮ ঘণ্টা", callback_data="clean_48")
        ],
        [InlineKeyboardButton(text="❌ মেনু বন্ধ করুন", callback_data="clean_cancel")]
    ])
    prompt = await message.reply(
        "🗑️ *গ্রুপ মেসেজ ক্লিনআপ মেনু:*\n\n"
        "কত ঘণ্টার মেসেজ মুছে ফেলতে চান নিচের বোতামে চাপুন, অথবা সরাসরি লিখুন: `/clean <ঘণ্টা>` (যেমন: `/clean 3`)",
        parse_mode="Markdown",
        reply_markup=kb
    )
    asyncio.create_task(auto_delete(message, 15))
    asyncio.create_task(auto_delete(prompt, 60))

@dp.callback_query(F.data.startswith("clean_"))
async def callback_clean(query: types.CallbackQuery):
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ শুধুমাত্র অ্যাডমিন এটি করতে পারেন!", show_alert=True)
        return

    if query.data == "clean_cancel":
        await query.message.delete()
        return

    hours = int(query.data.split("_")[1])
    await query.answer(f"🧹 গত {hours} ঘণ্টার চ্যাট মোছা হচ্ছে...", show_alert=False)
    await run_bulk_clean(query.message.chat.id, hours, query.message)

async def run_bulk_clean(chat_id: int, hours: int, trigger_msg: types.Message):
    now = time.time()
    cutoff = now - (hours * 3600)
    current_mid = trigger_msg.message_id

    to_delete = set()
    for mid, ts in GROUP_MESSAGES.get(chat_id, []):
        if ts >= cutoff:
            to_delete.add(mid)

    estimated_span = min(hours * 180, 1200)
    for mid in range(current_mid, max(1, current_mid - estimated_span), -1):
        to_delete.add(mid)

    count = 0
    for mid in to_delete:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=mid)
            count += 1
            await asyncio.sleep(0.03)
        except Exception:
            pass

    if chat_id in GROUP_MESSAGES:
        GROUP_MESSAGES[chat_id] = [m for m in GROUP_MESSAGES[chat_id] if m[1] < cutoff]

    done_msg = await bot.send_message(
        chat_id=chat_id,
        text=f"✅ *সাফাই সম্পন্ন!* গত *{hours} ঘণ্টার* মোট *{count}টি* মেসেজ মুছে দেওয়া হয়েছে।",
        parse_mode="Markdown"
    )
    asyncio.create_task(auto_delete(done_msg, 15))

# ==================== ৪. অ্যাডমিন কন্ট্রোল প্যানেল (A to Z শাখা-প্রশাখা) ====================

@dp.message(Command("admin"))
@dp.message(Command("panel"))
async def cmd_admin_main(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        if message.chat.type != "private":
            w = await message.reply("❌ এটি শুধুমাত্র অ্যাডমিনের জন্য অনুমোদিত!")
            asyncio.create_task(auto_delete(w, 10))
        return

    if message.chat.type != "private":
        try:
            bot_info = await bot.get_me()
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📬 ইনবক্সে কন্ট্রোল প্যানেল খুলুন", url=f"https://t.me/{bot_info.username}?start=admin")]
            ])
            w = await message.reply("👑 নিরাপত্তার স্বার্থে অ্যাডমিন প্যানেল ইনবক্সে ওপেন করুন:", reply_markup=kb)
            asyncio.create_task(auto_delete(message, 15))
            asyncio.create_task(auto_delete(w, 30))
            return
        except Exception:
            pass

    text, kb = build_admin_main_view()
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

def build_admin_main_view():
    now = time.time()
    rem_sec = max(0, shutdown_state["active_expiry"] - now)
    rem_str = format_time_remaining(rem_sec)

    status_badge = "🔴 শাটডাউন (বন্ধ)" if shutdown_state["is_shutdown"] else f"🟢 সক্রিয় ({rem_str} বাকি)"

    text = (
        "👑 **পাগলা বাবা বট — মূল অ্যাডমিন কন্ট্রোল প্যানেল**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ **গ্রুপ স্ট্যাটাস:** `{status_badge}`\n"
        f"🔹 **বর্তমান মোড:** `{config['mode']}`\n"
        f"🔹 **টার্গেট চ্যানেল:** `{config['target_channel']}`\n"
        f"🔹 **ভেরিফিকেশন ফিল্টার:** `{'🟢 চালু (ON)' if config['require_verification'] else '🔴 বন্ধ (OFF)'}`\n"
        f"🔹 **নন-টেলিগ্রাম লিংক ডিলিট:** `{'🟢 চালু (ON)' if config['allow_only_tg_links'] else '🔴 বন্ধ (OFF)'}`\n"
        f"🔹 **সাধারণ মেসেজ ডিলিট:** `{'🟢 চালু (ON)' if config['delete_non_links'] else '🔴 বন্ধ (OFF)'}`\n"
        f"🔹 **মোট মেম্বার:** `{len(all_known_users)} জন` | **ভেরিফাইড:** `{len(verified_users)} জন`\n\n"
        "👇 _যেকোনো শাখার বিস্তারিত দেখতে নিচের বোতামে চাপুন:_"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏱️ ২৪ ঘণ্টা শাটডাউন শাখা", callback_data="br_shutdown"),
            InlineKeyboardButton(text="🎯 চ্যানেল ও রিকোয়েস্ট শাখা", callback_data="br_channel")
        ],
        [
            InlineKeyboardButton(text="🌐 ডাইরেক্ট অ্যাড লিংক শাখা", callback_data="br_ad"),
            InlineKeyboardButton(text="🛡️ লিংক ফিল্টারিং শাখা (ON/OFF)", callback_data="br_filters")
        ],
        [
            InlineKeyboardButton(text="💬 ওয়েলকাম ও মেসেজ শাখা", callback_data="br_welcome"),
            InlineKeyboardButton(text="📢 অটো প্রোমোশন শাখা", callback_data="br_promo")
        ],
        [
            InlineKeyboardButton(text="👥 ইউজার ও ভেরিফিকেশন লিস্ট", callback_data="br_users"),
            InlineKeyboardButton(text="🔄 মোড পরিবর্তন (Toggle)", callback_data="act_toggle_mode")
        ],
        [
            InlineKeyboardButton(text="♻️ রিসেট অল ভেরিফিকেশন", callback_data="act_reset_verifications"),
            InlineKeyboardButton(text="❌ প্যানেল বন্ধ করুন", callback_data="act_close_panel")
        ]
    ])
    return text, kb

# ==================== ৫. শাখা ভিত্তিক নেভিগেশন ও বাটন হ্যান্ডলার ====================

@dp.callback_query(F.data.startswith("br_"))
@dp.callback_query(F.data.startswith("act_"))
@dp.callback_query(F.data.startswith("tog_"))
@dp.callback_query(F.data.startswith("edit_"))
@dp.callback_query(F.data.startswith("renew_"))
async def handle_admin_branches(query: types.CallbackQuery):
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ আপনি এই বটের অ্যাডমিন নন!", show_alert=True)
        return

    data = query.data

    # --- ৫.১ রিনিউয়াল বোতাম হ্যান্ডলার (কনফার্ম ও বাতিল) ---
    if data == "renew_confirm":
        await trigger_group_revive()
        await query.answer("✅ সফল! এখন থেকে নতুন করে চব্বিশ (২৪) ঘণ্টা সময় শুরু হলো।", show_alert=True)
        try:
            await query.message.edit_text(
                "✅ **গ্রুপ সফলভাবে রিনিউ করা হয়েছে!**\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "এই মুহূর্ত থেকে পরবর্তী ২৪ ঘণ্টার জন্য গ্রুপ ও বট পুরোদমে সচল থাকবে।\n"
                f"⏳ মেয়াদ শেষ হবে: {time.strftime('%I:%M %p, %d %b %Y', time.localtime(shutdown_state['active_expiry']))}",
                parse_mode="Markdown"
            )
        except Exception:
            pass
        return

    elif data == "renew_cancel":
        now = time.time()
        rem_sec = max(0, shutdown_state["active_expiry"] - now)
        rem_str = format_time_remaining(rem_sec)
        await query.answer(f"বাতিল করা হয়েছে। পূর্বের অনুমোদিত সময় থেকে আরও {rem_str} গ্রুপ চালু থাকবে।", show_alert=True)
        try:
            await query.message.edit_text(
                f"❌ **রিনিউ অনুরোধ বাতিল করা হয়েছে!**\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"পূর্বের সময় গণনা অব্যাহত থাকবে।\n"
                f"⏳ অবশিষ্ট সময়: `{rem_str}` পর গ্রুপ স্বয়ংক্রিয় শাটডাউন হবে।",
                parse_mode="Markdown"
            )
        except Exception:
            pass
        return

    # --- মূল মেনুতে ফেরা ---
    elif data == "br_main":
        text, kb = build_admin_main_view()
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        await query.answer()
        return

    # --- প্যানেল বন্ধ করা ---
    elif data == "act_close_panel":
        await query.message.delete()
        await query.answer("প্যানেল বন্ধ করা হয়েছে")
        return

    # --- ৫.২ চব্বিশ ঘণ্টা শাটডাউন শাখা ---
    elif data == "br_shutdown":
        now = time.time()
        rem_sec = max(0, shutdown_state["active_expiry"] - now)
        rem_str = format_time_remaining(rem_sec)
        status_txt = "🔴 বর্তমানে বন্ধ (Shutdown - Dead Mode)" if shutdown_state["is_shutdown"] else f"🟢 বর্তমানে চালু ({rem_str} বাকি)"

        text = (
            "⏱️ **২৪ ঘণ্টা অটো-শাটডাউন ও ৫ ঘণ্টা রিনিউ শাখা**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• বর্তমান অবস্থা: `{status_txt}`\n"
            f"• অবশিষ্ট সক্রিয় সময়: `{rem_str}`\n"
            f"• পরবর্তী নোটিফিকেশন: `প্রতি ৫ ঘণ্টা পর পর ইনবক্সে`\n"
            f"• লক্ষ্য গ্রুপ আইডি: `{TARGET_GROUP_ID or config.get('target_group_id') or 'অটোমেটিক ডিটেক্টেড'}`\n\n"
            "💡 *এই সিস্টেমটি কীভাবে কাজ করে?*\n"
            "১. প্রতি ৫ ঘণ্টা পর পর আপনার ইনবক্সে কনফার্মেশন মেসেজ আসবে।\n"
            "২. আপনি **'কনফার্ম করুন'** দিলে ওই মুহূর্ত থেকে ফ্রেশ ২৪ ঘণ্টা শুরু হবে।\n"
            "৩. **'বাতিল'** করলে পূর্বে যে ২৪ ঘণ্টা শুরু হয়েছিল, তার অবশিষ্ট সময় অনুযায়ী চলবে।\n"
            "৪. সময় শেষ হওয়ার পর আপনি সক্রিয় না থাকলে গ্রুপ **সম্পূর্ণ শাটডাউন** হয়ে যাবে (কেউ কোনো মেসেজ বা লিংক দিতে পারবে না)।\n\n"
            "নিচের বোতামগুলো দিয়ে এখনই নিয়ন্ত্রণ করতে পারেন:"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚡ এখনই রিনিউ করুন (২৪ ঘণ্টা)", callback_data="renew_confirm")],
            [InlineKeyboardButton(text="🛑 এখনই গ্রুপ শাটডাউন করুন", callback_data="act_force_shutdown")],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        await query.answer()

    elif data == "act_force_shutdown":
        await trigger_group_shutdown(source="admin_manual")
        await query.answer("🛑 গ্রুপ তাৎক্ষণিক শাটডাউন করা হয়েছে!", show_alert=True)
        text, kb = build_admin_main_view()
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        return

    # --- মোড সুইচ ---
    elif data == "act_toggle_mode":
        config["mode"] = "ad_link" if config["mode"] == "join_request" else "join_request"
        save_data()
        await query.answer(f"সফল! মোড এখন: {config['mode']}", show_alert=True)
        text, kb = build_admin_main_view()
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        return

    # --- সমস্ত ভেরিফিকেশন রিসেট ---
    elif data == "act_reset_verifications":
        config["current_version"] += 1
        verified_users.clear()
        save_data()
        await query.answer("♻️ সমস্ত ইউজারের ভেরিফিকেশন রিসেট করা হয়েছে!", show_alert=True)
        text, kb = build_admin_main_view()
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        return

    # --- চ্যানেল ও রিকোয়েস্ট শাখা ---
    elif data == "br_channel":
        text = (
            "🎯 **চ্যানেল ও জয়েন রিকোয়েস্ট শাখা**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• টার্গেট চ্যানেল ইউজারনেম: `{config['target_channel']}`\n"
            f"• চ্যানেল জয়েন রিকোয়েস্ট লিংক: `{config['target_channel_link']}`\n"
            f"• বর্তমান কার্যকারী মোড: `{config['mode']}`\n\n"
            "কী পরিবর্তন করতে চান নিচের বোতামে চাপুন:"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ চ্যানেল ইউজারনেম পরিবর্তন", callback_data="edit_channel_user")],
            [InlineKeyboardButton(text="✏️ চ্যানেল রিকোয়েস্ট লিংক পরিবর্তন", callback_data="edit_channel_link")],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        await query.answer()

    # --- ডাইরেক্ট অ্যাড শাখা ---
    elif data == "br_ad":
        text = (
            "🌐 **ডাইরেক্ট অ্যাড ও ট্রাফিক শাখা**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• অ্যাড ইউআরএল: `{config['ad_link']}`\n"
            f"• অপেক্ষার সময়: `{config['ad_wait_seconds']} সেকেন্ড`\n\n"
            "কী পরিবর্তন করতে চান:"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ অ্যাড লিংক পরিবর্তন", callback_data="edit_ad_link")],
            [InlineKeyboardButton(text="⏱️ ওয়েটিং টাইম পরিবর্তন", callback_data="edit_ad_wait")],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        await query.answer()

    # --- লিংক ফিল্টারিং শাখা (ON/OFF Switches) ---
    elif data == "br_filters":
        text = (
            "🛡️ **গ্রুপ লিংক ফিল্টারিং ও নিরাপত্তা শাখা**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"1️⃣ **ভেরিফিকেশন বাধ্যবাধকতা:** `{'🟢 চালু (ON)' if config['require_verification'] else '🔴 বন্ধ (OFF)'}`\n"
            f"2️⃣ **শুধুমাত্র টেলিগ্রাম লিংক অনুমোদন:** `{'🟢 চালু (ON)' if config['allow_only_tg_links'] else '🔴 বন্ধ (OFF)'}`\n"
            f"3️⃣ **নন-লিংক সাধারণ মেসেজ ডিলিট:** `{'🟢 চালু (ON)' if config['delete_non_links'] else '🔴 বন্ধ (OFF)'}`\n"
            f"4️⃣ **সার্ভিস মেসেজ ডিলিট (Joined/Left):** `{'🟢 চালু (ON)' if config['clean_service_msgs'] else '🔴 বন্ধ (OFF)'}`"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{'🔴 বন্ধ করুন' if config['require_verification'] else '🟢 চালু করুন'} (ভেরিফিকেশন)",
                callback_data="tog_verification"
            )],
            [InlineKeyboardButton(
                text=f"{'🔴 বন্ধ করুন' if config['allow_only_tg_links'] else '🟢 চালু করুন'} (অনলি টেলিগ্রাম লিংক)",
                callback_data="tog_only_tg"
            )],
            [InlineKeyboardButton(
                text=f"{'🔴 বন্ধ করুন' if config['delete_non_links'] else '🟢 চালু করুন'} (নন-লিংক টেক্সট ডিলিট)",
                callback_data="tog_delete_non_links"
            )],
            [InlineKeyboardButton(
                text=f"{'🔴 বন্ধ করুন' if config['clean_service_msgs'] else '🟢 চালু করুন'} (সার্ভিস নোটিশ ডিলিট)",
                callback_data="tog_clean_service"
            )],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        await query.answer()

    # --- ফিল্টার টগল হ্যান্ডলারসমূহ ---
    elif data == "tog_verification":
        config["require_verification"] = not config["require_verification"]
        save_data()
        await query.answer(f"ভেরিফিকেশন: {'চালু' if config['require_verification'] else 'বন্ধ'}")
        await handle_admin_branches(query)

    elif data == "tog_only_tg":
        config["allow_only_tg_links"] = not config["allow_only_tg_links"]
        save_data()
        await query.answer(f"শুধুমাত্র টেলিগ্রাম লিংক: {'চালু' if config['allow_only_tg_links'] else 'বন্ধ'}")
        await handle_admin_branches(query)

    elif data == "tog_delete_non_links":
        config["delete_non_links"] = not config["delete_non_links"]
        save_data()
        await query.answer(f"নন-লিংক ডিলিট: {'চালু' if config['delete_non_links'] else 'বন্ধ'}")
        await handle_admin_branches(query)

    elif data == "tog_clean_service":
        config["clean_service_msgs"] = not config["clean_service_msgs"]
        save_data()
        await query.answer(f"সার্ভিস মেসেজ ডিলিট: {'চালু' if config['clean_service_msgs'] else 'বন্ধ'}")
        await handle_admin_branches(query)

    # --- ওয়েলকাম মেসেজ শাখা ---
    elif data == "br_welcome":
        text = (
            "💬 **ওয়েলকাম মেসেজ শাখা**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• ওয়েলকাম নোটিফিকেশন: `{'🟢 চালু (ON)' if config['welcome_enabled'] else '🔴 বন্ধ (OFF)'}`\n\n"
            f"📝 **বর্তমান টেক্সট:**\n"
            f"_{config['welcome_text']}_\n\n"
            "💡 _(মেসেজে `{name}` লিখলে ইউজারের নাম স্বয়ংক্রিয়ভাবে বসে যাবে।)_"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{'🔴 ওয়েলকাম বন্ধ করুন' if config['welcome_enabled'] else '🟢 ওয়েলকাম চালু করুন'}",
                callback_data="tog_welcome"
            )],
            [InlineKeyboardButton(text="✏️ ওয়েলকাম টেক্সট পরিবর্তন করুন", callback_data="edit_welcome_text")],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        await query.answer()

    elif data == "tog_welcome":
        config["welcome_enabled"] = not config["welcome_enabled"]
        save_data()
        await query.answer(f"ওয়েলকাম: {'চালু' if config['welcome_enabled'] else 'বন্ধ'}")
        await handle_admin_branches(query)

    # --- অটো প্রোমোশন ব্রডকাস্ট শাখা ---
    elif data == "br_promo":
        text = (
            "📢 **অটো প্রোমোশন ও বিজ্ঞাপন শাখা**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• ব্রডকাস্ট স্ট্যাটাস: `{'🟢 চালু (ON)' if config['promo_enabled'] else '🔴 বন্ধ (OFF)'}`\n"
            f"• ব্যবধান: `প্রতি {int(config['broadcast_interval']/60)} মিনিট পর পর`\n"
            f"• বাটন নাম: `{config['promo_btn_text']}`\n"
            f"• বাটন লিংক: `{config['promo_btn_link']}`\n\n"
            f"📝 **বর্তমান বার্তা:**\n"
            f"_{config['promo_text']}_"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{'🔴 প্রোমো বন্ধ করুন' if config['promo_enabled'] else '🟢 প্রোমো চালু করুন'}",
                callback_data="tog_promo"
            )],
            [InlineKeyboardButton(text="✏️ প্রোমো মেসেজ পরিবর্তন", callback_data="edit_promo_text")],
            [InlineKeyboardButton(text="✏️ প্রোমো বাটন টেক্সট পরিবর্তন", callback_data="edit_promo_btn_text")],
            [InlineKeyboardButton(text="✏️ প্রোমো বাটন লিংক পরিবর্তন", callback_data="edit_promo_btn_link")],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        await query.answer()

    elif data == "tog_promo":
        config["promo_enabled"] = not config["promo_enabled"]
        save_data()
        await query.answer(f"প্রোমো: {'চালু' if config['promo_enabled'] else 'বন্ধ'}")
        await handle_admin_branches(query)

    # --- ইউজার ও ভেরিফিকেশন তালিকা শাখা ---
    elif data == "br_users":
        total_k = len(all_known_users)
        total_v = len(verified_users)

        recent_ver = []
        for uid, info in list(verified_users.items())[-6:]:
            u_name = info.get("name", "অজানা")
            u_uname = info.get("username", "")
            recent_ver.append(f"• `{uid}`: {u_name} ({u_uname})")

        ver_list_str = "\n".join(recent_ver) if recent_ver else "কোনো ভেরিফাইড ইউজার পাওয়া যায়নি।"

        text = (
            "👥 **ইউজার ও ভেরিফিকেশন তথ্য শাখা**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **মোট ট্র্যাকিং পরিসংখ্যান:**\n"
            f"• গ্রুপে সক্রিয় মোট পরিচিত সদস্য: `{total_k} জন`\n"
            f"• বর্তমানে ভেরিফাইড সদস্য: `{total_v} জন`\n"
            f"• বর্তমান সিকিউরিটি ভার্সন: `v{config['current_version']}`\n\n"
            f"📋 **সাম্প্রতিক ভেরিফাইড ইউজারদের তালিকা:**\n"
            f"{ver_list_str}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="♻️ সমস্ত ইউজার ভেরিফিকেশন বাতিল (Reset)", callback_data="act_reset_verifications")],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        await query.answer()

    # --- ইনপুট এডিটর প্রম্পটসমূহ ---
    elif data.startswith("edit_"):
        action = data.replace("edit_", "")
        admin_input_state[query.from_user.id] = {"action": action}

        prompts = {
            "channel_user": "✍️ দয়া করে চ্যানেলের নতুন ইউজারনেম লিখে পাঠান (যেমন: `@romantic_video900`):",
            "channel_link": "✍️ দয়া করে চ্যানেলের নতুন জয়েন রিকোয়েস্ট লিংক পাঠান (যেমন: `https://t.me/+AbCdEf...`):",
            "ad_link": "✍️ দয়া করে নতুন অ্যাড ওয়েবসাইটের লিংক লিখে পাঠান (যেমন: `https://example.com`):",
            "ad_wait": "✍️ দয়া করে মেম্বারদের জন্য অপেক্ষার সেকেন্ড লিখে পাঠান (যেমন: `15`):",
            "welcome_text": "✍️ নতুন ওয়েলকাম মেসেজটি লিখে পাঠান (মেম্বারের নাম আনতে চাইলে `{name}` ব্যবহার করুন):",
            "promo_text": "✍️ গ্রুপে প্রচার করার জন্য নতুন প্রোমো টেক্সটটি লিখে পাঠান:",
            "promo_btn_text": "✍️ প্রোমো বাটনের নাম লিখে পাঠান (যেমন: `🔥 জয়েন করুন`):",
            "promo_btn_link": "✍️ প্রোমো বাটনের লিংকটি লিখে পাঠান (যেমন: `https://t.me/...`):"
        }

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ বাতিল করুন", callback_data="cancel_input")]
        ])
        await query.message.answer(prompts.get(action, "দয়া করে মান লিখে পাঠান:"), parse_mode="Markdown", reply_markup=kb)
        await query.answer("ইনপুটের অপেক্ষায়...")

    elif data == "cancel_input":
        if query.from_user.id in admin_input_state:
            del admin_input_state[query.from_user.id]
        await query.message.delete()
        await query.answer("ইনপুট বাতিল করা হয়েছে")

# ==================== ৬. ইনবক্সে টেক্সট ইনপুট গ্রহণ ও সংরক্ষণ ====================

@dp.message(F.chat.type == "private")
async def handle_private_inputs(message: types.Message):
    track_user(message.from_user)
    if message.from_user.id != ADMIN_ID:
        return

    uid = message.from_user.id
    if uid not in admin_input_state:
        if not message.text.startswith("/"):
            await message.reply("💡 সেটিংস নিয়ন্ত্রণ করতে `/admin` অথবা `/panel` লিখুন।")
        return

    action = admin_input_state[uid]["action"]
    del admin_input_state[uid]
    text = (message.text or "").strip()

    if action == "channel_user":
        if not text.startswith("@") and not text.startswith("https://t.me/"):
            text = f"@{text}"
        config["target_channel"] = text
        save_data()
        await message.reply(f"✅ টার্গেট চ্যানেল সফলভাবে আপডেট হয়েছে: `{text}`", parse_mode="Markdown")

    elif action == "channel_link":
        config["target_channel_link"] = text
        save_data()
        await message.reply(f"✅ চ্যানেল রিকোয়েস্ট লিংক সফলভাবে আপডেট হয়েছে: `{text}`", parse_mode="Markdown")

    elif action == "ad_link":
        config["ad_link"] = text
        save_data()
        await message.reply(f"✅ অ্যাড লিংক সফলভাবে আপডেট হয়েছে: `{text}`", parse_mode="Markdown")

    elif action == "ad_wait":
        if text.isdigit():
            config["ad_wait_seconds"] = int(text)
            save_data()
            await message.reply(f"✅ অপেক্ষার সময় সেট হয়েছে: `{text} সেকেন্ড`", parse_mode="Markdown")
        else:
            await message.reply("❌ ভুল ইনপুট! শুধুমাত্র সংখ্যা লিখুন (যেমন: 15)।")

    elif action == "welcome_text":
        config["welcome_text"] = text
        save_data()
        await message.reply("✅ ওয়েলকাম বার্তা সফলভাবে পরিবর্তন করা হয়েছে!", parse_mode="Markdown")

    elif action == "promo_text":
        config["promo_text"] = text
        save_data()
        await message.reply("✅ প্রোমো বার্তা সফলভাবে আপডেট হয়েছে!", parse_mode="Markdown")

    elif action == "promo_btn_text":
        config["promo_btn_text"] = text
        save_data()
        await message.reply(f"✅ প্রোমো বাটনের নাম সেট হয়েছে: `{text}`", parse_mode="Markdown")

    elif action == "promo_btn_link":
        config["promo_btn_link"] = text
        save_data()
        await message.reply(f"✅ প্রোমো বাটনের লিংক সেট হয়েছে: `{text}`", parse_mode="Markdown")

    p_text, p_kb = build_admin_main_view()
    await message.answer(p_text, parse_mode="Markdown", reply_markup=p_kb)

# ==================== ৭. শর্টকাট কমান্ড হ্যান্ডলারস ====================

@dp.message(Command("setchannel"))
async def cmd_setchannel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) > 1:
        val = args[1]
        if not val.startswith("@") and not val.startswith("https://t.me/"):
            val = f"@{val}"
        config["target_channel"] = val
        save_data()
        m = await message.answer(f"✅ টার্গেট চ্যানেল সেট হয়েছে: `{val}`", parse_mode="Markdown")
        asyncio.create_task(auto_delete(message, 15))
        asyncio.create_task(auto_delete(m, 15))

@dp.message(Command("setlink"))
async def cmd_setlink(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) > 1:
        config["target_channel_link"] = args[1]
        save_data()
        m = await message.answer(f"✅ চ্যানেল রিকোয়েস্ট লিংক সেট হয়েছে: `{args[1]}`", parse_mode="Markdown")
        asyncio.create_task(auto_delete(message, 15))
        asyncio.create_task(auto_delete(m, 15))

@dp.message(Command("setad"))
async def cmd_setad(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) > 1:
        config["ad_link"] = args[1]
        save_data()
        m = await message.answer(f"✅ ডাইরেক্ট অ্যাড লিংক সেট হয়েছে: `{args[1]}`", parse_mode="Markdown")
        asyncio.create_task(auto_delete(message, 15))
        asyncio.create_task(auto_delete(m, 15))

@dp.message(Command("setwait"))
async def cmd_setwait(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        config["ad_wait_seconds"] = int(args[1])
        save_data()
        m = await message.answer(f"✅ অ্যাড ওয়েট টাইম সেট হয়েছে: `{args[1]} সেকেন্ড`", parse_mode="Markdown")
        asyncio.create_task(auto_delete(message, 15))
        asyncio.create_task(auto_delete(m, 15))

# ==================== ৮. সার্ভিস মেসেজ ও মেম্বার জয়েন হ্যান্ডলার ====================

@dp.message(F.content_type.in_({'new_chat_members', 'left_chat_member', 'pinned_message'}))
async def handle_service_messages(message: types.Message):
    if config.get("clean_service_msgs", True):
        try:
            await message.delete()
        except Exception:
            pass

@dp.chat_member()
async def on_user_join(event: types.ChatMemberUpdated):
    if event.new_chat_member.status in ["member", "restricted"] and event.old_chat_member.status in ["left", "kicked"]:
        user = event.new_chat_member.user
        track_user(user)

        # যদি গ্রুপ শাটডাউনে থাকে, নতুন মেম্বারকেও মেসেজ দেওয়া থেকে বিরত থাকবে
        if shutdown_state.get("is_shutdown", False):
            return

        if config.get("welcome_enabled", True):
            w_text = config.get("welcome_text", "স্বাগতম {name}!").replace("{name}", f"[{user.first_name}](tg://user?id={user.id})")
            group_username = event.chat.username or ""
            share_url = f"https://t.me/share/url?url=https://t.me/{group_username}&text=Join%20our%20link%20sharing%20group!"
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📢 বন্ধুদের শেয়ার করুন", url=share_url)]
            ])
            try:
                msg = await bot.send_message(
                    chat_id=event.chat.id,
                    text=w_text,
                    parse_mode="Markdown",
                    reply_markup=kb
                )
                record_msg(event.chat.id, msg.message_id)
                asyncio.create_task(auto_delete(msg, 30))
            except Exception:
                pass

# ==================== ৯. গ্রুপ মেসেজ ও লিংক ফিল্টারিং কোর ইঞ্জিন ====================

@dp.message(F.chat.type.in_({'group', 'supergroup'}))
async def handle_group_traffic(message: types.Message):
    global TARGET_GROUP_ID
    TARGET_GROUP_ID = message.chat.id
    if config.get("target_group_id") != message.chat.id:
        config["target_group_id"] = message.chat.id
        save_data()

    record_msg(message.chat.id, message.message_id)

    user = message.from_user
    if not user:
        return
    track_user(user)

    # মূল অ্যাডমিনের মেসেজে কোনো ফিল্টারিং প্রয়োগ হবে না
    if user.id == ADMIN_ID:
        return

    # ★★★ গুরুত্বপূর্ণ: গ্রুপ শাটডাউন চেক ★★★
    now = time.time()
    if shutdown_state.get("is_shutdown", False) or (now >= shutdown_state.get("active_expiry", 0)):
        # যদি শাটডাউন কার্যকর থাকে, কোনো মেম্বার মেসেজ পাঠাতে পারবে না
        if not shutdown_state.get("is_shutdown", False):
            asyncio.create_task(trigger_group_shutdown(source="auto_check"))
        try:
            await message.delete()
        except Exception:
            pass
        return

    # গ্রুপ অ্যাডমিন কি না যাচাই
    try:
        chat_member = await bot.get_chat_member(chat_id=message.chat.id, user_id=user.id)
        if chat_member.status in ["creator", "administrator"]:
            return
    except Exception:
        pass

    text_to_scan = message.text or message.caption or ""

    entities = message.entities or message.caption_entities or []
    for entity in entities:
        if entity.type == "text_link" and entity.url:
            text_to_scan += f" {entity.url}"
        elif entity.type == "url":
            offset = entity.offset
            length = entity.length
            raw_url = (message.text or message.caption or "")[offset:offset+length]
            text_to_scan += f" {raw_url}"

    has_tg_link = bool(TG_LINK_REGEX.search(text_to_scan))
    has_any_link = bool(ANY_LINK_REGEX.search(text_to_scan)) or has_tg_link

    # দৃশ্যপট ১: সাধারণ টেক্সট বা ছবি (কোনো লিংক নেই)
    if not has_any_link:
        if config.get("delete_non_links", True):
            try:
                await message.delete()
            except Exception:
                pass
        return

    # দৃশ্যপট ২: লিংক আছে কিন্তু টেলিগ্রাম লিংক নয়
    if has_any_link and not has_tg_link and config.get("allow_only_tg_links", True):
        try:
            await message.delete()
        except Exception:
            pass
        warn = await message.answer(
            f"⚠️ [{user.first_name}](tg://user?id={user.id}), এই গ্রুপে **শুধুমাত্র টেলিগ্রাম লিংক** শেয়ার করা অনুমোদিত!",
            parse_mode="Markdown"
        )
        asyncio.create_task(auto_delete(warn, 12))
        return

    # দৃশ্যপট ৩: টেলিগ্রাম লিংক পোস্ট করেছে
    if not config.get("require_verification", True):
        if str(user.id) in all_known_users:
            all_known_users[str(user.id)]["links_shared"] += 1
            save_data()
        return

    u_info = verified_users.get(str(user.id), {"version": 0, "click_time": 0})
    is_verified = (u_info.get("version") == config["current_version"])

    if not is_verified:
        try:
            await message.delete()
        except Exception:
            pass

        if config["mode"] == "join_request":
            try:
                member = await bot.get_chat_member(chat_id=config["target_channel"], user_id=user.id)
                if member.status in ["member", "administrator", "creator", "restricted"]:
                    verified_users[str(user.id)] = {
                        "version": config["current_version"],
                        "time": time.time(),
                        "name": user.full_name or user.first_name,
                        "username": f"@{user.username}" if user.username else "নেই"
                    }
                    save_data()
                    return
            except Exception:
                pass

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👉 জয়েন রিকোয়েস্ট পাঠান", url=config["target_channel_link"])],
                [InlineKeyboardButton(text="✅ আমি রিকোয়েস্ট দিয়েছি (Verify)", callback_data=f"v_req_{user.id}")]
            ])
            w = await message.answer(
                f"⚠️ [{user.first_name}](tg://user?id={user.id}), গ্রুপে পোস্ট করার আগে আমাদের চ্যানেলে জয়েন রিকোয়েস্ট পাঠাতে হবে!",
                parse_mode="Markdown",
                reply_markup=kb
            )
            asyncio.create_task(auto_delete(w, 20))

        elif config["mode"] == "ad_link":
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🌐 লিংকে গিয়ে অপেক্ষা করুন", url=config["ad_link"])],
                [InlineKeyboardButton(text="✅ ভেরিফাই করুন", callback_data=f"v_ad_{user.id}")]
            ])
            w = await message.answer(
                f"⚠️ [{user.first_name}](tg://user?id={user.id}), লিংক শেয়ার আনলক করতে নিচের ওয়েবসাইটে গিয়ে {config['ad_wait_seconds']} সেকেন্ড অপেক্ষা করে ভেরিফাই বাটনে চাপ দিন!",
                parse_mode="Markdown",
                reply_markup=kb
            )
            verified_users[str(user.id)] = {
                "version": 0,
                "click_time": time.time(),
                "name": user.full_name or user.first_name,
                "username": f"@{user.username}" if user.username else "নেই"
            }
            save_data()
            asyncio.create_task(auto_delete(w, 25))

# ==================== ১০. ভেরিফিকেশন বাটন কলব্যাক ====================

@dp.callback_query(F.data.startswith("v_"))
async def handle_user_verification_callback(query: types.CallbackQuery):
    parts = query.data.split("_")
    v_type = parts[1]
    u_id = int(parts[2])
    user = query.from_user

    if user.id != u_id:
        await query.answer("❌ এটি আপনার ভেরিফিকেশন বাটন নয়!", show_alert=True)
        return

    if v_type == "req":
        try:
            member = await bot.get_chat_member(chat_id=config["target_channel"], user_id=u_id)
            if member.status in ["member", "administrator", "creator", "restricted"]:
                verified_users[str(u_id)] = {
                    "version": config["current_version"],
                    "time": time.time(),
                    "name": user.full_name or user.first_name,
                    "username": f"@{user.username}" if user.username else "নেই"
                }
                save_data()
                await query.answer("🎉 ভেরিফিকেশন সফল! আপনার লিংক শেয়ারিং আনলক হয়েছে।", show_alert=True)
                try:
                    await query.message.delete()
                except Exception:
                    pass
                return
        except Exception:
            pass
        await query.answer("❌ আপনি এখনো রিকোয়েস্ট পাঠাননি! দয়া করে চ্যানেলে জয়েন রিকোয়েস্ট দিন।", show_alert=True)

    elif v_type == "ad":
        u_info = verified_users.get(str(u_id), {"version": 0, "click_time": 0})
        start_time = u_info.get("click_time", 0)
        elapsed = time.time() - start_time
        required = config["ad_wait_seconds"]
        if elapsed >= required:
            verified_users[str(u_id)] = {
                "version": config["current_version"],
                "time": time.time(),
                "name": user.full_name or user.first_name,
                "username": f"@{user.username}" if user.username else "নেই"
            }
            save_data()
            await query.answer("🎉 ভেরিফিকেশন সফল! আপনার লিংক শেয়ারিং আনলক হয়েছে।", show_alert=True)
            try:
                await query.message.delete()
            except Exception:
                pass
        else:
            remaining = int(required - elapsed)
            await query.answer(f"⏳ অনুগ্রহ করে আরও {remaining} সেকেন্ড লিংকে অপেক্ষা করুন!", show_alert=True)

# ==================== ১১. ব্যাকগ্রাউন্ড শিডিউলার্স ====================

async def shutdown_and_renew_scheduler():
    """
    ১. প্রতি ৫ ঘণ্টা পর পর অ্যাডমিনের ইনবক্সে রিনিউ করার প্রম্পট পাঠাবে।
    ২. প্রতি ১ মিনিটে চেক করবে ২৪ ঘণ্টা পার হয়েছে কি না। পার হলে গ্রুপ শাটডাউন করে দেবে।
    """
    FIVE_HOURS = 5 * 3600
    while True:
        try:
            await asyncio.sleep(60) # প্রতি ১ মিনিটে স্টেট যাচাই
            now = time.time()

            # ১. শাটডাউন টাইমার চেক
            if not shutdown_state.get("is_shutdown", False):
                if now >= shutdown_state.get("active_expiry", 0):
                    print("Shutdown timer triggered: 24 hours reached without renewal!")
                    await trigger_group_shutdown(source="timer")

            # ২. পাঁচ ঘণ্টা রিনিউ নোটিশ চেক
            # যদি গ্রুপ রানিং থাকে এবং সর্বশেষ প্রম্পটের পর ৫ ঘণ্টা পার হয়ে থাকে
            if not shutdown_state.get("is_shutdown", False):
                last_prompt = shutdown_state.get("last_prompt_time", 0)
                if now - last_prompt >= FIVE_HOURS:
                    shutdown_state["last_prompt_time"] = now
                    shutdown_state["prompt_count"] = shutdown_state.get("prompt_count", 0) + 1
                    save_data()

                    rem_sec = max(0, shutdown_state["active_expiry"] - now)
                    rem_str = format_time_remaining(rem_sec)

                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="✅ কনফার্ম করুন (নতুন ২৪ ঘণ্টা শুরু)", callback_data="renew_confirm"),
                            InlineKeyboardButton(text="❌ বাতিল (পূর্বের অবশিষ্ট সময় চলবে)", callback_data="renew_cancel")
                        ]
                    ])

                    prompt_msg = (
                        "🔔 **গ্রুপ মেয়াদ রিনিউ নোটিফিকেশন (৫ ঘণ্টা ব্যবধান)**\n"
                        "━━━━━━━━━━━━━━━━━━━━\n"
                        f"⏳ **পূর্বের সময় অনুযায়ী আর বাকি আছে:** `{rem_str}`\n\n"
                        "আপনি কি এখনই গ্রুপটি রিনিউ করতে চান?\n\n"
                        "👉 **'কনফার্ম করুন'** চাপলে এই মুহূর্ত থেকে নতুন **২৪ ঘণ্টা** শুরু হবে।\n"
                        "👉 **'বাতিল'** চাপলে পূর্বে শুরু হওয়া ২৪ ঘণ্টার বাকি সময় (`{rem_str}`) গ্রুপটি চলবে।"
                    ).replace("{rem_str}", rem_str)

                    try:
                        await bot.send_message(
                            chat_id=ADMIN_ID,
                            text=prompt_msg,
                            parse_mode="Markdown",
                            reply_markup=kb
                        )
                    except Exception as e:
                        print("Error sending 5-hour renewal prompt to admin:", e)

        except Exception as e:
            print("Error in shutdown_and_renew_scheduler:", e)
            await asyncio.sleep(10)

async def promo_broadcast_task():
    while True:
        await asyncio.sleep(config.get("broadcast_interval", 3600))
        # গ্রুপ শাটডাউন থাকলে প্রমোশন ব্রডকাস্ট হবে না
        if shutdown_state.get("is_shutdown", False):
            continue
        gid = TARGET_GROUP_ID or config.get("target_group_id")
        if config.get("promo_enabled", True) and gid:
            try:
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=config["promo_btn_text"], url=config["promo_btn_link"])]
                ])
                p_msg = await bot.send_message(
                    chat_id=gid,
                    text=config["promo_text"],
                    reply_markup=kb
                )
                record_msg(gid, p_msg.message_id)
            except Exception:
                pass

async def handle_ping(request):
    now = time.time()
    rem_sec = max(0, shutdown_state.get("active_expiry", 0) - now)
    status = "SHUTDOWN" if shutdown_state.get("is_shutdown", False) else f"ACTIVE ({int(rem_sec/3600)}h remaining)"
    return web.Response(text=f"Bot Engine Active! Status: {status}")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server running on port {port}")

async def main():
    print("🚀 টেলিগ্রাম সেশন প্রস্তুত করা হচ্ছে...")
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(start_web_server())
    asyncio.create_task(shutdown_and_renew_scheduler())
    asyncio.create_task(promo_broadcast_task())
    print("🚀 পাগলা বাবা টেলিগ্রাম বট সফলভাবে চালু হয়েছে এবং কাজ করছে!")
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
