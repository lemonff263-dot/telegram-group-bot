# -*- coding: utf-8 -*-
import asyncio
import os
import re
import time
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ----------------- কনফিগারেশন -----------------
BOT_TOKEN = "8879708023:AAE3tL5Rfdk0IZC7-hR92c-p3H6y9G_Ww40"
ADMIN_ID = 1958884768
TARGET_GROUP_ID = None

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

config = {
    "mode": "join_request",
    "target_channel": "@YourChannelName",
    "target_channel_link": "https://t.me/YourChannelLink",
    "ad_link": "https://google.com",
    "ad_wait_seconds": 15,
    "promo_text": "🔥 সেরা টেলিগ্রাম চ্যানেল ও গ্রুপের জন্য আমাদের মেইন চ্যানেলে জয়েন করুন!",
    "promo_btn_text": "🚀 জয়েন করুন",
    "promo_btn_link": "https://t.me/YourChannelLink",
    "broadcast_interval": 3600,
    "current_version": 1
}

# গ্রুপ মেসেজ হিস্টরি ট্র্যাকিং (message_id, timestamp)
GROUP_MESSAGES = {}  # {chat_id: [(msg_id, timestamp)]}
verified_users = {}

async def auto_delete(msg: types.Message, delay: int = 15):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass

# ----------------- মেসেজ সংরক্ষণ (ক্লিনআপের জন্য) -----------------
def record_msg(chat_id: int, msg_id: int):
    if chat_id not in GROUP_MESSAGES:
        GROUP_MESSAGES[chat_id] = []
    GROUP_MESSAGES[chat_id].append((msg_id, time.time()))
    # ৪৮ ঘণ্টার বেশি পুরোনো মেমোরি থেকে মুছে ফেলা
    cutoff = time.time() - (48 * 3600)
    GROUP_MESSAGES[chat_id] = [m for m in GROUP_MESSAGES[chat_id] if m[1] >= cutoff]

# ----------------- ১. সার্ভিস মেসেজ ক্লিনার -----------------
@dp.message(F.content_type.in_({'new_chat_members', 'left_chat_member', 'pinned_message'}))
async def clean_service_messages(message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass

# ----------------- ২. নতুন মেম্বার ওয়েলকাম মেসেজ -----------------
@dp.chat_member()
async def welcome_member(event: types.ChatMemberUpdated):
    if event.new_chat_member.status == "member" and event.old_chat_member.status in ["left", "kicked"]:
        user = event.new_chat_member.user
        group_username = event.chat.username or ""
        share_url = f"https://t.me/share/url?url=https://t.me/{group_username}&text=Join%20our%20link%20sharing%20group!"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 বন্ধুদের শেয়ার করুন", url=share_url)]
        ])
        try:
            msg = await bot.send_message(
                chat_id=event.chat.id,
                text=f"👋 স্বাগতম [{user.first_name}](tg://user?id={user.id})!\nএখানে শুধুমাত্র টেলিগ্রামের লিংক শেয়ার করতে পারবেন।",
                parse_mode="Markdown",
                reply_markup=kb
            )
            record_msg(event.chat.id, msg.message_id)
            asyncio.create_task(auto_delete(msg, 25))
        except Exception:
            pass

# ----------------- ৩. মেসেজ ফিল্টারিং ও গ্রুপ হিস্টরি ট্র্যাকিং -----------------
TG_LINK_REGEX = re.compile(r'(https?://)?(www\.)?(t\.me|telegram\.me)/[a-zA-Z0-9_+/?=-]+', re.IGNORECASE)

@dp.message(F.chat.type.in_({'group', 'supergroup'}))
async def filter_group_messages(message: types.Message):
    global TARGET_GROUP_ID
    TARGET_GROUP_ID = message.chat.id
    record_msg(message.chat.id, message.message_id)

    # ক্লিন কমান্ড ইত্যাদি থাকলে হ্যান্ডেল যাতে বিঘ্ন না ঘটে
    if message.text and message.text.startswith("/"):
        return

    # অ্যাডমিনদের মেসেজ ফিল্টার হবে না
    if message.from_user.id == ADMIN_ID:
        return

    text = message.text or message.caption or ""
    user_id = message.from_user.id

    # শুধুমাত্র টেক্সট এবং টেলিগ্রাম লিংক অনুমোদিত
    is_tg = bool(TG_LINK_REGEX.search(text))
    if not is_tg or message.content_type != 'text':
        try:
            await message.delete()
        except Exception:
            pass
        return

    # ভেরিফিকেশন চেক
    u_info = verified_users.get(user_id, {"version": 0, "click_time": 0})
    if u_info["version"] != config["current_version"]:
        try:
            await message.delete()
        except Exception:
            pass

        if config["mode"] == "join_request":
            try:
                member = await bot.get_chat_member(chat_id=config["target_channel"], user_id=user_id)
                if member.status in ["member", "administrator", "creator", "restricted"]:
                    verified_users[user_id] = {"version": config["current_version"], "click_time": 0}
                    return
            except Exception:
                pass

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👉 জয়েন রিকোয়েস্ট পাঠান", url=config["target_channel_link"])],
                [InlineKeyboardButton(text="✅ আমি রিকোয়েস্ট দিয়েছি (Verify)", callback_data=f"v_req_{user_id}")]
            ])
            w = await message.answer(
                f"⚠️ [{message.from_user.first_name}](tg://user?id={user_id}), গ্রুপে পোস্ট করার আগে আমাদের চ্যানেলে জয়েন রিকোয়েস্ট পাঠাতে হবে!",
                parse_mode="Markdown",
                reply_markup=kb
            )
            asyncio.create_task(auto_delete(w, 20))

        elif config["mode"] == "ad_link":
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🌐 লিংকে গিয়ে অপেক্ষা করুন", url=config["ad_link"])],
                [InlineKeyboardButton(text="✅ ভেরিফাই করুন", callback_data=f"v_ad_{user_id}")]
            ])
            w = await message.answer(
                f"⚠️ [{message.from_user.first_name}](tg://user?id={user_id}), লিংক শেয়ার আনলক করতে নিচের ওয়েবসাইটে গিয়ে {config['ad_wait_seconds']} সেকেন্ড অপেক্ষা করে ভেরিফাই বাটনে চাপ দিন!",
                parse_mode="Markdown",
                reply_markup=kb
            )
            verified_users[user_id] = {"version": 0, "click_time": time.time()}
            asyncio.create_task(auto_delete(w, 20))

# ----------------- ৪. ঘন্টা অনুযায়ী চ্যাট ডিলিট কমান্ড (/clean) -----------------
@dp.message(Command("clean"), F.chat.type.in_({'group', 'supergroup'}))
async def cmd_clean_prompt(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    # /clean 2 সরাসরি দেওয়া আছে কি না চেক
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        hours = int(args[1])
        await execute_clean(message.chat.id, hours, message)
        return

    # অপশন বাটন দেওয়া
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏱️ ১ ঘন্টা", callback_data="clean_1"),
            InlineKeyboardButton(text="⏱️ ২ ঘন্টা", callback_data="clean_2"),
            InlineKeyboardButton(text="⏱️ ৬ ঘন্টা", callback_data="clean_6")
        ],
        [
            InlineKeyboardButton(text="⏱️ ১২ ঘন্টা", callback_data="clean_12"),
            InlineKeyboardButton(text="⏱️ ২৪ ঘন্টা", callback_data="clean_24"),
            InlineKeyboardButton(text="⏱️ ৪৮ ঘন্টা", callback_data="clean_48")
        ],
        [InlineKeyboardButton(text="❌ বাতিল করুন", callback_data="clean_cancel")]
    ])
    ask_msg = await message.reply(
        "🗑️ *চ্যাট ডিলিট মেনু*\n\nআপনি কত ঘন্টার চ্যাট মুছে ফেলতে চান তা নির্বাচন করুন, অথবা সরাসরি `/clean <ঘন্টা>` লিখুন (যেমন: `/clean 3`):",
        parse_mode="Markdown",
        reply_markup=kb
    )
    asyncio.create_task(auto_delete(message, 15))
    asyncio.create_task(auto_delete(ask_msg, 40))

@dp.callback_query(F.data.startswith("clean_"))
async def handle_clean_callback(query: types.CallbackQuery):
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ এটি শুধুমাত্র গ্রুপের মূল অ্যাডমিনের জন্য!", show_alert=True)
        return

    if query.data == "clean_cancel":
        await query.message.delete()
        return

    hours = int(query.data.split("_")[1])
    await query.answer(f"🧹 গত {hours} ঘণ্টার চ্যাট মোছা শুরু হচ্ছে...", show_alert=False)
    await execute_clean(query.message.chat.id, hours, query.message)

async def execute_clean(chat_id: int, hours: int, trigger_msg: types.Message):
    now = time.time()
    cutoff = now - (hours * 3600)

    # মেমোরিতে ট্র্যাক করা মেসেজ এবং সাম্প্রতিক আইডি ডিলিট করা
    current_mid = trigger_msg.message_id
    tracked = GROUP_MESSAGES.get(chat_id, [])
    to_delete = set([m[0] for m in tracked if m[1] >= cutoff])

    # সাম্প্রতিক মেসেজ আইডি রেঞ্জ স্ক্যান (যদি আগে থেকে মেমোরিতে না থাকে)
    # গড়ে প্রতি ঘণ্টায় ৫০-২০০ মেসেজের অনুমান করে রেঞ্জ নেওয়া
    estimated_count = min(hours * 150, 1000)
    for mid in range(current_mid, max(1, current_mid - estimated_count), -1):
        to_delete.add(mid)

    deleted_count = 0
    for mid in to_delete:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=mid)
            deleted_count += 1
            await asyncio.sleep(0.05)  # Telegram Flood limit protection
        except Exception:
            pass

    # মেমোরি আপডেট
    if chat_id in GROUP_MESSAGES:
        GROUP_MESSAGES[chat_id] = [m for m in GROUP_MESSAGES[chat_id] if m[1] < cutoff]

    done = await bot.send_message(
        chat_id=chat_id,
        text=f"✅ *সাফাই সম্পন্ন!* গত *{hours} ঘণ্টার* মোট {deleted_count}টি মেসেজ সফলভাবে মুছে ফেলা হয়েছে।",
        parse_mode="Markdown"
    )
    asyncio.create_task(auto_delete(done, 15))

# ----------------- ৫. ভেরিফিকেশন বাটন হ্যান্ডলার -----------------
@dp.callback_query(F.data.startswith("v_"))
async def handle_verification(query: types.CallbackQuery):
    parts = query.data.split("_")
    v_type = parts[1]
    u_id = int(parts[2])

    if query.from_user.id != u_id:
        await query.answer("❌ এটি আপনার জন্য নয়!", show_alert=True)
        return

    if v_type == "req":
        try:
            member = await bot.get_chat_member(chat_id=config["target_channel"], user_id=u_id)
            if member.status in ["member", "administrator", "creator", "restricted"]:
                verified_users[u_id] = {"version": config["current_version"], "click_time": 0}
                await query.answer("🎉 ভেরিফিকেশন সফল! এখন লিংক শেয়ার করতে পারবেন।", show_alert=True)
                try:
                    await query.message.delete()
                except Exception:
                    pass
                return
        except Exception:
            pass
        await query.answer("❌ আপনি এখনো রিকোয়েস্ট পাঠাননি! দয়া করে আগে চ্যানেলে জয়েন রিকোয়েস্ট দিন।", show_alert=True)

    elif v_type == "ad":
        u_info = verified_users.get(u_id, {"version": 0, "click_time": 0})
        elapsed = time.time() - u_info.get("click_time", 0)
        if elapsed >= config["ad_wait_seconds"]:
            verified_users[u_id] = {"version": config["current_version"], "click_time": 0}
            await query.answer("🎉 ভেরিফিকেশন সফল! এখন লিংক শেয়ার করতে পারবেন।", show_alert=True)
            try:
                await query.message.delete()
            except Exception:
                pass
        else:
            rem = int(config["ad_wait_seconds"] - elapsed)
            await query.answer(f"⏳ অনুগ্রহ করে আরও {rem} সেকেন্ড অপেক্ষা করুন!", show_alert=True)

ADMIN_MSGS = []

# ----------------- ৬. সেলফ-ডেস্ট্রাক্টিং অ্যাডমিন প্যানেল -----------------
@dp.message(Command("panel"), F.chat.type == "private")
async def cmd_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    ADMIN_MSGS.append(message.message_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🔄 মোড পরিবর্তন (বর্তমান: {config['mode']})", callback_data="adm_mode")],
        [InlineKeyboardButton(text="♻️ সমস্ত ইউজার রিসেট (Reset All)", callback_data="adm_reset")],
        [InlineKeyboardButton(text="❌ চ্যাট ক্লোজ ও মুছুন (Wipe)", callback_data="adm_wipe")]
    ])

    text = (
        "👑 **অ্যাডমিন কন্ট্রোল প্যানেল**\n\n"
        f"• বর্তমান মোড: `{config['mode']}`\n"
        f"• টার্গেট চ্যানেল: `{config['target_channel']}`\n"
        f"• চ্যানেল লিংক: `{config['target_channel_link']}`\n"
        f"• অ্যাড লিংক: `{config['ad_link']}`\n"
        f"• অপেক্ষা সময়: `{config['ad_wait_seconds']} সেকেন্ড`\n"
        f"• ভার্সন: `{config['current_version']}`\n\n"
        "💡 *কমান্ডের মাধ্যমে দ্রুত পরিবর্তন করতে পারেন:*\n"
        "👉 `/setchannel @username`\n"
        "👉 `/setlink https://t.me/...`\n"
        "👉 `/setad https://...`\n"
        "👉 `/setwait 15` (সেকেন্ড)\n"
        "👉 গ্রুপে লিখুন: `/clean` বা `/clean 3` (নির্দিষ্ট ঘণ্টার চ্যাট মুছতে)"
    )
    p = await message.answer(text, parse_mode="Markdown", reply_markup=kb)
    ADMIN_MSGS.append(p.message_id)

@dp.callback_query(F.data.startswith("adm_"))
async def handle_adm_callbacks(query: types.CallbackQuery):
    if query.from_user.id != ADMIN_ID:
        return
    if query.data == "adm_mode":
        config["mode"] = "ad_link" if config["mode"] == "join_request" else "join_request"
        await query.answer(f"মোড বদলানো হয়েছে: {config['mode']}", show_alert=True)
        await cmd_panel(query.message)
    elif query.data == "adm_reset":
        config["current_version"] += 1
        await query.answer("✅ সমস্ত পুরোনো ইউজার রিসেট হয়েছে! সবাইকে আবার ভেরিফাই করতে হবে।", show_alert=True)
    elif query.data == "adm_wipe":
        for m in list(ADMIN_MSGS):
            try:
                await bot.delete_message(chat_id=query.message.chat.id, message_id=m)
            except Exception:
                pass
        ADMIN_MSGS.clear()

@dp.message(Command("setchannel"), F.chat.type == "private")
async def cmd_setchannel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) > 1:
        config["target_channel"] = args[1]
        m = await message.answer(f"✅ টার্গেট চ্যানেল সেট হয়েছে: `{args[1]}`", parse_mode="Markdown")
        asyncio.create_task(auto_delete(message, 15))
        asyncio.create_task(auto_delete(m, 15))

@dp.message(Command("setlink"), F.chat.type == "private")
async def cmd_setlink(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) > 1:
        config["target_channel_link"] = args[1]
        m = await message.answer(f"✅ চ্যানেল রিকোয়েস্ট লিংক সেট হয়েছে: `{args[1]}`", parse_mode="Markdown")
        asyncio.create_task(auto_delete(message, 15))
        asyncio.create_task(auto_delete(m, 15))

@dp.message(Command("setad"), F.chat.type == "private")
async def cmd_setad(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) > 1:
        config["ad_link"] = args[1]
        m = await message.answer(f"✅ ডাইরেক্ট অ্যাড লিংক সেট হয়েছে: `{args[1]}`", parse_mode="Markdown")
        asyncio.create_task(auto_delete(message, 15))
        asyncio.create_task(auto_delete(m, 15))

@dp.message(Command("setwait"), F.chat.type == "private")
async def cmd_setwait(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        config["ad_wait_seconds"] = int(args[1])
        m = await message.answer(f"✅ অ্যাড ওয়েট টাইম সেট হয়েছে: `{args[1]} সেকেন্ড`", parse_mode="Markdown")
        asyncio.create_task(auto_delete(message, 15))
        asyncio.create_task(auto_delete(m, 15))

# ----------------- ৭. প্রমোশনাল অটো শিডিউলার -----------------
async def promo_broadcast_task():
    while True:
        await asyncio.sleep(config["broadcast_interval"])
        if TARGET_GROUP_ID:
            try:
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=config["promo_btn_text"], url=config["promo_btn_link"])]
                ])
                await bot.send_message(chat_id=TARGET_GROUP_ID, text=config["promo_text"], reply_markup=kb)
            except Exception:
                pass

# ----------------- ৮. মেইন রানার -----------------
async def main():
    print("🚀 টেলিগ্রাম সেশন রিসেট করা হচ্ছে...")
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(promo_broadcast_task())
    print("🚀 টেলিগ্রাম বট সফলভাবে চালু হয়েছে এবং কাজ করছে!")
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())