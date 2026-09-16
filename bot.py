import asyncio
import re
import time
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ----------------- কনফিগারেশন (আপনার তথ্য এখানে দিন) -----------------
BOT_TOKEN = "8879708023:AAFQhoDftLDHv11fVztRrnaexCy0zpNuvWc"  # আপনার বটের টোকেন দিন
ADMIN_ID = 1958884768                        # আপনার টেলিগ্রাম নিউমেরিক আইডি দিন

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ডাটাবেজ/মেমোরি ভেরিয়েবল
config = {
    "mode": "join_request",         # 'join_request' অথবা 'ad_link'
    "target_channel": "@YourChannelUsername", # চ্যানেল ইউজারনেম বা -100xxxxxxxxxx আইডি
    "target_channel_link": "https://t.me/YourChannelLink", # জয়েন রিকোয়েস্ট লিংক
    "ad_link": "https://your-direct-ad-link.com",          # ডাইরেক্ট অ্যাড লিংক
    "ad_wait_seconds": 15,          # অ্যাডে কত সেকেন্ড অপেক্ষা করতে হবে
    "promo_text": "🔥 সেরা টেলিগ্রাম চ্যানেল ও গ্রুপ পেতে আমাদের মেইন চ্যানেলে জয়েন করুন!",
    "promo_button_text": "🚀 Join Main Channel",
    "promo_button_link": "https://t.me/YourChannelLink",
    "broadcast_interval": 3600,     # প্রতি কত সেকেন্ড পর প্রমোশনাল মেসেজ যাবে (৩৬০০ সে. = ১ ঘণ্টা)
    "current_version": 1            # লিংক পরিবর্তন করলে এই সংখ্যা বাড়িয়ে ইউজার রিসেট হবে
}

# ব্যবহারকারীদের ভেরিফিকেশন স্টেট: {user_id: {"version": 1, "click_time": 0}}
verified_users = {}

# মেসেজ স্বয়ংক্রিয়ভাবে মুছে ফেলার হেল্পার ফাংশন
async def delete_after_delay(message: types.Message, delay: int = 15):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass

# ----------------- ১. সার্ভিস মেসেজ ক্লিনার -----------------
# কেউ গ্রুপে ঢুকলে বা বের হলে আসা মেসেজ সাথে সাথে ডিলিট করবে
@dp.message(F.content_type.in_({'new_chat_members', 'left_chat_member', 'pinned_message'}))
async def clean_service_messages(message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass

# ----------------- ২. নতুন মেম্বার ওয়েলকাম মেসেজ -----------------
@dp.chat_member()
async def welcome_new_member(event: types.ChatMemberUpdated):
    if event.new_chat_member.status == "member" and event.old_chat_member.status in ["left", "kicked"]:
        user = event.new_chat_member.user
        group_username = event.chat.username or ""
        share_url = f"https://t.me/share/url?url=https://t.me/{group_username}&text=Join%20this%20awesome%20link%20sharing%20group!"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 বন্ধুদের সাথে শেয়ার করুন", url=share_url)]
        ])
        
        msg = await bot.send_message(
            chat_id=event.chat.id,
            text=f"👋 স্বাগতম [{user.first_name}](tg://user?id={user.id}) আমাদের গ্রুপে!\nএখানে শুধুমাত্র টেলিগ্রামের লিংক শেয়ার করতে পারবেন।",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        # ওয়েলকাম মেসেজটিও ৩০ সেকেন্ড পর মুছে যাবে যাতে চ্যাট ক্লিন থাকে
        asyncio.create_task(delete_after_delay(msg, 30))

# ----------------- ৩. গ্রুপের মেসেজ ফিল্টারিং ও গেটওয়ে -----------------
TELEGRAM_LINK_REGEX = re.compile(r'(https?://)?(www\.)?(t\.me|telegram\.me)/[a-zA-Z0-9_+/?=-]+', re.IGNORECASE)

@dp.message(F.chat.type.in_({'group', 'supergroup'}))
async def group_message_handler(message: types.Message):
    # অ্যাডমিনদের মেসেজ ফিল্টার হবে না
    if message.from_user.id == ADMIN_ID:
        return

    text = message.text or message.caption or ""
    user_id = message.from_user.id

    # রুলস ১: টেক্সট, ফটো, স্টিকার চেক - শুধুমাত্র টেলিগ্রাম লিংক এলাউড
    is_tg_link = bool(TELEGRAM_LINK_REGEX.search(text))
    
    # টেলিগ্রাম লিংক ছাড়া অন্য কিছু (টেক্সট, স্টিকার, মিডিয়া বা অন্য লিংক) দিলে ডিলিট
    if not is_tg_link or message.content_type not in {'text'}:
        try:
            await message.delete()
        except Exception:
            pass
        return

    # রুলস ২: ইউজার ভেরিফিকেশন চেক (Force Join বা Ad Link)
    user_data = verified_users.get(user_id, {"version": 0, "click_time": 0})
    is_verified = (user_data["version"] == config["current_version"])

    if not is_verified:
        # মেসেজটি মুছে দেওয়া
        try:
            await message.delete()
        except Exception:
            pass

        # গেটওয়ে মোড ১: জয়েন রিকোয়েস্ট চেক
        if config["mode"] == "join_request":
            try:
                member = await bot.get_chat_member(chat_id=config["target_channel"], user_id=user_id)
                # মেম্বার অথবা রিকোয়েস্ট পেন্ডিং থাকলেও এলাউড
                if member.status in ["member", "administrator", "creator", "restricted"]:
                    verified_users[user_id] = {"version": config["current_version"], "click_time": 0}
                    return
            except Exception:
                pass  # এখনো রিকোয়েস্ট বা জয়েন করেনি

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👉 এখানে জয়েন রিকোয়েস্ট পাঠান", url=config["target_channel_link"])],
                [InlineKeyboardButton(text="✅ আমি রিকোয়েস্ট পাঠিয়েছি (Verify)", callback_data=f"verify_req_{user_id}")]
            ])
            warn_msg = await message.answer(
                f"⚠️ [{message.from_user.first_name}](tg://user?id={user_id}), গ্রুপে লিংক শেয়ার করার আগে আমাদের চ্যানেলে জয়েন রিকোয়েস্ট পাঠাতে হবে!",
                parse_mode="Markdown",
                reply_markup=kb
            )
            asyncio.create_task(delete_after_delay(warn_msg, 20))

        # গেটওয়ে মোড ২: ডাইরেক্ট অ্যাড লিংক ভিজিট
        elif config["mode"] == "ad_link":
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🌐 লিংকে গিয়ে অপেক্ষা করুন", url=config["ad_link"])],
                [InlineKeyboardButton(text="✅ ভেরিফাই করুন", callback_data=f"verify_ad_{user_id}")]
            ])
            warn_msg = await message.answer(
                f"⚠️ [{message.from_user.first_name}](tg://user?id={user_id}), লিংক শেয়ার আনলক করতে নিচের ওয়েবসাইটে গিয়ে {config['ad_wait_seconds']} সেকেন্ড অপেক্ষা করে ভেরিফাই বাটনে চাপ দিন!",
                parse_mode="Markdown",
                reply_markup=kb
            )
            # ভিজিট শুরুর টাইম রেকর্ড করা
            if user_id not in verified_users:
                verified_users[user_id] = {"version": 0, "click_time": time.time()}
            else:
                verified_users[user_id]["click_time"] = time.time()

            asyncio.create_task(delete_after_delay(warn_msg, 20))

# ----------------- ৪. ভেরিফিকেশন বাটন হ্যান্ডলার -----------------
@dp.callback_query(F.data.startswith("verify_"))
async def callback_verify(query: types.CallbackQuery):
    data_parts = query.data.split("_")
    action = data_parts[1]
    target_user_id = int(data_parts[2])

    if query.from_user.id != target_user_id:
        await query.answer("❌ এটি আপনার জন্য নয়!", show_alert=True)
        return

    if action == "req":
        try:
            member = await bot.get_chat_member(chat_id=config["target_channel"], user_id=target_user_id)
            if member.status in ["member", "administrator", "creator", "restricted"]:
                verified_users[target_user_id] = {"version": config["current_version"], "click_time": 0}
                await query.answer("🎉 অভিনন্দন! আপনার ভেরিফিকেশন সফল হয়েছে। এখন লিংক শেয়ার করতে পারবেন।", show_alert=True)
                try:
                    await query.message.delete()
                except Exception:
                    pass
                return
        except Exception:
            pass
        await query.answer("❌ আপনি এখনো রিকোয়েস্ট পাঠাননি! দয়া করে আগে রিকোয়েস্ট পাঠান।", show_alert=True)

    elif action == "ad":
        user_info = verified_users.get(target_user_id, {"version": 0, "click_time": 0})
        elapsed = time.time() - user_info.get("click_time", 0)
        required = config["ad_wait_seconds"]

        if elapsed >= required:
            verified_users[target_user_id] = {"version": config["current_version"], "click_time": 0}
            await query.answer("🎉 ভেরিফিকেশন সফল! এখন থেকে আপনি লিংক শেয়ার করতে পারবেন।", show_alert=True)
            try:
                await query.message.delete()
            except Exception:
                pass
        else:
            remaining = int(required - elapsed)
            await query.answer(f"⏳ অনুগ্রহ করে আরও {remaining} সেকেন্ড অপেক্ষা করুন!", show_alert=True)

# ----------------- ৫. সেলফ-ডেস্ট্রাক্টিং অ্যাডমিন কন্ট্রোল প্যানেল -----------------
ADMIN_MESSAGES = []  # চ্যাট ওয়াইপ করার জন্য মেসেজ আইডি ট্র্যাক করা

async def track_and_auto_delete(chat_id: int, message_id: int, delay: int = 45):
    ADMIN_MESSAGES.append(message_id)
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        if message_id in ADMIN_MESSAGES:
            ADMIN_MESSAGES.remove(message_id)
    except Exception:
        pass

@dp.message(Command("panel"), F.chat.type == "private")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    ADMIN_MESSAGES.append(message.message_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🔄 মোড পরিবর্তন (বর্তমান: {config['mode']})", callback_data="toggle_mode")],
        [InlineKeyboardButton(text="♻️ সমস্ত ইউজার রিসেট করুন (Reset All)", callback_data="reset_users")],
        [InlineKeyboardButton(text="❌ চ্যাট ক্লোজ ও ডিলিট করুন (Wipe)", callback_data="wipe_chat")]
    ])

    text = (
        "👑 **অ্যাডমিন কন্ট্রোল প্যানেল**\n\n"
        f"• বর্তমান মোড: `{config['mode']}`\n"
        f"• টার্গেট চ্যানেল: `{config['target_channel']}`\n"
        f"• অ্যাড লিংক: `{config['ad_link']}`\n"
        f"• ভেরিফিকেশন ভার্সন: `{config['current_version']}`\n\n"
        "💡 *যেকোনো সময় সব হিস্ট্রি মুছতে 'Wipe' বাটনে চাপ দিন।*"
    )
    panel_msg = await message.answer(text, parse_mode="Markdown", reply_markup=kb)
    asyncio.create_task(track_and_auto_delete(message.chat.id, panel_msg.message_id, 60))

@dp.callback_query(F.data.in_({"toggle_mode", "reset_users", "wipe_chat"}))
async def admin_actions(query: types.CallbackQuery):
    if query.from_user.id != ADMIN_ID:
        return

    if query.data == "toggle_mode":
        config["mode"] = "ad_link" if config["mode"] == "join_request" else "join_request"
        await query.answer(f"মোড পরিবর্তন করা হয়েছে: {config['mode']}", show_alert=True)
        await admin_panel(query.message)

    elif query.data == "reset_users":
        config["current_version"] += 1  # ভার্সন বাড়ালেই আগের সব ইউজার রিসেট হয়ে যাবে
        await query.answer("✅ সমস্ত ইউজার রিসেট হয়েছে! এখন সবাইকে আবার ভেরিফাই করতে হবে।", show_alert=True)

    elif query.data == "wipe_chat":
        await query.answer("🧹 সমস্ত অ্যাডমিন চ্যাট ডিলিট করা হচ্ছে...")
        for mid in list(ADMIN_MESSAGES):
            try:
                await bot.delete_message(chat_id=query.message.chat.id, message_id=mid)
            except Exception:
                pass
        ADMIN_MESSAGES.clear()

# ----------------- ৬. অটো শিডিউলার ব্রডকাস্ট -----------------
async def auto_promo_scheduler(target_group_id: int):
    while True:
        await asyncio.sleep(config["broadcast_interval"])
        try:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=config["promo_button_text"], url=config["promo_button_link"])]
            ])
            await bot.send_message(
                chat_id=target_group_id,
                text=config["promo_text"],
                reply_markup=kb
            )
        except Exception:
            pass

# ----------------- মেইন রানার -----------------
async def main():
    print("🚀 টেলিগ্রাম বট চালু হয়েছে...")
    # আপনার গ্রুপের আইডি দিন (যেমন: -100xxxxxxxxxx)
    TARGET_GROUP_ID = -1001234567890 
    asyncio.create_task(auto_promo_scheduler(TARGET_GROUP_ID))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
