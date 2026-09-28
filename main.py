import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import datetime
import time

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==========================================
# 1. БАЗА ДАНИХ (ПРОГРЕС БЕЗ ТАЙМ-ЛОКІВ)
# ==========================================
def init_db():
    conn = sqlite3.connect("blind_secrets.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            current_page INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

init_db()

def check_time_lock(user_id, hours_required=5):
    return True, 0

def update_player_page(user_id, page_num):
    conn = sqlite3.connect("blind_secrets.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO players (user_id) VALUES (?)", (user_id,))
    cursor.execute("UPDATE players SET current_page = ? WHERE user_id = ?", (page_num, user_id))
    conn.commit()
    conn.close()

# ==========================================
# 2. МАСШТАБНИЙ СЮЖЕТНИЙ ТЕКСТ (ТАЄМНИЦЯ СЛІПОТИ)
# ==========================================
STORY_PAGES = {
    1: (
        "**PROLOGUE: The Gateway of Echoes (Part 1)** 🌧️\n\n"
        "The iron gates of the Sakamaki mansion closed behind you with a heavy, definitive clang. "
        "To anyone else, this place is a gothic nightmare of towering black stone. "
        "But to you, Lybid, the world doesn't exist in colors or shapes.\n\n"
        "Your world is a canvas of physical frequencies. You keep your white cane folded and hidden securely inside your long coat. "
        "They must never know your secret. As the heavy wooden front door creaks open, your leather boots step onto the marble floor. "
        "The subtle vibrations travel through the immense foyer, mapping out high ceilings, grand staircases, and thick curtains in your mind. "
        "You lock your gaze directly ahead, flawlessly simulating a girl who sees everything, while seeing absolutely nothing."
    ),
    2: (
        "**PROLOGUE: The Gateway of Echoes (Part 2)** ⚡\n\n"
        "You step into the main hall. The air inside is dead, frozen in time, smelling of ancient dust and expensive wax. "
        "Your mind remains a fortress of cold realism. You do not believe in supernatural fairy tales. "
        "If there are aristocratic monsters here, they are bound by biological laws, and anything with a pulse can be calculated.\n\n"
        "You position your head precisely toward the center of the hall, looking toward the grand staircase. "
        "To any onlooker, you appear calm, arrogant, and deeply observant. Your total blindness is your ultimate hidden weapon."
    ),
    3: (
        "**CHAPTER 1: The Raging Ivory (Part 1)** 👣\n\n"
        "Suddenly, the ground beneath your boots shifts. Your flawless seismic sense registers a sharp shockwave. "
        "Someone is moving. Fast. Aggressive. Chaotic, furious footsteps crash against the upper steps, sending tremors vibrating straight through your spine.\n\n"
        "You instantly pivot your face exactly toward the source of the sound, tracking the sudden displacement of air. "
        "A young male descends, stopping mere inches from you. You can hear his rapid, irregular breathing. "
        "You focus your unseeing purple eyes right on his facial level, perfectly pretending to stare him down in the dim light."
    ),
    4: (
        "**CHAPTER 1: The Raging Ivory (Part 2)** 🤍\n\n"
        "Without a single word of warning, the air splits. *BANG!* \n"
        "A fist violently smashes into the stone wall right next to your left ear. Plaster crumbles onto your shoulder. "
        "Through the floorboards, you felt the exact trajectory of his arm a fraction of a second before the impact. You didn't even flinch.\n\n"
        "A harsh, arrogant voice cuts through the silence, dripping with pure venom:\n"
        "*«Hey, you! What the hell are you doing here? This isn't a playground for pathetic humans. Get lost before I tear you to pieces!»*\n"
        "It's **Subaru Sakamaki**. He glares at you, completely convinced that you are staring directly back into his furious crimson eyes."
    ),
    5: (
        "**CHAPTER 2: Whispers in the Dark (Part 1)** 🎧\n\n"
        "Leaving Subaru behind in his stunned silence, you venture deeper into the West Wing corridors. "
        "Your breath is steady, unbothered by the long walk thanks to your marathon endurance. "
        "Suddenly, your seismic sense registers a heavy, static mass resting on an antique velvet lounge near the window.\n\n"
        "It is the eldest son, **Shu Sakamaki**. His golden hair catches the pale moonlight, his eyes are tightly shut, and white earphones are plugged in. "
        "You pull two heavy steel tuning forks from your pocket, casually balancing them between your fingers like a simple musical instrument. "
        "You lock your face toward him, effortlessly pretending to look down at his resting figure."
    ),
    6: (
        "**CHAPTER 2: Whispers in the Dark (Part 2)** 🤫\n\n"
        "You glide past him like a phantom, your light 25 kg frame making no sound on the floorboards. "
        "Suddenly, without opening his eyes, Shu speaks in a low, sleepy baritone:\n"
        "*«...How noisy. Or rather... how unusually quiet. Most mortal girls clatter through these halls like frightened cattle, irritating my ears. But you... you move like a corpse. It's almost... peaceful. And what are those steel forks in your hands?»*\n\n"
        "He shifts his head, a single sapphire eye opening to inspect you. He thinks you are boldly studying his face while holding a strange musical tool. "
        "How will you respond to the lazy maestro while keeping your blindness and powers hidden?"
    )
}

# ==========================================
# 3. ІНТЕРФЕЙСИ ТА КНОПКИ У ГРІ
# ==========================================
class GlobalRestartView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="Restart Story ↩️", style=discord.ButtonStyle.danger, custom_id="global_restart")
    async def restart(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your story!", ephemeral=True)
            return
        await interaction.response.defer()
        update_player_page(self.user_id, 1)
        
        embed = discord.Embed(description=STORY_PAGES[1], color=0x4A0E4E)
        if IMAGES[1] != "":
            embed.set_image(url=IMAGES[1])
            
        await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, view=StoryNavigationView(1, self.user_id))

class StoryNavigationView(discord.ui.View):
    def __init__(self, current_page: int, user_id: int):
        super().__init__(timeout=None)
        self.current_page = current_page
        self.user_id = user_id

    @discord.ui.button(label="Next Page ▶", style=discord.ButtonStyle.primary, custom_id="story_next")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your story!", ephemeral=True)
            return
            
        await interaction.response.defer()
        next_pg = self.current_page + 1
        update_player_page(self.user_id, next_pg)
        
        if next_pg in STORY_PAGES:
            embed = discord.Embed(description=STORY_PAGES[next_pg], color=0x4A0E4E)
            if next_pg in IMAGES and IMAGES[next_pg] != "":
                embed.set_image(url=IMAGES[next_pg])
            await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, view=StoryNavigationView(next_pg, self.user_id))
        else:
            embed = discord.Embed(
                title="CHAPTER 1: The Confrontation 🩸",
                description="Subaru Sakamaki is blocking your path. He thinks you are staring defiantly at him. How does Lybid handle the white-haired vampire while keeping her blindness hidden? Choose carefully:",
                color=0x4A0E4E
            )
            if IMAGES[4] != "":
                embed.set_image(url=IMAGES[4])
            await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, view=SubaruChoiceView(self.user_id))

class SubaruChoiceView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

    async def process_outcome(self, interaction, title, text):
        update_player_page(self.user_id, 5) 
        full_text = (
            f"**CHAPTER 1: Outcomes of Choice** 🩸\n\n"
            f"{title}\n\n{text}\n\n"
            f"*Subaru stands frozen, utterly bewildered by your chilling lack of vulnerability. "
            f"He is entirely fooled by your simulated gaze, leaving your secret safe in the shadows.*\n\n"
            f" Press **Next Page ▶** to proceed into the West Wing corridors to meet Shu."
        )
        embed = discord.Embed(description=full_text, color=0x4A0E4E)
        if IMAGES[4] != "":
            embed.set_image(url=IMAGES[4])
        await interaction.response.edit_message(embed=embed, view=StoryNavigationView(4, self.user_id))

    @discord.ui.button(label="Maintain Piercing Eye Contact", style=discord.ButtonStyle.secondary, custom_id="sub_c1")
    async def c1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_outcome(interaction, "👁️ **Path of Simulated Vision**", "You turn your face fully to him, locking your unseeing purple eyes directly onto his. You don't blink, tracking his breath to keep your gaze level. Subaru shivers under what he thinks is fearless, cold eye contact. *«What is with that look in your eyes?! Why are you staring at me like I'm nothing?!»*")

    @discord.ui.button(label="Use Enigmatic Logic", style=discord.ButtonStyle.primary, custom_id="sub_c2")
    async def c2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_outcome(interaction, "🔮 **Path of Enigmatic Logic**", "Looking right at his facial level, you state in a flat voice: *«Your screaming is statistically inefficient. If execution was your actual intent, you wouldn't waste oxygen on theatrics.»* Subaru freezes. He thinks you are analyzing his posture with your eyes.")

    @discord.ui.button(label="Predict His Next Move", style=discord.ButtonStyle.success, custom_id="sub_c3")
    async def c3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_outcome(interaction, "👣 **Path of Blind Deception**", "Your feet capture the tremors of his boots, feeling his weight shift backward. Keeping your eyes locked on his, you murmur: *«Your posture is tense, yet you stepped back. You are performing anger to scare me away, aren't you?»* Subaru blushes furiously: *«How can you tell just by looking at me?!»*")

class ShuChoiceView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

    async def process_outcome(self, interaction, title, text):
        update_player_page(self.user_id, 7) 
        full_text = (
            f"**CHAPTER 2: Outcomes of Choice** 🎼\n\n"
            f"{title}\n\n{text}\n\n"
            f"*Shu closes his eyes once more, drifting back into his silent world. Yet, his pulse remains altered. "
            f"Your blindness and your origin remain perfectly hidden in the dark.*"
        )
        embed = discord.Embed(description=full_text, color=0x4A0E4E)
        if IMAGES[6] != "":
            embed.set_image(url=IMAGES[6])
        await interaction.response.edit_message(embed=embed, view=GlobalRestartView(self.user_id))

    @discord.ui.button(label="Play an Enigmatic Note", style=discord.ButtonStyle.primary, custom_id="shu_c1")
    async def c1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_outcome(interaction, "🎵 **Path of Acoustic Deception**", "You gently strike your steel tuning forks. A pure frequency fills the room. *«Acoustic perfection helps me ignore the chaotic noise of the world. Just like your earphones do,»* you state flatly. Shu opens a single eye, genuinely intrigued by what he thinks is a shared eccentric passion for music.")

    @discord.ui.button(label="Dismiss with Biological Logic", style=discord.ButtonStyle.primary, custom_id="shu_c2")
    async def c2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_outcome(interaction, "🔮 **Path of Biological Logic**", "Fixing your simulated gaze on his posture, you state in a monotone whisper: *«Absolute physical apathy is merely an efficient biological method of conserving energy. Your laziness is logically sound.»* Shu chokes on a breath, completely stunned by your bizarre analysis.")

    @discord.ui.button(label="Drop the Cryptic Cipher", style=discord.ButtonStyle.success, custom_id="shu_c3")
    async def c3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_outcome(interaction, "💔 **Path of the Cryptic Cipher (SAD)**", "You focus your gaze into the empty space behind him and murmur softly: *«You find peace in silence? How ironic. To me, this quiet only means that I am already starting to feel quite sad.»* Shu subtly tenses up, trying to decode the heavy meaning. The secret of Sofia remains an impenetrable riddle.")

    @discord.ui.button(label="Simulate Confident Footsteps", style=discord.ButtonStyle.secondary, custom_id="shu_c4")
    async def c4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_outcome(interaction, "🏃‍♀️ **Path of Gymnastic Simulation**", "Utilizing your flawless marathon endurance and light 25 kg frame, you take a fluid, balanced step forward right in front of his sofa. *«My silent movements are just a habit. Frightened cattle run, but I have nowhere to run to.»* Shu opens his eye wider, entirely fooled into believing you see his every movement.")

    @discord.ui.button(label="Atheistic Indifference", style=discord.ButtonStyle.secondary, custom_id="shu_c5")
    async def c5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_outcome(interaction, "⛪ **Path of Cold Realism**", "You indifferently hide your steel forks back inside your coat pocket. *«I move like a corpse because I do not fear the dark, nor do I believe in supernatural monsters. You are just a biological entity occupying space.»* Shu slightly clenches his teeth, deeply fascinated.")

# ==========================================
# 4. ГОЛОВНА КОМАНДА ГРИ (!play) З КАРТИНКАМИ
# ==========================================
IMAGES = {
    1: "https://postimg.cc",   # Картка 1: Брама під дощем
    2: "https://postimg.cc",   # Картка 2: Сухий головний хол
    3: "https://postimg.cc",  # Картка 3: Кроки Субару на сходах
    4: "https://postimg.cc",   # Картка 4: Кулак Субару в стіні
    5: "https://postimg.cc",      # Картка 5: Шу на дивані
    6: "https://postimg.cc"       # Картка 6: Сапфірове око Шу
}

@bot.hybrid_command(name="play", description="Start or continue your year-long visual novel")
async def play(ctx: commands.Context):
    user_id = ctx.author.id

    conn = sqlite3.connect("blind_secrets.db")
    cursor = conn.cursor()
    
cursor.execute("SELECT current_page FROM players WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    current_page = row[0] if row else 1

    if current_page in STORY_PAGES:
        view = StoryNavigationView(current_page, user_id)
        embed = discord.Embed(description=STORY_PAGES[current_page], color=0x4A0E4E)
        if current_page in IMAGES and IMAGES[current_page] != "":
            embed.set_image(url=IMAGES[current_page])
        await ctx.send(embed=embed, view=view)
    else:
        if current_page == 5:
            embed = discord.Embed(
                title="CHAPTER 1: The Confrontation 🩸",
                description="Subaru Sakamaki is blocking your path. He thinks you are staring defiantly at him. How will Lybid handle the white-haired vampire while keeping her blindness hidden?",
                color=0x4A0E4E
            )
            if IMAGES.get(4) != "":
                embed.set_image(url=IMAGES.get(4))
            await ctx.send(embed=embed, view=SubaruChoiceView(user_id))
        elif current_page == 7:
            embed = discord.Embed(
                title="CHAPTER 2: Whispers in the Dark 🤫",
                description="The lazy maestro opens a single sapphire eye, inspecting your doll-like face. How will you respond to Shu Sakamaki while keeping your secrets completely hidden?",
                color=0x4A0E4E
            )
            if IMAGES.get(6) != "":
                embed.set_image(url=IMAGES.get(6))
            await ctx.send(embed=embed, view=ShuChoiceView(user_id))
        else:
            embed = discord.Embed(description="Your current stance is sealed in the shadows. Rest well in your chamber.", color=0x2b2d31)
            await ctx.send(embed=embed)

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print("✅ Команди синхронізовано з Discord!")
    except Exception as e:
        print(f"Помилка синхронізації: {e}")
    print(f"Бот {bot.user.name} успішно запустився! Сліпота Либідь — це секрет.")

# ==========================================
# 5. НАДІЙНИЙ ЗАПУСК БОТА З АВТО-ПЕРЕЗАПУСКОМ
# ==========================================
import os
TOKEN = os.getenv("DISCORD_TOKEN")

while True:
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"⚠️ Тимчасовий збій мережі: {e}. Перезапуск через 5 секунд...")
        time.sleep(5)
