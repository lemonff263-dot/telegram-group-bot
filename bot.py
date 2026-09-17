# -*- coding: utf-8 -*-
import asyncio
import json
import os
import re
import time
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

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
    "current_version": 1
}

config = default_config.copy()
verified_users = {}      # {str(user_id): {"version": int, "time": float, "name": str, "username": str}}
all_known_users = {}     # {str(user_id): {"name": str, "username": str, "joined_at": float, "links_shared": int}}
admin_input_state = {}   # {user_id: {"action": str, "step": str}}
GROUP_MESSAGES = {}      # {chat_id: [(msg_id, timestamp)]}

def load_data():
    global config, verified_users, all_known_users
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                config.update(data.get("config", {}))
                verified_users = data.get("verified_users", {})
                all_known_users = data.get("all_known_users", {})
        except Exception as e:
            print("Error loading data:", e)

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "config": config,
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

# লিংক ডিটেকশন রেজেক্স (সকল প্রকার t.me, telegram.me, https://, http://, www ইত্যাদি)
TG_LINK_REGEX = re.compile(
    r'(https?:\/\/)?([a-zA-Z0-9-]+\.)*(t\.me|telegram\.me|telegram\.dog)\/[a-zA-Z0-9_+/?=&#%-]+',
    re.IGNORECASE
)
ANY_LINK_REGEX = re.compile(
    r'(https?:\/\/|www\.)[a-zA-Z0-9_\-\.]+\.[a-zA-Z]{2,}(\/[a-zA-Z0-9_+/?=&#%-]*)?',
    re.IGNORECASE
)

# ==================== ১. কমান্ড হ্যান্ডলারস ====================

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
        "▫️ `/clean` - গ্রুপে কত ঘণ্টার চ্যাট ডিলিট করবেন তার বাটন মেনু আসবে\n"
        "▫️ `/clean <ঘণ্টা>` - সরাসরি নির্দিষ্ট ঘণ্টার মেসেজ সাফ করুন (যেমন: `/clean 2`)\n"
        "▫️ `/myid` - আপনার টেলিগ্রাম ইউজার আইডি ও স্ট্যাটাস প্রদর্শন\n\n"
        "⚙️ *ইনস্ট্যান্ট সেটিংস কমান্ড (শর্টকাট):*\n"
        "▫️ `/setchannel <@username>` - টার্গেট চ্যানেল পরিবর্তন (যেমন: `/setchannel @romantic_video900`)\n"
        "▫️ `/setlink <url>` - চ্যানেলের জয়েন রিকোয়েস্ট লিংক সেট (যেমন: `/setlink https://t.me/+...`)\n"
        "▫️ `/setad <url>` - অ্যাড ওয়েবসাইটের লিংক পরিবর্তন\n"
        "▫️ `/setwait <সেকেন্ড>` - অ্যাড দেখার অপেক্ষার সময় সেট (যেমন: `/setwait 15`)\n\n"
        "🛡️ *বটের স্বয়ংক্রিয় ফিচারসমূহ:*\n"
        "1️⃣ **লিংক ফিল্টারিং:** গ্রুপে কোনো সদস্য লিংক শেয়ার করলে বট যাচাই করে সে চ্যানেলে জয়েন আছে কি না।\n"
        "2️⃣ **অটো ডিলিট:** ভেরিফিকেশন ছাড়া লিংক পোস্ট করলে সাথে সাথে মুছে জয়েন বাটন প্রদর্শন করা হয়।\n"
        "3️⃣ **সার্ভিস মেসেজ ক্লিন:** মেম্বার জয়েন বা লিভ নেওয়ার নোটিফিকেশন নিজে নিজেই সাফ হয়ে যায়।\n"
        "4️⃣ **অটো প্রোমোশন:** নির্ধারিত সময় পর পর চ্যানেলের প্রমোশনাল পোস্ট গ্রুপে ব্রডকাস্ট হয়।"
    )
    m = await message.reply(help_text, parse_mode="Markdown")
    if message.chat.type != "private":
        asyncio.create_task(auto_delete(m, 45))

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

# ==================== ২. ক্লিনআপ কমান্ড ====================

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

    # অতিরিক্ত মেসেজ আইডি প্রি-স্ক্যান
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

# ==================== ৩. অ্যাডমিন কন্ট্রোল প্যানেল (A to Z শাখা-প্রশাখা) ====================

@dp.message(Command("admin"))
@dp.message(Command("panel"))
async def cmd_admin_main(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        if message.chat.type != "private":
            w = await message.reply("❌ এটি শুধুমাত্র অ্যাডমিনের জন্য অনুমোদিত!")
            asyncio.create_task(auto_delete(w, 10))
        return

    # ইনবক্স নিশ্চিত করা
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
    text = (
        "👑 **পাগলা বাবা বট — মূল অ্যাডমিন কন্ট্রোল প্যানেল**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "আপনার বটের সমস্ত সেটিংস, মোড, লিংক, ব্যবহারকারী ও টেক্সট এই প্যানেল থেকে শাখা ভিত্তিক সরাসরি নিয়ন্ত্রণ করতে পারবেন।\n\n"
        f"🔹 **বর্তমান মোড:** `{config['mode']}`\n"
        f"🔹 **টার্গেট চ্যানেল:** `{config['target_channel']}`\n"
        f"🔹 **ভেরিফিকেশন ফিল্টার:** `{'🟢 চালু (ON)' if config['require_verification'] else '🔴 বন্ধ (OFF)'}`\n"
        f"🔹 **নন-টেলিগ্রাম লিংক ডিলিট:** `{'🟢 চালু (ON)' if config['allow_only_tg_links'] else '🔴 বন্ধ (OFF)'}`\n"
        f"🔹 **সাধারণ মেসেজ ডিলিট:** `{'🟢 চালু (ON)' if config['delete_non_links'] else '🔴 বন্ধ (OFF)'}`\n"
        f"🔹 **মোট পরিচিত মেম্বার:** `{len(all_known_users)} জন` | **ভেরিফাইড:** `{len(verified_users)} জন`\n\n"
        "👇 _যেকোনো শাখার বিস্তারিত দেখতে নিচের বোতামে চাপুন:_"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 চ্যানেল ও রিকোয়েস্ট শাখা", callback_data="br_channel"),
            InlineKeyboardButton(text="🌐 ডাইরেক্ট অ্যাড লিংক শাখা", callback_data="br_ad")
        ],
        [
            InlineKeyboardButton(text="🛡️ লিংক ফিল্টারিং শাখা (ON/OFF)", callback_data="br_filters"),
            InlineKeyboardButton(text="💬 ওয়েলকাম ও মেসেজ শাখা", callback_data="br_welcome")
        ],
        [
            InlineKeyboardButton(text="📢 অটো প্রোমোশন শাখা", callback_data="br_promo"),
            InlineKeyboardButton(text="👥 ইউজার ও ভেরিফিকেশন লিস্ট", callback_data="br_users")
        ],
        [
            InlineKeyboardButton(text="🔄 মোড পরিবর্তন (Toggle Mode)", callback_data="act_toggle_mode"),
            InlineKeyboardButton(text="♻️ রিসেট অল ভেরিফিকেশন", callback_data="act_reset_verifications")
        ],
        [
            InlineKeyboardButton(text="❌ প্যানেল বন্ধ করুন", callback_data="act_close_panel")
        ]
    ])
    return text, kb

# ==================== ৪. শাখা ভিত্তিক নেভিগেশন ও বাটন হ্যান্ডলার ====================

@dp.callback_query(F.data.startswith("br_"))
@dp.callback_query(F.data.startswith("act_"))
@dp.callback_query(F.data.startswith("tog_"))
@dp.callback_query(F.data.startswith("edit_"))
async def handle_admin_branches(query: types.CallbackQuery):
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ আপনি এই বটের অ্যাডমিন নন!", show_alert=True)
        return

    data = query.data

    # --- ১. মূল মেনুতে ফেরা ---
    if data == "br_main":
        text, kb = build_admin_main_view()
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        await query.answer()
        return

    # --- ২. প্যানেল বন্ধ করা ---
    elif data == "act_close_panel":
        await query.message.delete()
        await query.answer("প্যানেল বন্ধ করা হয়েছে")
        return

    # --- ৩. মোড সুইচ (Join Request <-> Ad Link) ---
    elif data == "act_toggle_mode":
        config["mode"] = "ad_link" if config["mode"] == "join_request" else "join_request"
        save_data()
        await query.answer(f"সফল! মোড এখন: {config['mode']}", show_alert=True)
        text, kb = build_admin_main_view()
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        return

    # --- ৪. সমস্ত ভেরিফিকেশন রিসেট ---
    elif data == "act_reset_verifications":
        config["current_version"] += 1
        verified_users.clear()
        save_data()
        await query.answer("♻️ সমস্ত ইউজারের ভেরিফিকেশন রিসেট করা হয়েছে! সবাইকে নতুন করে ভেরিফাই করতে হবে।", show_alert=True)
        text, kb = build_admin_main_view()
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        return

    # --- ৫. চ্যানেল ও রিকোয়েস্ট শাখা ---
    elif data == "br_channel":
        text = (
            "🎯 **চ্যানেল ও জয়েন রিকোয়েস্ট শাখা**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• টার্গেট চ্যানেল ইউজারনেম: `{config['target_channel']}`\n"
            f"• চ্যানেল জয়েন রিকোয়েস্ট লিংক: `{config['target_channel_link']}`\n"
            f"• বর্তমান কার্যকারী মোড: `{config['mode']}`\n\n"
            "💡 *কিভাবে কাজ করে?*\n"
            "মেম্বাররা গ্রুপে লিংক দিলে এই চ্যানেলে রিকোয়েস্ট পাঠানো ছাড়া কোনো লিংক দিতে পারবে না। বট স্বয়ংক্রিয়ভাবে সদস্যপদ চেক করবে।\n\n"
            "কী পরিবর্তন করতে চান নিচের বোতামে চাপুন:"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ চ্যানেল ইউজারনেম পরিবর্তন", callback_data="edit_channel_user")],
            [InlineKeyboardButton(text="✏️ চ্যানেল রিকোয়েস্ট লিংক পরিবর্তন", callback_data="edit_channel_link")],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        await query.answer()

    # --- ৬. অ্যাড লিংক শাখা ---
    elif data == "br_ad":
        text = (
            "🌐 **ডাইরেক্ট অ্যাড ও ট্রাফিক শাখা**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• অ্যাড ইউআরএল: `{config['ad_link']}`\n"
            f"• অপেক্ষার সময়: `{config['ad_wait_seconds']} সেকেন্ড`\n"
            f"• মোড স্ট্যাটাস: `{'সক্রিয়' if config['mode'] == 'ad_link' else 'নিষ্ক্রিয় (বর্তমানে join_request চলছে)'}`\n\n"
            "💡 *কিভাবে কাজ করে?*\n"
            "মেম্বাররা এই লিংকে গিয়ে নির্ধারিত সেকেন্ড অপেক্ষা করার পর তাদের লিংক গ্রুপে শেয়ার করতে পারবে।\n\n"
            "কী পরিবর্তন করতে চান:"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ অ্যাড লিংক পরিবর্তন", callback_data="edit_ad_link")],
            [InlineKeyboardButton(text="⏱️ ওয়েটিং টাইম পরিবর্তন", callback_data="edit_ad_wait")],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        await query.answer()

    # --- ৭. লিংক ফিল্টারিং ও নিরাপত্তা শাখা (ON/OFF Switches) ---
    elif data == "br_filters":
        text = (
            "🛡️ **গ্রুপ লিংক ফিল্টারিং ও নিরাপত্তা শাখা**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "নিচের প্রতিটি সেটিং বোতামে চাপ দিয়ে সরাসরি ON বা OFF করতে পারেন:\n\n"
            f"1️⃣ **ভেরিফিকেশন বাধ্যবাধকতা:** `{'🟢 চালু (ON)' if config['require_verification'] else '🔴 বন্ধ (OFF)'}`\n"
            "_(বন্ধ থাকলে যে কেউ সরাসরি লিংক শেয়ার করতে পারবে)_\n\n"
            f"2️⃣ **শুধুমাত্র টেলিগ্রাম লিংক অনুমোদন:** `{'🟢 চালু (ON)' if config['allow_only_tg_links'] else '🔴 বন্ধ (OFF)'}`\n"
            "_(চালু থাকলে ইউটিউব/ফেসবুক বা অন্যান্য সাইটের লিংক ডিলিট হবে)_\n\n"
            f"3️⃣ **নন-লিংক সাধারণ মেসেজ ডিলিট:** `{'🟢 চালু (ON)' if config['delete_non_links'] else '🔴 বন্ধ (OFF)'}`\n"
            "_(চালু থাকলে লিংক ছাড়া সাধারণ টেক্সট/ছবি নিজে নিজে মুছে যাবে)_\n\n"
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

    # --- টগল হ্যান্ডলারসমূহ ---
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

    # --- ৮. ওয়েলকাম মেসেজ শাখা ---
    elif data == "br_welcome":
        text = (
            "💬 **ওয়েলকাম মেসেজ শাখা**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• ওয়েলকাম নোটিফিকেশন: `{'🟢 চালু (ON)' if config['welcome_enabled'] else '🔴 বন্ধ (OFF)'}`\n\n"
            f"📝 **বর্তমান টেক্সট:**\n"
            f"_{config['welcome_text']}_\n\n"
            "💡 _(নতুন ইউজার জয়েন করলে বট এই মেসেজটি দিয়ে তাকে গ্রুপে স্বাগত জানায়। মেসেজে `{name}` লিখলে ইউজারের নাম অটো বসে যাবে।)_"
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

    # --- ৯. অটো প্রোমোশন ব্রডকাস্ট শাখা ---
    elif data == "br_promo":
        text = (
            "📢 **অটো প্রোমোশন ও বিজ্ঞাপন শাখা**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• ব্রডকাস্ট স্ট্যাটাস: `{'🟢 চালু (ON)' if config['promo_enabled'] else '🔴 বন্ধ (OFF)'}`\n"
            f"• ব্যবধান: `প্রতি {int(config['broadcast_interval']/60)} মিনিট পর পর`\n"
            f"• বাটন নাম: `{config['promo_btn_text']}`\n"
            f"• বাটন লিংক: `{config['promo_btn_link']}`\n\n"
            f"📝 **বর্তমান প্রোমো বার্তা:**\n"
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

    # --- ১০. ইউজার ও ভেরিফিকেশন তালিকা শাখা ---
    elif data == "br_users":
        total_k = len(all_known_users)
        total_v = len(verified_users)

        # সাম্প্রতিক ৫ জন ভেরিফাইড ইউজার
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
            f"{ver_list_str}\n\n"
            "💡 _(আপনি চাইলে 'রিসেট অল' বাটনে চাপ দিয়ে যেকোনো সময় সমস্ত মেম্বারদের ভেরিফিকেশন বাতিল করে পুনরায় ভেরিফাই করতে বাধ্য করতে পারেন।)_"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="♻️ সমস্ত ইউজার ভেরিফিকেশন বাতিল (Reset)", callback_data="act_reset_verifications")],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
        await query.answer()

    # --- ১১. ইন্টারঅ্যাক্টিভ ইনপুট এডিটর প্রম্পটসমূহ ---
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

# ==================== ৫. ইনবক্সে টেক্সট ইনপুট গ্রহণ ও সংরক্ষণ ====================

@dp.message(F.chat.type == "private")
async def handle_private_inputs(message: types.Message):
    track_user(message.from_user)
    if message.from_user.id != ADMIN_ID:
        return

    uid = message.from_user.id
    if uid not in admin_input_state:
        # কোনো স্টেট না থাকলে নরমাল প্যানেল কমান্ড নির্দেশ করা
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

    # আপডেট করার পর নতুন মূল প্যানেল পাঠিয়ে দেওয়া
    p_text, p_kb = build_admin_main_view()
    await message.answer(p_text, parse_mode="Markdown", reply_markup=p_kb)

# ==================== ৬. শর্টকাট কমান্ড হ্যান্ডলারস ====================

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

# ==================== ৭. সার্ভিস মেসেজ ও মেম্বার জয়েন হ্যান্ডলার ====================

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

# ==================== ৮. গ্রুপ মেসেজ ও লিংক ফিল্টারিং কোর ইঞ্জিন ====================

@dp.message(F.chat.type.in_({'group', 'supergroup'}))
async def handle_group_traffic(message: types.Message):
    global TARGET_GROUP_ID
    TARGET_GROUP_ID = message.chat.id
    record_msg(message.chat.id, message.message_id)

    user = message.from_user
    if not user:
        return
    track_user(user)

    # অ্যাডমিনের মেসেজে কোনো ফিল্টারিং প্রয়োগ হবে না
    if user.id == ADMIN_ID:
        return

    # গ্রুপ অ্যাডমিন কি না যাচাই
    try:
        chat_member = await bot.get_chat_member(chat_id=message.chat.id, user_id=user.id)
        if chat_member.status in ["creator", "administrator"]:
            return
    except Exception:
        pass

    text_to_scan = message.text or message.caption or ""

    # এন্টাইটিস চেক (যদি মেসেজের ভেতর টেক্সট হাইপারলিংক থাকে)
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

    # দৃশ্যপট ১: ইউজার কোনো লিংক পোস্ট করেনি (সাধারণ মেসেজ, ছবি, স্টিকার ইত্যাদি)
    if not has_any_link:
        if config.get("delete_non_links", True):
            try:
                await message.delete()
            except Exception:
                pass
        return

    # দৃশ্যপট ২: লিংক আছে, কিন্তু টেলিগ্রাম লিংক নয় (ইউটিউব, ওয়েবসাইট ইত্যাদি)
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

    # দৃশ্যপট ৩: টেলিগ্রাম লিংক পোস্ট করেছে -> ভেরিফিকেশন চেক
    if not config.get("require_verification", True):
        # ভেরিফিকেশন অফ থাকলে সরাসরি অ্যালাও
        if str(user.id) in all_known_users:
            all_known_users[str(user.id)]["links_shared"] += 1
            save_data()
        return

    u_info = verified_users.get(str(user.id), {"version": 0, "click_time": 0})
    is_verified = (u_info.get("version") == config["current_version"])

    # যদি মেম্বার অলরেডি ভেরিফাইড না থাকে:
    if not is_verified:
        # সঙ্গে সঙ্গে অপরীক্ষিত লিংক মুছে দেওয়া হবে
        try:
            await message.delete()
        except Exception:
            pass

        # মোড ১: চ্যানেল জয়েন রিকোয়েস্ট মোড
        if config["mode"] == "join_request":
            # টেলিগ্রাম API দিয়ে লাইভ চেক: মেম্বার কি চ্যানেলে জয়েন আছে?
            try:
                target = config["target_channel"]
                cm = await bot.get_chat_member(chat_id=target, user_id=user.id)
                if cm.status in ["member", "administrator", "creator", "restricted"]:
                    # অলরেডি চ্যানেলে আছে, স্বয়ংক্রিয় ভেরিফাই করে নেওয়া হলো
                    verified_users[str(user.id)] = {
                        "version": config["current_version"],
                        "time": time.time(),
                        "name": user.full_name or user.first_name,
                        "username": f"@{user.username}" if user.username else "নেই"
                    }
                    save_data()
                    notice = await message.answer(
                        f"🎉 [{user.first_name}](tg://user?id={user.id}), আপনি আমাদের চ্যানেলের সদস্য! আপনার ভেরিফিকেশন সফল। এবার লিংক পোস্ট করুন।",
                        parse_mode="Markdown"
                    )
                    asyncio.create_task(auto_delete(notice, 10))
                    return
            except Exception as e:
                print("Live check error:", e)

            # চ্যানেলে না থাকলে জয়েন রিকোয়েস্ট কার্ড পাঠানো
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👉 চ্যানেলে জয়েন রিকোয়েস্ট পাঠান", url=config["target_channel_link"])],
                [InlineKeyboardButton(text="✅ আমি রিকোয়েস্ট দিয়েছি (Verify)", callback_data=f"v_req_{user.id}")]
            ])
            w = await message.answer(
                f"⚠️ [{user.first_name}](tg://user?id={user.id}), গ্রুপে লিংক শেয়ার করার আগে আমাদের মূল চ্যানেলে **জয়েন রিকোয়েস্ট** পাঠাতে হবে!\n\n"
                f"🔗 রিকোয়েস্ট পাঠিয়ে নিচের **'✅ আমি রিকোয়েস্ট দিয়েছি'** বাটনে চাপুন:",
                parse_mode="Markdown",
                reply_markup=kb
            )
            asyncio.create_task(auto_delete(w, 30))

        # মোড ২: ডাইরেক্ট অ্যাড লিংক মোড
        elif config["mode"] == "ad_link":
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🌐 লিংকে গিয়ে অপেক্ষা করুন", url=config["ad_link"])],
                [InlineKeyboardButton(text="✅ ভেরিফাই করুন", callback_data=f"v_ad_{user.id}")]
            ])
            w = await message.answer(
                f"⚠️ [{user.first_name}](tg://user?id={user.id}), লিংক শেয়ার আনলক করতে নিচের ওয়েবসাইটে গিয়ে **{config['ad_wait_seconds']} সেকেন্ড** অপেক্ষা করে ভেরিফাই বাটনে চাপুন!",
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
            asyncio.create_task(auto_delete(w, 30))

    else:
        # মেম্বার অলরেডি ভেরিফাইড! লিংক পোস্ট হতে দেওয়া হবে
        if str(user.id) in all_known_users:
            all_known_users[str(user.id)]["links_shared"] += 1
            save_data()

# ==================== ৯. মেম্বার ভেরিফিকেশন কলব্যাক ====================

@dp.callback_query(F.data.startswith("v_"))
async def handle_user_verification(query: types.CallbackQuery):
    parts = query.data.split("_")
    v_type = parts[1]
    u_id = int(parts[2])

    if query.from_user.id != u_id:
        await query.answer("❌ এটি আপনার জন্য নয়!", show_alert=True)
        return

    user = query.from_user

    if v_type == "req":
        try:
            target = config["target_channel"]
            member = await bot.get_chat_member(chat_id=target, user_id=u_id)
            if member.status in ["member", "administrator", "creator", "restricted"]:
                verified_users[str(u_id)] = {
                    "version": config["current_version"],
                    "time": time.time(),
                    "name": user.full_name or user.first_name,
                    "username": f"@{user.username}" if user.username else "নেই"
                }
                save_data()
                await query.answer("🎉 চমৎকার! আপনার ভেরিফিকেশন সফল হয়েছে। এখন লিংক পোস্ট করতে পারেন!", show_alert=True)
                try:
                    await query.message.delete()
                except Exception:
                    pass
                return
        except Exception as e:
            print("Verify check error:", e)

        await query.answer("❌ আপনি এখনো চ্যানেলে জয়েন বা রিকোয়েস্ট পাঠাননি! দয়া করে বাটনে ক্লিক করে আগে রিকোয়েস্ট দিন।", show_alert=True)

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

# ==================== ১০. ব্যাকগ্রাউন্ড শিডিউলার ও সার্ভার ====================

async def promo_broadcast_task():
    while True:
        await asyncio.sleep(config.get("broadcast_interval", 3600))
        if config.get("promo_enabled", True) and TARGET_GROUP_ID:
            try:
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=config["promo_btn_text"], url=config["promo_btn_link"])]
                ])
                p_msg = await bot.send_message(
                    chat_id=TARGET_GROUP_ID,
                    text=config["promo_text"],
                    reply_markup=kb
                )
                record_msg(TARGET_GROUP_ID, p_msg.message_id)
            except Exception:
                pass

async def handle_ping(request):
    return web.Response(text="Bot Engine is 100% Active, Safe and Running!")

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
    asyncio.create_task(promo_broadcast_task())
    print("🚀 পাগলা বাবা টেলিগ্রাম বট সফলভাবে চালু হয়েছে এবং কাজ করছে!")
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
