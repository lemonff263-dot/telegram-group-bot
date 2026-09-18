# -*- coding: utf-8 -*-
"""
পাগলা বাবা টেলিগ্রাম বট (PAGLA BABA TELEGRAM BOT)
- শতভাগ কাস্টমাইজেবল (A to Z সেটিংস, টাইমার, বাটন, টেক্সট ও লিংক)
- ডেটা সেভ ও ভেরিফিকেশন রিসেট শতভাগ নিরাপদ (কোনো সেটিংস রিসেট হবে না)
- ২৪ ঘণ্টা শাটডাউন ও ৫ ঘণ্টা রিনিউ সাইকেল
- চ্যানেল জয়েন রিকোয়েস্ট ও ডাইরেক্ট অ্যাড লিংক মোড
"""

import os
import re
import time
import json
import uuid
import html
import random
import asyncio
from urllib.parse import quote
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
try:
    from aiogram.types import ReactionTypeEmoji
except ImportError:
    ReactionTypeEmoji = None

# ----------------- পাথ ও কনফিগারেশন -----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "bot_data.json")
BACKUP_DATA_FILE = os.path.join(BASE_DIR, "bot_data_backup.json")

BOT_TOKEN = "8879708023:AAHXoRntXfHB0PqkTbMbBiQ3ZE8raib-N4o"
ADMIN_ID = 1958884768
TARGET_GROUP_ID = None

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ----------------- ডিফল্ট কনফিগারেশন (A to Z) -----------------
default_config = {
    # ১. মোড ও চ্যানেল/লিংক
    "mode": "both",                        # "both" (উভয় অপশন), "join_request", অথবা "ad_link"
    "target_channel": "@romantic_video900",
    "target_channel_link": "https://t.me/romantic_video900",
    "ad_link": "https://negotiatenapkin.com/x4ihpte44?key=4a61bc5be7fb6bf03e4b91ff497b17e6",
    "target_group_invite": "https://t.me/+1Q-p9zTyPpQ5MWVl",

    # ২. টাইমার ও সময়সীমা (Seconds / Minutes / Hours)
    "ad_wait_seconds": 8,                  # অ্যাড ওয়েবসাইটে অপেক্ষার সেকেন্ড (৮ সেকেন্ড)
    "verify_card_delete_sec": 30,          # ভেরিফিকেশন কার্ড ডিলিট টাইমার
    "non_link_warn_delete_sec": 8,         # সাধারণ মেসেজ নিষেধ নোটিশ ডিলিট টাইমার
    "other_link_warn_delete_sec": 12,      # অন্য লিংক নিষেধ নোটিশ ডিলিট টাইমার
    "verify_success_delete_sec": 10,       # ভেরিফিকেশন সফল নোটিশ ডিলিট টাইমার
    "welcome_delete_sec": 20,              # ওয়েলকাম মেসেজ ডিলিট টাইমার
    "broadcast_interval_mins": 60,         # অটো প্রোমো প্রচারের ব্যবধান (মিনিট)
    "promo_delete_sec": 300,               # প্রোমো মেসেজ ডিলিট হওয়ার সেকেন্ড (০ = স্থায়ী)
    "shutdown_duration_hours": 24,         # গ্রুপ সক্রিয় থাকার মেয়াদ (ঘণ্টা)
    "renew_prompt_hours": 5,               # রিনিউ প্রম্পটের ব্যবধান (ঘণ্টা)

    # ৩. মেসেজ ও নোটিশ টেক্সটসমূহ (A to Z)
    "msg_join_req_notice": "⚠️ {user_link}, গ্রুপে লিংক শেয়ার করার আগে আমাদের মূল চ্যানেলে <b>জয়েন রিকোয়েস্ট</b> পাঠাতে হবে!\n\n🔗 রিকোয়েস্ট পাঠিয়ে নিচের বোতামে চাপুন:",
    "msg_ad_link_notice": "⚠️ {user_link}, গ্রুপে লিংক শেয়ারের অনুমতি পেতে স্পন্সর ওয়েবসাইটে প্রবেশ করে পুরো <b>{wait_seconds} সেকেন্ড</b> অপেক্ষা করতে হবে!\n\n📌 <b>নির্দেশনা:</b>\n১. নিচের বোতাম চেপে ওয়েবসাইটে যান।\n২. পুরো {wait_seconds} সেকেন্ড অপেক্ষা করুন।\n৩. ফিরে এসে ভেরিফাই বোতাম চাপুন।",
    "msg_non_link_warn": "⚠️ {user_link}, এই গ্রুপে সাধারণ চ্যাট অনুমোদিত নয়! শুধুমাত্র ভেরিফাইড মেম্বাররা টেলিগ্রাম লিংক শেয়ার করতে পারেন।",
    "msg_only_tg_warn": "⚠️ {user_link}, এই গ্রুপে <b>শুধুমাত্র টেলিগ্রাম লিংক</b> শেয়ার করা অনুমোদিত!",
    "msg_verify_success": "🎉 {user_link}, আপনার ভেরিফিকেশন সফল হয়েছে! আপনার লিংক শেয়ারিং পারমিশন আনলক করা হয়েছে।",
    "welcome_text": "👋 স্বাগতম {name}!\nআমাদের এই গ্রুপে শুধুমাত্র টেলিগ্রাম লিংক শেয়ার করতে পারবেন।",
    "promo_text": "🔥 সেরা টেলিগ্রাম কনটেন্টের জন্য আমাদের মেইন চ্যানেলে জয়েন করুন!",

    # ৪. বাটন টেক্সটসমূহ
    "btn_join_req": "👉 চ্যানেলে জয়েন রিকোয়েস্ট পাঠান",
    "btn_join_verify": "✅ আমি রিকোয়েস্ট দিয়েছি (Verify)",
    "btn_ad_visit": "🌐 মূল ওয়েবসাইটে যান (অপেক্ষা করুন)",
    "btn_ad_verify": "✅ ভেরিফাই সম্পন্ন করুন",
    "btn_welcome_verify": "🔗 লিংক শেয়ারের পারমিশন নিতে ভেরিফাই করুন",
    "promo_btn_text": "🚀 চ্যানেলে জয়েন করুন",
    "promo_btn_link": "https://t.me/romantic_video900",

    # ৫. টগল সুইচসমূহ (ON / OFF)
    "require_verification": True,
    "allow_only_tg_links": True,
    "delete_non_links": True,
    "clean_service_msgs": True,
    "welcome_enabled": True,
    "welcome_verify_btn": True,
    "promo_enabled": True,
    "filter_admins": False,

    # ৬. ভেরিফাই ব্যাজ সেটিংস (Verified Badge System)
    "enable_admin_badge": True,            # নামের পাশে ভেরিফাই ব্যাজ দেখাবে কি না (ON/OFF)
    "badge_title": "✓ Verified",           # ব্যাজের নাম (টেলিগ্রাম কাস্টম টাইটেল, সর্বোচ্চ ১৬ অক্ষর)
    "badge_reaction_enabled": True,        # ভেরিফাইড মেম্বার লিংক দিলে রিঅ্যাকশন মার্ক (ON/OFF)
    "badge_reaction_emoji": "⚡",           # রিঅ্যাকশন ইমোজি

    # ৭. সিস্টেম ভেরিয়েবল
    "current_version": 1,
    "target_group_id": None,

    # ৮. পয়েন্ট, লেভেল ও গ্যামিফিকেশন সেটিংস (Gamification)
    "gamification_enabled": False,         # পয়েন্ট ও লেভেল সিস্টেম চালু/বন্ধ (সাময়িকভাবে বন্ধ)
    "points_per_link": 10,                 # গ্রুপে বৈধ লিংক শেয়ারে অর্জিত পয়েন্ট
    "points_per_l4l": 15,                  # অন্যের লিংকে সাপোর্ট দিয়ে অর্জিত পয়েন্ট
    "points_per_referral": 200,            # প্রতি সফল রেফারেল বোনাস
    "points_welcome_bonus": 50,            # নতুন ইউজারের ওয়েলকাম পয়েন্ট
    "points_daily_base": 100,              # ডেইলি বোনাস বেস পয়েন্ট
    "points_daily_streak_mult": 2,         # ৫ দিন স্ট্রিক পূরণ হলে বোনাস গুণক (২ গুণ)
    "daily_bonus_enabled": False,          # ডেইলি বোনাস চালু/বন্ধ
    "lucky_spin_enabled": False,           # লাকি স্পিন চালু/বন্ধ
    "store_enabled": False,                # ভার্চুয়াল শপ চালু/বন্ধ
    "tasks_enabled": False,                # অ্যাডমিন টাস্ক হাব চালু/বন্ধ
    "l4l_enabled": False,                  # লিংক ফর লিংক (L4L) চালু/বন্ধ
    "auto_delete_links_hours": 0,          # লিংক স্বয়ংক্রিয়ভাবে মুছে দেওয়ার সময় (ঘণ্টা, ০ = নিষ্ক্রিয়)
    "vip_custom_button_enabled": True,     # VIP মেম্বারদের লিংকে বিশেষ বাটন ও রিঅ্যাকশন

    # ভার্চুয়াল শপের মূল্য তালিকা
    "cost_pinned_1h": 2000,                 # ১ ঘণ্টার পিন্ড মেসেজ সুবিধা
    "cost_unlimited_24h": 4000,            # ২৪ ঘণ্টার আনলিমিটেড লিংক সুবিধা
    "cost_vip_7d": 8000,                   # ৭ দিনের VIP মেম্বারশিপ

    # ৯. পাবলিক গ্রুপ ও অটো জয়েন রিকোয়েস্ট সেটিংস
    "auto_accept_join_requests": False,    # গ্রুপে অটো জয়েন রিকোয়েস্ট একসেপ্ট (ডিফল্ট: বন্ধ)
    "disable_link_previews": True,         # বড় লিংক প্রিভিউ কার্ড বন্ধ করে কমপ্যাক্ট/ছোট লিংক রাখা
    "antiflood_enabled": True,             # পাবলিক গ্রুপে স্প্যাম ও রেইড বট আক্রমণ প্রতিরোধ
    "antiflood_limit": 4,                  # ৪ সেকেন্ডে সর্বোচ্চ ৩-৪ টি মেসেজ অনুমোদিত
    "antiflood_seconds": 4
}

default_shutdown_state = {
    "is_shutdown": False,
    "active_expiry": time.time() + (24 * 3600),
    "last_renew_time": time.time(),
    "last_prompt_time": time.time(),
    "prompt_count": 0,
    "shutdown_timestamp": 0
}

default_monetization_tasks = [
    {
        "id": "adsterra_1",
        "title": "🌐 স্পন্সর ওয়েবসাইট ভিজিট (Adsterra Direct Ad)",
        "type": "ad_wait",
        "url": "https://google.com",
        "wait_sec": 15,
        "points": 50,
        "active": True
    },
    {
        "id": "chan_official",
        "title": "📢 আমাদের অফিসিয়াল চ্যানেলে জয়েন করুন",
        "type": "channel_join",
        "channel": "@romantic_video900",
        "link": "https://t.me/romantic_video900",
        "points": 100,
        "active": True
    },
    {
        "id": "adsterra_bonus",
        "title": "🔥 স্পেশাল অফার পেজ ১০ সেকেন্ড দেখুন",
        "type": "ad_wait",
        "url": "https://google.com",
        "wait_sec": 10,
        "points": 75,
        "active": True
    }
]

config = default_config.copy()
shutdown_state = default_shutdown_state.copy()
verified_users = {}      # {str(user_id): {"version": int, "time": float, "name": str, "username": str}}
all_known_users = {}     # {str(user_id): {"name": str, "username": str, "first_seen": float, "links_shared": int}}
user_gamification = {}   # {str(user_id): {"points": int, "streak": int, "last_daily": float, "last_spin": float, ...}}
monetization_tasks = [dict(t) for t in default_monetization_tasks]
l4l_recent_links = []    # [{"user_id": int, "name": str, "url": str, "message_id": int, "chat_id": int, "time": float}]
admin_input_state = {}   # {user_id: {"action": str, "chat_id": int}}
GROUP_MESSAGES = {}      # {chat_id: [(msg_id, timestamp)]}
ad_sessions = {}         # {token: dict}
task_sessions = {}       # {token: dict}
pending_join_requests = {} # {str(user_id): {"user_id": int, "chat_id": int, "name": str, "username": str, "time": float}}
USER_FLOOD_TRACKER = {}   # {user_id: [timestamps]}
COMPACT_PERM_APPLIED = False
last_promo_time = time.time()

# ----------------- ডেটা সেভ ও লোড (বুলেটপ্রুফ পারসিস্টেন্স) -----------------
def load_data():
    global config, shutdown_state, verified_users, all_known_users, user_gamification, monetization_tasks, TARGET_GROUP_ID, pending_join_requests
    for path in [DATA_FILE, BACKUP_DATA_FILE]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        saved_cfg = data.get("config", {})
                        if isinstance(saved_cfg, dict):
                            for k, v in saved_cfg.items():
                                config[k] = v
                        saved_shutdown = data.get("shutdown_state", {})
                        if isinstance(saved_shutdown, dict):
                            shutdown_state.update(saved_shutdown)
                        if shutdown_state.get("active_expiry", 0) < time.time() and not shutdown_state.get("is_shutdown", False):
                            dur = config.get("shutdown_duration_hours", 24) * 3600
                            shutdown_state["active_expiry"] = time.time() + dur
                            shutdown_state["last_renew_time"] = time.time()
                            shutdown_state["last_prompt_time"] = time.time()
                        verified_users = data.get("verified_users", {})
                        all_known_users = data.get("all_known_users", {})
                        user_gamification = data.get("user_gamification", {})
                        pending_join_requests = data.get("pending_join_requests", {})
                        loaded_tasks = data.get("monetization_tasks", None)
                        if loaded_tasks and isinstance(loaded_tasks, list):
                            monetization_tasks = loaded_tasks
                        if config.get("target_group_id"):
                            TARGET_GROUP_ID = config["target_group_id"]
                        break
            except Exception as e:
                print(f"Error loading data from {path}:", e)

def save_data():
    try:
        data = {
            "config": config,
            "shutdown_state": shutdown_state,
            "verified_users": verified_users,
            "all_known_users": all_known_users,
            "user_gamification": user_gamification,
            "monetization_tasks": monetization_tasks,
            "pending_join_requests": pending_join_requests
        }
        tmp_file = DATA_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_file, DATA_FILE)
        with open(BACKUP_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Error saving data:", e)

load_data()

# ----------------- হেল্পার ফাংশনসমূহ -----------------
def check_user_flood(user_id: int) -> bool:
    """পাবলিক গ্রুপে স্প্যাম ও রেইড বট ফ্লাড প্রতিরোধ"""
    if not config.get("antiflood_enabled", True):
        return False
    now = time.time()
    times = USER_FLOOD_TRACKER.get(user_id, [])
    # শেষ ৪ সেকেন্ডের টাইমস্ট্যাম্প সংরক্ষণ
    times = [t for t in times if now - t <= float(config.get("antiflood_seconds", 4))]
    times.append(now)
    USER_FLOOD_TRACKER[user_id] = times
    return len(times) > int(config.get("antiflood_limit", 4))

async def apply_compact_link_permissions(chat_id: int) -> bool:
    """টেলিগ্রাম গ্রুপে মেম্বারদের লিংক প্রিভিউ বন্ধ করে লিংক ছোট ও পরিচ্ছন্ন রাখা"""
    if not chat_id:
        return False
    try:
        perms = ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=False,
            can_invite_users=True
        )
        await bot.set_chat_permissions(chat_id=chat_id, permissions=perms)
        return True
    except Exception as e:
        print("Error applying compact link permissions:", e)
        return False

def is_real_group_admin(chat_member) -> bool:
    """গ্রুপের প্রকৃত অ্যাডমিন বা ওনার কি না তা যাচাই (ভেরিফাইড ইউজারদের নকল অ্যাডমিন বাদ দিয়ে)"""
    if not chat_member:
        return False
    if chat_member.status == "creator":
        return True
    if chat_member.status == "administrator":
        badge_title = config.get("badge_title", "✓ Verified")[:16]
        c_title = getattr(chat_member, "custom_title", "") or ""
        # যদি সদস্যের পদবি ভেরিফাই ব্যাজের পদবির সাথে মিলে এবং কোনো মডারেশন পাওয়ার না থাকে
        if c_title == badge_title:
            return False
        # প্রকৃত অ্যাডমিন ক্ষমতা (মেসেজ ডিলিট বা ইউজার ব্যান/রেস্ট্রিক্ট) থাকলে
        if getattr(chat_member, "can_delete_messages", False) or getattr(chat_member, "can_restrict_members", False):
            return True
        return False
    return False

# ----------------- হেল্পার ফাংশনসমূহ -----------------
async def auto_delete(msg: types.Message, delay: int = 15):
    if delay <= 0:
        return
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
    get_user_profile(user.id, user)

def get_user_profile(user_id: int, user: types.User = None) -> dict:
    uid = str(user_id)
    if uid not in user_gamification:
        user_gamification[uid] = {
            "points": config.get("points_welcome_bonus", 50),
            "streak": 0,
            "last_daily": 0,
            "last_spin": 0,
            "vip_until": 0,
            "unlimited_pass_until": 0,
            "pinned_pass_until": 0,
            "referred_by": None,
            "referral_count": 0,
            "tasks_completed": [],
            "links_shared_count": 0,
            "l4l_credits": 0,
            "name": user.full_name or user.first_name if user else "User",
            "username": f"@{user.username}" if user and user.username else "নেই"
        }
        save_data()
    else:
        if user:
            user_gamification[uid]["name"] = user.full_name or user.first_name
            if user.username:
                user_gamification[uid]["username"] = f"@{user.username}"
    return user_gamification[uid]

def get_level_info(points: int, vip_until: float = 0):
    is_vip = vip_until > time.time()
    if is_vip:
        return 4, "VIP Member", "👑 VIP Member", "gold"
    if points >= 2000:
        return 3, "Top Promoter", "🏆 Top Promoter", "purple"
    elif points >= 501:
        return 2, "Active Member", "🔥 Active Member", "blue"
    else:
        return 1, "Newbie", "🌱 Newbie", "green"

def format_time_remaining(seconds: float) -> str:
    if seconds <= 0:
        return "০ মিনিট"
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    if hrs > 0:
        return f"{hrs} ঘণ্টা {mins} মিনিট"
    return f"{mins} মিনিট"

TG_LINK_REGEX = re.compile(
    r'(https?:\/\/)?([a-zA-Z0-9-]+\.)*(t\.me|telegram\.me|telegram\.dog)\/[a-zA-Z0-9_+/?=&#%-]+',
    re.IGNORECASE
)
ANY_LINK_REGEX = re.compile(
    r'(https?:\/\/[^\s]+)|(www\.[^\s]+)|([a-zA-Z0-9-]+\.(com|net|org|io|me|xyz|info|app|co|biz|tv|club|live|pro)[^\s]*)',
    re.IGNORECASE
)

# ----------------- ভেরিফাই ব্যাজ ও পারমিশন সিস্টেম -----------------
async def grant_user_verification(chat_id: int, user: types.User):
    """ইউজারকে ভেরিফাইড হিসেবে মার্ক করে এবং টেলিগ্রাম কাস্টম টাইটেল দিয়ে নামের পাশে ব্যাজ দেয়"""
    uid_str = str(user.id)
    verified_users[uid_str] = {
        "version": config.get("current_version", 1),
        "time": time.time(),
        "name": user.full_name or user.first_name,
        "username": f"@{user.username}" if user.username else "নেই"
    }
    save_data()

    # টেলিগ্রাম কাস্টম অ্যাডমিন টাইটেল দিয়ে নামের পাশে ব্যাজ সেট করা
    gid = chat_id or TARGET_GROUP_ID or config.get("target_group_id")
    if config.get("enable_admin_badge", True) and gid:
        try:
            badge_title = config.get("badge_title", "✓ Verified")[:16]
            await bot.promote_chat_member(
                chat_id=gid,
                user_id=user.id,
                can_manage_chat=True,
                can_invite_users=True,
                can_change_info=False,
                can_delete_messages=False,
                can_restrict_members=False,
                can_pin_messages=False,
                can_promote_members=False
            )
            await bot.set_chat_administrator_custom_title(
                chat_id=gid,
                user_id=user.id,
                custom_title=badge_title
            )
        except Exception as e:
            # বটের পারমিশন না থাকলে বা ইউজার ওনার/অ্যাডমিন হলে নিরাপদে পাস
            pass

async def remove_all_verified_badges(chat_id: int):
    """ভেরিফিকেশন রিসেটের সময় সমস্ত সাধারণ মেম্বারদের নামের পাশ থেকে ব্যাজ অপসারণ (ডিমোট) করা"""
    if not chat_id:
        return
    for uid_str in list(verified_users.keys()):
        try:
            uid = int(uid_str)
            if uid == ADMIN_ID:
                continue
            await bot.promote_chat_member(
                chat_id=chat_id,
                user_id=uid,
                can_manage_chat=False,
                can_change_info=False,
                can_delete_messages=False,
                can_invite_users=False,
                can_restrict_members=False,
                can_pin_messages=False,
                can_promote_members=False
            )
        except Exception:
            pass

# ==================== ১. গ্রুপ শাটডাউন ও আনলক মেকানিজম ====================

async def trigger_group_shutdown(source="timer"):
    shutdown_state["is_shutdown"] = True
    shutdown_state["shutdown_timestamp"] = time.time()
    save_data()

    gid = TARGET_GROUP_ID or config.get("target_group_id")
    if gid:
        try:
            locked_perm = ChatPermissions(
                can_send_messages=False,
                can_send_audios=False,
                can_send_documents=False,
                can_send_photos=False,
                can_send_videos=False,
                can_send_video_notes=False,
                can_send_voice_notes=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            )
            await bot.set_chat_permissions(chat_id=gid, permissions=locked_perm)
            dur = config.get("shutdown_duration_hours", 24)
            await bot.send_message(
                chat_id=gid,
                text=(
                    f"⛔ <b>গ্রুপ সাময়িকভাবে লক (শাটডাউন) করা হয়েছে!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"মেয়াদ ({dur} ঘণ্টা) শেষ হওয়ায় স্বয়ংক্রিয়ভাবে চ্যাট পাঠানো বন্ধ করা হয়েছে। "
                    f"অ্যাডমিন রিনিউ কনফার্ম করা মাত্রই গ্রুপটি পুনরায় উন্মুক্ত হবে।"
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            print("Error locking chat permissions in shutdown:", e)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ এখনই গ্রুপ রিভাইভ (আনলক) করুন", callback_data="renew_confirm")]
    ])
    try:
        dur = config.get("shutdown_duration_hours", 24)
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"🚨 <b>জরুরি সতর্কবার্তা: গ্রুপ শাটডাউন হয়েছে!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"পরপর {dur} ঘণ্টা অতিক্রান্ত হওয়ায় আপনার গ্রুপটিতে মেসেজ পাঠানো বন্ধ করে লক করা হয়েছে।\n\n"
                f"গ্রুপ পুনরায় চালু করতে নিচের বোতামে চাপ দিন:"
            ),
            parse_mode="HTML",
            reply_markup=kb
        )
    except Exception as e:
        print("Error sending admin shutdown alert:", e)

async def trigger_group_revive():
    dur_sec = config.get("shutdown_duration_hours", 24) * 3600
    shutdown_state["is_shutdown"] = False
    shutdown_state["active_expiry"] = time.time() + dur_sec
    shutdown_state["last_renew_time"] = time.time()
    shutdown_state["last_prompt_time"] = time.time()
    shutdown_state["prompt_count"] = 0
    save_data()

    gid = TARGET_GROUP_ID or config.get("target_group_id")
    if gid:
        try:
            open_perm = ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False
            )
            await bot.set_chat_permissions(chat_id=gid, permissions=open_perm)
            dur = config.get("shutdown_duration_hours", 24)
            await bot.send_message(
                chat_id=gid,
                text=(
                    f"🔓 <b>গ্রুপ সফলভাবে আনলক ও সচল করা হয়েছে!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"পরবর্তী {dur} ঘণ্টার জন্য মেম্বারদের জন্য গ্রুপ উন্মুক্ত করা হলো। নিয়ম মেনে লিংক শেয়ার করুন।"
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            print("Error restoring chat permissions:", e)

# ==================== ২. অ্যাডমিন ও ইউজার কমান্ডস ====================

# ==================== ২.১ ইউজার গ্যামিফিকেশন ও মনিটাইজেশন ড্যাশবোর্ড ভিউ ====================

def build_user_dashboard(user_id: int, user: types.User = None):
    prof = get_user_profile(user_id, user)
    lvl_num, lvl_title, badge, _ = get_level_info(prof.get("points", 0), prof.get("vip_until", 0))
    is_vip = prof.get("vip_until", 0) > time.time()
    vip_status = f"👑 সক্রিয় ({format_time_remaining(prof['vip_until'] - time.time())})" if is_vip else "সাধারণ মেম্বার"

    full_name = (user.full_name or user.first_name) if user else prof.get("name", "User")

    text = (
        f"👋 <b>স্বাগতম, {html.escape(full_name)}!</b>\n"
        f"👑 <b>পাগলা বাবা মেম্বার হাব ও রিওয়ার্ড সেন্টার</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>পয়েন্ট ব্যালেন্স:</b> <code>{prof.get('points', 0)} Points</code>\n"
        f"🎖️ <b>বর্তমান লেভেল:</b> <code>Level {lvl_num} — {lvl_title}</code>\n"
        f"🔥 <b>ডেইলি স্ট্রিক:</b> <code>{prof.get('streak', 0)} দিন</code>\n"
        f"👑 <b>VIP স্ট্যাটাস:</b> <code>{vip_status}</code>\n"
        f"👥 <b>মোট রেফারেল:</b> <code>{prof.get('referral_count', 0)} জন</code>\n"
        f"🔗 <b>শেয়ারকৃত লিংক:</b> <code>{prof.get('links_shared_count', 0)} টি</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 <i>পয়েন্ট ইনকাম ও শপ সুবিধা নিতে নিচের অপশন বাছাই করুন:</i>"
    )

    kb_rows = [
        [
            InlineKeyboardButton(text="📋 টাস্ক ও পয়েন্ট ইনকাম (+100 pts)", callback_data="usr_tasks"),
            InlineKeyboardButton(text="🎁 ডেইলি বোনাস", callback_data="usr_daily")
        ],
        [
            InlineKeyboardButton(text="🎰 লাকি স্পিন (Lucky Wheel)", callback_data="usr_spin"),
            InlineKeyboardButton(text="🛒 ভার্চুয়াল শপ / স্টোর", callback_data="usr_shop")
        ],
        [
            InlineKeyboardButton(text="🏆 টপ লিডারবোর্ড", callback_data="usr_leaderboard"),
            InlineKeyboardButton(text="🔗 ইনভাইট ও রেফারেল", callback_data="usr_invite")
        ],
        [
            InlineKeyboardButton(text="🤝 সাপোর্ট ও আর্ন (L4L)", callback_data="usr_l4l"),
            InlineKeyboardButton(text="👤 আমার পূর্ণাঙ্গ প্রোফাইল", callback_data="usr_profile")
        ]
    ]
    if user_id == ADMIN_ID:
        kb_rows.append([InlineKeyboardButton(text="⚙️ অ্যাডমিন কন্ট্রোল প্যানেল", callback_data="br_main")])

    return text, InlineKeyboardMarkup(inline_keyboard=kb_rows)

def build_tasks_view(user_id: int, user: types.User = None):
    prof = get_user_profile(user_id, user)
    completed = set(prof.get("tasks_completed", []))

    text = (
        "📋 <b>অ্যাড ও মনিটাইজেশন টাস্ক সেন্টার</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "নিচের সহজ টাস্কগুলো সম্পন্ন করে অতিরিক্ত পয়েন্ট আয় করুন। এই পয়েন্ট দিয়ে আপনি গ্রুপে পিন পোস্ট ও ভিআইপি মেম্বারশিপ নিতে পারবেন!\n\n"
    )
    kb = []
    active_tasks = [t for t in monetization_tasks if t.get("active", True)]
    if not active_tasks:
        text += "<i>বর্তমানে কোনো নতুন টাস্ক উপলব্ধ নেই। কিছু সময় পর পুনরায় চেষ্টা করুন।</i>\n"
    else:
        for t in active_tasks:
            tid = t.get("id")
            title = t.get("title")
            pts = t.get("points", 100)
            ttype = t.get("type")
            if tid in completed:
                kb.append([InlineKeyboardButton(text=f"✅ {title} (+{pts} pts) [সম্পন্ন]", callback_data=f"task_done_{tid}")])
            else:
                if ttype == "ad_wait":
                    kb.append([InlineKeyboardButton(text=f"🌐 {title} (+{pts} pts)", callback_data=f"task_open_ad_{tid}")])
                elif ttype == "channel_join":
                    kb.append([InlineKeyboardButton(text=f"📢 {title} (+{pts} pts)", callback_data=f"task_open_chan_{tid}")])

    kb.append([InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="usr_main")])
    return text, InlineKeyboardMarkup(inline_keyboard=kb)

def build_shop_view(user_id: int, user: types.User = None):
    prof = get_user_profile(user_id, user)
    pts = prof.get("points", 0)
    c_pin = config.get("cost_pinned_1h", 2000)
    c_unl = config.get("cost_unlimited_24h", 4000)
    c_vip = config.get("cost_vip_7d", 8000)

    text = (
        "🛒 <b>পয়েন্ট রিডিম শপ ও ভার্চুয়াল স্টোর</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 আপনার বর্তমান পয়েন্ট: <code>{pts} Points</code>\n\n"
        "🛍️ <b>উপলব্ধ সুবিধাসমূহ:</b>\n\n"
        f"📌 <b>১. গ্রুপে পিন্ড মেসেজ সুবিধা (১ ঘণ্টা)</b>\n"
        f"• আপনার শেয়ার করা লিংক গ্রুপে সবার উপরে পিন করে রাখা হবে।\n"
        f"• খরচ: <code>{c_pin} Points</code>\n\n"
        f"⚡ <b>২. আনলিমিটেড লিংক পাস (২৪ ঘণ্টা)</b>\n"
        f"• ২৪ ঘণ্টার জন্য কোনো বাধা ছাড়া যত খুশি লিংক পোস্ট করুন।\n"
        f"• খরচ: <code>{c_unl} Points</code>\n\n"
        f"👑 <b>৩. ভিআইপি মেম্বারশিপ পাস (৭ দিন)</b>\n"
        f"• নামের পাশে গোল্ডেন 👑 VIP Member টাইটেল ও স্টার রিঅ্যাকশন।\n"
        f"• খরচ: <code>{c_vip} Points</code>\n"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📌 পিন্ড মেসেজ পাস ({c_pin} pts)", callback_data="buy_pass_pinned")],
        [InlineKeyboardButton(text=f"⚡ আনলিমিটেড লিংক পাস ({c_unl} pts)", callback_data="buy_pass_unlimited")],
        [InlineKeyboardButton(text=f"👑 VIP মেম্বারশিপ ৭ দিন ({c_vip} pts)", callback_data="buy_pass_vip")],
        [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="usr_main")]
    ])
    return text, kb

def build_leaderboard_view(user_id: int):
    sorted_users = sorted(
        user_gamification.items(),
        key=lambda x: x[1].get("points", 0),
        reverse=True
    )
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    lines = []
    my_rank = "তালিকায় নেই"
    for i, (uid_s, data) in enumerate(sorted_users, 1):
        if str(user_id) == uid_s:
            my_rank = f"#{i}"
        if i <= 10:
            medal = medals[i-1] if i-1 < len(medals) else f"#{i}"
            uname = data.get("name", "User")
            pts = data.get("points", 0)
            lines.append(f"{medal} <b>{html.escape(uname)}</b> — <code>{pts} pts</code>")

    board_txt = "\n".join(lines) if lines else "<i>এখনও কোনো রেকর্ড পাওয়া যায়নি।</i>"

    text = (
        "🏆 <b>সাপ্তাহিক টপ প্রমোটার লিডারবোর্ড</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"আপনার অবস্থান: <b>{my_rank}</b>\n\n"
        f"{board_txt}\n\n"
        "💡 <i>প্রতি রবিবার রাতে সর্বোচ্চ পয়েন্টধারীদের স্পেশাল প্রোমোশন ও পিন ফিচার উপহার দেওয়া হয়!</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 রিফ্রেশ লিডারবোর্ড", callback_data="usr_leaderboard")],
        [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="usr_main")]
    ])
    return text, kb

def build_invite_view(user_id: int, bot_username: str):
    prof = get_user_profile(user_id)
    ref_count = prof.get("referral_count", 0)
    ref_pts = config.get("points_per_referral", 200)
    welcome_pts = config.get("points_welcome_bonus", 50)
    link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    share_url = f"https://t.me/share/url?url={quote(link)}&text={quote('🔥 সেরা টেলিগ্রাম লিংক শেয়ারিং ও ইনকাম বটে যোগ দিন এবং ফ্রি পয়েন্ট নিন!')}"

    text = (
        "🔗 <b>ইনভাইট ও রেফারেল প্রোগ্রাম</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "আপনার রেফারেল লিংকের মাধ্যমে নতুন বন্ধুদের ইনভাইট করুন এবং আনলিমিটেড পয়েন্ট আয় করুন!\n\n"
        f"🎁 <b>প্রতি সফল রেফারে:</b> <code>+{ref_pts} Points</code>\n"
        f"🎉 <b>আপনার বন্ধু পাবে:</b> <code>+{welcome_pts} Points ওয়েলকাম বোনাস</code>\n\n"
        f"📊 <b>আপনার পরিসংখ্যান:</b>\n"
        f"• মোট সফল রেফারেল: <code>{ref_count} জন</code>\n"
        f"• রেফারেল থেকে মোট অর্জিত: <code>{ref_count * ref_pts} Points</code>\n\n"
        f"📎 <b>আপনার ইউনিক রেফারেল লিংক:</b>\n<code>{link}</code>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📲 বন্ধুদের সাথে শেয়ার করুন", url=share_url)],
        [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="usr_main")]
    ])
    return text, kb

def build_profile_view(user_id: int, user: types.User = None):
    prof = get_user_profile(user_id, user)
    lvl_num, lvl_title, badge, _ = get_level_info(prof.get("points", 0), prof.get("vip_until", 0))
    is_vip = prof.get("vip_until", 0) > time.time()
    vip_str = f"👑 VIP সদস্য (মেয়াদ: {format_time_remaining(prof['vip_until'] - time.time())})" if is_vip else "সাধারণ সদস্য"

    unl_str = f"সক্রিয় ({format_time_remaining(prof['unlimited_pass_until'] - time.time())})" if prof.get("unlimited_pass_until", 0) > time.time() else "নিষ্ক্রিয়"
    pin_str = f"সক্রিয় ({format_time_remaining(prof['pinned_pass_until'] - time.time())})" if prof.get("pinned_pass_until", 0) > time.time() else "নিষ্ক্রিয়"

    name = (user.full_name or user.first_name) if user else prof.get("name", "User")

    text = (
        f"👤 <b>ব্যবহারকারীর বিস্তারিত প্রোফাইল</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"• নাম: <b>{html.escape(name)}</b>\n"
        f"• ইউজার আইডি: <code>{user_id}</code>\n"
        f"• মেম্বার পদমর্যাদা: <code>{lvl_title} ({badge})</code>\n"
        f"• বর্তমান লেভেল: <code>Level {lvl_num}</code>\n\n"
        f"💰 <b>পয়েন্ট ও ব্যালেন্স:</b>\n"
        f"• মোট পয়েন্ট: <code>{prof.get('points', 0)} Points</code>\n"
        f"• ডেইলি স্ট্রিক: <code>{prof.get('streak', 0)} দিন</code>\n"
        f"• রেফারেল সংখ্যা: <code>{prof.get('referral_count', 0)} জন</code>\n"
        f"• সম্পন্নকৃত টাস্ক: <code>{len(prof.get('tasks_completed', []))} টি</code>\n"
        f"• গ্রুপে পোস্টকৃত লিংক: <code>{prof.get('links_shared_count', 0)} টি</code>\n\n"
        f"🎟️ <b>সক্রিয় পাস ও সাবস্ক্রিপশন:</b>\n"
        f"• VIP স্ট্যাটাস: <code>{vip_str}</code>\n"
        f"• আনলিমিটেড লিংক পাস: <code>{unl_str}</code>\n"
        f"• পিন্ড মেসেজ পাস: <code>{pin_str}</code>\n"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="usr_main")]
    ])
    return text, kb

def build_l4l_view(user_id: int):
    prof = get_user_profile(user_id)
    pts_l4l = config.get("points_per_l4l", 15)
    text = (
        "🤝 <b>লিংক ফর লিংক (L4L) সাপোর্ট হাব</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "গ্রুপের অন্যান্য মেম্বারদের লিংকে ভিজিট বা সাপোর্ট করে পারস্পরিক সুবিধা নিন!\n"
        f"• প্রতি সাপোর্টে আপনি পাবেন: <code>+{pts_l4l} Points</code>\n\n"
        "📌 <b>সাম্প্রতিক শেয়ারকৃত লিংকসমূহ:</b>\n"
    )
    kb = []
    recent = [l for l in l4l_recent_links if l.get("user_id") != user_id][-5:]
    if not recent:
        text += "<i>বর্তমানে কোনো অপেক্ষমান লিংক নেই। গ্রুপে কেউ লিংক শেয়ার করলে এখানে দৃশ্যমান হবে।</i>\n"
    else:
        for idx, item in enumerate(recent, 1):
            text += f"{idx}. <b>{html.escape(item.get('name', 'User'))}</b> এর লিংক\n"
            mid = item.get("message_id")
            kb.append([InlineKeyboardButton(
                text=f"🔗 {html.escape(item.get('name', 'User'))} এর লিংকে সাপোর্ট (+{pts_l4l} pts)",
                callback_data=f"l4l_sup_{item.get('user_id')}_{mid}"
            )])

    kb.append([InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="usr_main")])
    return text, InlineKeyboardMarkup(inline_keyboard=kb)

# ==================== ২.২ অ্যাডমিন ও ইউজার কমান্ডস ====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    track_user(message.from_user)

    args = message.text.split() if message.text else []
    
    # ১. ডিপ-লিংক হ্যান্ডলার: স্পন্সর অ্যাড ভিজিট /start ad_TOKEN
    if len(args) > 1 and args[1].startswith("ad_"):
        token = args[1][3:]
        sess = ad_sessions.get(token)
        if sess and sess["user_id"] == message.from_user.id:
            now = time.time()
            sess["clicked"] = True
            sess["click_time"] = now
            wait_s = sess["wait_seconds"]
            ad_url = config.get("ad_link", "https://google.com")

            btn_visit_txt = config.get("btn_ad_visit", "🌐 মূল ওয়েবসাইটে যান (অপেক্ষা করুন)")
            btn_ver_txt = config.get("btn_ad_verify", "✅ ভেরিফাই সম্পন্ন করুন")

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=btn_visit_txt, url=ad_url)],
                [InlineKeyboardButton(text=btn_ver_txt, callback_data=f"v_ad_{sess['user_id']}_{token}")]
            ])
            await message.reply(
                f"🎉 <b>স্পন্সর ওয়েবসাইট ভিজিট সেশন চালু হয়েছে!</b>\n\n"
                f"⏱️ নিয়ম অনুযায়ী আপনাকে মূল ওয়েবসাইটে গিয়ে বাধ্যতামূলকভাবে কমপক্ষে <b>{wait_s} সেকেন্ড</b> অবস্থান করতে হবে।\n\n"
                f"⚠️ <i>সতর্কতা:</i> নির্দিষ্ট সময়ের পূর্বে ফিরে এসে বোতাম চাপলে ভেরিফিকেশন হবে না। সময় শেষ হলে নিচের বোতাম চাপুন।",
                parse_mode="HTML",
                reply_markup=kb
            )
            return

    # ২. রেফারেল ডিপ-লিংক হ্যান্ডলার: /start ref_USERID
    if len(args) > 1 and args[1].startswith("ref_"):
        ref_id_str = args[1][4:]
        if ref_id_str.isdigit() and int(ref_id_str) != message.from_user.id:
            prof = get_user_profile(message.from_user.id, message.from_user)
            if not prof.get("referred_by"):
                prof["referred_by"] = int(ref_id_str)
                # ওয়েলকাম বোনাস নতুন ইউজারকে
                wel_bonus = config.get("points_welcome_bonus", 50)
                prof["points"] = prof.get("points", 0) + wel_bonus

                # রেফারেল বোনাস রেফারারকে
                ref_user_prof = get_user_profile(int(ref_id_str))
                ref_bonus = config.get("points_per_referral", 200)
                ref_user_prof["points"] = ref_user_prof.get("points", 0) + ref_bonus
                ref_user_prof["referral_count"] = ref_user_prof.get("referral_count", 0) + 1
                save_data()

                try:
                    await bot.send_message(
                        chat_id=int(ref_id_str),
                        text=(
                            f"🎉 <b>অভিনন্দন! নতুন রেফারেল বোনাস!</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"ব্যবহারকারী <b>{html.escape(message.from_user.full_name)}</b> আপনার রেফারেল লিংকের মাধ্যমে যুক্ত হয়েছে।\n"
                            f"💰 আপনি পেয়েছেন: <b>+{ref_bonus} Points</b>!\n"
                            f"💵 মোট ব্যালেন্স: <code>{ref_user_prof['points']}</code> Points"
                        ),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

    # ৩. প্রাইভেট চ্যাটে ইউজার ড্যাশবোর্ড উপস্থাপন
    if message.chat.type == "private":
        dash_txt, dash_kb = build_user_dashboard(message.from_user.id, message.from_user)
        await message.answer(dash_txt, parse_mode="HTML", reply_markup=dash_kb)
        return

@dp.message(Command("daily"))
async def cmd_daily(message: types.Message):
    track_user(message.from_user)
    prof = get_user_profile(message.from_user.id, message.from_user)
    now = time.time()
    last = prof.get("last_daily", 0)

    if now - last < 86400:
        rem_sec = 86400 - (now - last)
        rem_str = format_time_remaining(rem_sec)
        w = await message.reply(f"⏳ আপনি ইতিমধ্যে আজকের ডেইলি বোনাস সংগ্রহ করেছেন!\nপরবর্তী বোনাস নিতে পারবেন আর <b>{rem_str}</b> পর।", parse_mode="HTML")
        if message.chat.type != "private":
            asyncio.create_task(auto_delete(w, 15))
        return

    # স্ট্রিক ক্যালকুলেশন
    streak = prof.get("streak", 0)
    if (now - last) <= (48 * 3600) and last > 0:
        streak += 1
    else:
        streak = 1
    prof["streak"] = streak

    base_pts = config.get("points_daily_base", 100)
    streak_mult = min(config.get("points_daily_streak_mult", 2.0), 1.0 + (streak - 1) * 0.1)
    bonus = int(base_pts * streak_mult)

    prof["points"] = prof.get("points", 0) + bonus
    prof["last_daily"] = now
    save_data()

    m = await message.reply(
        f"🎁 <b>ডেইলি রিওয়ার্ড সফলভাবে সংগ্রহ করা হয়েছে!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 প্রাপ্ত পয়েন্ট: <b>+{bonus} Points</b>\n"
        f"🔥 চলমান স্ট্রিক: <b>{streak} দিন</b> (মাল্টিপ্লায়ার: {streak_mult:.1f}x)\n"
        f"💵 বর্তমান মোট ব্যালেন্স: <code>{prof['points']}</code> Points\n\n"
        f"💡 <i>নিয়মিত প্রতিদিন এসে স্ট্রিক ধরে রাখুন এবং আরও বেশি পয়েন্ট জিতুন!</i>",
        parse_mode="HTML"
    )
    if message.chat.type != "private":
        asyncio.create_task(auto_delete(m, 20))

@dp.message(Command("spin"))
async def cmd_spin(message: types.Message):
    track_user(message.from_user)
    if not config.get("lucky_spin_enabled", True):
        await message.reply("⚠️ বর্তমানে লাকি স্পিন সিস্টেম সাময়িকভাবে বন্ধ রয়েছে।")
        return

    prof = get_user_profile(message.from_user.id, message.from_user)
    now = time.time()
    last = prof.get("last_spin", 0)

    if now - last < 86400:
        rem_sec = 86400 - (now - last)
        rem_str = format_time_remaining(rem_sec)
        w = await message.reply(f"⏳ আপনি আজকের ফ্রি স্পিন ব্যবহার করেছেন!\nপরবর্তী স্পিন করতে পারবেন আর <b>{rem_str}</b> পর।", parse_mode="HTML")
        if message.chat.type != "private":
            asyncio.create_task(auto_delete(w, 15))
        return

    won = random.choices([30, 50, 80, 100, 150, 200, 500], weights=[30, 25, 20, 12, 8, 4, 1])[0]
    prof["points"] = prof.get("points", 0) + won
    prof["last_spin"] = now
    save_data()

    m = await message.reply(
        f"🎰 <b>লাকি স্পিন ফলাফল! (Lucky Wheel)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎉 <b>অভিনন্দন! আপনি জিতেছেন:</b> <code>+{won} Points</code>!\n"
        f"💰 বর্তমান মোট ব্যালেন্স: <code>{prof['points']}</code> Points\n\n"
        f"পরবর্তী ফ্রি স্পিন আনলক হবে আগামী ২৪ ঘণ্টা পর।",
        parse_mode="HTML"
    )
    if message.chat.type != "private":
        asyncio.create_task(auto_delete(m, 20))

@dp.message(Command("tasks"))
@dp.message(Command("earn"))
async def cmd_tasks(message: types.Message):
    track_user(message.from_user)
    if message.chat.type != "private":
        bot_info = await bot.get_me()
        w = await message.reply(
            "📋 পয়েন্ট আর্নিং টাস্ক সম্পন্ন করতে ইনবক্সে বট ওপেন করুন:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📬 ইনবক্সে টাস্ক শুরু করুন", url=f"https://t.me/{bot_info.username}?start=tasks")]
            ])
        )
        asyncio.create_task(auto_delete(w, 20))
        return

    text, kb = build_tasks_view(message.from_user.id, message.from_user)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@dp.message(Command("shop"))
@dp.message(Command("store"))
async def cmd_shop(message: types.Message):
    track_user(message.from_user)
    text, kb = build_shop_view(message.from_user.id, message.from_user)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@dp.message(Command("leaderboard"))
@dp.message(Command("top"))
async def cmd_leaderboard(message: types.Message):
    track_user(message.from_user)
    text, kb = build_leaderboard_view(message.from_user.id)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@dp.message(Command("ref"))
@dp.message(Command("invite"))
async def cmd_invite(message: types.Message):
    track_user(message.from_user)
    bot_info = await bot.get_me()
    text, kb = build_invite_view(message.from_user.id, bot_info.username)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@dp.message(Command("profile"))
@dp.message(Command("points"))
@dp.message(Command("myinfo"))
async def cmd_profile(message: types.Message):
    track_user(message.from_user)
    text, kb = build_profile_view(message.from_user.id, message.from_user)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@dp.message(Command("l4l"))
async def cmd_l4l(message: types.Message):
    track_user(message.from_user)
    text, kb = build_l4l_view(message.from_user.id)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    track_user(message.from_user)
    help_txt = (
        "📖 <b>পাগলা বাবা বট নির্দেশিকা ও কমান্ড তালিকা</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 <code>/start</code> - মূল ইউজার হাব ও পয়েন্ট ব্যালেন্স\n"
        "🔹 <code>/daily</code> - দৈনিক ফ্রি বোনাস ও স্ট্রিক রিওয়ার্ড\n"
        "🔹 <code>/spin</code> - দৈনিক লাকি স্পিন হুইল\n"
        "🔹 <code>/tasks</code> - অ্যাড ও চ্যানেল জয়েন টাস্ক করে পয়েন্ট আয়\n"
        "🔹 <code>/shop</code> - পয়েন্ট খরচ করে পিন ও ভিআইপি পাস ক্রয়\n"
        "🔹 <code>/leaderboard</code> - সাপ্তাহিক টপ প্রমোটার তালিকা\n"
        "🔹 <code>/ref</code> - ইউনিক রেফারেল লিংক ও ইনভাইট বোনাস\n"
        "🔹 <code>/profile</code> - নিজের পয়েন্ট, স্ট্রিক ও ভিআইপি মেয়াদ\n"
        "🔹 <code>/l4l</code> - লিংক ফর লিংক পারস্পরিক সহায়তা\n"
    )
    if message.from_user.id == ADMIN_ID:
        help_txt += (
            "\n👑 <b>অ্যাডমিন কমান্ডসমূহ:</b>\n"
            "• <code>/admin</code> বা <code>/panel</code> - মূল কন্ট্রোল প্যানেল\n"
            "• <code>/reset_verify</code> - সকল মেম্বারের ভেরিফিকেশন রিসেট\n"
            "• <code>/clean &lt;hours&gt;</code> - নির্দিষ্ট ঘণ্টার চ্যাট মেসেজ মুছুন\n"
            "• <code>/settings</code> - পূর্ণাঙ্গ সিস্টেম সেটিংস ভিউ\n"
        )
    await message.answer(help_txt, parse_mode="HTML")

# ==================== ২.৩ ইউজার কলব্যাক হ্যান্ডলারস ====================

@dp.callback_query(F.data.startswith("usr_"))
async def handle_user_menu_callbacks(query: types.CallbackQuery):
    track_user(query.from_user)
    data = query.data
    uid = query.from_user.id

    if data == "usr_main":
        text, kb = build_user_dashboard(uid, query.from_user)
        try:
            await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass
        await query.answer()

    elif data == "usr_tasks":
        text, kb = build_tasks_view(uid, query.from_user)
        try:
            await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass
        await query.answer()

    elif data == "usr_daily":
        prof = get_user_profile(uid, query.from_user)
        now = time.time()
        last = prof.get("last_daily", 0)

        if now - last < 86400:
            rem_sec = 86400 - (now - last)
            rem_str = format_time_remaining(rem_sec)
            await query.answer(f"⏳ আপনি আজকের বোনাস নিয়েছেন! পরবর্তী বোনাস আর {rem_str} পর।", show_alert=True)
            return

        streak = prof.get("streak", 0)
        if (now - last) <= (48 * 3600) and last > 0:
            streak += 1
        else:
            streak = 1
        prof["streak"] = streak

        base_pts = config.get("points_daily_base", 100)
        streak_mult = min(config.get("points_daily_streak_mult", 2.0), 1.0 + (streak - 1) * 0.1)
        bonus = int(base_pts * streak_mult)

        prof["points"] = prof.get("points", 0) + bonus
        prof["last_daily"] = now
        save_data()

        await query.answer(f"🎉 +{bonus} Points সংগ্রহ হয়েছে! স্ট্রিক: {streak} দিন", show_alert=True)
        text, kb = build_user_dashboard(uid, query.from_user)
        try:
            await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass

    elif data == "usr_spin":
        if not config.get("lucky_spin_enabled", True):
            await query.answer("⚠️ লাকি স্পিন বর্তমানে বন্ধ রয়েছে।", show_alert=True)
            return

        prof = get_user_profile(uid, query.from_user)
        now = time.time()
        last = prof.get("last_spin", 0)

        if now - last < 86400:
            rem_sec = 86400 - (now - last)
            rem_str = format_time_remaining(rem_sec)
            await query.answer(f"⏳ আপনি আজকের ফ্রি স্পিন করেছেন! আর {rem_str} পর চেষ্টা করুন।", show_alert=True)
            return

        won = random.choices([30, 50, 80, 100, 150, 200, 500], weights=[30, 25, 20, 12, 8, 4, 1])[0]
        prof["points"] = prof.get("points", 0) + won
        prof["last_spin"] = now
        save_data()

        await query.answer(f"🎰 লাকি স্পিন! আপনি জিতেছেন +{won} Points! 🏆", show_alert=True)
        text, kb = build_user_dashboard(uid, query.from_user)
        try:
            await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass

    elif data == "usr_shop":
        text, kb = build_shop_view(uid, query.from_user)
        try:
            await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass
        await query.answer()

    elif data == "usr_leaderboard":
        text, kb = build_leaderboard_view(uid)
        try:
            await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass
        await query.answer()

    elif data == "usr_invite":
        bot_info = await bot.get_me()
        text, kb = build_invite_view(uid, bot_info.username)
        try:
            await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass
        await query.answer()

    elif data == "usr_profile":
        text, kb = build_profile_view(uid, query.from_user)
        try:
            await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass
        await query.answer()

    elif data == "usr_l4l":
        text, kb = build_l4l_view(uid)
        try:
            await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass
        await query.answer()

# ==================== ২.৪ টাস্ক এক্সিকিউশন ও ভেরিফিকেশন হ্যান্ডলারস ====================

@dp.callback_query(F.data.startswith("task_"))
async def handle_task_callbacks(query: types.CallbackQuery):
    data = query.data
    uid = query.from_user.id
    prof = get_user_profile(uid, query.from_user)

    if data.startswith("task_done_"):
        await query.answer("✅ আপনি এই টাস্কটি ইতিমধ্যে সম্পন্ন করেছেন!", show_alert=True)
        return

    # ১. অ্যাডস্টারা / ওয়েবসাইট টাস্ক শুরু
    elif data.startswith("task_open_ad_"):
        tid = data.split("_")[3]
        target_task = next((t for t in monetization_tasks if t.get("id") == tid), None)
        if not target_task:
            await query.answer("❌ টাস্কটি পাওয়া যায়নি!", show_alert=True)
            return

        token = str(uuid.uuid4())[:8]
        task_sessions[token] = {
            "user_id": uid,
            "task_id": tid,
            "start_time": time.time(),
            "wait_seconds": target_task.get("wait_seconds", 15),
            "points": target_task.get("points", 100)
        }

        ad_url = target_task.get("url", config.get("ad_link", "https://google.com"))
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌐 মূল ওয়েবসাইটে যান (অপেক্ষা করুন)", url=ad_url)],
            [InlineKeyboardButton(text="✅ ভেরিফাই করুন", callback_data=f"task_claim_ad_{tid}_{token}")],
            [InlineKeyboardButton(text="🔙 টাস্ক তালিকায় ফিরুন", callback_data="usr_tasks")]
        ])
        await query.message.edit_text(
            f"🌐 <b>স্পন্সর ওয়েবসাইট ভিজিট টাস্ক</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"টাস্কের নাম: <b>{target_task.get('title')}</b>\n"
            f"পুরস্কার: <b>+{target_task.get('points')} Points</b>\n\n"
            f"⏱️ <b>নির্দেশনা:</b>\n"
            f"১. নিচের বোতাম চেপে সাইটে প্রবেশ করুন।\n"
            f"২. বাধ্যতামূলকভাবে সাইটে কমপক্ষে <b>{target_task.get('wait_seconds')} সেকেন্ড</b> অবস্থান করুন।\n"
            f"৩. সময় পূর্ণ হলে 'ভেরিফাই করুন' বোতামে চাপুন।",
            parse_mode="HTML",
            reply_markup=kb
        )
        await query.answer()

    # ২. ওয়েবসাইট টাস্ক পয়েন্ট ক্লেইম ভেরিফিকেশন
    elif data.startswith("task_claim_ad_"):
        parts = data.split("_")
        tid = parts[3]
        token = parts[4]
        sess = task_sessions.get(token)

        if not sess or sess["user_id"] != uid:
            await query.answer("❌ সেশন মেয়াদোত্তীর্ণ! পুনরায় টাস্ক শুরু করুন।", show_alert=True)
            return

        elapsed = time.time() - sess["start_time"]
        req_wait = sess["wait_seconds"]

        if elapsed < req_wait:
            rem = int(req_wait - elapsed)
            await query.answer(f"⚠️ আপনি পর্যাপ্ত সময় অবস্থান করেননি! আরও {rem} সেকেন্ড অপেক্ষা করুন।", show_alert=True)
            return

        # সফলতা! পয়েন্ট প্রদান
        if tid not in prof.get("tasks_completed", []):
            prof.setdefault("tasks_completed", []).append(tid)
            prof["points"] = prof.get("points", 0) + sess["points"]
            save_data()

        task_sessions.pop(token, None)
        await query.answer(f"🎉 চমৎকার! টাস্ক সম্পন্ন হয়েছে এবং আপনি +{sess['points']} Points পেয়েছেন!", show_alert=True)
        text, kb = build_tasks_view(uid, query.from_user)
        try:
            await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass

    # ৩. টেলিগ্রাম চ্যানেল জয়েন টাস্ক শুরু
    elif data.startswith("task_open_chan_"):
        tid = data.split("_")[3]
        target_task = next((t for t in monetization_tasks if t.get("id") == tid), None)
        if not target_task:
            await query.answer("❌ টাস্কটি পাওয়া যায়নি!", show_alert=True)
            return

        chan_url = target_task.get("channel_link", "https://t.me")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👉 চ্যানেলে জয়েন করুন", url=chan_url)],
            [InlineKeyboardButton(text="✅ ভেরিফাই করুন", callback_data=f"task_claim_chan_{tid}")],
            [InlineKeyboardButton(text="🔙 টাস্ক তালিকায় ফিরুন", callback_data="usr_tasks")]
        ])
        await query.message.edit_text(
            f"📢 <b>টেলিগ্রাম চ্যানেল জয়েন টাস্ক</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"টাস্কের নাম: <b>{target_task.get('title')}</b>\n"
            f"পুরস্কার: <b>+{target_task.get('points')} Points</b>\n\n"
            f"📌 <b>নির্দেশনা:</b>\n"
            f"১. উপরের বোতাম চেপে আমাদের স্পন্সর চ্যানেলে জয়েন করুন।\n"
            f"২. জয়েন সম্পন্ন হলে 'ভেরিফাই করুন' বোতামে চাপুন।",
            parse_mode="HTML",
            reply_markup=kb
        )
        await query.answer()

    # ৪. টেলিগ্রাম চ্যানেল জয়েন ভেরিফিকেশন
    elif data.startswith("task_claim_chan_"):
        tid = data.split("_")[3]
        target_task = next((t for t in monetization_tasks if t.get("id") == tid), None)
        if not target_task:
            await query.answer("❌ টাস্ক পাওয়া যায়নি!", show_alert=True)
            return

        chan_user = target_task.get("channel_username")
        try:
            member = await bot.get_chat_member(chat_id=chan_user, user_id=uid)
            if member.status in ["member", "administrator", "creator", "restricted"]:
                if tid not in prof.get("tasks_completed", []):
                    prof.setdefault("tasks_completed", []).append(tid)
                    pts = target_task.get("points", 150)
                    prof["points"] = prof.get("points", 0) + pts
                    save_data()
                    await query.answer(f"🎉 সফল! আপনি চ্যানেলে জয়েন করেছেন এবং +{pts} Points পেয়েছেন!", show_alert=True)
                else:
                    await query.answer("আপনি ইতিমধ্যে পয়েন্ট গ্রহণ করেছেন!", show_alert=True)

                text, kb = build_tasks_view(uid, query.from_user)
                try:
                    await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
                except Exception:
                    pass
                return
            else:
                await query.answer("❌ আপনি এখনও চ্যানেলে জয়েন করেননি! দয়া করে জয়েন করে ভেরিফাই চাপুন।", show_alert=True)
        except Exception as e:
            # বট যদি চ্যানেলের মেম্বার স্ট্যাটাস পড়তে না পারে (চ্যানেলে বট অ্যাডমিন না থাকলে), ইউজারের সততাকে সম্মান জানিয়ে পয়েন্ট প্রদান
            if tid not in prof.get("tasks_completed", []):
                prof.setdefault("tasks_completed", []).append(tid)
                pts = target_task.get("points", 150)
                prof["points"] = prof.get("points", 0) + pts
                save_data()
                await query.answer(f"🎉 টাস্ক সম্পন্ন হয়েছে! +{pts} Points যুক্ত করা হয়েছে।", show_alert=True)
                text, kb = build_tasks_view(uid, query.from_user)
                try:
                    await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
                except Exception:
                    pass
            else:
                await query.answer("ইতিমধ্যে সম্পন্ন!", show_alert=True)

# ==================== ২.৫ ভার্চুয়াল শপ ক্রয় ও L4L সাপোর্ট হ্যান্ডলারস ====================

@dp.callback_query(F.data.startswith("buy_pass_"))
async def handle_shop_purchases(query: types.CallbackQuery):
    data = query.data
    uid = query.from_user.id
    prof = get_user_profile(uid, query.from_user)
    pts = prof.get("points", 0)
    now = time.time()

    if data == "buy_pass_pinned":
        cost = config.get("cost_pinned_1h", 2000)
        if pts < cost:
            await query.answer(f"❌ অপর্যাপ্ত পয়েন্ট! আপনার দরকার {cost} Points (আছে {pts})।", show_alert=True)
            return
        prof["points"] -= cost
        prof["pinned_pass_until"] = max(now, prof.get("pinned_pass_until", 0)) + 3600
        save_data()
        await query.answer("🎉 পিন্ড মেসেজ পাস সক্রিয় হয়েছে! পরবর্তী ১ ঘণ্টার মধ্যে শেয়ার করা লিংক গ্রুপে পিন থাকবে।", show_alert=True)
        text, kb = build_shop_view(uid, query.from_user)
        try:
            await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass

    elif data == "buy_pass_unlimited":
        cost = config.get("cost_unlimited_24h", 4000)
        if pts < cost:
            await query.answer(f"❌ অপর্যাপ্ত পয়েন্ট! আপনার দরকার {cost} Points (আছে {pts})।", show_alert=True)
            return
        prof["points"] -= cost
        prof["unlimited_pass_until"] = max(now, prof.get("unlimited_pass_until", 0)) + 86400
        save_data()
        await query.answer("🎉 আনলিমিটেড লিংক পাস সক্রিয় হয়েছে! পরবর্তী ২৪ ঘণ্টা কোনো কুলডাউন ছাড়াই লিংক শেয়ার করতে পারবেন।", show_alert=True)
        text, kb = build_shop_view(uid, query.from_user)
        try:
            await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass

    elif data == "buy_pass_vip":
        cost = config.get("cost_vip_7d", 8000)
        if pts < cost:
            await query.answer(f"❌ অপর্যাপ্ত পয়েন্ট! আপনার দরকার {cost} Points (আছে {pts})।", show_alert=True)
            return
        prof["points"] -= cost
        prof["vip_until"] = max(now, prof.get("vip_until", 0)) + (7 * 86400)
        save_data()
        gid = TARGET_GROUP_ID or config.get("target_group_id")
        if gid:
            asyncio.create_task(grant_user_verification(gid, query.from_user))
        await query.answer("👑 অভিনন্দন! আপনি ৭ দিনের VIP মেম্বারশিপ অর্জন করেছেন! আপনার নামের পাশে গোল্ডেন ভিআইপি টাইটেল যুক্ত হয়েছে।", show_alert=True)
        text, kb = build_shop_view(uid, query.from_user)
        try:
            await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass

@dp.callback_query(F.data.startswith("l4l_sup_"))
async def handle_l4l_support(query: types.CallbackQuery):
    uid = query.from_user.id
    prof = get_user_profile(uid, query.from_user)
    parts = query.data.split("_")
    target_uid = int(parts[2])

    if target_uid == uid:
        await query.answer("নিজের লিংক নিজে সাপোর্ট করা যাবে না!", show_alert=True)
        return

    pts_gain = config.get("points_per_l4l", 15)
    prof["points"] = prof.get("points", 0) + pts_gain
    prof["l4l_credits"] = prof.get("l4l_credits", 0) + 1
    save_data()

    await query.answer(f"🤝 লিংকে সাপোর্ট দেওয়ার জন্য আপনি পেয়েছেন +{pts_gain} Points!", show_alert=True)
    text, kb = build_l4l_view(uid)
    try:
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        pass

@dp.message(Command("reset_verify"))
@dp.message(Command("reset_users"))
async def cmd_reset_verify(message: types.Message):
    """নিরাপদ শর্টকাট: শুধুমাত্র ইউজারদের ভেরিফিকেশন রিসেট হবে, কোনো সেটিংস/টাইমার রিসেট হবে না"""
    if message.from_user.id != ADMIN_ID:
        return
    gid = TARGET_GROUP_ID or config.get("target_group_id")
    if gid:
        asyncio.create_task(remove_all_verified_badges(gid))
    config["current_version"] = config.get("current_version", 1) + 1
    verified_users.clear()
    save_data()
    await message.answer(
        f"♻️ <b>ইউজার ভেরিফিকেশন সফলভাবে রিসেট করা হয়েছে!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"• সমস্ত সংরক্ষিত সেটিংস, টাইমার ও অ্যাড লিংক <b>সম্পূর্ণ অক্ষত</b> আছে।\n"
        f"• মেম্বারদের নামের পাশের ভেরিফাই ব্যাজ রিসেট করা হয়েছে।\n"
        f"• বর্তমান সিকিউরিটি ভার্সন: <code>v{config['current_version']}</code>\n\n"
        f"এখন যেকোনো আইডি দিয়ে গ্রুপে লিংক পোস্ট করে ভেরিফিকেশন টেস্ট করতে পারবেন।",
        parse_mode="HTML"
    )

@dp.message(Command("settings"))
async def cmd_settings(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    text, kb = build_all_settings_view()
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

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
    w = await message.reply("🧹 আপনি কতক্ষণের পূর্বের মেসেজ ডিলিট করতে চান নির্বাচন করুন:", reply_markup=kb)
    asyncio.create_task(auto_delete(w, 30))

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
        text=f"✅ <b>সাফাই সম্পন্ন!</b> গত <b>{hours} ঘণ্টার</b> মোট <b>{count}টি</b> মেসেজ মুছে দেওয়া হয়েছে।",
        parse_mode="HTML"
    )
    asyncio.create_task(auto_delete(done_msg, 15))

# ==================== ৩. মূল অ্যাডমিন প্যানেল ভিউ ও বিল্ডার ====================

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
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

def build_admin_main_view():
    now = time.time()
    rem_sec = max(0, shutdown_state["active_expiry"] - now)
    rem_str = format_time_remaining(rem_sec)
    status_badge = "🔴 শাটডাউন (লক)" if shutdown_state["is_shutdown"] else f"🟢 সক্রিয় ({rem_str} বাকি)"

    mode_label = "চ্যানেল জয়েন রিকোয়েস্ট" if config["mode"] == "join_request" else "ডাইরেক্ট অ্যাড লিংক"

    text = (
        "👑 <b>পাগলা বাবা বট — মূল কন্ট্রোল সেন্টার (A to Z)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <b>গ্রুপ স্ট্যাটাস:</b> <code>{status_badge}</code>\n"
        f"🔹 <b>বর্তমান মোড:</b> <code>{mode_label}</code>\n"
        f"🔹 <b>টার্গেট চ্যানেল:</b> <code>{config['target_channel']}</code>\n"
        f"🔹 <b>ডাইরেক্ট অ্যাড লিংক:</b> <code>{config['ad_link'][:35]}...</code>\n"
        f"🔹 <b>ভেরিফিকেশন ফিল্টার:</b> <code>{'🟢 চালু (ON)' if config['require_verification'] else '🔴 বন্ধ (OFF)'}</code>\n"
        f"🔹 <b>নন-টেলিগ্রাম লিংক ডিলিট:</b> <code>{'🟢 চালু (ON)' if config['allow_only_tg_links'] else '🔴 বন্ধ (OFF)'}</code>\n"
        f"🔹 <b>সাধারণ মেসেজ ডিলিট:</b> <code>{'🟢 চালু (ON)' if config['delete_non_links'] else '🔴 বন্ধ (OFF)'}</code>\n"
        f"🔹 <b>অটো জয়েন রিকোয়েস্ট:</b> <code>{'🟢 চালু (ON)' if config.get('auto_accept_join_requests', False) else '🔴 বন্ধ (OFF)'}</code>\n"
        f"🔹 <b>কমপ্যাক্ট লিংক (পাবলিক গ্রুপ):</b> <code>{'🟢 চালু' if config.get('disable_link_previews', True) else '🔴 বন্ধ'}</code>\n"
        f"🔹 <b>অ্যাডমিন টেস্ট ফিল্টার:</b> <code>{'🟢 চালু (ON)' if config.get('filter_admins', False) else '🔴 বন্ধ (OFF)'}</code>\n"
        f"👥 <b>পরিচিত সদস্য:</b> <code>{len(all_known_users)} জন</code> | <b>ভেরিফাইড:</b> <code>{len(verified_users)} জন</code>\n\n"
        "👇 <i>যেকোনো শাখা বা সেটিংস নিয়ন্ত্রণ করতে নিচের বোতামে চাপুন:</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🤝 অটো জয়েন রিকোয়েস্ট", callback_data="br_join_req"),
            InlineKeyboardButton(text="🌐 পাবলিক গ্রুপ সিকিউরিটি", callback_data="br_public_group")
        ],
        [
            InlineKeyboardButton(text="🎯 চ্যানেল ও রিকোয়েস্ট", callback_data="br_channel"),
            InlineKeyboardButton(text="🌐 ডাইরেক্ট অ্যাড লিংক", callback_data="br_ad")
        ],
        [
            InlineKeyboardButton(text="⏱️ টাইমার ও সময়সীমা", callback_data="br_timers"),
            InlineKeyboardButton(text="📝 মেসেজ ও নোটিশ টেক্সট", callback_data="br_messages")
        ],
        [
            InlineKeyboardButton(text="🔘 বাটন টেক্সট ও লিংক", callback_data="br_buttons"),
            InlineKeyboardButton(text="🛡️ ফিল্টারিং রুলস (ON/OFF)", callback_data="br_filters")
        ],
        [
            InlineKeyboardButton(text="💬 স্বাগতম (Welcome) শাখা", callback_data="br_welcome"),
            InlineKeyboardButton(text="📢 অটো প্রোমোশন শাখা", callback_data="br_promo")
        ],
        [
            InlineKeyboardButton(text="⏱️ ২৪ ঘণ্টা শাটডাউন শাখা", callback_data="br_shutdown"),
            InlineKeyboardButton(text="👥 ইউজার ও ভেরিফিকেশন", callback_data="br_users")
        ],
        [
            InlineKeyboardButton(text="👑 নামের পাশে ভেরিফাই ব্যাজ", callback_data="br_badge"),
            InlineKeyboardButton(text="🔄 মোড পরিবর্তন (Toggle)", callback_data="act_toggle_mode")
        ],
        [
            InlineKeyboardButton(text="🎮 পয়েন্ট ও গ্যামিফিকেশন", callback_data="br_gamification"),
            InlineKeyboardButton(text="💰 টাস্ক ও মনিটাইজেশন হাব", callback_data="br_monetization")
        ],
        [
            InlineKeyboardButton(text="📋 সকল সেটিংস দেখুন", callback_data="br_view_all"),
            InlineKeyboardButton(text="♻️ রিসেট অল ভেরিফিকেশন", callback_data="br_confirm_reset_verif")
        ],
        [
            InlineKeyboardButton(text="❌ প্যানেল বন্ধ করুন", callback_data="act_close_panel")
        ]
    ])
    return text, kb

def build_all_settings_view():
    text = (
        "📋 <b>বর্তমান সম্পূর্ণ সিস্টেম সেটিংস রিপোর্ট (A to Z)</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🔹 <b>কার্যকারী মোড:</b> <code>{config['mode']}</code>\n"
        f"🔹 <b>টার্গেট চ্যানেল:</b> <code>{config['target_channel']}</code>\n"
        f"🔹 <b>রিকোয়েস্ট লিংক:</b> <code>{config['target_channel_link']}</code>\n"
        f"🔹 <b>ডাইরেক্ট অ্যাড লিংক:</b> <code>{config['ad_link']}</code>\n\n"
        f"👑 <b>ভেরিফাই ব্যাজ ও পদবি:</b>\n"
        f"• নামের পাশে ব্যাজ: <code>{'চালু' if config.get('enable_admin_badge', True) else 'বন্ধ'}</code>\n"
        f"• ব্যাজের পদবি/টাইটেল: <code>{config.get('badge_title', '✓ Verified')}</code>\n"
        f"• লিংক রিঅ্যাকশন: <code>{'চালু' if config.get('badge_reaction_enabled', True) else 'বন্ধ'} ({config.get('badge_reaction_emoji', '⚡')})</code>\n\n"
        f"⏱️ <b>সকল টাইমার ও সময়সীমা:</b>\n"
        f"• অ্যাড অপেক্ষার সময়: <code>{config['ad_wait_seconds']} সেকেন্ড</code>\n"
        f"• ভেরিফিকেশন কার্ড ডিলিট: <code>{config['verify_card_delete_sec']} সেকেন্ড</code>\n"
        f"• নন-লিংক সতর্কবার্তা ডিলিট: <code>{config['non_link_warn_delete_sec']} সেকেন্ড</code>\n"
        f"• অন্য লিংক সতর্কবার্তা ডিলিট: <code>{config['other_link_warn_delete_sec']} সেকেন্ড</code>\n"
        f"• ভেরিফিকেশন সফল বার্তা ডিলিট: <code>{config['verify_success_delete_sec']} সেকেন্ড</code>\n"
        f"• ওয়েলকাম বার্তা ডিলিট: <code>{config['welcome_delete_sec']} সেকেন্ড</code>\n"
        f"• অটো প্রোমো প্রচার ব্যবধান: <code>{config['broadcast_interval_mins']} মিনিট</code>\n"
        f"• প্রোমো মেসেজ ডিলিট: <code>{config['promo_delete_sec']} সেকেন্ড</code>\n"
        f"• শাটডাউন মেয়াদ: <code>{config['shutdown_duration_hours']} ঘণ্টা</code>\n"
        f"• রিনিউ প্রম্পট ব্যবধান: <code>{config['renew_prompt_hours']} ঘণ্টা</code>\n\n"
        f"🛡️ <b>ফিল্টারিং সুইচসমূহ:</b>\n"
        f"• ভেরিফিকেশন বাধ্যবাধকতা: <code>{'চালু' if config['require_verification'] else 'বন্ধ'}</code>\n"
        f"• শুধুমাত্র টেলিগ্রাম লিংক: <code>{'চালু' if config['allow_only_tg_links'] else 'বন্ধ'}</code>\n"
        f"• নন-লিংক মেসেজ ডিলিট: <code>{'চালু' if config['delete_non_links'] else 'বন্ধ'}</code>\n"
        f"• সার্ভিস মেসেজ ডিলিট: <code>{'চালু' if config['clean_service_msgs'] else 'বন্ধ'}</code>\n"
        f"• স্বাগতম বার্তা: <code>{'চালু' if config['welcome_enabled'] else 'বন্ধ'}</code>\n"
        f"• স্বাগতম বাটনে ভেরিফাই: <code>{'চালু' if config['welcome_verify_btn'] else 'বন্ধ'}</code>\n"
        f"• অটো প্রোমো ব্রডকাস্ট: <code>{'চালু' if config['promo_enabled'] else 'বন্ধ'}</code>\n"
        f"• অ্যাডমিন টেস্ট ফিল্টার: <code>{'চালু' if config.get('filter_admins', False) else 'বন্ধ'}</code>\n\n"
        f"👥 <b>ইউজার ডাটা:</b>\n"
        f"• মোট মেম্বার: <code>{len(all_known_users)} জন</code> | ভেরিফাইড: <code>{len(verified_users)} জন</code>\n"
        f"• সিকিউরিটি ভার্সন: <code>v{config['current_version']}</code>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 মূল মেনুতে ফিরুন", callback_data="br_main")]
    ])
    return text, kb

# ==================== ৪. শাখা ভিত্তিক নেভিগেশন ও বাটন হ্যান্ডলার ====================

@dp.callback_query(F.data.startswith("br_"))
@dp.callback_query(F.data.startswith("act_"))
@dp.callback_query(F.data.startswith("tog_"))
@dp.callback_query(F.data.startswith("edit_"))
@dp.callback_query(F.data.startswith("renew_"))
@dp.callback_query(F.data.startswith("intv_"))
async def handle_admin_branches(query: types.CallbackQuery):
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ আপনি এই বটের অ্যাডমিন নন!", show_alert=True)
        return

    data = query.data

    # --- রিনিউয়াল বোতাম হ্যান্ডলার ---
    if data == "renew_confirm":
        await trigger_group_revive()
        dur = config.get("shutdown_duration_hours", 24)
        await query.answer(f"✅ সফল! এখন থেকে নতুন করে {dur} ঘণ্টা সময় শুরু হলো।", show_alert=True)
        try:
            await query.message.edit_text(
                f"✅ <b>গ্রুপ সফলভাবে রিনিউ করা হয়েছে!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"এই মুহূর্ত থেকে পরবর্তী {dur} ঘণ্টার জন্য গ্রুপ ও বট পুরোদমে সচল থাকবে।\n"
                f"⏳ মেয়াদ শেষ হবে: {time.strftime('%I:%M %p, %d %b %Y', time.localtime(shutdown_state['active_expiry']))}",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    elif data == "renew_cancel":
        now = time.time()
        rem_sec = max(0, shutdown_state["active_expiry"] - now)
        rem_str = format_time_remaining(rem_sec)
        await query.answer(f"বাতিল করা হয়েছে। পূর্বের অবশিষ্ট সময় {rem_str} গ্রুপ চালু থাকবে।", show_alert=True)
        try:
            await query.message.edit_text(
                f"❌ <b>রিনিউ অনুরোধ বাতিল করা হয়েছে!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"পূর্বের সময় গণনা অব্যাহত থাকবে।\n"
                f"⏳ অবশিষ্ট সময়: <code>{rem_str}</code> পর গ্রুপ শাটডাউন হবে।",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    # --- মূল মেনুতে ফেরা ---
    elif data == "br_main":
        text, kb = build_admin_main_view()
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer()
        return

    # --- সমস্ত সেটিংস এক নজরে দেখা ---
    elif data == "br_view_all":
        text, kb = build_all_settings_view()
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer()
        return

    # --- প্যানেল বন্ধ করা ---
    elif data == "act_close_panel":
        await query.message.delete()
        await query.answer("প্যানেল বন্ধ করা হয়েছে")
        return

    # --- মোড টগল (Join Request <-> Ad Link) ---
    elif data == "act_toggle_mode":
        if config["mode"] == "both":
            config["mode"] = "join_request"
        elif config["mode"] == "join_request":
            config["mode"] = "ad_link"
        else:
            config["mode"] = "both"
        save_data()
        mode_label = "চ্যানেল জয়েন রিকোয়েস্ট" if config["mode"] == "join_request" else "ডাইরেক্ট অ্যাড লিংক"
        await query.answer(f"✅ মোড পরিবর্তন সম্পন্ন: {mode_label}", show_alert=True)
        text, kb = build_admin_main_view()
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        return

    # --- নিরাপদ ভেরিফিকেশন রিসেট কনফার্মেশন স্ক্রিন ---
    elif data == "br_confirm_reset_verif":
        text = (
            "⚠️ <b>নিশ্চিতকরণ: আপনি কি সমস্ত মেম্বারদের ভেরিফিকেশন রিসেট করতে চান?</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💡 <b>সম্পূর্ণ নিরাপদ সুরক্ষা গ্যারান্টি:</b>\n"
            "• আপনার কোনো সেটিংস বা কনফিগারেশন রিসেট <b>হবে না</b>।\n"
            "• আপনার ডাইরেক্ট অ্যাড লিংক ও চ্যানেলের লিংক <b>১০০% অক্ষত</b> থাকবে।\n"
            "• আপনার সেট করা সকল টাইমার যেমন আছে তেমনই থাকবে।\n"
            "• শুধুমাত্র সমস্ত গ্রুপের মেম্বারদের আন-ভেরিফাইড করা হবে, যাতে তাদের নতুন করে ভেরিফাই হতে হয়।\n\n"
            "আপনি কি নিশ্চিত?"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ হ্যাঁ, মেম্বারদের ভেরিফিকেশন রিসেট করুন", callback_data="act_do_reset_verif")],
            [InlineKeyboardButton(text="❌ বাতিল করুন (মূল মেনুতে ফেরত)", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer()
        return

    # --- প্রকৃত ভেরিফিকেশন রিসেট এক্সিকিউশন ---
    elif data == "act_do_reset_verif":
        gid = TARGET_GROUP_ID or config.get("target_group_id")
        if gid:
            asyncio.create_task(remove_all_verified_badges(gid))
        config["current_version"] = config.get("current_version", 1) + 1
        verified_users.clear()
        save_data()
        await query.answer("♻️ সমস্ত মেম্বারদের ভেরিফিকেশন ও নামের পাশের ব্যাজ রিসেট করা হয়েছে! সেটিংস ও লিংক সম্পূর্ণ অক্ষত রয়েছে।", show_alert=True)
        text, kb = build_admin_main_view()
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        return

    # --- নামের পাশে ভেরিফাই ব্যাজ শাখা ---
    elif data == "br_badge":
        badge_on = config.get("enable_admin_badge", True)
        rx_on = config.get("badge_reaction_enabled", True)
        title = config.get("badge_title", "✓ Verified")
        rx_emoji = config.get("badge_reaction_emoji", "⚡")

        text = (
            "👑 <b>নামের পাশে ভেরিফাই ব্যাজ ও পদবি শাখা</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• ভেরিফাই ব্যাজ (কাস্টম অ্যাডমিন টাইটেল): <code>{'🟢 চালু (ON)' if badge_on else '🔴 বন্ধ (OFF)'}</code>\n"
            f"• ব্যাজের নাম / পদবি: <code>{title}</code>\n"
            f"• লিংক শেয়ারে ভেরিফাইড রিঅ্যাকশন: <code>{'🟢 চালু (ON)' if rx_on else '🔴 বন্ধ (OFF)'}</code>\n"
            f"• রিঅ্যাকশন ইমোজি: <code>{rx_emoji}</code>\n\n"
            "💡 <b>এটি কীভাবে কাজ করে?</b>\n"
            "১. মেম্বার যখন ভেরিফাই করবে, বট তাকে টেলিগ্রামের অফিসিয়াল কাস্টম টাইটেল দিয়ে এই ব্যাজ প্রদান করবে।\n"
            f"২. এর ফলে সে গ্রুপে যেকোনো চ্যাট বা লিংক শেয়ার করলে তার নামের পাশেই <b>[{title}]</b> ব্যাজটি গ্রুপের সবাই দেখতে পাবে!\n"
            "৩. যারা ভেরিফাই করবে না তাদের নামের পাশে এই ব্যাজ থাকবে না।\n"
            "৪. রিসেট অল ভেরিফিকেশন দিলে স্বয়ংক্রিয়ভাবে সবার এই ব্যাজ মুছে যাবে।\n\n"
            "⚠️ <i>জরুরি: বটকে অবশ্যই গ্রুপে 'অ্যাডমিন যোগ করার ক্ষমতা' (Promote Members) দিতে হবে।</i>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{'🔴 ব্যাজ বন্ধ করুন' if badge_on else '🟢 ব্যাজ চালু করুন'}",
                callback_data="tog_badge"
            )],
            [InlineKeyboardButton(text="✏️ ব্যাজের নাম পরিবর্তন (Title)", callback_data="edit_badge_title")],
            [InlineKeyboardButton(
                text=f"{'🔴 রিঅ্যাকশন বন্ধ করুন' if rx_on else '🟢 রিঅ্যাকশন চালু করুন'}",
                callback_data="tog_badge_reaction"
            )],
            [InlineKeyboardButton(text="✏️ রিঅ্যাকশন ইমোজি পরিবর্তন", callback_data="edit_badge_reaction_emoji")],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer()
        return

    elif data == "tog_badge":
        config["enable_admin_badge"] = not config.get("enable_admin_badge", True)
        save_data()
        await query.answer(f"ভেরিফাই ব্যাজ: {'চালু' if config['enable_admin_badge'] else 'বন্ধ'}")
        query.data = "br_badge"
        await handle_admin_branches(query)
        return

    elif data == "tog_badge_reaction":
        config["badge_reaction_enabled"] = not config.get("badge_reaction_enabled", True)
        save_data()
        await query.answer(f"লিংক রিঅ্যাকশন: {'চালু' if config['badge_reaction_enabled'] else 'বন্ধ'}")
        query.data = "br_badge"
        await handle_admin_branches(query)
        return

    # --- গ্যামিফিকেশন ও পয়েন্ট শাখা ---
    elif data == "br_gamification":
        g_on = config.get("gamification_enabled", True)
        d_on = config.get("daily_bonus_enabled", True)
        s_on = config.get("lucky_spin_enabled", True)
        st_on = config.get("store_enabled", True)
        l_on = config.get("l4l_enabled", True)
        del_hrs = config.get("auto_delete_links_hours", 0)

        text = (
            "🎮 <b>গ্যামিফিকেশন ও রিওয়ার্ড কন্ট্রোল হাব</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• গ্যামিফিকেশন সিস্টেম: <code>{'🟢 চালু (ON)' if g_on else '🔴 বন্ধ (OFF)'}</code>\n"
            f"• প্রতি লিংকে পয়েন্ট: <code>+{config.get('points_per_link', 10)} pts</code>\n"
            f"• প্রতি রেফারে পয়েন্ট: <code>+{config.get('points_per_referral', 200)} pts</code>\n"
            f"• ওয়েলকাম বোনাস: <code>+{config.get('points_welcome_bonus', 50)} pts</code>\n"
            f"• ডেইলি বোনাস সিস্টেম: <code>{'🟢 চালু (ON)' if d_on else '🔴 বন্ধ (OFF)'}</code> (মূল: {config.get('points_daily_base', 100)} pts)\n"
            f"• ডেইলি স্ট্রিক মাল্টিপ্লায়ার: <code>{config.get('points_daily_streak_mult', 2.0)}x সর্বোচ্চ</code>\n"
            f"• লাকি স্পিন (Wheel): <code>{'🟢 চালু (ON)' if s_on else '🔴 বন্ধ (OFF)'}</code>\n"
            f"• ভার্চুয়াল রিডিম শপ: <code>{'🟢 চালু (ON)' if st_on else '🔴 বন্ধ (OFF)'}</code>\n"
            f"• L4L (সাপোর্ট ফর লিংক): <code>{'🟢 চালু (ON)' if l_on else '🔴 বন্ধ (OFF)'}</code>\n"
            f"• স্মার্ট সেলফ-ডিলিট টাইমার: <code>{'বন্ধ (০)' if del_hrs == 0 else str(del_hrs) + ' ঘণ্টা'}</code>\n\n"
            "👇 <i>যেকোনো সেটিংস পরিবর্তন করতে বোতাম চাপুন:</i>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=f"{'🔴 গ্যামিফিকেশন বন্ধ' if g_on else '🟢 গ্যামিফিকেশন চালু'}", callback_data="tog_gamification"),
                InlineKeyboardButton(text=f"{'🔴 ডেইলি বোনাস বন্ধ' if d_on else '🟢 ডেইলি বোনাস চালু'}", callback_data="tog_daily_bonus")
            ],
            [
                InlineKeyboardButton(text=f"{'🔴 লাকি স্পিন বন্ধ' if s_on else '🟢 লাকি স্পিন চালু'}", callback_data="tog_lucky_spin"),
                InlineKeyboardButton(text=f"{'🔴 ভার্চুয়াল শপ বন্ধ' if st_on else '🟢 ভার্চুয়াল শপ চালু'}", callback_data="tog_store")
            ],
            [
                InlineKeyboardButton(text=f"{'🔴 L4L বন্ধ' if l_on else '🟢 L4L চালু'}", callback_data="tog_l4l"),
                InlineKeyboardButton(text="✏️ অটো ডিলিট সময় (ঘণ্টা)", callback_data="edit_auto_delete_links_hours")
            ],
            [
                InlineKeyboardButton(text="✏️ লিংকে প্রাপ্ত পয়েন্ট", callback_data="edit_points_per_link"),
                InlineKeyboardButton(text="✏️ রেফারে প্রাপ্ত পয়েন্ট", callback_data="edit_points_per_referral")
            ],
            [
                InlineKeyboardButton(text="✏️ ডেইলি বেস পয়েন্ট", callback_data="edit_points_daily_base"),
                InlineKeyboardButton(text="✏️ ওয়েলকাম পয়েন্ট", callback_data="edit_points_welcome_bonus")
            ],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer()
        return

    elif data == "tog_gamification":
        config["gamification_enabled"] = not config.get("gamification_enabled", True)
        save_data()
        await query.answer(f"গ্যামিফিকেশন: {'চালু' if config['gamification_enabled'] else 'বন্ধ'}")
        query.data = "br_gamification"
        await handle_admin_branches(query)
        return

    elif data == "tog_daily_bonus":
        config["daily_bonus_enabled"] = not config.get("daily_bonus_enabled", True)
        save_data()
        await query.answer(f"ডেইলি বোনাস: {'চালু' if config['daily_bonus_enabled'] else 'বন্ধ'}")
        query.data = "br_gamification"
        await handle_admin_branches(query)
        return

    elif data == "tog_lucky_spin":
        config["lucky_spin_enabled"] = not config.get("lucky_spin_enabled", True)
        save_data()
        await query.answer(f"লাকি স্পিন: {'চালু' if config['lucky_spin_enabled'] else 'বন্ধ'}")
        query.data = "br_gamification"
        await handle_admin_branches(query)
        return

    elif data == "tog_store":
        config["store_enabled"] = not config.get("store_enabled", True)
        save_data()
        await query.answer(f"ভার্চুয়াল শপ: {'চালু' if config['store_enabled'] else 'বন্ধ'}")
        query.data = "br_gamification"
        await handle_admin_branches(query)
        return

    elif data == "tog_l4l":
        config["l4l_enabled"] = not config.get("l4l_enabled", True)
        save_data()
        await query.answer(f"L4L সিস্টেম: {'চালু' if config['l4l_enabled'] else 'বন্ধ'}")
        query.data = "br_gamification"
        await handle_admin_branches(query)
        return

    # --- মনিটাইজেশন ও টাস্ক হাব শাখা ---
    elif data == "br_monetization":
        ad_count = sum(1 for t in monetization_tasks if t.get("type") == "ad_wait")
        chan_count = sum(1 for t in monetization_tasks if t.get("type") == "channel_join")
        active_count = sum(1 for t in monetization_tasks if t.get("active", True))

        t_lines = []
        for i, t in enumerate(monetization_tasks, 1):
            st = "🟢" if t.get("active", True) else "🔴"
            tp = "🌐 Adsterra/Web" if t.get("type") == "ad_wait" else "📢 TG Channel"
            t_lines.append(f"{i}. {st} <b>{html.escape(t.get('title', 'Task'))}</b> ({tp}) — <code>+{t.get('points')} pts</code>")
        tasks_display = "\n".join(t_lines) if t_lines else "<i>কোনো টাস্ক তৈরি করা হয়নি।</i>"

        text = (
            "💰 <b>অ্যাড ও টাস্ক মনিটাইজেশন কন্ট্রোল হাব</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>মোট সক্রিয় টাস্ক:</b> <code>{active_count}/{len(monetization_tasks)} টি</code>\n"
            f"🌐 <b>অ্যাডস্টারা / ডাইরেক্ট লিংক টাস্ক:</b> <code>{ad_count} টি</code>\n"
            f"📢 <b>টেলিগ্রাম চ্যানেল জয়েন টাস্ক:</b> <code>{chan_count} টি</code>\n\n"
            f"📋 <b>বিদ্যমান টাস্ক তালিকা:</b>\n{tasks_display}\n\n"
            "💡 <i>ইউজাররা এই টাস্কগুলো সম্পন্ন করে পয়েন্ট পাবে, আর আপনি প্রতিটি ক্লিকে ও চ্যানেলে প্রফিট/গ্রোথ পাবেন!</i>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ নতুন ডাইরেক্ট অ্যাড টাস্ক", callback_data="act_add_task_ad"),
                InlineKeyboardButton(text="➕ নতুন চ্যানেল টাস্ক", callback_data="act_add_task_chan")
            ],
            [
                InlineKeyboardButton(text="🔄 টাস্ক সচল/অচল ও ডিলিট", callback_data="br_toggle_tasks"),
                InlineKeyboardButton(text="📢 গ্রুপে লিডারবোর্ড প্রকাশ", callback_data="act_announce_leaderboard")
            ],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer()
        return

    # --- টাস্ক অন/অফ ও ম্যানেজমেন্ট শাখা ---
    elif data == "br_toggle_tasks":
        if not monetization_tasks:
            await query.answer("কোনো টাস্ক নেই!", show_alert=True)
            return

        kb = []
        for t in monetization_tasks:
            tid = t.get("id")
            title = t.get("title")
            st_text = "🟢 সক্রিয়" if t.get("active", True) else "🔴 বন্ধ"
            kb.append([
                InlineKeyboardButton(text=f"{st_text}: {title}", callback_data=f"tog_task_act_{tid}"),
                InlineKeyboardButton(text="🗑️ ডিলিট", callback_data=f"del_task_{tid}")
            ])
        kb.append([InlineKeyboardButton(text="🔙 টাস্ক হাবে ফিরুন", callback_data="br_monetization")])

        await query.message.edit_text(
            "⚙️ <b>টাস্ক সক্রিয়/নিষ্ক্রিয় ও মুছে ফেলার প্যানেল</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "যেকোনো টাস্ক বন্ধ করতে বা মুছে ফেলতে নিচের বোতামে চাপুন:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )
        await query.answer()
        return

    elif data.startswith("tog_task_act_"):
        tid = data.split("_")[3]
        target_task = next((t for t in monetization_tasks if t.get("id") == tid), None)
        if target_task:
            target_task["active"] = not target_task.get("active", True)
            save_data()
            await query.answer(f"টাস্ক স্ট্যাটাস: {'সক্রিয়' if target_task['active'] else 'নিষ্ক্রিয়'}")
            query.data = "br_toggle_tasks"
            await handle_admin_branches(query)
        return

    elif data.startswith("del_task_"):
        tid = data.split("_")[2]
        monetization_tasks[:] = [t for t in monetization_tasks if t.get("id") != tid]
        save_data()
        await query.answer("🗑️ টাস্ক মুছে ফেলা হয়েছে!", show_alert=True)
        query.data = "br_toggle_tasks"
        await handle_admin_branches(query)
        return

    # --- গ্রুপে সাপ্তাহিক লিডারবোর্ড ঘোষণা ও পিন ---
    elif data == "act_announce_leaderboard":
        gid = TARGET_GROUP_ID or config.get("target_group_id")
        if not gid:
            await query.answer("❌ টার্গেট গ্রুপ আইডি সেট করা নেই!", show_alert=True)
            return

        sorted_users = sorted(
            user_gamification.items(),
            key=lambda x: x[1].get("points", 0),
            reverse=True
        )
        top_5 = sorted_users[:5]
        medals = ["🥇 ১ম স্থান", "🥈 ২য় স্থান", "🥉 ৩য় স্থান", "4️⃣ ৪র্থ স্থান", "5️⃣ ৫ম স্থান"]

        lines = []
        for idx, (uid_s, udata) in enumerate(top_5):
            uname = udata.get("name", "Promoter")
            pts = udata.get("points", 0)
            sh = udata.get("links_shared_count", 0)
            lines.append(f"{medals[idx]}: <b>{html.escape(uname)}</b>\n   └ <code>{pts} Points</code> | লিংক শেয়ার: <code>{sh} টি</code>")

        board_str = "\n\n".join(lines) if lines else "<i>এখনও কোনো প্রমোটার তালিকাভুক্ত হয়নি।</i>"

        ann_text = (
            "👑 <b>সাপ্তাহিক টপ প্রমোটার ও মেম্বার অ্যাওয়ার্ড ঘোষণা!</b> 🏆\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "অভিনন্দন আমাদের গ্রুপের সেরা পারফর্মারদের! তাদের অক্লান্ত লিংক শেয়ারিং ও সক্রিয়তার জন্য গ্রুপের পক্ষ থেকে স্যালুট:\n\n"
            f"{board_str}\n\n"
            "🎁 <b>সেরা প্রমোটারদের বিশেষ উপহার:</b>\n"
            "টপ স্থানাধিকারীদের পোস্ট স্বয়ংক্রিয়ভাবে ভিআইপি ব্যাজ ও বিশেষ পিন সম্মাননা পাবে!\n\n"
            "👉 <i>আপনিও গ্রুপে নিয়মিত লিংক শেয়ার করুন, টাস্ক পূরণ করুন ও লিডারবোর্ডে উঠে আসুন!</i>"
        )
        try:
            bot_info = await bot.get_me()
            post_m = await bot.send_message(
                chat_id=gid,
                text=ann_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🌟 আমিও পয়েন্ট আয় করবো", url=f"https://t.me/{bot_info.username}?start=earn")]
                ])
            )
            try:
                await bot.pin_chat_message(chat_id=gid, message_id=post_m.message_id)
            except Exception:
                pass
            await query.answer("🎉 গ্রুপে সাপ্তাহিক লিডারবোর্ড ঘোষণা পাঠানো এবং পিন করা হয়েছে!", show_alert=True)
        except Exception as e:
            await query.answer(f"❌ ঘোষণা পাঠাতে সমস্যা: {str(e)[:40]}", show_alert=True)
        return

    # --- ১. চ্যানেল ও রিকোয়েস্ট শাখা ---
    elif data == "br_channel":
        text = (
            "🎯 <b>চ্যানেল ও জয়েন রিকোয়েস্ট শাখা</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• টার্গেট চ্যানেল ইউজারনেম: <code>{config['target_channel']}</code>\n"
            f"• চ্যানেল জয়েন রিকোয়েস্ট লিংক: <code>{config['target_channel_link']}</code>\n"
            f"• জয়েন রিকোয়েস্ট বাটন টেক্সট: <code>{config['btn_join_req']}</code>\n"
            f"• ভেরিফাই বাটন টেক্সট: <code>{config['btn_join_verify']}</code>\n"
            f"• বর্তমান কার্যকারী মোড: <code>{config['mode']}</code>\n\n"
            "কী পরিবর্তন করতে চান নিচের বোতামে চাপুন:"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ চ্যানেল ইউজারনেম পরিবর্তন", callback_data="edit_target_channel")],
            [InlineKeyboardButton(text="✏️ চ্যানেল রিকোয়েস্ট লিংক পরিবর্তন", callback_data="edit_target_channel_link")],
            [InlineKeyboardButton(text="✏️ জয়েন বাটন নাম পরিবর্তন", callback_data="edit_btn_join_req")],
            [InlineKeyboardButton(text="✏️ ভেরিফাই বাটন নাম পরিবর্তন", callback_data="edit_btn_join_verify")],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer()

    # --- ২. ডাইরেক্ট অ্যাড শাখা ---
    elif data == "br_ad":
        text = (
            "🌐 <b>ডাইরেক্ট অ্যাড ও ট্রাফিক শাখা</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• অ্যাড ইউআরএল: <code>{config['ad_link']}</code>\n"
            f"• অপেক্ষার সময়: <code>{config['ad_wait_seconds']} সেকেন্ড</code>\n"
            f"• ভিজিট বাটন নাম: <code>{config['btn_ad_visit']}</code>\n"
            f"• ভেরিফাই বাটন নাম: <code>{config['btn_ad_verify']}</code>\n\n"
            "কী পরিবর্তন করতে চান:"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ অ্যাড লিংক পরিবর্তন", callback_data="edit_ad_link")],
            [InlineKeyboardButton(text="⏱️ অপেক্ষার সময় পরিবর্তন (সেকেন্ড)", callback_data="edit_ad_wait_seconds")],
            [InlineKeyboardButton(text="✏️ ভিজিট বাটন নাম পরিবর্তন", callback_data="edit_btn_ad_visit")],
            [InlineKeyboardButton(text="✏️ ভেরিফাই বাটন নাম পরিবর্তন", callback_data="edit_btn_ad_verify")],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer()

    # --- ৩. টাইমার ও সময়সীমা কন্ট্রোল শাখা (A to Z) ---
    elif data == "br_timers":
        text = (
            "⏱️ <b>সকল টাইমার ও সময়সীমা কন্ট্রোল শাখা</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"1️⃣ অ্যাড ওয়েবসাইটে অবস্থান: <code>{config['ad_wait_seconds']} সেকেন্ড</code>\n"
            f"2️⃣ ভেরিফিকেশন কার্ড ডিলিট: <code>{config['verify_card_delete_sec']} সেকেন্ড</code>\n"
            f"3️⃣ সাধারণ চ্যাট নিষেধ নোটিশ ডিলিট: <code>{config['non_link_warn_delete_sec']} সেকেন্ড</code>\n"
            f"4️⃣ অন্য লিংক নিষেধ নোটিশ ডিলিট: <code>{config['other_link_warn_delete_sec']} সেকেন্ড</code>\n"
            f"5️⃣ ভেরিফিকেশন সফল বার্তা ডিলিট: <code>{config['verify_success_delete_sec']} সেকেন্ড</code>\n"
            f"6️⃣ স্বাগতম (Welcome) বার্তা ডিলিট: <code>{config['welcome_delete_sec']} সেকেন্ড</code>\n"
            f"7️⃣ অটো প্রোমো প্রচারের ব্যবধান: <code>{config['broadcast_interval_mins']} মিনিট</code>\n"
            f"8️⃣ প্রোমো মেসেজ ডিলিট হওয়ার সময়: <code>{config['promo_delete_sec']} সেকেন্ড</code>\n"
            f"9️⃣ শাটডাউন সাইকেল মেয়াদ: <code>{config['shutdown_duration_hours']} ঘণ্টা</code>\n"
            f"🔟 রিনিউ প্রম্পট ব্যবধান: <code>{config['renew_prompt_hours']} ঘণ্টা</code>\n\n"
            "👇 <i>যেকোনো টাইমার পরিবর্তন করতে নিচের বোতামে চাপুন:</i>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⏱️ অ্যাড ওয়েটিং সেকেন্ড", callback_data="edit_ad_wait_seconds"),
                InlineKeyboardButton(text="⏱️ ভেরিফাই কার্ড ডিলিট", callback_data="edit_verify_card_delete_sec")
            ],
            [
                InlineKeyboardButton(text="⏱️ নন-লিংক নোটিশ ডিলিট", callback_data="edit_non_link_warn_delete_sec"),
                InlineKeyboardButton(text="⏱️ অন্য লিংক নোটিশ ডিলিট", callback_data="edit_other_link_warn_delete_sec")
            ],
            [
                InlineKeyboardButton(text="⏱️ সফল বার্তা ডিলিট", callback_data="edit_verify_success_delete_sec"),
                InlineKeyboardButton(text="⏱️ ওয়েলকাম বার্তা ডিলিট", callback_data="edit_welcome_delete_sec")
            ],
            [
                InlineKeyboardButton(text="⏱️ প্রোমো ব্যবধান (মিনিট)", callback_data="edit_broadcast_interval_mins"),
                InlineKeyboardButton(text="⏱️ প্রোমো ডিলিট (সেকেন্ড)", callback_data="edit_promo_delete_sec")
            ],
            [
                InlineKeyboardButton(text="⏱️ শাটডাউন মেয়াদ (ঘণ্টা)", callback_data="edit_shutdown_duration_hours"),
                InlineKeyboardButton(text="⏱️ রিনিউ প্রম্পট (ঘণ্টা)", callback_data="edit_renew_prompt_hours")
            ],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer()

    # --- ৪. মেসেজ ও নোটিশ টেক্সট শাখা (A to Z) ---
    elif data == "br_messages":
        text = (
            "📝 <b>সকল মেসেজ ও নোটিশ টেক্সট শাখা</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "১. <b>চ্যানেল জয়েন রিকোয়েস্ট নোটিশ:</b>\n"
            f"<code>{config['msg_join_req_notice'][:60]}...</code>\n\n"
            "২. <b>অ্যাড লিংক ভিজিট নোটিশ:</b>\n"
            f"<code>{config['msg_ad_link_notice'][:60]}...</code>\n\n"
            "৩. <b>সাধারণ মেসেজ নিষেধ নোটিশ:</b>\n"
            f"<code>{config['msg_non_link_warn']}</code>\n\n"
            "৪. <b>অন্য লিংক নিষেধ নোটিশ:</b>\n"
            f"<code>{config['msg_only_tg_warn']}</code>\n\n"
            "৫. <b>ভেরিফিকেশন সফল বার্তা:</b>\n"
            f"<code>{config['msg_verify_success']}</code>\n\n"
            "৬. <b>স্বাগতম (Welcome) মেসেজ:</b>\n"
            f"<code>{config['welcome_text']}</code>\n\n"
            "৭. <b>অটো প্রোমোশন মেসেজ:</b>\n"
            f"<code>{config['promo_text']}</code>\n\n"
            "👇 <i>যেকোনো টেক্সট পরিবর্তন করতে নিচের বোতাম চাপুন:</i>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ চ্যানেল রিকোয়েস্ট নোটিশ এডিট", callback_data="edit_msg_join_req_notice")],
            [InlineKeyboardButton(text="✏️ অ্যাড লিংক নোটিশ এডিট", callback_data="edit_msg_ad_link_notice")],
            [InlineKeyboardButton(text="✏️ সাধারণ চ্যাট নিষেধ বার্তা এডিট", callback_data="edit_msg_non_link_warn")],
            [InlineKeyboardButton(text="✏️ অন্য লিংক নিষেধ বার্তা এডিট", callback_data="edit_msg_only_tg_warn")],
            [InlineKeyboardButton(text="✏️ ভেরিফিকেশন সফল বার্তা এডিট", callback_data="edit_msg_verify_success")],
            [InlineKeyboardButton(text="✏️ ওয়েলকাম টেক্সট এডিট", callback_data="edit_welcome_text")],
            [InlineKeyboardButton(text="✏️ প্রোমো বার্তা এডিট", callback_data="edit_promo_text")],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer()

    # --- ৫. বাটন টেক্সট ও লিংক শাখা ---
    elif data == "br_buttons":
        text = (
            "🔘 <b>সকল বাটন নাম ও লিংক শাখা</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• জয়েন রিকোয়েস্ট বাটন: <code>{config['btn_join_req']}</code>\n"
            f"• রিকোয়েস্ট ভেরিফাই বাটন: <code>{config['btn_join_verify']}</code>\n"
            f"• অ্যাড ভিজিট বাটন: <code>{config['btn_ad_visit']}</code>\n"
            f"• অ্যাড ভেরিফাই বাটন: <code>{config['btn_ad_verify']}</code>\n"
            f"• ওয়েলকাম ভেরিফাই বাটন: <code>{config['btn_welcome_verify']}</code>\n"
            f"• প্রোমো বাটন টেক্সট: <code>{config['promo_btn_text']}</code>\n"
            f"• প্রোমো বাটন লিংক: <code>{config['promo_btn_link']}</code>\n\n"
            "কোন বাটনের নাম পরিবর্তন করতে চান:"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ জয়েন রিকোয়েস্ট বাটন টেক্সট", callback_data="edit_btn_join_req")],
            [InlineKeyboardButton(text="✏️ রিকোয়েস্ট ভেরিফাই বাটন টেক্সট", callback_data="edit_btn_join_verify")],
            [InlineKeyboardButton(text="✏️ অ্যাড ভিজিট বাটন টেক্সট", callback_data="edit_btn_ad_visit")],
            [InlineKeyboardButton(text="✏️ অ্যাড ভেরিফাই বাটন টেক্সট", callback_data="edit_btn_ad_verify")],
            [InlineKeyboardButton(text="✏️ ওয়েলকাম ভেরিফাই বাটন টেক্সট", callback_data="edit_btn_welcome_verify")],
            [InlineKeyboardButton(text="✏️ প্রোমো বাটন নাম এডিট", callback_data="edit_promo_btn_text")],
            [InlineKeyboardButton(text="✏️ প্রোমো বাটন লিংক এডিট", callback_data="edit_promo_btn_link")],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer()

    # --- ৬. ফিল্টারিং রুলস ও সুইচসমূহ (ON/OFF) ---
    elif data == "br_filters":
        text = (
            "🛡️ <b>গ্রুপ লিংক ফিল্টারিং ও নিরাপত্তা শাখা</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"1️⃣ <b>ভেরিফিকেশন বাধ্যবাধকতা:</b> <code>{'🟢 চালু (ON)' if config['require_verification'] else '🔴 বন্ধ (OFF)'}</code>\n"
            f"2️⃣ <b>শুধুমাত্র টেলিগ্রাম লিংক অনুমোদন:</b> <code>{'🟢 চালু (ON)' if config['allow_only_tg_links'] else '🔴 বন্ধ (OFF)'}</code>\n"
            f"3️⃣ <b>নন-লিংক সাধারণ মেসেজ ডিলিট:</b> <code>{'🟢 চালু (ON)' if config['delete_non_links'] else '🔴 বন্ধ (OFF)'}</code>\n"
            f"4️⃣ <b>সার্ভিস মেসেজ ডিলিট (Joined/Left):</b> <code>{'🟢 চালু (ON)' if config['clean_service_msgs'] else '🔴 বন্ধ (OFF)'}</code>\n"
            f"5️⃣ <b>স্বাগতম (Welcome) মেসেজ:</b> <code>{'🟢 চালু (ON)' if config['welcome_enabled'] else '🔴 বন্ধ (OFF)'}</code>\n"
            f"6️⃣ <b>স্বাগতম বাটনে ভেরিফাই অপশন:</b> <code>{'🟢 চালু (ON)' if config.get('welcome_verify_btn', True) else '🔴 বন্ধ (OFF)'}</code>\n"
            f"7️⃣ <b>অটো প্রোমো ব্রডকাস্ট:</b> <code>{'🟢 চালু (ON)' if config['promo_enabled'] else '🔴 বন্ধ (OFF)'}</code>\n"
            f"8️⃣ <b>গ্রুপ অ্যাডমিনদেরও ফিল্টার (টেস্টিং মোড):</b> <code>{'🟢 চালু (ON)' if config.get('filter_admins', False) else '🔴 বন্ধ (OFF)'}</code>"
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
                text=f"{'🔴 বন্ধ করুন' if config['clean_service_msgs'] else '🟢 চালু করুন'} (সার্ভিস মেসেজ ডিলিট)",
                callback_data="tog_clean_service"
            )],
            [InlineKeyboardButton(
                text=f"{'🔴 বন্ধ করুন' if config['welcome_enabled'] else '🟢 চালু করুন'} (স্বাগতম বার্তা)",
                callback_data="tog_welcome_enabled"
            )],
            [InlineKeyboardButton(
                text=f"{'🔴 বন্ধ করুন' if config.get('welcome_verify_btn', True) else '🟢 চালু করুন'} (ওয়েলকাম ভেরিফাই বাটন)",
                callback_data="tog_welcome_verify_btn"
            )],
            [InlineKeyboardButton(
                text=f"{'🔴 বন্ধ করুন' if config['promo_enabled'] else '🟢 চালু করুন'} (অটো প্রোমোশন)",
                callback_data="tog_promo"
            )],
            [InlineKeyboardButton(
                text=f"{'🔴 বন্ধ করুন' if config.get('filter_admins', False) else '🟢 চালু করুন'} (অ্যাডমিন টেস্ট ফিল্টার)",
                callback_data="tog_filter_admins"
            )],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer()

    # --- ফিল্টার সুইচ টগল হ্যান্ডলার্স ---
    elif data == "tog_verification":
        config["require_verification"] = not config["require_verification"]
        save_data()
        await query.answer(f"ভেরিফিকেশন: {'চালু' if config['require_verification'] else 'বন্ধ'}")
        query.data = "br_filters"
        await handle_admin_branches(query)

    elif data == "tog_only_tg":
        config["allow_only_tg_links"] = not config["allow_only_tg_links"]
        save_data()
        await query.answer(f"শুধুমাত্র টেলিগ্রাম লিংক: {'চালু' if config['allow_only_tg_links'] else 'বন্ধ'}")
        query.data = "br_filters"
        await handle_admin_branches(query)

    elif data == "tog_delete_non_links":
        config["delete_non_links"] = not config["delete_non_links"]
        save_data()
        await query.answer(f"নন-লিংক ডিলিট: {'চালু' if config['delete_non_links'] else 'বন্ধ'}")
        query.data = "br_filters"
        await handle_admin_branches(query)

    elif data == "tog_clean_service":
        config["clean_service_msgs"] = not config["clean_service_msgs"]
        save_data()
        await query.answer(f"সার্ভিস মেসেজ ডিলিট: {'চালু' if config['clean_service_msgs'] else 'বন্ধ'}")
        query.data = "br_filters"
        await handle_admin_branches(query)

    elif data == "tog_welcome_enabled":
        config["welcome_enabled"] = not config["welcome_enabled"]
        save_data()
        await query.answer(f"স্বাগতম বার্তা: {'চালু' if config['welcome_enabled'] else 'বন্ধ'}")
        query.data = "br_filters"
        await handle_admin_branches(query)

    elif data == "tog_welcome_verify_btn":
        config["welcome_verify_btn"] = not config.get("welcome_verify_btn", True)
        save_data()
        await query.answer(f"ওয়েলকাম ভেরিফাই বাটন: {'চালু' if config['welcome_verify_btn'] else 'বন্ধ'}")
        query.data = "br_filters"
        await handle_admin_branches(query)

    elif data == "tog_promo":
        config["promo_enabled"] = not config["promo_enabled"]
        save_data()
        await query.answer(f"প্রোমোশন: {'চালু' if config['promo_enabled'] else 'বন্ধ'}")
        query.data = "br_promo"
        await handle_admin_branches(query)

    elif data.startswith("intv_"):
        try:
            m = int(data.split("_")[1])
            config["broadcast_interval_mins"] = m
            save_data()
            await query.answer(f"✅ অটো প্রোমোর প্রচার ব্যবধান সেট হয়েছে: প্রতি {m} মিনিট পর পর!", show_alert=True)
            query.data = "br_promo"
            await handle_admin_branches(query)
        except Exception:
            await query.answer("ত্রুটি ঘটেছে!")

    elif data == "tog_filter_admins":
        config["filter_admins"] = not config.get("filter_admins", False)
        save_data()
        await query.answer(f"অ্যাডমিন টেস্ট ফিল্টার: {'চালু' if config['filter_admins'] else 'বন্ধ'}")
        query.data = "br_filters"
        await handle_admin_branches(query)

    # --- ৭. স্বাগতম (Welcome) শাখা ---
    elif data == "br_welcome":
        text = (
            "💬 <b>স্বাগতম (Welcome) মেসেজ শাখা</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• অবস্থা: <code>{'🟢 চালু (ON)' if config['welcome_enabled'] else '🔴 বন্ধ (OFF)'}</code>\n"
            f"• ভেরিফাই বাটন: <code>{'🟢 যুক্ত আছে' if config.get('welcome_verify_btn', True) else '🔴 বন্ধ'}</code>\n"
            f"• মেসেজ ডিলিট টাইমার: <code>{config['welcome_delete_sec']} সেকেন্ড</code>\n"
            f"• ভেরিফাই বাটন টেক্সট: <code>{config['btn_welcome_verify']}</code>\n\n"
            f"📝 <b>বর্তমান বার্তা:</b>\n"
            f"<code>{config['welcome_text']}</code>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{'🔴 স্বাগতম বার্তা বন্ধ করুন' if config['welcome_enabled'] else '🟢 স্বাগতম বার্তা চালু করুন'}",
                callback_data="tog_welcome_enabled"
            )],
            [InlineKeyboardButton(text="✏️ স্বাগতম মেসেজ পরিবর্তন", callback_data="edit_welcome_text")],
            [InlineKeyboardButton(text="✏️ ভেরিফাই বাটন টেক্সট পরিবর্তন", callback_data="edit_btn_welcome_verify")],
            [InlineKeyboardButton(text="⏱️ ডিলিট হওয়ার সময় পরিবর্তন (সেকেন্ড)", callback_data="edit_welcome_delete_sec")],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer()

    # --- ৮. অটো প্রোমোশন শাখা ---
    elif data == "br_promo":
        text = (
            "📢 <b>অটো প্রোমোশন ও ব্রডকাস্ট শাখা</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• অবস্থা: <code>{'🟢 চালু (ON)' if config['promo_enabled'] else '🔴 বন্ধ (OFF)'}</code>\n"
            f"• প্রচার ব্যবধান: <code>প্রতি {config['broadcast_interval_mins']} মিনিট পর পর</code>\n"
            f"• বাটন নাম: <code>{config['promo_btn_text']}</code>\n"
            f"• বাটন লিংক: <code>{config['promo_btn_link']}</code>\n"
            f"• মেসেজ ডিলিট টাইমার: <code>{config['promo_delete_sec']} সেকেন্ড</code>\n\n"
            f"📝 <b>বর্তমান বার্তা:</b>\n"
            f"<i>{config['promo_text']}</i>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{'🔴 প্রোমো বন্ধ করুন' if config['promo_enabled'] else '🟢 প্রোমো চালু করুন'}",
                callback_data="tog_promo"
            )],
            [InlineKeyboardButton(text="✏️ প্রোমো মেসেজ পরিবর্তন", callback_data="edit_promo_text")],
            [InlineKeyboardButton(text="✏️ প্রোমো বাটন টেক্সট পরিবর্তন", callback_data="edit_promo_btn_text")],
            [InlineKeyboardButton(text="✏️ প্রোমো বাটন লিংক পরিবর্তন", callback_data="edit_promo_btn_link")],
            [
                InlineKeyboardButton(text="⚡ ১৫ মিনিট", callback_data="intv_15"),
                InlineKeyboardButton(text="⚡ ৩০ মিনিট", callback_data="intv_30"),
                InlineKeyboardButton(text="⚡ ১ ঘণ্টা (৬০ মি.)", callback_data="intv_60")
            ],
            [
                InlineKeyboardButton(text="⚡ ২ ঘণ্টা (১২০ মি.)", callback_data="intv_120"),
                InlineKeyboardButton(text="⚡ ৪ ঘণ্টা (২৪০ মি.)", callback_data="intv_240"),
                InlineKeyboardButton(text="⚡ ৬ ঘণ্টা (৩৬০ মি.)", callback_data="intv_360")
            ],
            [InlineKeyboardButton(text="✍️ যেকোনো কাস্টম মিনিট লিখে সেট করুন", callback_data="edit_broadcast_interval_mins")],
            [InlineKeyboardButton(text="⏱️ মেসেজ ডিলিট সময় পরিবর্তন (সেকেন্ড)", callback_data="edit_promo_delete_sec")],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer()

    # --- ৯. শাটডাউন ও রিনিউ শাখা ---
    elif data == "br_shutdown":
        now = time.time()
        rem_sec = max(0, shutdown_state["active_expiry"] - now)
        rem_str = format_time_remaining(rem_sec)
        status_txt = "🔴 বর্তমানে বন্ধ (লক)" if shutdown_state["is_shutdown"] else f"🟢 বর্তমানে চালু ({rem_str} বাকি)"

        text = (
            "⏱️ <b>২৪ ঘণ্টা অটো-শাটডাউন ও ৫ ঘণ্টা রিনিউ শাখা</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• বর্তমান অবস্থা: <code>{status_txt}</code>\n"
            f"• অবশিষ্ট সক্রিয় সময়: <code>{rem_str}</code>\n"
            f"• শাটডাউন ডিউরেশন: <code>প্রতি {config.get('shutdown_duration_hours', 24)} ঘণ্টা পর পর</code>\n"
            f"• রিনিউ প্রম্পট ব্যবধান: <code>প্রতি {config.get('renew_prompt_hours', 5)} ঘণ্টা পর পর</code>\n"
            f"• টার্গেট গ্রুপ আইডি: <code>{TARGET_GROUP_ID or config.get('target_group_id') or 'অটোমেটিক ডিটেক্টেড'}</code>\n\n"
            "💡 <i>ম্যানুয়ালি নিয়ন্ত্রণ করতে নিচের অপশন ব্যবহার করুন:</i>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⚡ এখনই রিনিউ করুন (রিসেট টাইমার)", callback_data="renew_confirm"),
                InlineKeyboardButton(text="⛔ এখনই গ্রুপ লক করুন (শাটডাউন)", callback_data="act_manual_shutdown")
            ],
            [
                InlineKeyboardButton(text="⏱️ শাটডাউন ডিউরেশন পরিবর্তন", callback_data="edit_shutdown_duration_hours"),
                InlineKeyboardButton(text="⏱️ রিনিউ প্রম্পট ব্যবধান পরিবর্তন", callback_data="edit_renew_prompt_hours")
            ],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer()

    elif data == "act_manual_shutdown":
        await trigger_group_shutdown(source="manual")
        await query.answer("⛔ গ্রুপটি তাৎক্ষণিকভাবে শাটডাউন ও লক করা হয়েছে!", show_alert=True)
        query.data = "br_shutdown"
        await handle_admin_branches(query)

    # --- ১০. ইউজার ও ভেরিফিকেশন তথ্য শাখা ---
    elif data == "br_users":
        total_k = len(all_known_users)
        total_v = len(verified_users)

        recent_ver = []
        for uid, info in list(verified_users.items())[-6:]:
            u_name = info.get("name", "অজানা")
            u_uname = info.get("username", "")
            recent_ver.append(f"• <code>{uid}</code>: {u_name} ({u_uname})")

        ver_list_str = "\n".join(recent_ver) if recent_ver else "কোনো ভেরিফাইড ইউজার পাওয়া যায়নি।"

        text = (
            "👥 <b>ইউজার ও ভেরিফিকেশন তথ্য শাখা</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>পরিসংখ্যান:</b>\n"
            f"• গ্রুপে সক্রিয় পরিচিত সদস্য: <code>{total_k} জন</code>\n"
            f"• বর্তমানে ভেরিফাইড সদস্য: <code>{total_v} জন</code>\n"
            f"• বর্তমান সিকিউরিটি ভার্সন: <code>v{config['current_version']}</code>\n\n"
            f"📋 <b>সাম্প্রতিক ভেরিফাইড ইউজার তালিকা:</b>\n"
            f"{ver_list_str}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="♻️ শুধুমাত্র মেম্বার ভেরিফিকেশন রিসেট করুন", callback_data="br_confirm_reset_verif")],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer()

    # --- ১১. ইনপুট এডিটর ট্রিগারসমূহ (A to Z) ---
    elif data.startswith("edit_"):
        action = data.replace("edit_", "")
        admin_input_state[query.from_user.id] = {"action": action, "chat_id": query.message.chat.id}

        prompts = {
            # চ্যানেল ও লিংক
            "target_channel": "✍️ চ্যানেলের নতুন ইউজারনেম লিখে পাঠান (যেমন: <code>@my_channel</code>):",
            "target_channel_link": "✍️ চ্যানেলের জয়েন রিকোয়েস্ট লিংক লিখে পাঠান (যেমন: <code>https://t.me/+AbCdEf...</code>):",
            "ad_link": "✍️ নতুন ডাইরেক্ট অ্যাড ওয়েবসাইটের লিংক লিখে পাঠান (যেমন: <code>https://example.com</code>):",

            # টাইমারসমূহ (সেকেন্ড / মিনিট / ঘণ্টা)
            "ad_wait_seconds": "✍️ অ্যাড ওয়েবসাইটে ইউজারদের অপেক্ষার সময় (সেকেন্ডে) লিখে পাঠান (যেমন: <code>15</code> বা <code>30</code>):",
            "verify_card_delete_sec": "✍️ ভেরিফিকেশন কার্ড গ্রুপ থেকে কত সেকেন্ড পর ডিলিট হবে লিখে পাঠান (যেমন: <code>30</code>):",
            "non_link_warn_delete_sec": "✍️ সাধারণ মেসেজ নিষেধ নোটিশ কত সেকেন্ড পর ডিলিট হবে লিখে পাঠান (যেমন: <code>8</code>):",
            "other_link_warn_delete_sec": "✍️ অন্য লিংক নিষেধ নোটিশ কত সেকেন্ড পর ডিলিট হবে লিখে পাঠান (যেমন: <code>12</code>):",
            "verify_success_delete_sec": "✍️ ভেরিফিকেশন সফল বার্তা কত সেকেন্ড পর ডিলিট হবে লিখে পাঠান (যেমন: <code>10</code>):",
            "welcome_delete_sec": "✍️ স্বাগতম বার্তা কত সেকেন্ড পর ডিলিট হবে লিখে পাঠান (যেমন: <code>20</code>):",
            "broadcast_interval_mins": "✍️ অটো প্রোমো প্রতি কত মিনিট পর পর গ্রুপে প্রচার হবে লিখে পাঠান (যেমন: <code>60</code>):",
            "promo_delete_sec": "✍️ প্রোমো বার্তা কত সেকেন্ড পর ডিলিট হবে লিখে পাঠান (০ দিলে ডিলিট হবে না):",
            "shutdown_duration_hours": "✍️ গ্রুপ সক্রিয় থাকার মেয়াদ (ঘণ্টায়) লিখে পাঠান (যেমন: <code>24</code>):",
            "renew_prompt_hours": "✍️ রিনিউ প্রম্পট কত ঘণ্টা পর পর আসবে লিখে পাঠান (যেমন: <code>5</code>):",

            # মেসেজ ও টেক্সটসমূহ
            "msg_join_req_notice": "✍️ চ্যানেল জয়েন রিকোয়েস্ট নোটিশটি লিখে পাঠান\n(ইউজারের নামের লিংকের জন্য <code>{user_link}</code> ব্যবহার করতে পারেন):",
            "msg_ad_link_notice": "✍️ অ্যাড লিংক ভেরিফিকেশন নোটিশটি লিখে পাঠান\n(ব্যবহার করতে পারেন: <code>{user_link}</code>, <code>{wait_seconds}</code>):",
            "msg_non_link_warn": "✍️ সাধারণ চ্যাট নিষেধ সতর্কবার্তাটি লিখে পাঠান\n(ব্যবহার করতে পারেন: <code>{user_link}</code>):",
            "msg_only_tg_warn": "✍️ শুধুমাত্র টেলিগ্রাম লিংক সতর্কবার্তাটি লিখে পাঠান\n(ব্যবহার করতে পারেন: <code>{user_link}</code>):",
            "msg_verify_success": "✍️ ভেরিফিকেশন সফল বার্তাটি লিখে পাঠান\n(ব্যবহার করতে পারেন: <code>{user_link}</code>):",
            "welcome_text": "✍️ নতুন স্বাগতম বার্তা লিখে পাঠান (মেম্বারের নাম আনতে <code>{name}</code> ব্যবহার করুন):",
            "promo_text": "✍️ গ্রুপে প্রচার করার জন্য নতুন প্রোমো টেক্সটটি লিখে পাঠান:",

            # বাটন টেক্সটসমূহ
            "btn_join_req": "✍️ জয়েন রিকোয়েস্ট বাটনের নাম লিখে পাঠান (যেমন: <code>👉 জয়েন রিকোয়েস্ট পাঠান</code>):",
            "btn_join_verify": "✍️ রিকোয়েস্ট ভেরিফাই বাটনের নাম লিখে পাঠান (যেমন: <code>✅ আমি রিকোয়েস্ট দিয়েছি</code>):",
            "btn_ad_visit": "✍️ অ্যাড ভিজিট বাটনের নাম লিখে পাঠান (যেমন: <code>🌐 মূল ওয়েবসাইটে যান</code>):",
            "btn_ad_verify": "✍️ অ্যাড ভেরিফাই বাটনের নাম লিখে পাঠান (যেমন: <code>✅ ভেরিফাই সম্পন্ন করুন</code>):",
            "btn_welcome_verify": "✍️ ওয়েলকাম ভেরিফাই বাটনের নাম লিখে পাঠান:",
            "promo_btn_text": "✍️ প্রোমো বাটনের নাম লিখে পাঠান:",
            "promo_btn_link": "✍️ প্রোমো বাটনের লিংক লিখে পাঠান (যেমন: <code>https://t.me/...</code>):",

            # ভেরিফাই ব্যাজ ও রিঅ্যাকশন
            "badge_title": "✍️ মেম্বারদের নামের পাশে যে ভেরিফাই ব্যাজ/পদবি দেখাবে তা লিখে পাঠান (সর্বোচ্চ ১৬ অক্ষর, যেমন: <code>✓ Verified</code> বা <code>👑 ভেরিফাইড</code>):",
            "badge_reaction_emoji": "✍️ ভেরিফাইড মেম্বার লিংক পাঠালে যে রিঅ্যাকশন ইমোজি পড়বে তা লিখে পাঠান (যেমন: ⚡ বা 🔥 বা 👍):",

            # গ্যামিফিকেশন ও রিওয়ার্ডস
            "points_per_link": "✍️ গ্রুপে প্রতি লিংকে ইউজার কত পয়েন্ট পাবে লিখে পাঠান (যেমন: <code>10</code>):",
            "points_per_referral": "✍️ প্রতি সফল রেফারেলে ইউজার কত পয়েন্ট পাবে লিখে পাঠান (যেমন: <code>200</code>):",
            "points_daily_base": "✍️ দৈনিক বেস বোনাস পয়েন্ট কত হবে লিখে পাঠান (যেমন: <code>100</code>):",
            "points_welcome_bonus": "✍️ নতুন ইউজারের ওয়েলকাম বোনাস পয়েন্ট কত হবে লিখে পাঠান (যেমন: <code>50</code>):",
            "auto_delete_links_hours": "✍️ গ্রুপে পোস্ট করা লিংক কত ঘণ্টা পর অটো ডিলিট হবে লিখে পাঠান (০ দিলে ডিলিট হবে না, যেমন: <code>6</code> বা <code>12</code> বা <code>24</code>):"
        }

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ ইনপুট বাতিল করুন", callback_data="cancel_input")]
        ])
        prompt_txt = prompts.get(action, "✍️ দয়া করে নতুন মানটি লিখে পাঠান:")
        await query.message.answer(prompt_txt, parse_mode="HTML", reply_markup=kb)
        await query.answer("ইনপুটের অপেক্ষায়...")

    elif data == "act_add_task_ad":
        admin_input_state[query.from_user.id] = {"action": "new_task_ad", "chat_id": query.message.chat.id}
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ বাতিল করুন", callback_data="cancel_input")]
        ])
        await query.message.answer(
            "🌐 <b>নতুন ডাইরেক্ট অ্যাড / ওয়েবসাইট টাস্ক যুক্তকরণ</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "দয়া করে এক লাইনে নিচের ফরম্যাটে লিখে পাঠান:\n"
            "<code>টাইটেল | ওয়েবসাইট লিংক | অপেক্ষার সেকেন্ড | পয়েন্ট</code>\n\n"
            "📌 <b>উদাহরণ:</b>\n"
            "<code>Adsterra High CPM | https://example.com/direct | 15 | 100</code>",
            parse_mode="HTML",
            reply_markup=kb
        )
        await query.answer()

    elif data == "act_add_task_chan":
        admin_input_state[query.from_user.id] = {"action": "new_task_chan", "chat_id": query.message.chat.id}
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ বাতিল করুন", callback_data="cancel_input")]
        ])
        await query.message.answer(
            "📢 <b>নতুন টেলিগ্রাম চ্যানেল জয়েন টাস্ক যুক্তকরণ</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "দয়া করে এক লাইনে নিচের ফরম্যাটে লিখে পাঠান:\n"
            "<code>টাইটেল | চ্যানেল ইউজারনেম | জয়েন লিংক | পয়েন্ট</code>\n\n"
            "📌 <b>উদাহরণ:</b>\n"
            "<code>Join Movies Hub | @movies_hub_official | https://t.me/+AbCdEfGh | 150</code>",
            parse_mode="HTML",
            reply_markup=kb
        )
        await query.answer()

    # --- ১২. অটো জয়েন রিকোয়েস্ট একসেপ্ট শাখা ---
    elif data == "br_join_req":
        is_on = config.get("auto_accept_join_requests", False)
        count = len(pending_join_requests)
        text = (
            "🤝 <b>অটো জয়েন রিকোয়েস্ট একসেপ্ট শাখা</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>বর্তমান অবস্থা:</b> <code>{'🟢 চালু (ON)' if is_on else '🔴 বন্ধ (OFF)'}</code>\n"
            f"• <b>জমা হওয়া পেন্ডিং রিকোয়েস্ট:</b> <code>{count} জন</code>\n\n"
            "💡 <b>কীভাবে কাজ করে?</b>\n"
            "১. <b>বন্ধ থাকলে (ডিফল্ট):</b> গ্রুপে কেউ জয়েন রিকোয়েস্ট পাঠালে তা তালিকায় জমা থাকবে, স্বয়ংক্রিয়ভাবে অ্যাপ্রুভ হবে না।\n"
            "২. <b>অন করলে:</b> পূর্বে জমা থাকা সমস্ত রিকোয়েস্ট সাথে সাথে একসেপ্ট হয়ে যাবে এবং পরবর্তীতে যে-ই রিকোয়েস্ট পাঠাবে তৎক্ষণাৎ গ্রুপে অ্যাপ্রুভ হয়ে যাবে!\n\n"
            "👇 <i>নিচের অপশনগুলো ব্যবহার করুন:</i>"
        )
        kb_rows = [
            [InlineKeyboardButton(
                text=f"{'🔴 বন্ধ করুন' if is_on else '🟢 চালু করুন'} (অটো একসেপ্ট)",
                callback_data="tog_auto_join_req"
            )]
        ]
        if count > 0:
            kb_rows.append([InlineKeyboardButton(
                text=f"⚡ জমা হওয়া {count} জনের রিকোয়েস্ট এখনই একসেপ্ট করুন",
                callback_data="act_approve_all_pending_req"
            )])
            kb_rows.append([InlineKeyboardButton(
                text="🗑️ পেন্ডিং তালিকা পরিষ্কার করুন",
                callback_data="act_clear_pending_req"
            )])
        kb_rows.append([InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")])
        kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer()

    elif data == "tog_auto_join_req":
        config["auto_accept_join_requests"] = not config.get("auto_accept_join_requests", False)
        save_data()
        if config["auto_accept_join_requests"]:
            approved_count = 0
            for uid_str, p_item in list(pending_join_requests.items()):
                try:
                    await bot.approve_chat_join_request(chat_id=p_item["chat_id"], user_id=p_item["user_id"])
                    approved_count += 1
                    pending_join_requests.pop(uid_str, None)
                except Exception:
                    pass
            save_data()
            if approved_count > 0:
                await query.answer(f"✅ অটো একসেপ্ট চালু হয়েছে এবং পেন্ডিং থাকা {approved_count} জনের রিকোয়েস্ট একসেপ্ট হয়েছে!", show_alert=True)
            else:
                await query.answer("✅ অটো একসেপ্ট চালু হয়েছে! এখন থেকে যেকোনো জয়েন রিকোয়েস্ট সাথে সাথে অ্যাপ্রুভ হবে।", show_alert=True)
        else:
            await query.answer("🔴 অটো জয়েন রিকোয়েস্ট বন্ধ করা হয়েছে। এখন রিকোয়েস্ট জমা থাকবে।", show_alert=True)
        query.data = "br_join_req"
        await handle_admin_branches(query)

    elif data == "act_approve_all_pending_req":
        if not pending_join_requests:
            await query.answer("ℹ️ বর্তমানে কোনো পেন্ডিং জয়েন রিকোয়েস্ট নেই!", show_alert=True)
            return
        approved = 0
        failed = 0
        for uid_str, p_item in list(pending_join_requests.items()):
            try:
                await bot.approve_chat_join_request(chat_id=p_item["chat_id"], user_id=p_item["user_id"])
                approved += 1
                pending_join_requests.pop(uid_str, None)
            except Exception:
                failed += 1
        save_data()
        await query.answer(f"✅ {approved} টি রিকোয়েস্ট সফলভাবে একসেপ্ট করা হয়েছে!" + (f" ({failed} টি ব্যর্থ)" if failed else ""), show_alert=True)
        query.data = "br_join_req"
        await handle_admin_branches(query)

    elif data == "act_clear_pending_req":
        pending_join_requests.clear()
        save_data()
        await query.answer("🗑️ পেন্ডিং তালিকা পরিষ্কার করা হয়েছে।")
        query.data = "br_join_req"
        await handle_admin_branches(query)

    # --- ১৩. পাবলিক গ্রুপ সিকিউরিটি ও কমপ্যাক্ট লিংক শাখা ---
    elif data == "br_public_group":
        gid = TARGET_GROUP_ID or config.get("target_group_id")
        g_status = f"<code>{gid}</code>" if gid else "<i>গ্রুপ সনাক্ত হয়নি (গ্রুপে মেসেজ দিন)</i>"
        text = (
            "🌐 <b>পাবলিক গ্রুপ সিকিউরিটি ও কমপ্যাক্ট লিংক শাখা</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>টার্গেট গ্রুপ আইডি:</b> {g_status}\n"
            f"• <b>কমপ্যাক্ট লিংক (প্রিভিউ অফ):</b> <code>{'🟢 চালু' if config.get('disable_link_previews', True) else '🔴 বন্ধ'}</code>\n"
            f"• <b>অ্যান্টি-ফ্লাড স্প্যাম ফিল্টার:</b> <code>{'🟢 চালু (সক্রিয়)' if config.get('antiflood_enabled', True) else '🔴 বন্ধ'}</code>\n"
            f"• <b>অনলি টেলিগ্রাম লিংক:</b> <code>{'🟢 চালু' if config.get('allow_only_tg_links', True) else '🔴 বন্ধ'}</code>\n"
            f"• <b>সার্ভিস মেসেজ ডিলিট:</b> <code>{'🟢 চালু' if config.get('clean_service_msgs', True) else '🔴 বন্ধ'}</code>\n"
            f"• <b>নন-লিংক সাধারণ মেসেজ ডিলিট:</b> <code>{'🟢 চালু' if config.get('delete_non_links', True) else '🔴 বন্ধ'}</code>\n\n"
            "📌 <b>পাবলিক গ্রুপ চালুর চেকলিস্ট:</b>\n"
            "১. বটকে গ্রুপে <b>Administrator (অ্যাডমিন)</b> করুন এবং 'Delete messages', 'Invite users via link' পারমিশন দিন।\n"
            "২. নিচে <b>'🔗 কমপ্যাক্ট লিংক কার্যকর করুন'</b> চাপুন — এতে গ্রুপ মেম্বারদের লিংকের বড় প্রিভিউ কার্ড বন্ধ হয়ে লিংকগুলো ছোট ও পরিচ্ছন্ন থাকবে।\n"
            "৩. অ্যান্টি-ফ্লাড প্রোটেকশন চালু থাকায় স্প্যামার বা রেইড বট দ্রুত মেসেজ পাঠাতে পারবে না।"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 গ্রুপে কমপ্যাক্ট লিংক কার্যকর করুন", callback_data="act_apply_compact_links")],
            [InlineKeyboardButton(
                text=f"{'🔴 অ্যান্টি-ফ্লাড বন্ধ করুন' if config.get('antiflood_enabled', True) else '🟢 অ্যান্টি-ফ্লাড চালু করুন'}",
                callback_data="tog_antiflood"
            )],
            [InlineKeyboardButton(
                text=f"{'🔴 কমপ্যাক্ট লিংক বন্ধ' if config.get('disable_link_previews', True) else '🟢 কমপ্যাক্ট লিংক চালু'}",
                callback_data="tog_disable_previews"
            )],
            [InlineKeyboardButton(text="🔙 মূল মেনুতে ফেরত যান", callback_data="br_main")]
        ])
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await query.answer()

    elif data == "act_apply_compact_links":
        gid = TARGET_GROUP_ID or config.get("target_group_id")
        if not gid:
            await query.answer("❌ গ্রুপ এখনও সনাক্ত হয়নি! অনুগ্রহ করে গ্রুপে একটি মেসেজ দিন যাতে বট গ্রুপ চ্যাট আইডি পায়।", show_alert=True)
            return
        success = await apply_compact_link_permissions(gid)
        if success:
            await query.answer("✅ গ্রুপে সফলভাবে কমপ্যাক্ট লিংক পারমিশন কার্যকর হয়েছে! এখন থেকে মেম্বারদের লিংকের বড় প্রিভিউ আসবে না, লিংক ছোট দেখাবে।", show_alert=True)
        else:
            await query.answer("⚠️ পারমিশন পরিবর্তন করা যায়নি। নিশ্চিত করুন বটের গ্রুপে পর্যাপ্ত অ্যাডমিন ক্ষমতা দেওয়া আছে।", show_alert=True)

    elif data == "tog_antiflood":
        config["antiflood_enabled"] = not config.get("antiflood_enabled", True)
        save_data()
        await query.answer(f"অ্যান্টি-ফ্লাড: {'চালু' if config['antiflood_enabled'] else 'বন্ধ'}")
        query.data = "br_public_group"
        await handle_admin_branches(query)

    elif data == "tog_disable_previews":
        config["disable_link_previews"] = not config.get("disable_link_previews", True)
        save_data()
        await query.answer(f"কমপ্যাক্ট লিংক: {'চালু' if config['disable_link_previews'] else 'বন্ধ'}")
        query.data = "br_public_group"
        await handle_admin_branches(query)

    elif data == "cancel_input":
        if query.from_user.id in admin_input_state:
            del admin_input_state[query.from_user.id]
        await query.message.delete()
        await query.answer("ইনপুট গ্রহণ বাতিল করা হয়েছে")

# ==================== ৫. টেক্সট ইনপুট গ্রহণ ও সংরক্ষণ ====================

@dp.message(F.from_user.id == ADMIN_ID)
async def handle_admin_text_inputs(message: types.Message):
    track_user(message.from_user)
    uid = message.from_user.id

    if uid not in admin_input_state:
        if message.chat.type == "private" and not (message.text or "").startswith("/"):
            await message.reply("💡 সেটিংস নিয়ন্ত্রণ করতে <code>/admin</code> অথবা <code>/panel</code> লিখুন।", parse_mode="HTML")
        return

    action = admin_input_state[uid]["action"]
    del admin_input_state[uid]
    text = (message.text or "").strip()

    # ১. চ্যানেল ও লিংক
    if action == "target_channel":
        if not text.startswith("@") and not text.startswith("https://t.me/"):
            text = f"@{text}"
        config["target_channel"] = text
        save_data()
        await message.reply(f"✅ টার্গেট চ্যানেল সফলভাবে সংরক্ষিত হয়েছে: <code>{text}</code>", parse_mode="HTML")

    elif action == "target_channel_link":
        config["target_channel_link"] = text
        save_data()
        await message.reply(f"✅ চ্যানেল রিকোয়েস্ট লিংক সংরক্ষিত হয়েছে: <code>{text}</code>", parse_mode="HTML")

    elif action == "ad_link":
        config["ad_link"] = text
        save_data()
        await message.reply(f"✅ ডাইরেক্ট অ্যাড লিংক সংরক্ষিত হয়েছে: <code>{text}</code>", parse_mode="HTML")

    # ২. টাইমারসমূহ ও গ্যামিফিকেশন সংখ্যাসমূহ
    elif action in [
        "ad_wait_seconds", "verify_card_delete_sec", "non_link_warn_delete_sec",
        "other_link_warn_delete_sec", "verify_success_delete_sec", "welcome_delete_sec",
        "broadcast_interval_mins", "promo_delete_sec", "shutdown_duration_hours", "renew_prompt_hours",
        "points_per_link", "points_per_referral", "points_daily_base", "points_welcome_bonus",
        "auto_delete_links_hours"
    ]:
        if text.isdigit():
            val = int(text)
            config[action] = val
            save_data()
            await message.reply(f"✅ মান সফলভাবে আপডেট হয়েছে: <code>{val}</code>", parse_mode="HTML")
        else:
            await message.reply("❌ ভুল ইনপুট! শুধুমাত্র পূর্ণসংখ্যা (Digit) লিখুন।")

    # ৩. মেসেজ ও টেক্সটসমূহ
    elif action in [
        "msg_join_req_notice", "msg_ad_link_notice", "msg_non_link_warn",
        "msg_only_tg_warn", "msg_verify_success", "welcome_text", "promo_text"
    ]:
        config[action] = text
        save_data()
        await message.reply("✅ মেসেজ টেক্সট সফলভাবে আপডেট ও সংরক্ষিত হয়েছে!", parse_mode="HTML")

    # ৪. বাটন টেক্সট ও লিংক
    elif action in [
        "btn_join_req", "btn_join_verify", "btn_ad_visit",
        "btn_ad_verify", "btn_welcome_verify", "promo_btn_text", "promo_btn_link"
    ]:
        config[action] = text
        save_data()
        await message.reply(f"✅ বাটন সংক্রান্ত তথ্য সংরক্ষিত হয়েছে: <code>{text}</code>", parse_mode="HTML")

    # ৫. ভেরিফাই ব্যাজ সেটিংস
    elif action == "badge_title":
        clean_title = text[:16]
        config["badge_title"] = clean_title
        save_data()
        await message.reply(f"✅ নামের পাশের ভেরিফাই ব্যাজের পদবি সফলভাবে সেট হয়েছে: <code>{clean_title}</code>", parse_mode="HTML")

    elif action == "badge_reaction_emoji":
        config["badge_reaction_emoji"] = text[:4]
        save_data()
        await message.reply(f"✅ লিংক শেয়ারের ভেরিফাইড রিঅ্যাকশন ইমোজি সেট হয়েছে: {text[:4]}")

    # ৬. নতুন ডাইরেক্ট অ্যাড টাস্ক তৈরি
    elif action == "new_task_ad":
        parts = [p.strip() for p in text.split("|")]
        if len(parts) >= 4 and parts[2].isdigit() and parts[3].isdigit():
            t_title, t_url, t_wait, t_pts = parts[0], parts[1], int(parts[2]), int(parts[3])
            t_id = f"ad_{uuid.uuid4().hex[:6]}"
            monetization_tasks.append({
                "id": t_id,
                "title": t_title,
                "type": "ad_wait",
                "url": t_url,
                "wait_seconds": t_wait,
                "points": t_pts,
                "active": True
            })
            save_data()
            await message.reply(f"✅ <b>নতুন অ্যাড টাস্ক সফলভাবে যুক্ত হয়েছে!</b>\n• নাম: <code>{t_title}</code>\n• পয়েন্ট: <code>+{t_pts} pts</code>\n• অপেক্ষার সময়: <code>{t_wait}s</code>", parse_mode="HTML")
        else:
            await message.reply("❌ ফরম্যাট সঠিক নয়! অনুগ্রহ করে <code>টাইটেল | লিংক | সেকেন্ড | পয়েন্ট</code> ফরম্যাটে লিখুন।", parse_mode="HTML")

    # ৭. নতুন চ্যানেল জয়েন টাস্ক তৈরি
    elif action == "new_task_chan":
        parts = [p.strip() for p in text.split("|")]
        if len(parts) >= 4 and parts[3].isdigit():
            t_title, t_chan, t_link, t_pts = parts[0], parts[1], parts[2], int(parts[3])
            if not t_chan.startswith("@") and not t_chan.startswith("-100"):
                t_chan = f"@{t_chan}"
            t_id = f"chan_{uuid.uuid4().hex[:6]}"
            monetization_tasks.append({
                "id": t_id,
                "title": t_title,
                "type": "channel_join",
                "channel_username": t_chan,
                "channel_link": t_link,
                "points": t_pts,
                "active": True
            })
            save_data()
            await message.reply(f"✅ <b>নতুন চ্যানেল জয়েন টাস্ক সফলভাবে যুক্ত হয়েছে!</b>\n• নাম: <code>{t_title}</code>\n• চ্যানেল: <code>{t_chan}</code>\n• পয়েন্ট: <code>+{t_pts} pts</code>", parse_mode="HTML")
        else:
            await message.reply("❌ ফরম্যাট সঠিক নয়! অনুগ্রহ করে <code>টাইটেল | চ্যানেল ইউজারনেম | জয়েন লিংক | পয়েন্ট</code> ফরম্যাটে লিখুন।", parse_mode="HTML")

    p_text, p_kb = build_admin_main_view()
    await message.answer(p_text, parse_mode="HTML", reply_markup=p_kb)

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
        m = await message.answer(f"✅ টার্গেট চ্যানেল সেট হয়েছে: <code>{val}</code>", parse_mode="HTML")
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
        m = await message.answer(f"✅ চ্যানেল রিকোয়েস্ট লিংক সেট হয়েছে: <code>{args[1]}</code>", parse_mode="HTML")
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
        m = await message.answer(f"✅ ডাইরেক্ট অ্যাড লিংক সেট হয়েছে: <code>{args[1]}</code>", parse_mode="HTML")
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
        m = await message.answer(f"✅ অ্যাড ওয়েট টাইম সেট হয়েছে: <code>{args[1]} সেকেন্ড</code>", parse_mode="HTML")
        asyncio.create_task(auto_delete(message, 15))
        asyncio.create_task(auto_delete(m, 15))

# ==================== ৭. সার্ভিস মেসেজ ও মেম্বার জয়েন হ্যান্ডলার ====================

@dp.message(F.chat.type.in_({"group", "supergroup"}) & (F.new_chat_members | F.left_chat_member))
async def handle_service_messages(message: types.Message):
    global TARGET_GROUP_ID
    TARGET_GROUP_ID = message.chat.id
    if config.get("target_group_id") != message.chat.id:
        config["target_group_id"] = message.chat.id
        save_data()

    if config.get("clean_service_msgs", True):
        try:
            await message.delete()
        except Exception:
            pass

    if message.new_chat_members and config.get("welcome_enabled", True):
        for member in message.new_chat_members:
            if member.is_bot:
                continue
            track_user(member)
            name = html.escape(member.full_name or member.first_name)
            user_link = f"<a href='tg://user?id={member.id}'>{name}</a>"

            w_text = config.get("welcome_text", "👋 স্বাগতম {name}!")
            w_text = w_text.replace("{name}", name).replace("{channel}", config.get("target_channel", ""))

            kb_buttons = []
            if config.get("welcome_verify_btn", True):
                btn_txt = config.get("btn_welcome_verify", "🔗 লিংক শেয়ারের পারমিশন নিতে ভেরিফাই করুন")
                kb_buttons.append([InlineKeyboardButton(text=btn_txt, callback_data=f"wel_verify_{member.id}")])

            kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons) if kb_buttons else None
            try:
                w_msg = await bot.send_message(
                    chat_id=message.chat.id,
                    text=f"👋 স্বাগতম {user_link}!\n\n{w_text}",
                    parse_mode="HTML",
                    reply_markup=kb
                )
                del_sec = config.get("welcome_delete_sec", 20)
                asyncio.create_task(auto_delete(w_msg, del_sec))
            except Exception as e:
                print("Error sending welcome message:", e)

# ==================== ৭.২ অটো জয়েন রিকোয়েস্ট হ্যান্ডলার ====================

@dp.chat_join_request()
async def handle_chat_join_request(request: types.ChatJoinRequest):
    global TARGET_GROUP_ID
    chat = request.chat
    user = request.from_user
    uid_str = str(user.id)
    track_user(user)

    if chat.id and not TARGET_GROUP_ID:
        TARGET_GROUP_ID = chat.id
        config["target_group_id"] = chat.id
        save_data()

    if config.get("auto_accept_join_requests", False):
        try:
            await bot.approve_chat_join_request(chat_id=chat.id, user_id=user.id)
            if uid_str in pending_join_requests:
                pending_join_requests.pop(uid_str, None)
                save_data()
        except Exception as e:
            print(f"Error auto-approving join request for {user.id}:", e)
    else:
        pending_join_requests[uid_str] = {
            "user_id": user.id,
            "chat_id": chat.id,
            "name": user.full_name or user.first_name,
            "username": f"@{user.username}" if user.username else "নেই",
            "time": time.time()
        }
        save_data()

# ==================== ৮. গ্রুপ ট্র্যাফিক ও লিংক ফিল্টারিং কোর ইঞ্জিন ====================

@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_group_traffic(message: types.Message):
    global TARGET_GROUP_ID, COMPACT_PERM_APPLIED
    TARGET_GROUP_ID = message.chat.id
    if config.get("target_group_id") != message.chat.id:
        config["target_group_id"] = message.chat.id
        save_data()

    # পাবলিক গ্রুপ কমপ্যাক্ট লিংক পারমিশন প্রয়োগ
    if not COMPACT_PERM_APPLIED and config.get("disable_link_previews", True):
        COMPACT_PERM_APPLIED = True
        asyncio.create_task(apply_compact_link_permissions(message.chat.id))

    record_msg(message.chat.id, message.message_id)

    user = message.from_user
    if not user:
        return
    track_user(user)

    # মূল বট ওনারের ক্ষেত্রে কোনো ফিল্টারিং প্রযোজ্য নয়
    if user.id == ADMIN_ID:
        return

    # শাটডাউন চেক: গ্রুপ লক থাকলে মেসেজ সঙ্গে সঙ্গে ডিলিট
    if shutdown_state.get("is_shutdown", False):
        try:
            await message.delete()
        except Exception:
            pass
        return

    # পাবলিক গ্রুপ অ্যান্টি-ফ্লাড সুরক্ষা (স্প্যাম ও রেইড বট প্রতিরোধ)
    if check_user_flood(user.id):
        try:
            await message.delete()
        except Exception:
            pass
        return

    # গ্রুপ অ্যাডমিনদের ফিল্টার করা হবে কি না (টেস্টিং মোড)
    if not config.get("filter_admins", False):
        try:
            chat_member = await bot.get_chat_member(chat_id=message.chat.id, user_id=user.id)
            if is_real_group_admin(chat_member):
                return
        except Exception:
            pass

    name_safe = html.escape(user.full_name or user.first_name)
    user_link = f"<a href='tg://user?id={user.id}'>{name_safe}</a>"

    text_to_scan = message.text or message.caption or ""
    entities = message.entities or message.caption_entities or []
    for entity in entities:
        if entity.type == "text_link" and entity.url:
            text_to_scan += f" {entity.url}"
        elif entity.type in ["url", "mention"]:
            offset = entity.offset
            length = entity.length
            raw_val = (message.text or message.caption or "")[offset:offset+length]
            text_to_scan += f" {raw_val}"

    has_tg_link = bool(TG_LINK_REGEX.search(text_to_scan))
    has_any_link = bool(ANY_LINK_REGEX.search(text_to_scan)) or has_tg_link

    # দৃশ্যপট ১: সাধারণ টেক্সট বা ছবি (কোনো লিংক নেই)
    if not has_any_link:
        if config.get("delete_non_links", True):
            try:
                await message.delete()
            except Exception:
                pass

            raw_tpl = config.get(
                "msg_non_link_warn",
                "⚠️ {user_link}, এই গ্রুপে সাধারণ চ্যাট অনুমোদিত নয়! শুধুমাত্র ভেরিফাইড মেম্বাররা টেলিগ্রাম লিংক শেয়ার করতে পারেন।"
            )
            warn_txt = raw_tpl.replace("{user_link}", user_link)

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="ℹ️ ভেরিফিকেশন ও লিংক শেয়ার নিয়ম", callback_data=f"show_verify_info_{user.id}")]
            ])
            try:
                warn = await bot.send_message(
                    chat_id=message.chat.id,
                    text=warn_txt,
                    parse_mode="HTML",
                    reply_markup=kb
                )
                del_sec = config.get("non_link_warn_delete_sec", 8)
                asyncio.create_task(auto_delete(warn, del_sec))
            except Exception:
                pass
        return

    # দৃশ্যপট ২: লিংক আছে কিন্তু টেলিগ্রাম লিংক নয় (ইউটিউব, ওয়েবসাইট)
    if has_any_link and not has_tg_link and config.get("allow_only_tg_links", True):
        try:
            await message.delete()
        except Exception:
            pass

        raw_tpl = config.get(
            "msg_only_tg_warn",
            "⚠️ {user_link}, এই গ্রুপে <b>শুধুমাত্র টেলিগ্রাম লিংক</b> শেয়ার করা অনুমোদিত!"
        )
        warn_txt = raw_tpl.replace("{user_link}", user_link)
        try:
            warn = await bot.send_message(
                chat_id=message.chat.id,
                text=warn_txt,
                parse_mode="HTML"
            )
            del_sec = config.get("other_link_warn_delete_sec", 12)
            asyncio.create_task(auto_delete(warn, del_sec))
        except Exception:
            pass
        return

    # দৃশ্যপট ৩: টেলিগ্রাম লিংক পোস্ট করেছে -> ভেরিফিকেশন যাচাই
    if not config.get("require_verification", True):
        if str(user.id) in all_known_users:
            all_known_users[str(user.id)]["links_shared"] += 1
            save_data()
        return

    u_info = verified_users.get(str(user.id), {"version": 0, "click_time": 0})
    is_verified = (u_info.get("version") == config.get("current_version", 1))

    if not is_verified:
        try:
            await message.delete()
        except Exception:
            pass

        # মোড: অপশন C (উভয় অপশন: জয়েন রিকোয়েস্ট অথবা ৮ সেকেন্ডের ডাইরেক্ট অ্যাড লিংক)
        if config.get("mode") in ["both", "combined"]:
            # লাইভ চেক: ইউজার কি ইতিমধ্যে চ্যানেলে জয়েন আছে?
            try:
                target_chan = config.get("target_channel", "@romantic_video900")
                member = await bot.get_chat_member(chat_id=target_chan, user_id=user.id)
                if member.status in ["member", "administrator", "creator", "restricted"]:
                    await grant_user_verification(message.chat.id, user)
                    succ_tpl = config.get(
                        "msg_verify_success",
                        "🎉 {user_link}, আপনার ভেরিফিকেশন সফল হয়েছে! আপনার লিংক শেয়ারিং পারমিশন আনলক করা হয়েছে।"
                    )
                    succ_txt = succ_tpl.replace("{user_link}", user_link)
                    notice = await bot.send_message(
                        chat_id=message.chat.id,
                        text=succ_txt,
                        parse_mode="HTML"
                    )
                    del_sec = config.get("verify_success_delete_sec", 10)
                    asyncio.create_task(auto_delete(notice, del_sec))
                    return
            except Exception as e:
                print("Live channel check error:", e)

            # অ্যাড ট্র্যাকিং সেশন তৈরি
            token = uuid.uuid4().hex[:10]
            ad_sessions[token] = {
                "user_id": user.id,
                "created_at": time.time(),
                "wait_seconds": int(config.get("ad_wait_seconds", 8)),
                "clicked": False,
                "click_time": 0
            }
            try:
                bot_user = (await bot.get_me()).username
                track_url = f"https://t.me/{bot_user}?start=ad_{token}"
            except Exception:
                track_url = config.get("ad_link", "https://negotiatenapkin.com/x4ihpte44?key=4a61bc5be7fb6bf03e4b91ff497b17e6")

            btn_join = config.get("btn_join_req", "👉 চ্যানেলে জয়েন রিকোয়েস্ট পাঠান")
            btn_verify_req = config.get("btn_join_verify", "✅ রিকোয়েস্ট দিয়েছি (ভেরিফাই)")
            btn_ad_visit = f"🌐 অ্যাড লিংকে ৮ সেকেন্ড অপেক্ষা করুন"
            btn_verify_ad = "✅ ওয়েবসাইট ভেরিফাই সম্পন্ন করুন"

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=btn_join, url=config.get("target_channel_link", "https://t.me/romantic_video900"))],
                [InlineKeyboardButton(text=btn_verify_req, callback_data=f"v_req_{user.id}")],
                [InlineKeyboardButton(text=btn_ad_visit, url=track_url)],
                [InlineKeyboardButton(text=btn_verify_ad, callback_data=f"v_ad_{user.id}_{token}")]
            ])

            wait_s = config.get("ad_wait_seconds", 8)
            card_txt = (
                f"⚠️ {user_link}, গ্রুপে লিংক শেয়ারের অনুমতি পেতে নিচের যেকোনো <b>১টি পদ্ধতি</b> সম্পন্ন করুন:\n\n"
                f"🔹 <b>১ম পদ্ধতি:</b> মূল চ্যানেলে জয়েন রিকোয়েস্ট পাঠিয়ে ভেরিফাই চাপুন।\n"
                f"🔹 <b>২য় পদ্ধতি:</b> স্পন্সর ওয়েবসাইটে গিয়ে মাত্র <b>{wait_s} সেকেন্ড</b> অপেক্ষা করে ভেরিফাই চাপুন।\n\n"
                f"👇 <i>পছন্দমতো বোতাম বেছে নিন:</i>"
            )
            try:
                w = await bot.send_message(
                    chat_id=message.chat.id,
                    text=card_txt,
                    parse_mode="HTML",
                    reply_markup=kb
                )
                del_sec = config.get("verify_card_delete_sec", 30)
                asyncio.create_task(auto_delete(w, del_sec))
            except Exception as e:
                print("Error sending both mode card:", e)

        # মোড ১: চ্যানেল জয়েন রিকোয়েস্ট মোড
        elif config.get("mode") == "join_request":
            # লাইভ চেক: ইউজার কি ইতিমধ্যে চ্যানেলে জয়েন আছে?
            try:
                target_chan = config.get("target_channel", "@romantic_video900")
                member = await bot.get_chat_member(chat_id=target_chan, user_id=user.id)
                if member.status in ["member", "administrator", "creator", "restricted"]:
                    await grant_user_verification(message.chat.id, user)

                    succ_tpl = config.get(
                        "msg_verify_success",
                        "🎉 {user_link}, আপনার ভেরিফিকেশন সফল হয়েছে! আপনার লিংক শেয়ারিং পারমিশন আনলক করা হয়েছে।"
                    )
                    succ_txt = succ_tpl.replace("{user_link}", user_link)

                    notice = await bot.send_message(
                        chat_id=message.chat.id,
                        text=succ_txt,
                        parse_mode="HTML"
                    )
                    del_sec = config.get("verify_success_delete_sec", 10)
                    asyncio.create_task(auto_delete(notice, del_sec))
                    return
            except Exception as e:
                print("Live channel check error:", e)

            btn_join = config.get("btn_join_req", "👉 চ্যানেলে জয়েন রিকোয়েস্ট পাঠান")
            btn_verify = config.get("btn_join_verify", "✅ আমি রিকোয়েস্ট দিয়েছি (Verify)")

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=btn_join, url=config.get("target_channel_link", "https://t.me"))],
                [InlineKeyboardButton(text=btn_verify, callback_data=f"v_req_{user.id}")]
            ])

            raw_tpl = config.get(
                "msg_join_req_notice",
                "⚠️ {user_link}, গ্রুপে লিংক শেয়ার করার আগে আমাদের মূল চ্যানেলে <b>জয়েন রিকোয়েস্ট</b> পাঠাতে হবে!\n\n🔗 রিকোয়েস্ট পাঠিয়ে নিচের বোতামে চাপুন:"
            )
            card_txt = raw_tpl.replace("{user_link}", user_link)

            try:
                w = await bot.send_message(
                    chat_id=message.chat.id,
                    text=card_txt,
                    parse_mode="HTML",
                    reply_markup=kb
                )
                del_sec = config.get("verify_card_delete_sec", 30)
                asyncio.create_task(auto_delete(w, del_sec))
            except Exception as e:
                print("Error sending join request card:", e)

        # মোড ২: ডাইরেক্ট অ্যাড লিংক মোড
        elif config.get("mode") == "ad_link":
            token = uuid.uuid4().hex[:10]
            ad_sessions[token] = {
                "user_id": user.id,
                "created_at": time.time(),
                "wait_seconds": config.get("ad_wait_seconds", 15),
                "clicked": False,
                "click_time": 0
            }
            try:
                bot_user = (await bot.get_me()).username
                track_url = f"https://t.me/{bot_user}?start=ad_{token}"
            except Exception:
                track_url = config.get("ad_link", "https://google.com")

            btn_visit = config.get("btn_ad_visit", "🌐 মূল ওয়েবসাইটে যান (অপেক্ষা করুন)")
            btn_verify = config.get("btn_ad_verify", "✅ ভেরিফাই সম্পন্ন করুন")

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=btn_visit, url=track_url)],
                [InlineKeyboardButton(text=btn_verify, callback_data=f"v_ad_{user.id}_{token}")]
            ])

            raw_tpl = config.get(
                "msg_ad_link_notice",
                "⚠️ {user_link}, গ্রুপে লিংক শেয়ারের অনুমতি পেতে স্পন্সর ওয়েবসাইটে প্রবেশ করে পুরো <b>{wait_seconds} সেকেন্ড</b> অপেক্ষা করতে হবে!\n\n📌 <b>নির্দেশনা:</b>\n১. নিচের বোতাম চেপে ওয়েবসাইটে যান।\n২. পুরো {wait_seconds} সেকেন্ড অপেক্ষা করুন।\n৩. ফিরে এসে ভেরিফাই বোতাম চাপুন।"
            )
            card_txt = raw_tpl.replace("{user_link}", user_link).replace("{wait_seconds}", str(config.get("ad_wait_seconds", 15)))

            try:
                w = await bot.send_message(
                    chat_id=message.chat.id,
                    text=card_txt,
                    parse_mode="HTML",
                    reply_markup=kb
                )
                del_sec = config.get("verify_card_delete_sec", 30)
                asyncio.create_task(auto_delete(w, del_sec))
            except Exception as e:
                print("Error sending ad card:", e)
    else:
        # ভেরিফাইড মেম্বার লিংক শেয়ার করছে
        now_ts = time.time()
        if str(user.id) in all_known_users:
            all_known_users[str(user.id)]["links_shared"] = all_known_users[str(user.id)].get("links_shared", 0) + 1

        prof = get_user_profile(user.id, user)
        is_vip = prof.get("vip_until", 0) > now_ts
        has_pinned = prof.get("pinned_pass_until", 0) > now_ts

        # ১. গ্যামিফিকেশন পয়েন্ট আর্নিং
        if config.get("gamification_enabled", True):
            pts_link = config.get("points_per_link", 10)
            prof["points"] = prof.get("points", 0) + pts_link
            prof["links_shared_count"] = prof.get("links_shared_count", 0) + 1

        # ২. L4L সাপোর্ট তালিকায় লিংক নথিভুক্তকরণ
        if config.get("l4l_enabled", True):
            l4l_recent_links.append({
                "user_id": user.id,
                "name": user.full_name or user.first_name,
                "message_id": message.message_id,
                "time": now_ts
            })
            if len(l4l_recent_links) > 25:
                l4l_recent_links.pop(0)

        # ৩. স্মার্ট সেলফ-ডিলিট টাইমার
        del_hrs = config.get("auto_delete_links_hours", 0)
        if del_hrs > 0:
            asyncio.create_task(auto_delete(message, del_hrs * 3600))

        # ৪. পিন্ড মেসেজ পাস কার্যকর করা
        if has_pinned:
            try:
                await bot.pin_chat_message(chat_id=message.chat.id, message_id=message.message_id)
            except Exception:
                pass

        save_data()

        # ৫. নামের পাশে ভেরিফাই ব্যাজ নিশ্চিত করা
        if config.get("enable_admin_badge", True):
            asyncio.create_task(grant_user_verification(message.chat.id, user))

        # ৬. ভেরিফাইড লিংকে বিশেষ রিঅ্যাকশন দেওয়া (VIP মেম্বাররা স্টার ⭐ রিঅ্যাকশন পায়)
        if config.get("badge_reaction_enabled", True) and ReactionTypeEmoji:
            try:
                rx_emoji = "⭐" if is_vip else config.get("badge_reaction_emoji", "⚡")
                await bot.set_message_reaction(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    reaction=[ReactionTypeEmoji(emoji=rx_emoji)]
                )
            except Exception:
                pass

# ==================== ৯. ভেরিফিকেশন বাটন ও সহায়তা কলব্যাক ====================

@dp.callback_query(F.data.startswith("show_verify_info_"))
async def handle_show_verify_info(query: types.CallbackQuery):
    u_id = int(query.data.split("_")[3])
    if query.from_user.id != u_id:
        await query.answer("❌ এটি আপনার নোটিশ নয়!", show_alert=True)
        return

    u_info = verified_users.get(str(u_id), {"version": 0})
    if u_info.get("version") == config.get("current_version", 1):
        await query.answer("🎉 আপনি ইতিমধ্যে ভেরিফাইড! আপনি সরাসরি টেলিগ্রাম লিংক শেয়ার করতে পারেন।", show_alert=True)
        return

    if config.get("mode") == "join_request":
        await query.answer(
            f"ℹ️ নিয়মাবলী:\n১. মূল চ্যানেলে ({config.get('target_channel')}) জয়েন রিকোয়েস্ট পাঠান।\n২. তারপর গ্রুপে লিংক পোস্ট করার সময় ভেরিফাই বাটনে চাপুন।",
            show_alert=True
        )
    else:
        await query.answer(
            f"ℹ️ নিয়মাবলী:\n১. স্পন্সর ওয়েবসাইটে প্রবেশ করুন।\n২. পুরো {config.get('ad_wait_seconds', 15)} সেকেন্ড অবস্থান করুন।\n৩. তারপর ফিরে এসে ভেরিফাই বোতাম চাপুন।",
            show_alert=True
        )

@dp.callback_query(F.data.startswith("wel_verify_"))
async def handle_welcome_verify_click(query: types.CallbackQuery):
    u_id = int(query.data.split("_")[2])
    user = query.from_user
    if user.id != u_id:
        await query.answer("❌ এটি আপনার ভেরিফিকেশন বাটন নয়!", show_alert=True)
        return

    u_info = verified_users.get(str(u_id), {"version": 0})
    if u_info.get("version") == config.get("current_version", 1):
        await query.answer("🎉 আপনি ইতিমধ্যে ভেরিফাইড! সরাসরি লিংক শেয়ার করতে পারেন।", show_alert=True)
        return

    name_safe = html.escape(user.full_name or user.first_name)
    user_link = f"<a href='tg://user?id={user.id}'>{name_safe}</a>"

    if config.get("mode") == "join_request":
        btn_join = config.get("btn_join_req", "👉 চ্যানেলে জয়েন রিকোয়েস্ট পাঠান")
        btn_verify = config.get("btn_join_verify", "✅ আমি রিকোয়েস্ট দিয়েছি (Verify)")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=btn_join, url=config.get("target_channel_link", "https://t.me"))],
            [InlineKeyboardButton(text=btn_verify, callback_data=f"v_req_{user.id}")]
        ])
        raw_tpl = config.get(
            "msg_join_req_notice",
            "⚠️ {user_link}, গ্রুপে লিংক শেয়ার করার আগে আমাদের মূল চ্যানেলে <b>জয়েন রিকোয়েস্ট</b> পাঠাতে হবে!\n\n🔗 রিকোয়েস্ট পাঠিয়ে নিচের বোতামে চাপুন:"
        )
        card_txt = raw_tpl.replace("{user_link}", user_link)
        try:
            w = await bot.send_message(
                chat_id=query.message.chat.id,
                text=card_txt,
                parse_mode="HTML",
                reply_markup=kb
            )
            del_sec = config.get("verify_card_delete_sec", 30)
            asyncio.create_task(auto_delete(w, del_sec))
            await query.answer("ভেরিফিকেশন কার্ড পাঠানো হয়েছে!")
        except Exception as e:
            print("Error sending welcome verify prompt:", e)
            await query.answer("ত্রুটি হয়েছে, অনুগ্রহ করে আবার চেষ্টা করুন।")
    else:
        token = uuid.uuid4().hex[:10]
        ad_sessions[token] = {
            "user_id": user.id,
            "created_at": time.time(),
            "wait_seconds": config.get("ad_wait_seconds", 15),
            "clicked": False,
            "click_time": 0
        }
        try:
            bot_user = (await bot.get_me()).username
            track_url = f"https://t.me/{bot_user}?start=ad_{token}"
        except Exception:
            track_url = config.get("ad_link", "https://google.com")

        btn_visit = config.get("btn_ad_visit", "🌐 মূল ওয়েবসাইটে যান (অপেক্ষা করুন)")
        btn_verify = config.get("btn_ad_verify", "✅ ভেরিফাই সম্পন্ন করুন")

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=btn_visit, url=track_url)],
            [InlineKeyboardButton(text=btn_verify, callback_data=f"v_ad_{user.id}_{token}")]
        ])

        raw_tpl = config.get(
            "msg_ad_link_notice",
            "⚠️ {user_link}, গ্রুপে লিংক শেয়ারের অনুমতি পেতে স্পন্সর ওয়েবসাইটে প্রবেশ করে পুরো <b>{wait_seconds} সেকেন্ড</b> অপেক্ষা করতে হবে!\n\n📌 <b>নির্দেশনা:</b>\n১. নিচের বোতাম চেপে ওয়েবসাইটে যান।\n২. পুরো {wait_seconds} সেকেন্ড অপেক্ষা করুন।\n৩. ফিরে এসে ভেরিফাই বোতাম চাপুন।"
        )
        card_txt = raw_tpl.replace("{user_link}", user_link).replace("{wait_seconds}", str(config.get("ad_wait_seconds", 15)))

        try:
            w = await bot.send_message(
                chat_id=query.message.chat.id,
                text=card_txt,
                parse_mode="HTML",
                reply_markup=kb
            )
            del_sec = config.get("verify_card_delete_sec", 30)
            asyncio.create_task(auto_delete(w, del_sec))
            await query.answer("ভেরিফিকেশন কার্ড পাঠানো হয়েছে!")
        except Exception as e:
            print("Error sending welcome verify prompt:", e)
            await query.answer("ত্রুটি হয়েছে, অনুগ্রহ করে আবার চেষ্টা করুন।")

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
            target_chan = config.get("target_channel", "@romantic_video900")
            member = await bot.get_chat_member(chat_id=target_chan, user_id=u_id)
            if member.status in ["member", "administrator", "creator", "restricted"]:
                gid = query.message.chat.id if query.message.chat.type in ["group", "supergroup"] else (TARGET_GROUP_ID or config.get("target_group_id"))
                await grant_user_verification(gid, user)
                await query.answer("🎉 চমৎকার! আপনার চ্যানেল রিকোয়েস্ট পাওয়া গেছে। লিংক শেয়ারিং পারমিশন আনলক হয়েছে এবং নামের পাশে ভেরিফাই ব্যাজ যুক্ত হয়েছে।", show_alert=True)
                try:
                    await query.message.delete()
                except Exception:
                    pass
                return
        except Exception as e:
            print("Callback req check error:", e)
        await query.answer("❌ আপনি এখনো রিকোয়েস্ট পাঠাননি বা চ্যানেলে যোগ দেননি! দয়া করে চ্যানেলে জয়েন রিকোয়েস্ট দিন।", show_alert=True)

    elif v_type == "ad":
        token = parts[3] if len(parts) > 3 else None
        sess = ad_sessions.get(token) if token else None
        required = config.get("ad_wait_seconds", 15)

        # ১. ইউজার কি লিংকের ভেতরে প্রবেশ করেছে?
        if not sess or not sess.get("clicked", False):
            btn_visit_txt = config.get("btn_ad_visit", "🌐 মূল ওয়েবসাইটে যান (অপেক্ষা করুন)")
            await query.answer(
                f"❌ ভেরিফিকেশন ব্যর্থ!\n\n"
                f"আপনি এখনো ওয়েবসাইটের ভেতরে প্রবেশ করেননি! দয়া করে প্রথমে '{btn_visit_txt}' বোতামে চেপে ওয়েবসাইটে যান।",
                show_alert=True
            )
            return

        # ২. ইউজার কি নির্দিষ্ট সময় অপেক্ষা করেছে?
        start_time = sess.get("click_time", 0)
        elapsed = time.time() - start_time
        required = sess.get("wait_seconds", required)
        if elapsed < required:
            remaining = max(1, int(required - elapsed))
            await query.answer(
                f"⏳ আপনি নির্দিষ্ট সময় অপেক্ষা করেননি!\n\n"
                f"আপনি মাত্র {int(elapsed)} সেকেন্ড ছিলেন। নিয়ম অনুযায়ী আপনাকে আরও {remaining} সেকেন্ড ওয়েবসাইটে অবস্থান করতে হবে। সময় শেষ হওয়ার পর আবার চেষ্টা করুন।",
                show_alert=True
            )
            return

        # ৩. শতভাগ শর্ত পূরণ: ইউজার লিংকে গেছে এবং নির্দিষ্ট সময় অবস্থান করেছে
        gid = query.message.chat.id if query.message.chat.type in ["group", "supergroup"] else (TARGET_GROUP_ID or config.get("target_group_id"))
        await grant_user_verification(gid, user)

        if token in ad_sessions:
            del ad_sessions[token]

        await query.answer("🎉 চমৎকার! ভেরিফিকেশন সফল হয়েছে। আপনার লিংক শেয়ারিং পারমিশন আনলক হয়েছে এবং নামের পাশে ভেরিফাই ব্যাজ যুক্ত হয়েছে।", show_alert=True)
        try:
            await query.message.delete()
        except Exception:
            pass

# ==================== ১০. ব্যাকগ্রাউন্ড শিডিউলার্স ====================

async def shutdown_and_renew_scheduler():
    """
    ১. প্রতি renew_prompt_hours ঘণ্টা পর পর অ্যাডমিনের ইনবক্সে রিনিউ করার প্রম্পট পাঠাবে।
    ২. প্রতি ১ মিনিটে চেক করবে shutdown_duration_hours ঘণ্টা পার হয়েছে কি না। পার হলে গ্রুপ শাটডাউন করে দেবে।
    """
    while True:
        try:
            await asyncio.sleep(60)
            now = time.time()

            # ১. শাটডাউন টাইমার চেক
            if not shutdown_state.get("is_shutdown", False):
                if now >= shutdown_state.get("active_expiry", 0):
                    print("Shutdown timer triggered: Duration reached without renewal!")
                    await trigger_group_shutdown(source="timer")

            # ২. রিনিউ নোটিশ চেক
            if not shutdown_state.get("is_shutdown", False):
                last_prompt = shutdown_state.get("last_prompt_time", 0)
                renew_gap = config.get("renew_prompt_hours", 5) * 3600
                if now - last_prompt >= renew_gap:
                    shutdown_state["last_prompt_time"] = now
                    shutdown_state["prompt_count"] = shutdown_state.get("prompt_count", 0) + 1
                    save_data()

                    rem_sec = max(0, shutdown_state["active_expiry"] - now)
                    rem_str = format_time_remaining(rem_sec)
                    dur = config.get("shutdown_duration_hours", 24)

                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text=f"✅ কনফার্ম করুন (নতুন {dur} ঘণ্টা শুরু)", callback_data="renew_confirm"),
                            InlineKeyboardButton(text="❌ বাতিল (পূর্বের অবশিষ্ট সময় চলবে)", callback_data="renew_cancel")
                        ]
                    ])

                    prompt_msg = (
                        f"🔔 <b>গ্রুপ মেয়াদ রিনিউ নোটিফিকেশন ({config.get('renew_prompt_hours', 5)} ঘণ্টা ব্যবধান)</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"⏳ <b>পূর্বের সময় অনুযায়ী আর বাকি আছে:</b> <code>{rem_str}</code>\n\n"
                        f"আপনি কি এখনই গ্রুপটি রিনিউ করতে চান?\n\n"
                        f"👉 <b>'কনফার্ম করুন'</b> চাপলে এই মুহূর্ত থেকে নতুন <b>{dur} ঘণ্টা</b> শুরু হবে।\n"
                        f"👉 <b>'বাতিল'</b> চাপলে পূর্বে শুরু হওয়া সময়ের বাকি অংশ (<code>{rem_str}</code>) গ্রুপটি চলবে।"
                    )

                    try:
                        await bot.send_message(
                            chat_id=ADMIN_ID,
                            text=prompt_msg,
                            parse_mode="HTML",
                            reply_markup=kb
                        )
                    except Exception as e:
                        print("Error sending renewal prompt to admin:", e)

        except Exception as e:
            print("Error in shutdown_and_renew_scheduler:", e)
            await asyncio.sleep(10)

async def promo_broadcast_task():
    global last_promo_time
    while True:
        await asyncio.sleep(10)

        if shutdown_state.get("is_shutdown", False):
            continue

        if not config.get("promo_enabled", True):
            continue

        mins = config.get("broadcast_interval_mins", 60)
        target_interval_sec = max(60, mins * 60)

        if time.time() - last_promo_time >= target_interval_sec:
            last_promo_time = time.time()
            gid = TARGET_GROUP_ID or config.get("target_group_id")
            if gid:
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

                    del_sec = config.get("promo_delete_sec", 300)
                    if del_sec > 0:
                        asyncio.create_task(auto_delete(p_msg, del_sec))
                except Exception as e:
                    print("Error in promo_broadcast_task:", e)

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
