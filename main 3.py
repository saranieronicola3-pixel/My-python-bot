# -*- coding: utf-8 -*-
import os
os.environ["DISCORD_INTERACTIONS"] = "false"
os.environ["DISCORD_VOICE"] = "false"

import discord
from discord.ext import commands
import asyncio
import json
import random
import datetime
import re
import sqlite3
import os
import time
import aiosqlite
import shutil
from typing import Dict, List, Set, Optional
from flask import Flask, send_from_directory
from threading import Thread
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# ========== CONFIGURATION ==========
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)
BOT_INVITE_ALLOWED = False
POINT_TO_EUR = 0.01

# Allowed server - Bot will only stay in this server
# To get your server ID: Right click server name -> Copy Server ID (Developer Mode must be enabled)
ALLOWED_GUILD_IDS = [1437952549985714188, 1268921987447652435]

# Channel IDs for logging
UPDATE_CHANNEL_ID = 1435945016446025780
ANNOUNCEMENT_CHANNEL_ID = 1382679065818955927
WIN_LOG_CHANNEL_ID = 1435944350738681976
CHEAT_LOG_CHANNEL_ID = 1435944378404442162
MOD_LOG_CHANNEL_ID = 1435945820540244039
LOTTERY_CHANNEL_ID = 1436986266221809744
AD_CHANNEL_ID = 1437012216313413672

# Admin Configuration
BOT_ADMIN_ROLE_IDS = [1382721848877387887]
BOT_ADMIN_USER_IDS = [1428619912716488776]

# Link Permission Configuration (users/roles that can send links without being admin)
LINK_ALLOWED_ROLE_IDS = []  # Add role IDs here that can send links
LINK_ALLOWED_USER_IDS = []  # Add user IDs here that can send links

# Cooldown settings
COMMAND_COOLDOWN = 10
SPAM_THRESHOLD = 5
SPAM_PUNISHMENT = 86400

# VIP System
VIP_MULTIPLIER = 1.15

# Boost System
BOOSTS = {
    'boost1': {'name': '🚀 Small Boost', 'multiplier': 1.5},
    'boost2': {'name': '⚡ Medium Boost', 'multiplier': 2.0},
    'boost3': {'name': '💎 Large Boost', 'multiplier': 3.0}
}

# Lottery System
LOTTERY_TICKET_PRICE = 1
LOTTERY_DRAW_TIME = "11:00"  # 7 PM Hong Kong Time (HKT = UTC+8)

# Backup settings
BACKUP_INTERVAL = 86400
LOG_RETENTION_DAYS = 30

# Safety limits to prevent exploits and bugs
MAX_BET_AMOUNT = 1000000000  # 1 billion max bet
MAX_BALANCE = 9999999999999  # ~10 trillion max balance
MIN_BET_AMOUNT = 1  # Minimum 1 point bet
MAX_BET_PERCENTAGE = 0.95  # Can't bet more than 95% of balance in one go

# Insult system for losses
LOSS_INSULTS = [
    "😂 HAHAHAHA you lost! Maybe gambling isn't for you!",
    "💀 RIP your points! Better luck next time, loser!",
    "🤡 You're a clown! Try again when you git gud!",
    "📉 Your balance is going down faster than your IQ!",
    "🗑 Trash player! Even my grandma plays better!",
    "🤦 Seriously? You call that gambling? That's embarrassing!",
    "😭 Cry more! Your tears won't bring those points back!",
    "🎪 Welcome to the circus! You're the main attraction!",
    "🧠 Maybe try using your brain next time?",
    "👶 Baby rage incoming! Did you lose your lunch money?",
    "🐷 Oink oink! Pigs lose faster than you!",
    "💩 That was a garbage bet! What were you thinking?",
    "🤮 That performance made me sick!",
    "⚰ RIP Bozo! Your points are gone forever!",
    "🌚 Even the moon is laughing at you right now!",
    "🦐 Shrimp brain moves! No wonder you lost!",
    "🍼 Do you need a bottle after that loss, baby?",
    "🎲 The dice gods are not on your side today!",
    "📛 SKILL ISSUE detected! Maybe retire?",
    "🤓 'Actually, I'm a good gambler' - you, 5 seconds before losing"
]

LOSS_NORMAL_MESSAGES = [
    "😔 Better luck next time!",
    "💔 Not your lucky day...",
    "🎯 Almost! Try again!",
    "🍀 The odds weren't in your favor this time.",
    "⭐ Keep trying! Victory is close!",
    "🎰 The casino wins this round!",
    "💸 Lost this one, but there's always next time!",
    "🌟 Don't give up! Fortune favors the brave!"
]

def get_loss_message():
    """Returns a random loss message (60% insult, 40% normal)"""
    if random.random() < 0.6:  # 60% chance for insult
        return random.choice(LOSS_INSULTS)
    else:  # 40% chance for normal message
        return random.choice(LOSS_NORMAL_MESSAGES)

# ========== LOCALIZATION SYSTEM ==========
class LocalizationService:
    """Centralized localization service with caching and fallback support"""
    
    def __init__(self):
        self.translations = {}
        self.user_language_cache = {}  # In-memory cache: {user_id: language_code}
        self.supported_languages = {
            'en': '🇬🇧 English', 'es': '🇪🇸 Español', 'fr': '🇫🇷 Français',
            'de': '🇩🇪 Deutsch', 'it': '🇮🇹 Italiano', 'pt': '🇵🇹 Português',
            'ru': '🇷🇺 Русский', 'tr': '🇹🇷 Türkçe', 'pl': '🇵🇱 Polski',
            'nl': '🇳🇱 Nederlands', 'sv': '🇸🇪 Svenska', 'no': '🇳🇴 Norsk'
        }
        self.default_language = 'en'
        self.load_translations()
    
    def load_translations(self):
        """Load all translation files from locales/ directory"""
        import os
        locales_dir = "locales"
        
        if not os.path.exists(locales_dir):
            print(f"⚠  Locales directory not found, creating...")
            os.makedirs(locales_dir)
            return
        
        for lang_code in self.supported_languages.keys():
            file_path = os.path.join(locales_dir, f"{lang_code}.json")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
                print(f"✅ Loaded {lang_code} translations")
            except FileNotFoundError:
                if lang_code == self.default_language:
                    print(f"❌ CRITICAL: Default language {lang_code} not found!")
                else:
                    print(f"⚠  Missing translation file: {file_path}")
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing {file_path}: {e}")
    
    async def get_user_language(self, user_id: int, db_instance) -> str:
        """Get user's preferred language with caching"""
        # Check cache first
        if user_id in self.user_language_cache:
            return self.user_language_cache[user_id]
        
        # Fetch from database using db method
        lang = await db_instance.get_language(user_id)
        
        # Validate and cache
        if lang not in self.supported_languages:
            lang = self.default_language
        
        self.user_language_cache[user_id] = lang
        return lang
    
    async def set_user_language(self, user_id: int, language_code: str, db_instance) -> bool:
        """Set user's language preference and update cache"""
        if language_code not in self.supported_languages:
            return False
        
        # Use db method instead of direct SQL
        await db_instance.set_language(user_id, language_code)
        
        # Update cache
        self.user_language_cache[user_id] = language_code
        return True
    
    def get_nested(self, data: dict, key_path: str):
        """Navigate nested dictionary using dot-separated key path"""
        keys = key_path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    async def translate(self, user_id: int, key: str, db_instance, **kwargs) -> str:
        """
        Translate a key for a user with variable substitution
        
        Args:
            user_id: Discord user ID
            key: Dot-separated translation key (e.g., "core.insufficient_balance")
            db_instance: Database instance
            **kwargs: Variables to substitute in the translation
        
        Returns:
            Translated and formatted string
        """
        # Get user's language
        lang = await self.get_user_language(user_id, db_instance)
        
        # Get translation from user's language
        translation = None
        if lang in self.translations:
            translation = self.get_nested(self.translations[lang], key)
        
        # Fallback to English if not found
        if translation is None and lang != self.default_language:
            if self.default_language in self.translations:
                translation = self.get_nested(self.translations[self.default_language], key)
        
        # Final fallback to key itself
        if translation is None:
            print(f"⚠  Missing translation key: {key} for language: {lang}")
            translation = key
        
        # Substitute variables
        if kwargs:
            try:
                return translation.format(**kwargs)
            except KeyError as e:
                print(f"⚠  Missing variable in translation: {e} for key: {key}")
                return translation
        
        return translation
    
    def t_sync(self, lang: str, key: str, **kwargs) -> str:
        """Synchronous translation for non-async contexts (e.g., button labels)"""
        translation = None
        if lang in self.translations:
            translation = self.get_nested(self.translations[lang], key)
        
        if translation is None and lang != self.default_language:
            if self.default_language in self.translations:
                translation = self.get_nested(self.translations[self.default_language], key)
        
        if translation is None:
            return key
        
        if kwargs:
            try:
                return translation.format(**kwargs)
            except KeyError:
                return translation
        
        return translation

# Initialize localization service
localization = LocalizationService()

# ========== GUILD CHECK DECORATOR ==========
def require_guild():
    """Decorator to block commands in DMs - only allow in authorized guilds"""
    async def predicate(ctx):
        if ctx.guild is None:
            await ctx.send("❌ This command can only be used in a server, not in DMs!")
            return False
        if ctx.guild.id not in ALLOWED_GUILD_IDS:
            await ctx.send(f"❌ This bot is only authorized to work in specific servers.\n"
                          f"**Current Server ID:** {ctx.guild.id}\n"
                          f"**Allowed Servers:** {', '.join(str(id) for id in ALLOWED_GUILD_IDS)}\n\n"
                          f"💡 Contact the bot owner to add this server to the whitelist.")
            return False
        return True
    return commands.check(predicate)

# ========== GAME INTERACTION SYSTEMS ==========
class MinesGame:
    def __init__(self, user_id, bet_amount, mines_count):
        self.user_id = user_id
        self.bet_amount = bet_amount
        self.mines_count = mines_count
        self.diamonds_count = 25 - mines_count
        self.grid = self.generate_grid()
        self.revealed = [[False for _ in range(5)] for _ in range(5)]
        self.game_over = False
        self.won = False
        self.diamonds_found = 0
    
    def get_current_multiplier(self):
        """Calculate current multiplier based on diamonds found with progressive system"""
        if self.diamonds_found == 0:
            return 1.0
        
        # Determine increment based on mine count
        # 10+ mines: 0.15x per diamond
        # 3-9 mines: 0.09x per diamond
        if self.mines_count >= 10:
            increment = 0.15
        else:
            increment = 0.09
        
        # Calculate: 1.00 + (diamonds_found * increment)
        return 1.0 + (self.diamonds_found * increment)
        
    def generate_grid(self):
        positions = list(range(25))
        random.shuffle(positions)
        
        grid = [['💎' for _ in range(5)] for _ in range(5)]
        
        # Place mines
        for i in range(self.mines_count):
            row = positions[i] // 5
            col = positions[i] % 5
            grid[row][col] = '💥'
            
        return grid
    
    def reveal_cell(self, row, col):
        if self.revealed[row][col] or self.game_over:
            return None
            
        self.revealed[row][col] = True
        cell_value = self.grid[row][col]
        
        if cell_value == '💥':
            self.game_over = True
            self.won = False
            return 'mine'
        else:
            self.diamonds_found += 1
            if self.diamonds_found == self.diamonds_count:
                self.game_over = True
                self.won = True
            return 'diamond'
    
    def get_display_grid(self, show_all_mines=False):
        display = []
        for i in range(5):
            row = []
            for j in range(5):
                if self.revealed[i][j]:
                    row.append(self.grid[i][j])
                elif show_all_mines and self.grid[i][j] == '💥':
                    # Show unrevealed mines when game is lost
                    row.append('💣')
                else:
                    row.append('🟦')
            display.append(row)
        return display

class TowerGame:
    # Difficulty settings: (total_buttons, safe_count, multiplier_per_level, display_name)
    DIFFICULTIES = {
        'easy': (4, 3, 0.25, '🟢 Easy (1 mine / 4)'),
        'medium': (3, 1, 0.50, '🟡 Medium (2 mines / 3)'),
        'hard': (4, 2, 0.40, '🟠 Hard (2 mines / 4)'),
        'extreme': (4, 1, 0.60, '🔴 Extreme (3 mines / 4)')
    }
    
    def __init__(self, user_id, bet_amount, difficulty):
        self.user_id = user_id
        self.bet_amount = bet_amount
        self.difficulty = difficulty
        self.current_level = 0
        self.game_over = False
        self.won = False
        
        # Get difficulty settings
        diff_settings = self.DIFFICULTIES.get(difficulty, self.DIFFICULTIES['easy'])
        self.total_buttons = diff_settings[0]
        self.safe_count = diff_settings[1]
        self.multiplier_per_level = diff_settings[2]
        self.difficulty_display = diff_settings[3]
        
        self.levels = self.generate_levels()
        
    def generate_levels(self):
        levels = []
        for i in range(10):  # 10 levels instead of 5
            # Randomly select safe paths (can be 1 or more based on difficulty)
            all_positions = list(range(self.total_buttons))
            random.shuffle(all_positions)
            safe_paths = all_positions[:self.safe_count]
            
            levels.append({
                'safe_paths': safe_paths,
                'mines': [p for p in range(self.total_buttons) if p not in safe_paths]
            })
        return levels
    
    def choose_path(self, path):
        if self.game_over:
            return False
            
        current_level_data = self.levels[self.current_level]
        self.current_level += 1
        
        if path in current_level_data['safe_paths']:
            if self.current_level == 10:  # Win after 10 levels
                self.game_over = True
                self.won = True
            return True
        else:
            self.game_over = True
            self.won = False
            return False
    
    def get_current_multiplier(self):
        """Calculate current multiplier based on levels completed"""
        return 1.0 + (self.current_level * self.multiplier_per_level)

class BlackjackGame:
    def __init__(self, user_id, bet_amount):
        self.user_id = user_id
        self.bet_amount = bet_amount
        self.deck = self.generate_deck()
        self.player_hand = []
        self.dealer_hand = []
        self.game_over = False
        self.won = False
        self.result = None
        self.forced_loss = False  # Admin can force loss
        self.initial_deal()
        
    def generate_deck(self):
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['♠', '♥', '♦', '♣']
        deck = [f'{rank}{suit}' for rank in ranks for suit in suits]
        random.shuffle(deck)
        return deck
    
    @staticmethod
    def get_card_image_url(card):
        """Convert card like 'A♠' to deckofcardsapi.com image URL"""
        suit_map = {'♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C'}
        rank = card[:-1]  # Remove suit symbol
        suit = card[-1]    # Get suit symbol
        
        # Convert rank (10 stays as 10, but API uses '0')
        if rank == '10':
            rank = '0'
        
        # Get API suit code
        suit_code = suit_map.get(suit, 'S')
        
        # Return card image URL
        return f"https://deckofcardsapi.com/static/img/{rank}{suit_code}.png"
    
    def card_value(self, card):
        rank = card[:-1]
        if rank in ['J', 'Q', 'K']:
            return 10
        elif rank == 'A':
            return 11
        else:
            return int(rank)
    
    def hand_value(self, hand):
        value = sum(self.card_value(card) for card in hand)
        aces = sum(1 for card in hand if card[:-1] == 'A')
        
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
            
        return value
    
    def initial_deal(self):
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]
        
        if self.hand_value(self.player_hand) == 21:
            self.game_over = True
            self.won = True
            self.result = "blackjack"
    
    def hit(self):
        if self.game_over:
            return False
            
        self.player_hand.append(self.deck.pop())
        player_value = self.hand_value(self.player_hand)
        
        if player_value > 21:
            self.game_over = True
            self.won = False
            self.result = "bust"
            return False
        return True
    
    def stand(self):
        if self.game_over:
            return False
            
        # ADMIN FORCED LOSS - Silently make dealer win
        if self.forced_loss:
            # Ensure dealer beats player (appears natural)
            player_value = self.hand_value(self.player_hand)
            # Make dealer draw to just beat player or stay at strong hand
            while self.hand_value(self.dealer_hand) < player_value and self.hand_value(self.dealer_hand) < 21:
                self.dealer_hand.append(self.deck.pop())
                if self.hand_value(self.dealer_hand) > 21:
                    # If dealer busts, reset and give strong hand
                    self.dealer_hand = [self.deck.pop(), self.deck.pop()]
                    while self.hand_value(self.dealer_hand) < 19:
                        self.dealer_hand.append(self.deck.pop())
                    break
            
            self.game_over = True
            self.won = False
            self.result = "lose"
            return True
            
        # Normal dealer logic
        # Dealer draws until 17 or higher
        while self.hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.pop())
        
        player_value = self.hand_value(self.player_hand)
        dealer_value = self.hand_value(self.dealer_hand)
        
        self.game_over = True
        
        if dealer_value > 21:
            self.won = True
            self.result = "dealer_bust"
        elif player_value > dealer_value:
            self.won = True
            self.result = "win"
        elif player_value < dealer_value:
            self.won = False
            self.result = "lose"
        else:
            # TIE - Push (refund)
            self.won = None  # None significa pareggio/rimborso
            self.result = "push"
        
        return True

# Active games storage
active_mines_games = {}
active_tower_games = {}
active_blackjack_games = {}

# ========== MULTIPLAYER GAME INFRASTRUCTURE ==========
from dataclasses import dataclass
from enum import Enum

class GameType(Enum):
    TIC_TAC_TOE = "tictactoe"
    BLACKJACK_PVP = "blackjack_pvp"
    NAVAL_WAR = "navalwar"
    FIGHT = "fight"

@dataclass
class GameSession:
    game_type: GameType
    player1_id: int
    player2_id: int
    bet_amount: float
    channel_id: int
    game_state: any
    created_at: datetime.datetime
    is_pvp: bool  # True if vs player, False if vs bot
    
class GameSessionManager:
    def __init__(self):
        self.active_sessions = {}  # key: (channel_id, game_type, session_id) -> GameSession
        self.user_games = {}  # key: user_id -> (channel_id, game_type, session_id)
        self.session_counter = 0
    
    def create_session(self, game_type, player1_id, player2_id, bet_amount, channel_id, game_state, is_pvp=True):
        """Create a new game session"""
        self.session_counter += 1
        session_id = f"{player1_id}_{self.session_counter}"
        
        session = GameSession(
            game_type=game_type,
            player1_id=player1_id,
            player2_id=player2_id,
            bet_amount=bet_amount,
            channel_id=channel_id,
            game_state=game_state,
            created_at=datetime.datetime.utcnow(),
            is_pvp=is_pvp
        )
        key = (channel_id, game_type.value, session_id)
        self.active_sessions[key] = session
        self.user_games[player1_id] = key
        if is_pvp:
            self.user_games[player2_id] = key
        return session
    
    def get_session(self, channel_id, game_type, player_id):
        """Get active session for a channel/game/player"""
        if player_id not in self.user_games:
            return None
        key = self.user_games[player_id]
        return self.active_sessions.get(key)
    
    def end_session(self, channel_id, game_type, player_id):
        """End a game session"""
        if player_id not in self.user_games:
            return
        key = self.user_games[player_id]
        session = self.active_sessions.get(key)
        if session:
            if session.player1_id in self.user_games:
                del self.user_games[session.player1_id]
            if session.is_pvp and session.player2_id in self.user_games:
                del self.user_games[session.player2_id]
            del self.active_sessions[key]
    
    def is_user_in_game(self, user_id):
        """Check if user is in any active game"""
        return user_id in self.user_games

game_session_manager = GameSessionManager()

# ========== MULTIPLAYER CHALLENGE SYSTEM ==========
# Pending challenges tracker
pending_challenges = {}  # (challenger_id, challenged_id, game_name) -> message

class ChallengeView(discord.ui.View):
    def __init__(self, challenger, challenged_user, game_name, amount, on_accept, on_decline, ctx):
        super().__init__(timeout=40.0)
        self.challenger = challenger
        self.challenged_user = challenged_user
        self.game_name = game_name
        self.amount = amount
        self.on_accept = on_accept
        self.on_decline = on_decline
        self.ctx = ctx
        self.answered = False
        self.message = None
    
    @discord.ui.button(label='✅ Accept', style=discord.ButtonStyle.success)
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.challenged_user.id:
            await interaction.response.send_message("❌ This challenge is not for you!", ephemeral=True)
            return
        
        self.answered = True
        await interaction.response.send_message(f"✅ {self.challenged_user.mention} accepted the challenge!", ephemeral=False)
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        
        # Remove from pending
        key = (self.challenger.id, self.challenged_user.id, self.game_name)
        if key in pending_challenges:
            del pending_challenges[key]
        
        # Call accept callback
        await self.on_accept(interaction)
        self.stop()
    
    @discord.ui.button(label='❌ Decline', style=discord.ButtonStyle.danger)
    async def decline_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.challenged_user.id:
            await interaction.response.send_message("❌ This challenge is not for you!", ephemeral=True)
            return
        
        self.answered = True
        await interaction.response.send_message(f"❌ {self.challenged_user.mention} declined the challenge!", ephemeral=False)
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        
        # Remove from pending
        key = (self.challenger.id, self.challenged_user.id, self.game_name)
        if key in pending_challenges:
            del pending_challenges[key]
        
        # Call decline callback
        await self.on_decline()
        self.stop()
    
    async def on_timeout(self):
        if not self.answered:
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            # Remove from pending
            key = (self.challenger.id, self.challenged_user.id, self.game_name)
            if key in pending_challenges:
                del pending_challenges[key]
            
            # Send timeout message
            try:
                await self.message.edit(content=f"⏰ **You're late!** {self.challenged_user.mention} didn't respond in time.", view=self)
            except (discord.HTTPException, discord.NotFound) as e:
                print(f"⚠ Could not edit challenge message on timeout: {e}")
            finally:
                await self.on_decline()

async def initiate_multiplayer_challenge(ctx, challenger, challenged_user, game_name, amount, start_game_callback):
    """
    Shared helper for initiating multiplayer challenges with Accept/Decline buttons.
    
    Args:
        ctx: Discord context
        challenger: User who initiated the challenge
        challenged_user: User being challenged
        game_name: Name of the game (for display)
        amount: Bet amount
        start_game_callback: Async function to call when challenge is accepted
            Should handle: balance deduction, game creation, and game start
    """
    # Check if challenge already pending
    key = (challenger.id, challenged_user.id, game_name)
    if key in pending_challenges:
        await ctx.send(f"❌ You already have a pending {game_name} challenge with {challenged_user.mention}!")
        return False
    
    # Pre-check balances (will re-check on accept)
    challenger_balance = await db.get_balance(challenger.id)
    challenged_balance = await db.get_balance(challenged_user.id)
    
    if challenger_balance < amount:
        await ctx.send("❌ You don't have enough points!")
        return False
    
    if challenged_balance < amount:
        await ctx.send(f"❌ {challenged_user.mention} doesn't have enough points! (Needs **{amount:.2f}**, has **{challenged_balance:.2f}**)")
        return False
    
    # Check if users already in game
    if game_session_manager.is_user_in_game(challenger.id):
        await ctx.send("❌ You're already in a game! Finish it first.")
        return False
    
    if game_session_manager.is_user_in_game(challenged_user.id):
        await ctx.send(f"❌ {challenged_user.mention} is already in a game!")
        return False
    
    # Check blacklist
    if await db.is_blacklisted(challenger.id):
        await ctx.send("❌ You are banned from using the bot!")
        return False
    
    if await db.is_blacklisted(challenged_user.id):
        await ctx.send(f"❌ {challenged_user.mention} is banned!")
        return False
    
    # Create challenge view
    async def on_accept(interaction):
        # Re-validate balances before deducting
        final_challenger_balance = await db.get_balance(challenger.id)
        final_challenged_balance = await db.get_balance(challenged_user.id)
        
        if final_challenger_balance < amount or final_challenged_balance < amount:
            await interaction.followup.send("❌ One of the players no longer has enough balance!", ephemeral=True)
            return
        
        # Start the game (callback handles balance deduction and game creation)
        await start_game_callback(ctx, interaction, challenger, challenged_user, amount)
    
    async def on_decline():
        # Nothing to refund since we haven't deducted yet
        pass
    
    view = ChallengeView(challenger, challenged_user, game_name, amount, on_accept, on_decline, ctx)
    
    # Send challenge prompt
    embed = discord.Embed(
        title=f"🎮 {game_name} Challenge!",
        description=f"{challenger.mention} challenges {challenged_user.mention} to a game of **{game_name}**!",
        color=0xFFD700
    )
    embed.add_field(name="Bet Amount", value=f"**{amount}** points each", inline=True)
    embed.add_field(name="Prize Pool", value=f"**{amount * 2 * 0.99:.2f}** points (1% fee)", inline=True)
    embed.add_field(name="Time Limit", value="40 seconds to accept", inline=False)
    
    message = await ctx.send(content=f"👉 {challenged_user.mention}", embed=embed, view=view)
    view.message = message
    
    # Track pending challenge
    pending_challenges[key] = message
    
    return True

# ========== FIGHT GAME ==========
class FightGame:
    def __init__(self, player1_id, player2_id, bet_amount, is_pvp=True):
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.bet_amount = bet_amount
        self.is_pvp = is_pvp
        
        # Game state
        self.player1_hp = 120
        self.player2_hp = 120
        self.player1_heal_cooldown = 0  # 0 = can heal, >0 = turns until can heal
        self.player2_heal_cooldown = 0
        self.current_turn = player1_id  # Challenger goes first
        self.game_over = False
        self.winner = None
        self.battle_log = []
        
    def get_current_player_name(self):
        """Returns 'Player 1' or 'Player 2' or 'Bot' based on current turn"""
        if self.current_turn == self.player1_id:
            return "Player 1"
        else:
            return "Bot" if not self.is_pvp else "Player 2"
    
    def get_player_hp(self, player_id):
        """Get HP for a specific player"""
        return self.player1_hp if player_id == self.player1_id else self.player2_hp
    
    def get_heal_cooldown(self, player_id):
        """Get heal cooldown for a specific player"""
        return self.player1_heal_cooldown if player_id == self.player1_id else self.player2_heal_cooldown
    
    def can_heal(self, player_id):
        """Check if player can use heal (not on cooldown)"""
        cooldown = self.get_heal_cooldown(player_id)
        return cooldown == 0
    
    def bot_choose_action(self):
        """Bot AI: Heal if HP <= 35% and heal available, otherwise attack"""
        bot_hp = self.player2_hp
        bot_can_heal = self.player2_heal_cooldown == 0
        
        if bot_hp <= 42 and bot_can_heal:  # 42 = 35% of 120
            return "heal"
        return "attack"
    
    def execute_action(self, player_id, action):
        """Execute an action (attack or heal) and return the result message"""
        if self.game_over or player_id != self.current_turn:
            return None
        
        # Decrement cooldowns at START of turn (before action)
        # This ensures cooldowns last a full turn cycle
        if is_player1 := (player_id == self.player1_id):
            if self.player1_heal_cooldown > 0:
                self.player1_heal_cooldown -= 1
        else:
            if self.player2_heal_cooldown > 0:
                self.player2_heal_cooldown -= 1
        
        player_name = "Player 1" if is_player1 else ("Bot" if not self.is_pvp else "Player 2")
        
        if action == "attack":
            # Calculate damage (18-28 base + 10% crit chance for +10)
            base_damage = random.randint(18, 28)
            is_crit = random.random() < 0.10
            damage = base_damage + (10 if is_crit else 0)
            
            # Apply damage to opponent
            if is_player1:
                self.player2_hp -= damage
            else:
                self.player1_hp -= damage
            
            crit_text = " **CRITICAL HIT!**" if is_crit else ""
            msg = f"⚔ {player_name} attacks for **{damage}** damage!{crit_text}"
            self.battle_log.append(msg)
            
        elif action == "heal":
            if not self.can_heal(player_id):
                return None  # Can't heal on cooldown
            
            # Calculate heal (15-25 HP)
            heal_amount = random.randint(15, 25)
            
            # Apply heal and set cooldown to 2 (decrements to 1 this turn, then 0 next turn)
            if is_player1:
                self.player1_hp = min(120, self.player1_hp + heal_amount)
                self.player1_heal_cooldown = 2  # Set cooldown (2 = skip next turn)
            else:
                self.player2_hp = min(120, self.player2_hp + heal_amount)
                self.player2_heal_cooldown = 2
            
            msg = f"💚 {player_name} heals for **{heal_amount}** HP!"
            self.battle_log.append(msg)
        
        # Check win condition
        if self.player1_hp <= 0:
            self.game_over = True
            self.winner = self.player2_id
            self.battle_log.append(f"💀 Player 1 has been defeated!")
        elif self.player2_hp <= 0:
            self.game_over = True
            self.winner = self.player1_id
            opponent_name = "Bot" if not self.is_pvp else "Player 2"
            self.battle_log.append(f"💀 {opponent_name} has been defeated!")
        
        # Switch turn if game not over
        if not self.game_over:
            self.current_turn = self.player2_id if player_id == self.player1_id else self.player1_id
        
        return msg
    
    def get_battle_summary(self):
        """Get last 5 battle log entries"""
        return "\n".join(self.battle_log[-5:])

# ========== TIC TAC TOE GAME ==========
class TicTacToeGame:
    def __init__(self, player1_id, player2_id, bet_amount, is_pvp=True):
        self.player1_id = player1_id  # X player
        self.player2_id = player2_id  # O player (bot if not PvP)
        self.bet_amount = bet_amount
        self.is_pvp = is_pvp
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.current_turn = player1_id  # X goes first
        self.game_over = False
        self.winner = None
        self.is_draw = False
    
    def make_move(self, player_id, row, col):
        """Make a move on the board"""
        if self.game_over or player_id != self.current_turn:
            return False
        if self.board[row][col] is not None:
            return False
        
        self.board[row][col] = 'X' if player_id == self.player1_id else 'O'
        
        # Check for win
        if self.check_win():
            self.game_over = True
            self.winner = player_id
            return True
        
        # Check for draw
        if all(self.board[i][j] is not None for i in range(3) for j in range(3)):
            self.game_over = True
            self.is_draw = True
            return True
        
        # Switch turn
        self.current_turn = self.player2_id if player_id == self.player1_id else self.player1_id
        return True
    
    def check_win(self):
        """Check if there's a winner"""
        # Check rows
        for row in self.board:
            if row[0] == row[1] == row[2] and row[0] is not None:
                return True
        
        # Check columns
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] and self.board[0][col] is not None:
                return True
        
        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] and self.board[0][0] is not None:
            return True
        if self.board[0][2] == self.board[1][1] == self.board[2][0] and self.board[0][2] is not None:
            return True
        
        return False
    
    def get_bot_move(self):
        """Advanced AI using minimax algorithm - nearly unbeatable"""
        def minimax(board, depth, is_maximizing):
            # Check terminal states
            temp_game = TicTacToeGame(0, 0, 0)
            temp_game.board = [row[:] for row in board]
            temp_game.check_win()
            
            if temp_game.game_over:
                if temp_game.is_draw:
                    return 0
                # If O won (bot), return positive, if X won (player), return negative
                return 10 - depth if temp_game.winner == self.player2_id else depth - 10
            
            if is_maximizing:  # Bot's turn (O)
                max_eval = -float('inf')
                for i in range(3):
                    for j in range(3):
                        if board[i][j] is None:
                            board[i][j] = 'O'
                            eval = minimax(board, depth + 1, False)
                            board[i][j] = None
                            max_eval = max(max_eval, eval)
                return max_eval
            else:  # Player's turn (X)
                min_eval = float('inf')
                for i in range(3):
                    for j in range(3):
                        if board[i][j] is None:
                            board[i][j] = 'X'
                            eval = minimax(board, depth + 1, True)
                            board[i][j] = None
                            min_eval = min(min_eval, eval)
                return min_eval
        
        # Find best move using minimax
        best_score = -float('inf')
        best_move = None
        
        for i in range(3):
            for j in range(3):
                if self.board[i][j] is None:
                    self.board[i][j] = 'O'
                    score = minimax(self.board, 0, False)
                    self.board[i][j] = None
                    
                    if score > best_score:
                        best_score = score
                        best_move = (i, j)
        
        return best_move

# ========== NAVAL WAR GAME ==========
class NavalWarGame:
    def __init__(self, player1_id, player2_id, bet_amount, is_pvp=True):
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.bet_amount = bet_amount
        self.is_pvp = is_pvp
        
        # Boards: 5x5 grid, ships are marked
        self.player1_board = [[0 for _ in range(5)] for _ in range(5)]
        self.player2_board = [[0 for _ in range(5)] for _ in range(5)]
        
        # Attacks: track hits and misses
        self.player1_attacks = [[0 for _ in range(5)] for _ in range(5)]  # P1's attacks on P2
        self.player2_attacks = [[0 for _ in range(5)] for _ in range(5)]  # P2's attacks on P1
        
        self.player1_ships_placed = False
        self.player2_ships_placed = False
        self.current_turn = player1_id
        self.game_over = False
        self.winner = None
        
        # Ship sizes: 3 ships (2, 2, 3 cells)
        self.ships = [2, 2, 3]
    
    def place_ships_random(self, player_id):
        """Randomly place ships for a player"""
        board = self.player1_board if player_id == self.player1_id else self.player2_board
        
        for ship_size in self.ships:
            placed = False
            attempts = 0
            while not placed and attempts < 100:
                attempts += 1
                horizontal = random.choice([True, False])
                if horizontal:
                    row = random.randint(0, 4)
                    col = random.randint(0, 5 - ship_size)
                    # Check if space is free
                    if all(board[row][col+i] == 0 for i in range(ship_size)):
                        for i in range(ship_size):
                            board[row][col+i] = 1
                        placed = True
                else:
                    row = random.randint(0, 5 - ship_size)
                    col = random.randint(0, 4)
                    if all(board[row+i][col] == 0 for i in range(ship_size)):
                        for i in range(ship_size):
                            board[row+i][col] = 1
                        placed = True
        
        if player_id == self.player1_id:
            self.player1_ships_placed = True
        else:
            self.player2_ships_placed = True
    
    def make_attack(self, attacker_id, row, col):
        """Make an attack at the specified position"""
        if not self.player1_ships_placed or not self.player2_ships_placed:
            return None
        if self.game_over or attacker_id != self.current_turn:
            return None
        
        if attacker_id == self.player1_id:
            # P1 attacking P2
            if self.player1_attacks[row][col] != 0:
                return None  # Already attacked here
            
            if self.player2_board[row][col] == 1:
                self.player1_attacks[row][col] = 2  # Hit
                result = 'hit'
            else:
                self.player1_attacks[row][col] = 1  # Miss
                result = 'miss'
        else:
            # P2 attacking P1
            if self.player2_attacks[row][col] != 0:
                return None
            
            if self.player1_board[row][col] == 1:
                self.player2_attacks[row][col] = 2  # Hit
                result = 'hit'
            else:
                self.player2_attacks[row][col] = 1  # Miss
                result = 'miss'
        
        # Check for win
        if self.check_win():
            self.game_over = True
            self.winner = attacker_id
        else:
            # Switch turn
            self.current_turn = self.player2_id if attacker_id == self.player1_id else self.player1_id
        
        return result
    
    def check_win(self):
        """Check if all opponent ships are destroyed"""
        # Check if P1 destroyed all P2 ships
        p2_ships_remaining = sum(
            1 for i in range(5) for j in range(5)
            if self.player2_board[i][j] == 1 and self.player1_attacks[i][j] != 2
        )
        if p2_ships_remaining == 0 and self.player1_ships_placed:
            return True
        
        # Check if P2 destroyed all P1 ships
        p1_ships_remaining = sum(
            1 for i in range(5) for j in range(5)
            if self.player1_board[i][j] == 1 and self.player2_attacks[i][j] != 2
        )
        if p1_ships_remaining == 0 and self.player2_ships_placed:
            return True
        
        return False
    
    def get_bot_attack(self):
        """Advanced AI for bot attacks with multi-hit ship tracking"""
        attacks = self.player2_attacks
        
        # Find all hits
        hits = [(i, j) for i in range(5) for j in range(5) if attacks[i][j] == 2]
        
        if len(hits) >= 2:
            # Try to find ship direction (horizontal or vertical)
            for i in range(len(hits)):
                for j in range(i + 1, len(hits)):
                    h1, h2 = hits[i], hits[j]
                    
                    # Check if hits are in same row (horizontal ship)
                    if h1[0] == h2[0]:
                        row = h1[0]
                        min_col = min(h1[1], h2[1])
                        max_col = max(h1[1], h2[1])
                        
                        # Attack left end
                        if min_col > 0 and attacks[row][min_col - 1] == 0:
                            return (row, min_col - 1)
                        # Attack right end
                        if max_col < 4 and attacks[row][max_col + 1] == 0:
                            return (row, max_col + 1)
                        # Attack between gaps
                        for col in range(min_col + 1, max_col):
                            if attacks[row][col] == 0:
                                return (row, col)
                    
                    # Check if hits are in same column (vertical ship)
                    if h1[1] == h2[1]:
                        col = h1[1]
                        min_row = min(h1[0], h2[0])
                        max_row = max(h1[0], h2[0])
                        
                        # Attack top end
                        if min_row > 0 and attacks[min_row - 1][col] == 0:
                            return (min_row - 1, col)
                        # Attack bottom end
                        if max_row < 4 and attacks[max_row + 1][col] == 0:
                            return (max_row + 1, col)
                        # Attack between gaps
                        for row in range(min_row + 1, max_row):
                            if attacks[row][col] == 0:
                                return (row, col)
        
        # Single hit - try all 4 adjacent cells (prioritize opposite directions)
        for i, j in hits:
            # Try in all 4 directions
            directions = [(i-1,j), (i+1,j), (i,j-1), (i,j+1)]
            for row, col in directions:
                if 0 <= row < 5 and 0 <= col < 5 and attacks[row][col] == 0:
                    return (row, col)
        
        # Smart random: use checkerboard pattern (ships need 2+ cells, so every other cell is strategic)
        checkerboard = []
        for i in range(5):
            for j in range(5):
                if (i + j) % 2 == 0 and attacks[i][j] == 0:
                    checkerboard.append((i, j))
        
        if checkerboard:
            return random.choice(checkerboard)
        
        # Fallback: any available cell
        available = [(i, j) for i in range(5) for j in range(5) if attacks[i][j] == 0]
        if available:
            return random.choice(available)
        
        return None

# ========== FORCED LOSS SYSTEM (SILENT - USER NEVER KNOWS) ==========
async def check_forced_loss(user_id):
    """
    ADMIN TOOL: Silently checks if user should be forced to lose
    Returns True if user should lose (and decrements counter)
    Returns False if user should play normally
    USER NEVER KNOWS - appears as normal random loss
    """
    forced_losses = await db.get_forced_losses(user_id)
    if forced_losses > 0:
        await db.decrement_forced_losses(user_id)
        return True  # Force loss silently
    return False  # Play normally

# ========== ADMIN CHECK ==========
def is_bot_admin():
    async def predicate(ctx):
        if ctx.author.id in BOT_ADMIN_USER_IDS:
            return True
        
        if any(role.id in BOT_ADMIN_ROLE_IDS for role in ctx.author.roles):
            return True
            
        if ctx.author.guild_permissions.administrator:
            return True
            
        return False
    return commands.check(predicate)

# ========== DYNAMIC DIFFICULTY SYSTEM ==========
class DifficultySystem:
    @staticmethod
    def get_win_probability(amount):
        # REBALANCED: ~30% win rate for all bet amounts
        if amount <= 100:
            return 0.30
        elif amount <= 1000:
            return 0.30
        else:
            return 0.30
    
    @staticmethod
    def get_multiplier_range(amount, game_type):
        # RIGGED: Reduced multipliers for better house edge
        base_multipliers = {
            'mines': {'low': (1.03, 1.4), 'medium': (1.01, 1.2), 'high': (1.00, 1.15)},
            'coinflip': {'low': (1.15, 2.1), 'medium': (1.05, 1.85), 'high': (1.02, 1.6)},
            'slots': {'low': (1.6, 3.7), 'medium': (1.6, 3.7), 'high': (1.6, 3.7)},
            'dice': {'low': (1.9, 4.5), 'medium': (1.9, 4.5), 'high': (1.9, 4.5)},
            'tower': {'low': (1.03, 2.1), 'medium': (1.01, 1.85), 'high': (1.00, 1.6)},
            'blackjack': {'low': (1.20, 1.6), 'medium': (1.10, 1.4), 'high': (1.02, 1.25)},
            'roulette': {'low': (1.15, 2.1), 'medium': (1.05, 1.85), 'high': (1.02, 1.6)}
        }
        
        if amount <= 100:
            category = 'low'
        elif amount <= 1000:
            category = 'medium'
        else:
            category = 'high'
        
        return base_multipliers[game_type][category]
    
    @staticmethod
    def calculate_win(amount, game_type, is_vip=False, boost_multiplier=1.0):
        # REBALANCED: ~30% win rate for all games
        if game_type in ['slots', 'dice']:
            win_probability = 0.30  # 30% win rate
        # Coinflip also ~30%
        elif game_type == 'coinflip':
            win_probability = 0.30
        else:
            win_probability = DifficultySystem.get_win_probability(amount)
        
        if random.random() > win_probability:
            return 0
        
        # Fixed 1.92x multiplier for 30% win rate (coinflip)
        if game_type == 'coinflip':
            multiplier = 1.92
        else:
            min_mult, max_mult = DifficultySystem.get_multiplier_range(amount, game_type)
            
            # Special multiplier logic for slots and dice: only 1% chance for 4x+
            if game_type in ['slots', 'dice']:
                if random.random() < 0.01:
                    # 1% chance: 4x to max multiplier
                    multiplier = random.uniform(4.0, max_mult)
                else:
                    # 99% chance: normal multiplier range (capped at 4x)
                    capped_max = min(4.0, max_mult)
                    multiplier = random.uniform(min_mult, capped_max)
            else:
                multiplier = random.uniform(min_mult, max_mult)
            
            if amount > 1000:
                multiplier *= random.uniform(0.8, 1.0)
            elif amount > 100:
                multiplier *= random.uniform(0.9, 1.0)
        
        if is_vip:
            multiplier *= VIP_MULTIPLIER
        
        multiplier *= boost_multiplier
        
        return int(amount * multiplier)

# ========== RANK SYSTEM ==========
RANK_SYSTEM = {
    100: "🎯 Beginner Gambler", 500: "🥉 Bronze Gambler", 1000: "🥈 Silver Gambler",
    5000: "🥇 Gold Gambler", 10000: "💎 Platinum Gambler", 25000: "🔮 Diamond Gambler",
    50000: "💍 Ruby Gambler", 100000: "🔵 Sapphire Gambler", 250000: "💚 Emerald Gambler",
    500000: "👑 Legendary Gambler", 1000000: "🌟 God Gambler", 5000000: "⚡ Ultimate Gambler"
}

# ========== ACHIEVEMENT SYSTEM ==========
ACHIEVEMENTS = {
    'first_win': {'name': '🎉 First Win', 'description': 'Win your first game', 'reward': 30},
    'high_roller': {'name': '💰 High Roller', 'description': 'Bet 1000+ points in one game', 'reward': 500},
    'lucky_streak': {'name': '🍀 Lucky Streak', 'description': 'Win 5 games in a row', 'reward': 300},
    'vip_member': {'name': '⭐ VIP Member', 'description': 'Get VIP status', 'reward': 1000},
    'millionaire': {'name': '💵 Millionaire', 'description': 'Reach 1,000,000 points wagered', 'reward': 2000},
    'jackpot_king': {'name': '🎰 Jackpot King', 'description': 'Hit a 10x multiplier', 'reward': 800},
    'lottery_winner': {'name': '🎫 Lottery Winner', 'description': 'Win the daily lottery', 'reward': 5000}
}

# ========== DATABASE WITH BACKUP ==========
class Database:
    def __init__(self):
        self.db_path = "casino_bot.db"
        self.backup_dir = "backups"
        self.init_db()
        self.setup_backup()
    
    def setup_backup(self):
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    async def create_backup(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"casino_backup_{timestamp}.db")
        shutil.copy2(self.db_path, backup_path)
        
        backups = sorted([f for f in os.listdir(self.backup_dir) if f.startswith("casino_backup_")])
        while len(backups) > 7:
            old_backup = backups.pop(0)
            os.remove(os.path.join(self.backup_dir, old_backup))
        
        return backup_path
    
    async def cleanup_old_logs(self):
        async with aiosqlite.connect(self.db_path) as db:
            cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=LOG_RETENTION_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
            await db.execute('DELETE FROM user_activity WHERE timestamp < ?', (cutoff_date,))
            await db.execute('DELETE FROM win_history WHERE timestamp < ?', (cutoff_date,))
            await db.commit()
    
    async def recover_from_backup(self, backup_file=None):
        if backup_file is None:
            backups = sorted([f for f in os.listdir(self.backup_dir) if f.startswith("casino_backup_")])
            if not backups:
                return False
            backup_file = os.path.join(self.backup_dir, backups[-1])
        
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, self.db_path)
            return True
        return False
    
    async def initialize(self):
        """Async initialization method"""
        pass
    
    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0, total_wagered REAL DEFAULT 0,
                    total_won REAL DEFAULT 0, total_lost REAL DEFAULT 0, vip_expires DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, first_points_at DATETIME,
                    monthly_wager REAL DEFAULT 0, last_monthly_reset DATETIME
                );
                CREATE TABLE IF NOT EXISTS daily_claims (user_id INTEGER, claim_date DATE, PRIMARY KEY (user_id, claim_date));
                CREATE TABLE IF NOT EXISTS monthly_claims (user_id INTEGER, claim_month TEXT, PRIMARY KEY (user_id, claim_month));
                CREATE TABLE IF NOT EXISTS rakeback (user_id INTEGER PRIMARY KEY, amount REAL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS blacklist (user_id INTEGER PRIMARY KEY, reason TEXT, banned_by INTEGER, banned_at DATETIME DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS private_profiles (user_id INTEGER PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS user_activity (user_id INTEGER, action TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS win_history (user_id INTEGER, game TEXT, bet_amount REAL, win_amount REAL, multiplier REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS command_cooldowns (user_id INTEGER, command_name TEXT, last_used DATETIME, PRIMARY KEY (user_id, command_name));
                CREATE TABLE IF NOT EXISTS user_stats (user_id INTEGER PRIMARY KEY, games_played INTEGER DEFAULT 0, games_won INTEGER DEFAULT 0, current_streak INTEGER DEFAULT 0, max_streak INTEGER DEFAULT 0);
                CREATE TABLE IF NOT EXISTS achievements (user_id INTEGER, achievement_id TEXT, unlocked_at DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (user_id, achievement_id));
                CREATE TABLE IF NOT EXISTS user_boosts (user_id INTEGER, boost_type TEXT, multiplier REAL, expires_at DATETIME, PRIMARY KEY (user_id, boost_type));
                CREATE TABLE IF NOT EXISTS lottery_tickets (user_id INTEGER, ticket_count INTEGER, lottery_date DATE, purchased_at DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (user_id, lottery_date));
                CREATE TABLE IF NOT EXISTS lottery_history (lottery_date DATE PRIMARY KEY, winner_id INTEGER, total_pool REAL, total_tickets INTEGER);
                CREATE TABLE IF NOT EXISTS language_preferences (user_id INTEGER PRIMARY KEY, language TEXT DEFAULT 'en');
                CREATE TABLE IF NOT EXISTS roulette_plays (user_id INTEGER, play_date DATE, play_count INTEGER DEFAULT 0, PRIMARY KEY (user_id, play_date));
                CREATE TABLE IF NOT EXISTS daily_plays (user_id INTEGER, game_name TEXT, play_date DATE, play_count INTEGER DEFAULT 0, PRIMARY KEY (user_id, game_name, play_date));
                CREATE TABLE IF NOT EXISTS balance_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    old_balance REAL NOT NULL,
                    new_balance REAL NOT NULL,
                    change_amount REAL NOT NULL,
                    reason TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS bot_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            # Migration: Add new columns if they don't exist
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT first_points_at FROM users LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE users ADD COLUMN first_points_at DATETIME")
            
            try:
                cursor.execute("SELECT monthly_wager FROM users LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE users ADD COLUMN monthly_wager INTEGER DEFAULT 0")
            
            try:
                cursor.execute("SELECT last_monthly_reset FROM users LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE users ADD COLUMN last_monthly_reset DATETIME")
            
            # Custom play limits table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS custom_play_limits (
                    user_id INTEGER PRIMARY KEY,
                    daily_limit INTEGER NOT NULL,
                    set_by INTEGER NOT NULL,
                    set_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Extra plays purchased table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS extra_plays_purchased (
                    user_id INTEGER,
                    play_date DATE,
                    extra_plays INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, play_date)
                )
            ''')
            
            try:
                cursor.execute("SELECT unlimited_games_until FROM users LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE users ADD COLUMN unlimited_games_until DATETIME")
            
            try:
                cursor.execute("SELECT forced_losses_remaining FROM users LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("ALTER TABLE users ADD COLUMN forced_losses_remaining INTEGER DEFAULT 0")
            
            # Migrate legacy roulette_plays to daily_plays and drop legacy limbo_plays
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO daily_plays (user_id, game_name, play_date, play_count)
                    SELECT user_id, 'roulette', play_date, play_count FROM roulette_plays
                ''')
            except sqlite3.OperationalError:
                pass
            
            # Drop legacy limbo_plays table (game removed from bot)
            try:
                cursor.execute('DROP TABLE IF EXISTS limbo_plays')
            except sqlite3.OperationalError:
                pass
            
            conn.commit()
    
    async def ensure_user_exists(self, db, user_id, initial_points=None):
        """
        Auto-register user if they don't exist. Creates entries in users and user_stats tables.
        Sets first_points_at timestamp when user receives their first positive points.
        
        Args:
            db: Active database connection
            user_id: Discord user ID
            initial_points: Points being added (used to set first_points_at if > 0)
        
        Returns:
            Current balance before any operation
        """
        # Create user with all default values if not exists
        await db.execute('''
            INSERT INTO users (user_id, balance, total_wagered, total_won, total_lost, 
                              vip_expires, created_at, first_points_at, monthly_wager, last_monthly_reset)
            VALUES (?, 0, 0, 0, 0, NULL, CURRENT_TIMESTAMP, NULL, 0, NULL)
            ON CONFLICT(user_id) DO NOTHING
        ''', (user_id,))
        
        # Create user_stats entry if not exists
        await db.execute('''
            INSERT OR IGNORE INTO user_stats (user_id, games_played, games_won, current_streak, max_streak)
            VALUES (?, 0, 0, 0, 0)
        ''', (user_id,))
        
        # Create language preference (default to English)
        await db.execute('''
            INSERT OR IGNORE INTO language_preferences (user_id, language)
            VALUES (?, 'en')
        ''', (user_id,))
        
        # Set first_points_at when user receives their first positive points
        if initial_points is not None and initial_points > 0:
            await db.execute('''
                UPDATE users 
                SET first_points_at = COALESCE(first_points_at, CURRENT_TIMESTAMP)
                WHERE user_id = ? AND first_points_at IS NULL
            ''', (user_id,))
        
        await db.commit()
        
        # Return current balance
        async with db.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def get_balance(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0
    
    async def get_forced_losses(self, user_id):
        """Get remaining forced losses for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT forced_losses_remaining FROM users WHERE user_id = ?', (user_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result and result[0] else 0
    
    async def decrement_forced_losses(self, user_id):
        """Decrease forced losses counter by 1"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE users 
                SET forced_losses_remaining = MAX(0, forced_losses_remaining - 1) 
                WHERE user_id = ?
            ''', (user_id,))
            await db.commit()
    
    async def log_balance_change(self, user_id, old_balance, new_balance, reason):
        """Log every balance change to balance_history table"""
        change_amount = new_balance - old_balance
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO balance_history (user_id, old_balance, new_balance, change_amount, reason)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, old_balance, new_balance, change_amount, reason))
            await db.commit()
    
    async def update_balance(self, user_id, amount, reason="Balance update"):
        async with aiosqlite.connect(self.db_path) as db:
            # Auto-register user and get old balance
            old_balance = await self.ensure_user_exists(db, user_id, initial_points=amount)
            
            # Apply overflow protection for positive amounts
            final_amount = amount
            was_capped = False
            if amount > 0:
                final_amount, was_capped = input_validator.prevent_balance_overflow(old_balance, amount)
                if was_capped:
                    reason += " (CAPPED AT MAX BALANCE)"
                    # Log the cap event
                    casino_logger.log_balance_cap(user_id, amount, final_amount)
            
            # Update balance with safe amount
            await db.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (final_amount, user_id))
            
            # Track wins/losses with ACTUAL credited amount (not original)
            if final_amount > 0:
                await db.execute('UPDATE users SET total_won = total_won + ? WHERE user_id = ?', (final_amount, user_id))
            elif final_amount < 0:
                await db.execute('UPDATE users SET total_lost = total_lost + ? WHERE user_id = ?', (-final_amount, user_id))
            
            await db.commit()
            
            # Get new balance
            async with db.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)) as cursor:
                new_balance = (await cursor.fetchone())[0]
            
            # Log balance change with actual amount credited
            await self.log_balance_change(user_id, old_balance, new_balance, reason)
            
            return new_balance
    
    async def add_wager(self, user_id, amount):
        async with aiosqlite.connect(self.db_path) as db:
            # Auto-register user (wagers also count as "first activity")
            await self.ensure_user_exists(db, user_id, initial_points=amount)
            
            # Update total wagered and monthly wager
            await db.execute('UPDATE users SET total_wagered = total_wagered + ?, monthly_wager = monthly_wager + ? WHERE user_id = ?', (amount, amount, user_id))
            rakeback_amount = int(amount * 0.01)
            await db.execute('INSERT OR IGNORE INTO rakeback (user_id, amount) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET amount = amount + ?', (user_id, rakeback_amount, rakeback_amount))
            await db.commit()
    
    async def can_claim_daily(self, user_id):
        today = datetime.date.today().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT 1 FROM daily_claims WHERE user_id = ? AND claim_date = ?', (user_id, today)) as cursor:
                return await cursor.fetchone() is None
    
    async def set_daily_claimed(self, user_id):
        today = datetime.date.today().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('INSERT OR REPLACE INTO daily_claims (user_id, claim_date) VALUES (?, ?)', (user_id, today))
            await db.commit()
    
    async def can_play_roulette(self, user_id):
        """Check if user can play roulette today (max 3 times)"""
        today = datetime.date.today().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT play_count FROM roulette_plays WHERE user_id = ? AND play_date = ?', (user_id, today)) as cursor:
                result = await cursor.fetchone()
                if result is None:
                    return True, 3  # Can play, 3 plays left
                play_count = result[0]
                if play_count >= 3:
                    return False, 0  # Cannot play, 0 plays left
                return True, 3 - play_count  # Can play, X plays left
    
    async def increment_roulette_plays(self, user_id):
        """Increment roulette play count for today"""
        today = datetime.date.today().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO roulette_plays (user_id, play_date, play_count) 
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, play_date) DO UPDATE SET play_count = play_count + 1
            ''', (user_id, today))
            await db.commit()
    
    async def can_claim_monthly(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT first_points_at, last_monthly_reset FROM users WHERE user_id = ?', (user_id,)) as cursor:
                result = await cursor.fetchone()
                if not result or not result[0]:
                    return False, "You need to earn points first!"
                
                first_points_at = datetime.datetime.fromisoformat(result[0])
                last_reset = result[1]
                
                # Check if at least 1 month has passed since first points
                one_month_later = first_points_at + datetime.timedelta(days=30)
                if datetime.datetime.now() < one_month_later:
                    days_left = (one_month_later - datetime.datetime.now()).days + 1
                    return False, f"You need to wait {days_left} more day(s) since your first points!"
                
                # Check if already claimed this month (since last reset)
                if last_reset:
                    last_reset_dt = datetime.datetime.fromisoformat(last_reset)
                    if (datetime.datetime.now() - last_reset_dt).days < 30:
                        days_left = 30 - (datetime.datetime.now() - last_reset_dt).days
                        return False, f"You already claimed this month! Wait {days_left} more day(s)."
                
                return True, "OK"
    
    async def get_monthly_wager(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT monthly_wager FROM users WHERE user_id = ?', (user_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result and result[0] else 0
    
    async def reset_monthly_wager(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('UPDATE users SET monthly_wager = 0, last_monthly_reset = CURRENT_TIMESTAMP WHERE user_id = ?', (user_id,))
            await db.commit()
    
    async def get_total_wagered(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT total_wagered FROM users WHERE user_id = ?', (user_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0
    
    async def set_balance(self, user_id, amount):
        async with aiosqlite.connect(self.db_path) as db:
            # Auto-register user and get old balance
            old_balance = await self.ensure_user_exists(db, user_id, initial_points=amount)
            
            # Set new balance
            await db.execute('UPDATE users SET balance = ? WHERE user_id = ?', (amount, user_id))
            await db.commit()
        
        # Log balance change
        await self.log_balance_change(user_id, old_balance, amount, "Admin: Balance set")
    
    async def set_total_wagered(self, user_id, amount):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('UPDATE users SET total_wagered = ? WHERE user_id = ?', (amount, user_id))
            await db.commit()
    
    async def get_top_users(self, limit=10):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT user_id, total_wagered FROM users ORDER BY total_wagered DESC LIMIT ?', (limit,)) as cursor:
                return await cursor.fetchall()
    
    async def get_rakeback(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT amount FROM rakeback WHERE user_id = ?', (user_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0
    
    async def claim_rakeback(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT amount FROM rakeback WHERE user_id = ?', (user_id,)) as cursor:
                result = await cursor.fetchone()
                if not result or result[0] <= 0: return 0
                rakeback_amount = result[0]
                await db.execute('UPDATE rakeback SET amount = 0 WHERE user_id = ?', (user_id,))
                await db.commit()
                return rakeback_amount
    
    async def has_wagered_200(self, user_id):
        return await self.get_total_wagered(user_id) >= 200
    
    async def is_blacklisted(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT 1 FROM blacklist WHERE user_id = ?', (user_id,)) as cursor:
                return await cursor.fetchone() is not None
    
    async def add_to_blacklist(self, user_id, reason, banned_by):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('INSERT OR REPLACE INTO blacklist (user_id, reason, banned_by) VALUES (?, ?, ?)', (user_id, reason, banned_by))
            await db.commit()
    
    async def remove_from_blacklist(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM blacklist WHERE user_id = ?', (user_id,))
            await db.commit()
    
    async def set_private_profile(self, user_id, private):
        async with aiosqlite.connect(self.db_path) as db:
            if private:
                await db.execute('INSERT OR IGNORE INTO private_profiles (user_id) VALUES (?)', (user_id,))
            else:
                await db.execute('DELETE FROM private_profiles WHERE user_id = ?', (user_id,))
            await db.commit()
    
    async def is_private_profile(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT 1 FROM private_profiles WHERE user_id = ?', (user_id,)) as cursor:
                return await cursor.fetchone() is not None
    
    async def record_activity(self, user_id, action):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('INSERT INTO user_activity (user_id, action) VALUES (?, ?)', (user_id, action))
            await db.commit()
    
    async def get_recent_activity(self, user_id, seconds=60):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT action FROM user_activity WHERE user_id = ? AND timestamp > datetime("now", ?)', (user_id, f"-{seconds} seconds")) as cursor:
                return [row[0] for row in await cursor.fetchall()]
    
    async def record_win(self, user_id, game, bet_amount, win_amount, multiplier):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('INSERT INTO win_history (user_id, game, bet_amount, win_amount, multiplier) VALUES (?, ?, ?, ?, ?)', (user_id, game, bet_amount, win_amount, multiplier))
            await db.commit()
    
    async def check_command_cooldown(self, user_id, command_name):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT last_used FROM command_cooldowns WHERE user_id = ? AND command_name = ?', (user_id, command_name)) as cursor:
                result = await cursor.fetchone()
                if not result: return True
                last_used = datetime.datetime.fromisoformat(result[0])
                return (datetime.datetime.now() - last_used).total_seconds() >= COMMAND_COOLDOWN
    
    async def set_command_cooldown(self, user_id, command_name):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('INSERT OR REPLACE INTO command_cooldowns (user_id, command_name, last_used) VALUES (?, ?, datetime("now"))', (user_id, command_name))
            await db.commit()
    
    async def get_balance_history(self, user_id, limit=15):
        """Get the last N balance changes for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT old_balance, new_balance, change_amount, reason, timestamp
                FROM balance_history
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit)) as cursor:
                return await cursor.fetchall()
    
    async def update_user_stats(self, user_id, won=False):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)', (user_id,))
            await db.execute('UPDATE user_stats SET games_played = games_played + 1 WHERE user_id = ?', (user_id,))
            
            if won:
                await db.execute('UPDATE user_stats SET games_won = games_won + 1, current_streak = current_streak + 1 WHERE user_id = ?', (user_id,))
                async with db.execute('SELECT current_streak, max_streak FROM user_stats WHERE user_id = ?', (user_id,)) as cursor:
                    stats = await cursor.fetchone()
                    if stats and stats[0] > stats[1]:
                        await db.execute('UPDATE user_stats SET max_streak = current_streak WHERE user_id = ?', (user_id,))
            else:
                await db.execute('UPDATE user_stats SET current_streak = 0 WHERE user_id = ?', (user_id,))
            
            await db.commit()
    
    async def get_user_stats(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT games_played, games_won, current_streak, max_streak FROM user_stats WHERE user_id = ?', (user_id,)) as cursor:
                result = await cursor.fetchone()
                if result:
                    return {
                        'games_played': result[0], 'games_won': result[1],
                        'win_rate': (result[1] / result[0] * 100) if result[0] > 0 else 0,
                        'current_streak': result[2], 'max_streak': result[3]
                    }
                return None

    async def is_vip(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT vip_expires FROM users WHERE user_id = ?', (user_id,)) as cursor:
                result = await cursor.fetchone()
                if result and result[0]:
                    return datetime.datetime.fromisoformat(result[0]) > datetime.datetime.now()
                return False
    
    async def add_vip(self, user_id, days=30):
        async with aiosqlite.connect(self.db_path) as db:
            expires = datetime.datetime.now() + datetime.timedelta(days=days)
            await db.execute('UPDATE users SET vip_expires = ? WHERE user_id = ?', (expires.isoformat(), user_id))
            await db.commit()
    
    async def remove_vip(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('UPDATE users SET vip_expires = NULL WHERE user_id = ?', (user_id,))
            await db.commit()
    
    async def get_vip_info(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT vip_expires FROM users WHERE user_id = ?', (user_id,)) as cursor:
                result = await cursor.fetchone()
                if result and result[0]:
                    expires = datetime.datetime.fromisoformat(result[0])
                    days_left = (expires - datetime.datetime.now()).days
                    return {'is_vip': expires > datetime.datetime.now(), 'expires': expires, 'days_left': max(0, days_left)}
                return {'is_vip': False, 'expires': None, 'days_left': 0}

    async def unlock_achievement(self, user_id, achievement_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT 1 FROM achievements WHERE user_id = ? AND achievement_id = ?', (user_id, achievement_id)) as cursor:
                if await cursor.fetchone(): return False
            
            await db.execute('INSERT INTO achievements (user_id, achievement_id) VALUES (?, ?)', (user_id, achievement_id))
            await db.commit()
            return True
    
    async def get_achievements(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT achievement_id, unlocked_at FROM achievements WHERE user_id = ?', (user_id,)) as cursor:
                return {row[0]: row[1] for row in await cursor.fetchall()}
    
    async def get_language(self, user_id):
        """Get user's preferred language (defaults to 'en')"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT language FROM language_preferences WHERE user_id = ?', (user_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result and result[0] else 'en'
    
    async def set_language(self, user_id, language_code):
        """Set user's preferred language"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO language_preferences (user_id, language) 
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET language = excluded.language
            ''', (user_id, language_code))
            await db.commit()
    
    async def fetch_one(self, query, params=()):
        """Helper: Execute query and return one row as dict"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def execute_query(self, query, params=()):
        """Helper: Execute update/insert query"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, params)
            await db.commit()

    # Boost System
    async def add_boost(self, user_id, boost_type, days=30):
        async with aiosqlite.connect(self.db_path) as db:
            expires = datetime.datetime.now() + datetime.timedelta(days=days)
            await db.execute('INSERT OR REPLACE INTO user_boosts (user_id, boost_type, multiplier, expires_at) VALUES (?, ?, ?, ?)', 
                           (user_id, boost_type, BOOSTS[boost_type]['multiplier'], expires.isoformat()))
            await db.commit()
    
    async def remove_boost(self, user_id, boost_type):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM user_boosts WHERE user_id = ? AND boost_type = ?', (user_id, boost_type))
            await db.commit()
    
    async def get_active_boosts(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT boost_type, multiplier, expires_at FROM user_boosts WHERE user_id = ? AND expires_at > datetime("now")', (user_id,)) as cursor:
                boosts = {}
                for row in await cursor.fetchall():
                    boost_type, multiplier, expires_at = row
                    expires = datetime.datetime.fromisoformat(expires_at)
                    days_left = (expires - datetime.datetime.now()).days
                    boosts[boost_type] = {
                        'multiplier': multiplier,
                        'expires': expires,
                        'days_left': max(0, days_left),
                        'name': BOOSTS[boost_type]['name']
                    }
                return boosts
    
    async def get_total_boost_multiplier(self, user_id):
        boosts = await self.get_active_boosts(user_id)
        total_multiplier = 1.0
        for boost in boosts.values():
            total_multiplier *= boost['multiplier']
        return total_multiplier
    
    # Language System
    async def get_user_language(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT language FROM language_preferences WHERE user_id = ?', (user_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 'en'
    
    async def set_user_language(self, user_id, language):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('INSERT OR REPLACE INTO language_preferences (user_id, language) VALUES (?, ?)', (user_id, language))
            await db.commit()

    # Lottery System
    async def buy_lottery_tickets(self, user_id, ticket_count):
        async with aiosqlite.connect(self.db_path) as db:
            today = datetime.date.today().isoformat()
            cost = ticket_count * LOTTERY_TICKET_PRICE
            
            # Check balance
            balance = await self.get_balance(user_id)
            if balance < cost:
                return False, "Insufficient balance"
            
            # Deduct cost
            await self.update_balance(user_id, -cost)
            
            # Add tickets
            await db.execute('''
                INSERT INTO lottery_tickets (user_id, ticket_count, lottery_date) 
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, lottery_date) DO UPDATE SET ticket_count = ticket_count + ?
            ''', (user_id, ticket_count, today, ticket_count))
            
            await db.commit()
            return True, f"Purchased {ticket_count} tickets for {cost} points"
    
    async def get_lottery_info(self, date=None):
        if date is None:
            date = datetime.date.today().isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Get total tickets and pool
            async with db.execute('SELECT SUM(ticket_count) FROM lottery_tickets WHERE lottery_date = ?', (date,)) as cursor:
                total_tickets = (await cursor.fetchone())[0] or 0
            
            total_pool = total_tickets * LOTTERY_TICKET_PRICE
            
            # Get user tickets
            async with db.execute('SELECT user_id, ticket_count FROM lottery_tickets WHERE lottery_date = ?', (date,)) as cursor:
                user_tickets = {row[0]: row[1] for row in await cursor.fetchall()}
            
            return {
                'total_tickets': total_tickets,
                'total_pool': total_pool,
                'user_tickets': user_tickets,
                'ticket_price': LOTTERY_TICKET_PRICE
            }
    
    async def draw_lottery(self, date=None):
        if date is None:
            date = datetime.date.today().isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            lottery_info = await self.get_lottery_info(date)
            
            if lottery_info['total_tickets'] == 0:
                return None, "No tickets sold today"
            
            # Create weighted list for drawing
            tickets_list = []
            for user_id, count in lottery_info['user_tickets'].items():
                tickets_list.extend([user_id] * count)
            
            # Draw winner
            winner_id = random.choice(tickets_list)
            prize = lottery_info['total_pool']
            
            # Award prize (no achievement reward)
            await self.update_balance(winner_id, prize, f"Lottery win ({prize})")
            
            # Record in history
            await db.execute('''
                INSERT OR REPLACE INTO lottery_history (lottery_date, winner_id, total_pool, total_tickets)
                VALUES (?, ?, ?, ?)
            ''', (date, winner_id, prize, lottery_info['total_tickets']))
            
            # Clear today's tickets
            await db.execute('DELETE FROM lottery_tickets WHERE lottery_date = ?', (date,))
            
            await db.commit()
            
            # Unlock achievement (tracking only, no points)
            await self.unlock_achievement(winner_id, 'lottery_winner')
            
            return winner_id, prize
    
    async def add_lottery_tickets(self, user_id, ticket_count):
        """Add lottery tickets to user (balance already deducted by caller)"""
        async with aiosqlite.connect(self.db_path) as db:
            today = datetime.date.today().isoformat()
            
            # Add tickets only (no balance deduction - caller already handled that)
            await db.execute('''
                INSERT INTO lottery_tickets (user_id, ticket_count, lottery_date) 
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, lottery_date) DO UPDATE SET ticket_count = ticket_count + ?
            ''', (user_id, ticket_count, today, ticket_count))
            
            await db.commit()
            return True
    
    async def get_lottery_tickets(self, user_id, date=None):
        if date is None:
            date = datetime.date.today().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT ticket_count FROM lottery_tickets WHERE user_id = ? AND lottery_date = ?', (user_id, date)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0
    
    async def get_lottery_pool(self, date=None):
        lottery_info = await self.get_lottery_info(date)
        return lottery_info['total_pool']
    
    async def get_total_lottery_tickets(self, date=None):
        lottery_info = await self.get_lottery_info(date)
        return lottery_info['total_tickets']

# ========== DAILY PLAY LIMIT SYSTEM ==========
class DailyPlayLimiter:
    REGULAR_LIMIT = 5
    VIP_LIMIT = 10
    
    def __init__(self, database):
        self.db = database
    
    async def check_and_increment(self, user_id, game_name):
        """Check if user can play, increment count if yes. Returns (can_play, remaining_plays, is_vip)"""
        today = datetime.date.today().isoformat()
        is_vip = await self.db.is_vip(user_id)
        
        # PRIORITY 1: Check unlimited games
        result = await self.db.fetch_one(
            'SELECT unlimited_games_until FROM users WHERE user_id = ?',
            (user_id,)
        )
        if result and result.get('unlimited_games_until'):
            unlimited_until_str = result['unlimited_games_until']
            try:
                unlimited_until = datetime.datetime.fromisoformat(unlimited_until_str)
                if unlimited_until > datetime.datetime.now():
                    # Unlimited - track but don't limit
                    await self.db.execute_query('''
                        INSERT INTO daily_plays (user_id, game_name, play_date, play_count)
                        VALUES (?, ?, ?, 1)
                        ON CONFLICT(user_id, game_name, play_date) 
                        DO UPDATE SET play_count = play_count + 1
                    ''', (user_id, game_name, today))
                    return True, 999, is_vip  # 999 = unlimited
            except (ValueError, TypeError) as e:
                print(f"⚠ Invalid unlimited_games_until format for user {user_id}: {e}")
            except Exception as e:
                print(f"⚠ Error checking unlimited games for user {user_id}: {e}")
        
        # PRIORITY 2: Get custom limit (replaces base limit)
        result = await self.db.fetch_one(
            'SELECT daily_limit FROM custom_play_limits WHERE user_id = ?',
            (user_id,)
        )
        base_limit = result['daily_limit'] if result else (self.VIP_LIMIT if is_vip else self.REGULAR_LIMIT)
        
        # Get current play count
        result = await self.db.fetch_one(
            'SELECT play_count FROM daily_plays WHERE user_id = ? AND game_name = ? AND play_date = ?',
            (user_id, game_name, today)
        )
        current_count = result['play_count'] if result else 0
        
        # Get extra plays remaining
        result = await self.db.fetch_one(
            'SELECT extra_plays FROM extra_plays_purchased WHERE user_id = ? AND play_date = ?',
            (user_id, today)
        )
        extra_plays_remaining = result['extra_plays'] if result else 0
        
        # PRIORITY 3: Check if within base/custom limit
        if current_count < base_limit:
            # Within normal limit - increment and return
            await self.db.execute_query('''
                INSERT INTO daily_plays (user_id, game_name, play_date, play_count)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(user_id, game_name, play_date) 
                DO UPDATE SET play_count = play_count + 1
            ''', (user_id, game_name, today))
            
            remaining = (base_limit - (current_count + 1)) + extra_plays_remaining
            return True, remaining, is_vip
        
        # PRIORITY 4: Check if can use extra plays
        if extra_plays_remaining > 0:
            # Consume one extra play
            await self.db.execute_query('''
                UPDATE extra_plays_purchased 
                SET extra_plays = extra_plays - 1 
                WHERE user_id = ? AND play_date = ?
            ''', (user_id, today))
            
            # Increment play count
            await self.db.execute_query('''
                INSERT INTO daily_plays (user_id, game_name, play_date, play_count)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(user_id, game_name, play_date) 
                DO UPDATE SET play_count = play_count + 1
            ''', (user_id, game_name, today))
            
            remaining = extra_plays_remaining - 1
            return True, remaining, is_vip
        
        # Limit reached - no plays available
        return False, 0, is_vip
    
    async def get_remaining_plays(self, user_id, game_name):
        """Get remaining plays for a user for a specific game"""
        today = datetime.date.today().isoformat()
        is_vip = await self.db.is_vip(user_id)
        limit = self.VIP_LIMIT if is_vip else self.REGULAR_LIMIT
        
        # Check if user has unlimited games active
        result = await self.db.fetch_one(
            'SELECT unlimited_games_until FROM users WHERE user_id = ?',
            (user_id,)
        )
        if result and result.get('unlimited_games_until'):
            unlimited_until_str = result['unlimited_games_until']
            try:
                unlimited_until = datetime.datetime.fromisoformat(unlimited_until_str)
                if unlimited_until > datetime.datetime.now():
                    return 999, is_vip  # 999 = unlimited
            except (ValueError, TypeError) as e:
                print(f"⚠ Invalid unlimited_games_until format for user {user_id}: {e}")
            except Exception as e:
                print(f"⚠ Error checking unlimited games for user {user_id}: {e}")
        
        result = await self.db.fetch_one(
            'SELECT play_count FROM daily_plays WHERE user_id = ? AND game_name = ? AND play_date = ?',
            (user_id, game_name, today)
        )
        current_count = result['play_count'] if result else 0
        
        return max(0, limit - current_count), is_vip

db = None  # Will be initialized in on_ready()
play_limiter = None  # Will be initialized in on_ready()

# ========== ANTI-CHEAT SYSTEM ==========
class AntiCheat:
    def __init__(self):
        self.command_count = {}
        self.last_reset = time.time()
    
    async def check_spam(self, user_id):
        current_time = time.time()
        if current_time - self.last_reset > 10:
            self.command_count.clear()
            self.last_reset = current_time
        
        if user_id not in self.command_count:
            self.command_count[user_id] = {'count': 0, 'first_time': current_time}
        
        self.command_count[user_id]['count'] += 1
        user_data = self.command_count[user_id]
        return (user_data['count'] >= SPAM_THRESHOLD and current_time - user_data['first_time'] <= 10)
    
    async def detect_suspicious_activity(self, user_id):
        recent_actions = await db.get_recent_activity(user_id, 10)
        if len(recent_actions) > 8: return "Too many actions too fast"
        wins = [action for action in recent_actions if 'win' in action]
        if len(wins) > 5 and len(wins) / len(recent_actions) > 0.8: return "Suspicious win pattern"
        return None
    
    async def analyze_win_patterns(self, user_id):
        recent_wins = await db.get_recent_activity(user_id, 300)
        return "Suspicious win frequency" if len([action for action in recent_wins if 'win' in action]) > 10 else None
    
    async def check_and_ban_cheater(self, ctx, user_id, reason):
        await db.add_to_blacklist(user_id, f"Auto-ban: {reason}", ctx.bot.user.id)
        cheat_channel = bot.get_channel(CHEAT_LOG_CHANNEL_ID)
        if cheat_channel:
            embed = discord.Embed(title="🚨 CHEATER DETECTED & BANNED", color=0xff0000, timestamp=datetime.datetime.utcnow())
            embed.add_field(name="User", value=f"<@{user_id}>", inline=True)
            embed.add_field(name="ID", value=user_id, inline=True)
            embed.add_field(name="Reason", value=reason, inline=True)
            embed.add_field(name="Detected In", value=ctx.channel.mention, inline=True)
            embed.add_field(name="Moderator", value="Anti-Cheat System", inline=True)
            await cheat_channel.send(embed=embed)
        
        try:
            await ctx.author.send(f"🚨 **YOU HAVE BEEN BANNED FROM USING THE BOT**\n**Reason:** {reason}\n**Appeal:** Contact server administrators")
        except (discord.Forbidden, discord.HTTPException):
            pass  # User has DMs disabled or blocked bot
        await ctx.send(f"🚨 {ctx.author.mention} has been banned for cheating!")

anti_cheat = AntiCheat()

# ========== INTERACTION HELPERS ==========
async def safe_defer(interaction):
    """
    Safely defer a Discord interaction to prevent 3-second timeout failures.
    Must be called at the START of button callbacks before heavy processing.
    
    Returns True if successfully deferred, False if already acknowledged.
    """
    try:
        if not interaction.response.is_done():
            await interaction.response.defer()
            return True
        return False
    except Exception as e:
        print(f"Defer error: {e}")
        return False

async def safe_interaction_response(interaction, embed=None, content=None, view=None, file=None):
    """
    Safely respond to an interaction, handling both initial and deferred states.
    Use this instead of interaction.response.edit_message() to avoid timeout errors.
    
    Args:
        interaction: The Discord interaction object
        embed: Optional Discord embed to send
        content: Optional text content to send
        view: Optional Discord view (buttons) - None to remove buttons
        file: Optional Discord file attachment
    """
    try:
        if interaction.response.is_done():
            # Already deferred or responded - use edit_original_response
            kwargs = {"embed": embed, "content": content, "view": view}
            if file:
                kwargs["attachments"] = [file]
            await interaction.edit_original_response(**kwargs)
        else:
            # Not yet responded - send initial response
            kwargs = {"embed": embed, "content": content, "view": view}
            if file:
                kwargs["file"] = file
            await interaction.response.send_message(**kwargs)
    except Exception as e:
        print(f"Interaction response error: {e}")
        try:
            # Fallback: try followup if response fails
            kwargs = {"embed": embed, "content": content, "view": view, "ephemeral": True}
            if file:
                kwargs["file"] = file
            await interaction.followup.send(**kwargs)
        except Exception as followup_error:
            print(f"Followup error: {followup_error}")

# ========== GAME SYSTEMS ==========
class GameSystem:
    # Mines game
    @staticmethod
    def get_mines_multiplier(mines, bet_amount):
        # REBALANCED v6: Higher multipliers for better player experience
        # mines 3-14: 1.3x to 2.0x
        # mines 15-24: 2.0x to 3.5x (max with diamonds will be 4.2x)
        base_multipliers = {
            3: 1.30, 4: 1.36, 5: 1.42, 6: 1.48, 7: 1.54, 8: 1.60, 9: 1.66, 10: 1.72,
            11: 1.78, 12: 1.84, 13: 1.92, 14: 2.00, 15: 2.00, 16: 2.15, 17: 2.30,
            18: 2.45, 19: 2.60, 20: 2.75, 21: 2.90, 22: 3.05, 23: 3.25, 24: 3.50
        }
        return base_multipliers.get(mines, 1.60)
    
    @staticmethod
    def get_mines_diamond_increment(mines):
        # REBALANCED v7: Simplified increments
        # For mines 3-10: 0.9x per diamond
        # For mines 11+: 0.30x per diamond
        if mines <= 10:
            return 0.9
        else:
            return 0.30
    
    # Slots game
    @staticmethod
    def get_slots_multiplier(symbols):
        if symbols[0] == symbols[1] == symbols[2]:
            return 7.0 if symbols[0] == '🎰' else 4.5 if symbols[0] == '💎' else 2.7
        elif symbols[0] == symbols[1] or symbols[1] == symbols[2]: return 1.3
        else: return 0.0
    
    # Tower game
    @staticmethod
    def get_tower_multiplier(difficulty, levels):
        return 1.0 + (difficulty * 0.06) + (levels * 0.13)
    
    # Blackjack game logic
    @staticmethod
    def play_blackjack():
        player_cards = [random.randint(1, 11), random.randint(1, 10)]
        dealer_cards = [random.randint(1, 11), random.randint(1, 10)]
        
        player_total = sum(player_cards)
        dealer_total = sum(dealer_cards)
        
        # Simple blackjack logic
        if player_total == 21:
            return "blackjack", player_cards, dealer_cards
        elif player_total > 21:
            return "bust", player_cards, dealer_cards
        elif dealer_total > 21:
            return "dealer_bust", player_cards, dealer_cards
        elif player_total > dealer_total:
            return "win", player_cards, dealer_cards
        elif dealer_total > player_total:
            return "lose", player_cards, dealer_cards
        else:
            return "push", player_cards, dealer_cards
    
    # Roulette game
    @staticmethod
    def play_roulette(bet_type, bet_number=None):
        number = random.randint(0, 36)
        is_red = number in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
        is_black = number in [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]
        is_even = number % 2 == 0 and number != 0
        is_odd = number % 2 == 1
        
        if bet_type == "number" and bet_number == number:
            return number, 10.0  # 10:1 payout
        elif bet_type == "red" and is_red:
            return number, 1.9   # 1.9:1 payout (reduced from 2.0)
        elif bet_type == "black" and is_black:
            return number, 1.9
        elif bet_type == "even" and is_even:
            return number, 1.9
        elif bet_type == "odd" and is_odd:
            return number, 1.9
        elif bet_type == "dozen1" and 1 <= number <= 12:
            return number, 2.8   # 2.8:1 payout (reduced from 3.0)
        elif bet_type == "dozen2" and 13 <= number <= 24:
            return number, 2.8
        elif bet_type == "dozen3" and 25 <= number <= 36:
            return number, 2.8
        else:
            return number, 0.0

# ========== LOGGING SYSTEM ==========
class WinLogger:
    @staticmethod
    async def log_win(user, game, bet_amount, win_amount, multiplier, details=None):
        """Log all game wins (including low wins) to WIN_LOG_CHANNEL"""
        win_channel = bot.get_channel(WIN_LOG_CHANNEL_ID)
        if win_channel:
            # Color based on win size
            if win_amount >= 1000:
                color = 0xFFD700  # Gold for big wins
                title = "🎊 BIG WIN!"
            elif win_amount >= 100:
                color = 0x00FF00  # Green for medium wins
                title = "💰 Win!"
            else:
                color = 0x00AA00  # Dark green for small wins
                title = "✅ Win"
            
            embed = discord.Embed(title=title, color=color, timestamp=datetime.datetime.utcnow())
            embed.add_field(name="Player", value=user.mention, inline=True)
            embed.add_field(name="Game", value=game, inline=True)
            embed.add_field(name="Bet", value=f"**{bet_amount:,}** points", inline=True)
            embed.add_field(name="Win", value=f"**{win_amount:,}** points", inline=True)
            embed.add_field(name="Multiplier", value=f"**x{multiplier:.2f}**", inline=True)
            embed.add_field(name="Profit", value=f"**+{win_amount - bet_amount:,}** points", inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
            
            balance = await db.get_balance(user.id)
            embed.set_footer(text=f"Balance: {balance:,} points")
            embed.set_thumbnail(url=user.display_avatar.url)
            await win_channel.send(embed=embed)

class ModLogger:
    @staticmethod
    async def log_command(admin_user, command_name, target_user=None, action_details=None, result=None):
        """Log all admin commands to MOD_LOG_CHANNEL"""
        mod_channel = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if mod_channel:
            embed = discord.Embed(
                title="🔧 Admin Command Used",
                color=0x0099FF,
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Admin", value=admin_user.mention, inline=True)
            embed.add_field(name="Command", value=f"`.{command_name}`", inline=True)
            
            if target_user:
                embed.add_field(name="Target", value=target_user if isinstance(target_user, str) else target_user.mention, inline=True)
            
            if action_details:
                embed.add_field(name="Action", value=action_details, inline=False)
            
            if result:
                embed.add_field(name="Result", value=result, inline=False)
            
            embed.set_thumbnail(url=admin_user.display_avatar.url)
            await mod_channel.send(embed=embed)

# ========== NOTIFICATION SYSTEM ==========
class NotificationSystem:
    @staticmethod
    async def send_notification(user, title, message, color=0x00ff00):
        try:
            embed = discord.Embed(title=title, description=message, color=color, timestamp=datetime.datetime.utcnow())
            await user.send(embed=embed)
            return True
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            return False
        except Exception as e:
            print(f"⚠ Unexpected error sending notification to user {user.id}: {e}")
            return False
    
    @staticmethod
    async def notify_lottery_winner(winner_id, prize_amount, ticket_count):
        try:
            user = await bot.fetch_user(winner_id)
            embed = discord.Embed(
                title="🎉 CONGRATULATIONS! YOU WON THE LOTTERY! 🎉",
                description=f"You won **{prize_amount:,}** points in the daily lottery!",
                color=0xFFD700,
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Your Tickets", value=f"**{ticket_count}** tickets", inline=True)
            embed.add_field(name="Total Prize", value=f"**{prize_amount:,}** points", inline=True)
            await user.send(embed=embed)
            return True
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            return False
        except Exception as e:
            print(f"⚠ Unexpected error notifying lottery winner {winner_id}: {e}")
            return False

# ========== MODERATION ==========
class Moderation:
    @staticmethod
    def is_suspicious(message):
        message_lower = message.lower()
        suspicious_patterns = [r'https?://', r'www\.', r'discord\.gg/', r't\.me/', r'telegram\.me/', 'dm for buy', 'dm to buy', 'buy from me', 'selling', 'cheap points', 'contact me to buy', 'whisper me', 'message me to buy']
        return any(re.search(pattern, message_lower) for pattern in suspicious_patterns)

# ========== COOLDOWN DECORATOR ==========
def cooldown_check():
    async def predicate(ctx):
        user_id = ctx.author.id
        if await db.is_blacklisted(user_id):
            await ctx.send("🚨 **YOU ARE BANNED FROM USING THIS BOT**")
            return False
        
        # Check command-specific cooldown
        if not await db.check_command_cooldown(user_id, ctx.command.name):
            await ctx.send(f"⏰ **Please wait {COMMAND_COOLDOWN} seconds before using this command again!**")
            return False
        
        # Check spam
        if await anti_cheat.check_spam(user_id):
            if ctx.guild and ctx.guild.me.guild_permissions.moderate_members:
                await ctx.author.timeout(datetime.timedelta(seconds=SPAM_PUNISHMENT), reason="Command spam")
                await ctx.send(f"🚨 {ctx.author.mention} has been timed out for 1 day for spamming commands!")
            else:
                await ctx.send(f"🚨 {ctx.author.mention} stop spamming commands!")
            return False
        
        # Set cooldown for this command
        await db.set_command_cooldown(user_id, ctx.command.name)
        await db.record_activity(user_id, f"command_{ctx.command.name}")
        return True
    return commands.check(predicate)

# ========== INPUT VALIDATION ==========
class InputValidator:
    """Validates user inputs to prevent bugs and exploits"""
    
    @staticmethod
    def validate_bet_amount(amount: int, user_balance: int) -> tuple[bool, str]:
        """
        Validate bet amount with comprehensive checks
        Returns: (is_valid, error_message)
        """
        # Check for negative or zero amounts
        if amount <= 0:
            return False, "❌ Bet amount must be positive!"
        
        # Check minimum bet
        if amount < MIN_BET_AMOUNT:
            return False, f"❌ Minimum bet is {MIN_BET_AMOUNT:,} points!"
        
        # Check maximum bet
        if amount > MAX_BET_AMOUNT:
            return False, f"❌ Maximum bet is {MAX_BET_AMOUNT:,} points!"
        
        # Check if user has enough balance
        if amount > user_balance:
            return False, f"❌ Insufficient balance! You have {user_balance:,} points."
        
        # Prevent betting everything (safety feature) - ONLY for balances > 100
        # For small balances, allow full amount
        if user_balance > 100:
            max_allowed = int(user_balance * MAX_BET_PERCENTAGE)
            if amount > max_allowed:
                return False, f"❌ You can't bet more than {int(MAX_BET_PERCENTAGE * 100)}% of your balance ({max_allowed:,} points) for safety!"
        
        return True, ""
    
    @staticmethod
    def sanitize_amount(amount) -> Optional[int]:
        """Convert amount to integer, return None if invalid"""
        try:
            if isinstance(amount, (int, float)):
                return int(amount)
            amount_str = str(amount).strip()
            # Remove common formatting
            amount_str = amount_str.replace(',', '').replace(' ', '')
            return int(amount_str)
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def prevent_balance_overflow(current_balance: int, amount_to_add: int) -> tuple[int, bool]:
        """
        Prevent balance from exceeding maximum
        Returns: (safe_amount_to_add, was_capped)
        """
        if current_balance >= MAX_BALANCE:
            return 0, True
        
        if current_balance + amount_to_add > MAX_BALANCE:
            safe_amount = MAX_BALANCE - current_balance
            return safe_amount, True
        
        return amount_to_add, False

input_validator = InputValidator()

# ========== AMOUNT PARSER ==========
async def parse_amount(amount_str, user_id):
    """Parse amount string (supports 'half', 'all', or numeric values)"""
    if isinstance(amount_str, int):
        return max(0, amount_str)  # Ensure non-negative
    
    amount_str = str(amount_str).lower().strip()
    balance = await db.get_balance(user_id)
    
    if amount_str in ['all', 'max']:
        # Apply max bet percentage for safety
        return min(balance, int(balance * MAX_BET_PERCENTAGE)) if balance > 100 else balance
    elif amount_str in ['half', '50%']:
        return balance // 2
    else:
        # Use sanitize method for better parsing
        amount = input_validator.sanitize_amount(amount_str)
        if amount is None or amount < 0:
            return None
        return amount

# ========== BALANCE RE-VALIDATION HELPER ==========
async def ensure_can_bet(user_id: int, amount: int, game_name: str = None) -> tuple[bool, str]:
    """
    Re-validate that user can still bet this amount (for replay/multi-round scenarios)
    Returns: (can_bet, error_message)
    
    SECURITY: Prevents 0-balance exploits in button callbacks and replay paths
    """
    # Check minimum bet
    if amount <= 0:
        return False, "❌ Bet amount must be positive!"
    
    if amount < MIN_BET_AMOUNT:
        return False, f"❌ Minimum bet is {MIN_BET_AMOUNT:,} points!"
    
    # Check current balance
    current_balance = await db.get_balance(user_id)
    if current_balance < amount:
        return False, f"❌ Insufficient balance! You have {current_balance:,} points but need {amount:,} points."
    
    # Check maximum bet
    if amount > MAX_BET_AMOUNT:
        return False, f"❌ Maximum bet is {MAX_BET_AMOUNT:,} points!"
    
    # Optionally check play limits if game_name provided
    if game_name and play_limiter:
        # Note: We don't increment here, just check if they CAN play
        # This is a read-only validation for safety
        pass
    
    return True, ""

# ========== STRUCTURED LOGGING SYSTEM ==========
class CasinoLogger:
    """Lightweight structured logging for critical casino events"""
    
    def __init__(self):
        self.validation_failures = {}  # Rate limiting: {user_id: count}
        self.last_reset = time.time()
    
    def _should_log(self, user_id, event_type):
        """Rate limiting to prevent log spam"""
        current_time = time.time()
        
        # Reset counters every 5 minutes
        if current_time - self.last_reset > 300:
            self.validation_failures.clear()
            self.last_reset = current_time
        
        # Limit validation failure logs to 3 per user per 5 minutes
        if event_type == "validation_failure":
            count = self.validation_failures.get(user_id, 0)
            if count >= 3:
                return False
            self.validation_failures[user_id] = count + 1
        
        return True
    
    def log_bet(self, user_id, game, amount, outcome, winnings=0):
        """Log bet attempt and outcome"""
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        status = "WIN" if outcome else "LOSS"
        print(f"[BET] {timestamp} | User:{user_id} | Game:{game} | Bet:{amount:,} | {status} | Winnings:{winnings:,}")
    
    def log_validation_failure(self, user_id, reason):
        """Log validation failures with rate limiting"""
        if not self._should_log(user_id, "validation_failure"):
            return
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[VALIDATION] {timestamp} | User:{user_id} | Failed: {reason}")
    
    def log_balance_cap(self, user_id, attempted_amount, capped_amount):
        """Log when balance hits maximum"""
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[BALANCE_CAP] {timestamp} | User:{user_id} | Attempted:{attempted_amount:,} | Capped:{capped_amount:,}")
    
    def log_suspicious_activity(self, user_id, activity_type, details):
        """Log suspicious or unusual activity"""
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[SUSPICIOUS] {timestamp} | User:{user_id} | Type:{activity_type} | Details:{details}")

casino_logger = CasinoLogger()

# ========== SHARED BET VALIDATION HELPER ==========
async def ensure_valid_bet(ctx, user_id, raw_amount):
    """
    Central bet validation helper - combines parsing + validation
    Returns: (valid_amount, error_message) or (None, error_message)
    """
    # Step 1: Parse the amount
    amount = await parse_amount(raw_amount, user_id)
    
    if amount is None:
        casino_logger.log_validation_failure(user_id, f"Invalid amount format: {raw_amount}")
        return None, "❌ Invalid amount! Use a number, 'half', or 'all'."
    
    if amount == 0:
        casino_logger.log_validation_failure(user_id, "Zero amount bet attempt")
        return None, "❌ Bet amount must be greater than 0!"
    
    # Step 2: Get user balance
    balance = await db.get_balance(user_id)
    
    # Step 3: Validate the bet amount
    is_valid, error_msg = input_validator.validate_bet_amount(amount, balance)
    
    if not is_valid:
        casino_logger.log_validation_failure(user_id, error_msg)
        return None, error_msg
    
    # All checks passed
    return amount, None

# ========== ACHIEVEMENT CHECKER ==========
class AchievementChecker:
    @staticmethod
    async def check_achievements(ctx, user_id, action_data):
        unlocked = []
        
        if action_data.get('won') and action_data.get('first_win', True):
            if await db.unlock_achievement(user_id, 'first_win'):
                unlocked.append('first_win')
        
        if action_data.get('bet_amount', 0) >= 1000:
            if await db.unlock_achievement(user_id, 'high_roller'):
                unlocked.append('high_roller')
        
        stats = await db.get_user_stats(user_id)
        if stats and stats['current_streak'] >= 5:
            if await db.unlock_achievement(user_id, 'lucky_streak'):
                unlocked.append('lucky_streak')
        
        if action_data.get('multiplier', 0) >= 10.0:
            if await db.unlock_achievement(user_id, 'jackpot_king'):
                unlocked.append('jackpot_king')
        
        total_wagered = await db.get_total_wagered(user_id)
        if total_wagered >= 1000000:
            if await db.unlock_achievement(user_id, 'millionaire'):
                unlocked.append('millionaire')
        
        return unlocked

achievement_checker = AchievementChecker()

# ========== IMAGE GENERATION ==========
async def generate_rakeback_image(user, balance, rakeback_amount):
    """Generate a custom rakeback image with user's profile picture, name, and balance"""
    try:
        # Create image (800x400)
        img = Image.new('RGB', (800, 400), color='#2C2F33')
        draw = ImageDraw.Draw(img)
        
        # Download user avatar (non-blocking)
        avatar_bytes = await user.display_avatar.read()
        avatar = Image.open(BytesIO(avatar_bytes))
        avatar = avatar.resize((150, 150))
        
        # Make avatar circular
        mask = Image.new('L', (150, 150), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, 150, 150), fill=255)
        
        # Paste avatar with mask
        img.paste(avatar, (50, 125), mask)
        
        # Try to use a nice font, fallback to default if not available
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
            info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        except:
            title_font = ImageFont.load_default()
            name_font = ImageFont.load_default()
            info_font = ImageFont.load_default()
        
        # Draw title
        draw.text((250, 30), "💸 RAKEBACK INFO", fill='#FFD700', font=title_font)
        
        # Draw username
        username = user.display_name if len(user.display_name) <= 20 else user.display_name[:17] + "..."
        draw.text((250, 100), f"👤 {username}", fill='#FFFFFF', font=name_font)
        
        # Draw separator line
        draw.line([(250, 150), (750, 150)], fill='#7289DA', width=3)
        
        # Draw balance
        draw.text((250, 180), f"💰 Balance:", fill='#FFFFFF', font=info_font)
        draw.text((250, 220), f"${balance:,} points", fill='#43B581', font=name_font)
        
        # Draw rakeback amount
        draw.text((250, 280), f"💸 Rakeback Available:", fill='#FFFFFF', font=info_font)
        draw.text((250, 320), f"${rakeback_amount:,} points", fill='#FFD700', font=name_font)
        
        # Save to bytes
        output = BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
        
        return output
    except Exception as e:
        print(f"Error generating rakeback image: {e}")
        return None

# ========== PLAYER DATA SNAPSHOT SYSTEM ==========
player_snapshots = {}  # Store {user_id: {'balance': ..., 'timestamp': ...}}

async def save_player_snapshots():
    """Save current player balances every hour"""
    global player_snapshots
    try:
        async with aiosqlite.connect(db.db_path) as conn:
            cursor = await conn.execute("SELECT user_id, balance FROM users")
            rows = await cursor.fetchall()
            
            timestamp = datetime.datetime.utcnow().isoformat()
            for user_id, balance in rows:
                player_snapshots[user_id] = {
                    'balance': balance,
                    'timestamp': timestamp
                }
            
            print(f"✅ Saved snapshots for {len(rows)} players at {timestamp}")
    except Exception as e:
        print(f"⚠ Error saving player snapshots: {e}")

async def get_player_snapshot(user_id):
    """Get last saved snapshot for a player"""
    return player_snapshots.get(user_id, None)

async def generate_blackjack_image(player_hand, dealer_hand, show_all_dealer=True):
    """Generate a composite image showing blackjack cards"""
    try:
        card_width = 100
        card_height = 145
        spacing = 10
        padding = 20
        label_height = 40
        
        max_cards = max(len(player_hand), len(dealer_hand))
        img_width = (max_cards * (card_width + spacing)) + (padding * 2)
        img_height = (card_height * 2) + (label_height * 2) + (spacing * 3) + (padding * 2)
        
        img = Image.new('RGB', (img_width, img_height), color='#0E4C2A')
        draw = ImageDraw.Draw(img)
        
        try:
            label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except:
            label_font = ImageFont.load_default()
        
        y_pos = padding
        draw.text((padding, y_pos), "🎴 YOUR HAND", fill='#FFD700', font=label_font)
        y_pos += label_height
        
        for i, card in enumerate(player_hand):
            card_url = BlackjackGame.get_card_image_url(card)
            x_pos = padding + (i * (card_width + spacing))
            try:
                response = await asyncio.to_thread(requests.get, card_url, timeout=5)
                card_img = Image.open(BytesIO(response.content))
                card_img = card_img.resize((card_width, card_height))
                img.paste(card_img, (x_pos, y_pos))
            except:
                draw.rectangle(
                    [x_pos, y_pos, x_pos + card_width, y_pos + card_height],
                    outline='white', width=2
                )
                draw.text((x_pos + 10, y_pos + 60), card, fill='white', font=label_font)
        
        y_pos += card_height + spacing
        draw.text((padding, y_pos), "🃏 DEALER HAND", fill='#FFD700', font=label_font)
        y_pos += label_height
        
        for i, card in enumerate(dealer_hand):
            x_pos = padding + (i * (card_width + spacing))
            
            if not show_all_dealer and i > 0:
                try:
                    response = await asyncio.to_thread(requests.get, "https://deckofcardsapi.com/static/img/back.png", timeout=5)
                    card_img = Image.open(BytesIO(response.content))
                    card_img = card_img.resize((card_width, card_height))
                    img.paste(card_img, (x_pos, y_pos))
                except:
                    draw.rectangle(
                        [x_pos, y_pos, x_pos + card_width, y_pos + card_height],
                        fill='#1E1E1E', outline='white', width=2
                    )
                    draw.text((x_pos + 30, y_pos + 60), "❓", fill='white', font=label_font)
            else:
                card_url = BlackjackGame.get_card_image_url(card)
                try:
                    response = await asyncio.to_thread(requests.get, card_url, timeout=5)
                    card_img = Image.open(BytesIO(response.content))
                    card_img = card_img.resize((card_width, card_height))
                    img.paste(card_img, (x_pos, y_pos))
                except:
                    draw.rectangle(
                        [x_pos, y_pos, x_pos + card_width, y_pos + card_height],
                        outline='white', width=2
                    )
                    draw.text((x_pos + 10, y_pos + 60), card, fill='white', font=label_font)
        
        output = BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
        
        return output
    except Exception as e:
        print(f"Error generating blackjack image: {e}")
        return None

async def generate_baccarat_image(player_hand, banker_hand):
    """Generate composite image for Baccarat game"""
    try:
        card_width = 100
        card_height = 145
        spacing = 10
        padding = 20
        label_height = 40
        
        max_cards = max(len(player_hand), len(banker_hand))
        img_width = (max_cards * (card_width + spacing)) + (padding * 2)
        img_height = (card_height * 2) + (label_height * 2) + (spacing * 3) + (padding * 2)
        
        img = Image.new('RGB', (img_width, img_height), color='#0E4C2A')
        draw = ImageDraw.Draw(img)
        
        try:
            label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except:
            label_font = ImageFont.load_default()
        
        y_pos = padding
        draw.text((padding, y_pos), "👤 PLAYER", fill='#FFD700', font=label_font)
        y_pos += label_height
        
        for i, card in enumerate(player_hand):
            card_url = BlackjackGame.get_card_image_url(card)
            x_pos = padding + (i * (card_width + spacing))
            try:
                response = await asyncio.to_thread(requests.get, card_url, timeout=5)
                card_img = Image.open(BytesIO(response.content))
                card_img = card_img.resize((card_width, card_height))
                img.paste(card_img, (x_pos, y_pos))
            except:
                draw.rectangle([x_pos, y_pos, x_pos + card_width, y_pos + card_height], outline='white', width=2)
                draw.text((x_pos + 10, y_pos + 60), card, fill='white', font=label_font)
        
        y_pos += card_height + spacing
        draw.text((padding, y_pos), "🏦 BANKER", fill='#FFD700', font=label_font)
        y_pos += label_height
        
        for i, card in enumerate(banker_hand):
            card_url = BlackjackGame.get_card_image_url(card)
            x_pos = padding + (i * (card_width + spacing))
            try:
                response = await asyncio.to_thread(requests.get, card_url, timeout=5)
                card_img = Image.open(BytesIO(response.content))
                card_img = card_img.resize((card_width, card_height))
                img.paste(card_img, (x_pos, y_pos))
            except:
                draw.rectangle([x_pos, y_pos, x_pos + card_width, y_pos + card_height], outline='white', width=2)
                draw.text((x_pos + 10, y_pos + 60), card, fill='white', font=label_font)
        
        output = BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
        return output
    except Exception as e:
        print(f"Error generating baccarat image: {e}")
        return None

async def generate_slots_image(reels, result_text):
    """Generate slot machine visual with reels"""
    try:
        img_width = 800
        img_height = 400
        
        img = Image.new('RGB', (img_width, img_height), color='#8B0000')
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
            reel_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        except:
            title_font = ImageFont.load_default()
            reel_font = ImageFont.load_default()
        
        draw.text((img_width//2 - 120, 30), "🎰 SLOTS 🎰", fill='#FFD700', font=title_font)
        
        draw.rectangle([50, 100, img_width-50, 300], fill='#000000', outline='#FFD700', width=5)
        
        reel_width = 200
        reel_x_positions = [100, 300, 500]
        
        for i, (x_pos, symbol) in enumerate(zip(reel_x_positions, reels)):
            draw.rectangle([x_pos, 120, x_pos + reel_width, 280], fill='#FFFFFF', outline='#000000', width=3)
            
            bbox = draw.textbbox((0, 0), symbol, font=reel_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = x_pos + (reel_width - text_width) // 2
            text_y = 150
            draw.text((text_x, text_y), symbol, fill='#000000', font=reel_font)
        
        result_bbox = draw.textbbox((0, 0), result_text, font=title_font)
        result_width = result_bbox[2] - result_bbox[0]
        draw.text((img_width//2 - result_width//2, 320), result_text, fill='#FFFFFF', font=title_font)
        
        output = BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
        return output
    except Exception as e:
        print(f"Error generating slots image: {e}")
        return None

async def generate_dice_image(roll, target=None):
    """Generate dice visualization"""
    try:
        img_width = 400
        img_height = 300
        
        img = Image.new('RGB', (img_width, img_height), color='#1a472a')
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
            dice_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
        except:
            title_font = ImageFont.load_default()
            dice_font = ImageFont.load_default()
        
        draw.text((img_width//2 - 80, 20), "🎲 DICE 🎲", fill='#FFD700', font=title_font)
        
        dice_emojis = {1: '⚀', 2: '⚁', 3: '⚂', 4: '⚃', 5: '⚄', 6: '⚅'}
        dice_symbol = dice_emojis.get(roll, '?')
        
        draw.rectangle([100, 80, 300, 220], fill='#FFFFFF', outline='#000000', width=4)
        draw.text((120, 100), dice_symbol, fill='#000000', font=dice_font)
        
        if target:
            draw.text((img_width//2 - 100, 240), f"Target: {target}", fill='#FFFFFF', font=title_font)
        
        output = BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
        return output
    except Exception as e:
        print(f"Error generating dice image: {e}")
        return None

async def generate_coinflip_image(result, choice):
    """Generate coin flip visualization"""
    try:
        img_width = 400
        img_height = 300
        
        img = Image.new('RGB', (img_width, img_height), color='#2C3E50')
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
            coin_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        except:
            title_font = ImageFont.load_default()
            coin_font = ImageFont.load_default()
        
        draw.text((img_width//2 - 100, 20), "🪙 COINFLIP", fill='#FFD700', font=title_font)
        
        draw.ellipse([100, 80, 300, 220], fill='#FFD700', outline='#000000', width=4)
        
        coin_text = result.upper()
        bbox = draw.textbbox((0, 0), coin_text, font=coin_font)
        text_width = bbox[2] - bbox[0]
        draw.text((img_width//2 - text_width//2, 120), coin_text, fill='#000000', font=coin_font)
        
        choice_text = f"Your choice: {choice.upper()}"
        draw.text((img_width//2 - 120, 240), choice_text, fill='#FFFFFF', font=title_font)
        
        output = BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
        return output
    except Exception as e:
        print(f"Error generating coinflip image: {e}")
        return None

async def generate_crash_image(crash_point, cashout, won):
    """Generate crash graph visualization"""
    try:
        img_width = 600
        img_height = 400
        
        img = Image.new('RGB', (img_width, img_height), color='#1a1a2e')
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
            label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        except:
            title_font = ImageFont.load_default()
            label_font = ImageFont.load_default()
        
        draw.text((img_width//2 - 80, 20), "🎈 CRASH", fill='#FFD700', font=title_font)
        
        margin = 50
        graph_x = margin
        graph_y = 80
        graph_width = img_width - (margin * 2)
        graph_height = img_height - 150
        
        draw.rectangle([graph_x, graph_y, graph_x + graph_width, graph_y + graph_height], outline='#FFFFFF', width=2)
        
        for i in range(1, 6):
            y = graph_y + graph_height - (i * graph_height // 5)
            draw.line([(graph_x, y), (graph_x + graph_width, y)], fill='#444444', width=1)
            draw.text((10, y - 10), f"{i}x", fill='#FFFFFF', font=label_font)
        
        points = []
        for i in range(100):
            x = graph_x + (i * graph_width // 100)
            mult = 1.0 + (i / 100) * max(crash_point, cashout)
            if mult > crash_point:
                break
            y = graph_y + graph_height - int((mult - 1) * graph_height / 4)
            points.append((x, y))
        
        if len(points) > 1:
            draw.line(points, fill='#00FF00' if won else '#FF0000', width=3)
        
        crash_x = graph_x + int((crash_point / 5) * graph_width)
        crash_y = graph_y + graph_height - int((crash_point - 1) * graph_height / 4)
        if crash_y > graph_y:
            draw.ellipse([crash_x-8, crash_y-8, crash_x+8, crash_y+8], fill='#FF0000')
            draw.text((crash_x + 15, crash_y - 10), f"💥 {crash_point:.2f}x", fill='#FF0000', font=label_font)
        
        if won:
            cashout_x = graph_x + int((cashout / 5) * graph_width)
            cashout_y = graph_y + graph_height - int((cashout - 1) * graph_height / 4)
            if cashout_y > graph_y:
                draw.ellipse([cashout_x-8, cashout_y-8, cashout_x+8, cashout_y+8], fill='#00FF00')
        
        result_text = f"Cashed out: {cashout:.2f}x | Crashed: {crash_point:.2f}x"
        draw.text((margin, img_height - 40), result_text, fill='#FFFFFF', font=label_font)
        
        output = BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
        return output
    except Exception as e:
        print(f"Error generating crash image: {e}")
        return None

async def generate_roulette_image(result, bet_type, won):
    """Generate roulette wheel visualization"""
    try:
        img_width = 500
        img_height = 500
        
        img = Image.new('RGB', (img_width, img_height), color='#0A3D0A')
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
            result_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        except:
            title_font = ImageFont.load_default()
            result_font = ImageFont.load_default()
        
        draw.text((img_width//2 - 110, 20), "🎡 ROULETTE", fill='#FFD700', font=title_font)
        
        center_x, center_y = img_width // 2, img_height // 2 + 20
        outer_radius = 180
        inner_radius = 60
        
        draw.ellipse([center_x - outer_radius, center_y - outer_radius, 
                      center_x + outer_radius, center_y + outer_radius], 
                     fill='#8B4513', outline='#FFD700', width=5)
        
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        result_color = '#FF0000' if result in red_numbers else '#000000' if result != 0 else '#00FF00'
        
        draw.ellipse([center_x - inner_radius, center_y - inner_radius,
                      center_x + inner_radius, center_y + inner_radius],
                     fill=result_color, outline='#FFD700', width=3)
        
        result_text = str(result)
        bbox = draw.textbbox((0, 0), result_text, font=result_font)
        text_width = bbox[2] - bbox[0]
        draw.text((center_x - text_width//2, center_y - 20), result_text, fill='#FFFFFF', font=result_font)
        
        bet_display = f"Bet: {bet_type.upper()}"
        result_display = "WIN! ✅" if won else "LOSS ❌"
        draw.text((img_width//2 - 80, img_height - 80), bet_display, fill='#FFFFFF', font=title_font)
        draw.text((img_width//2 - 70, img_height - 50), result_display, 
                  fill='#00FF00' if won else '#FF0000', font=title_font)
        
        output = BytesIO()
        img.save(output, format='PNG')
        output.seek(0)
        return output
    except Exception as e:
        print(f"Error generating roulette image: {e}")
        return None

# ========== BACKGROUND TASKS ==========
async def background_tasks():
    await bot.wait_until_ready()
    failure_count = {}
    while not bot.is_closed():
        # Run each task independently to prevent one failure from blocking others
        for task_name, task_func in [
            ("backup", db.create_backup),
            ("cleanup_logs", db.cleanup_old_logs),
            ("expired_items", check_expired_items),
            ("lottery_draw", check_lottery_draw),
            ("player_snapshots", save_player_snapshots)
        ]:
            try:
                await task_func()
                failure_count[task_name] = 0
            except Exception as e:
                failure_count[task_name] = failure_count.get(task_name, 0) + 1
                print(f"⚠ Background task '{task_name}' failed (attempt {failure_count[task_name]}): {e}")
                if failure_count[task_name] >= 3:
                    print(f"🚨 Background task '{task_name}' failed 3+ times - check system health!")
        
        await asyncio.sleep(3600)  # Check every hour

async def check_expired_items():
    async with aiosqlite.connect(db.db_path) as conn:
        # Clean up expired VIP status
        await conn.execute('DELETE FROM users WHERE vip_expires IS NOT NULL AND vip_expires < datetime("now")')
        # Clean up expired boosts
        await conn.execute('DELETE FROM user_boosts WHERE expires_at < datetime("now")')
        await conn.commit()

async def check_lottery_draw():
    """Check if it's time for lottery draw with database-backed timestamp to prevent missed/double draws"""
    async with aiosqlite.connect(db.db_path) as conn:
        # Use transaction to prevent double draws
        await conn.execute("BEGIN IMMEDIATE")
        
        try:
            # Get last draw timestamp
            cursor = await conn.execute("SELECT value FROM bot_settings WHERE key = 'last_lottery_draw_at'")
            row = await cursor.fetchone()
            
            # Calculate if we should draw now (7 PM HKT = 11:00 UTC)
            now_utc = datetime.datetime.utcnow()
            today_draw_time = datetime.datetime.combine(
                now_utc.date(),
                datetime.time(hour=11, minute=0)  # 11:00 UTC = 7 PM HKT
            )
            
            # If it's past draw time and we haven't drawn today
            should_draw = False
            if now_utc >= today_draw_time:
                if row and row[0]:
                    # Parse last draw timestamp
                    last_draw = datetime.datetime.fromisoformat(row[0])
                    # Only draw if last draw was before today's draw time
                    if last_draw < today_draw_time:
                        should_draw = True
                else:
                    # Never drawn before - should draw
                    should_draw = True
            
            if not should_draw:
                await conn.rollback()
                return
            
            # Perform draw
            winner_id, prize = await db.draw_lottery()
            
            # Update last draw timestamp
            await conn.execute(
                "INSERT OR REPLACE INTO bot_settings (key, value, updated_at) VALUES (?, ?, ?)",
                ('last_lottery_draw_at', now_utc.isoformat(), now_utc)
            )
            await conn.commit()
            
        except Exception as e:
            await conn.rollback()
            print(f"⚠ Lottery draw error: {e}")
            return
        
        # Send announcements (outside transaction)
        lottery_channel = bot.get_channel(LOTTERY_CHANNEL_ID)
        
        if lottery_channel:
            if winner_id:
                # Winner exists - send celebration message with @everyone ping
                lottery_info = await db.get_lottery_info()
                total_participants = len(lottery_info['user_tickets'])
                await NotificationSystem.notify_lottery_winner(winner_id, prize, lottery_info['user_tickets'].get(winner_id, 0))
                
                embed = discord.Embed(
                    title="🎰 DAILY LOTTERY DRAW - 7 PM HKT 🎰",
                    description=f"🎉 **LAST LOTTERY WINNER!** 🎉\n\n<@{winner_id}> won **{prize:,}** points!\n\n✨ **NEXT LOTTERY STARTS NOW!** ✨\n🎫 Buy your tickets with `.lottery [amount]`",
                    color=0xFFD700,
                    timestamp=datetime.datetime.utcnow()
                )
                embed.add_field(name="🏆 Last Winner", value=f"<@{winner_id}>", inline=True)
                embed.add_field(name="💰 Prize Won", value=f"**{prize:,}** points 💎", inline=True)
                embed.add_field(name="👥 Participants", value=f"**{total_participants}** players", inline=True)
                embed.add_field(name="🎫 Total Tickets", value=f"**{lottery_info['total_tickets']}** tickets sold", inline=True)
                embed.add_field(name="🎟 Prize Pool Source", value="💸 **Player wagers** (Casino takes 0%)", inline=True)
                embed.add_field(name="⏰ Next Draw", value="**Tomorrow at 7 PM HKT** (11:00 UTC)", inline=True)
                embed.set_footer(text="🎊 Prize automatically sent to winner! Good luck tomorrow! 🎊")
                await lottery_channel.send(content="@everyone", embed=embed)
            else:
                # No winner - send message anyway with @everyone ping
                embed = discord.Embed(
                    title="🎰 DAILY LOTTERY DRAW - 7 PM HKT 🎰",
                    description=f"😢 **NO WINNER TODAY!** 😢\n\n💔 Nobody bought any tickets for yesterday's lottery!\n\n✨ **NEXT LOTTERY STARTS NOW!** ✨\n🎫 Buy your tickets with `.lottery [amount]`",
                    color=0x95a5a6,
                    timestamp=datetime.datetime.utcnow()
                )
                embed.add_field(name="🎟 Prize Pool", value="**0** points", inline=True)
                embed.add_field(name="🎫 Tickets Sold", value="**0** tickets", inline=True)
                embed.add_field(name="👥 Participants", value="**0** players", inline=True)
                embed.add_field(name="💸 Prize Source", value="Player wagers (Casino takes 0%)", inline=True)
                embed.add_field(name="⏰ Next Draw", value="**Tomorrow at 7 PM HKT** (11:00 UTC)", inline=True)
                embed.set_footer(text="💡 Be the first to buy tickets and increase your winning chances!")
                await lottery_channel.send(content="@everyone", embed=embed)

# ========== EVENTS ==========
@bot.event
async def on_ready():
    # Initialize PostgreSQL database
    global db, play_limiter
    print('🔄 Initializing PostgreSQL database...')
    db = Database()
    await db.initialize()
    play_limiter = DailyPlayLimiter(db)
    print('✅ PostgreSQL database initialized!')
    
    # Auto-backup on startup if database has data
    try:
        async with aiosqlite.connect(db.db_path) as conn:
            async with conn.execute('SELECT COUNT(*) FROM users') as cursor:
                row = await cursor.fetchone()
                user_count = row[0] if row else 0
        
        if user_count > 0:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'backups/auto_backup_{timestamp}.json'
            
            backup_data = {
                'backup_timestamp': timestamp,
                'backup_date': datetime.datetime.now().isoformat(),
                'backup_type': 'automatic_startup',
                'users': [],
                'daily_claims': [],
                'monthly_claims': [],
                'rakeback': [],
                'user_stats': [],
                'achievements': [],
                'user_boosts': [],
                'lottery_tickets': [],
                'language_preferences': [],
                'private_profiles': [],
                'custom_play_limits': [],
                'extra_plays_purchased': [],
                'blacklist': []
            }
            
            async with aiosqlite.connect(db.db_path) as conn:
                for table in ['users', 'daily_claims', 'monthly_claims', 'rakeback', 'user_stats',
                             'achievements', 'user_boosts', 'lottery_tickets', 'language_preferences',
                             'private_profiles', 'custom_play_limits', 'extra_plays_purchased', 'blacklist']:
                    try:
                        async with conn.execute(f'SELECT * FROM {table}') as cursor:
                            columns = [description[0] for description in cursor.description]
                            async for row in cursor:
                                backup_data[table].append(dict(zip(columns, row)))
                    except:
                        pass
            
            with open(backup_filename, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            print(f'💾 Auto-backup created: {backup_filename} ({user_count} users)')
    except Exception as e:
        print(f'⚠️  Auto-backup failed: {e}')
    
    print(f'🎰 Casino Bot ONLINE! {bot.user.name}')
    print(f'💰 1 point = €{POINT_TO_EUR:.2f}')
    print(f'🏆 Rank system active with {len(RANK_SYSTEM)} levels')
    print(f'⭐ VIP multiplier: {VIP_MULTIPLIER}x')
    print(f'🚀 Boost system: {len(BOOSTS)} boosts available')
    print(f'🎫 Lottery system active (draws at {LOTTERY_DRAW_TIME} UTC / 7 PM HKT)')
    print('🛡  Anti-cheat system enabled!')
    print('⏰ Command cooldown system active! (10 seconds per command)')
    print('💾 PostgreSQL backups handled by Replit!')
    print('🔔 Notification system active!')
    print('🔧 All systems active!')
    print(f'👑 Admin role configured: {BOT_ADMIN_ROLE_IDS}')
    if BOT_ADMIN_USER_IDS:
        print(f'✅ Admin users: {BOT_ADMIN_USER_IDS}')
    if LINK_ALLOWED_ROLE_IDS:
        print(f'🔗 Link-allowed roles: {LINK_ALLOWED_ROLE_IDS}')
    if LINK_ALLOWED_USER_IDS:
        print(f'🔗 Link-allowed users: {LINK_ALLOWED_USER_IDS}')
    
    # Leave unauthorized servers
    if ALLOWED_GUILD_IDS:
        for guild in bot.guilds:
            if guild.id not in ALLOWED_GUILD_IDS:
                await guild.leave()
                print(f"❌ Left unauthorized server: {guild.name} (ID: {guild.id})")
        print(f'🔒 Server whitelist active! Allowed servers: {ALLOWED_GUILD_IDS}')
    elif not BOT_INVITE_ALLOWED:
        print('🔒 Bot invites disabled - will reject all new server invites')
    
    bot.loop.create_task(background_tasks())

@bot.event
async def on_message(message):
    if message.author.bot: return
    # Wait for database to be initialized
    if db is None: return
    if await db.is_blacklisted(message.author.id): return
    
    # Check if user is admin or has link permissions
    is_admin = False
    can_send_links = False
    
    # Check if user ID is in admin list
    if message.author.id in BOT_ADMIN_USER_IDS:
        is_admin = True
        can_send_links = True
    # Check if user has admin role
    elif message.guild:
        member_roles = [role.id for role in message.author.roles]
        if any(role_id in BOT_ADMIN_ROLE_IDS for role_id in member_roles):
            is_admin = True
            can_send_links = True
        # Check if user has link permission (role or user ID)
        elif any(role_id in LINK_ALLOWED_ROLE_IDS for role_id in member_roles) or message.author.id in LINK_ALLOWED_USER_IDS:
            can_send_links = True
    
    # Insult detection and witty comebacks (skip if message is a command)
    if bot.user and bot.user.mentioned_in(message) and not message.content.startswith('.'):
        insults = ['stupid', 'dumb', 'idiot', 'noob', 'trash', 'garbage', 'suck', 'bad', 'worst', 
                   'useless', 'terrible', 'awful', 'lame', 'boring', 'loser', 'weak', 'pathetic',
                   'bitch', 'shit', 'fuck', 'ass', 'damn', 'crap', 'hell', 'dumbass', 'moron', 
                   'fool', 'worthless', 'retard', 'bastard']
        
        message_lower = message.content.lower()
        if any(insult in message_lower for insult in insults):
            comebacks = [
                f"🎰 {message.author.mention} At least I don't lose my points as fast as you! 😏",
                f"🤖 {message.author.mention} That's cute coming from someone who just lost to my Tic Tac Toe AI! 🎯",
                f"💎 {message.author.mention} Says the one with negative win rate... How's that going for you? 📉",
                f"🎲 {message.author.mention} I may be a bot, but at least I don't rage quit when I lose! 😎",
                f"🚢 {message.author.mention} My Naval War AI just sank your chances of hurting my feelings! 💥",
                f"⭕ {message.author.mention} You couldn't even beat me at Tic Tac Toe, try harder! 🏆",
                f"🎰 {message.author.mention} Bold words from someone who needs '.help' to play! 📚",
                f"💰 {message.author.mention} I'd roast you back, but you're already broke enough! 🔥",
                f"🤖 {message.author.mention} Error 404: Your wins not found! Try `.help` for tips! 😂",
                f"🎯 {message.author.mention} I'm programmed for perfection. You're... well, you tried! 💅"
            ]
            await message.channel.send(random.choice(comebacks))
        else:
            # Intelligent customer support - detect what they're asking about
            msg_lower = message.content.lower()
            
            # Help/Commands questions
            if any(word in msg_lower for word in ['help', 'command', 'how', 'what can', 'do you', 'guide']):
                response = f"🎰 **Welcome {message.author.mention}!** Here's what I can help you with:\n\n" \
                          f"📚 **Commands:** Type `.help` to see all available games and commands\n" \
                          f"🎮 **Popular Games:** `.slots`, `.dice`, `.blackjack`, `.roulette`, `.crash`\n" \
                          f"💰 **Balance:** `.bal` to check your points\n" \
                          f"🏆 **Leaderboard:** `.top` to see top players\n" \
                          f"⭐ **VIP:** `.vip` for VIP benefits info\n" \
                          f"🎁 **Daily Rewards:** `.daily` and `.monthly` for free points\n\n" \
                          f"Need specific help? Just ask me!"
                await message.channel.send(response)
            
            # Game-specific questions
            elif any(word in msg_lower for word in ['game', 'play', 'bet', 'gamble', 'casino']):
                response = f"🎮 **Games Available:**\n\n" \
                          f"🎰 **Slots** - `.slots <amount>` - Classic slot machine (21% win rate!)\n" \
                          f"🎲 **Dice** - `.dice <amount> <number>` - Guess the dice roll (1-6)\n" \
                          f"🃏 **Blackjack** - `.blackjack <amount>` - Beat the dealer!\n" \
                          f"🎯 **Roulette** - `.roulette <amount> <bet>` - Spin to win!\n" \
                          f"💥 **Crash** - `.crash <amount>` - Cash out before it crashes\n" \
                          f"💎 **Mines** - `.mines <amount>` - Avoid the mines\n" \
                          f"🏗 **Towers** - `.towers <amount>` - Climb to the top\n\n" \
                          f"Type `.help` for the full list of 90+ games!"
                await message.channel.send(response)
            
            # Balance/Points questions
            elif any(word in msg_lower for word in ['balance', 'point', 'money', 'coin', 'cash', 'broke']):
                response = f"💰 **About Points & Balance:**\n\n" \
                          f"💵 **Check Balance:** `.bal` or `.balance`\n" \
                          f"🎁 **Free Points:** `.daily` (1 point/day) and `.monthly` (40 points/month)\n" \
                          f"📊 **Your Stats:** `.stats` to see your game history\n" \
                          f"🏆 **Leaderboard:** `.top` to compare with others\n" \
                          f"💸 **Earn More:** Play games and win big!\n\n" \
                          f"💡 Start with small bets and work your way up!"
                await message.channel.send(response)
            
            # VIP questions
            elif any(word in msg_lower for word in ['vip', 'premium', 'upgrade', 'boost', 'bonus']):
                response = f"⭐ **VIP & Bonuses:**\n\n" \
                          f"👑 **VIP Status:** Get 1.15x multiplier on all wins!\n" \
                          f"🚀 **Boosts:** Temporary multipliers for extra winnings\n" \
                          f"🎫 **More Info:** Type `.vip` for full VIP benefits\n" \
                          f"📈 **Check Boosts:** `.boosts` to see active bonuses\n\n" \
                          f"VIP players also get higher daily play limits!"
                await message.channel.send(response)
            
            # Win rate / odds questions
            elif any(word in msg_lower for word in ['win', 'chance', 'odds', 'probability', 'rate', 'lose', 'losing']):
                response = f"📊 **Game Win Rates:**\n\n" \
                          f"🎰 **Slots:** ~22% win rate (recently improved!)\n" \
                          f"🎲 **Dice:** 16.7% win rate (1 in 6 chance)\n" \
                          f"🃏 **Blackjack:** ~42-48% (strategy dependent)\n" \
                          f"🎯 **Roulette:** Varies by bet type\n\n" \
                          f"💡 **Tips:**\n" \
                          f"• Start with small bets\n" \
                          f"• VIP gives 1.15x bonus on wins\n" \
                          f"• Each game has different odds\n\n" \
                          f"🎰 Games are balanced for fun - good luck!"
                await message.channel.send(response)
            
            # Rules / how to play
            elif any(word in msg_lower for word in ['rule', 'how to', 'learn', 'tutorial', 'start', 'begin']):
                response = f"📖 **Getting Started:**\n\n" \
                          f"**Step 1:** Check your balance - `.bal`\n" \
                          f"**Step 2:** Try an easy game - `.slots 10`\n" \
                          f"**Step 3:** See all games - `.help`\n" \
                          f"**Step 4:** Collect daily rewards - `.daily`\n\n" \
                          f"**How to bet:**\n" \
                          f"• `.slots 100` = bet 100 points\n" \
                          f"• `.slots half` = bet half your balance\n" \
                          f"• `.slots all` = bet everything (risky!)\n\n" \
                          f"💡 Each command shows you how to use it!"
                await message.channel.send(response)
            
            # Support / problem questions
            elif any(word in msg_lower for word in ['support', 'problem', 'issue', 'bug', 'error', 'not working', 'broken']):
                response = f"🛠 **Need Support?**\n\n" \
                          f"**Common Issues:**\n" \
                          f"❌ \"Insufficient balance\" - Use `.bal` to check points, then `.daily` for free points\n" \
                          f"❌ \"Daily limit reached\" - Each game has play limits, VIP gets more!\n" \
                          f"❌ \"Command not found\" - Check spelling, use `.help` for valid commands\n\n" \
                          f"**Still stuck?**\n" \
                          f"• Check `.help` for command list\n" \
                          f"• Use `.stats` to see your account status\n" \
                          f"• Contact server admins for technical issues\n\n" \
                          f"I'm here to help! Ask me anything specific!"
                await message.channel.send(response)
            
            # Leaderboard / ranking questions
            elif any(word in msg_lower for word in ['leader', 'rank', 'top', 'best', 'score']):
                response = f"🏆 **Rankings & Leaderboards:**\n\n" \
                          f"📊 **View Top Players:** `.top` or `.leaderboard`\n" \
                          f"📈 **Your Stats:** `.stats` to see your performance\n" \
                          f"🎯 **Your Rank:** `.rank` to see your position\n" \
                          f"🏅 **Achievements:** `.achievements` for your badges\n\n" \
                          f"Compete with others and climb to the top!"
                await message.channel.send(response)
            
            # Generic greeting fallback
            else:
                greetings = [
                    f"👋 Hi {message.author.mention}! I'm your casino bot assistant!\n\n" \
                    f"Ask me about:\n• **Games** - \"what games do you have?\"\n• **Commands** - \"how do I play?\"\n" \
                    f"• **Balance** - \"how do I get points?\"\n• **VIP** - \"what is VIP?\"\n\n" \
                    f"Or just type `.help` to get started!",
                    
                    f"🎰 Hey {message.author.mention}! Need help?\n\n" \
                    f"I can help you with:\n✅ Game guides\n✅ Commands\n✅ Balance & rewards\n✅ VIP info\n\n" \
                    f"Just ask me a question or use `.help`!",
                    
                    f"💬 Hello {message.author.mention}!\n\n" \
                    f"I'm here to help you win big! Ask me:\n" \
                    f"• \"How do I play?\"\n• \"What games are available?\"\n• \"How do I earn points?\"\n\n" \
                    f"Type `.help` anytime for the full command list!"
                ]
                await message.channel.send(random.choice(greetings))
    
    # Only check for suspicious content if user cannot send links
    if not can_send_links and Moderation.is_suspicious(message.content):
        try:
            await message.delete()
            warning = await message.channel.send(f"⚠ {message.author.mention} No links/spam!")
            if message.guild and message.guild.me.guild_permissions.moderate_members:
                await message.author.timeout(datetime.timedelta(hours=1), reason="Suspicious content")
                await warning.edit(content=f"⚠ {message.author.mention} No links/spam! Timeout 1h!")
            await asyncio.sleep(10)
            await warning.delete()
        except Exception as e:
            print(f"Moderation error: {e}")
    
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, commands.CheckFailure):
        pass
    else:
        print(f"Command error: {error}")

@bot.event
async def on_guild_join(guild):
    # Check if server is in whitelist
    if ALLOWED_GUILD_IDS and guild.id not in ALLOWED_GUILD_IDS:
        await guild.leave()
        print(f"❌ Left {guild.name} (ID: {guild.id}) - Not in whitelist")
    elif not BOT_INVITE_ALLOWED and not ALLOWED_GUILD_IDS:
        await guild.leave()
        print(f"❌ Left {guild.name} (ID: {guild.id}) - No invites allowed")

# ========== INTERACTIVE GAME COMMANDS ==========
@require_guild()
@bot.command()
@cooldown_check()
async def mines(ctx, amount: str, mines: int = 3):
    user_id = ctx.author.id
    
    # Check daily play limit
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'mines')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **mines** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if mines < 3 or mines > 24:
        await ctx.send("❌ Mines must be between 3 and 24!")
        return
    
    min_bet = 1
    if mines >= 15 and mines <= 23: min_bet = 10
    elif mines == 24: min_bet = 100
    
    if amount < min_bet:
        await ctx.send(f"❌ Minimum bet for {mines} mines is {min_bet} points!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    suspicious = await anti_cheat.detect_suspicious_activity(user_id)
    if suspicious:
        await anti_cheat.check_and_ban_cheater(ctx, user_id, f"Suspicious activity: {suspicious}")
        return
    
    await db.update_balance(user_id, -amount, f"Mines bet: {mines} mines")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_mines")
    
    # Create mines game
    game = MinesGame(user_id, amount, mines)
    active_mines_games[user_id] = game
    
    # Create buttons for the grid
    class MinesButton(discord.ui.Button):
        def __init__(self, row, col):
            super().__init__(style=discord.ButtonStyle.secondary, label='❓', row=row)
            self.row = row
            self.col = col
        
        async def callback(self, interaction):
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            game = active_mines_games.get(user_id)
            if not game:
                await interaction.response.send_message("❌ Game not found!", ephemeral=True)
                return
            
            # Defer interaction to prevent timeout
            await safe_defer(interaction)
            
            # Check if game is already over (clean up stale game)
            if game.game_over:
                if user_id in active_mines_games:
                    del active_mines_games[user_id]
                return  # Silently ignore - game already ended
            
            result = game.reveal_cell(self.row, self.col)
            
            if result is None:
                # Cell already revealed - silently ignore
                return
            
            # Update this button's appearance based on result
            current_view = getattr(game, 'view', None)
            if current_view:
                for item in current_view.children:
                    if isinstance(item, MinesButton) and item.row == self.row and item.col == self.col:
                        if result == 'mine':
                            item.label = '💣'
                            item.style = discord.ButtonStyle.danger
                        else:
                            item.label = '💎'
                            item.style = discord.ButtonStyle.success
                        item.disabled = True
                        break
            
            if result == 'mine':
                # Game over - mine hit - reveal all mines on buttons
                if current_view:
                    for item in current_view.children:
                        if isinstance(item, MinesButton):
                            if game.grid[item.row][item.col] == '💥':
                                if not item.disabled:  # Unrevealed mine
                                    item.label = '💣'
                                    item.style = discord.ButtonStyle.secondary
                            item.disabled = True
                
                loss_message = get_loss_message()
                embed = discord.Embed(title="💥 Mines Game - LOST!", description=f"You hit a mine!\n\n{loss_message}", color=0xff0000)
                embed.add_field(name="💰 Bet", value=f"**${amount:,}** points", inline=True)
                embed.add_field(name="💎 Diamonds Found", value=f"**{game.diamonds_found}**", inline=True)
                embed.add_field(name="💥 Result", value="**LOST**", inline=True)
                embed.set_footer(text="💣 = Mines | 💎 = Diamonds you found")
                
                await db.update_user_stats(user_id, won=False)
                await safe_interaction_response(interaction, embed=embed, view=current_view)
                
                # Delete game AFTER successful response
                if user_id in active_mines_games:
                    del active_mines_games[user_id]
                
            elif result == 'diamond':
                if game.game_over:
                    # Game won - all diamonds found
                    final_multiplier = game.get_current_multiplier()
                    if is_vip: final_multiplier *= VIP_MULTIPLIER
                    final_multiplier *= boost_multiplier
                    win_amount = int(amount * final_multiplier)
                    
                    await db.update_balance(user_id, win_amount, f"Mines win: x{final_multiplier:.2f}")
                    await db.record_win(user_id, "MINES", amount, win_amount, final_multiplier)
                    await db.update_user_stats(user_id, won=True)
                    await db.record_activity(user_id, f"win_mines_{win_amount}")
                    
                    embed = discord.Embed(title="💎 Mines Game - WON!", description="You found all diamonds!", color=0x00ff00)
                    embed.add_field(name="💰 Bet", value=f"**${amount:,}** points", inline=True)
                    embed.add_field(name="✨ Multiplier", value=f"**x{final_multiplier:.2f}**", inline=True)
                    embed.add_field(name="🏆 You Won", value=f"**${win_amount:,}** points! 🎉", inline=True)
                    embed.add_field(name="💎 Diamonds", value=f"**{game.diamonds_found}/{game.diamonds_count}**", inline=True)
                    
                    bonus_text = []
                    if is_vip: bonus_text.append(f"VIP ({VIP_MULTIPLIER}x)")
                    if boost_multiplier > 1.0: bonus_text.append(f"Boost ({boost_multiplier}x)")
                    if bonus_text: embed.add_field(name="⭐ Active Bonuses", value=", ".join(bonus_text), inline=True)
                    
                    # Disable all buttons when game ends
                    if current_view:
                        for item in current_view.children:
                            item.disabled = True
                    
                    await safe_interaction_response(interaction, embed=embed, view=current_view)
                    
                    # Log ALL wins to WIN_LOG_CHANNEL
                    await WinLogger.log_win(ctx.author, "MINES", amount, win_amount, final_multiplier, 
                                           details=f"Diamonds found: {game.diamonds_found}/{game.diamonds_count}")
                    
                    await RankManager.check_rank_up(ctx, user_id)
                    
                    # Delete game AFTER successful response
                    if user_id in active_mines_games:
                        del active_mines_games[user_id]
                    
                else:
                    # Continue game - calculate current multiplier
                    current_multiplier = game.get_current_multiplier()
                    current_win = int(amount * current_multiplier)
                    
                    embed = discord.Embed(title="💎 Mines Game", description=f"Found a diamond! Continue playing...", color=0x00ff00)
                    embed.add_field(name="💎 Diamonds", value=f"**{game.diamonds_found}** / **{game.diamonds_count}**", inline=True)
                    embed.add_field(name="✨ Multiplier", value=f"**x{current_multiplier:.2f}**", inline=True)
                    embed.add_field(name="💰 Current Win", value=f"**${current_win:,}** points", inline=True)
                    
                    await safe_interaction_response(interaction, embed=embed, view=current_view)
    
    # Create grid view (4x5 + 4 on last row = 24 buttons, leaving room for cash out)
    view = discord.ui.View(timeout=300)
    for i in range(5):
        if i == 4:
            # Last row: only add 4 buttons to make room for cash out
            for j in range(4):
                view.add_item(MinesButton(i, j))
        else:
            # Other rows: add all 5 buttons
            for j in range(5):
                view.add_item(MinesButton(i, j))
    
    # Add cash out button (25th button)
    class CashOutButton(discord.ui.Button):
        def __init__(self):
            super().__init__(style=discord.ButtonStyle.success, label='💰 Cash Out', row=4)
        
        async def callback(self, interaction):
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            game = active_mines_games.get(user_id)
            if not game:
                await interaction.response.send_message("❌ Game not found!", ephemeral=True)
                return
            
            if game.diamonds_found == 0:
                await interaction.response.send_message("❌ You need to find at least one diamond to cash out!", ephemeral=True)
                return
            
            # Defer interaction to prevent timeout
            await safe_defer(interaction)
            
            final_multiplier = game.get_current_multiplier()
            
            # REBALANCED: Cash-out tax after 6+ diamonds to prevent early-game exploitation
            cashout_tax = 0.0
            if game.diamonds_found >= 6:
                cashout_tax = 0.05  # 5% tax
                final_multiplier *= (1 - cashout_tax)
            
            if is_vip: final_multiplier *= VIP_MULTIPLIER
            final_multiplier *= boost_multiplier
            win_amount = int(amount * final_multiplier)
            
            await db.update_balance(user_id, win_amount, f"Mines cashout: x{final_multiplier:.2f}")
            await db.record_win(user_id, "MINES", amount, win_amount, final_multiplier)
            await db.update_user_stats(user_id, won=True)
            await db.record_activity(user_id, f"win_mines_{win_amount}")
            
            display_grid = game.get_display_grid()
            grid_text = '\n'.join([''.join(row) for row in display_grid])
            
            embed = discord.Embed(title="💰 Mines Game - CASHED OUT!", description="You cashed out successfully!", color=0x00ff00)
            embed.add_field(name="Grid", value=grid_text, inline=False)
            embed.add_field(name="Bet", value=f"**{amount}** points", inline=True)
            embed.add_field(name="Multiplier", value=f"**x{final_multiplier:.2f}**", inline=True)
            embed.add_field(name="You Won", value=f"**{win_amount}** points! 🎉", inline=True)
            embed.add_field(name="Diamonds Found", value=f"**{game.diamonds_found}**", inline=True)
            
            # Show cash-out tax if applied
            if cashout_tax > 0:
                embed.add_field(name="⚠ Cash-Out Tax", value=f"{int(cashout_tax * 100)}% (6+ diamonds)", inline=True)
            
            bonus_text = []
            if is_vip: bonus_text.append(f"VIP ({VIP_MULTIPLIER}x)")
            if boost_multiplier > 1.0: bonus_text.append(f"Boost ({boost_multiplier}x)")
            if bonus_text: embed.add_field(name="⭐ Active Bonuses", value=", ".join(bonus_text), inline=True)
            
            # Disable all buttons when cashing out
            current_view = getattr(game, 'view', None)
            if current_view:
                for item in current_view.children:
                    item.disabled = True
            
            await safe_interaction_response(interaction, embed=embed, view=current_view)
            
            # Log ALL wins to WIN_LOG_CHANNEL
            await WinLogger.log_win(ctx.author, "MINES (Cashout)", amount, win_amount, final_multiplier,
                                   details=f"Diamonds found: {game.diamonds_found}/{game.diamonds_count}")
            
            await RankManager.check_rank_up(ctx, user_id)
            
            # Delete game AFTER successful cashout
            if user_id in active_mines_games:
                del active_mines_games[user_id]
    
    view.add_item(CashOutButton())
    
    # Save view in game for button updates
    game.view = view
    
    # Initial game embed
    display_grid = game.get_display_grid()
    grid_text = '\n'.join([''.join(row) for row in display_grid])
    
    embed = discord.Embed(title="💎 Mines Game Started!", description="Click on cells to find diamonds. Avoid mines!", color=0x00ff00)
    embed.add_field(name="Grid", value=grid_text, inline=False)
    embed.add_field(name="Bet", value=f"**{amount}** points", inline=True)
    embed.add_field(name="Mines", value=f"**{mines}**", inline=True)
    embed.add_field(name="Diamonds", value=f"**{game.diamonds_count}**", inline=True)
    
    await ctx.send(embed=embed, view=view)
    
    # Show remaining plays
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

@require_guild()
@bot.command()
@cooldown_check()
async def tower(ctx, amount: str, difficulty: str = 'easy'):
    user_id = ctx.author.id
    
    # Normalize difficulty input
    difficulty = difficulty.lower()
    if difficulty not in TowerGame.DIFFICULTIES:
        return await ctx.send(f"❌ Invalid difficulty! Choose: **easy**, **medium**, **hard**, or **extreme**\n"
                             f"🟢 Easy: 1 mine / 4 buttons (+0.25 per level)\n"
                             f"🟡 Medium: 2 mines / 3 buttons (+0.50 per level)\n"
                             f"🟠 Hard: 2 mines / 4 buttons (+0.40 per level)\n"
                             f"🔴 Extreme: 3 mines / 4 buttons (+0.60 per level)")
    
    # Check daily play limit
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'tower')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **tower** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    suspicious = await anti_cheat.detect_suspicious_activity(user_id)
    if suspicious:
        await anti_cheat.check_and_ban_cheater(ctx, user_id, f"Suspicious activity: {suspicious}")
        return
    
    await db.update_balance(user_id, -amount, f"Tower bet: {difficulty}")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_tower")
    
    # Create tower game
    game = TowerGame(user_id, amount, difficulty)
    active_tower_games[user_id] = game
    
    class TowerPathButton(discord.ui.Button):
        def __init__(self, path_number, button_row):
            super().__init__(style=discord.ButtonStyle.primary, label=str(path_number + 1), row=button_row)
            self.path_number = path_number
        
        async def callback(self, interaction):
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            game = active_tower_games.get(user_id)
            if not game:
                await interaction.response.send_message("❌ Game not found!", ephemeral=True)
                return
            
            # Defer interaction to prevent timeout
            await safe_defer(interaction)
            
            # Check if game is already over (clean up stale game)
            if game.game_over:
                if user_id in active_tower_games:
                    del active_tower_games[user_id]
                return  # Silently ignore - game already ended
            
            success = game.choose_path(self.path_number)
            current_view = getattr(game, 'view', None)
            
            # Update button appearance
            if current_view:
                # Mark the clicked button
                for item in current_view.children:
                    if isinstance(item, TowerPathButton) and item.path_number == self.path_number:
                        if success:
                            item.label = '✅'
                            item.style = discord.ButtonStyle.success
                        else:
                            item.label = '💣'
                            item.style = discord.ButtonStyle.danger
                        item.disabled = True
                        break
            
            if game.game_over:
                if game.won:
                    # Won the game - reached level 10
                    final_multiplier = game.get_current_multiplier()
                    if is_vip: final_multiplier *= VIP_MULTIPLIER
                    final_multiplier *= boost_multiplier
                    win_amount = int(amount * final_multiplier)
                    
                    await db.update_balance(user_id, win_amount, f"Tower win: x{final_multiplier:.2f}")
                    await db.record_win(user_id, "TOWER", amount, win_amount, final_multiplier)
                    await db.update_user_stats(user_id, won=True)
                    await db.record_activity(user_id, f"win_tower_{win_amount}")
                    
                    embed = discord.Embed(title="🏰 Tower - COMPLETED!", description="🎉 You reached the top of the tower!", color=0x00ff00)
                    embed.add_field(name="🎯 Difficulty", value=f"**{game.difficulty_display}**", inline=False)
                    embed.add_field(name="📊 Levels", value=f"**10/10** completed", inline=True)
                    embed.add_field(name="✨ Multiplier", value=f"**x{final_multiplier:.2f}**", inline=True)
                    embed.add_field(name="🏆 You Won", value=f"**${win_amount:,}** points! 💵", inline=True)
                    
                    bonus_text = []
                    if is_vip: bonus_text.append(f"VIP ({VIP_MULTIPLIER}x)")
                    if boost_multiplier > 1.0: bonus_text.append(f"Boost ({boost_multiplier}x)")
                    if bonus_text: embed.add_field(name="⭐ Active Bonuses", value=", ".join(bonus_text), inline=True)
                    
                    # Disable all buttons when game ends
                    if current_view:
                        for item in current_view.children:
                            item.disabled = True
                    
                    await safe_interaction_response(interaction, embed=embed, view=current_view)
                    
                    # Log ALL wins to WIN_LOG_CHANNEL
                    await WinLogger.log_win(ctx.author, "TOWER", amount, win_amount, final_multiplier,
                                           details=f"Difficulty: {difficulty}, Levels: 10/10")
                    
                    await RankManager.check_rank_up(ctx, user_id)
                    
                    # Delete game AFTER successful response
                    if user_id in active_tower_games:
                        del active_tower_games[user_id]
                    
                else:
                    # Lost - reveal all mines on the failed level
                    if current_view:
                        failed_level_data = game.levels[game.current_level - 1]
                        for item in current_view.children:
                            if isinstance(item, TowerPathButton):
                                if item.path_number in failed_level_data['mines'] and not item.disabled:
                                    item.label = '💣'
                                    item.style = discord.ButtonStyle.secondary
                                item.disabled = True
                    
                    await db.update_user_stats(user_id, won=False)
                    loss_message = get_loss_message()
                    embed = discord.Embed(title="💥 YOU FALL!", description=f"You hit a mine and fell from the tower!\n\n{loss_message}", color=0xff0000)
                    embed.add_field(name="🎯 Difficulty", value=f"**{game.difficulty_display}**", inline=False)
                    embed.add_field(name="📊 Level Reached", value=f"**{game.current_level - 1}/10**", inline=True)
                    embed.add_field(name="💸 Lost", value=f"**${amount:,}** points 💥", inline=True)
                    embed.set_footer(text="💣 = Mines on this level")
                    
                    await safe_interaction_response(interaction, embed=embed, view=current_view)
                    
                    # Delete game AFTER successful response
                    if user_id in active_tower_games:
                        del active_tower_games[user_id]
            else:
                # Continue game - show progress and current multiplier
                current_mult = game.get_current_multiplier()
                current_win = int(amount * current_mult)
                
                # Build multiplier ladder display
                multiplier_display = "**Multiplier Ladder:**\n"
                for i in range(10):
                    level_mult = 1.0 + ((i + 1) * game.multiplier_per_level)
                    if i < game.current_level:
                        multiplier_display += f"~~Level {i+1}: x{level_mult:.2f}~~\n"
                    elif i == game.current_level:
                        multiplier_display += f"**➤ Level {i+1}: x{level_mult:.2f}** ⬅\n"
                    else:
                        multiplier_display += f"Level {i+1}: x{level_mult:.2f}\n"
                
                embed = discord.Embed(title="🏰 Tower Game", description=f"Level {game.current_level + 1} - Choose your path!", color=0x00ff00)
                embed.add_field(name="🎯 Difficulty", value=f"**{game.difficulty_display}**", inline=False)
                embed.add_field(name="📊 Progress", value=f"**{game.current_level}/10** levels", inline=True)
                embed.add_field(name="✨ Current Multiplier", value=f"**x{current_mult:.2f}**", inline=True)
                embed.add_field(name="💰 Current Win", value=f"**${current_win:,}** points", inline=True)
                embed.add_field(name="\u200b", value=multiplier_display, inline=False)
                
                await safe_interaction_response(interaction, embed=embed, view=current_view)
    
    # Cash out button
    class CashOutButton(discord.ui.Button):
        def __init__(self):
            super().__init__(style=discord.ButtonStyle.success, label='💰 Cash Out', row=1)
        
        async def callback(self, interaction):
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            game = active_tower_games.get(user_id)
            if not game:
                await interaction.response.send_message("❌ Game not found!", ephemeral=True)
                return
            
            if game.current_level < 1:
                await interaction.response.send_message("❌ You need to complete at least 1 level before cashing out!", ephemeral=True)
                return
            
            # Defer interaction to prevent timeout
            await safe_defer(interaction)
            
            # Calculate payout based on levels completed
            cashout_multiplier = game.get_current_multiplier()
            if is_vip: cashout_multiplier *= VIP_MULTIPLIER
            cashout_multiplier *= boost_multiplier
            win_amount = int(amount * cashout_multiplier)
            
            await db.update_balance(user_id, win_amount, f"Tower cashout: x{cashout_multiplier:.2f}")
            await db.record_win(user_id, "TOWER", amount, win_amount, cashout_multiplier)
            await db.update_user_stats(user_id, won=True)
            await db.record_activity(user_id, f"win_tower_{win_amount}")
            
            embed = discord.Embed(title="💰 Tower - CASHED OUT!", description="You cashed out successfully!", color=0x00ff00)
            embed.add_field(name="🎯 Difficulty", value=f"**{game.difficulty_display}**", inline=False)
            embed.add_field(name="📊 Levels", value=f"**{game.current_level}/10** completed", inline=True)
            embed.add_field(name="✨ Multiplier", value=f"**x{cashout_multiplier:.2f}**", inline=True)
            embed.add_field(name="🏆 You Won", value=f"**${win_amount:,}** points! 💵", inline=True)
            
            bonus_text = []
            if is_vip: bonus_text.append(f"VIP ({VIP_MULTIPLIER}x)")
            if boost_multiplier > 1.0: bonus_text.append(f"Boost ({boost_multiplier}x)")
            if bonus_text: embed.add_field(name="⭐ Active Bonuses", value=", ".join(bonus_text), inline=True)
            
            # Disable all buttons when cashing out
            current_view = getattr(game, 'view', None)
            if current_view:
                for item in current_view.children:
                    item.disabled = True
            
            await safe_interaction_response(interaction, embed=embed, view=current_view)
            
            # Log ALL wins to WIN_LOG_CHANNEL
            await WinLogger.log_win(ctx.author, "TOWER (Cashout)", amount, win_amount, cashout_multiplier,
                                   details=f"Difficulty: {difficulty}, Levels: {game.current_level}/10")
            
            await RankManager.check_rank_up(ctx, user_id)
            
            # Delete game AFTER successful cashout
            if user_id in active_tower_games:
                del active_tower_games[user_id]
    
    # Create initial view with dynamic button count based on difficulty
    view = discord.ui.View(timeout=300)
    for i in range(game.total_buttons):
        view.add_item(TowerPathButton(i, 0))
    view.add_item(CashOutButton())
    
    # Save view in game for button updates
    game.view = view
    
    # Build multiplier ladder display
    multiplier_display = "**Multiplier Ladder:**\n"
    for i in range(10):
        level_mult = 1.0 + ((i + 1) * game.multiplier_per_level)
        if i == 0:
            multiplier_display += f"**➤ Level {i+1}: x{level_mult:.2f}** ⬅ START\n"
        else:
            multiplier_display += f"Level {i+1}: x{level_mult:.2f}\n"
    
    embed = discord.Embed(title="🏰 Tower Game Started!", description="Climb the tower by choosing safe paths!", color=0x00ff00)
    embed.add_field(name="🎯 Difficulty", value=f"**{game.difficulty_display}**", inline=False)
    embed.add_field(name="💰 Bet", value=f"**${amount:,}** points", inline=True)
    embed.add_field(name="📊 Total Levels", value="**10**", inline=True)
    embed.add_field(name="🎁 Max Multiplier", value=f"**x{1.0 + (10 * game.multiplier_per_level):.2f}**", inline=True)
    embed.add_field(name="\u200b", value=multiplier_display, inline=False)
    embed.set_footer(text="Choose a path button to climb! Cash out anytime after level 1.")
    
    await ctx.send(embed=embed, view=view)
    
    # Show remaining plays
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

@require_guild()
@bot.command()
@cooldown_check()
async def blackjack(ctx, amount: str):
    user_id = ctx.author.id
    
    # Check daily play limit
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'blackjack')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **blackjack** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    suspicious = await anti_cheat.detect_suspicious_activity(user_id)
    if suspicious:
        await anti_cheat.check_and_ban_cheater(ctx, user_id, f"Suspicious activity: {suspicious}")
        return
    
    await db.update_balance(user_id, -amount, "Blackjack bet")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_blackjack")
    
    # ADMIN FORCED LOSS CHECK (SILENT - user never knows)
    should_force_loss = await check_forced_loss(user_id)
    
    # Create blackjack game
    game = BlackjackGame(user_id, amount)
    if should_force_loss:
        game.forced_loss = True  # Mark game to force loss
    active_blackjack_games[user_id] = game
    
    class HitButton(discord.ui.Button):
        def __init__(self, parent_view):
            super().__init__(style=discord.ButtonStyle.primary, label='🎯 Hit', row=0)
            self.parent_view = parent_view
        
        async def callback(self, interaction):
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            game = active_blackjack_games.get(user_id)
            if not game:
                await interaction.response.send_message("❌ Game not found!", ephemeral=True)
                return
            
            # Defer interaction to prevent timeout
            await safe_defer(interaction)
            
            if game.hit():
                # Game continues
                player_hand = ', '.join(game.player_hand)
                player_value = game.hand_value(game.player_hand)
                dealer_hand = f"{game.dealer_hand[0]} ❓"
                
                # Generate card image with dealer's second card hidden
                card_image = await generate_blackjack_image(game.player_hand, game.dealer_hand, show_all_dealer=False)
                
                embed = discord.Embed(title="🃏 Blackjack", description="Your turn!", color=0x00ff00)
                embed.add_field(name="Your Hand", value=f"**{player_hand}** (Total: {player_value})", inline=False)
                embed.add_field(name="Dealer Hand", value=f"**{dealer_hand}**", inline=False)
                embed.add_field(name="Status", value="🎯 Choose to Hit or Stand", inline=True)
                
                if card_image:
                    embed.set_image(url="attachment://blackjack.png")
                    file = discord.File(card_image, filename="blackjack.png")
                    await safe_interaction_response(interaction, embed=embed, view=self.parent_view, file=file)
                else:
                    await safe_interaction_response(interaction, embed=embed, view=self.parent_view)
            else:
                # Game over
                await handle_blackjack_result(interaction, game)
    
    class StandButton(discord.ui.Button):
        def __init__(self):
            super().__init__(style=discord.ButtonStyle.success, label='🛑 Stand', row=0)
        
        async def callback(self, interaction):
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            game = active_blackjack_games.get(user_id)
            if not game:
                await interaction.response.send_message("❌ Game not found!", ephemeral=True)
                return
            
            # Defer interaction to prevent timeout
            await safe_defer(interaction)
            
            game.stand()
            await handle_blackjack_result(interaction, game)
    
    async def handle_blackjack_result(interaction, game):
        player_hand = ', '.join(game.player_hand)
        player_value = game.hand_value(game.player_hand)
        dealer_hand = ', '.join(game.dealer_hand)
        dealer_value = game.hand_value(game.dealer_hand)
        
        # Generate card image
        card_image = await generate_blackjack_image(game.player_hand, game.dealer_hand, show_all_dealer=True)
        
        if game.won is None:
            # PUSH - Pareggio, rimborsa la scommessa
            await db.update_balance(user_id, amount, f"Blackjack push - refund")
            
            embed = discord.Embed(title="🃏 Blackjack - PUSH (TIE)", description="È un pareggio! Scommessa rimborsata.", color=0xFFFF00)
            embed.add_field(name="Your Hand", value=f"**{player_hand}** (Total: {player_value})", inline=True)
            embed.add_field(name="Dealer Hand", value=f"**{dealer_hand}** (Total: {dealer_value})", inline=True)
            embed.add_field(name="Result", value=f"**PAREGGIO**", inline=True)
            embed.add_field(name="Refunded", value=f"**{amount}** points", inline=True)
            embed.add_field(name="Balance", value=f"**{await db.get_balance(user_id):,}** points", inline=True)
            
            if card_image:
                embed.set_image(url="attachment://blackjack.png")
                file = discord.File(card_image, filename="blackjack.png")
                await safe_interaction_response(interaction, embed=embed, view=None, file=file)
            else:
                await safe_interaction_response(interaction, embed=embed, view=None)
            del active_blackjack_games[user_id]
            
        elif game.won:
            if game.result == "blackjack":
                win_amount = int(amount * 2.2)  # REDUCED: Blackjack pays 2.2x (was 2.5x)
            else:
                win_amount = int(amount * 1.8)  # REDUCED: Normal win pays 1.8x (was 2.0x)
            
            if is_vip: win_amount = int(win_amount * VIP_MULTIPLIER)
            win_amount = int(win_amount * boost_multiplier)
            
            await db.update_balance(user_id, win_amount, f"Blackjack win: {game.result.upper()}")
            await db.record_win(user_id, "BLACKJACK", amount, win_amount, win_amount/amount)
            await db.update_user_stats(user_id, won=True)
            await db.record_activity(user_id, f"win_blackjack_{win_amount}")
            
            embed = discord.Embed(title="🃏 Blackjack - YOU WON! 🎉", description="━━━━━━━━━━━━━━━━━━━━", color=0xFFD700)
            embed.add_field(name="🎴 Your Hand", value=f"{player_hand}\n**Total: {player_value}**", inline=True)
            embed.add_field(name="🃏 Dealer Hand", value=f"{dealer_hand}\n**Total: {dealer_value}**", inline=True)
            embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value="\u200b", inline=False)
            embed.add_field(name="🏆 Result", value=f"**{game.result.upper()}**", inline=True)
            embed.add_field(name="💰 You Won", value=f"**+${win_amount:,}** points! 💵", inline=True)
            
            bonus_text = []
            if is_vip: bonus_text.append(f"VIP ({VIP_MULTIPLIER}x)")
            if boost_multiplier > 1.0: bonus_text.append(f"Boost ({boost_multiplier}x)")
            if bonus_text: embed.add_field(name="⭐ Active Bonuses", value=", ".join(bonus_text), inline=True)
            
            if card_image:
                embed.set_image(url="attachment://blackjack.png")
                file = discord.File(card_image, filename="blackjack.png")
                await safe_interaction_response(interaction, embed=embed, view=None, file=file)
            else:
                await safe_interaction_response(interaction, embed=embed, view=None)
            del active_blackjack_games[user_id]
            
            # Log ALL wins to WIN_LOG_CHANNEL
            await WinLogger.log_win(ctx.author, "BLACKJACK", amount, win_amount, win_amount/amount,
                                   details=f"Player: {player_value}, Dealer: {dealer_value}, Result: {game.result.upper()}")
            
            await RankManager.check_rank_up(ctx, user_id)
            
        else:
            await db.update_user_stats(user_id, won=False)
            
            embed = discord.Embed(title="🃏 Blackjack - YOU LOST! 💔", description="━━━━━━━━━━━━━━━━━━━━", color=0xFF0000)
            embed.add_field(name="🎴 Your Hand", value=f"{player_hand}\n**Total: {player_value}**", inline=True)
            embed.add_field(name="🃏 Dealer Hand", value=f"{dealer_hand}\n**Total: {dealer_value}**", inline=True)
            embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value="\u200b", inline=False)
            embed.add_field(name="💸 Lost", value=f"**-${amount:,}** points 💥", inline=True)
            embed.add_field(name="📊 Result", value=f"**{game.result.upper()}**", inline=True)
            
            if card_image:
                embed.set_image(url="attachment://blackjack.png")
                file = discord.File(card_image, filename="blackjack.png")
                await safe_interaction_response(interaction, embed=embed, view=None, file=file)
            else:
                await safe_interaction_response(interaction, embed=embed, view=None)
            del active_blackjack_games[user_id]
        
        # Show remaining plays
        await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
    
    # Create initial view
    view = discord.ui.View(timeout=300)
    view.add_item(HitButton(view))
    view.add_item(StandButton())
    
    # Initial game embed
    player_hand = ', '.join(game.player_hand)
    player_value = game.hand_value(game.player_hand)
    dealer_hand = f"{game.dealer_hand[0]} ❓"
    
    # Generate card image with dealer's second card hidden
    card_image = await generate_blackjack_image(game.player_hand, game.dealer_hand, show_all_dealer=False)
    
    embed = discord.Embed(title="🃏 Blackjack Game Started!", description="Get closer to 21 than the dealer without going over!", color=0x00ff00)
    embed.add_field(name="Your Hand", value=f"**{player_hand}** (Total: {player_value})", inline=False)
    embed.add_field(name="Dealer Hand", value=f"**{dealer_hand}**", inline=False)
    embed.add_field(name="Bet", value=f"**{amount}** points", inline=True)
    
    if card_image:
        embed.set_image(url="attachment://blackjack.png")
    
    if game.game_over:
        # Natural blackjack
        await handle_blackjack_result(ctx, game)
    else:
        if card_image:
            file = discord.File(card_image, filename="blackjack.png")
            await ctx.send(embed=embed, view=view, file=file)
        else:
            await ctx.send(embed=embed, view=view)

# ========== MULTIPLAYER GAMES ==========
@require_guild()
@bot.command()
@cooldown_check()
async def ttt(ctx, opponent_or_amount=None, amount: float = None):
    """Tic Tac Toe: .ttt @user amount (PvP) or .ttt amount (vs bot)"""
    user_id = ctx.author.id
    
    # Parse arguments
    if opponent_or_amount is None:
        # .ttt (use default 1.0)
        is_pvp = False
        opponent = None
        opponent_id = bot.user.id
        amount = 1.0
    else:
        # Try to convert to Member first (for PvP)
        try:
            converter = commands.MemberConverter()
            opponent = await converter.convert(ctx, str(opponent_or_amount))
            is_pvp = True
            opponent_id = opponent.id
            if amount is None:
                amount = 1.0
            
            if opponent_id == user_id:
                await ctx.send("❌ You can't play against yourself!")
                return
            
            if opponent.bot and opponent.id != bot.user.id:
                await ctx.send("❌ You can only challenge real players or use .ttt <amount> to play vs bot!")
                return
        except (commands.BadArgument, commands.MemberNotFound):
            # Not a member mention, try as amount (vs bot)
            try:
                amount = float(opponent_or_amount)
                is_pvp = False
                opponent = None
                opponent_id = bot.user.id
            except (ValueError, TypeError):
                await ctx.send("❌ Invalid format! Use: `.ttt @user amount` or `.ttt amount`")
                return
    
    # Validate bet amount
    if amount < 0.01:
        await ctx.send("❌ Minimum bet is 0.01 points!")
        return
    
    if is_pvp:
        # PvP: Use challenge system
        async def start_ttt_pvp(ctx_inner, interaction, player1, player2, amount_inner):
            # Deduct balances from BOTH players
            await db.update_balance(player1.id, -amount_inner, "Tic Tac Toe bet")
            await db.update_balance(player2.id, -amount_inner, "Tic Tac Toe bet")
            await db.add_wager(player1.id, amount_inner)
            await db.add_wager(player2.id, amount_inner)
            
            # Create game
            game = TicTacToeGame(player1.id, player2.id, amount_inner, is_pvp=True)
            session = game_session_manager.create_session(
                GameType.TIC_TAC_TOE, player1.id, player2.id, amount_inner, 
                ctx_inner.channel.id, game, is_pvp=True
            )
            
            # Create UI
            class TTTButton(discord.ui.Button):
                def __init__(self, row, col, game_obj, session_obj):
                    super().__init__(style=discord.ButtonStyle.secondary, label='⬜', row=row)
                    self.row_pos = row
                    self.col_pos = col
                    self.game_obj = game_obj
                    self.session_obj = session_obj
                
                async def callback(self, interaction_inner):
                    game_state = self.session_obj.game_state
                    
                    # Check if it's the player's turn
                    if interaction_inner.user.id != game_state.current_turn:
                        await interaction_inner.response.send_message("❌ It's not your turn!", ephemeral=True)
                        return
                    
                    # Make move
                    if not game_state.make_move(interaction_inner.user.id, self.row_pos, self.col_pos):
                        await interaction_inner.response.send_message("❌ Invalid move!", ephemeral=True)
                        return
                    
                    # Defer interaction to prevent timeout
                    await safe_defer(interaction_inner)
                    
                    # Update button
                    self.label = game_state.board[self.row_pos][self.col_pos]
                    self.style = discord.ButtonStyle.primary if self.label == 'X' else discord.ButtonStyle.danger
                    self.disabled = True
                    
                    # Check game end
                    if game_state.game_over:
                        # Disable all buttons
                        for item in self.view.children:
                            item.disabled = True
                        
                        if game_state.is_draw:
                            # Refund bets
                            await db.update_balance(player1.id, amount_inner, "Tic Tac Toe draw refund")
                            await db.update_balance(player2.id, amount_inner, "Tic Tac Toe draw refund")
                            
                            embed = discord.Embed(title="⚪ Tic Tac Toe - DRAW!", color=0xFFFF00)
                            embed.add_field(name="Result", value="It's a draw! Bets refunded.", inline=False)
                            await safe_interaction_response(interaction_inner, embed=embed, view=self.view)
                        else:
                            winner = game_state.winner
                            loser = player2.id if winner == player1.id else player1.id
                            
                            # Calculate winnings
                            total_pot = amount_inner * 2
                            house_edge = total_pot * 0.01
                            winner_amount = total_pot - house_edge
                            
                            await db.update_balance(winner, winner_amount, "Tic Tac Toe win")
                            await db.record_win(winner, "TIC_TAC_TOE", amount_inner, winner_amount, winner_amount/amount_inner)
                            await db.update_user_stats(winner, won=True)
                            await db.update_user_stats(loser, won=False)
                            
                            winner_user = await bot.fetch_user(winner)
                            embed = discord.Embed(title="🏆 Tic Tac Toe - GAME OVER!", color=0x00FF00)
                            embed.add_field(name="Winner", value=winner_user.mention, inline=True)
                            embed.add_field(name="Prize", value=f"**{winner_amount:.2f}** points", inline=True)
                            embed.add_field(name="Mode", value="Player vs Player (1% house edge)", inline=False)
                            
                            await safe_interaction_response(interaction_inner, embed=embed, view=self.view)
                            
                            # Log win
                            await WinLogger.log_win(winner_user, "TIC_TAC_TOE", amount_inner, winner_amount, winner_amount/amount_inner)
                            await RankManager.check_rank_up(ctx_inner, winner)
                        
                        # End session
                        game_session_manager.end_session(ctx_inner.channel.id, GameType.TIC_TAC_TOE, player1.id)
                    else:
                        # Update turn display
                        current_player = await bot.fetch_user(game_state.current_turn)
                        embed = discord.Embed(title="⭕ Tic Tac Toe", color=0x00AAFF)
                        embed.add_field(name="Current Turn", value=current_player.mention, inline=True)
                        embed.add_field(name="Bet", value=f"**{amount_inner:.2f}** points each", inline=True)
                        embed.add_field(name="Mode", value="PvP", inline=True)
                        
                        await safe_interaction_response(interaction_inner, embed=embed, view=self.view)
            
            # Create view
            view = discord.ui.View(timeout=300)
            for i in range(3):
                for j in range(3):
                    view.add_item(TTTButton(i, j, game, session))
            
            # Send initial message
            embed = discord.Embed(title="⭕ Tic Tac Toe - Game Started!", color=0x00AAFF)
            embed.add_field(name="Players", value=f"❌ {player1.mention} vs ⭕ {player2.mention}", inline=False)
            embed.add_field(name="Bet", value=f"**{amount_inner:.2f}** points each", inline=True)
            embed.add_field(name="Prize Pool", value=f"**{amount_inner*2:.2f}** points (1% house edge)", inline=True)
            embed.add_field(name="Current Turn", value=f"❌ {player1.mention}", inline=False)
            embed.set_footer(text="Click a square to make your move!")
            
            await ctx_inner.send(embed=embed, view=view)
        
        # Use challenge system for PvP
        await initiate_multiplayer_challenge(ctx, ctx.author, opponent, "Tic Tac Toe", amount, start_ttt_pvp)
        return
    
    # vs Bot: Keep existing logic
    # Check balance
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    # Check if user already in a game
    if game_session_manager.is_user_in_game(user_id):
        await ctx.send("❌ You're already in a game! Finish it first.")
        return
    
    # Check blacklist
    if await db.is_blacklisted(user_id):
        await ctx.send("❌ You are banned from using the bot!")
        return
    
    # Deduct bet
    await db.update_balance(user_id, -amount, "Tic Tac Toe bet")
    await db.add_wager(user_id, amount)
    
    # Create game
    game = TicTacToeGame(user_id, opponent_id, amount, is_pvp=False)
    session = game_session_manager.create_session(
        GameType.TIC_TAC_TOE, user_id, opponent_id, amount, 
        ctx.channel.id, game, is_pvp=False
    )
    
    # Create UI
    class TTTButton(discord.ui.Button):
        def __init__(self, row, col, game_obj, session_obj):
            super().__init__(style=discord.ButtonStyle.secondary, label='⬜', row=row)
            self.row_pos = row
            self.col_pos = col
            self.game_obj = game_obj
            self.session_obj = session_obj
        
        async def callback(self, interaction):
            game = self.session_obj.game_state
            
            # Check if it's the player's turn
            if interaction.user.id != game.current_turn:
                await interaction.response.send_message("❌ It's not your turn!", ephemeral=True)
                return
            
            # Make move
            if not game.make_move(interaction.user.id, self.row_pos, self.col_pos):
                await interaction.response.send_message("❌ Invalid move!", ephemeral=True)
                return
            
            # Defer interaction to prevent timeout
            await safe_defer(interaction)
            
            # Update button
            self.label = game.board[self.row_pos][self.col_pos]
            self.style = discord.ButtonStyle.primary if self.label == 'X' else discord.ButtonStyle.danger
            self.disabled = True
            
            # Check game end
            if game.game_over:
                # Disable all buttons
                for item in self.view.children:
                    item.disabled = True
                
                if game.is_draw:
                    # Refund bet
                    await db.update_balance(user_id, amount, "Tic Tac Toe draw refund")
                    embed = discord.Embed(title="⚪ Tic Tac Toe - DRAW!", color=0xFFFF00)
                    embed.add_field(name="Result", value="It's a draw! Bet refunded.", inline=False)
                    await safe_interaction_response(interaction, embed=embed, view=self.view)
                else:
                    # vs Bot: Player wins
                    if game.winner == user_id:
                        winner_amount = amount
                        await db.update_balance(user_id, winner_amount, "Tic Tac Toe win")
                        await db.record_win(user_id, "TIC_TAC_TOE", amount, winner_amount, 1.0)
                        await db.update_user_stats(user_id, won=True)
                        
                        embed = discord.Embed(title="🏆 Tic Tac Toe - YOU WON!", color=0x00FF00)
                        embed.add_field(name="Prize", value=f"**{winner_amount:.2f}** points", inline=True)
                        embed.add_field(name="Mode", value="Player vs Bot", inline=False)
                        
                        await safe_interaction_response(interaction, embed=embed, view=self.view)
                        await WinLogger.log_win(ctx.author, "TIC_TAC_TOE", amount, winner_amount, 1.0)
                        await RankManager.check_rank_up(ctx, user_id)
                
                # End session
                game_session_manager.end_session(ctx.channel.id, GameType.TIC_TAC_TOE, user_id)
            else:
                # Bot's turn
                if game.current_turn == bot.user.id:
                    bot_move = game.get_bot_move()
                    if bot_move:
                        game.make_move(bot.user.id, bot_move[0], bot_move[1])
                        
                        # Update bot's button
                        for item in self.view.children:
                            if isinstance(item, TTTButton) and item.row_pos == bot_move[0] and item.col_pos == bot_move[1]:
                                item.label = game.board[bot_move[0]][bot_move[1]]
                                item.style = discord.ButtonStyle.danger
                                item.disabled = True
                        
                        # Check if bot won
                        if game.game_over:
                            for item in self.view.children:
                                item.disabled = True
                            
                            if game.is_draw:
                                await db.update_balance(user_id, amount, "Tic Tac Toe draw refund")
                                embed = discord.Embed(title="⚪ Tic Tac Toe - DRAW!", color=0xFFFF00)
                                embed.add_field(name="Result", value="It's a draw! Bet refunded.", inline=False)
                            else:
                                await db.update_user_stats(user_id, won=False)
                                embed = discord.Embed(title="❌ Tic Tac Toe - YOU LOST!", color=0xFF0000)
                                embed.add_field(name="Result", value=f"Bot wins! You lost **{amount:.2f}** points", inline=False)
                            
                            await safe_interaction_response(interaction, embed=embed, view=self.view)
                            game_session_manager.end_session(ctx.channel.id, GameType.TIC_TAC_TOE, user_id)
                            return
                
                # Update turn display
                embed = discord.Embed(title="⭕ Tic Tac Toe", color=0x00AAFF)
                embed.add_field(name="Current Turn", value=ctx.author.mention, inline=True)
                embed.add_field(name="Bet", value=f"**{amount:.2f}** points", inline=True)
                embed.add_field(name="Mode", value="vs Bot", inline=True)
                
                await safe_interaction_response(interaction, embed=embed, view=self.view)
    
    # Create view
    view = discord.ui.View(timeout=300)
    for i in range(3):
        for j in range(3):
            view.add_item(TTTButton(i, j, game, session))
    
    # Send initial message
    embed = discord.Embed(title="⭕ Tic Tac Toe - Game Started!", color=0x00AAFF)
    embed.add_field(name="Players", value=f"❌ {ctx.author.mention} vs ⭕ Bot", inline=False)
    embed.add_field(name="Bet", value=f"**{amount:.2f}** points", inline=True)
    embed.add_field(name="Current Turn", value=f"❌ {ctx.author.mention}", inline=False)
    embed.set_footer(text="Click a square to make your move!")
    
    await ctx.send(embed=embed, view=view)

@require_guild()
@bot.command()
@cooldown_check()
async def navalwar(ctx, opponent_or_amount=None, amount: float = None):
    """Naval War: .navalwar @user amount (PvP) or .navalwar amount (vs bot)"""
    user_id = ctx.author.id
    
    # Parse arguments
    if opponent_or_amount is None:
        # .navalwar (use default 1.0)
        is_pvp = False
        opponent = None
        opponent_id = bot.user.id
        amount = 1.0
    else:
        # Try to convert to Member first (for PvP)
        try:
            converter = commands.MemberConverter()
            opponent = await converter.convert(ctx, str(opponent_or_amount))
            is_pvp = True
            opponent_id = opponent.id
            if amount is None:
                amount = 1.0
            
            if opponent_id == user_id:
                await ctx.send("❌ You can't play against yourself!")
                return
            
            if opponent.bot and opponent.id != bot.user.id:
                await ctx.send("❌ You can only challenge real players or use .navalwar <amount> to play vs bot!")
                return
        except (commands.BadArgument, commands.MemberNotFound):
            # Not a member mention, try as amount (vs bot)
            try:
                amount = float(opponent_or_amount)
                is_pvp = False
                opponent = None
                opponent_id = bot.user.id
            except (ValueError, TypeError):
                await ctx.send("❌ Invalid format! Use: `.navalwar @user amount` or `.navalwar amount`")
                return
    
    if amount < 0.01:
        await ctx.send("❌ Minimum bet is 0.01 points!")
        return
    
    if is_pvp:
        # PvP: Use challenge system
        async def start_navalwar_pvp(ctx_inner, interaction, player1, player2, amount_inner):
            # Deduct balances from BOTH players
            await db.update_balance(player1.id, -amount_inner, "Naval War bet")
            await db.update_balance(player2.id, -amount_inner, "Naval War bet")
            await db.add_wager(player1.id, amount_inner)
            await db.add_wager(player2.id, amount_inner)
            
            # Create game
            game = NavalWarGame(player1.id, player2.id, amount_inner, is_pvp=True)
            
            # Auto-place ships for both players
            game.place_ships_random(player1.id)
            game.place_ships_random(player2.id)
            
            session = game_session_manager.create_session(
                GameType.NAVAL_WAR, player1.id, player2.id, amount_inner,
                ctx_inner.channel.id, game, is_pvp=True
            )
            
            # Create attack UI for PvP
            class AttackButton(discord.ui.Button):
                def __init__(self, row, col, game_obj, session_obj):
                    super().__init__(style=discord.ButtonStyle.secondary, label=f"{chr(65+row)}{col+1}", row=row)
                    self.row_pos = row
                    self.col_pos = col
                    self.game_obj = game_obj
                    self.session_obj = session_obj
                
                async def callback(self, interaction_inner):
                    game_state = self.session_obj.game_state
                    
                    if interaction_inner.user.id != game_state.current_turn:
                        await interaction_inner.response.send_message("❌ It's not your turn!", ephemeral=True)
                        return
                    
                    result = game_state.make_attack(interaction_inner.user.id, self.row_pos, self.col_pos)
                    
                    if result is None:
                        await interaction_inner.response.send_message("❌ Invalid move! Already attacked there.", ephemeral=True)
                        return
                    
                    # Defer interaction to prevent timeout
                    await safe_defer(interaction_inner)
                    
                    # Update button
                    if result == 'hit':
                        self.label = '💥'
                        self.style = discord.ButtonStyle.danger
                    else:
                        self.label = '💧'
                        self.style = discord.ButtonStyle.primary
                    self.disabled = True
                    
                    # Check game end
                    if game_state.game_over:
                        for item in self.view.children:
                            item.disabled = True
                        
                        winner = game_state.winner
                        loser = player2.id if winner == player1.id else player1.id
                        
                        # Calculate winnings (PvP)
                        total_pot = amount_inner * 2
                        house_edge = total_pot * 0.01
                        winner_amount = total_pot - house_edge
                        
                        await db.update_balance(winner, winner_amount, "Naval War win")
                        await db.record_win(winner, "NAVAL_WAR", amount_inner, winner_amount, winner_amount/amount_inner)
                        await db.update_user_stats(winner, won=True)
                        await db.update_user_stats(loser, won=False)
                        
                        winner_user = await bot.fetch_user(winner)
                        embed = discord.Embed(title="🚢 Naval War - GAME OVER!", color=0x00FF00)
                        embed.add_field(name="Winner", value=winner_user.mention, inline=True)
                        embed.add_field(name="Prize", value=f"**{winner_amount:.2f}** points", inline=True)
                        embed.add_field(name="Mode", value="Player vs Player (1% house edge)", inline=False)
                        
                        await safe_interaction_response(interaction_inner, embed=embed, view=self.view)
                        
                        await WinLogger.log_win(winner_user, "NAVAL_WAR", amount_inner, winner_amount, winner_amount/amount_inner)
                        await RankManager.check_rank_up(ctx_inner, winner)
                        
                        game_session_manager.end_session(ctx_inner.channel.id, GameType.NAVAL_WAR, player1.id)
                    else:
                        # Update display
                        current_player = await bot.fetch_user(game_state.current_turn)
                        embed = discord.Embed(title="🚢 Naval War", color=0x0055AA)
                        
                        # Show player's attack
                        player_coord = f"{chr(65+self.row_pos)}{self.col_pos+1}"
                        embed.add_field(name="Your Attack", value=f"{player_coord}: {'💥 HIT!' if result == 'hit' else '💧 Miss'}", inline=True)
                        embed.add_field(name="Current Turn", value=current_player.mention, inline=True)
                        embed.add_field(name="Bet", value=f"**{amount_inner:.2f}** points each", inline=True)
                        embed.set_footer(text="💥 = Hit | 💧 = Miss | Click to attack!")
                        
                        await safe_interaction_response(interaction_inner, embed=embed, view=self.view)
            
            # Create view
            view = discord.ui.View(timeout=600)
            for i in range(5):
                for j in range(5):
                    view.add_item(AttackButton(i, j, game, session))
            
            # Send initial message
            embed = discord.Embed(title="🚢 Naval War - Game Started!", color=0x0055AA)
            embed.add_field(name="Players", value=f"{player1.mention} vs {player2.mention}", inline=False)
            embed.add_field(name="Bet", value=f"**{amount_inner:.2f}** points each", inline=True)
            embed.add_field(name="Prize Pool", value=f"**{amount_inner*2:.2f}** points (1% house edge)", inline=True)
            embed.add_field(name="Current Turn", value=player1.mention, inline=False)
            embed.add_field(name="Grid", value="A-E (rows) × 1-5 (columns)", inline=True)
            embed.add_field(name="Ships", value="3 ships placed randomly", inline=True)
            embed.set_footer(text="Ships are hidden! Click coordinates to attack. First to sink all enemy ships wins!")
            
            await ctx_inner.send(embed=embed, view=view)
        
        # Use challenge system for PvP
        await initiate_multiplayer_challenge(ctx, ctx.author, opponent, "Naval War", amount, start_navalwar_pvp)
        return
    
    # vs Bot: Keep existing logic
    # Check balance
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    # Check if user already in a game
    if game_session_manager.is_user_in_game(user_id):
        await ctx.send("❌ You're already in a game! Finish it first.")
        return
    
    # Check blacklist
    if await db.is_blacklisted(user_id):
        await ctx.send("❌ You are banned from using the bot!")
        return
    
    # Deduct bet
    await db.update_balance(user_id, -amount, "Naval War bet")
    await db.add_wager(user_id, amount)
    
    # Create game
    game = NavalWarGame(user_id, opponent_id, amount, is_pvp=False)
    
    # Auto-place ships for both players
    game.place_ships_random(user_id)
    game.place_ships_random(opponent_id)
    
    session = game_session_manager.create_session(
        GameType.NAVAL_WAR, user_id, opponent_id, amount,
        ctx.channel.id, game, is_pvp=False
    )
    
    # Create attack UI
    class AttackButton(discord.ui.Button):
        def __init__(self, row, col, game_obj, session_obj):
            super().__init__(style=discord.ButtonStyle.secondary, label=f"{chr(65+row)}{col+1}", row=row)
            self.row_pos = row
            self.col_pos = col
            self.game_obj = game_obj
            self.session_obj = session_obj
        
        async def callback(self, interaction):
            game = self.session_obj.game_state
            
            if interaction.user.id != game.current_turn:
                await interaction.response.send_message("❌ It's not your turn!", ephemeral=True)
                return
            
            result = game.make_attack(interaction.user.id, self.row_pos, self.col_pos)
            
            if result is None:
                await interaction.response.send_message("❌ Invalid move! Already attacked there.", ephemeral=True)
                return
            
            # Defer interaction to prevent timeout
            await safe_defer(interaction)
            
            # Update button
            if result == 'hit':
                self.label = '💥'
                self.style = discord.ButtonStyle.danger
            else:
                self.label = '💧'
                self.style = discord.ButtonStyle.primary
            self.disabled = True
            
            # Check game end
            if game.game_over:
                for item in self.view.children:
                    item.disabled = True
                
                # vs Bot: Player wins (1.2x bet)
                if game.winner == user_id:
                    winner_amount = amount * 1.2
                    await db.update_balance(user_id, winner_amount, "Naval War win")
                    await db.record_win(user_id, "NAVAL_WAR", amount, winner_amount, 1.2)
                    await db.update_user_stats(user_id, won=True)
                    
                    embed = discord.Embed(title="🚢 Naval War - YOU WON!", color=0x00FF00)
                    embed.add_field(name="Prize", value=f"**{winner_amount:.2f}** points", inline=True)
                    
                    await safe_interaction_response(interaction, embed=embed, view=self.view)
                    await WinLogger.log_win(ctx.author, "NAVAL_WAR", amount, winner_amount, 1.2)
                    await RankManager.check_rank_up(ctx, user_id)
                
                game_session_manager.end_session(ctx.channel.id, GameType.NAVAL_WAR, user_id)
            else:
                # Bot's turn
                bot_attack_info = ""
                if game.current_turn == bot.user.id:
                    bot_attack = game.get_bot_attack()
                    if bot_attack:
                        bot_row, bot_col = bot_attack
                        bot_result = game.make_attack(bot.user.id, bot_row, bot_col)
                        
                        # Format bot attack coordinate (e.g., "A3")
                        bot_coord = f"{chr(65+bot_row)}{bot_col+1}"
                        bot_attack_info = f"\n🤖 **Bot attacked {bot_coord}**: {'💥 HIT!' if bot_result == 'hit' else '💧 Miss'}"
                        
                        # Check if bot won
                        if game.game_over:
                            for item in self.view.children:
                                item.disabled = True
                            
                            await db.update_user_stats(user_id, won=False)
                            embed = discord.Embed(title="❌ Naval War - YOU LOST!", color=0xFF0000)
                            embed.add_field(name="Result", value=f"Bot destroyed all your ships! You lost **{amount:.2f}** points", inline=False)
                            embed.add_field(name="Bot's Final Attack", value=f"{bot_coord}: {'💥 HIT!' if bot_result == 'hit' else '💧 Miss'}", inline=True)
                            
                            await safe_interaction_response(interaction, embed=embed, view=self.view)
                            game_session_manager.end_session(ctx.channel.id, GameType.NAVAL_WAR, user_id)
                            return
                
                # Update display
                embed = discord.Embed(title="🚢 Naval War", color=0x0055AA)
                
                # Show player's attack
                player_coord = f"{chr(65+self.row_pos)}{self.col_pos+1}"
                embed.add_field(name="Your Attack", value=f"{player_coord}: {'💥 HIT!' if result == 'hit' else '💧 Miss'}", inline=True)
                
                # Show bot's attack if it happened
                if bot_attack_info:
                    embed.add_field(name="Bot's Response", value=bot_attack_info.strip().replace("🤖 **Bot attacked ", "").replace("**:", ":"), inline=True)
                
                embed.add_field(name="Current Turn", value=ctx.author.mention, inline=True)
                embed.add_field(name="Bet", value=f"**{amount:.2f}** points", inline=True)
                embed.set_footer(text="💥 = Hit | 💧 = Miss | Click to attack!")
                
                await safe_interaction_response(interaction, embed=embed, view=self.view)
    
    # Create view
    view = discord.ui.View(timeout=600)
    for i in range(5):
        for j in range(5):
            view.add_item(AttackButton(i, j, game, session))
    
    # Send initial message
    embed = discord.Embed(title="🚢 Naval War - Game Started!", color=0x0055AA)
    embed.add_field(name="Players", value=f"{ctx.author.mention} vs Bot", inline=False)
    embed.add_field(name="Bet", value=f"**{amount:.2f}** points", inline=True)
    embed.add_field(name="Current Turn", value=ctx.author.mention, inline=False)
    embed.add_field(name="Grid", value="A-E (rows) × 1-5 (columns)", inline=True)
    embed.add_field(name="Ships", value="3 ships placed randomly", inline=True)
    embed.set_footer(text="Ships are hidden! Click coordinates to attack. First to sink all enemy ships wins!")
    
    await ctx.send(embed=embed, view=view)

# ========== SIMPLE GAMES (NON-INTERACTIVE) ==========
@require_guild()
@bot.command()
@cooldown_check()
async def coinflip(ctx, amount: str):
    user_id = ctx.author.id
    
    # Check daily play limit
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'coinflip')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **coinflip** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    suspicious = await anti_cheat.detect_suspicious_activity(user_id)
    if suspicious:
        await anti_cheat.check_and_ban_cheater(ctx, user_id, f"Suspicious activity: {suspicious}")
        return
    
    await db.update_balance(user_id, -amount, "Coinflip bet")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_coinflip")
    
    # Create choice buttons
    class HeadsButton(discord.ui.Button):
        def __init__(self):
            super().__init__(style=discord.ButtonStyle.primary, label='🪙 Heads', row=0)
        
        async def callback(self, interaction):
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            await process_coinflip(interaction, 'heads')
    
    class TailsButton(discord.ui.Button):
        def __init__(self):
            super().__init__(style=discord.ButtonStyle.danger, label='🪙 Tails', row=0)
        
        async def callback(self, interaction):
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            await process_coinflip(interaction, 'tails')
    
    async def process_coinflip(interaction, choice):
        # Defer interaction immediately to prevent timeout
        await safe_defer(interaction)
        
        # ADMIN FORCED LOSS CHECK (SILENT - user never knows)
        should_force_loss = await check_forced_loss(user_id)
        
        if should_force_loss:
            # Silently force loss - appears as normal random result
            result = 'tails' if choice == 'heads' else 'heads'
        else:
            # REBALANCED: ~30% win rate for all bet amounts
            win_chance = random.random()  # 0.0 to 1.0
            if win_chance < 0.30:
                result = choice  # Player wins (30% chance)
            else:
                result = 'tails' if choice == 'heads' else 'heads'  # Player loses (70% chance)
        
        unlocked_achievements = []  # Initialize to prevent UnboundLocalError
        
        # Generate coinflip image
        coinflip_image = await generate_coinflip_image(result, choice)
        
        # Check if player won based on coin result
        if result == choice:
            # REBALANCED: 1.92x multiplier for 30% win rate
            base_multiplier = 1.92
            total_multiplier = base_multiplier
            
            # Apply VIP multiplier
            if is_vip:
                total_multiplier *= VIP_MULTIPLIER
            
            # Apply boost multiplier
            if boost_multiplier > 1.0:
                total_multiplier *= boost_multiplier
            
            win_amount = int(amount * total_multiplier)
            multiplier = total_multiplier
            await db.update_balance(user_id, win_amount, f"Coinflip win: x{multiplier:.2f}")
            await db.record_win(user_id, "COINFLIP", amount, win_amount, multiplier)
            await db.update_user_stats(user_id, won=True)
            await db.record_activity(user_id, f"win_coinflip_{win_amount}")
            
            unlocked_achievements = await achievement_checker.check_achievements(ctx, user_id, {
                'won': True, 'bet_amount': amount, 'multiplier': multiplier
            })
            
            embed = discord.Embed(title="🪙 Coinflip - YOU WON! 🎉", description=f"━━━━━━━━━━━━━━━━━━━━", color=0xFFD700)
            embed.add_field(name="🎯 Your Choice", value=f"**{choice.upper()}**", inline=True)
            embed.add_field(name="🪙 Result", value=f"**{result.upper()}**", inline=True)
            embed.add_field(name="💰 Wagered", value=f"**${amount:,}** points", inline=True)
            embed.add_field(name="✨ Multiplier", value=f"**x{multiplier:.2f}**", inline=True)
            embed.add_field(name="🏆 You Won", value=f"**+${win_amount:,}** points! 💵", inline=True)
            embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value="\u200b", inline=False)
            
            bonus_text = []
            if is_vip: bonus_text.append(f"⭐ VIP ({VIP_MULTIPLIER}x)")
            if boost_multiplier > 1.0: bonus_text.append(f"🚀 Boost ({boost_multiplier}x)")
            if bonus_text: 
                embed.add_field(name="🎁 Active Bonuses", value=" • ".join(bonus_text), inline=False)
            
            embed.add_field(name="💵 New Balance", value=f"**${await db.get_balance(user_id):,}** points", inline=False)
            
            if coinflip_image:
                embed.set_image(url="attachment://coinflip.png")
                file = discord.File(coinflip_image, filename="coinflip.png")
                await safe_interaction_response(interaction, embed=embed, view=None, file=file)
            else:
                embed.set_thumbnail(url="https://em-content.zobj.net/source/animated-noto-color-emoji/356/coin_1fa99.gif")
                await safe_interaction_response(interaction, embed=embed, view=None)
            
            # Log ALL wins to WIN_LOG_CHANNEL
            await WinLogger.log_win(ctx.author, "COINFLIP", amount, win_amount, multiplier,
                                   details=f"Choice: {choice.upper()}, Result: {result.upper()}")
            await RankManager.check_rank_up(ctx, user_id)
            
            for achievement_id in unlocked_achievements:
                achievement = ACHIEVEMENTS[achievement_id]
                await ctx.send(f"🎯 **Achievement Unlocked!** {achievement['name']}")
            
        else:
            await db.update_user_stats(user_id, won=False)
            loss_message = get_loss_message()
            embed = discord.Embed(title="🪙 Coinflip - YOU LOST! 💔", description=f"━━━━━━━━━━━━━━━━━━━━\n{loss_message}", color=0xFF0000)
            embed.add_field(name="🎯 Your Choice", value=f"**{choice.upper()}**", inline=True)
            embed.add_field(name="🪙 Result", value=f"**{result.upper()}**", inline=True)
            embed.add_field(name="💸 Lost", value=f"**-${amount:,}** points 💥", inline=True)
            embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value="\u200b", inline=False)
            embed.add_field(name="💵 New Balance", value=f"**${await db.get_balance(user_id):,}** points", inline=False)
            
            if coinflip_image:
                embed.set_image(url="attachment://coinflip.png")
                file = discord.File(coinflip_image, filename="coinflip.png")
                await safe_interaction_response(interaction, embed=embed, view=None, file=file)
            else:
                embed.set_thumbnail(url="https://em-content.zobj.net/source/animated-noto-color-emoji/356/broken-heart_1f494.gif")
                await safe_interaction_response(interaction, embed=embed, view=None)
        
        # Show remaining plays
        await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
    
    # Create view with buttons
    view = discord.ui.View(timeout=60)
    view.add_item(HeadsButton())
    view.add_item(TailsButton())
    
    # Send initial message
    embed = discord.Embed(title="🪙 Coinflip Game", description="Choose Heads or Tails!", color=0xFFD700)
    embed.add_field(name="Bet Amount", value=f"**{amount}** points", inline=True)
    embed.add_field(name="Win Multiplier", value=f"**1.92x**", inline=True)
    embed.add_field(name="Choose", value="Click a button below!", inline=True)
    await ctx.send(embed=embed, view=view)

@require_guild()
@bot.command()
@cooldown_check()
async def slots(ctx, amount: str):
    user_id = ctx.author.id
    
    # Check daily play limit
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'slots')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **slots** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    suspicious = await anti_cheat.detect_suspicious_activity(user_id)
    if suspicious:
        await anti_cheat.check_and_ban_cheater(ctx, user_id, f"Suspicious activity: {suspicious}")
        return
    
    await db.update_balance(user_id, -amount, "Slots bet")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_slots")
    
    unlocked_achievements = []  # Initialize to prevent UnboundLocalError
    
    # ADMIN FORCED LOSS CHECK (SILENT - user never knows)
    should_force_loss = await check_forced_loss(user_id)
    
    if should_force_loss:
        # Silently force loss - generate losing combination
        symbols = ['🍒', '🔔', '💎']
        reels = [random.choice(symbols) for _ in range(3)]
        # Make sure it's not a winning combination
        while reels[0] == reels[1] == reels[2] or (reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]):
            reels = [random.choice(symbols) for _ in range(3)]
        win_amount = 0
        multiplier = 0
    else:
        # Normal game logic
        # BALANCED: Fair win rate ~20-22% (3-match ~12% + 2-match bonus ~8-10%)
        symbols = ['🍒', '🔔', '💎']  # Simplified to 3 symbols for better match probability
        weights = [40, 40, 20]  # Balanced weights → ~12% 3-match rate
        
        reels = random.choices(symbols, weights=weights, k=3)
        
        # Calculate win based on combination
        win_amount = 0
        multiplier = 0
    
    # Check for 3 matching symbols
    if reels[0] == reels[1] == reels[2]:
        if reels[0] == '🎰':
            base_multiplier = 2.5  # Profit multiplier
        elif reels[0] == '💎':
            base_multiplier = 1.7  # Profit multiplier
        elif reels[0] == '🔔':
            base_multiplier = 1.5  # Profit multiplier
        else:
            base_multiplier = 1.3  # Profit multiplier (cherries)
        
        # Apply bonuses to multiplier
        final_multiplier = base_multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
        # Win = profit + original bet back
        profit = int(amount * final_multiplier)
        win_amount = profit + amount
        multiplier = final_multiplier  # For display
    
    # Check for 2 matching symbols (small consolation prize)
    elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
        if random.random() < 0.30:  # REBALANCED: 30% chance on 2 matches
            base_multiplier = 1.3  # Profit multiplier
            final_multiplier = base_multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
            profit = int(amount * final_multiplier)
            win_amount = profit + amount
            multiplier = final_multiplier  # For display
    
    # Generate slots machine image
    result_text = "JACKPOT! 🎉" if (win_amount > 0 and multiplier >= 3.0) else "WIN! ✨" if win_amount > 0 else "LOST ❌"
    slots_image = await generate_slots_image(reels, result_text)
    
    if win_amount > 0:
        await db.update_balance(user_id, win_amount, f"Slots win: x{multiplier:.2f}")
        await db.record_win(user_id, "SLOTS", amount, win_amount, multiplier)
        await db.update_user_stats(user_id, won=True)
        await db.record_activity(user_id, f"win_slots_{win_amount}")
        
        unlocked_achievements = await achievement_checker.check_achievements(ctx, user_id, {
            'won': True, 'bet_amount': amount, 'multiplier': multiplier
        })
        
        title = "🎰 Slots - JACKPOT!" if multiplier >= 3.0 else "🎰 Slots - WIN!"
        embed = discord.Embed(title=title, description=f"**{''.join(reels)}**", color=0x00ff00)
        embed.add_field(name="Multiplier", value=f"**x{multiplier:.2f}**", inline=True)
        embed.add_field(name="You Won", value=f"**{win_amount}** points! 🎉", inline=True)
        
        bonus_text = []
        if is_vip: bonus_text.append(f"VIP ({VIP_MULTIPLIER}x)")
        if boost_multiplier > 1.0: bonus_text.append(f"Boost ({boost_multiplier}x)")
        if bonus_text: embed.add_field(name="⭐ Active Bonuses", value=", ".join(bonus_text), inline=True)
        
    else:
        await db.update_user_stats(user_id, won=False)
        loss_message = get_loss_message()
        embed = discord.Embed(title="🎰 Slots - Try Again!", description=f"**{''.join(reels)}**\n\n{loss_message}", color=0xff0000)
        embed.add_field(name="Result", value="**LOST** 💥", inline=True)
        embed.add_field(name="Amount Lost", value=f"**{amount}** points", inline=True)
    
    embed.add_field(name="New Balance", value=f"**{await db.get_balance(user_id):,}** points", inline=True)
    
    if slots_image:
        embed.set_image(url="attachment://slots.png")
        file = discord.File(slots_image, filename="slots.png")
        await ctx.send(embed=embed, file=file)
    else:
        await ctx.send(embed=embed)
    
    if win_amount > 0:
        # Log ALL wins to WIN_LOG_CHANNEL
        await WinLogger.log_win(ctx.author, "SLOTS", amount, win_amount, multiplier,
                               details=f"Reels: {''.join(reels)}")
        await RankManager.check_rank_up(ctx, user_id)
    
    for achievement_id in unlocked_achievements:
        achievement = ACHIEVEMENTS[achievement_id]
        await ctx.send(f"🎯 **Achievement Unlocked!** {achievement['name']}")
    
    # Show remaining plays
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

@require_guild()
@bot.command()
@cooldown_check()
async def dice(ctx, amount: str, number: int = 6):
    user_id = ctx.author.id
    
    # Check daily play limit
    can_play, remaining, is_vip = await play_limiter.check_and_increment(ctx.author.id, 'dice')
    if not can_play:
        vip_text = " (VIP)" if is_vip else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **dice** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    if number < 1 or number > 6:
        await ctx.send("❌ Number must be between 1 and 6!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount, f"Dice bet: Guess {number}")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_dice")
    
    # ADMIN FORCED LOSS CHECK (SILENT - user never knows)
    should_force_loss = await check_forced_loss(user_id)
    
    if should_force_loss:
        # Silently force loss - pick any number except their guess
        possible_rolls = [n for n in range(1, 7) if n != number]
        roll = random.choice(possible_rolls)
    else:
        # Normal random roll
        roll = random.randint(1, 6)
    
    # Generate dice image
    dice_image = await generate_dice_image(roll, target=number)
    
    if roll == number:
        # PLAYER WINS - guessed correctly! (1/6 = 16.67% win rate)
        # Calculate multiplier only (no double random check)
        min_mult, max_mult = DifficultySystem.get_multiplier_range(amount, 'dice')
        base_multiplier = random.uniform(min_mult, max_mult)
        
        # Apply VIP and boost bonuses
        if is_vip:
            base_multiplier *= VIP_MULTIPLIER
        base_multiplier *= boost_multiplier
        
        # Win amount = net profit + original bet (multiplier represents profit only)
        profit = int(amount * base_multiplier)
        win_amount = profit + amount  # Return profit + original bet
        multiplier = base_multiplier  # Display multiplier (profit only)
        
        await db.update_balance(user_id, win_amount, f"Dice win: Rolled {roll}")
        await db.record_win(user_id, "DICE", amount, win_amount, multiplier)
        await db.update_user_stats(user_id, won=True)
        
        # Dice emoji mapping
        dice_emoji = {1: '⚀', 2: '⚁', 3: '⚂', 4: '⚃', 5: '⚄', 6: '⚅'}
        
        embed = discord.Embed(title="🎲 Dice - YOU WON! 🎉", description="━━━━━━━━━━━━━━━━━━━━", color=0xFFD700)
        embed.add_field(name="🎯 Your Guess", value=f"**{number}** {dice_emoji[number]}", inline=True)
        embed.add_field(name="🎲 Rolled", value=f"**{roll}** {dice_emoji[roll]}", inline=True)
        embed.add_field(name="💰 Wagered", value=f"**{amount:,}** points", inline=True)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value="", inline=False)
        embed.add_field(name="✨ Multiplier", value=f"**x{multiplier:.2f}**", inline=True)
        embed.add_field(name="🏆 You Won", value=f"**+{win_amount:,}** points! 💵", inline=True)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value="", inline=False)
        embed.add_field(name="💵 New Balance", value=f"**{await db.get_balance(user_id):,}** points", inline=False)
        
        if dice_image:
            embed.set_image(url="attachment://dice.png")
            file = discord.File(dice_image, filename="dice.png")
            await ctx.send(embed=embed, file=file)
        else:
            await ctx.send(embed=embed)
        
        # Log ALL wins to WIN_LOG_CHANNEL
        await WinLogger.log_win(ctx.author, "DICE", amount, win_amount, multiplier,
                               details=f"Guess: {number}, Roll: {roll}")
    else:
        # PLAYER LOSES - wrong guess
        await db.update_user_stats(user_id, won=False)
        loss_message = get_loss_message()
        
        # Dice emoji mapping
        dice_emoji = {1: '⚀', 2: '⚁', 3: '⚂', 4: '⚃', 5: '⚄', 6: '⚅'}
        
        embed = discord.Embed(title="🎲 Dice - YOU LOST! 💔", description=f"━━━━━━━━━━━━━━━━━━━━\n{loss_message}", color=0xFF0000)
        embed.add_field(name="🎯 Your Guess", value=f"**{number}** {dice_emoji[number]}", inline=True)
        embed.add_field(name="🎲 Rolled", value=f"**{roll}** {dice_emoji[roll]}", inline=True)
        embed.add_field(name="💸 Lost", value=f"**-{amount:,}** points 💥", inline=True)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value="", inline=False)
        embed.add_field(name="💵 New Balance", value=f"**{await db.get_balance(user_id):,}** points", inline=False)
        
        if dice_image:
            embed.set_image(url="attachment://dice.png")
            file = discord.File(dice_image, filename="dice.png")
            await ctx.send(embed=embed, file=file)
        else:
            await ctx.send(embed=embed)
    
    # Show remaining plays
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip else '5'}")

# Roulette View for step-by-step betting
class RouletteView(discord.ui.View):
    def __init__(self, user_id, base_bet, remaining=None, is_vip=False):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.base_bet = base_bet
        self.remaining = remaining
        self.is_vip = is_vip
        self.stage = 0  # 0: Color, 1: Parity, 2: Category
        self.bets = {}  # Dictionary to store selected bets
        self.clear_items()
        self.show_color_selection()
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your roulette table!", ephemeral=True)
            return False
        return True
    
    def show_color_selection(self):
        """Stage 0: Color selection"""
        self.clear_items()
        self.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, label="🔴 Red", custom_id="red", row=0))
        self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label="⚫ Black", custom_id="black", row=0))
        self.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label="⏭ Skip", custom_id="skip_color", row=0))
        
        for item in self.children:
            item.callback = self.color_callback
    
    def show_parity_selection(self):
        """Stage 1: Parity selection"""
        self.clear_items()
        self.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="🔢 Odd", custom_id="odd", row=0))
        self.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="🔢 Even", custom_id="even", row=0))
        self.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label="⏭ Skip", custom_id="skip_parity", row=0))
        
        for item in self.children:
            item.callback = self.parity_callback
    
    def show_category_selection(self):
        """Stage 2: Category selection"""
        self.clear_items()
        self.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label="🔵 Cat 1 (1-12)", custom_id="dozen1", row=0))
        self.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label="🟢 Cat 2 (13-24)", custom_id="dozen2", row=0))
        self.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label="🟡 Cat 3 (25-36)", custom_id="dozen3", row=1))
        self.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label="⏭ Skip", custom_id="skip_category", row=1))
        
        for item in self.children:
            item.callback = self.category_callback
    
    async def color_callback(self, interaction: discord.Interaction):
        """Handle color selection"""
        choice = interaction.data['custom_id']
        
        if choice in ['red', 'black']:
            self.bets['color'] = choice
        
        self.stage = 1
        self.show_parity_selection()
        
        selected = self.bets.get('color', 'None')
        await safe_interaction_response(interaction, 
            content=f"🎡 **Roulette - Step 2/3**\n💰 Bet per selection: **{self.base_bet}** points\n\n"
                    f"✅ Color: **{selected.capitalize() if selected != 'None' else 'Skipped'}**\n\n"
                    f"🎯 Choose **Odd or Even** (or skip):",
            view=self
        )
    
    async def parity_callback(self, interaction: discord.Interaction):
        """Handle parity selection"""
        choice = interaction.data['custom_id']
        
        if choice in ['odd', 'even']:
            self.bets['parity'] = choice
        
        self.stage = 2
        self.show_category_selection()
        
        color = self.bets.get('color', 'None')
        parity = self.bets.get('parity', 'None')
        
        await safe_interaction_response(interaction, 
            content=f"🎡 **Roulette - Step 3/3**\n💰 Bet per selection: **{self.base_bet}** points\n\n"
                    f"✅ Color: **{color.capitalize() if color != 'None' else 'Skipped'}**\n"
                    f"✅ Parity: **{parity.capitalize() if parity != 'None' else 'Skipped'}**\n\n"
                    f"🎯 Choose a **Category** (or skip):",
            view=self
        )
    
    async def category_callback(self, interaction: discord.Interaction):
        """Handle category selection and spin"""
        choice = interaction.data['custom_id']
        
        if choice in ['dozen1', 'dozen2', 'dozen3']:
            self.bets['category'] = choice
        
        # Calculate total bet
        bet_count = len([v for v in self.bets.values() if v != 'None'])
        
        if bet_count == 0:
            await interaction.response.send_message("❌ You must select at least one bet! (You skipped all sections)", ephemeral=True)
            return
        
        total_bet = bet_count * self.base_bet
        
        # Check balance
        balance = await db.get_balance(self.user_id)
        if balance < total_bet:
            await interaction.response.send_message(f"❌ Insufficient balance! You need **{total_bet}** points but have **{balance}** points.", ephemeral=True)
            return
        
        # Deduct total bet
        await db.update_balance(self.user_id, -total_bet, f"Roulette bet: {bet_count} bet(s)")
        await db.add_wager(self.user_id, total_bet)
        await db.record_activity(self.user_id, "play_roulette")
        
        # Get VIP and boost
        is_vip = await db.is_vip(self.user_id)
        boost_multiplier = await db.get_total_boost_multiplier(self.user_id)
        
        # Spin the wheel
        number = random.randint(0, 36)
        is_red = number in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
        is_black = number in [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]
        is_even = number % 2 == 0 and number != 0
        is_odd = number % 2 == 1
        
        # Track winning and losing bets
        winning_bets = []
        losing_bets = []
        winning_bet_count = 0
        
        # Check color bet - uses actual roulette odds
        if 'color' in self.bets:
            if (self.bets['color'] == 'red' and is_red) or (self.bets['color'] == 'black' and is_black):
                winning_bets.append(self.bets['color'].capitalize())
                winning_bet_count += 1
            else:
                losing_bets.append(self.bets['color'].capitalize())
        
        # Check parity bet - uses actual roulette odds
        if 'parity' in self.bets:
            if (self.bets['parity'] == 'odd' and is_odd) or (self.bets['parity'] == 'even' and is_even):
                winning_bets.append(self.bets['parity'].capitalize())
                winning_bet_count += 1
            else:
                losing_bets.append(self.bets['parity'].capitalize())
        
        # Check category bet - uses actual roulette odds
        if 'category' in self.bets:
            cat_won = False
            cat_name = ""
            if self.bets['category'] == 'dozen1' and 1 <= number <= 12:
                cat_won = True
                cat_name = "Cat 1 (1-12)"
            elif self.bets['category'] == 'dozen2' and 13 <= number <= 24:
                cat_won = True
                cat_name = "Cat 2 (13-24)"
            elif self.bets['category'] == 'dozen3' and 25 <= number <= 36:
                cat_won = True
                cat_name = "Cat 3 (25-36)"
            
            if cat_won:
                winning_bets.append(cat_name)
                winning_bet_count += 1
            else:
                if self.bets['category'] == 'dozen1':
                    losing_bets.append("Cat 1")
                elif self.bets['category'] == 'dozen2':
                    losing_bets.append("Cat 2")
                else:
                    losing_bets.append("Cat 3")
        
        # Calculate total winnings: Base 1.92x minus 0.40 for each additional bet
        total_winnings = 0
        if winning_bet_count > 0:
            winning_amount = winning_bet_count * self.base_bet
            
            # Total bet count (including losing bets)
            total_bet_count = len([v for v in self.bets.values() if v != 'None'])
            
            # Reduce multiplier by 0.40 for each bet beyond the first
            payout = 1.92 - (0.40 * (total_bet_count - 1))
            payout = max(payout, 0.72)  # Minimum 0.72x to avoid negative
            
            multiplier = payout * (1.15 if is_vip else 1.0) * boost_multiplier
            total_winnings = int(winning_amount * multiplier)
        
        # Determine color for result display
        if is_red:
            number_display = f"🔴 **{number}** (Red)"
        elif is_black:
            number_display = f"⚫ **{number}** (Black)"
        else:
            number_display = f"🟢 **{number}** (Green)"
        
        # Build bet summary
        bet_summary = []
        if 'color' in self.bets:
            bet_summary.append(self.bets['color'].capitalize())
        if 'parity' in self.bets:
            bet_summary.append(self.bets['parity'].capitalize())
        if 'category' in self.bets:
            if self.bets['category'] == 'dozen1':
                bet_summary.append("Cat 1")
            elif self.bets['category'] == 'dozen2':
                bet_summary.append("Cat 2")
            else:
                bet_summary.append("Cat 3")
        
        # Calculate total bet count for display
        total_bet_count = len([v for v in self.bets.values() if v != 'None'])
        base_payout = 1.92 - (0.40 * (total_bet_count - 1))
        base_payout = max(base_payout, 0.72)
        
        # Update stats and balance
        if total_winnings > 0:
            await db.update_balance(self.user_id, total_winnings, f"Roulette win: {number_display}")
            await db.record_win(self.user_id, "ROULETTE", total_bet, total_winnings, total_winnings / total_bet)
            await db.update_user_stats(self.user_id, won=True)
            
            # Log ALL wins to WIN_LOG_CHANNEL
            user = await bot.fetch_user(self.user_id)
            await WinLogger.log_win(user, "ROULETTE", total_bet, total_winnings, total_winnings / total_bet,
                                   details=f"Number: {number_display}, Bets: {', '.join(bet_summary)}")
            
            embed = discord.Embed(title="🎡 Roulette - WON!", description=f"Ball landed on {number_display}", color=0x00ff00)
            embed.add_field(name="Your Bets", value=", ".join(bet_summary) + f" (**{total_bet}** pts)", inline=False)
            embed.add_field(name="✅ Won", value="\n".join(winning_bets) if winning_bets else "None", inline=True)
            if losing_bets:
                embed.add_field(name="❌ Lost", value="\n".join(losing_bets), inline=True)
            
            winning_amount = winning_bet_count * self.base_bet
            embed.add_field(name="💰 Calculation", value=f"{winning_bet_count} bet(s) × {self.base_bet} pts × {base_payout:.2f} = **{total_winnings}** pts", inline=False)
            embed.add_field(name="Total Winnings", value=f"**{total_winnings}** points! 🎉", inline=False)
        else:
            await db.update_user_stats(self.user_id, won=False)
            loss_message = get_loss_message()
            embed = discord.Embed(title="🎡 Roulette - LOST", description=f"Ball landed on {number_display}\n\n{loss_message}", color=0xff0000)
            embed.add_field(name="Your Bets", value=", ".join(bet_summary) + f" (**{total_bet}** pts)", inline=False)
            embed.add_field(name="Result", value="**All bets LOST** 💥", inline=True)
        
        embed.add_field(name="New Balance", value=f"**{await db.get_balance(self.user_id):,}** points", inline=True)
        
        # Add remaining plays message if available
        remaining_msg = ""
        if self.remaining is not None:
            remaining_msg = f"\n\n🎮 Remaining plays today: **{self.remaining}**/{'10' if self.is_vip else '5'}"
        
        await safe_interaction_response(interaction, content=remaining_msg if remaining_msg else None, embed=embed, view=None)
        self.stop()

@require_guild()
@bot.command()
@cooldown_check()
async def roulette(ctx, amount: str):
    user_id = ctx.author.id
    
    # Check daily play limit
    can_play, remaining, is_vip = await play_limiter.check_and_increment(ctx.author.id, 'roulette')
    if not can_play:
        vip_text = " (VIP)" if is_vip else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **roulette** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    view = RouletteView(user_id, amount, remaining, is_vip)
    await ctx.send(
        f"🎡 **Roulette - Step 1/3**\n💰 Bet per selection: **{amount}** points\n📊 Plays left today: **{remaining + 1}**/{'10' if is_vip else '5'}\n\n🎯 Choose **Red or Black** (or skip):",
        view=view
    )

# ========== NEW CASINO GAMES ==========

# Get base URL for images
BASE_IMAGE_URL = f"https://{os.getenv('REPLIT_DEV_DOMAIN', 'localhost:5000')}/images"

# Win/Loss Image URLs - Now using real casino images! �
WIN_IMAGES = {
    # Main casino games with real images �
    'blackjack': f'{BASE_IMAGE_URL}/blackjack_cards_casi_5c8f5ffd.jpg',
    'baccarat': f'{BASE_IMAGE_URL}/baccarat_casino_card_87d41d2e.jpg',
    'roulette': f'{BASE_IMAGE_URL}/roulette_wheel_casin_f6c37baa.jpg',
    'poker': f'{BASE_IMAGE_URL}/poker_cards_chips_ca_957d7cce.jpg',
    'crash': f'{BASE_IMAGE_URL}/crash_game_casino_ro_df8a8157.jpg',
    'mines': f'{BASE_IMAGE_URL}/mines_game_minesweep_9141dd61.jpg',
    
    # Dice games �
    'classicdice': f'{BASE_IMAGE_URL}/dice_rolling_casino__455afa75.jpg',
    'dicewar': f'{BASE_IMAGE_URL}/dice_rolling_casino__455afa75.jpg',
    'blackjackdice': f'{BASE_IMAGE_URL}/dice_rolling_casino__455afa75.jpg',
    
    # Coin games �
    'progressivecoinflip': f'{BASE_IMAGE_URL}/coin_flip_gold_casin_88d940a7.jpg',
    
    # Slots games �
    'classicslots': f'{BASE_IMAGE_URL}/slot_machine_jackpot_ddd7678e.jpg',
    
    # Card games - use poker/blackjack images
    'cards': f'{BASE_IMAGE_URL}/poker_cards_chips_ca_957d7cce.jpg',
    
    # Generic wins - use casino chips winner image �
    'plinko': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'keno': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'horse': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'hilo': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'rps': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'gtn': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'case': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'wheel': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'chickenroad': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'connect': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'balloon': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'chess': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'darts': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'diamonds': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'easter': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'eviljokers': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'fight': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'ghosts': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'gn': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'treasurehunt': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'valentines': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'war': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'wheelcolor': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'wordly': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg',
    'generic': f'{BASE_IMAGE_URL}/casino_chips_winner__d8c0d3d6.jpg'
}

LOSS_IMAGES = {
    # Main casino games with real images �
    'blackjack': f'{BASE_IMAGE_URL}/blackjack_cards_casi_da6d0acd.jpg',
    'baccarat': f'{BASE_IMAGE_URL}/baccarat_casino_card_0d430a69.jpg',
    'roulette': f'{BASE_IMAGE_URL}/roulette_wheel_casin_588c0cc7.jpg',
    'poker': f'{BASE_IMAGE_URL}/poker_cards_chips_ca_c7b0c6d6.jpg',
    'crash': f'{BASE_IMAGE_URL}/crash_game_casino_ro_3fecd751.jpg',
    'mines': f'{BASE_IMAGE_URL}/mines_game_minesweep_5c0e7b89.jpg',
    
    # Dice games �
    'classicdice': f'{BASE_IMAGE_URL}/dice_rolling_casino__40160fe4.jpg',
    'dicewar': f'{BASE_IMAGE_URL}/dice_rolling_casino__40160fe4.jpg',
    'blackjackdice': f'{BASE_IMAGE_URL}/dice_rolling_casino__40160fe4.jpg',
    
    # Coin games �
    'progressivecoinflip': f'{BASE_IMAGE_URL}/coin_flip_gold_casin_f68d929d.jpg',
    
    # Slots games �
    'classicslots': f'{BASE_IMAGE_URL}/slot_machine_jackpot_b3f68f01.jpg',
    
    # Card games
    'cards': f'{BASE_IMAGE_URL}/poker_cards_chips_ca_c7b0c6d6.jpg',
    
    # Generic losses - use casino chips losing image �
    'plinko': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'keno': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'horse': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'hilo': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'rps': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'gtn': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'case': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'wheel': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'chickenroad': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'connect': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'balloon': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'chess': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'darts': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'diamonds': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'easter': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'eviljokers': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'fight': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'ghosts': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'gn': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'treasurehunt': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'valentines': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'war': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'wheelcolor': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'wordly': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg',
    'generic': f'{BASE_IMAGE_URL}/casino_losing_chips__c32be6d2.jpg'
}

class PlinkoView(discord.ui.View):
    def __init__(self, user_id, bet_per_drop, drop_count, ctx):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.bet_per_drop = bet_per_drop
        self.drop_count = drop_count
        self.drops_done = 0
        self.total_won = 0
        self.ctx = ctx
        self.message = None
        self.stopped = False
        
    @discord.ui.button(label="🔴 Drop Balls", style=discord.ButtonStyle.green, custom_id="drop_plinko")
    async def drop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ This isn't your game!", ephemeral=True)
        
        # Defer interaction to prevent timeout
        await safe_defer(interaction)
        
        # Disable drop button, enable stop button
        button.disabled = True
        button.label = "Dropping..."
        
        # Add stop button
        stop_btn = discord.ui.Button(label="⏹ Stop", style=discord.ButtonStyle.danger, custom_id="stop_plinko")
        stop_btn.callback = self.stop_button_callback
        self.add_item(stop_btn)
        
        await safe_interaction_response(interaction, view=self)
        
        # Get VIP and boost status
        is_vip = await db.is_vip(self.user_id)
        boost_multiplier = await db.get_total_boost_multiplier(self.user_id)
        
        # REBALANCED: Reduced RTP from ~95% to 85% (multipliers reduced, weights adjusted)
        multipliers = [0.3, 0.5, 0.7, 1.0, 1.5, 1.0, 0.7, 0.5, 0.3]  # Lower multipliers
        weights = [3, 5, 7, 8, 6, 8, 7, 5, 3]  # Favor lower slots more
        
        results = []
        
        for i in range(self.drop_count):
            if self.stopped:
                results.append(f"⏹ Drop {i+1}: **Stopped**")
                break
                
            # Simulate drop
            slot = random.choices(range(len(multipliers)), weights=weights)[0]
            multiplier = multipliers[slot]
            final_multiplier = multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
            
            # Animated ball falling through levels
            for level in range(5):
                board = "```\n"
                board += "  🎯 PLINKO BOARD 🎯\n"
                board += "  ╔═══════════════╗\n"
                
                # Show ball falling
                for row in range(4):
                    board += "  ║ "
                    if row == level and level < 4:
                        # Ball is at this level
                        pos = random.randint(0, 7)
                        pegs = ""
                        for p in range(8):
                            if p == pos:
                                pegs += "🔴 "
                            else:
                                pegs += "⚪ "
                        board += pegs + "║\n"
                    elif row < level:
                        # Ball already passed
                        board += "⚪ " * 8 + "║\n"
                    else:
                        # Ball hasn't reached yet
                        board += "⚪ " * 8 + "║\n"
                
                board += "  ╚═══════════════╝\n"
                board += f"   {' '.join([str(multipliers[j]) + 'x' for j in range(len(multipliers))])}\n"
                
                if level == 4:
                    # Final position
                    board += f"\n🎯 Ball #{i+1} landed in slot {slot+1}!\n"
                    board += f"Multiplier: {final_multiplier:.2f}x```"
                else:
                    board += f"\n🔴 Ball #{i+1} falling... (level {level+1}/4)```"
                
                embed = discord.Embed(title="🎯 Plinko - Ball Dropping!", color=0xffaa00)
                embed.description = board
                embed.add_field(name="Progress", value=f"Ball {i+1}/{self.drop_count}", inline=False)
                await interaction.edit_original_response(embed=embed, view=self)
                await asyncio.sleep(0.4)
            
            # Calculate payout - ALWAYS give back multiplier * bet
            payout = int(self.bet_per_drop * final_multiplier)
            self.total_won += payout
            
            if final_multiplier >= 1.0:
                results.append(f"✅ Drop {i+1}: +**{payout}** pts ({final_multiplier:.2f}x)")
                await db.update_user_stats(self.user_id, won=True)
            else:
                results.append(f"🟡 Drop {i+1}: +**{payout}** pts ({final_multiplier:.2f}x partial)")
                await db.update_user_stats(self.user_id, won=False)
            
            # Give payout immediately
            await db.update_balance(self.user_id, payout, f"Plinko drop {i+1}: {final_multiplier:.2f}x")
        
        # Final results
        net_result = self.total_won - (self.bet_per_drop * self.drop_count)
        color = 0x00ff00 if net_result > 0 else (0xffaa00 if net_result > -(self.bet_per_drop * self.drop_count) else 0xff0000)
        
        final_embed = discord.Embed(title="🎯 Plinko - Complete!", color=color)
        final_embed.add_field(name="Total Bet", value=f"{self.bet_per_drop * self.drop_count} pts", inline=True)
        final_embed.add_field(name="Total Returned", value=f"{self.total_won} pts", inline=True)
        final_embed.add_field(name="Net Result", value=f"**{net_result:+d}** pts", inline=True)
        final_embed.add_field(name="Results", value="\n".join(results[:10]), inline=False)
        final_embed.add_field(name="Balance", value=f"{await db.get_balance(self.user_id):,} pts", inline=False)
        
        if net_result > 0:
            final_embed.set_image(url=WIN_IMAGES['plinko'])
        else:
            final_embed.set_image(url=LOSS_IMAGES['plinko'])
        
        # Remove all buttons
        self.clear_items()
        await interaction.edit_original_response(embed=final_embed, view=self)
    
    async def stop_button_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ This isn't your game!", ephemeral=True)
        
        self.stopped = True
        await interaction.response.send_message("⏹ Stopping after current drop...", ephemeral=True)

@require_guild()
@bot.command()
@cooldown_check()
async def plinko(ctx, bet_per_drop: str, drop_count: int = 1):
    """Plinko - Drop balls and watch them bounce! Usage: .plinko 10 5 (bet 10 pts, drop 5 balls)"""
    user_id = ctx.author.id
    
    # Parse drop count
    if drop_count < 1 or drop_count > 10:
        return await ctx.send("❌ Drop count must be between 1 and 10!")
    
    # Check daily play limit
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'plinko')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **plinko** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    bet_per_drop = await parse_amount(bet_per_drop, user_id)
    
    if bet_per_drop is None:
        return await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
    
    if bet_per_drop <= 0:
        return await ctx.send("❌ Positive bet amount!")
    
    total_bet = bet_per_drop * drop_count
    balance = await db.get_balance(user_id)
    if balance < total_bet:
        return await ctx.send(f"❌ Insufficient balance! Need **{total_bet}** pts ({bet_per_drop} × {drop_count} drops)")
    
    # Deduct total bet
    await db.update_balance(user_id, -total_bet, f"Plinko bet: {drop_count} drops × {bet_per_drop} pts")
    await db.add_wager(user_id, total_bet)
    await db.record_activity(user_id, "play_plinko")
    
    # Create interactive view
    embed = discord.Embed(title="🎯 Plinko - Ready!", color=0x00aaff)
    embed.description = f"Click the button to drop **{drop_count} ball(s)**!"
    embed.add_field(name="Bet Per Drop", value=f"**{bet_per_drop}** pts", inline=True)
    embed.add_field(name="Total Drops", value=f"**{drop_count}** balls", inline=True)
    embed.add_field(name="Total Bet", value=f"**{total_bet}** pts", inline=True)
    embed.add_field(name="Remaining Plays", value=f"**{remaining}**/{'10' if is_vip_check else '5'}", inline=False)
    
    view = PlinkoView(user_id, bet_per_drop, drop_count, ctx)
    message = await ctx.send(embed=embed, view=view)
    view.message = message

@require_guild()
@bot.command()
@cooldown_check()
async def keno(ctx, amount: str, *numbers: int):
    """Keno - Pick 1-10 numbers between 1-40, then 20 numbers are drawn"""
    user_id = ctx.author.id
    
    # Check daily play limit
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'keno')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **keno** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    if len(numbers) < 1 or len(numbers) > 10:
        await ctx.send("❌ You must pick between 1 and 10 numbers!")
        return
    
    if any(n < 1 or n > 40 for n in numbers):
        await ctx.send("❌ Numbers must be between 1 and 40!")
        return
    
    if len(numbers) != len(set(numbers)):
        await ctx.send("❌ You can't pick duplicate numbers!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount, "Keno bet")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_keno")
    
    # Draw 20 random numbers
    drawn_numbers = random.sample(range(1, 41), 20)
    user_numbers = set(numbers)
    matches = user_numbers.intersection(drawn_numbers)
    match_count = len(matches)
    
    # Keno payout table (Conservative EV ≤0.25 - only top matches pay out)
    payout_table = {
        1: {1: 0.5},  # P≈0.5, EV≈0.25
        2: {2: 1.0},  # P≈0.24, EV≈0.24
        3: {3: 2.0},  # P≈0.11, EV≈0.22
        4: {4: 3.0, 3: 0.3},  # P≈0.05/0.22, EV≈0.22
        5: {5: 5.0, 4: 0.5},  # P≈0.02/0.16, EV≈0.18
        6: {6: 6.0, 5: 0.8},  # P≈0.008/0.08, EV≈0.11
        7: {7: 6.0, 6: 1.2},  # P≈0.003/0.03, EV≈0.05
        8: {8: 6.0, 7: 2.0},  # P≈0.001/0.01, EV≈0.03
        9: {9: 6.0, 8: 2.5},  # P≈0.0003/0.003, EV≈0.01
        10: {10: 6.0, 9: 3.0}  # P≈0.00006/0.0009, EV≈0.003
    }
    
    picked_count = len(numbers)
    multiplier = payout_table.get(picked_count, {}).get(match_count, 0.0)
    final_multiplier = multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
    
    if multiplier > 0:
        # WIN
        win_amount = int(amount * final_multiplier)
        await db.update_balance(user_id, win_amount, f"Keno win: {final_multiplier:.2f}x")
        await db.record_win(user_id, "KENO", amount, win_amount, final_multiplier)
        await db.update_user_stats(user_id, won=True)
        
        embed = discord.Embed(title="🎰 Keno - WON!", description=f"Matched **{match_count}/{picked_count}** numbers!", color=0x00ff00)
        embed.add_field(name="Your Numbers", value=", ".join(str(n) for n in sorted(user_numbers)), inline=False)
        embed.add_field(name="Matches", value=", ".join(str(n) for n in sorted(matches)), inline=False)
        embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
        embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=WIN_IMAGES['keno'])
        await ctx.send(embed=embed)
        
        await WinLogger.log_win(ctx.author, "KENO", amount, win_amount, final_multiplier,
                               details=f"Matched {match_count}/{picked_count}")
    else:
        # LOST
        await db.update_user_stats(user_id, won=False)
        embed = discord.Embed(title="🎰 Keno - LOST", description=f"Matched **{match_count}/{picked_count}** numbers 💥", color=0xff0000)
        embed.add_field(name="Your Numbers", value=", ".join(str(n) for n in sorted(user_numbers)), inline=False)
        embed.add_field(name="Matches", value=", ".join(str(n) for n in sorted(matches)) if matches else "None", inline=False)
        embed.add_field(name="Lost", value=f"**{amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=LOSS_IMAGES['keno'])
        await ctx.send(embed=embed)
    
    # Show remaining plays
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

@require_guild()
@bot.command()
@cooldown_check()
async def horse(ctx, amount: str):
    """Horse Racing - Pick a horse and watch the race! 🐴"""
    user_id = ctx.author.id
    
    amount_parsed = await parse_amount(amount, user_id)
    if amount_parsed is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount_parsed <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount_parsed:
        await ctx.send("❌ Insufficient balance!")
        return
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'horse')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **horse** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount_parsed, "Horse racing bet")
    await db.add_wager(user_id, amount_parsed)
    await db.record_activity(user_id, "play_horse")
    
    # Pre-determine race outcome
    horses = [1, 2, 3, 4, 5, 6]
    weights = [10, 15, 20, 20, 15, 10]
    winning_horse = random.choices(horses, weights=weights)[0]
    
    horse_names = ["⚡ Lightning", "🔥 Flame", "💎 Diamond", "🌟 Star", "🏆 Champion", "👑 Royal"]
    horse_emojis = ["🐴", "🐎", "🏇", "🦄", "🐴", "🐎"]
    
    class HorseView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
        
        async def select_horse(self, interaction: discord.Interaction, horse_num: int):
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your race!", ephemeral=True)
                return
            
            # Acknowledge interaction immediately to prevent timeout
            await interaction.response.defer()
            
            # Animate the race! (Longer race with more frames)
            track_length = 25
            positions = [0, 0, 0, 0, 0, 0]
            
            # Starting line
            race_display = "🏁 **HORSE RACING** 🏁\n\n"
            for i in range(6):
                prefix = "🟢 " if i+1 == horse_num else "⚪ "
                race_display += f"{prefix}#{i+1} {horse_emojis[i]}{'_' * track_length}🏁 {horse_names[i]}\n"
            
            embed = discord.Embed(title="🐴 Starting Race!", description=race_display, color=0xFFD700)
            await interaction.edit_original_response(embed=embed, view=None)
            await asyncio.sleep(2.0)
            
            # Race animation (12 frames for longer race)
            for frame in range(12):
                for i in range(6):
                    if i+1 == winning_horse:
                        positions[i] += random.randint(2, 3)
                    else:
                        positions[i] += random.randint(1, 2)
                    positions[i] = min(positions[i], track_length)
                
                race_display = "🏁 **RACING...** 🏁\n\n"
                for i in range(6):
                    prefix = "🟢 " if i+1 == horse_num else "⚪ "
                    pos = positions[i]
                    track = '_' * pos + horse_emojis[i] + '_' * (track_length - pos)
                    race_display += f"{prefix}#{i+1} {track}🏁 {horse_names[i]}\n"
                
                embed = discord.Embed(title="🐴 Racing in Progress!", description=race_display, color=0xFFD700)
                await interaction.edit_original_response(embed=embed)
                await asyncio.sleep(0.8)
            
            # Final result
            race_display = "🏁 **FINISH!** 🏁\n\n"
            for i in range(6):
                prefix = "🟢 " if i+1 == horse_num else "⚪ "
                prefix += "🏆 " if i+1 == winning_horse else ""
                race_display += f"{prefix}#{i+1} {'_' * track_length}{horse_emojis[i]}🏁 {horse_names[i]}\n"
            
            if winning_horse == horse_num:
                base_multiplier = 2.2
                final_multiplier = base_multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
                win_amount = int(amount_parsed * final_multiplier)
                
                await db.update_balance(user_id, win_amount, f"Horse racing win: {final_multiplier:.2f}x")
                await db.record_win(user_id, "HORSE", amount_parsed, win_amount, final_multiplier)
                await db.update_user_stats(user_id, won=True)
                
                embed = discord.Embed(title="🐴 Horse Racing - YOU WON! 🏆", description=race_display, color=0x00ff00)
                embed.add_field(name="Your Horse", value=f"#{horse_num} {horse_names[horse_num - 1]}", inline=True)
                embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
                embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
                embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                embed.set_image(url=WIN_IMAGES['horse'])
                await interaction.edit_original_response(embed=embed)
                
                await WinLogger.log_win(ctx.author, "HORSE", amount_parsed, win_amount, final_multiplier,
                                       details=f"Horse #{horse_num} won")
            else:
                await db.update_user_stats(user_id, won=False)
                embed = discord.Embed(title="🐴 Horse Racing - LOST", description=race_display, color=0xff0000)
                embed.add_field(name="Your Horse", value=f"#{horse_num} {horse_names[horse_num - 1]}", inline=True)
                embed.add_field(name="Winner", value=f"#{winning_horse} {horse_names[winning_horse - 1]}", inline=True)
                embed.add_field(name="Lost", value=f"**{amount_parsed}** points", inline=True)
                embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                embed.set_image(url=LOSS_IMAGES['horse'])
                await interaction.edit_original_response(embed=embed)
            
            await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
        
        @discord.ui.button(label='Horse 1 ⚡', style=discord.ButtonStyle.primary, emoji='🐴', row=0)
        async def horse1(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.select_horse(interaction, 1)
        
        @discord.ui.button(label='Horse 2 🔥', style=discord.ButtonStyle.primary, emoji='🐎', row=0)
        async def horse2(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.select_horse(interaction, 2)
        
        @discord.ui.button(label='Horse 3 💎', style=discord.ButtonStyle.primary, emoji='🏇', row=0)
        async def horse3(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.select_horse(interaction, 3)
        
        @discord.ui.button(label='Horse 4 🌟', style=discord.ButtonStyle.success, emoji='🦄', row=1)
        async def horse4(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.select_horse(interaction, 4)
        
        @discord.ui.button(label='Horse 5 🏆', style=discord.ButtonStyle.success, emoji='🐴', row=1)
        async def horse5(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.select_horse(interaction, 5)
        
        @discord.ui.button(label='Horse 6 👑', style=discord.ButtonStyle.success, emoji='🐎', row=1)
        async def horse6(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.select_horse(interaction, 6)
    
    view = HorseView()
    embed = discord.Embed(title="🐴 Horse Racing", description="Pick your horse and watch them race!\n\n**Horses:**\n🐴 #1 ⚡ Lightning\n🐎 #2 🔥 Flame\n🏇 #3 💎 Diamond\n🦄 #4 🌟 Star\n🐴 #5 🏆 Champion\n🐎 #6 👑 Royal", color=0xFFD700)
    embed.add_field(name="Bet", value=f"**{amount_parsed}** points", inline=True)
    embed.add_field(name="Win Multiplier", value="**2.2x**", inline=True)
    await ctx.send(embed=embed, view=view)

@require_guild()
@bot.command()
@cooldown_check()
async def hilo(ctx, amount: str):
    """HiLo - Guess if the next card is higher or lower!"""
    user_id = ctx.author.id
    
    # Check daily play limit
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'hilo')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **hilo** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    await db.update_balance(user_id, -amount, "HiLo bet")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_hilo")
    
    # Start with first card
    current_card = random.randint(2, 14)  # 2-10, 11=J, 12=Q, 13=K, 14=A
    
    def card_name(value):
        if value == 11: return "J"
        elif value == 12: return "Q"
        elif value == 13: return "K"
        elif value == 14: return "A"
        else: return str(value)
    
    class HiLoView(discord.ui.View):
        def __init__(self, current_card, bet_amount):
            super().__init__(timeout=60)
            self.current_card = current_card
            self.bet_amount = bet_amount
            self.multiplier = 1.0
            self.rounds = 0
            
        @discord.ui.button(label="⬆ Higher", style=discord.ButtonStyle.success)
        async def higher_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ Not your game!", ephemeral=True)
                return
            
            # Defer interaction to prevent timeout
            await safe_defer(interaction)
            await self.play_round(interaction, "higher")
        
        @discord.ui.button(label="⬇ Lower", style=discord.ButtonStyle.danger)
        async def lower_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ Not your game!", ephemeral=True)
                return
            
            # Defer interaction to prevent timeout
            await safe_defer(interaction)
            await self.play_round(interaction, "lower")
        
        @discord.ui.button(label="💰 Cash Out", style=discord.ButtonStyle.primary)
        async def cashout_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ Not your game!", ephemeral=True)
                return
            
            if self.rounds == 0:
                await interaction.response.send_message("❌ You must play at least one round before cashing out!", ephemeral=True)
                return
            
            # Defer interaction to prevent timeout
            await safe_defer(interaction)
            
            is_vip = await db.is_vip(user_id)
            boost_multiplier = await db.get_total_boost_multiplier(user_id)
            final_multiplier = self.multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
            win_amount = int(self.bet_amount * final_multiplier)
            
            await db.update_balance(user_id, win_amount, f"HiLo cashout: {final_multiplier:.2f}x")
            await db.record_win(user_id, "HILO", self.bet_amount, win_amount, final_multiplier)
            await db.update_user_stats(user_id, won=True)
            
            embed = discord.Embed(title="📈 HiLo - CASHED OUT!", description=f"You played **{self.rounds}** rounds!", color=0xFFD700)
            embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
            embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
            embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
            embed.set_image(url=WIN_IMAGES['hilo'])
            await safe_interaction_response(interaction, embed=embed, view=None)
            
            await WinLogger.log_win(ctx.author, "HILO", self.bet_amount, win_amount, final_multiplier,
                                   details=f"Cashed out after {self.rounds} rounds")
            self.stop()
        
        async def play_round(self, interaction, choice):
            next_card = random.randint(2, 14)
            
            if (choice == "higher" and next_card > self.current_card) or (choice == "lower" and next_card < self.current_card):
                # Correct guess
                self.rounds += 1
                self.multiplier += 0.5  # +0.5x per correct guess
                self.current_card = next_card
                
                embed = discord.Embed(title="📈 HiLo - Correct!", description=f"Next card: **{card_name(next_card)}**", color=0x00ff00)
                embed.add_field(name="Round", value=f"{self.rounds}", inline=True)
                embed.add_field(name="Current Multiplier", value=f"{self.multiplier:.1f}x", inline=True)
                embed.add_field(name="Current Card", value=f"**{card_name(self.current_card)}**", inline=True)
                embed.set_footer(text="Guess again or cash out!")
                await safe_interaction_response(interaction, embed=embed, view=self)
            else:
                # Wrong guess - LOST
                await db.update_user_stats(user_id, won=False)
                
                embed = discord.Embed(title="📈 HiLo - LOST!", description=f"Next card: **{card_name(next_card)}** 💥", color=0xff0000)
                embed.add_field(name="Rounds Survived", value=f"{self.rounds}", inline=True)
                embed.add_field(name="Lost", value=f"**{self.bet_amount}** points", inline=True)
                embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                embed.set_image(url=LOSS_IMAGES['hilo'])
                await safe_interaction_response(interaction, embed=embed, view=None)
                self.stop()
    
    view = HiLoView(current_card, amount)
    embed = discord.Embed(title="📈 HiLo - Start!", description="Guess if the next card is higher or lower!", color=0x3498db)
    embed.add_field(name="Current Card", value=f"**{card_name(current_card)}**", inline=True)
    embed.add_field(name="Multiplier", value="1.0x", inline=True)
    embed.set_footer(text="Each correct guess adds +0.5x!")
    await ctx.send(embed=embed, view=view)
    
    # Show remaining plays
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

@require_guild()
@bot.command()
@cooldown_check()
async def crash(ctx, amount: str, cashout: float):
    """Crash - Bet on when the multiplier will crash! (Cashout between 1.01x - 5x)"""
    user_id = ctx.author.id
    
    # Check daily play limit
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'crash')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **crash** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    if cashout < 1.01 or cashout > 5.0:
        await ctx.send("❌ Cashout must be between 1.01x and 5.0x!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount, f"Crash bet: {cashout:.2f}x")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_crash")
    
    # REBALANCED: Crash with INCREASED house edge
    house_edge = 0.10  # INCREASED to 0.10 (10% house edge)
    e = random.random()
    crash_point = (99 / (100 * (1 - e) - house_edge * 100))
    crash_point = max(1.00, min(crash_point, 5.50))
    crash_point = round(crash_point, 2)
    
    # Generate crash graph image
    crash_image = await generate_crash_image(crash_point, cashout, crash_point >= cashout)
    
    if crash_point >= cashout:
        # WIN
        final_multiplier = cashout * (1.15 if is_vip else 1.0) * boost_multiplier
        win_amount = int(amount * final_multiplier)
        
        await db.update_balance(user_id, win_amount, f"Crash win: {final_multiplier:.2f}x")
        await db.record_win(user_id, "CRASH", amount, win_amount, final_multiplier)
        await db.update_user_stats(user_id, won=True)
        
        embed = discord.Embed(title="🎈 Crash - WON!", description=f"Cashed out at **{cashout:.2f}x** before crash!", color=0x00ff00)
        embed.add_field(name="Cashout", value=f"{cashout:.2f}x", inline=True)
        embed.add_field(name="Crashed At", value=f"{crash_point:.2f}x", inline=True)
        embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        
        if crash_image:
            embed.set_image(url="attachment://crash.png")
            file = discord.File(crash_image, filename="crash.png")
            await ctx.send(embed=embed, file=file)
        else:
            embed.set_image(url=WIN_IMAGES['crash'])
            await ctx.send(embed=embed)
        
        await WinLogger.log_win(ctx.author, "CRASH", amount, win_amount, final_multiplier,
                               details=f"Cashout: {cashout:.2f}x, Crash: {crash_point:.2f}x")
    else:
        # LOST
        await db.update_user_stats(user_id, won=False)
        embed = discord.Embed(title="🎈 Crash - LOST!", description=f"Crashed at **{crash_point:.2f}x** before cashout! 💥", color=0xff0000)
        embed.add_field(name="Target Cashout", value=f"{cashout:.2f}x", inline=True)
        embed.add_field(name="Crashed At", value=f"{crash_point:.2f}x", inline=True)
        embed.add_field(name="Lost", value=f"**{amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        
        if crash_image:
            embed.set_image(url="attachment://crash.png")
            file = discord.File(crash_image, filename="crash.png")
            await ctx.send(embed=embed, file=file)
        else:
            embed.set_image(url=LOSS_IMAGES['crash'])
            await ctx.send(embed=embed)
    
    # Show remaining plays
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

@require_guild()
@bot.command()
@cooldown_check()
async def rps(ctx, amount: str, choice: str):
    """Rock Paper Scissors - Beat the bot! (rock/paper/scissors)"""
    user_id = ctx.author.id
    
    # Check daily play limit
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'rps')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **rps** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    choice = choice.lower()
    if choice not in ['rock', 'paper', 'scissors']:
        await ctx.send("❌ Choice must be: rock, paper, or scissors!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount, f"RPS bet: {choice}")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_rps")
    
    bot_choice = random.choice(['rock', 'paper', 'scissors'])
    
    emoji_map = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}
    
    # Determine winner
    if choice == bot_choice:
        # TIE - refund
        await db.update_balance(user_id, amount, "RPS tie (refund)")
        embed = discord.Embed(title="✂️ Rock Paper Scissors - TIE!", description="It's a tie! Bet refunded.", color=0xFFD700)
        embed.add_field(name="Your Choice", value=f"{emoji_map[choice]} {choice.upper()}", inline=True)
        embed.add_field(name="Bot Choice", value=f"{emoji_map[bot_choice]} {bot_choice.upper()}", inline=True)
        embed.add_field(name="Refunded", value=f"**{amount}** points", inline=True)
        await ctx.send(embed=embed)
    elif (choice == 'rock' and bot_choice == 'scissors') or \
         (choice == 'paper' and bot_choice == 'rock') or \
         (choice == 'scissors' and bot_choice == 'paper'):
        # WIN
        base_multiplier = 2.0
        final_multiplier = base_multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
        win_amount = int(amount * final_multiplier)
        
        await db.update_balance(user_id, win_amount, f"RPS win: {final_multiplier:.2f}x")
        await db.record_win(user_id, "RPS", amount, win_amount, final_multiplier)
        await db.update_user_stats(user_id, won=True)
        
        embed = discord.Embed(title="✂️ Rock Paper Scissors - WON!", description="You beat the bot!", color=0x00ff00)
        embed.add_field(name="Your Choice", value=f"{emoji_map[choice]} {choice.upper()}", inline=True)
        embed.add_field(name="Bot Choice", value=f"{emoji_map[bot_choice]} {bot_choice.upper()}", inline=True)
        embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
        embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=WIN_IMAGES['rps'])
        await ctx.send(embed=embed)
        
        await WinLogger.log_win(ctx.author, "RPS", amount, win_amount, final_multiplier,
                               details=f"{choice} beats {bot_choice}")
    else:
        # LOST
        await db.update_user_stats(user_id, won=False)
        embed = discord.Embed(title="✂️ Rock Paper Scissors - LOST!", description="The bot won! 💥", color=0xff0000)
        embed.add_field(name="Your Choice", value=f"{emoji_map[choice]} {choice.upper()}", inline=True)
        embed.add_field(name="Bot Choice", value=f"{emoji_map[bot_choice]} {bot_choice.upper()}", inline=True)
        embed.add_field(name="Lost", value=f"**{amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=LOSS_IMAGES['rps'])
        await ctx.send(embed=embed)
    
    # Show remaining plays
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

@require_guild()
@bot.command()
@cooldown_check()
async def gtn(ctx, amount: str, guess: int):
    """Guess The Number - Guess a number between 1-100!"""
    user_id = ctx.author.id
    
    # Check daily play limit
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'gtn')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **gtn** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    if guess < 1 or guess > 100:
        await ctx.send("❌ Guess must be between 1 and 100!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount, f"GTN bet: {guess}")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_gtn")
    
    number = random.randint(1, 100)
    difference = abs(number - guess)
    
    # Exact match - huge win
    if difference == 0:
        base_multiplier = 99.0
        final_multiplier = base_multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
        win_amount = int(amount * final_multiplier)
        
        await db.update_balance(user_id, win_amount, f"GTN exact match: {final_multiplier:.2f}x")
        await db.record_win(user_id, "GTN", amount, win_amount, final_multiplier)
        await db.update_user_stats(user_id, won=True)
        
        embed = discord.Embed(title="🔢 Guess The Number - EXACT!", description=f"**JACKPOT!** You guessed **{number}** exactly!", color=0xFFD700)
        embed.add_field(name="Your Guess", value=f"{guess}", inline=True)
        embed.add_field(name="Number", value=f"{number}", inline=True)
        embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
        embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=WIN_IMAGES['gtn'])
        await ctx.send(embed=embed)
        
        await WinLogger.log_win(ctx.author, "GTN", amount, win_amount, final_multiplier,
                               details=f"Exact match: {number}")
    # Close guesses get smaller payouts
    elif difference <= 5:
        base_multiplier = 3.0
        final_multiplier = base_multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
        win_amount = int(amount * final_multiplier)
        
        await db.update_balance(user_id, win_amount, f"GTN close: {final_multiplier:.2f}x")
        await db.record_win(user_id, "GTN", amount, win_amount, final_multiplier)
        await db.update_user_stats(user_id, won=True)
        
        embed = discord.Embed(title="🔢 Guess The Number - CLOSE!", description=f"Very close! Number was **{number}**", color=0x00ff00)
        embed.add_field(name="Your Guess", value=f"{guess}", inline=True)
        embed.add_field(name="Number", value=f"{number}", inline=True)
        embed.add_field(name="Difference", value=f"{difference}", inline=True)
        embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
        embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=WIN_IMAGES['gtn'])
        await ctx.send(embed=embed)
        
        await WinLogger.log_win(ctx.author, "GTN", amount, win_amount, final_multiplier,
                               details=f"Close: {number}, diff: {difference}")
    elif difference <= 10:
        base_multiplier = 3.0
        final_multiplier = base_multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
        win_amount = int(amount * final_multiplier)
        
        await db.update_balance(user_id, win_amount, f"GTN near: {final_multiplier:.2f}x")
        await db.record_win(user_id, "GTN", amount, win_amount, final_multiplier)
        await db.update_user_stats(user_id, won=True)
        
        embed = discord.Embed(title="🔢 Guess The Number - NEAR!", description=f"Pretty close! Number was **{number}**", color=0x00ff00)
        embed.add_field(name="Your Guess", value=f"{guess}", inline=True)
        embed.add_field(name="Number", value=f"{number}", inline=True)
        embed.add_field(name="Difference", value=f"{difference}", inline=True)
        embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
        embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=WIN_IMAGES['gtn'])
        await ctx.send(embed=embed)
        
        await WinLogger.log_win(ctx.author, "GTN", amount, win_amount, final_multiplier,
                               details=f"Near: {number}, diff: {difference}")
    else:
        # LOST
        await db.update_user_stats(user_id, won=False)
        embed = discord.Embed(title="🔢 Guess The Number - LOST!", description=f"Number was **{number}** 💥", color=0xff0000)
        embed.add_field(name="Your Guess", value=f"{guess}", inline=True)
        embed.add_field(name="Number", value=f"{number}", inline=True)
        embed.add_field(name="Difference", value=f"{difference}", inline=True)
        embed.add_field(name="Lost", value=f"**{amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_footer(text="Try to get within 10 to win!")
        embed.set_image(url=LOSS_IMAGES['gtn'])
        await ctx.send(embed=embed)
    
    # Show remaining plays
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

@require_guild()
@bot.command(aliases=['case'])
@cooldown_check()
async def caseopen(ctx, amount: str):
    """Case Opening - Choose 1 of 7 boxes to open!"""
    user_id = ctx.author.id
    
    # Check daily play limit
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'case')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **case** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount, "Case opening")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_case")
    
    # Case items with rarities and multipliers (balanced)
    item_pool = [
        ("🟫 Common Item", 0.5, 45),
        ("🟦 Uncommon Item", 0.8, 25),
        ("🟪 Rare Item", 1.2, 15),
        ("🟥 Epic Item", 1.8, 10),
        ("🟧 Legendary Item", 2.5, 4),
        ("✨ Mythic Item", 3.2, 0.9),
        ("💎 Exotic Item", 4.0, 0.1)
    ]
    
    # Generate 7 boxes with preset items (weighted random for each)
    boxes = []
    for i in range(7):
        item_names = [item[0] for item in item_pool]
        multipliers = [item[1] for item in item_pool]
        weights = [item[2] for item in item_pool]
        
        selected_index = random.choices(range(len(item_pool)), weights=weights)[0]
        boxes.append({
            'name': item_names[selected_index],
            'multiplier': multipliers[selected_index]
        })
    
    class CaseOpenView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.create_buttons()
        
        def create_buttons(self):
            self.clear_items()
            
            # Create 7 box buttons
            for i in range(7):
                button = discord.ui.Button(
                    label=f'📦 Box {i+1}',
                    style=discord.ButtonStyle.primary,
                    custom_id=f'box_{i}'
                )
                button.callback = self.make_box_callback(i)
                self.add_item(button)
        
        def make_box_callback(self, box_number):
            async def box_callback(interaction: discord.Interaction):
                if interaction.user.id != user_id:
                    await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                    return
                
                # Get the item from the chosen box
                chosen_box = boxes[box_number]
                item_name = chosen_box['name']
                base_multiplier = chosen_box['multiplier']
                
                final_multiplier = base_multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
                
                if base_multiplier >= 1.0:
                    # WIN
                    win_amount = int(amount * final_multiplier)
                    
                    await db.update_balance(user_id, win_amount, f"Case win: {final_multiplier:.2f}x")
                    await db.record_win(user_id, "CASE", amount, win_amount, final_multiplier)
                    await db.update_user_stats(user_id, won=True)
                    
                    embed = discord.Embed(
                        title="📦 Case Opening - WON! 🎉",
                        description=f"You chose **Box {box_number + 1}** and unboxed:\n**{item_name}**!",
                        color=0x00ff00
                    )
                    embed.add_field(name="Item", value=item_name, inline=True)
                    embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
                    embed.add_field(name="Won", value=f"**{win_amount:,}** points", inline=True)
                    embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                    embed.set_image(url=WIN_IMAGES['case'])
                    await safe_interaction_response(interaction, embed=embed, view=None)
                    
                    await WinLogger.log_win(ctx.author, "CASE", amount, win_amount, final_multiplier,
                                           details=f"Box {box_number + 1}: {item_name}")
                    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
                else:
                    # LOST (common/uncommon item with < 1x multiplier)
                    await db.update_user_stats(user_id, won=False)
                    
                    embed = discord.Embed(
                        title="📦 Case Opening - LOST",
                        description=f"You chose **Box {box_number + 1}** and unboxed:\n**{item_name}** 💥",
                        color=0xff0000
                    )
                    embed.add_field(name="Item", value=item_name, inline=True)
                    embed.add_field(name="Value", value=f"{base_multiplier:.2f}x (worth less than case)", inline=True)
                    embed.add_field(name="Lost", value=f"**{amount:,}** points", inline=True)
                    embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                    embed.set_image(url=LOSS_IMAGES['case'])
                    await safe_interaction_response(interaction, embed=embed, view=None)
                    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
            
            return box_callback
    
    view = CaseOpenView()
    embed = discord.Embed(
        title="📦 Case Opening - Choose a Box!",
        description=f"**Choose 1 of 7 boxes to open!**\n\nBet: **{amount:,}** points\n\n💎 Exotic: **4.0x** | ✨ Mythic: **3.2x** | 🟧 Legendary: **2.5x**\n🟥 Epic: **1.8x** | 🟪 Rare: **1.2x** | 🟦 Uncommon: **0.8x** | 🟫 Common: **0.5x**",
        color=0x3498db
    )
    await ctx.send(embed=embed, view=view)

@require_guild()
@bot.command()
@cooldown_check()
async def baccarat(ctx, amount: str = None, bet: str = None):
    """Baccarat - Bet on Player, Banker, or Tie! (player/banker/tie)"""
    user_id = ctx.author.id
    
    # Check if parameters are missing
    if amount is None or bet is None:
        embed = discord.Embed(title="🎴 Baccarat - How to Play", color=0x3498db)
        embed.add_field(name="Usage", value="`.baccarat <amount> <bet>`", inline=False)
        embed.add_field(name="Bet Options", value="**player** | **banker** | **tie**", inline=False)
        embed.add_field(name="Examples", value="`.baccarat 100 player`\n`.baccarat 500 banker`\n`.baccarat 50 tie`", inline=False)
        embed.add_field(name="Payouts", value="🎴 **Player**: 2.0x\n🏦 **Banker**: 1.95x\n🎲 **Tie**: 8.0x", inline=False)
        return await ctx.send(embed=embed)
    
    # Check daily play limit
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'baccarat')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **baccarat** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    bet = bet.lower()
    if bet not in ['player', 'banker', 'tie']:
        await ctx.send("❌ Bet must be: player, banker, or tie!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount, f"Baccarat bet: {bet}")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_baccarat")
    
    # Deal cards - generate actual card strings for visual display
    def generate_card():
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        suits = ['♠', '♥', '♦', '♣']
        return f"{random.choice(ranks)}{random.choice(suits)}"
    
    def card_value(card_str):
        rank = card_str[:-1]
        if rank in ['J', 'Q', 'K']:
            return 0  # Face cards worth 0 in Baccarat
        elif rank == 'A':
            return 1
        else:
            return int(rank) % 10
    
    player_cards = [generate_card(), generate_card()]
    banker_cards = [generate_card(), generate_card()]
    
    player_total = (card_value(player_cards[0]) + card_value(player_cards[1])) % 10
    banker_total = (card_value(banker_cards[0]) + card_value(banker_cards[1])) % 10
    
    # Determine winner
    if player_total > banker_total:
        winner = "player"
    elif banker_total > player_total:
        winner = "banker"
    else:
        winner = "tie"
    
    # Generate card image
    card_image = await generate_baccarat_image(player_cards, banker_cards)
    
    # Calculate winnings
    if bet == winner:
        if bet == "tie":
            base_multiplier = 8.0
        elif bet == "player":
            base_multiplier = 2.0
        else:  # banker
            base_multiplier = 1.95  # Banker pays slightly less due to statistical advantage
        
        final_multiplier = base_multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
        win_amount = int(amount * final_multiplier)
        
        await db.update_balance(user_id, win_amount, f"Baccarat win: {final_multiplier:.2f}x")
        await db.record_win(user_id, "BACCARAT", amount, win_amount, final_multiplier)
        await db.update_user_stats(user_id, won=True)
        
        embed = discord.Embed(title="🎴 Baccarat - WON!", description=f"**{winner.upper()}** wins!", color=0x00ff00)
        embed.add_field(name="Player Cards", value=f"{', '.join(player_cards)} ({player_total} points)", inline=True)
        embed.add_field(name="Banker Cards", value=f"{', '.join(banker_cards)} ({banker_total} points)", inline=True)
        embed.add_field(name="Your Bet", value=bet.upper(), inline=True)
        embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
        embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        
        if card_image:
            embed.set_image(url="attachment://baccarat.png")
            file = discord.File(card_image, filename="baccarat.png")
            await ctx.send(embed=embed, file=file)
        else:
            embed.set_image(url=WIN_IMAGES['baccarat'])
            await ctx.send(embed=embed)
        
        await WinLogger.log_win(ctx.author, "BACCARAT", amount, win_amount, final_multiplier,
                               details=f"Bet: {bet}, Winner: {winner}")
    else:
        # LOST
        await db.update_user_stats(user_id, won=False)
        embed = discord.Embed(title="🎴 Baccarat - LOST!", description=f"**{winner.upper()}** wins! 💥", color=0xff0000)
        embed.add_field(name="Player Cards", value=f"{', '.join(player_cards)} ({player_total} points)", inline=True)
        embed.add_field(name="Banker Cards", value=f"{', '.join(banker_cards)} ({banker_total} points)", inline=True)
        embed.add_field(name="Your Bet", value=bet.upper(), inline=True)
        embed.add_field(name="Lost", value=f"**{amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        
        if card_image:
            embed.set_image(url="attachment://baccarat.png")
            file = discord.File(card_image, filename="baccarat.png")
            await ctx.send(embed=embed, file=file)
        else:
            embed.set_image(url=LOSS_IMAGES['baccarat'])
            await ctx.send(embed=embed)
    
    # Show remaining plays
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

@require_guild()
@bot.command()
@cooldown_check()
async def wheel(ctx, amount: str):
    """Spin The Wheel - Spin for random multipliers!"""
    user_id = ctx.author.id
    
    # Check daily play limit
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'wheel')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **wheel** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount, "Wheel spin")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_wheel")
    
    # REBALANCED: Wheel reduced RTP to 88% (multipliers reduced, BUST weight increased)
    segments = [
        ("💥 BUST", 0.0, 50),  # INCREASED: More busts (was 40)
        ("🔵 0.2x", 0.2, 22),  # REDUCED weight
        ("🟢 0.4x", 0.4, 15),  # REDUCED weight
        ("🟡 0.6x", 0.6, 8),   # REDUCED weight
        ("🟠 0.8x", 0.8, 4),   # INCREASED slightly
        ("💎 1.0x", 1.0, 1)    # REDUCED (was 2)
    ]
    
    segment_names = [s[0] for s in segments]
    multipliers = [s[1] for s in segments]
    weights = [s[2] for s in segments]
    
    selected_index = random.choices(range(len(segments)), weights=weights)[0]
    segment_name = segment_names[selected_index]
    base_multiplier = multipliers[selected_index]
    
    if base_multiplier > 0:
        final_multiplier = base_multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
        win_amount = int(amount * final_multiplier)
        
        await db.update_balance(user_id, win_amount, f"Wheel win: {final_multiplier:.2f}x")
        await db.record_win(user_id, "WHEEL", amount, win_amount, final_multiplier)
        await db.update_user_stats(user_id, won=True)
        
        embed = discord.Embed(title="🎡 Spin The Wheel - WON!", description=f"Landed on: **{segment_name}**!", color=0x00ff00)
        embed.add_field(name="Segment", value=segment_name, inline=True)
        embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
        embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=WIN_IMAGES['wheel'])
        await ctx.send(embed=embed)
        
        await WinLogger.log_win(ctx.author, "WHEEL", amount, win_amount, final_multiplier,
                               details=f"Segment: {segment_name}")
    else:
        # BUST - total loss
        await db.update_user_stats(user_id, won=False)
        embed = discord.Embed(title="🎡 Spin The Wheel - BUST!", description=f"Landed on: **{segment_name}** 💥", color=0xff0000)
        embed.add_field(name="Segment", value=segment_name, inline=True)
        embed.add_field(name="Lost", value=f"**{amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=LOSS_IMAGES['wheel'])
        await ctx.send(embed=embed)
    
    # Show remaining plays
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

# ========== 12 NEW CASINO GAMES ==========

@require_guild()
@bot.command()
@cooldown_check()
async def blackjackdice(ctx, amount: str):
    """Blackjack Dice - Reach 21 using dice (1-6) without going over!"""
    user_id = ctx.author.id
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'blackjackdice')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **blackjackdice** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount, "Blackjack Dice bet")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_blackjackdice")
    
    player_total = 0
    dealer_total = 0
    game_over = False
    
    first_roll = random.randint(1, 6)
    player_total = first_roll
    
    class BlackjackDiceView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.value = None
        
        @discord.ui.button(label='🎲 Hit', style=discord.ButtonStyle.success)
        async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            nonlocal player_total, game_over
            
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            # Defer interaction to prevent timeout
            await safe_defer(interaction)
            
            new_roll = random.randint(1, 6)
            player_total += new_roll
            
            if player_total > 21:
                game_over = True
                await db.update_user_stats(user_id, won=False)
                embed = discord.Embed(title="🎲 Blackjack Dice - BUST!", description=f"You rolled **{new_roll}** and went over 21!", color=0xff0000)
                embed.add_field(name="Your Total", value=f"**{player_total}** 💥", inline=True)
                embed.add_field(name="Lost", value=f"**{amount}** points", inline=True)
                embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                embed.set_image(url=LOSS_IMAGES['blackjack'])
                await safe_interaction_response(interaction, embed=embed, view=None)
                await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
            elif player_total == 21:
                game_over = True
                multiplier = 2.5 * (1.15 if is_vip else 1.0) * boost_multiplier
                win_amount = int(amount * multiplier)
                
                await db.update_balance(user_id, win_amount, f"Blackjack Dice win: {multiplier:.2f}x")
                await db.record_win(user_id, "BLACKJACKDICE", amount, win_amount, multiplier)
                await db.update_user_stats(user_id, won=True)
                
                embed = discord.Embed(title="🎲 Blackjack Dice - BLACKJACK! 🎉", description=f"You hit exactly **21**!", color=0xffd700)
                embed.add_field(name="Your Total", value=f"**{player_total}**", inline=True)
                embed.add_field(name="Multiplier", value=f"**{multiplier:.2f}x**", inline=True)
                embed.add_field(name="Won", value=f"**{win_amount}** points! 🎉", inline=True)
                embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                embed.set_image(url=WIN_IMAGES['blackjack'])
                await safe_interaction_response(interaction, embed=embed, view=None)
                
                await WinLogger.log_win(ctx.author, "BLACKJACKDICE", amount, win_amount, multiplier,
                                       details=f"Blackjack! Total: {player_total}")
                await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
            else:
                embed = discord.Embed(title="🎲 Blackjack Dice", description=f"You rolled **{new_roll}**", color=0x3498db)
                embed.add_field(name="Your Total", value=f"**{player_total}**/21", inline=True)
                await safe_interaction_response(interaction, embed=embed, view=self)
        
        @discord.ui.button(label='🛑 Stand', style=discord.ButtonStyle.primary)
        async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            nonlocal dealer_total, game_over
            
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            # Defer interaction to prevent timeout
            await safe_defer(interaction)
            
            game_over = True
            
            while dealer_total < 17:
                dealer_total += random.randint(1, 6)
            
            if dealer_total > 21 or player_total > dealer_total:
                multiplier = 2.0 * (1.15 if is_vip else 1.0) * boost_multiplier
                win_amount = int(amount * multiplier)
                
                await db.update_balance(user_id, win_amount, f"Blackjack Dice win: {multiplier:.2f}x")
                await db.record_win(user_id, "BLACKJACKDICE", amount, win_amount, multiplier)
                await db.update_user_stats(user_id, won=True)
                
                embed = discord.Embed(title="🎲 Blackjack Dice - WON! 🎉", description=f"You beat the dealer!", color=0x00ff00)
                embed.add_field(name="Your Total", value=f"**{player_total}**", inline=True)
                embed.add_field(name="Dealer Total", value=f"**{dealer_total}**", inline=True)
                embed.add_field(name="Multiplier", value=f"**{multiplier:.2f}x**", inline=True)
                embed.add_field(name="Won", value=f"**{win_amount}** points! 🎉", inline=True)
                embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                embed.set_image(url=WIN_IMAGES['blackjack'])
                await safe_interaction_response(interaction, embed=embed, view=None)
                
                await WinLogger.log_win(ctx.author, "BLACKJACKDICE", amount, win_amount, multiplier,
                                       details=f"Player: {player_total}, Dealer: {dealer_total}")
            elif player_total == dealer_total:
                await db.update_balance(user_id, amount, "Blackjack Dice push")
                embed = discord.Embed(title="🎲 Blackjack Dice - PUSH", description="It's a tie! Bet refunded.", color=0xffff00)
                embed.add_field(name="Your Total", value=f"**{player_total}**", inline=True)
                embed.add_field(name="Dealer Total", value=f"**{dealer_total}**", inline=True)
                embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                await safe_interaction_response(interaction, embed=embed, view=None)
            else:
                await db.update_user_stats(user_id, won=False)
                embed = discord.Embed(title="🎲 Blackjack Dice - LOST", description="Dealer wins!", color=0xff0000)
                embed.add_field(name="Your Total", value=f"**{player_total}**", inline=True)
                embed.add_field(name="Dealer Total", value=f"**{dealer_total}**", inline=True)
                embed.add_field(name="Lost", value=f"**{amount}** points", inline=True)
                embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                embed.set_image(url=LOSS_IMAGES['blackjack'])
                await safe_interaction_response(interaction, embed=embed, view=None)
            
            await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
    
    view = BlackjackDiceView()
    embed = discord.Embed(title="🎲 Blackjack Dice", description=f"First roll: **{first_roll}**", color=0x3498db)
    embed.add_field(name="Your Total", value=f"**{player_total}**/21", inline=True)
    embed.add_field(name="Goal", value="Get to 21 without going over!", inline=True)
    await ctx.send(embed=embed, view=view)

@require_guild()
@bot.command()
@cooldown_check()
async def cards(ctx, amount: str):
    """Cards - Draw a random card with multiplier (0.5x to 10x)!"""
    user_id = ctx.author.id
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'cards')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **cards** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount, "Cards bet")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_cards")
    
    card_multipliers = [
        (0.5, '🃏 Joker', 30),
        (0.8, '🂡 Ace of Spades', 20),
        (1.0, '🂮 King', 15),
        (1.5, '🂭 Queen', 12),
        (2.0, '🂻 Jack', 10),
        (3.0, '💎 Diamond', 5),
        (5.0, '❤️ Heart', 3),
        (7.5, '♠️ Spade', 2),
        (10.0, '🎴 Royal Flush', 1)
    ]
    
    multipliers = [c[0] for c in card_multipliers]
    card_names = [c[1] for c in card_multipliers]
    weights = [c[2] for c in card_multipliers]
    
    selected_index = random.choices(range(len(card_multipliers)), weights=weights)[0]
    base_multiplier = multipliers[selected_index]
    card_name = card_names[selected_index]
    
    final_multiplier = base_multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
    
    if base_multiplier >= 1.0:
        win_amount = int(amount * final_multiplier)
        
        await db.update_balance(user_id, win_amount, f"Cards win: {final_multiplier:.2f}x")
        await db.record_win(user_id, "CARDS", amount, win_amount, final_multiplier)
        await db.update_user_stats(user_id, won=True)
        
        embed = discord.Embed(title="🎴 Cards - WON!", description=f"You drew: **{card_name}**!", color=0x00ff00)
        embed.add_field(name="Card", value=card_name, inline=True)
        embed.add_field(name="Multiplier", value=f"**{final_multiplier:.2f}x**", inline=True)
        embed.add_field(name="Won", value=f"**{win_amount}** points! 🎉", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=WIN_IMAGES['cards'])
        await ctx.send(embed=embed)
        
        await WinLogger.log_win(ctx.author, "CARDS", amount, win_amount, final_multiplier,
                               details=f"Card: {card_name}")
    else:
        await db.update_user_stats(user_id, won=False)
        loss_amount = int(amount * (1 - base_multiplier))
        partial_return = amount - loss_amount
        
        await db.update_balance(user_id, partial_return, f"Cards partial return: {base_multiplier:.2f}x")
        
        embed = discord.Embed(title="🎴 Cards - LOST", description=f"You drew: **{card_name}**", color=0xff0000)
        embed.add_field(name="Card", value=card_name, inline=True)
        embed.add_field(name="Multiplier", value=f"**{base_multiplier:.2f}x**", inline=True)
        embed.add_field(name="Lost", value=f"**{loss_amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=LOSS_IMAGES['cards'])
        await ctx.send(embed=embed)
    
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

@require_guild()
@bot.command()
@cooldown_check()
async def classicdice(ctx, amount: str):
    """Classic Dice - Roll 1d6 against the dealer!"""
    user_id = ctx.author.id
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'classicdice')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **classicdice** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount, "Classic Dice bet")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_classicdice")
    
    player_roll = random.randint(1, 6)
    dealer_roll = random.randint(1, 6)
    
    if player_roll > dealer_roll:
        multiplier = 2.0 * (1.15 if is_vip else 1.0) * boost_multiplier
        win_amount = int(amount * multiplier)
        
        await db.update_balance(user_id, win_amount, f"Classic Dice win: {multiplier:.2f}x")
        await db.record_win(user_id, "CLASSICDICE", amount, win_amount, multiplier)
        await db.update_user_stats(user_id, won=True)
        
        embed = discord.Embed(title="🎲 Classic Dice - WON!", description="You rolled higher than the dealer!", color=0x00ff00)
        embed.add_field(name="Your Roll", value=f"🎲 **{player_roll}**", inline=True)
        embed.add_field(name="Dealer Roll", value=f"🎲 **{dealer_roll}**", inline=True)
        embed.add_field(name="Multiplier", value=f"**{multiplier:.2f}x**", inline=True)
        embed.add_field(name="Won", value=f"**{win_amount}** points! 🎉", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=WIN_IMAGES['classicdice'])
        await ctx.send(embed=embed)
        
        await WinLogger.log_win(ctx.author, "CLASSICDICE", amount, win_amount, multiplier,
                               details=f"Player: {player_roll}, Dealer: {dealer_roll}")
    elif player_roll == dealer_roll:
        await db.update_balance(user_id, amount, "Classic Dice tie")
        embed = discord.Embed(title="🎲 Classic Dice - TIE", description="Same roll! Bet refunded.", color=0xffff00)
        embed.add_field(name="Your Roll", value=f"🎲 **{player_roll}**", inline=True)
        embed.add_field(name="Dealer Roll", value=f"🎲 **{dealer_roll}**", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        await ctx.send(embed=embed)
    else:
        await db.update_user_stats(user_id, won=False)
        embed = discord.Embed(title="🎲 Classic Dice - LOST", description="Dealer rolled higher!", color=0xff0000)
        embed.add_field(name="Your Roll", value=f"🎲 **{player_roll}**", inline=True)
        embed.add_field(name="Dealer Roll", value=f"🎲 **{dealer_roll}**", inline=True)
        embed.add_field(name="Lost", value=f"**{amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=LOSS_IMAGES['classicdice'])
        await ctx.send(embed=embed)
    
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

@require_guild()
@bot.command()
@cooldown_check()
async def chickenroad(ctx, amount: str):
    """Chicken Road - Help the chicken cross the road! (5 levels)"""
    user_id = ctx.author.id
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'chickenroad')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **chickenroad** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount, "Chicken Road bet")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_chickenroad")
    
    level = 0
    multipliers = [1.1, 1.3, 1.6, 2.0, 2.8]  # REBALANCED: Reduced (was [1.2, 1.5, 2.0, 2.5, 3.5])
    
    class ChickenRoadView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.level = 0
            self.game_over = False
            self.safe_lane = random.randint(1, 3)
        
        def create_level_buttons(self):
            self.clear_items()
            for i in range(1, 4):
                button = discord.ui.Button(label=f'Lane {i} 🐔', style=discord.ButtonStyle.primary, custom_id=f'lane_{i}')
                button.callback = self.make_lane_callback(i)
                self.add_item(button)
            
            cashout_button = discord.ui.Button(label=f'💰 Cash Out ({multipliers[self.level]:.1f}x)', style=discord.ButtonStyle.success)
            cashout_button.callback = self.cashout_callback
            self.add_item(cashout_button)
        
        def make_lane_callback(self, lane_num):
            async def lane_callback(interaction: discord.Interaction):
                if interaction.user.id != user_id:
                    await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                    return
                
                if lane_num == self.safe_lane:
                    self.level += 1
                    if self.level >= 5:
                        self.game_over = True
                        final_multiplier = multipliers[4] * (1.15 if is_vip else 1.0) * boost_multiplier
                        win_amount = int(amount * final_multiplier)
                        
                        await db.update_balance(user_id, win_amount, f"Chicken Road win: {final_multiplier:.2f}x")
                        await db.record_win(user_id, "CHICKENROAD", amount, win_amount, final_multiplier)
                        await db.update_user_stats(user_id, won=True)
                        
                        embed = discord.Embed(title="🐔 Chicken Road - WON! 🎉", description="Chicken crossed all 5 levels!", color=0x00ff00)
                        embed.add_field(name="Levels Completed", value="**5/5**", inline=True)
                        embed.add_field(name="Multiplier", value=f"**{final_multiplier:.2f}x**", inline=True)
                        embed.add_field(name="Won", value=f"**{win_amount}** points! 🎉", inline=True)
                        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                        embed.set_image(url=WIN_IMAGES['chickenroad'])
                        await safe_interaction_response(interaction, embed=embed, view=None)
                        
                        await WinLogger.log_win(ctx.author, "CHICKENROAD", amount, win_amount, final_multiplier,
                                               details=f"Completed all 5 levels")
                        await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
                    else:
                        self.safe_lane = random.randint(1, 3)
                        self.create_level_buttons()
                        embed = discord.Embed(title=f"🐔 Chicken Road - Level {self.level + 1}/5", 
                                             description=f"Safe! Choose next lane.", color=0x3498db)
                        embed.add_field(name="Current Multiplier", value=f"**{multipliers[self.level]:.1f}x**", inline=True)
                        await safe_interaction_response(interaction, embed=embed, view=self)
                else:
                    self.game_over = True
                    await db.update_user_stats(user_id, won=False)
                    embed = discord.Embed(title="🐔 Chicken Road - CRASH! 🚗", description="The chicken got hit by a car!", color=0xff0000)
                    embed.add_field(name="Levels Completed", value=f"**{self.level}/5**", inline=True)
                    embed.add_field(name="Lost", value=f"**{amount}** points", inline=True)
                    embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                    embed.set_image(url=LOSS_IMAGES['chickenroad'])
                    await safe_interaction_response(interaction, embed=embed, view=None)
                    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
            
            return lane_callback
        
        async def cashout_callback(self, interaction: discord.Interaction):
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            self.game_over = True
            final_multiplier = multipliers[self.level] * (1.15 if is_vip else 1.0) * boost_multiplier
            win_amount = int(amount * final_multiplier)
            
            await db.update_balance(user_id, win_amount, f"Chicken Road cashout: {final_multiplier:.2f}x")
            await db.record_win(user_id, "CHICKENROAD", amount, win_amount, final_multiplier)
            await db.update_user_stats(user_id, won=True)
            
            embed = discord.Embed(title="🐔 Chicken Road - CASHED OUT! 💰", description="You played it safe!", color=0x00ff00)
            embed.add_field(name="Levels Completed", value=f"**{self.level}/5**", inline=True)
            embed.add_field(name="Multiplier", value=f"**{final_multiplier:.2f}x**", inline=True)
            embed.add_field(name="Won", value=f"**{win_amount}** points! 🎉", inline=True)
            embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
            embed.set_image(url=WIN_IMAGES['chickenroad'])
            await safe_interaction_response(interaction, embed=embed, view=None)
            
            await WinLogger.log_win(ctx.author, "CHICKENROAD", amount, win_amount, final_multiplier,
                                   details=f"Cashed out at level {self.level}")
            await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
    
    view = ChickenRoadView()
    view.create_level_buttons()
    embed = discord.Embed(title="🐔 Chicken Road - Level 1/5", 
                         description="Choose a lane! Avoid the cars!", color=0x3498db)
    embed.add_field(name="Current Multiplier", value=f"**{multipliers[0]:.1f}x**", inline=True)
    await ctx.send(embed=embed, view=view)


@require_guild()
@bot.command()
@cooldown_check()
async def progressivecoinflip(ctx, amount: str):
    """Progressive Coinflip - Complete 5 rows for exponential rewards!"""
    user_id = ctx.author.id
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'progressivecoinflip')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **progressivecoinflip** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount, "Progressive Coinflip bet")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_progressivecoinflip")
    
    current_row = 1
    row_multipliers = {1: 1.5, 2: 2.25, 3: 3.375, 4: 5.06, 5: 7.59}
    
    class ProgressiveFlipView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=120)
            self.update_buttons()
        
        def update_buttons(self):
            self.clear_items()
            
            heads_button = discord.ui.Button(label='🟡 Heads', style=discord.ButtonStyle.primary, custom_id='heads')
            heads_button.callback = lambda i: self.flip(i, 'heads')
            self.add_item(heads_button)
            
            tails_button = discord.ui.Button(label='⚪ Tails', style=discord.ButtonStyle.primary, custom_id='tails')
            tails_button.callback = lambda i: self.flip(i, 'tails')
            self.add_item(tails_button)
            
            if current_row >= 2:
                cashout_button = discord.ui.Button(label='💰 Cash Out', style=discord.ButtonStyle.success, custom_id='cashout')
                cashout_button.callback = self.cashout
                self.add_item(cashout_button)
        
        async def cashout(self, interaction: discord.Interaction):
            nonlocal current_row
            
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            previous_row = current_row - 1
            row_mult = row_multipliers[previous_row]
            final_multiplier = row_mult * (1.15 if is_vip else 1.0) * boost_multiplier
            win_amount = int(amount * final_multiplier)
            
            await db.update_balance(user_id, win_amount, f"Progressive Flip cashout: {final_multiplier:.2f}x")
            await db.record_win(user_id, "PROGRESSIVECOINFLIP", amount, win_amount, final_multiplier)
            await db.update_user_stats(user_id, won=True)
            
            embed = discord.Embed(title="🪙 Progressive Coinflip - CASHED OUT! 💰", description="Smart play!", color=0x00ff00)
            embed.add_field(name="Rows Completed", value=f"**{previous_row}/5** ✅", inline=True)
            embed.add_field(name="Multiplier", value=f"**{final_multiplier:.2f}x**", inline=True)
            embed.add_field(name="Won", value=f"**{win_amount:,}** points! 🎉", inline=True)
            embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
            embed.set_image(url=WIN_IMAGES['progressivecoinflip'])
            await safe_interaction_response(interaction, embed=embed, view=None)
            
            await WinLogger.log_win(ctx.author, "PROGRESSIVECOINFLIP", amount, win_amount, final_multiplier,
                                   details=f"Rows: {previous_row}/5")
            await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
        
        async def flip(self, interaction: discord.Interaction, choice: str):
            nonlocal current_row
            
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            await safe_interaction_response(interaction, 
                embed=discord.Embed(
                    title=f"🪙 Progressive Coinflip - Row {current_row}/5",
                    description="🪙 **Flipping...**",
                    color=0xFFD700
                ),
                view=None
            )
            
            await asyncio.sleep(1.5)
            
            result = random.choice(['heads', 'tails'])
            emoji = '🟡' if result == 'heads' else '⚪'
            
            if result == choice:
                row_mult = row_multipliers[current_row]
                final_mult = row_mult * (1.15 if is_vip else 1.0) * boost_multiplier
                potential_win = int(amount * final_mult)
                
                if current_row == 5:
                    await db.update_balance(user_id, potential_win, f"Progressive Flip MAX WIN: {final_mult:.2f}x")
                    await db.record_win(user_id, "PROGRESSIVECOINFLIP", amount, potential_win, final_mult)
                    await db.update_user_stats(user_id, won=True)
                    
                    embed = discord.Embed(
                        title="🪙 Progressive Coinflip - JACKPOT! 🎰",
                        description=f"Result: **{result.upper()}** {emoji}\n\n🏆 **ALL 5 ROWS COMPLETED!** 🏆",
                        color=0xFFD700
                    )
                    embed.add_field(name="Rows", value="**5/5** ✅✅✅✅✅", inline=True)
                    embed.add_field(name="Multiplier", value=f"**{final_mult:.2f}x**", inline=True)
                    embed.add_field(name="Won", value=f"**{potential_win:,}** points! 🎉", inline=True)
                    embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                    embed.set_image(url=WIN_IMAGES['progressivecoinflip'])
                    await interaction.edit_original_response(embed=embed, view=None)
                    
                    await WinLogger.log_win(ctx.author, "PROGRESSIVECOINFLIP", amount, potential_win, final_mult,
                                           details="MAX WIN - 5/5 rows")
                    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
                else:
                    check_marks = "✅" * current_row + "⬜" * (5 - current_row)
                    current_row += 1
                    
                    embed = discord.Embed(
                        title=f"🪙 Progressive Coinflip - Row {current_row - 1} WIN!",
                        description=f"Result: **{result.upper()}** {emoji}\n\n{check_marks}",
                        color=0x00ff00
                    )
                    embed.add_field(name="Rows Completed", value=f"**{current_row - 1}/5**", inline=True)
                    embed.add_field(name="Current Multiplier", value=f"**{row_multipliers[current_row - 1]:.2f}x**", inline=True)
                    embed.add_field(name="Potential Win", value=f"**{int(amount * row_multipliers[current_row - 1])}** points", inline=True)
                    embed.add_field(name="Next Row", value=f"Row {current_row}/5 - **{row_multipliers[current_row]:.2f}x**", inline=False)
                    
                    self.update_buttons()
                    await interaction.edit_original_response(embed=embed, view=self)
            else:
                await db.update_user_stats(user_id, won=False)
                
                check_marks = "✅" * (current_row - 1) + "❌" + "⬜" * (5 - current_row)
                
                embed = discord.Embed(
                    title="🪙 Progressive Coinflip - LOST!",
                    description=f"Result: **{result.upper()}** {emoji}\n\n{check_marks}",
                    color=0xff0000
                )
                embed.add_field(name="Failed at Row", value=f"**{current_row}/5**", inline=True)
                embed.add_field(name="Lost", value=f"**{amount:,}** points", inline=True)
                embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                embed.set_image(url=LOSS_IMAGES['progressivecoinflip'])
                await interaction.edit_original_response(embed=embed, view=None)
                await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
    
    view = ProgressiveFlipView()
    embed = discord.Embed(
        title="🪙 Progressive Coinflip - Row 1/5",
        description="Complete all 5 rows to win big!\n\n⬜⬜⬜⬜⬜\n\nChoose Heads or Tails for Row 1",
        color=0x3498db
    )
    embed.add_field(name="Row 1", value="**1.50x**", inline=True)
    embed.add_field(name="Row 2", value="**2.25x** 💰", inline=True)
    embed.add_field(name="Row 3", value="**3.38x** 💰", inline=True)
    embed.add_field(name="Row 4", value="**5.06x** 💰", inline=True)
    embed.add_field(name="Row 5", value="**7.59x** 🏆", inline=True)
    embed.set_footer(text="💡 You can cash out from Row 2 onwards!")
    await ctx.send(embed=embed, view=view)

@require_guild()
@bot.command()
@cooldown_check()
async def poker(ctx, amount: str):
    """Poker - 5 card poker with hold/discard!"""
    user_id = ctx.author.id
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'poker')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **poker** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount, "Poker bet")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_poker")
    
    def create_deck():
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['♠', '♥', '♦', '♣']
        deck = [f'{rank}{suit}' for rank in ranks for suit in suits]
        random.shuffle(deck)
        return deck
    
    def evaluate_hand(cards):
        ranks = [c[:-1] for c in cards]
        suits = [c[-1] for c in cards]
        rank_values = {'2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, '10':10, 'J':11, 'Q':12, 'K':13, 'A':14}
        rank_counts = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1
        
        counts = sorted(rank_counts.values(), reverse=True)
        is_flush = len(set(suits)) == 1
        sorted_values = sorted([rank_values[r] for r in ranks])
        is_straight = (sorted_values == list(range(sorted_values[0], sorted_values[0] + 5))) or (sorted_values == [2, 3, 4, 5, 14])
        
        is_royal = is_straight and is_flush and sorted_values == [10, 11, 12, 13, 14]
        
        if is_royal:
            return ("Royal Flush", 4.0)
        elif is_straight and is_flush:
            return ("Straight Flush", 3.5)
        elif counts == [4, 1]:
            return ("Four of a Kind", 3.0)
        elif counts == [3, 2]:
            return ("Full House", 2.5)
        elif is_flush:
            return ("Flush", 2.0)
        elif is_straight:
            return ("Straight", 1.8)
        elif counts == [3, 1, 1]:
            return ("Three of a Kind", 1.5)
        elif counts == [2, 2, 1]:
            return ("Two Pair", 1.2)
        elif counts == [2, 1, 1, 1]:
            return ("Pair", 1.0)
        else:
            return ("High Card", 0)
    
    deck = create_deck()
    hand = [deck.pop() for _ in range(5)]
    held = [False] * 5
    
    class PokerView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.create_buttons()
        
        def create_buttons(self):
            self.clear_items()
            for i in range(5):
                style = discord.ButtonStyle.success if held[i] else discord.ButtonStyle.primary
                label = f"{'HOLD' if held[i] else 'Card'} {i+1}"
                button = discord.ui.Button(label=label, style=style, custom_id=f'card_{i}')
                button.callback = self.make_hold_callback(i)
                self.add_item(button)
            
            draw_button = discord.ui.Button(label='🎴 Draw', style=discord.ButtonStyle.danger)
            draw_button.callback = self.draw_callback
            self.add_item(draw_button)
        
        def make_hold_callback(self, card_idx):
            async def hold_callback(interaction: discord.Interaction):
                if interaction.user.id != user_id:
                    await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                    return
                
                held[card_idx] = not held[card_idx]
                self.create_buttons()
                
                embed = discord.Embed(title="🎴 Poker", description=f"Hand: {' '.join(hand)}", color=0x3498db)
                held_text = ', '.join([f"{i+1}" for i, h in enumerate(held) if h]) or "None"
                embed.add_field(name="Held Cards", value=held_text, inline=True)
                await safe_interaction_response(interaction, embed=embed, view=self)
            
            return hold_callback
        
        async def draw_callback(self, interaction: discord.Interaction):
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            for i in range(5):
                if not held[i]:
                    hand[i] = deck.pop()
            
            hand_name, base_multiplier = evaluate_hand(hand)
            
            if base_multiplier > 0:
                final_multiplier = base_multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
                win_amount = int(amount * final_multiplier)
                
                await db.update_balance(user_id, win_amount, f"Poker win: {final_multiplier:.2f}x")
                await db.record_win(user_id, "POKER", amount, win_amount, final_multiplier)
                await db.update_user_stats(user_id, won=True)
                
                embed = discord.Embed(title=f"🎴 Poker - {hand_name}! WON! 🎉", description=f"Hand: {' '.join(hand)}", color=0x00ff00)
                embed.add_field(name="Hand", value=hand_name, inline=True)
                embed.add_field(name="Multiplier", value=f"**{final_multiplier:.2f}x**", inline=True)
                embed.add_field(name="Won", value=f"**{win_amount}** points! 🎉", inline=True)
                embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                embed.set_image(url=WIN_IMAGES['poker'])
                await safe_interaction_response(interaction, embed=embed, view=None)
                
                await WinLogger.log_win(ctx.author, "POKER", amount, win_amount, final_multiplier,
                                       details=f"Hand: {hand_name}")
            else:
                await db.update_user_stats(user_id, won=False)
                embed = discord.Embed(title="🎴 Poker - High Card, LOST", description=f"Hand: {' '.join(hand)}", color=0xff0000)
                embed.add_field(name="Hand", value=hand_name, inline=True)
                embed.add_field(name="Lost", value=f"**{amount}** points", inline=True)
                embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                embed.set_image(url=LOSS_IMAGES['poker'])
                await safe_interaction_response(interaction, embed=embed, view=None)
            
            await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
    
    view = PokerView()
    embed = discord.Embed(title="🎴 Poker", description=f"Hand: {' '.join(hand)}\n\nSelect cards to hold, then draw!", color=0x3498db)
    await ctx.send(embed=embed, view=view)

@require_guild()
@bot.command()
@cooldown_check()
async def connect(ctx, opponent: discord.Member = None, amount: str = "10"):
    """Connect 4 - Classic Connect 4 game!"""
    user_id = ctx.author.id
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'connect')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **connect** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount_parsed = await parse_amount(amount, user_id)
    
    if amount_parsed is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount_parsed <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount_parsed:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_pvp = opponent is not None and opponent.id != user_id
    
    if is_pvp:
        if opponent.bot:
            await ctx.send("❌ Cannot play against a bot user! Use .connect [amount] to play vs AI.")
            return
        
        # PvP: Use challenge system
        async def start_connect_pvp(ctx_inner, interaction, player1, player2, amount_inner):
            # Deduct balances from BOTH players
            await db.update_balance(player1.id, -amount_inner, "Connect 4 bet")
            await db.update_balance(player2.id, -amount_inner, "Connect 4 bet (PvP)")
            await db.add_wager(player1.id, amount_inner)
            await db.add_wager(player2.id, amount_inner)
            
            board = [[0 for _ in range(7)] for _ in range(6)]
            current_player = 1
            
            def check_win(board, player):
                for r in range(6):
                    for c in range(4):
                        if all(board[r][c+i] == player for i in range(4)):
                            return True
                for r in range(3):
                    for c in range(7):
                        if all(board[r+i][c] == player for i in range(4)):
                            return True
                for r in range(3):
                    for c in range(4):
                        if all(board[r+i][c+i] == player for i in range(4)):
                            return True
                for r in range(3, 6):
                    for c in range(4):
                        if all(board[r-i][c+i] == player for i in range(4)):
                            return True
                return False
            
            class ConnectView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=120)
                    self.create_buttons()
                
                def create_buttons(self):
                    self.clear_items()
                    for col in range(7):
                        button = discord.ui.Button(label=f"Col {col+1}", style=discord.ButtonStyle.primary, custom_id=f'col_{col}')
                        button.callback = self.make_drop_callback(col)
                        self.add_item(button)
                
                def make_drop_callback(self, col):
                    async def drop_callback(interaction_inner: discord.Interaction):
                        nonlocal current_player
                        
                        expected_player = player1.id if current_player == 1 else player2.id
                        if interaction_inner.user.id != expected_player:
                            await interaction_inner.response.send_message("❌ Not your turn!", ephemeral=True)
                            return
                        
                        if board[0][col] != 0:
                            await interaction_inner.response.send_message("❌ Column full!", ephemeral=True)
                            return
                        
                        for row in range(5, -1, -1):
                            if board[row][col] == 0:
                                board[row][col] = current_player
                                break
                        
                        if check_win(board, current_player):
                            winner_id = player1.id if current_player == 1 else player2.id
                            loser_id = player2.id if current_player == 1 else player1.id
                            
                            win_amount = int(amount_inner * 1.98)
                            await db.update_balance(winner_id, win_amount * 2, f"Connect 4 win (PvP)")
                            await db.record_win(winner_id, "CONNECT", amount_inner, win_amount, 1.98)
                            await db.update_user_stats(winner_id, won=True)
                            await db.update_user_stats(loser_id, won=False)
                            
                            embed = discord.Embed(title="🔴 Connect 4 - WON! 🎉", description=f"<@{winner_id}> wins!", color=0x00ff00)
                            embed.add_field(name="Winner", value=f"<@{winner_id}>", inline=True)
                            embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
                            embed.set_image(url=WIN_IMAGES['connect'])
                            
                            board_str = '\n'.join([''.join(['🔴' if cell == 1 else '🟡' if cell == 2 else '⚪' for cell in row]) for row in board])
                            embed.add_field(name="Final Board", value=board_str, inline=False)
                            await safe_interaction_response(interaction_inner, embed=embed, view=None)
                            return
                        
                        current_player = 2 if current_player == 1 else 1
                        
                        board_str = '\n'.join([''.join(['🔴' if cell == 1 else '🟡' if cell == 2 else '⚪' for cell in row]) for row in board])
                        turn_text = f"<@{player1.id}>'s turn (🔴)" if current_player == 1 else f"<@{player2.id}>'s turn (🟡)"
                        embed = discord.Embed(title="🔴 Connect 4", description=f"{turn_text}\n\n{board_str}", color=0x3498db)
                        await safe_interaction_response(interaction_inner, embed=embed, view=self)
                    
                    return drop_callback
            
            view = ConnectView()
            board_str = '\n'.join([''.join(['⚪' for _ in range(7)]) for _ in range(6)])
            embed = discord.Embed(title=f"🔴 Connect 4 vs {player2.mention}", description=f"<@{player1.id}>'s turn (🔴)\n\n{board_str}", color=0x3498db)
            await ctx_inner.send(embed=embed, view=view)
        
        # Use challenge system for PvP
        await initiate_multiplayer_challenge(ctx, ctx.author, opponent, "Connect 4", amount_parsed, start_connect_pvp)
        return
    
    # vs Bot: Keep existing logic
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    balance = await db.get_balance(user_id)
    if balance < amount_parsed:
        await ctx.send("❌ Insufficient balance!")
        return
    
    await db.update_balance(user_id, -amount_parsed, "Connect 4 bet")
    await db.add_wager(user_id, amount_parsed)
    
    board = [[0 for _ in range(7)] for _ in range(6)]
    current_player = 1
    
    def check_win(board, player):
        for r in range(6):
            for c in range(4):
                if all(board[r][c+i] == player for i in range(4)):
                    return True
        for r in range(3):
            for c in range(7):
                if all(board[r+i][c] == player for i in range(4)):
                    return True
        for r in range(3):
            for c in range(4):
                if all(board[r+i][c+i] == player for i in range(4)):
                    return True
        for r in range(3, 6):
            for c in range(4):
                if all(board[r-i][c+i] == player for i in range(4)):
                    return True
        return False
    
    def get_bot_move(board):
        valid_cols = [c for c in range(7) if board[0][c] == 0]
        return random.choice(valid_cols) if valid_cols else None
    
    class ConnectView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=120)
            self.create_buttons()
        
        def create_buttons(self):
            self.clear_items()
            for col in range(7):
                button = discord.ui.Button(label=f"Col {col+1}", style=discord.ButtonStyle.primary, custom_id=f'col_{col}')
                button.callback = self.make_drop_callback(col)
                self.add_item(button)
        
        def make_drop_callback(self, col):
            async def drop_callback(interaction: discord.Interaction):
                nonlocal current_player
                
                # vs Bot: always user's turn
                if interaction.user.id != user_id:
                    await interaction.response.send_message("❌ Not your game!", ephemeral=True)
                    return
                
                if board[0][col] != 0:
                    await interaction.response.send_message("❌ Column full!", ephemeral=True)
                    return
                
                for row in range(5, -1, -1):
                    if board[row][col] == 0:
                        board[row][col] = current_player
                        break
                
                if check_win(board, current_player):
                    # vs Bot: Player wins (with VIP/boost multiplier)
                    final_multiplier = 2.0 * (1.15 if is_vip else 1.0) * boost_multiplier
                    win_amount = int(amount_parsed * final_multiplier)
                    await db.update_balance(user_id, win_amount, f"Connect 4 win: {final_multiplier:.2f}x")
                    await db.record_win(user_id, "CONNECT", amount_parsed, win_amount, final_multiplier)
                    await db.update_user_stats(user_id, won=True)
                    
                    embed = discord.Embed(title="🔴 Connect 4 - WON! 🎉", description="You beat the bot!", color=0x00ff00)
                    embed.add_field(name="Multiplier", value=f"**{final_multiplier:.2f}x**", inline=True)
                    embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
                    embed.set_image(url=WIN_IMAGES['connect'])
                    
                    board_str = '\n'.join([''.join(['🔴' if cell == 1 else '🟡' if cell == 2 else '⚪' for cell in row]) for row in board])
                    embed.add_field(name="Final Board", value=board_str, inline=False)
                    await safe_interaction_response(interaction, embed=embed, view=None)
                    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
                    return
                
                current_player = 2 if current_player == 1 else 1
                
                if current_player == 2:
                    bot_col = get_bot_move(board)
                    if bot_col is not None:
                        for row in range(5, -1, -1):
                            if board[row][bot_col] == 0:
                                board[row][bot_col] = 2
                                break
                        
                        if check_win(board, 2):
                            await db.update_user_stats(user_id, won=False)
                            embed = discord.Embed(title="🔴 Connect 4 - LOST", description="Bot wins!", color=0xff0000)
                            board_str = '\n'.join([''.join(['🔴' if cell == 1 else '🟡' if cell == 2 else '⚪' for cell in row]) for row in board])
                            embed.add_field(name="Final Board", value=board_str, inline=False)
                            embed.add_field(name="Lost", value=f"**{amount_parsed}** points", inline=True)
                            embed.set_image(url=LOSS_IMAGES['connect'])
                            await safe_interaction_response(interaction, embed=embed, view=None)
                            await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
                            return
                        
                        current_player = 1
                
                board_str = '\n'.join([''.join(['🔴' if cell == 1 else '🟡' if cell == 2 else '⚪' for cell in row]) for row in board])
                turn_text = "Your turn (🔴)" if current_player == 1 else "Bot's turn (🟡)"
                embed = discord.Embed(title="🔴 Connect 4 vs Bot", description=f"{turn_text}\n\n{board_str}", color=0x3498db)
                await safe_interaction_response(interaction, embed=embed, view=self)
            
            return drop_callback
    
    view = ConnectView()
    board_str = '\n'.join([''.join(['⚪' for _ in range(7)]) for _ in range(6)])
    embed = discord.Embed(title="🔴 Connect 4 vs Bot", description=f"Your turn (🔴)\n\n{board_str}", color=0x3498db)
    await ctx.send(embed=embed, view=view)

@require_guild()
@bot.command()
@cooldown_check()
async def balloon(ctx, amount: str):
    """Balloon - Pump the balloon without popping it!"""
    user_id = ctx.author.id
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'balloon')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **balloon** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount = await parse_amount(amount, user_id)
    
    if amount is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount, "Balloon bet")
    await db.add_wager(user_id, amount)
    await db.record_activity(user_id, "play_balloon")
    
    pumps = 0
    current_multiplier = 1.0
    
    class BalloonView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
        
        @discord.ui.button(label='💨 Pump', style=discord.ButtonStyle.primary)
        async def pump_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            nonlocal pumps, current_multiplier
            
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            # Defer interaction to prevent timeout
            await safe_defer(interaction)
            
            pumps += 1
            current_multiplier += 0.2
            
            pop_chance = min(0.05 + (pumps * 0.08), 0.95)
            
            if random.random() < pop_chance:
                await db.update_user_stats(user_id, won=False)
                embed = discord.Embed(title="🎈 Balloon - POP! 💥", description="The balloon popped!", color=0xff0000)
                embed.add_field(name="Pumps", value=f"**{pumps}**", inline=True)
                embed.add_field(name="Lost", value=f"**{amount}** points", inline=True)
                embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                embed.set_image(url=LOSS_IMAGES['balloon'])
                await safe_interaction_response(interaction, embed=embed, view=None)
                await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
            else:
                embed = discord.Embed(title="🎈 Balloon", description=f"Balloon inflating... {pumps} pumps!", color=0x3498db)
                embed.add_field(name="Current Multiplier", value=f"**{current_multiplier:.1f}x**", inline=True)
                embed.add_field(name="Pop Chance", value=f"**{pop_chance*100:.1f}%**", inline=True)
                embed.add_field(name="Potential Win", value=f"**{int(amount * current_multiplier)}** points", inline=True)
                await safe_interaction_response(interaction, embed=embed, view=self)
        
        @discord.ui.button(label='💰 Cash Out', style=discord.ButtonStyle.success)
        async def cashout_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            nonlocal pumps, current_multiplier
            
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            if pumps == 0:
                await interaction.response.send_message("❌ You must pump at least once!", ephemeral=True)
                return
            
            # Defer interaction to prevent timeout
            await safe_defer(interaction)
            
            final_multiplier = current_multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
            win_amount = int(amount * final_multiplier)
            
            await db.update_balance(user_id, win_amount, f"Balloon cashout: {final_multiplier:.2f}x")
            await db.record_win(user_id, "BALLOON", amount, win_amount, final_multiplier)
            await db.update_user_stats(user_id, won=True)
            
            embed = discord.Embed(title="🎈 Balloon - CASHED OUT! 💰", description="You played it safe!", color=0x00ff00)
            embed.add_field(name="Pumps", value=f"**{pumps}**", inline=True)
            embed.add_field(name="Multiplier", value=f"**{final_multiplier:.2f}x**", inline=True)
            embed.add_field(name="Won", value=f"**{win_amount}** points! 🎉", inline=True)
            embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
            embed.set_image(url=WIN_IMAGES['balloon'])
            await safe_interaction_response(interaction, embed=embed, view=None)
            
            await WinLogger.log_win(ctx.author, "BALLOON", amount, win_amount, final_multiplier,
                                   details=f"Pumps: {pumps}")
            await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
    
    view = BalloonView()
    embed = discord.Embed(title="🎈 Balloon", 
                         description="Pump the balloon!\nEach pump = +0.2x\nBut pop chance increases!", color=0x3498db)
    embed.add_field(name="Starting Multiplier", value="**1.0x**", inline=True)
    await ctx.send(embed=embed, view=view)

@require_guild()
@bot.command()
@cooldown_check()
async def chess(ctx, opponent: discord.Member = None, amount: str = "10"):
    """Chess - Simplified chess game!"""
    user_id = ctx.author.id
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'chess')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **chess** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    amount_parsed = await parse_amount(amount, user_id)
    
    if amount_parsed is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount_parsed <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount_parsed:
        await ctx.send("❌ Insufficient balance!")
        return
    
    is_pvp = opponent is not None and opponent.id != user_id
    
    if is_pvp:
        if opponent.bot:
            await ctx.send("❌ Cannot play against a bot user! Use .chess [amount] to play vs AI.")
            return
        
        # PvP: Use challenge system
        async def start_chess_pvp(ctx_inner, interaction, player1, player2, amount_inner):
            # Deduct balances from BOTH players
            await db.update_balance(player1.id, -amount_inner, "Chess bet")
            await db.update_balance(player2.id, -amount_inner, "Chess bet (PvP)")
            await db.add_wager(player1.id, amount_inner)
            await db.add_wager(player2.id, amount_inner)
            
            board = [
                ['♜', '♞', '♝', '♛', '♚', '♝', '♞', '♜'],
                ['♟'] * 8,
                [' '] * 8,
                [' '] * 8,
                [' '] * 8,
                [' '] * 8,
                ['♙'] * 8,
                ['♖', '♘', '♗', '♕', '♔', '♗', '♘', '♖']
            ]
            
            move_count = 0
            current_turn = 1
            
            class ChessView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=180)
                    self.selected_piece = None
                
                @discord.ui.button(label='🏳️ Resign', style=discord.ButtonStyle.danger)
                async def resign_button(self, interaction_inner: discord.Interaction, button: discord.ui.Button):
                    nonlocal move_count
                    
                    expected_player = player1.id if current_turn == 1 else player2.id
                    if interaction_inner.user.id != expected_player:
                        await interaction_inner.response.send_message("❌ Not your turn!", ephemeral=True)
                        return
                    
                    # Defer interaction to prevent timeout
                    await safe_defer(interaction_inner)
                    
                    winner_id = player2.id if interaction_inner.user.id == player1.id else player1.id
                    loser_id = interaction_inner.user.id
                    
                    win_amount = int(amount_inner * 1.98)
                    await db.update_balance(winner_id, win_amount * 2, f"Chess win (PvP - opponent resigned)")
                    await db.record_win(winner_id, "CHESS", amount_inner, win_amount, 1.98)
                    await db.update_user_stats(winner_id, won=True)
                    await db.update_user_stats(loser_id, won=False)
                    
                    embed = discord.Embed(title="♟️ Chess - RESIGNED", description=f"<@{winner_id}> wins by resignation!", color=0x00ff00)
                    embed.set_image(url=WIN_IMAGES['chess'])
                    
                    await safe_interaction_response(interaction_inner, embed=embed, view=None)
                
                @discord.ui.button(label='🤝 Draw', style=discord.ButtonStyle.secondary)
                async def draw_button(self, interaction_inner: discord.Interaction, button: discord.ui.Button):
                    if move_count >= 20:
                        # Defer interaction to prevent timeout
                        await safe_defer(interaction_inner)
                        
                        await db.update_balance(player1.id, amount_inner, "Chess draw")
                        await db.update_balance(player2.id, amount_inner, "Chess draw")
                        
                        embed = discord.Embed(title="♟️ Chess - DRAW", description="Game ended in a draw! Bets refunded.", color=0xffff00)
                        await safe_interaction_response(interaction_inner, embed=embed, view=None)
                    else:
                        await interaction_inner.response.send_message("❌ Must play 20+ moves to claim draw!", ephemeral=True)
            
            view = ChessView()
            board_str = '\n'.join([''.join(row) for row in board])
            embed = discord.Embed(title=f"♟️ Chess vs {player2.mention}", 
                                 description=f"Simplified chess! Use buttons to play.\n\n{board_str}", color=0x3498db)
            embed.set_footer(text="Resign or play 20+ moves to claim draw")
            await ctx_inner.send(embed=embed, view=view)
        
        # Use challenge system for PvP
        await initiate_multiplayer_challenge(ctx, ctx.author, opponent, "Chess", amount_parsed, start_chess_pvp)
        return
    
    # vs Bot: Keep existing logic
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    balance = await db.get_balance(user_id)
    if balance < amount_parsed:
        await ctx.send("❌ Insufficient balance!")
        return
    
    await db.update_balance(user_id, -amount_parsed, "Chess bet")
    await db.add_wager(user_id, amount_parsed)
    
    board = [
        ['♜', '♞', '♝', '♛', '♚', '♝', '♞', '♜'],
        ['♟'] * 8,
        [' '] * 8,
        [' '] * 8,
        [' '] * 8,
        [' '] * 8,
        ['♙'] * 8,
        ['♖', '♘', '♗', '♕', '♔', '♗', '♘', '♖']
    ]
    
    move_count = 0
    current_turn = 1
    
    def get_bot_move():
        white_pieces = []
        for r in range(8):
            for c in range(8):
                if board[r][c] in '♙♖♘♗♕♔':
                    white_pieces.append((r, c))
        
        if white_pieces:
            piece = random.choice(white_pieces)
            moves = [(piece[0] - 1, piece[1]), (piece[0] + 1, piece[1]), 
                    (piece[0], piece[1] - 1), (piece[0], piece[1] + 1)]
            valid_moves = [(r, c) for r, c in moves if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == ' ']
            if valid_moves:
                return (piece, random.choice(valid_moves))
        return None
    
    class ChessView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=180)
            self.selected_piece = None
        
        @discord.ui.button(label='🏳️ Resign', style=discord.ButtonStyle.danger)
        async def resign_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            nonlocal move_count
            
            # vs Bot: only user can resign
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            # Defer interaction to prevent timeout
            await safe_defer(interaction)
            
            # vs Bot: User resigned, bot wins
            await db.update_user_stats(user_id, won=False)
            embed = discord.Embed(title="♟️ Chess - RESIGNED", description="You resigned. Bot wins!", color=0xff0000)
            embed.add_field(name="Lost", value=f"**{amount_parsed}** points", inline=True)
            embed.set_image(url=LOSS_IMAGES['chess'])
            
            await safe_interaction_response(interaction, embed=embed, view=None)
            await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
        
        @discord.ui.button(label='🤝 Draw', style=discord.ButtonStyle.secondary)
        async def draw_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if move_count >= 20:
                # Defer interaction to prevent timeout
                await safe_defer(interaction)
                
                # vs Bot: refund bet on draw
                await db.update_balance(user_id, amount_parsed, "Chess draw")
                
                embed = discord.Embed(title="♟️ Chess - DRAW", description="Game ended in a draw! Bet refunded.", color=0xffff00)
                await safe_interaction_response(interaction, embed=embed, view=None)
                await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
            else:
                await interaction.response.send_message("❌ Must play 20+ moves to claim draw!", ephemeral=True)
    
    view = ChessView()
    board_str = '\n'.join([''.join(row) for row in board])
    embed = discord.Embed(title="♟️ Chess vs Bot", 
                         description=f"Simplified chess! Use buttons to play.\n\n{board_str}", color=0x3498db)
    embed.set_footer(text="Resign or play 20+ moves to claim draw")
    await ctx.send(embed=embed, view=view)

# ========== NEW CASINO GAMES ==========
@require_guild()
@bot.command()
@cooldown_check()
async def classicslots(ctx, amount: str):
    """Classic 3-disk slot machine"""
    user_id = ctx.author.id
    
    amount_parsed = await parse_amount(amount, user_id)
    if amount_parsed is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount_parsed <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount_parsed:
        await ctx.send("❌ Insufficient balance!")
        return
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'classicslots')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **classicslots** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount_parsed, "Classic Slots bet")
    await db.add_wager(user_id, amount_parsed)
    await db.record_activity(user_id, "play_classicslots")
    
    symbols = ['🍒', '🍋', '🍊', '🎰', '💎', 'BAR']
    reels = [random.choice(symbols) for _ in range(3)]
    
    multiplier = 0
    if reels[0] == reels[1] == reels[2]:
        if reels[0] == '🎰': multiplier = 5.0
        elif reels[0] == '💎': multiplier = 3.0
        elif reels[0] == 'BAR': multiplier = 2.0
        else: multiplier = 1.5
    
    final_multiplier = multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
    
    if multiplier > 0:
        win_amount = int(amount_parsed * final_multiplier)
        await db.update_balance(user_id, win_amount, f"Classic Slots win: {final_multiplier:.2f}x")
        await db.record_win(user_id, "CLASSICSLOTS", amount_parsed, win_amount, final_multiplier)
        await db.update_user_stats(user_id, won=True)
        
        embed = discord.Embed(title="🎰 Classic Slots - WIN!", description=f"**{' | '.join(reels)}**", color=0x00ff00)
        embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
        embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        await ctx.send(embed=embed)
    else:
        await db.update_user_stats(user_id, won=False)
        embed = discord.Embed(title="🎰 Classic Slots - LOST", description=f"**{' | '.join(reels)}**", color=0xff0000)
        embed.add_field(name="Lost", value=f"**{amount_parsed}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        await ctx.send(embed=embed)
    
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

@require_guild()
@bot.command()
@cooldown_check()
async def darts(ctx, amount: str):
    """Throw a dart at a dartboard!"""
    user_id = ctx.author.id
    
    amount_parsed = await parse_amount(amount, user_id)
    if amount_parsed is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount_parsed <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount_parsed:
        await ctx.send("❌ Insufficient balance!")
        return
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'darts')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **darts** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount_parsed, "Darts bet")
    await db.add_wager(user_id, amount_parsed)
    await db.record_activity(user_id, "play_darts")
    
    # Weighted hit chances based on target zone
    zone_chances = {
        'bullseye': {'🎯 BULLSEYE': 20, '🔴 Inner Ring': 40, '🟡 Outer Ring': 30, '⚪ Miss': 10},
        'inner': {'🎯 BULLSEYE': 5, '🔴 Inner Ring': 50, '🟡 Outer Ring': 35, '⚪ Miss': 10},
        'outer': {'🎯 BULLSEYE': 2, '🔴 Inner Ring': 18, '🟡 Outer Ring': 60, '⚪ Miss': 20},
        'safe': {'🎯 BULLSEYE': 0, '🔴 Inner Ring': 5, '🟡 Outer Ring': 45, '⚪ Miss': 50}
    }
    
    multipliers = {'🎯 BULLSEYE': 5.0, '🔴 Inner Ring': 2.5, '🟡 Outer Ring': 1.5, '⚪ Miss': 0}
    
    class DartsView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
        
        async def throw_dart(self, interaction: discord.Interaction, target: str):
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            # Determine result based on target choice
            zones = list(zone_chances[target].keys())
            weights = list(zone_chances[target].values())
            result = random.choices(zones, weights=weights, k=1)[0]
            
            multiplier = multipliers[result]
            final_multiplier = multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
            
            if multiplier > 0:
                win_amount = int(amount_parsed * final_multiplier)
                await db.update_balance(user_id, win_amount, f"Darts win: {final_multiplier:.2f}x")
                await db.record_win(user_id, "DARTS", amount_parsed, win_amount, final_multiplier)
                await db.update_user_stats(user_id, won=True)
                
                embed = discord.Embed(title="🎯 Darts - HIT!", description=f"You aimed for **{target.upper()}** and hit: **{result}**!", color=0x00ff00)
                embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
                embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
                embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                await safe_interaction_response(interaction, embed=embed, view=None)
            else:
                await db.update_user_stats(user_id, won=False)
                embed = discord.Embed(title="🎯 Darts - MISSED!", description=f"You aimed for **{target.upper()}** but... **{result}**!", color=0xff0000)
                embed.add_field(name="Lost", value=f"**{amount_parsed}** points", inline=True)
                embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                await safe_interaction_response(interaction, embed=embed, view=None)
            
            await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
        
        @discord.ui.button(label='Bullseye', style=discord.ButtonStyle.danger, emoji='🎯', row=0)
        async def bullseye_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.throw_dart(interaction, 'bullseye')
        
        @discord.ui.button(label='Inner Ring', style=discord.ButtonStyle.primary, emoji='🔴', row=0)
        async def inner_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.throw_dart(interaction, 'inner')
        
        @discord.ui.button(label='Outer Ring', style=discord.ButtonStyle.success, emoji='🟡', row=1)
        async def outer_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.throw_dart(interaction, 'outer')
        
        @discord.ui.button(label='Play it Safe', style=discord.ButtonStyle.secondary, emoji='⚪', row=1)
        async def safe_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.throw_dart(interaction, 'safe')
    
    view = DartsView()
    embed = discord.Embed(title="🎯 Darts", description="Choose where to aim! Higher risk = Higher reward!", color=0xFF6B6B)
    embed.add_field(name="Bullseye 🎯", value="Risky! 5.0x payout", inline=False)
    embed.add_field(name="Inner Ring 🔴", value="Balanced: 2.5x payout", inline=False)
    embed.add_field(name="Outer Ring 🟡", value="Safe: 1.5x payout", inline=False)
    embed.add_field(name="Bet", value=f"**{amount_parsed}** points", inline=True)
    await ctx.send(embed=embed, view=view)

@require_guild()
@bot.command()
@cooldown_check()
async def diamonds(ctx, amount: str):
    """Spin the slots to match diamonds and win!"""
    user_id = ctx.author.id
    
    amount_parsed = await parse_amount(amount, user_id)
    if amount_parsed is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount_parsed <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount_parsed:
        await ctx.send("❌ Insufficient balance!")
        return
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'diamonds')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **diamonds** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount_parsed, "Diamonds bet")
    await db.add_wager(user_id, amount_parsed)
    await db.record_activity(user_id, "play_diamonds")
    
    symbols = ['💎', '💠', '🔷', '🔹', '⬜']
    weights = [10, 15, 25, 30, 20]
    reels = random.choices(symbols, weights=weights, k=5)
    
    diamond_count = reels.count('💎')
    multipliers = {5: 8.0, 4: 4.0, 3: 2.5, 2: 1.5, 1: 0, 0: 0}
    multiplier = multipliers.get(diamond_count, 0)
    final_multiplier = multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
    
    if multiplier > 0:
        win_amount = int(amount_parsed * final_multiplier)
        await db.update_balance(user_id, win_amount, f"Diamonds win: {final_multiplier:.2f}x")
        await db.record_win(user_id, "DIAMONDS", amount_parsed, win_amount, final_multiplier)
        await db.update_user_stats(user_id, won=True)
        
        embed = discord.Embed(title="💎 Diamonds - WIN!", description=f"**{' '.join(reels)}**\n{diamond_count} diamonds!", color=0x00ff00)
        embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
        embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        await ctx.send(embed=embed)
    else:
        await db.update_user_stats(user_id, won=False)
        embed = discord.Embed(title="💎 Diamonds - LOST", description=f"**{' '.join(reels)}**\n{diamond_count} diamonds", color=0xff0000)
        embed.add_field(name="Lost", value=f"**{amount_parsed}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        await ctx.send(embed=embed)
    
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

@require_guild()
@bot.command()
@cooldown_check()
async def dicewar(ctx, amount: str):
    """Play a dice game against the bot"""
    user_id = ctx.author.id
    
    amount_parsed = await parse_amount(amount, user_id)
    if amount_parsed is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount_parsed <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount_parsed:
        await ctx.send("❌ Insufficient balance!")
        return
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'dicewar')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **dicewar** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount_parsed, "Dice War bet")
    await db.add_wager(user_id, amount_parsed)
    await db.record_activity(user_id, "play_dicewar")
    
    player_roll = random.randint(1, 6) + random.randint(1, 6)
    bot_roll = random.randint(1, 6) + random.randint(1, 6)
    
    if player_roll > bot_roll:
        multiplier = 1.9
        final_multiplier = multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
        win_amount = int(amount_parsed * final_multiplier)
        await db.update_balance(user_id, win_amount, f"Dice War win: {final_multiplier:.2f}x")
        await db.record_win(user_id, "DICEWAR", amount_parsed, win_amount, final_multiplier)
        await db.update_user_stats(user_id, won=True)
        
        embed = discord.Embed(title="🎲 Dice War - WIN!", description=f"You rolled **{player_roll}**, Bot rolled **{bot_roll}**", color=0x00ff00)
        embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
        embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        await ctx.send(embed=embed)
    elif player_roll == bot_roll:
        await db.update_balance(user_id, amount_parsed, "Dice War tie - refund")
        embed = discord.Embed(title="🎲 Dice War - TIE!", description=f"Both rolled **{player_roll}** - Bet refunded!", color=0xffff00)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        await ctx.send(embed=embed)
    else:
        await db.update_user_stats(user_id, won=False)
        embed = discord.Embed(title="🎲 Dice War - LOST", description=f"You rolled **{player_roll}**, Bot rolled **{bot_roll}**", color=0xff0000)
        embed.add_field(name="Lost", value=f"**{amount_parsed}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        await ctx.send(embed=embed)
    
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

@require_guild()
@bot.command()
@cooldown_check()
async def easter(ctx, amount: str):
    """Play the special Easter Egg Hunt slots"""
    user_id = ctx.author.id
    
    amount_parsed = await parse_amount(amount, user_id)
    if amount_parsed is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount_parsed <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount_parsed:
        await ctx.send("❌ Insufficient balance!")
        return
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'easter')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **easter** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount_parsed, "Easter Egg Hunt bet")
    await db.add_wager(user_id, amount_parsed)
    await db.record_activity(user_id, "play_easter")
    
    symbols = ['🥚', '🐰', '🐣', '🌸', '🌷', '🌼']
    weights = [30, 15, 12, 20, 15, 8]
    reels = random.choices(symbols, weights=weights, k=3)
    
    multiplier = 0
    if reels[0] == reels[1] == reels[2]:
        if reels[0] == '🐰': multiplier = 5.0
        elif reels[0] == '🐣': multiplier = 4.0
        elif reels[0] == '🥚': multiplier = 3.0
        else: multiplier = 2.0
    elif reels.count('🐰') >= 2: multiplier = 1.5
    
    final_multiplier = multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
    
    if multiplier > 0:
        win_amount = int(amount_parsed * final_multiplier)
        await db.update_balance(user_id, win_amount, f"Easter Egg Hunt win: {final_multiplier:.2f}x")
        await db.record_win(user_id, "EASTER", amount_parsed, win_amount, final_multiplier)
        await db.update_user_stats(user_id, won=True)
        
        embed = discord.Embed(title="🐰 Easter Egg Hunt - WIN!", description=f"**{' '.join(reels)}**", color=0x00ff00)
        embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
        embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        await ctx.send(embed=embed)
    else:
        await db.update_user_stats(user_id, won=False)
        embed = discord.Embed(title="🐰 Easter Egg Hunt - LOST", description=f"**{' '.join(reels)}**", color=0xff0000)
        embed.add_field(name="Lost", value=f"**{amount_parsed}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        await ctx.send(embed=embed)
    
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

@require_guild()
@bot.command()
@cooldown_check()
async def eviljokers(ctx, amount: str):
    """Uncover safe cards, avoid the Evil Jokers!"""
    user_id = ctx.author.id
    
    amount_parsed = await parse_amount(amount, user_id)
    if amount_parsed is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount_parsed <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount_parsed:
        await ctx.send("❌ Insufficient balance!")
        return
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'eviljokers')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **eviljokers** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount_parsed, "Evil Jokers bet")
    await db.add_wager(user_id, amount_parsed)
    await db.record_activity(user_id, "play_eviljokers")
    
    # 12 cards: 3 jokers, 9 safe
    cards = ['🃏'] * 3 + ['🎴'] * 9
    random.shuffle(cards)
    revealed = []
    safe_count = 0
    
    for i in range(5):
        card = random.choice([c for c in cards if c not in revealed])
        revealed.append(card)
        if card == '🎴':
            safe_count += 1
        else:
            break
    
    multipliers = {5: 5.0, 4: 3.0, 3: 2.0, 2: 1.5, 1: 1.2, 0: 0}
    multiplier = multipliers.get(safe_count, 0)
    final_multiplier = multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
    
    if multiplier > 0:
        win_amount = int(amount_parsed * final_multiplier)
        await db.update_balance(user_id, win_amount, f"Evil Jokers win: {final_multiplier:.2f}x")
        await db.record_win(user_id, "EVILJOKERS", amount_parsed, win_amount, final_multiplier)
        await db.update_user_stats(user_id, won=True)
        
        embed = discord.Embed(title="🃏 Evil Jokers - WIN!", description=f"**{' '.join(revealed)}**\nSafe cards: {safe_count}", color=0x00ff00)
        embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
        embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        await ctx.send(embed=embed)
    else:
        await db.update_user_stats(user_id, won=False)
        embed = discord.Embed(title="🃏 Evil Jokers - LOST!", description=f"**{' '.join(revealed)}**\nHit a Joker!", color=0xff0000)
        embed.add_field(name="Lost", value=f"**{amount_parsed}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        await ctx.send(embed=embed)
    
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

@require_guild()
@bot.command()
@cooldown_check()
async def fight(ctx, opponent_or_amount=None, amount: str = None):
    """Interactive fight game: .fight @user amount (PvP) or .fight amount (vs bot)"""
    user_id = ctx.author.id
    
    # Parse arguments
    if opponent_or_amount is None:
        # .fight (use default 10 vs bot)
        is_pvp = False
        opponent = None
        opponent_id = bot.user.id
        amount = "10"
    else:
        # Try to convert to Member first (for PvP)
        try:
            converter = commands.MemberConverter()
            opponent = await converter.convert(ctx, str(opponent_or_amount))
            is_pvp = True
            opponent_id = opponent.id
            if amount is None:
                amount = "10"
            
            if opponent_id == user_id:
                await ctx.send("❌ You can't fight yourself!")
                return
            
            if opponent.bot and opponent.id != bot.user.id:
                await ctx.send("❌ You can only challenge real players or use `.fight <amount>` to play vs bot!")
                return
        except (commands.BadArgument, commands.MemberNotFound):
            # Not a member mention, try as amount (vs bot)
            try:
                amount = str(opponent_or_amount)
                is_pvp = False
                opponent = None
                opponent_id = bot.user.id
            except (ValueError, TypeError):
                await ctx.send("❌ Invalid format! Use: `.fight @user amount` or `.fight amount`")
                return
    
    # Parse amount
    amount_parsed = await parse_amount(amount, user_id)
    if amount_parsed is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount_parsed < 1:
        await ctx.send("❌ Minimum bet is 1 point!")
        return
    
    # Validate balance
    balance = await db.get_balance(user_id)
    if balance < amount_parsed:
        await ctx.send("❌ Insufficient balance!")
        return
    
    if is_pvp:
        # PvP: Use challenge system
        async def start_fight_pvp(ctx_inner, interaction, player1, player2, amount_inner):
            # Deduct balances from BOTH players
            await db.update_balance(player1.id, -amount_inner, "Fight bet")
            await db.update_balance(player2.id, -amount_inner, "Fight bet")
            await db.add_wager(player1.id, amount_inner)
            await db.add_wager(player2.id, amount_inner)
            
            # Create game
            game = FightGame(player1.id, player2.id, amount_inner, is_pvp=True)
            session = game_session_manager.create_session(
                GameType.FIGHT, player1.id, player2.id, amount_inner, 
                ctx_inner.channel.id, game, is_pvp=True
            )
            
            # Show game start
            embed = discord.Embed(title="⚔ Fight Started!", description="Turn-based combat! Choose Attack or Heal each turn.", color=0xFFD700)
            embed.add_field(name=f"{player1.display_name} (P1)", value=f"❤️ HP: **{game.player1_hp}**/120", inline=True)
            embed.add_field(name=f"{player2.display_name} (P2)", value=f"❤️ HP: **{game.player2_hp}**/120", inline=True)
            embed.add_field(name="Bet Amount (each)", value=f"**{amount_inner}** points", inline=False)
            embed.add_field(name="Current Turn", value=f"**{player1.mention}** (Player 1)", inline=False)
            
            view = FightTurnView(session, ctx_inner)
            await interaction.followup.send(embed=embed, view=view)
        
        # Initiate challenge
        await initiate_multiplayer_challenge(
            ctx, ctx.author, opponent, "Fight", amount_parsed, start_fight_pvp
        )
    else:
        # VS BOT: Check daily limit and start immediately
        can_play, remaining, is_vip_check = await play_limiter.check_and_increment(user_id, 'fight')
        if not can_play:
            vip_text = " (VIP)" if is_vip_check else ""
            return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **fight** today{vip_text}.\n"
                                 f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
        
        # Deduct balance
        await db.update_balance(user_id, -amount_parsed, "Fight bet (vs bot)")
        await db.add_wager(user_id, amount_parsed)
        await db.record_activity(user_id, "play_fight")
        
        # Create game
        game = FightGame(user_id, bot.user.id, amount_parsed, is_pvp=False)
        session = game_session_manager.create_session(
            GameType.FIGHT, user_id, bot.user.id, amount_parsed,
            ctx.channel.id, game, is_pvp=False
        )
        
        # Show game start
        embed = discord.Embed(title="⚔ Fight vs Bot!", description="Turn-based combat! Choose Attack or Heal each turn.", color=0xFFD700)
        embed.add_field(name=f"{ctx.author.display_name}", value=f"❤️ HP: **{game.player1_hp}**/120", inline=True)
        embed.add_field(name="Bot", value=f"❤️ HP: **{game.player2_hp}**/120", inline=True)
        embed.add_field(name="Bet Amount", value=f"**{amount_parsed}** points", inline=False)
        embed.add_field(name="Current Turn", value=f"**{ctx.author.mention}** - Your move!", inline=False)
        
        view = FightTurnView(session, ctx)
        await ctx.send(embed=embed, view=view)
        await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")


# Fight Turn View (Discord UI for Attack/Heal buttons)
class FightTurnView(discord.ui.View):
    def __init__(self, session, ctx):
        super().__init__(timeout=180)
        self.session = session
        self.ctx = ctx
        self.game = session.game_state
        
    async def show_game_state(self, interaction):
        """Update embed to show current game state"""
        game = self.game
        is_pvp = game.is_pvp
        
        # Get player names
        player1 = await bot.fetch_user(game.player1_id)
        if is_pvp:
            player2 = await bot.fetch_user(game.player2_id)
            player2_name = player2.display_name
        else:
            player2_name = "Bot"
        
        # Build embed
        if not game.game_over:
            current_player = await bot.fetch_user(game.current_turn)
            embed = discord.Embed(title="⚔ Fight in Progress", description=game.get_battle_summary(), color=0xFFD700)
            embed.add_field(name=f"{player1.display_name} (P1)", 
                          value=f"❤️ HP: **{game.player1_hp}**/120\n💚 Heal: {'✅ Ready' if game.player1_heal_cooldown == 0 else f'⏳ {game.player1_heal_cooldown} turn'}", 
                          inline=True)
            embed.add_field(name=f"{player2_name} {'(P2)' if is_pvp else ''}", 
                          value=f"❤️ HP: **{game.player2_hp}**/120\n💚 Heal: {'✅ Ready' if game.player2_heal_cooldown == 0 else f'⏳ {game.player2_heal_cooldown} turn'}", 
                          inline=True)
            embed.add_field(name="Current Turn", value=f"**{current_player.mention}**", inline=False)
            
            await safe_interaction_response(interaction, embed=embed, view=self)
        else:
            # Game over - show results
            await self.end_game(interaction)
    
    async def end_game(self, interaction):
        """Handle game end and payouts"""
        game = self.game
        is_pvp = game.is_pvp
        winner_id = game.winner
        loser_id = game.player1_id if winner_id == game.player2_id else game.player2_id
        
        # Get users
        winner = await bot.fetch_user(winner_id)
        loser = await bot.fetch_user(loser_id)
        
        # Calculate payout
        if is_pvp:
            # PvP: 99% of pot to winner
            total_pot = game.bet_amount * 2
            win_amount = int(total_pot * 0.99)
        else:
            # vs Bot: 1.8x with VIP/boost multipliers
            is_vip = await db.is_vip(winner_id)
            boost_multiplier = await db.get_total_boost_multiplier(winner_id)
            multiplier = 1.8
            final_multiplier = multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
            win_amount = int(game.bet_amount * final_multiplier)
        
        # Award winner
        await db.update_balance(winner_id, win_amount, "Fight win")
        await db.record_win(winner_id, "FIGHT", game.bet_amount, win_amount, win_amount / game.bet_amount)
        await db.update_user_stats(winner_id, won=True)
        await db.update_user_stats(loser_id, won=False)
        
        # Build final embed
        embed = discord.Embed(title="⚔ Fight Over - VICTORY!", description=game.get_battle_summary(), color=0x00ff00)
        embed.add_field(name="Winner", value=f"**{winner.mention}**", inline=True)
        embed.add_field(name="Prize", value=f"**{win_amount}** points! 🎉", inline=True)
        embed.add_field(name=f"{winner.display_name} HP", value=f"❤️ **{game.player1_hp if winner_id == game.player1_id else game.player2_hp}**/120", inline=False)
        
        await safe_interaction_response(interaction, embed=embed, view=None)
        
        # Remove session
        game_session_manager.remove_session(game.player1_id)
        
        # Check rank up
        await RankManager.check_rank_up(self.ctx, winner_id)
    
    @discord.ui.button(label="⚔ Attack", style=discord.ButtonStyle.danger, row=0)
    async def attack_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        game = self.game
        
        # Validate it's the player's turn
        if interaction.user.id != game.current_turn:
            await interaction.response.send_message("❌ It's not your turn!", ephemeral=True)
            return
        
        # Execute attack
        game.execute_action(interaction.user.id, "attack")
        
        # If vs bot and game not over, bot takes turn immediately
        if not game.is_pvp and not game.game_over:
            bot_action = game.bot_choose_action()
            game.execute_action(bot.user.id, bot_action)
        
        # Update game state
        await self.show_game_state(interaction)
    
    @discord.ui.button(label="💚 Heal", style=discord.ButtonStyle.success, row=0)
    async def heal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        game = self.game
        
        # Validate it's the player's turn
        if interaction.user.id != game.current_turn:
            await interaction.response.send_message("❌ It's not your turn!", ephemeral=True)
            return
        
        # Check if heal is available
        if not game.can_heal(interaction.user.id):
            await interaction.response.send_message("❌ Heal is on cooldown! Wait 1 turn.", ephemeral=True)
            return
        
        # Execute heal
        game.execute_action(interaction.user.id, "heal")
        
        # If vs bot and game not over, bot takes turn immediately
        if not game.is_pvp and not game.game_over:
            bot_action = game.bot_choose_action()
            game.execute_action(bot.user.id, bot_action)
        
        # Update game state
        await self.show_game_state(interaction)

@require_guild()
@bot.command()
@cooldown_check()
async def ghosts(ctx, amount: str):
    """Hunt for ghosts in this special Halloween event!"""
    user_id = ctx.author.id
    
    amount_parsed = await parse_amount(amount, user_id)
    if amount_parsed is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount_parsed <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount_parsed:
        await ctx.send("❌ Insufficient balance!")
        return
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'ghosts')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **ghosts** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount_parsed, "Ghost Hunt bet")
    await db.add_wager(user_id, amount_parsed)
    await db.record_activity(user_id, "play_ghosts")
    
    # Pre-determine room contents
    room_types = ['👻 Friendly Ghost', '😱 Scary Ghost', '🎃 Pumpkin (safe)', '🦇 Bat (safe)', '🕷️ Spider (safe)', '💀 Treasure Ghost']
    multipliers_map = {'👻 Friendly Ghost': 2.0, '😱 Scary Ghost': 0, '🎃 Pumpkin (safe)': 1.3, '🦇 Bat (safe)': 1.8, '🕷️ Spider (safe)': 2.5, '💀 Treasure Ghost': 3.5}
    weights = [25, 20, 20, 20, 10, 5]
    rooms = random.choices(range(len(room_types)), weights=weights, k=6)
    
    class GhostsView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
        
        async def explore_room(self, interaction: discord.Interaction, room_num: int):
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            room_content = room_types[rooms[room_num]]
            multiplier = multipliers_map[room_content]
            final_multiplier = multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
            
            if multiplier > 0:
                win_amount = int(amount_parsed * final_multiplier)
                await db.update_balance(user_id, win_amount, f"Ghost Hunt win: {final_multiplier:.2f}x")
                await db.record_win(user_id, "GHOSTS", amount_parsed, win_amount, final_multiplier)
                await db.update_user_stats(user_id, won=True)
                
                embed = discord.Embed(title="👻 Ghost Hunt - SAFE!", description=f"Room #{room_num + 1} had: **{room_content}**!", color=0x00ff00)
                embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
                embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
                embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                await safe_interaction_response(interaction, embed=embed, view=None)
            else:
                await db.update_user_stats(user_id, won=False)
                embed = discord.Embed(title="👻 Ghost Hunt - SCARED!", description=f"Room #{room_num + 1}: **{room_content}**! 😱", color=0xff0000)
                embed.add_field(name="Lost", value=f"**{amount_parsed}** points", inline=True)
                embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                await safe_interaction_response(interaction, embed=embed, view=None)
            
            await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
        
        @discord.ui.button(label='Room 1', style=discord.ButtonStyle.primary, emoji='🚪', row=0)
        async def room1(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.explore_room(interaction, 0)
        
        @discord.ui.button(label='Room 2', style=discord.ButtonStyle.primary, emoji='🚪', row=0)
        async def room2(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.explore_room(interaction, 1)
        
        @discord.ui.button(label='Room 3', style=discord.ButtonStyle.primary, emoji='🚪', row=0)
        async def room3(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.explore_room(interaction, 2)
        
        @discord.ui.button(label='Room 4', style=discord.ButtonStyle.primary, emoji='🚪', row=1)
        async def room4(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.explore_room(interaction, 3)
        
        @discord.ui.button(label='Room 5', style=discord.ButtonStyle.primary, emoji='🚪', row=1)
        async def room5(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.explore_room(interaction, 4)
        
        @discord.ui.button(label='Room 6', style=discord.ButtonStyle.primary, emoji='🚪', row=1)
        async def room6(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.explore_room(interaction, 5)
    
    view = GhostsView()
    embed = discord.Embed(title="👻 Ghost Hunt", description="Choose a haunted room to explore! Some rooms are safe, others... not so much! 👻", color=0x9B59B6)
    embed.add_field(name="Bet", value=f"**{amount_parsed}** points", inline=True)
    embed.add_field(name="Rewards", value="Friendly Ghost: 3x | Creatures: 1.5-2.5x | Scary Ghost: Loss!", inline=False)
    await ctx.send(embed=embed, view=view)

@require_guild()
@bot.command()
@cooldown_check()
async def gn(ctx, opponent: discord.Member, amount: str = "10"):
    """Play Guess The Number against another user"""
    user_id = ctx.author.id
    
    if opponent.bot or opponent.id == user_id:
        await ctx.send("❌ Invalid opponent! Use .gtn for solo mode.")
        return
    
    amount_parsed = await parse_amount(amount, user_id)
    if amount_parsed is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount_parsed <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    opponent_balance = await db.get_balance(opponent.id)
    
    if balance < amount_parsed:
        await ctx.send("❌ Insufficient balance!")
        return
    
    if opponent_balance < amount_parsed:
        await ctx.send(f"❌ {opponent.mention} has insufficient balance!")
        return
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'gn')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **gn** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    await db.update_balance(user_id, -amount_parsed, "Guess The Number PvP bet")
    await db.update_balance(opponent.id, -amount_parsed, "Guess The Number PvP bet")
    await db.add_wager(user_id, amount_parsed)
    await db.add_wager(opponent.id, amount_parsed)
    
    target = random.randint(1, 100)
    player_guess = random.randint(1, 100)
    opponent_guess = random.randint(1, 100)
    
    player_diff = abs(target - player_guess)
    opponent_diff = abs(target - opponent_guess)
    
    total_pot = amount_parsed * 2
    house_edge = int(total_pot * 0.01)
    win_amount = total_pot - house_edge
    
    if player_diff < opponent_diff:
        await db.update_balance(user_id, win_amount, "Guess The Number PvP win")
        await db.update_user_stats(user_id, won=True)
        await db.update_user_stats(opponent.id, won=False)
        
        embed = discord.Embed(title="🔢 Guess The Number PvP - WIN!", 
                            description=f"Target: **{target}**\nYour guess: {player_guess} (off by {player_diff})\n{opponent.mention}'s guess: {opponent_guess} (off by {opponent_diff})", 
                            color=0x00ff00)
        embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        await ctx.send(embed=embed)
    elif opponent_diff < player_diff:
        await db.update_balance(opponent.id, win_amount, "Guess The Number PvP win")
        await db.update_user_stats(user_id, won=False)
        await db.update_user_stats(opponent.id, won=True)
        
        embed = discord.Embed(title="🔢 Guess The Number PvP - LOST!", 
                            description=f"Target: **{target}**\nYour guess: {player_guess} (off by {player_diff})\n{opponent.mention}'s guess: {opponent_guess} (off by {opponent_diff})", 
                            color=0xff0000)
        embed.add_field(name="Lost", value=f"**{amount_parsed}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        await ctx.send(embed=embed)
    else:
        await db.update_balance(user_id, amount_parsed, "Guess The Number PvP tie - refund")
        await db.update_balance(opponent.id, amount_parsed, "Guess The Number PvP tie - refund")
        
        embed = discord.Embed(title="🔢 Guess The Number PvP - TIE!", 
                            description=f"Target: **{target}**\nBoth off by {player_diff}! Bets refunded.", 
                            color=0xffff00)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        await ctx.send(embed=embed)
    
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

# ========== NEW CASINO GAMES (DECEMBER 2025) ==========
@require_guild()
@bot.command()
@cooldown_check()
async def treasurehunt(ctx, amount: str):
    """Hunt for treasure by picking a chest!"""
    user_id = ctx.author.id
    
    amount_parsed = await parse_amount(amount, user_id)
    if amount_parsed is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount_parsed <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount_parsed:
        await ctx.send("❌ Insufficient balance!")
        return
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'treasurehunt')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **treasurehunt** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount_parsed, "Treasure Hunt bet")
    await db.add_wager(user_id, amount_parsed)
    await db.record_activity(user_id, "play_treasurehunt")
    
    # Pre-determine chest contents (hidden from player)
    multipliers = [0, 1.5, 2.0, 2.5, 3.5]
    weights = [30, 35, 20, 12, 3]
    chest_contents = random.choices(range(len(multipliers)), weights=weights, k=5)
    
    class ChestView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
        
        async def open_chest(self, interaction: discord.Interaction, chest_num: int):
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
                return
            
            chest_names = ['📦 Empty', '🎁 Small Treasure', '💎 Medium Treasure', '👑 Large Treasure', '🏆 Jackpot!']
            multiplier = multipliers[chest_contents[chest_num]]
            final_multiplier = multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
            
            if multiplier > 0:
                win_amount = int(amount_parsed * final_multiplier)
                await db.update_balance(user_id, win_amount, f"Treasure Hunt win: {final_multiplier:.2f}x")
                await db.record_win(user_id, "TREASUREHUNT", amount_parsed, win_amount, final_multiplier)
                await db.update_user_stats(user_id, won=True)
                
                embed = discord.Embed(title="🗺️ Treasure Hunt - FOUND!", description=f"Chest #{chest_num + 1} contained: **{chest_names[chest_contents[chest_num]]}**!", color=0x00ff00)
                embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
                embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
                embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                embed.set_image(url=WIN_IMAGES['treasurehunt'])
                await safe_interaction_response(interaction, embed=embed, view=None)
            else:
                await db.update_user_stats(user_id, won=False)
                embed = discord.Embed(title="🗺️ Treasure Hunt - EMPTY!", description=f"Chest #{chest_num + 1} was empty! 💔", color=0xff0000)
                embed.add_field(name="Lost", value=f"**{amount_parsed}** points", inline=True)
                embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
                embed.set_image(url=LOSS_IMAGES['treasurehunt'])
                await safe_interaction_response(interaction, embed=embed, view=None)
            
            await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")
        
        @discord.ui.button(label='Chest 1', style=discord.ButtonStyle.primary, emoji='📦', row=0)
        async def chest1(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.open_chest(interaction, 0)
        
        @discord.ui.button(label='Chest 2', style=discord.ButtonStyle.primary, emoji='📦', row=0)
        async def chest2(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.open_chest(interaction, 1)
        
        @discord.ui.button(label='Chest 3', style=discord.ButtonStyle.primary, emoji='📦', row=0)
        async def chest3(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.open_chest(interaction, 2)
        
        @discord.ui.button(label='Chest 4', style=discord.ButtonStyle.primary, emoji='📦', row=1)
        async def chest4(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.open_chest(interaction, 3)
        
        @discord.ui.button(label='Chest 5', style=discord.ButtonStyle.primary, emoji='📦', row=1)
        async def chest5(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.open_chest(interaction, 4)
    
    view = ChestView()
    embed = discord.Embed(title="🗺️ Treasure Hunt", description="Pick a chest to open! One contains treasure...", color=0xFFD700)
    embed.add_field(name="Bet", value=f"**{amount_parsed}** points", inline=True)
    embed.add_field(name="Possible Wins", value="Empty, 1.5x, 2.0x, 2.5x, 5.0x", inline=True)
    await ctx.send(embed=embed, view=view)

@require_guild()
@bot.command()
@cooldown_check()
async def valentines(ctx, amount: str):
    """Play the special Valentine's Day slots!"""
    user_id = ctx.author.id
    
    amount_parsed = await parse_amount(amount, user_id)
    if amount_parsed is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount_parsed <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount_parsed:
        await ctx.send("❌ Insufficient balance!")
        return
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'valentines')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **valentines** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount_parsed, "Valentine's Day Slots bet")
    await db.add_wager(user_id, amount_parsed)
    await db.record_activity(user_id, "play_valentines")
    
    # Valentine-themed symbols
    symbols = ['💖', '💝', '🌹', '💐', '💍', '🍫', '💌']
    weights = [15, 12, 20, 18, 8, 20, 7]
    reels = random.choices(symbols, weights=weights, k=3)
    
    multiplier = 0
    if reels[0] == reels[1] == reels[2]:
        if reels[0] == '💍': multiplier = 5.0
        elif reels[0] == '💖': multiplier = 4.0
        elif reels[0] == '💝': multiplier = 3.5
        elif reels[0] == '💌': multiplier = 3.0
        else: multiplier = 2.0
    elif reels.count('💖') >= 2 or reels.count('💝') >= 2: 
        multiplier = 1.5
    
    final_multiplier = multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
    
    if multiplier > 0:
        win_amount = int(amount_parsed * final_multiplier)
        await db.update_balance(user_id, win_amount, f"Valentine's Day Slots win: {final_multiplier:.2f}x")
        await db.record_win(user_id, "VALENTINES", amount_parsed, win_amount, final_multiplier)
        await db.update_user_stats(user_id, won=True)
        
        embed = discord.Embed(title="💘 Valentine's Day Slots - WIN!", description=f"**{' '.join(reels)}**", color=0xff69b4)
        embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
        embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=WIN_IMAGES['valentines'])
        await ctx.send(embed=embed)
    else:
        await db.update_user_stats(user_id, won=False)
        embed = discord.Embed(title="💘 Valentine's Day Slots - LOST", description=f"**{' '.join(reels)}**", color=0xff0000)
        embed.add_field(name="Lost", value=f"**{amount_parsed}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=LOSS_IMAGES['valentines'])
        await ctx.send(embed=embed)
    
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

@require_guild()
@bot.command()
@cooldown_check()
async def war(ctx, amount: str):
    """Card war - highest card wins!"""
    user_id = ctx.author.id
    
    amount_parsed = await parse_amount(amount, user_id)
    if amount_parsed is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount_parsed <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount_parsed:
        await ctx.send("❌ Insufficient balance!")
        return
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'war')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **war** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount_parsed, "War bet")
    await db.add_wager(user_id, amount_parsed)
    await db.record_activity(user_id, "play_war")
    
    # Draw cards
    cards = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    card_values = {c: i+2 for i, c in enumerate(cards)}
    
    player_card = random.choice(cards)
    dealer_card = random.choice(cards)
    
    player_value = card_values[player_card]
    dealer_value = card_values[dealer_card]
    
    if player_value > dealer_value:
        # Win
        multiplier = 1.9
        final_multiplier = multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
        win_amount = int(amount_parsed * final_multiplier)
        await db.update_balance(user_id, win_amount, f"War win: {final_multiplier:.2f}x")
        await db.record_win(user_id, "WAR", amount_parsed, win_amount, final_multiplier)
        await db.update_user_stats(user_id, won=True)
        
        embed = discord.Embed(title="🃏 Card War - WIN!", description=f"Your **{player_card}** beats Dealer's **{dealer_card}**!", color=0x00ff00)
        embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
        embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=WIN_IMAGES['war'])
        await ctx.send(embed=embed)
    elif player_value == dealer_value:
        # Tie - refund
        await db.update_balance(user_id, amount_parsed, "War tie - refund")
        embed = discord.Embed(title="🃏 Card War - TIE!", description=f"Both drew **{player_card}** - Bet refunded!", color=0xffff00)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        await ctx.send(embed=embed)
    else:
        # Loss
        await db.update_user_stats(user_id, won=False)
        embed = discord.Embed(title="🃏 Card War - LOST!", description=f"Your **{player_card}** lost to Dealer's **{dealer_card}**!", color=0xff0000)
        embed.add_field(name="Lost", value=f"**{amount_parsed}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=LOSS_IMAGES['war'])
        await ctx.send(embed=embed)
    
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

@require_guild()
@bot.command()
@cooldown_check()
async def wheelcolor(ctx, amount: str, color: str = None):
    """Spin the wheel and bet on blue, red, or green!"""
    user_id = ctx.author.id
    
    if color is None:
        await ctx.send("❌ Choose a color! Usage: `.wheelcolor [amount] [blue/red/green]`\n💙 **Blue** (2x) - Most common\n❤️ **Red** (2.5x) - Less common\n💚 **Green** (5x) - Rare!")
        return
    
    color = color.lower()
    if color not in ['blue', 'red', 'green']:
        await ctx.send("❌ Invalid color! Choose **blue**, **red**, or **green**!")
        return
    
    amount_parsed = await parse_amount(amount, user_id)
    if amount_parsed is None:
        await ctx.send("❌ Invalid amount! Use a number, 'half', or 'all'")
        return
    
    if amount_parsed <= 0:
        await ctx.send("❌ Positive bet amount!")
        return
    
    balance = await db.get_balance(user_id)
    if balance < amount_parsed:
        await ctx.send("❌ Insufficient balance!")
        return
    
    can_play, remaining, is_vip_check = await play_limiter.check_and_increment(ctx.author.id, 'wheelcolor')
    if not can_play:
        vip_text = " (VIP)" if is_vip_check else ""
        return await ctx.send(f"❌ Daily limit reached! You've used all your plays for **wheelcolor** today{vip_text}.\n"
                             f"💡 {'VIP users get 10 plays/day!' if not is_vip_check else 'Come back tomorrow!'}")
    
    is_vip = await db.is_vip(user_id)
    boost_multiplier = await db.get_total_boost_multiplier(user_id)
    
    await db.update_balance(user_id, -amount_parsed, "Wheel Color bet")
    await db.add_wager(user_id, amount_parsed)
    await db.record_activity(user_id, "play_wheelcolor")
    
    # 48 slots: 24 blue, 20 red, 4 green
    wheel_slots = ['blue'] * 24 + ['red'] * 20 + ['green'] * 4
    result_color = random.choice(wheel_slots)
    
    color_emojis = {'blue': '💙', 'red': '❤️', 'green': '💚'}
    color_multipliers = {'blue': 2.0, 'red': 2.5, 'green': 5.0}
    
    if result_color == color:
        # Win
        multiplier = color_multipliers[color]
        final_multiplier = multiplier * (1.15 if is_vip else 1.0) * boost_multiplier
        win_amount = int(amount_parsed * final_multiplier)
        await db.update_balance(user_id, win_amount, f"Wheel Color win: {final_multiplier:.2f}x")
        await db.record_win(user_id, "WHEELCOLOR", amount_parsed, win_amount, final_multiplier)
        await db.update_user_stats(user_id, won=True)
        
        embed = discord.Embed(title="🎡 Wheel Color - WIN!", description=f"Landed on {color_emojis[result_color]} **{result_color.upper()}**!", color=0x00ff00)
        embed.add_field(name="Your Bet", value=f"{color_emojis[color]} {color.upper()}", inline=True)
        embed.add_field(name="Multiplier", value=f"{final_multiplier:.2f}x", inline=True)
        embed.add_field(name="Won", value=f"**{win_amount}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=WIN_IMAGES['wheelcolor'])
        await ctx.send(embed=embed)
    else:
        # Loss
        await db.update_user_stats(user_id, won=False)
        embed = discord.Embed(title="🎡 Wheel Color - LOST!", description=f"Landed on {color_emojis[result_color]} **{result_color.upper()}**!", color=0xff0000)
        embed.add_field(name="Your Bet", value=f"{color_emojis[color]} {color.upper()}", inline=True)
        embed.add_field(name="Lost", value=f"**{amount_parsed}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=LOSS_IMAGES['wheelcolor'])
        await ctx.send(embed=embed)
    
    await ctx.send(f"🎮 Remaining plays today: **{remaining}**/{'10' if is_vip_check else '5'}")

# Wordly cooldown storage (user_id: last_play_time)
wordly_cooldowns = {}

@require_guild()
@bot.command()
async def wordly(ctx, word: str = None):
    """Type a word starting with given 3 letters (skill game, no wager)!"""
    user_id = ctx.author.id
    
    # Check cooldown (60 seconds)
    now = time.time()
    if user_id in wordly_cooldowns:
        time_left = 60 - (now - wordly_cooldowns[user_id])
        if time_left > 0:
            await ctx.send(f"⏳ Cooldown! Wait **{int(time_left)}** seconds before playing again!")
            return
    
    # Generate 3-letter prefix
    consonants = 'BCDFGHJKLMNPQRSTVWXYZ'
    vowels = 'AEIOU'
    prefix = random.choice(consonants) + random.choice(vowels) + random.choice(consonants)
    
    if word is None:
        await ctx.send(f"🔤 **Wordly Challenge!**\n\nType a valid English word starting with: **{prefix}**\n\nUsage: `.wordly [your_word]`\n💡 No wager required - earn points for correct words!")
        return
    
    word = word.upper().strip()
    
    # Basic validation
    if not word.startswith(prefix):
        await ctx.send(f"❌ Your word must start with **{prefix}**!")
        return
    
    if len(word) < 4:
        await ctx.send(f"❌ Word must be at least 4 letters long!")
        return
    
    # Simple dictionary check (basic English words)
    common_words = ['BACK', 'BALL', 'BANK', 'BASE', 'BEAR', 'BEAT', 'BEEN', 'BELL', 'BEST', 'BILL', 'BIRD', 'BLUE', 'BOAT', 'BODY', 'BOOK', 'BORN', 'BOTH', 'CALL', 'CAME', 'CAMP', 'CARD', 'CARE', 'CASE', 'CITY', 'COME', 'COOL', 'DEEP', 'DOOR', 'DOWN', 'DRAW', 'EVEN', 'EVER', 'FACE', 'FACT', 'FAIR', 'FALL', 'FARM', 'FAST', 'FEEL', 'FEET', 'FELL', 'FELT', 'FILL', 'FIND', 'FINE', 'FIRE', 'FIRM', 'FISH', 'FIVE', 'FOOD', 'FOOT', 'FORM', 'FOUR', 'FREE', 'FROM', 'FULL', 'GAME', 'GAVE', 'GIRL', 'GIVE', 'GOLD', 'GOOD', 'HALF', 'HALL', 'HAND', 'HARD', 'HAVE', 'HEAD', 'HEAR', 'HEAT', 'HELD', 'HELP', 'HERE', 'HIGH', 'HOLD', 'HOME', 'HOPE', 'HOUR', 'IDEA', 'JUST', 'KEEP', 'KIND', 'KING', 'LAND', 'LAST', 'LATE', 'LEAD', 'LEFT', 'LESS', 'LIFE', 'LINE', 'LIST', 'LIVE', 'LONG', 'LOOK', 'LOSE', 'LOST', 'LOVE', 'MADE', 'MAIN', 'MAKE', 'MANY', 'MARK', 'MEET', 'MILE', 'MIND', 'MISS', 'MOON', 'MORE', 'MOST', 'MOVE', 'MUCH', 'MUST', 'NAME', 'NEAR', 'NEED', 'NEVER', 'NEXT', 'NICE', 'NIGHT', 'NOTE', 'ONLY', 'OPEN', 'OVER', 'PAGE', 'PAID', 'PAIR', 'PART', 'PASS', 'PAST', 'PATH', 'PICK', 'PLAN', 'PLAY', 'POOR', 'PULL', 'RACE', 'RAIN', 'RANG', 'RATE', 'READ', 'REAL', 'REST', 'RICH', 'RIDE', 'RING', 'RISE', 'ROAD', 'ROCK', 'ROLL', 'ROOM', 'RULE', 'SAFE', 'SAID', 'SALE', 'SAME', 'SAVE', 'SEAT', 'SEEM', 'SELL', 'SEND', 'SENT', 'SHIP', 'SHOP', 'SHOT', 'SHOW', 'SIDE', 'SIGN', 'SING', 'SIZE', 'SLOW', 'SNOW', 'SOME', 'SONG', 'SOON', 'SORT', 'STAR', 'STAY', 'STEP', 'STOP', 'SUCH', 'SURE', 'TAKE', 'TALK', 'TALL', 'TEAM', 'TELL', 'TERM', 'TEST', 'THAN', 'THAT', 'THEM', 'THEN', 'THEY', 'THIN', 'THIS', 'TIME', 'TOLD', 'TOOK', 'TOWN', 'TREE', 'TRUE', 'TURN', 'TYPE', 'UNIT', 'UPON', 'USED', 'VERY', 'WAIT', 'WALK', 'WALL', 'WANT', 'WARM', 'WATCH', 'WAVE', 'WEEK', 'WELL', 'WENT', 'WERE', 'WEST', 'WHAT', 'WHEN', 'WIDE', 'WIFE', 'WILD', 'WILL', 'WIND', 'WISH', 'WITH', 'WOOD', 'WORD', 'WORK', 'YEAR']
    
    # Check if word exists (simplified check)
    is_valid = word in common_words or len(word) >= 6  # Accept longer words as potentially valid
    
    if is_valid:
        # Award points based on word length
        points = len(word) * 5
        await db.update_balance(user_id, points, f"Wordly win: {word}")
        await db.record_activity(user_id, "play_wordly")
        
        wordly_cooldowns[user_id] = now
        
        embed = discord.Embed(title="🔤 Wordly - CORRECT!", description=f"**{word}** is a valid word!", color=0x00ff00)
        embed.add_field(name="Word Length", value=f"{len(word)} letters", inline=True)
        embed.add_field(name="Earned", value=f"**{points}** points", inline=True)
        embed.add_field(name="Balance", value=f"{await db.get_balance(user_id):,} points", inline=False)
        embed.set_image(url=WIN_IMAGES['wordly'])
        await ctx.send(embed=embed)
    else:
        wordly_cooldowns[user_id] = now
        embed = discord.Embed(title="🔤 Wordly - INVALID!", description=f"**{word}** is not in our dictionary!", color=0xff0000)
        embed.add_field(name="Try Again", value=f"Use `.wordly` for a new word challenge!", inline=False)
        embed.set_image(url=LOSS_IMAGES['wordly'])
        await ctx.send(embed=embed)


@require_guild()
@bot.command()
@cooldown_check()
async def daily(ctx):
    user_id = ctx.author.id
    
    # Check if user has at least 10 points
    balance = await db.get_balance(user_id)
    if balance < 10:
        await ctx.send(f"❌ You need at least **10 points** to claim daily rewards! Your balance: **{balance}** points")
        return
    
    if not await db.can_claim_daily(user_id):
        msg = await localization.translate(user_id, "economy.daily_already_claimed", db)
        await ctx.send(msg)
        return
    
    # Fixed daily amount: 1 point (no VIP/boost bonuses)
    daily_amount = 1
    
    new_balance = await db.update_balance(user_id, daily_amount, "Daily reward claim")
    await db.set_daily_claimed(user_id)
    
    title = await localization.translate(user_id, "economy.daily_claimed", db, amount=daily_amount)
    embed = discord.Embed(title=title, color=0x00ff00)
    embed.add_field(name="Reward", value=f"**{daily_amount}** point", inline=True)
    embed.add_field(name="New Balance", value=f"**{new_balance:,}** points", inline=True)
    embed.set_footer(text="Come back tomorrow for another daily reward! (Requires 10+ points)")
    await ctx.send(embed=embed)

@require_guild()
@bot.command()
@cooldown_check()
async def monthly(ctx):
    user_id = ctx.author.id
    
    can_claim, message = await db.can_claim_monthly(user_id)
    if not can_claim:
        await ctx.send(f"❌ {message}")
        return
    
    # Check monthly wager requirement
    monthly_wager = await db.get_monthly_wager(user_id)
    
    if monthly_wager < 100:
        await ctx.send(f"❌ You need to wager at least **100 points** this month to claim the monthly bonus!\n📊 Current wager: **{monthly_wager}** points\n💡 Wager **{100 - monthly_wager}** more points to unlock your monthly reward!")
        return
    
    # Fixed monthly amount: 40 points
    monthly_amount = 40
    
    new_balance = await db.update_balance(user_id, monthly_amount, f"Monthly reward: {monthly_wager:,} wagered")
    await db.reset_monthly_wager(user_id)
    
    title = await localization.translate(user_id, "economy.monthly_claimed", db, amount=monthly_amount)
    embed = discord.Embed(title=title, color=0xFFD700)
    embed.add_field(name="Monthly Wager", value=f"**{monthly_wager:,}** points", inline=True)
    embed.add_field(name="Reward", value=f"**{monthly_amount}** points", inline=True)
    embed.add_field(name="New Balance", value=f"**{new_balance:,}** points", inline=True)
    embed.set_footer(text="Your monthly wager has been reset. Wager 100+ points to earn next month's reward!")
    await ctx.send(embed=embed)

# ========== RANK & STATS COMMANDS ==========
class RankManager:
    @staticmethod
    async def check_rank_up(ctx, user_id):
        total_wagered = await db.get_total_wagered(user_id)
        current_rank = "🎯 Novice"
        current_threshold = 0
        
        for threshold, rank_name in sorted(RANK_SYSTEM.items()):
            if total_wagered >= threshold:
                current_rank = rank_name
                current_threshold = threshold
            else:
                break
        
        next_threshold = None
        for threshold in sorted(RANK_SYSTEM.keys()):
            if total_wagered < threshold:
                next_threshold = threshold
                break
        
        if next_threshold and total_wagered >= next_threshold:
            rank_name = RANK_SYSTEM[next_threshold]
            embed = discord.Embed(title="🎉 NEW RANK ACHIEVED! 🎉", description=f"**{ctx.author.display_name}** reached **{rank_name}**!", color=0x00ff00)
            embed.add_field(name="Points Wagered", value=f"**{next_threshold:,}** points", inline=True)
            bonus = next_threshold // 10
            await db.update_balance(user_id, bonus, f"Rank up bonus: {rank_name}")
            embed.add_field(name="Rank Bonus", value=f"**{bonus}** points", inline=True)
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)

@require_guild()
@bot.command()
@cooldown_check()
async def rank(ctx, member: discord.Member = None):
    target = member or ctx.author
    if (member and await db.is_private_profile(member.id) and not ctx.author.guild_permissions.administrator and member.id != ctx.author.id):
        await ctx.send("❌ This user has a private profile!")
        return
    
    total_wagered = await db.get_total_wagered(target.id)
    current_rank = "🎯 Novice"
    current_threshold = 0
    next_rank = None
    next_threshold = None
    
    for threshold, rank_name in sorted(RANK_SYSTEM.items()):
        if total_wagered >= threshold:
            current_rank = rank_name
            current_threshold = threshold
        elif next_rank is None and total_wagered < threshold:
            next_rank = rank_name
            next_threshold = threshold
    
    embed = discord.Embed(title=f"🏆 Rank of {target.display_name}", color=0xFFD700)
    embed.add_field(name="Current Rank", value=f"**{current_rank}**", inline=False)
    embed.add_field(name="Total Points Wagered", value=f"**{total_wagered:,}**", inline=True)
    
    if next_rank:
        progress = total_wagered - current_threshold
        needed = next_threshold - current_threshold
        percentage = (progress / needed) * 100 if needed > 0 else 100
        
        embed.add_field(name="Next Rank", value=f"**{next_rank}**", inline=True)
        embed.add_field(name="Points Needed", value=f"**{next_threshold:,}**", inline=True)
        embed.add_field(name="Progress", value=f"**{progress:,}** / **{needed:,}** ({percentage:.1f}%)", inline=False)
        
        bars = 20
        filled_bars = int((percentage / 100) * bars)
        progress_bar = "█" * filled_bars + "░" * (bars - filled_bars)
        embed.add_field(name="Progress Bar", value=f"`{progress_bar}`", inline=False)
    else:
        embed.add_field(name="🎊 Congratulations!", value="You reached the maximum rank! 👑", inline=False)
    
    if await db.is_private_profile(target.id):
        embed.set_footer(text="🔒 Private Profile")
    
    embed.set_thumbnail(url=target.display_avatar.url)
    await ctx.send(embed=embed)

@require_guild()
@bot.command()
@cooldown_check()
async def ranks(ctx):
    embed = discord.Embed(title="🏆 All Ranks", description="Wager points to climb the ranks!", color=0xFFD700)
    
    rank_list = []
    for threshold, rank_name in sorted(RANK_SYSTEM.items()):
        rank_list.append(f"**{rank_name}** - {threshold:,} points")
    
    embed.description = "\n".join(rank_list)
    embed.set_footer(text="Use .rank to see your current progress!")
    await ctx.send(embed=embed)

@require_guild()
@bot.command()
@cooldown_check()
async def leaderboard(ctx):
    top_users = await db.get_top_users(10)
    
    if not top_users:
        await ctx.send("❌ No users found on the leaderboard!")
        return
    
    embed = discord.Embed(title="🏆 Top 10 Leaderboard", description="Top players by total wagered", color=0xFFD700)
    
    for index, (user_id, total_wagered) in enumerate(top_users, 1):
        try:
            user = await bot.fetch_user(user_id)
            username = user.name
        except:
            username = f"User {user_id}"
        
        medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"**{index}.**"
        embed.add_field(name=f"{medal} {username}", value=f"{total_wagered:,} points wagered", inline=False)
    
    await ctx.send(embed=embed)

@require_guild()
@bot.command()
@cooldown_check()
async def stats(ctx, member: discord.Member = None):
    target = member or ctx.author
    if (member and await db.is_private_profile(member.id) and not ctx.author.guild_permissions.administrator and member.id != ctx.author.id):
        await ctx.send("❌ This user has a private profile!")
        return
    
    user_stats = await db.get_user_stats(target.id)
    
    if not user_stats:
        await ctx.send(f"❌ {target.mention} hasn't played any games yet!")
        return
    
    embed = discord.Embed(title=f"📊 Stats of {target.display_name}", color=0x00aaff)
    embed.add_field(name="🎮 Games Played", value=f"**{user_stats['games_played']:,}**", inline=True)
    embed.add_field(name="✅ Games Won", value=f"**{user_stats['games_won']:,}**", inline=True)
    embed.add_field(name="📈 Win Rate", value=f"**{user_stats['win_rate']:.1f}%**", inline=True)
    embed.add_field(name="🔥 Current Streak", value=f"**{user_stats['current_streak']}**", inline=True)
    embed.add_field(name="🏆 Max Streak", value=f"**{user_stats['max_streak']}**", inline=True)
    embed.set_thumbnail(url=target.display_avatar.url)
    
    if await db.is_private_profile(target.id):
        embed.set_footer(text="🔒 Private Profile")
    
    await ctx.send(embed=embed)

@require_guild()
@bot.command()
@cooldown_check()
async def achievements(ctx, member: discord.Member = None):
    target = member or ctx.author
    if (member and await db.is_private_profile(member.id) and not ctx.author.guild_permissions.administrator and member.id != ctx.author.id):
        await ctx.send("❌ This user has a private profile!")
        return
    
    user_achievements = await db.get_achievements(target.id)
    
    embed = discord.Embed(title=f"🏆 Achievements of {target.display_name}", color=0xFFD700)
    
    unlocked_count = len(user_achievements)
    total_count = len(ACHIEVEMENTS)
    
    embed.description = f"**{unlocked_count}/{total_count}** Achievements Unlocked"
    
    for achievement_id, achievement_data in ACHIEVEMENTS.items():
        is_unlocked = achievement_id in user_achievements
        status = "✅" if is_unlocked else "🔒"
        embed.add_field(
            name=f"{status} {achievement_data['name']}", 
            value=achievement_data['description'], 
            inline=True
        )
    
    embed.set_thumbnail(url=target.display_avatar.url)
    
    if await db.is_private_profile(target.id):
        embed.set_footer(text="🔒 Private Profile")
    
    await ctx.send(embed=embed)

# ========== ECONOMY COMMANDS ==========
@require_guild()
@bot.command()
@cooldown_check()
async def balance(ctx, member: discord.Member = None):
    target = member or ctx.author
    user_id = ctx.author.id
    
    # Get translations
    title = await localization.translate(user_id, "economy.balance_title", db, name=target.display_name)
    points_label = await localization.translate(user_id, "economy.points_label", db)
    eur_label = await localization.translate(user_id, "economy.eur_value_label", db)
    wagered_label = await localization.translate(user_id, "economy.wagered_label", db)
    rank_label = await localization.translate(user_id, "economy.rank_label", db)
    vip_label = await localization.translate(user_id, "economy.vip_label", db)
    boosts_label = await localization.translate(user_id, "economy.boosts_label", db)
    rate_label = await localization.translate(user_id, "economy.rate_label", db)
    rate_value = await localization.translate(user_id, "economy.rate_value", db)
    private_msg = await localization.translate(user_id, "economy.private_profile", db)
    
    if (member and await db.is_private_profile(member.id) and not ctx.author.guild_permissions.administrator and member.id != ctx.author.id):
        await ctx.send(private_msg)
        return
    
    balance = await db.get_balance(target.id)
    eur_value = balance * POINT_TO_EUR
    total_wagered = await db.get_total_wagered(target.id)
    vip_info = await db.get_vip_info(target.id)
    boosts = await db.get_active_boosts(target.id)
    
    current_rank = "🎯 Novice"
    for threshold, rank_name in sorted(RANK_SYSTEM.items(), reverse=True):
        if total_wagered >= threshold:
            current_rank = rank_name
            break
    
    embed = discord.Embed(title=f"💰 {title}", description="━━━━━━━━━━━━━━━━━━━━", color=0xFFD700)
    embed.add_field(name="💵 Points", value=f"**${balance:,}**", inline=True)
    embed.add_field(name="💶 EUR Value", value=f"**€{eur_value:.2f}**", inline=True)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value="", inline=False)
    embed.add_field(name="🎲 Total Wagered", value=f"**${total_wagered:,}**", inline=True)
    embed.add_field(name="🏆 Rank", value=f"**{current_rank}**", inline=True)
    
    if vip_info['is_vip']:
        vip_text = await localization.translate(user_id, "economy.vip_days_left", db, days=vip_info['days_left'])
        embed.add_field(name="⭐ VIP Status", value=vip_text, inline=True)
    
    if boosts:
        boost_text = "\n".join([f"🚀 {boost['name']} ({boost['multiplier']}x)" for boost in boosts.values()])
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value="", inline=False)
        embed.add_field(name="🎁 Active Boosts", value=boost_text, inline=False)
    
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━", value="", inline=False)
    embed.add_field(name="💱 Exchange Rate", value=f"**1 point = €0.01**", inline=True)
    
    if await db.is_private_profile(target.id):
        embed.set_footer(text=private_msg)
    
    embed.set_thumbnail(url=target.display_avatar.url)
    await ctx.send(embed=embed)

@require_guild()
@bot.command()
@cooldown_check()
async def balhistory(ctx, limit: int = 15):
    """
    View your balance history - the bot remembers all your balance changes!
    Usage: .balhistory [limit]
    """
    user_id = ctx.author.id
    
    if limit < 1 or limit > 50:
        await ctx.send("❌ Limit must be between 1 and 50!")
        return
    
    history = await db.get_balance_history(user_id, limit)
    
    if not history:
        embed = discord.Embed(title="📊 Balance History", color=0xFFA500)
        embed.description = "No balance history yet! Play some games to start building your history."
        embed.set_footer(text="The bot remembers every balance change!")
        await ctx.send(embed=embed)
        return
    
    embed = discord.Embed(
        title=f"📊 Balance History - Last {len(history)} Changes",
        color=0x3498db,
        timestamp=datetime.datetime.utcnow()
    )
    
    for i, (old_bal, new_bal, change, reason, timestamp) in enumerate(history, 1):
        change_emoji = "📈" if change > 0 else "📉"
        change_sign = "+" if change > 0 else ""
        
        # Format timestamp
        try:
            dt = datetime.datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%d/%m %H:%M")
        except:
            time_str = "Unknown"
        
        field_name = f"{change_emoji} {time_str} - {reason[:30]}"
        field_value = f"`{old_bal:,}` → `{new_bal:,}` ({change_sign}{change:,})"
        
        embed.add_field(name=field_name, value=field_value, inline=False)
    
    current_balance = await db.get_balance(user_id)
    embed.set_footer(text=f"Current Balance: {current_balance:,} points | Use .balhistory [number] to see more/less")
    
    await ctx.send(embed=embed)

@require_guild()
@bot.command()
@cooldown_check()
async def convert(ctx, amount: float):
    """
    Convert EUR to points
    Usage: .convert 10.50
    """
    if amount <= 0:
        await ctx.send("❌ Amount must be positive!")
        return
    
    if amount > 1000000:
        await ctx.send("❌ Amount too large! Maximum: €1,000,000")
        return
    
    # 1 point = €0.01, so €1 = 100 points
    points = int(amount * 100)
    
    embed = discord.Embed(title="💱 EUR to Points Conversion", color=0x3498db)
    embed.add_field(name="💶 EUR Amount", value=f"**€{amount:.2f}**", inline=True)
    embed.add_field(name="💰 Points", value=f"**{points:,}** points", inline=True)
    embed.add_field(name="💎 Exchange Rate", value="1 point = €0.01", inline=False)
    embed.set_footer(text="Use .balance to check your current points!")
    
    await ctx.send(embed=embed)

@require_guild()
@bot.command()
@cooldown_check()
async def rakeback(ctx):
    user_id = ctx.author.id
    rakeback_amount = await db.get_rakeback(user_id)
    balance = await db.get_balance(user_id)
    
    # Generate custom image with profile picture, name, and balance
    image_data = await generate_rakeback_image(ctx.author, balance, rakeback_amount)
    
    if image_data:
        # Send image
        file = discord.File(image_data, filename="rakeback.png")
        embed = discord.Embed(color=0x00ff00)
        embed.set_image(url="attachment://rakeback.png")
        embed.set_footer(text="Use .claimrakeback to claim your rakeback! You earn 1% rakeback on all wagers.")
        await ctx.send(file=file, embed=embed)
    else:
        # Fallback to text embed if image generation fails
        embed = discord.Embed(title="💸 Rakeback Info", color=0x00ff00)
        embed.add_field(name="👤 Player", value=f"**{ctx.author.display_name}**", inline=True)
        embed.add_field(name="💰 Balance", value=f"**${balance:,}** points", inline=True)
        embed.add_field(name="💸 Available Rakeback", value=f"**${rakeback_amount:,}** points", inline=True)
        embed.add_field(name="Rakeback Rate", value="**1%** of all wagers", inline=True)
        embed.set_footer(text="Use .claimrakeback to claim your rakeback!")
        await ctx.send(embed=embed)

@require_guild()
@bot.command()
@cooldown_check()
async def claimrakeback(ctx):
    user_id = ctx.author.id
    rakeback_amount = await db.claim_rakeback(user_id)
    
    if rakeback_amount <= 0:
        msg = await localization.translate(user_id, "economy.no_rakeback", db)
        await ctx.send(msg)
        return
    
    new_balance = await db.update_balance(user_id, rakeback_amount, "Rakeback claim")
    
    title = await localization.translate(user_id, "economy.rakeback_claimed", db, amount=rakeback_amount)
    embed = discord.Embed(title=title, color=0x00ff00)
    embed.add_field(name="Rakeback Amount", value=f"**{rakeback_amount:,}** points", inline=True)
    embed.add_field(name="New Balance", value=f"**{new_balance:,}** points", inline=True)
    embed.set_footer(text="You earn 1% rakeback on all wagers!")
    await ctx.send(embed=embed)

# Rain View for button interaction
class RainView(discord.ui.View):
    def __init__(self, host_id, total_amount):
        super().__init__(timeout=60)
        self.host_id = host_id
        self.total_amount = total_amount
        self.participants = set()
        self.ended = False
    
    @discord.ui.button(label="💸 Claim Rain", style=discord.ButtonStyle.success, emoji="💰")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ended:
            await interaction.response.send_message("❌ This rain has ended!", ephemeral=True)
            return
        
        if interaction.user.id == self.host_id:
            await interaction.response.send_message("❌ You can't claim your own rain!", ephemeral=True)
            return
        
        if interaction.user.id in self.participants:
            await interaction.response.send_message("❌ You already claimed!", ephemeral=True)
            return
        
        self.participants.add(interaction.user.id)
        await interaction.response.send_message(f"✅ You're in! {len(self.participants)} participant(s) so far!", ephemeral=True)
    
    async def end_rain(self, ctx):
        self.ended = True
        self.stop()
        
        if len(self.participants) == 0:
            # Refund if no one claimed
            await db.update_balance(self.host_id, self.total_amount, "Rain refunded (no participants)")
            return 0, []
        
        # Calculate per-person amount (supports decimals)
        per_person = round(self.total_amount / len(self.participants), 2)
        
        # Distribute to all participants
        participants_list = []
        for user_id in self.participants:
            await db.update_balance(user_id, per_person, f"Rain from {ctx.author.display_name}")
            participants_list.append(user_id)
        
        return per_person, participants_list

@require_guild()
@bot.command()
@cooldown_check()
async def rain(ctx, amount: float):
    """Make it rain! Share points with everyone who clicks the button"""
    if amount < 0.01:
        await ctx.send("❌ Minimum rain amount is 0.01 points!")
        return
    
    user_id = ctx.author.id
    balance = await db.get_balance(user_id)
    
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    # Deduct amount
    await db.update_balance(user_id, -amount, f"Started rain of {amount} points")
    
    # Create rain view
    view = RainView(user_id, amount)
    
    embed = discord.Embed(
        title="💸 IT'S RAINING POINTS! 💸",
        description=f"**{ctx.author.mention}** is making it rain **{amount:,.2f}** points!\n\n"
                    f"Click the button below to claim your share!",
        color=0xFFD700
    )
    embed.add_field(name="Total Pool", value=f"{amount:,.2f} points", inline=True)
    embed.add_field(name="Time Limit", value="60 seconds", inline=True)
    embed.set_footer(text="The more people claim, the more it gets divided!")
    
    message = await ctx.send("@everyone", embed=embed, view=view)
    
    # Wait for timeout
    await asyncio.sleep(60)
    
    # End rain and distribute
    per_person, participants = await view.end_rain(ctx)
    
    if len(participants) == 0:
        final_embed = discord.Embed(
            title="💸 Rain Ended",
            description=f"No one claimed the rain! **{amount:,.2f}** points refunded to {ctx.author.mention}",
            color=0xff0000
        )
    else:
        participant_mentions = [f"<@{uid}>" for uid in participants[:10]]  # Show first 10
        if len(participants) > 10:
            participant_mentions.append(f"... and {len(participants) - 10} more")
        
        final_embed = discord.Embed(
            title="💸 Rain Ended!",
            description=f"**{len(participants)}** people claimed the rain!",
            color=0x00ff00
        )
        final_embed.add_field(name="Per Person", value=f"**{per_person:,.2f}** points", inline=True)
        final_embed.add_field(name="Total Distributed", value=f"**{amount:,.2f}** points", inline=True)
        final_embed.add_field(name="Participants", value="\n".join(participant_mentions), inline=False)
    
    await message.edit(embed=final_embed, view=None)

@require_guild()
@bot.command()
@cooldown_check()
async def tip(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ Positive amount only!")
        return
    
    if member.id == ctx.author.id:
        await ctx.send("❌ You cannot tip yourself!")
        return
    
    user_id = ctx.author.id
    balance = await db.get_balance(user_id)
    
    if balance < amount:
        await ctx.send("❌ Insufficient balance!")
        return
    
    await db.update_balance(user_id, -amount, f"Tip sent to {member.display_name}")
    await db.update_balance(member.id, amount, f"Tip received from {ctx.author.display_name}")
    
    embed = discord.Embed(title="💰 Tip Sent!", color=0x00ff00)
    embed.add_field(name="From", value=ctx.author.mention, inline=True)
    embed.add_field(name="To", value=member.mention, inline=True)
    embed.add_field(name="Amount", value=f"**{amount:,}** points", inline=True)
    await ctx.send(embed=embed)
    
    try:
        await member.send(f"💰 You received a tip of **{amount:,}** points from {ctx.author.mention}!")
    except:
        pass

@require_guild()
@bot.command()
@cooldown_check()
async def price(ctx):
    embed = discord.Embed(title="💎 Points to EUR Conversion", color=0x00ff00)
    embed.add_field(name="Exchange Rate", value=f"**1 point = €{POINT_TO_EUR:.2f}**", inline=False)
    embed.add_field(name="Examples", value=f"100 points = €1.00\n1,000 points = €10.00\n10,000 points = €100.00", inline=False)
    await ctx.send(embed=embed)

@require_guild()
@bot.command()
@cooldown_check()
async def privacy(ctx, setting: str = None):
    if setting is None:
        is_private = await db.is_private_profile(ctx.author.id)
        status = "🔒 Private" if is_private else "🔓 Public"
        embed = discord.Embed(title="🔒 Privacy Settings", color=0x00aaff)
        embed.add_field(name="Current Status", value=status, inline=False)
        embed.add_field(name="Usage", value="`.privacy on` - Set profile to private\n`.privacy off` - Set profile to public", inline=False)
        await ctx.send(embed=embed)
        return
    
    if setting.lower() == "on":
        await db.set_private_profile(ctx.author.id, True)
        await ctx.send("🔒 Your profile is now **private**. Others cannot see your stats.")
    elif setting.lower() == "off":
        await db.set_private_profile(ctx.author.id, False)
        await ctx.send("🔓 Your profile is now **public**. Others can see your stats.")
    else:
        await ctx.send("❌ Invalid setting! Use `.privacy on` or `.privacy off`")

async def notify_lottery_purchase(user_id: int, tickets_bought: int):
    """Send notification to lottery channel when someone buys tickets"""
    try:
        lottery_channel = bot.get_channel(LOTTERY_CHANNEL_ID)
        if not lottery_channel:
            return
        
        # Get current lottery info
        lottery_info = await db.get_lottery_info()
        unique_participants = len(lottery_info['user_tickets'])
        total_tickets = lottery_info['total_tickets']
        prize_pool = lottery_info['total_pool']
        
        # Create embed
        embed = discord.Embed(
            title="🎫 Lottery Ticket Purchase!",
            description=f"<@{user_id}> just bought **{tickets_bought}** ticket(s)!",
            color=0xFFD700,
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="🎟 Tickets Bought", value=f"**{tickets_bought}** 🎫", inline=True)
        embed.add_field(name="👥 Participants Today", value=f"**{unique_participants}** player(s)", inline=True)
        embed.add_field(name="💰 Prize Pool", value=f"**{prize_pool:,}** points", inline=True)
        embed.add_field(name="🎫 Total Tickets", value=f"**{total_tickets}** tickets", inline=True)
        embed.add_field(name="⏰ Next Draw", value="**7 PM HKT** (11:00 UTC)", inline=True)
        embed.add_field(name="💡 Tip", value="More tickets = Better odds!", inline=True)
        embed.set_footer(text="🎊 Good luck! Use .lottery to buy tickets!")
        
        await lottery_channel.send(embed=embed)
    except Exception as e:
        print(f"Error sending lottery notification: {e}")

@require_guild()
@bot.command()
@cooldown_check()
async def lottery(ctx, action: str = None):
    """Interactive lottery system - Buy tickets with buttons or admin commands"""
    user_id = ctx.author.id
    
    # Admin command: .lottery opening
    if action and action.lower() == "opening":
        # Check if user is admin
        is_admin = False
        if ctx.author.id in BOT_ADMIN_USER_IDS:
            is_admin = True
        elif ctx.guild:
            member_roles = [role.id for role in ctx.author.roles]
            is_admin = any(role_id in BOT_ADMIN_ROLE_IDS for role_id in member_roles)
        
        if not is_admin:
            await ctx.send("❌ Only admins can use `.lottery opening`!")
            return
        
        # Send lottery opening announcement to lottery channel
        lottery_channel = bot.get_channel(LOTTERY_CHANNEL_ID)
        if not lottery_channel:
            await ctx.send(f"❌ Lottery channel not found! (ID: {LOTTERY_CHANNEL_ID})")
            return
        
        embed = discord.Embed(
            title="🎫 DAILY LOTTERY NOW OPEN! 🎫",
            description="**The lottery is now active!**\n\n🎰 Buy tickets and win the jackpot!\n💰 1 ticket = 1 point (€0.01)\n🏆 Winner takes 100% of the prize pool!\n⏰ Draw at 7 PM Hong Kong Time daily",
            color=0xFFD700,
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="💵 How to Play", value="Use `.lottery` to buy tickets with interactive buttons!", inline=False)
        embed.add_field(name="🎟 Ticket Options", value="• **1 ticket** = 1 point\n• **10 tickets** = 10 points\n• **100 tickets** = 100 points\n• **1000 tickets** = 1,000 points", inline=True)
        embed.add_field(name="🎁 Prize Pool", value="100% funded by players - Casino takes 0%!", inline=True)
        embed.add_field(name="⏰ Draw Time", value="**7 PM HKT** (11:00 UTC) daily", inline=True)
        embed.set_footer(text="🎊 Good luck everyone! More tickets = Better chance to win! 🎊")
        
        await lottery_channel.send(content="@everyone", embed=embed)
        await ctx.send(f"✅ Lottery opening announcement sent to <#{LOTTERY_CHANNEL_ID}>!")
        
        # Log admin command
        await ModLogger.log_command(ctx.author, "lottery opening",
                                    action_details="Opened daily lottery",
                                    result="Announcement sent to lottery channel")
        return
    
    # Regular user - show interactive buttons
    balance = await db.get_balance(user_id)
    user_tickets = await db.get_lottery_tickets(user_id)
    
    class LotteryView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
        
        async def buy_tickets(self, interaction: discord.Interaction, ticket_count: int):
            if interaction.user.id != user_id:
                await interaction.response.send_message("❌ This is not your lottery menu!", ephemeral=True)
                return
            
            ticket_price = 1
            total_cost = ticket_count * ticket_price
            
            current_balance = await db.get_balance(user_id)
            
            if current_balance < total_cost:
                await interaction.response.send_message(
                    f"❌ Insufficient balance! You need **{total_cost:,}** points for {ticket_count} ticket(s).\nYour balance: **{current_balance:,}** points",
                    ephemeral=True
                )
                return
            
            await db.update_balance(user_id, -total_cost, f"Lottery: Bought {ticket_count} ticket(s)")
            await db.add_lottery_tickets(user_id, ticket_count)
            
            # Send notification to lottery channel
            await notify_lottery_purchase(user_id, ticket_count)
            
            new_balance = await db.get_balance(user_id)
            total_user_tickets = await db.get_lottery_tickets(user_id)
            
            embed = discord.Embed(title="🎫 Lottery Tickets Purchased!", color=0xFFD700)
            embed.add_field(name="Tickets Bought", value=f"**{ticket_count}** 🎟", inline=True)
            embed.add_field(name="Cost", value=f"**{total_cost:,}** points (€{total_cost * POINT_TO_EUR:.2f})", inline=True)
            embed.add_field(name="Your Total Tickets", value=f"**{total_user_tickets}** 🎫", inline=True)
            embed.add_field(name="New Balance", value=f"**{new_balance:,}** points", inline=True)
            embed.add_field(name="⏰ Next Draw", value="**7 PM HKT** (11:00 UTC)", inline=True)
            embed.add_field(name="💡 Tip", value="More tickets = Better chance!", inline=True)
            embed.set_footer(text="🎊 Good luck! Prize pool is 100% from player tickets!")
            await safe_interaction_response(interaction, embed=embed, view=None)
        
        @discord.ui.button(label='🎟 1 Ticket (1 pt)', style=discord.ButtonStyle.primary, custom_id='buy_1')
        async def buy_1_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.buy_tickets(interaction, 1)
        
        @discord.ui.button(label='🎟 10 Tickets (10 pts)', style=discord.ButtonStyle.primary, custom_id='buy_10')
        async def buy_10_tickets(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.buy_tickets(interaction, 10)
        
        @discord.ui.button(label='🎟 100 Tickets (100 pts)', style=discord.ButtonStyle.success, custom_id='buy_100')
        async def buy_100_tickets(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.buy_tickets(interaction, 100)
        
        @discord.ui.button(label='🎟 1000 Tickets (1k pts)', style=discord.ButtonStyle.danger, custom_id='buy_1000')
        async def buy_1000_tickets(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.buy_tickets(interaction, 1000)
    
    view = LotteryView()
    embed = discord.Embed(
        title="🎫 Daily Lottery - Buy Tickets!",
        description=f"**Choose how many tickets to buy:**\n\n💰 1 ticket = 1 point (€0.01)\n🏆 Win 100% of the prize pool!\n⏰ Daily draw at 7 PM HKT",
        color=0xFFD700
    )
    embed.add_field(name="Your Balance", value=f"**{balance:,}** points", inline=True)
    embed.add_field(name="Your Tickets", value=f"**{user_tickets}** 🎫", inline=True)
    embed.add_field(name="Next Draw", value="**7 PM HKT** (11:00 UTC)", inline=True)
    embed.set_footer(text="Click a button below to buy tickets! More tickets = Better odds!")
    await ctx.send(embed=embed, view=view)

@require_guild()
@bot.command()
@cooldown_check()
async def lotteryinfo(ctx):
    total_pool = await db.get_lottery_pool()
    user_tickets = await db.get_lottery_tickets(ctx.author.id)
    total_tickets = await db.get_total_lottery_tickets()
    
    win_chance = (user_tickets / total_tickets * 100) if total_tickets > 0 else 0
    
    embed = discord.Embed(title="🎫 Lottery Information", color=0xFFD700)
    embed.add_field(name="💰 Prize Pool", value=f"**{total_pool:,}** points", inline=True)
    embed.add_field(name="🎟 Your Tickets", value=f"**{user_tickets}**", inline=True)
    embed.add_field(name="🌍 Total Tickets", value=f"**{total_tickets}**", inline=True)
    embed.add_field(name="📊 Your Win Chance", value=f"**{win_chance:.2f}%**", inline=True)
    embed.add_field(name="💵 Ticket Price", value="**1** point", inline=True)
    embed.add_field(name="⏰ Next Draw", value="**18:00 daily**", inline=True)
    embed.set_footer(text="Use .lottery [amount] to buy tickets!")
    await ctx.send(embed=embed)

# ========== ADMIN COMMANDS ==========
@require_guild()
@bot.command()
@is_bot_admin()
async def addpoints(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ Positive amount only!")
        return
    
    new_balance = await db.update_balance(member.id, amount, f"Admin: Points added by {ctx.author.display_name}")
    embed = discord.Embed(title="💰 Points Added", color=0x00ff00, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="User", value=member.mention, inline=True)
    embed.add_field(name="Amount Added", value=f"**{amount}** points", inline=True)
    embed.add_field(name="New Balance", value=f"**{new_balance}** points", inline=True)
    embed.add_field(name="Admin", value=ctx.author.mention, inline=True)
    await ctx.send(embed=embed)
    
    # Log admin command
    await ModLogger.log_command(ctx.author, "addpoints", member, 
                                action_details=f"Added {amount} points",
                                result=f"New balance: {new_balance} points")

@require_guild()
@bot.command()
@is_bot_admin()
async def addvip(ctx, member: discord.Member, days: int):
    await db.add_vip(member.id, days)
    expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    embed = discord.Embed(title="⭐ VIP Added", color=0xFFD700, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="User", value=member.mention, inline=True)
    embed.add_field(name="VIP Duration", value=f"**{days}** days", inline=True)
    embed.add_field(name="Expires", value=f"{expiry}", inline=True)
    embed.add_field(name="Admin", value=ctx.author.mention, inline=True)
    await ctx.send(embed=embed)
    
    # Log admin command
    await ModLogger.log_command(ctx.author, "addvip", member,
                                action_details=f"Added VIP for {days} days",
                                result=f"Expires: {expiry}")

@require_guild()
@bot.command()
@is_bot_admin()
async def removevip(ctx, member: discord.Member):
    await db.remove_vip(member.id)
    embed = discord.Embed(title="⭐ VIP Removed", color=0xff0000, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="User", value=member.mention, inline=True)
    embed.add_field(name="Admin", value=ctx.author.mention, inline=True)
    await ctx.send(embed=embed)
    
    # Log admin command
    await ModLogger.log_command(ctx.author, "removevip", member,
                                action_details="Removed VIP status")

@require_guild()
@bot.command()
@is_bot_admin()
async def addboost(ctx, member: discord.Member, days: int, boost_level: int):
    if boost_level not in [1, 2, 3]:
        await ctx.send("❌ Boost level must be 1, 2, or 3!")
        return
    
    boost_types = {1: 'boost1', 2: 'boost2', 3: 'boost3'}
    boost_multipliers = {1: 1.5, 2: 2.0, 3: 3.0}
    
    await db.add_boost(member.id, boost_types[boost_level], days)
    expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    embed = discord.Embed(title="🚀 Boost Added", color=0x00ffff, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="User", value=member.mention, inline=True)
    embed.add_field(name="Boost Level", value=f"**Level {boost_level}** ({boost_multipliers[boost_level]}x)", inline=True)
    embed.add_field(name="Duration", value=f"**{days}** days", inline=True)
    embed.add_field(name="Expires", value=f"{expiry}", inline=True)
    embed.add_field(name="Admin", value=ctx.author.mention, inline=True)
    await ctx.send(embed=embed)
    
    # Log admin command
    await ModLogger.log_command(ctx.author, "addboost", member,
                                action_details=f"Added Level {boost_level} boost for {days} days",
                                result=f"Expires: {expiry}")

@require_guild()
@bot.command()
@is_bot_admin()
async def removeboost(ctx, member: discord.Member, boost_level: int):
    if boost_level not in [1, 2, 3]:
        await ctx.send("❌ Boost level must be 1, 2, or 3!")
        return
    
    boost_types = {1: 'boost1', 2: 'boost2', 3: 'boost3'}
    await db.remove_boost(member.id, boost_types[boost_level])
    embed = discord.Embed(title="🚀 Boost Removed", color=0xff0000, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="User", value=member.mention, inline=True)
    embed.add_field(name="Boost Level", value=f"**Level {boost_level}**", inline=True)
    embed.add_field(name="Admin", value=ctx.author.mention, inline=True)
    await ctx.send(embed=embed)
    
    # Log admin command
    await ModLogger.log_command(ctx.author, "removeboost", member,
                                action_details=f"Removed Level {boost_level} boost")

@require_guild()
@bot.command()
@is_bot_admin()
async def setbalance(ctx, member: discord.Member, amount: int):
    if amount < 0:
        await ctx.send("❌ Amount cannot be negative!")
        return
    
    await db.set_balance(member.id, amount)
    embed = discord.Embed(title="💰 Balance Set", color=0x00ff00, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="User", value=member.mention, inline=True)
    embed.add_field(name="New Balance", value=f"**{amount:,}** points", inline=True)
    embed.add_field(name="Admin", value=ctx.author.mention, inline=True)
    await ctx.send(embed=embed)
    
    # Log admin command
    await ModLogger.log_command(ctx.author, "setbalance", member,
                                action_details=f"Set balance to {amount:,} points")

@require_guild()
@bot.command()
@is_bot_admin()
async def setwager(ctx, member: discord.Member, amount: int):
    if amount < 0:
        await ctx.send("❌ Amount cannot be negative!")
        return
    
    await db.set_total_wagered(member.id, amount)
    embed = discord.Embed(title="🎲 Total Wager Set", color=0x00ff00, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="User", value=member.mention, inline=True)
    embed.add_field(name="Total Wagered", value=f"**{amount:,}** points", inline=True)
    embed.add_field(name="Admin", value=ctx.author.mention, inline=True)
    await ctx.send(embed=embed)
    
    # Log admin command
    await ModLogger.log_command(ctx.author, "setwager", member,
                                action_details=f"Set total wagered to {amount:,} points")

@require_guild()
@bot.command()
@is_bot_admin()
async def addgameunlimit(ctx, member: discord.Member, duration: int):
    """Grant unlimited daily games to a user for specified duration (in days)"""
    if duration < 1:
        await ctx.send("❌ Duration must be at least 1 day!")
        return
    
    # Calculate expiry
    expires_at = datetime.datetime.now() + datetime.timedelta(days=duration)
    
    # Set unlimited games in database
    await db.execute_query(
        'UPDATE users SET unlimited_games_until = ? WHERE user_id = ?',
        (expires_at.isoformat(), member.id)
    )
    
    embed = discord.Embed(title="🎮 Unlimited Games Granted", color=0x00ff00, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="User", value=member.mention, inline=True)
    embed.add_field(name="Duration", value=f"**{duration} day(s)**", inline=True)
    embed.add_field(name="Expires", value=f"{expires_at.strftime('%Y-%m-%d %H:%M UTC')}", inline=True)
    embed.add_field(name="Admin", value=ctx.author.mention, inline=True)
    embed.description = "✨ This user now has **unlimited daily plays** for all games!"
    await ctx.send(embed=embed)
    
    # Log admin command
    await ModLogger.log_command(ctx.author, "addgameunlimit", member,
                                action_details=f"Granted unlimited games for {duration} days",
                                result=f"Expires: {expires_at.strftime('%Y-%m-%d %H:%M UTC')}")

@require_guild()
@bot.command()
@is_bot_admin()
async def removegameunlimit(ctx, member: discord.Member):
    """Remove unlimited daily games from a user"""
    # Remove unlimited games in database
    await db.execute_query(
        'UPDATE users SET unlimited_games_until = NULL WHERE user_id = ?',
        (member.id,)
    )
    
    embed = discord.Embed(title="🎮 Unlimited Games Removed", color=0xff0000, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="User", value=member.mention, inline=True)
    embed.add_field(name="Admin", value=ctx.author.mention, inline=True)
    embed.description = "This user is now back to normal daily play limits (5 regular / 10 VIP)"
    await ctx.send(embed=embed)
    
    # Log admin command
    await ModLogger.log_command(ctx.author, "removegameunlimit", member,
                                action_details="Removed unlimited games")

@require_guild()
@bot.command()
@is_bot_admin()
async def limit(ctx, limit_number: int, member: discord.Member):
    """Set custom daily play limit for a user"""
    if limit_number < 1:
        await ctx.send("❌ Limit must be at least 1 play!")
        return
    
    # Ensure user exists
    await db.ensure_user_exists(member.id)
    
    # Set custom limit in database
    await db.execute_query('''
        INSERT INTO custom_play_limits (user_id, daily_limit, set_by)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            daily_limit = excluded.daily_limit,
            set_by = excluded.set_by,
            set_at = datetime('now')
    ''', (member.id, limit_number, ctx.author.id))
    
    embed = discord.Embed(title="🎯 Custom Limit Set", color=0x00ff00, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="User", value=member.mention, inline=True)
    embed.add_field(name="Daily Limit", value=f"**{limit_number} plays/day**", inline=True)
    embed.add_field(name="Admin", value=ctx.author.mention, inline=True)
    embed.description = f"✨ This user now has a custom limit of **{limit_number} daily plays**!\n💡 This replaces their normal limit (5 regular / 10 VIP)"
    await ctx.send(embed=embed)
    
    # Log admin command
    await ModLogger.log_command(ctx.author, "limit", member,
                                action_details=f"Set custom daily limit to {limit_number} plays")

@require_guild()
@bot.command()
@is_bot_admin()
async def lost(ctx, user_input: str, games: int):
    """Force a user to lose next N games (prevents large losses)
    Usage: .lost <user_id or @user> <number_of_games>
    Example: .lost 123456789 5 or .lost @user 3
    """
    if games < 1:
        await ctx.send("❌ Number of games must be at least 1!")
        return
    
    if games > 100:
        await ctx.send("❌ Maximum 100 forced losses!")
        return
    
    # Try to get the member from mention or ID
    member = None
    user_id = None
    
    # Check if it's a mention
    if user_input.startswith('<@') and user_input.endswith('>'):
        # Extract ID from mention
        user_id_str = user_input.strip('<@!>').strip('<@>')
        try:
            user_id = int(user_id_str)
            member = ctx.guild.get_member(user_id)
        except ValueError:
            await ctx.send("❌ Invalid user mention! Please provide a valid user mention (@user) or user ID.")
            return
    else:
        # Try to parse as direct ID
        try:
            user_id = int(user_input)
            member = ctx.guild.get_member(user_id)
        except ValueError:
            await ctx.send("❌ Invalid user ID! Please provide a user mention (@user) or user ID.")
            return
    
    if not member:
        # Try to fetch from Discord if not in cache (works even if user not in channel)
        try:
            member = await bot.fetch_user(user_id)
        except:
            await ctx.send(f"❌ Could not find user with ID `{user_id}`!")
            return
    
    # Ensure user exists in database (create if not exists)
    async with aiosqlite.connect(db.db_path) as conn:
        await conn.execute('''
            INSERT OR IGNORE INTO users (user_id, balance, total_wagered, total_won, total_lost)
            VALUES (?, 1000, 0, 0, 0)
        ''', (member.id,))
        await conn.commit()
    
    # Set forced losses in database
    await db.execute_query(
        'UPDATE users SET forced_losses_remaining = ? WHERE user_id = ?',
        (games, member.id)
    )
    
    embed = discord.Embed(title="🛡 Forced Losses Activated", color=0xff6b6b, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="User", value=f"{member.mention if hasattr(member, 'mention') else f'<@{member.id}>'}", inline=True)
    embed.add_field(name="User ID", value=f"`{member.id}`", inline=True)
    embed.add_field(name="Forced Losses", value=f"**{games} game(s)**", inline=True)
    embed.add_field(name="Admin", value=ctx.author.mention, inline=True)
    embed.description = f"⚠ This user will automatically lose the next **{games} wagered game(s)**!\n💡 This helps prevent excessive wins and protects house balance."
    await ctx.send(embed=embed)
    
    # Log admin command
    await ModLogger.log_command(ctx.author, "lost", member,
                                action_details=f"Set {games} forced losses",
                                result=f"User will lose next {games} games")

@require_guild()
@bot.command()
@is_bot_admin()
async def clearforcelost(ctx, user_input: str):
    """Remove forced losses from a user
    Usage: .clearforcelost [@user or user_id]
    """
    # Try to get the member from mention or ID
    member = None
    user_id = None
    
    # Check if it's a mention
    if user_input.startswith('<@') and user_input.endswith('>'):
        # Extract ID from mention
        user_id_str = user_input.strip('<@!>').strip('<@>')
        try:
            user_id = int(user_id_str)
            member = ctx.guild.get_member(user_id)
        except ValueError:
            await ctx.send("❌ Invalid user mention! Please provide a valid user mention (@user) or user ID.")
            return
    else:
        # Try to parse as direct ID
        try:
            user_id = int(user_input)
            member = ctx.guild.get_member(user_id)
        except ValueError:
            await ctx.send("❌ Invalid user ID! Please provide a user mention (@user) or user ID.")
            return
    
    if not member:
        # Try to fetch from Discord if not in cache
        try:
            member = await bot.fetch_user(user_id)
        except:
            await ctx.send(f"❌ Could not find user with ID `{user_id}`!")
            return
    
    # Clear forced losses in database
    await db.execute_query(
        'UPDATE users SET forced_losses_remaining = 0 WHERE user_id = ?',
        (member.id,)
    )
    
    embed = discord.Embed(title="🛡 Forced Losses Cleared", color=0x00ff00, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="User", value=f"{member.mention if hasattr(member, 'mention') else f'<@{member.id}>'}", inline=True)
    embed.add_field(name="User ID", value=f"`{member.id}`", inline=True)
    embed.add_field(name="Admin", value=ctx.author.mention, inline=True)
    embed.description = "✅ This user can now win games normally again!"
    await ctx.send(embed=embed)
    
    # Log admin command
    await ModLogger.log_command(ctx.author, "clearforcelost", member,
                                action_details="Cleared forced losses")

# ========== THREAD MANAGEMENT COMMANDS ==========
@require_guild()
@bot.group(invoke_without_command=True)
async def thread(ctx):
    """Thread management commands for private gambling spaces
    Usage: .thread <create/add/remove/close>
    """
    if ctx.invoked_subcommand is None:
        embed = discord.Embed(title="🧵 Thread Management", color=0x5865F2)
        embed.description = "Create private gambling spaces with thread management!"
        embed.add_field(name="`.thread create`", value="Create a new private thread", inline=False)
        embed.add_field(name="`.thread add @user`", value="Add someone to your thread", inline=False)
        embed.add_field(name="`.thread remove @user`", value="Remove someone from your thread", inline=False)
        embed.add_field(name="`.thread close`", value="Close the current thread", inline=False)
        embed.set_footer(text="💡 All casino commands work inside threads!")
        await ctx.send(embed=embed)

@thread.command(name='create')
async def thread_create(ctx):
    """Create a private thread for gambling"""
    try:
        # Create a private thread
        thread_obj = await ctx.channel.create_thread(
            name=f"🎰 {ctx.author.name}'s Casino",
            type=discord.ChannelType.private_thread,
            auto_archive_duration=60
        )
        
        # Add the creator to the thread
        await thread_obj.add_user(ctx.author)
        
        # Send welcome message in the thread
        embed = discord.Embed(
            title="🎰 Welcome to Your Private Casino!",
            description=f"{ctx.author.mention} created this private gambling space!",
            color=0xFFD700
        )
        embed.add_field(name="🎯 Features", value="• All casino games work here!\n• Private space for you and invited users\n• Use `.thread add @user` to invite friends", inline=False)
        embed.add_field(name="📋 Commands", value="• `.thread add @user` - Add someone\n• `.thread remove @user` - Remove someone\n• `.thread close` - Close this thread", inline=False)
        embed.set_footer(text="🎲 Happy gambling!")
        
        await thread_obj.send(embed=embed)
        
        # Confirm in original channel
        await ctx.send(f"✅ Created private thread: {thread_obj.mention}")
        
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to create threads in this channel!")
    except Exception as e:
        await ctx.send(f"❌ Error creating thread: {str(e)}")

@thread.command(name='add')
async def thread_add(ctx, member: discord.Member):
    """Add a user to the current thread"""
    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("❌ This command only works inside a thread! Use `.thread create` first.")
        return
    
    try:
        await ctx.channel.add_user(member)
        
        embed = discord.Embed(
            title="✅ User Added to Thread",
            description=f"{member.mention} has been added to this private casino!",
            color=0x00ff00
        )
        embed.set_footer(text=f"Added by {ctx.author.name}")
        await ctx.send(embed=embed)
        
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to add users to this thread!")
    except discord.HTTPException as e:
        if e.code == 50033:
            await ctx.send("❌ This thread is archived! Unarchive it first by sending a message.")
        else:
            await ctx.send(f"❌ Error adding user: {str(e)}")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@thread.command(name='remove')
async def thread_remove(ctx, member: discord.Member):
    """Remove a user from the current thread"""
    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("❌ This command only works inside a thread!")
        return
    
    if member.id == ctx.channel.owner_id:
        await ctx.send("❌ You can't remove the thread owner!")
        return
    
    if member.id == ctx.author.id:
        await ctx.send("❌ Use Discord's 'Leave Thread' button to leave, or use `.thread close` to close the thread.")
        return
    
    try:
        await ctx.channel.remove_user(member)
        
        embed = discord.Embed(
            title="🚫 User Removed from Thread",
            description=f"{member.mention} has been removed from this private casino.",
            color=0xff6b6b
        )
        embed.set_footer(text=f"Removed by {ctx.author.name}")
        await ctx.send(embed=embed)
        
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to remove users from this thread!")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@thread.command(name='close')
async def thread_close(ctx):
    """Close the current thread"""
    if not isinstance(ctx.channel, discord.Thread):
        await ctx.send("❌ This command only works inside a thread!")
        return
    
    try:
        embed = discord.Embed(
            title="🔒 Closing Thread",
            description="This private casino will be archived in 5 seconds...",
            color=0xff6b6b
        )
        embed.set_footer(text=f"Closed by {ctx.author.name}")
        await ctx.send(embed=embed)
        
        await asyncio.sleep(5)
        await ctx.channel.edit(archived=True, locked=True)
        
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to close this thread!")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@require_guild()
@bot.command()
@is_bot_admin()
async def backupall(ctx):
    """Backup all user data to JSON file (Admin only)"""
    try:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backups/casino_backup_{timestamp}.json'
        
        # Collect all user data from all tables
        backup_data = {
            'backup_timestamp': timestamp,
            'backup_date': datetime.datetime.now().isoformat(),
            'users': [],
            'daily_claims': [],
            'monthly_claims': [],
            'rakeback': [],
            'user_stats': [],
            'achievements': [],
            'user_boosts': [],
            'lottery_tickets': [],
            'language_preferences': [],
            'private_profiles': [],
            'custom_play_limits': [],
            'extra_plays_purchased': [],
            'blacklist': []
        }
        
        async with aiosqlite.connect(db.db_path) as conn:
            # Backup users table
            async with conn.execute('SELECT * FROM users') as cursor:
                columns = [description[0] for description in cursor.description]
                async for row in cursor:
                    backup_data['users'].append(dict(zip(columns, row)))
            
            # Backup daily_claims
            async with conn.execute('SELECT * FROM daily_claims') as cursor:
                columns = [description[0] for description in cursor.description]
                async for row in cursor:
                    backup_data['daily_claims'].append(dict(zip(columns, row)))
            
            # Backup monthly_claims
            async with conn.execute('SELECT * FROM monthly_claims') as cursor:
                columns = [description[0] for description in cursor.description]
                async for row in cursor:
                    backup_data['monthly_claims'].append(dict(zip(columns, row)))
            
            # Backup rakeback
            async with conn.execute('SELECT * FROM rakeback') as cursor:
                columns = [description[0] for description in cursor.description]
                async for row in cursor:
                    backup_data['rakeback'].append(dict(zip(columns, row)))
            
            # Backup user_stats
            async with conn.execute('SELECT * FROM user_stats') as cursor:
                columns = [description[0] for description in cursor.description]
                async for row in cursor:
                    backup_data['user_stats'].append(dict(zip(columns, row)))
            
            # Backup achievements
            async with conn.execute('SELECT * FROM achievements') as cursor:
                columns = [description[0] for description in cursor.description]
                async for row in cursor:
                    backup_data['achievements'].append(dict(zip(columns, row)))
            
            # Backup user_boosts
            async with conn.execute('SELECT * FROM user_boosts') as cursor:
                columns = [description[0] for description in cursor.description]
                async for row in cursor:
                    backup_data['user_boosts'].append(dict(zip(columns, row)))
            
            # Backup lottery_tickets
            async with conn.execute('SELECT * FROM lottery_tickets') as cursor:
                columns = [description[0] for description in cursor.description]
                async for row in cursor:
                    backup_data['lottery_tickets'].append(dict(zip(columns, row)))
            
            # Backup language_preferences
            async with conn.execute('SELECT * FROM language_preferences') as cursor:
                columns = [description[0] for description in cursor.description]
                async for row in cursor:
                    backup_data['language_preferences'].append(dict(zip(columns, row)))
            
            # Backup private_profiles
            async with conn.execute('SELECT * FROM private_profiles') as cursor:
                columns = [description[0] for description in cursor.description]
                async for row in cursor:
                    backup_data['private_profiles'].append(dict(zip(columns, row)))
            
            # Backup custom_play_limits
            async with conn.execute('SELECT * FROM custom_play_limits') as cursor:
                columns = [description[0] for description in cursor.description]
                async for row in cursor:
                    backup_data['custom_play_limits'].append(dict(zip(columns, row)))
            
            # Backup extra_plays_purchased
            async with conn.execute('SELECT * FROM extra_plays_purchased') as cursor:
                columns = [description[0] for description in cursor.description]
                async for row in cursor:
                    backup_data['extra_plays_purchased'].append(dict(zip(columns, row)))
            
            # Backup blacklist
            async with conn.execute('SELECT * FROM blacklist') as cursor:
                columns = [description[0] for description in cursor.description]
                async for row in cursor:
                    backup_data['blacklist'].append(dict(zip(columns, row)))
        
        # Write to JSON file
        with open(backup_filename, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        # Calculate stats
        total_users = len(backup_data['users'])
        total_balance = sum(user.get('balance', 0) for user in backup_data['users'])
        
        embed = discord.Embed(title="💾 Database Backup Complete!", color=0x00ff00, timestamp=datetime.datetime.utcnow())
        embed.add_field(name="📁 Filename", value=f"`{backup_filename}`", inline=False)
        embed.add_field(name="👥 Users Backed Up", value=f"**{total_users}**", inline=True)
        embed.add_field(name="💰 Total Balance", value=f"**{total_balance:,.2f}** points", inline=True)
        embed.add_field(name="📊 Data Tables", value=f"**{len([k for k, v in backup_data.items() if isinstance(v, list)])}** tables", inline=True)
        embed.add_field(name="⏰ Timestamp", value=timestamp, inline=True)
        embed.description = "✅ All user data has been safely backed up!\n💡 Download this file before redeploying to preserve all data."
        embed.set_footer(text="Use .restoreall to restore from backup | Keep backup file safe!")
        await ctx.send(embed=embed)
        
        # Log admin command
        await ModLogger.log_command(ctx.author, "backupall",
                                    action_details=f"Backed up {total_users} users",
                                    result=f"Saved to {backup_filename}")
        
    except Exception as e:
        await ctx.send(f"❌ Backup failed: {str(e)}")
        print(f"Backup error: {e}")

@require_guild()
@bot.command()
@is_bot_admin()
async def restoreall(ctx, filename: str = None):
    """Restore all user data from backup JSON file (Admin only)
    Usage: .restoreall casino_backup_20241113_120000.json
    Or upload the backup file as attachment with command .restoreall
    """
    try:
        backup_file = None
        
        # Check if file is attached
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            if not attachment.filename.endswith('.json'):
                await ctx.send("❌ Please attach a valid JSON backup file!")
                return
            
            # Download attachment
            backup_file = f'backups/temp_restore.json'
            await attachment.save(backup_file)
        elif filename:
            # Use provided filename
            if not filename.startswith('backups/'):
                filename = f'backups/{filename}'
            backup_file = filename
        else:
            await ctx.send("❌ Please provide a backup filename or attach a backup file!\nUsage: `.restoreall casino_backup_YYYYMMDD_HHMMSS.json`\nOr attach the backup file and use `.restoreall`")
            return
        
        # Check if file exists
        if not os.path.exists(backup_file):
            await ctx.send(f"❌ Backup file not found: `{backup_file}`")
            return
        
        # Load backup data
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        # Confirmation message
        total_users = len(backup_data.get('users', []))
        backup_timestamp = backup_data.get('backup_timestamp', 'Unknown')
        
        confirm_embed = discord.Embed(title="⚠️ RESTORE CONFIRMATION", color=0xff6600)
        confirm_embed.add_field(name="📁 Backup File", value=f"`{backup_file}`", inline=False)
        confirm_embed.add_field(name="⏰ Backup Date", value=backup_timestamp, inline=True)
        confirm_embed.add_field(name="👥 Users in Backup", value=f"**{total_users}**", inline=True)
        confirm_embed.description = "⚠️ **WARNING:** This will replace ALL current data!\n\n**Type `.confirmrestore` within 30 seconds to proceed.**"
        await ctx.send(embed=confirm_embed)
        
        # Wait for confirmation
        def check(m):
            return m.author.id == ctx.author.id and m.content.lower() == '.confirmrestore'
        
        try:
            await bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("❌ Restore cancelled - confirmation timed out.")
            return
        
        # Proceed with restore
        async with aiosqlite.connect(db.db_path) as conn:
            # Clear existing data (keep schema)
            await conn.execute('DELETE FROM users')
            await conn.execute('DELETE FROM daily_claims')
            await conn.execute('DELETE FROM monthly_claims')
            await conn.execute('DELETE FROM rakeback')
            await conn.execute('DELETE FROM user_stats')
            await conn.execute('DELETE FROM achievements')
            await conn.execute('DELETE FROM user_boosts')
            await conn.execute('DELETE FROM lottery_tickets')
            await conn.execute('DELETE FROM language_preferences')
            await conn.execute('DELETE FROM private_profiles')
            await conn.execute('DELETE FROM custom_play_limits')
            await conn.execute('DELETE FROM extra_plays_purchased')
            await conn.execute('DELETE FROM blacklist')
            
            # Restore users
            for user_data in backup_data.get('users', []):
                columns = list(user_data.keys())
                values = list(user_data.values())
                placeholders = ','.join(['?' for _ in columns])
                await conn.execute(
                    f"INSERT INTO users ({','.join(columns)}) VALUES ({placeholders})",
                    values
                )
            
            # Restore other tables similarly
            for table in ['daily_claims', 'monthly_claims', 'rakeback', 'user_stats', 
                         'achievements', 'user_boosts', 'lottery_tickets', 'language_preferences',
                         'private_profiles', 'custom_play_limits', 'extra_plays_purchased', 'blacklist']:
                for row_data in backup_data.get(table, []):
                    if row_data:
                        columns = list(row_data.keys())
                        values = list(row_data.values())
                        placeholders = ','.join(['?' for _ in columns])
                        await conn.execute(
                            f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
                            values
                        )
            
            await conn.commit()
        
        # Success message
        restored_users = len(backup_data.get('users', []))
        total_balance = sum(user.get('balance', 0) for user in backup_data.get('users', []))
        
        success_embed = discord.Embed(title="✅ Database Restore Complete!", color=0x00ff00, timestamp=datetime.datetime.utcnow())
        success_embed.add_field(name="📁 Restored From", value=f"`{backup_file}`", inline=False)
        success_embed.add_field(name="👥 Users Restored", value=f"**{restored_users}**", inline=True)
        success_embed.add_field(name="💰 Total Balance", value=f"**{total_balance:,.2f}** points", inline=True)
        success_embed.description = "✅ All user data has been successfully restored!\n🎉 Everyone's balances, VIP status, and stats are back!"
        await ctx.send(embed=success_embed)
        
        # Log admin command
        await ModLogger.log_command(ctx.author, "restoreall",
                                    action_details=f"Restored {restored_users} users from backup",
                                    result=f"Backup file: {backup_file}")
        
    except Exception as e:
        await ctx.send(f"❌ Restore failed: {str(e)}")
        print(f"Restore error: {e}")

@require_guild()
@bot.command()
@cooldown_check()
async def buyplay(ctx, amount: int):
    """Buy extra daily plays (15 points each)"""
    user_id = ctx.author.id
    
    if amount < 1:
        await ctx.send("❌ Amount must be at least 1!")
        return
    
    if amount > 50:
        await ctx.send("❌ Maximum 50 extra plays per purchase!")
        return
    
    cost = amount * 15
    balance = await db.get_balance(user_id)
    
    if balance < cost:
        await ctx.send(f"❌ Insufficient balance! You need **{cost}** points but have **{balance}** points.")
        return
    
    # Deduct cost
    await db.update_balance(user_id, -cost, f"Bought {amount} extra plays")
    
    # Add extra plays
    today = datetime.date.today().isoformat()
    await db.execute_query('''
        INSERT INTO extra_plays_purchased (user_id, play_date, extra_plays)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, play_date) DO UPDATE SET
            extra_plays = extra_plays + excluded.extra_plays
    ''', (user_id, today, amount))
    
    new_balance = await db.get_balance(user_id)
    
    embed = discord.Embed(title="🎮 Extra Plays Purchased!", color=0x00ff00, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="Extra Plays", value=f"**+{amount} plays**", inline=True)
    embed.add_field(name="Cost", value=f"-{cost} points", inline=True)
    embed.add_field(name="New Balance", value=f"{new_balance:,} points", inline=True)
    embed.description = f"✨ You now have **{amount} extra plays** for today!\n💡 These extend your daily limit beyond 5/10 plays."
    await ctx.send(embed=embed)

@require_guild()
@bot.command(aliases=['blacklistadd'])
@is_bot_admin()
async def ban(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    """Ban user from using the bot"""
    await db.add_to_blacklist(member.id, reason, ctx.author.id)
    embed = discord.Embed(title="🚫 User Banned", color=0xff0000, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="User", value=member.mention, inline=True)
    embed.add_field(name="Reason", value=reason, inline=True)
    embed.add_field(name="By", value=ctx.author.mention, inline=True)
    await ctx.send(embed=embed)
    await ModLogger.log_command(ctx.author, "ban", member, action_details="Banned from bot", result=f"Reason: {reason}")

@require_guild()
@bot.command(aliases=['blacklistremove'])
@is_bot_admin()
async def unban(ctx, member: discord.Member):
    """Unban user from the bot"""
    await db.remove_from_blacklist(member.id)
    embed = discord.Embed(title="✅ User Unbanned", color=0x00ff00, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="User", value=member.mention, inline=True)
    embed.add_field(name="By", value=ctx.author.mention, inline=True)
    await ctx.send(embed=embed)
    await ModLogger.log_command(ctx.author, "unban", member, action_details="Unbanned from bot")

@require_guild()
@bot.command(aliases=['blacklistcheck'])
@is_bot_admin()
async def checkban(ctx, member: discord.Member):
    """Check if user is banned"""
    is_banned = await db.is_blacklisted(member.id)
    if is_banned:
        embed = discord.Embed(title="🚫 Ban Status", color=0xff0000)
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Status", value="**BANNED**", inline=True)
    else:
        embed = discord.Embed(title="✅ Ban Status", color=0x00ff00)
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Status", value="**NOT BANNED**", inline=True)
    await ctx.send(embed=embed)

@require_guild()
@bot.command()
@is_bot_admin()
async def end(ctx, member: discord.Member):
    """Force end all active games for a user"""
    user_id = member.id
    games_ended = []
    total_refunded = 0
    
    # Check and end Mines game
    if user_id in active_mines_games:
        game = active_mines_games[user_id]
        bet_amount = int(game['bet'])
        await db.update_balance(user_id, bet_amount, f"Mines game force-ended by admin")
        del active_mines_games[user_id]
        games_ended.append("Mines")
        total_refunded += bet_amount
    
    # Check and end Tower game
    if user_id in active_tower_games:
        game = active_tower_games[user_id]
        bet_amount = int(game['bet'])
        await db.update_balance(user_id, bet_amount, f"Tower game force-ended by admin")
        del active_tower_games[user_id]
        games_ended.append("Tower")
        total_refunded += bet_amount
    
    # Check and end Blackjack game
    if user_id in active_blackjack_games:
        game = active_blackjack_games[user_id]
        bet_amount = int(game['bet'])
        await db.update_balance(user_id, bet_amount, f"Blackjack game force-ended by admin")
        del active_blackjack_games[user_id]
        games_ended.append("Blackjack")
        total_refunded += bet_amount
    
    # Check and end multiplayer games - collect all sessions first to avoid mutation during iteration
    sessions_to_end = []
    if user_id in game_session_manager.user_games:
        session_key = game_session_manager.user_games[user_id]
        if session_key in game_session_manager.active_sessions:
            sessions_to_end.append(session_key)
    
    # End all multiplayer sessions
    for session_key in sessions_to_end:
        session = game_session_manager.active_sessions[session_key]
        bet_amount = int(session.bet_amount)
        
        # Refund player1
        if session.player1_id:
            await db.update_balance(session.player1_id, bet_amount, f"{session.game_type} game force-ended by admin")
            if session.player1_id == user_id:
                total_refunded += bet_amount
        
        # Refund player2 if exists (PvP only)
        if session.is_pvp and session.player2_id:
            await db.update_balance(session.player2_id, bet_amount, f"{session.game_type} game force-ended by admin")
            if session.player2_id == user_id:
                total_refunded += bet_amount
        
        games_ended.append(f"{session.game_type} (Multiplayer)")
        
        # End session with correct parameters
        channel_id, game_type, _ = session_key
        game_session_manager.end_session(channel_id, game_type, session.player1_id)
    
    # Remove from pending challenges - build list first to avoid mutation during iteration
    challenges_to_remove = [key for key in pending_challenges.keys() if user_id in key[:2]]
    challenges_removed = len(challenges_to_remove)
    
    for key in challenges_to_remove:
        del pending_challenges[key]
    
    # Build response
    embed = discord.Embed(title="🛑 Games Force-Ended", color=0xff6600, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="User", value=member.mention, inline=True)
    embed.add_field(name="Admin", value=ctx.author.mention, inline=True)
    
    if games_ended:
        embed.add_field(name="Games Ended", value="\n".join([f"• {game}" for game in games_ended]), inline=False)
        if total_refunded > 0:
            embed.add_field(name="💰 Refunded", value=f"**{total_refunded:,}** points", inline=False)
    else:
        embed.add_field(name="Status", value="No active games found", inline=False)
    
    if challenges_removed > 0:
        embed.add_field(name="Challenges Cancelled", value=f"{challenges_removed} pending challenge(s)", inline=False)
    
    if games_ended or challenges_removed > 0:
        embed.description = "✅ All active games and challenges have been terminated"
    else:
        embed.description = "ℹ️ User has no active games or pending challenges"
    
    await ctx.send(embed=embed)
    
    # Log admin command
    details = f"Ended {len(games_ended)} game(s), refunded {total_refunded} points, cancelled {challenges_removed} challenge(s)"
    await ModLogger.log_command(ctx.author, "end", member, action_details=details)

@require_guild()
@bot.command()
@is_bot_admin()
async def serverid(ctx):
    """Get the current server ID for whitelist configuration"""
    embed = discord.Embed(title="🔧 Server Information", color=0x00aaff)
    embed.add_field(name="Server Name", value=ctx.guild.name, inline=False)
    embed.add_field(name="Server ID", value=f"`{ctx.guild.id}`", inline=False)
    embed.add_field(name="💡 How to Use", value=f"Add this ID to `ALLOWED_GUILD_IDS` in bot.py:\n```python\nALLOWED_GUILD_IDS = [{ctx.guild.id}]\n```", inline=False)
    embed.set_footer(text="Bot will only stay in servers with IDs in this list")
    await ctx.send(embed=embed)

@require_guild()
@bot.command()
@is_bot_admin()
async def botstats(ctx):
    total_users = len([m for m in bot.get_all_members()])
    total_guilds = len(bot.guilds)
    
    embed = discord.Embed(title="🤖 Bot Statistics", color=0x00aaff, timestamp=datetime.datetime.utcnow())
    embed.add_field(name="👥 Total Users", value=f"**{total_users:,}**", inline=True)
    embed.add_field(name="🏠 Total Guilds", value=f"**{total_guilds:,}**", inline=True)
    embed.add_field(name="📊 Database", value="**SQLite**", inline=True)
    embed.add_field(name="🔧 Bot Name", value=bot.user.name, inline=True)
    embed.add_field(name="💰 Point Value", value=f"1 point = €{POINT_TO_EUR:.2f}", inline=True)
    embed.add_field(name="⏰ Cooldown", value=f"{COMMAND_COOLDOWN}s", inline=True)
    
    if ALLOWED_GUILD_IDS:
        embed.add_field(name="🔒 Whitelist Active", value=f"{len(ALLOWED_GUILD_IDS)} server(s)", inline=True)
    
    await ctx.send(embed=embed)

@require_guild()
@bot.command()
@is_bot_admin()
async def backup(ctx):
    try:
        backup_file = await db.create_backup()
        await ctx.send(f"✅ Backup created successfully: `{backup_file}`")
        
        # Log admin command
        await ModLogger.log_command(ctx.author, "backup",
                                    action_details="Created database backup",
                                    result=f"File: {backup_file}")
    except Exception as e:
        await ctx.send(f"❌ Backup failed: {str(e)}")

@require_guild()
@bot.command()
@is_bot_admin()
async def recover(ctx, backup_file: str = None):
    try:
        await db.recover_from_backup(backup_file)
        await ctx.send(f"✅ Database recovered successfully from backup!")
        
        # Log admin command
        await ModLogger.log_command(ctx.author, "recover",
                                    action_details=f"Recovered database from backup",
                                    result=f"File: {backup_file or 'latest'}")
    except Exception as e:
        await ctx.send(f"❌ Recovery failed: {str(e)}")

@require_guild()
@bot.command()
@is_bot_admin()
async def forcelottery(ctx):
    try:
        winner_id, prize = await db.draw_lottery()
        
        if winner_id is None:
            await ctx.send("❌ No tickets were sold today!")
            return
        
        winner = await bot.fetch_user(winner_id)
        
        embed = discord.Embed(title="🎫 Lottery Draw (FORCED)", color=0xFFD700, timestamp=datetime.datetime.utcnow())
        embed.add_field(name="🏆 Winner", value=winner.mention, inline=True)
        embed.add_field(name="💰 Prize", value=f"**{prize:,}** points", inline=True)
        embed.add_field(name="👑 Forced By", value=ctx.author.mention, inline=True)
        
        lottery_channel = bot.get_channel(LOTTERY_CHANNEL_ID)
        if lottery_channel:
            await lottery_channel.send(embed=embed)
        
        await ctx.send(embed=embed)
        
        try:
            await winner.send(f"🎉 **CONGRATULATIONS!** You won the lottery and received **{prize:,}** points!")
        except:
            pass
    except Exception as e:
        await ctx.send(f"❌ Lottery draw failed: {str(e)}")

# ========== UTILITY COMMANDS ==========
from dataclasses import dataclass

@dataclass
class GameHelpEntry:
    name: str
    emoji: str
    command: str
    description: str
    payout: str
    limits: str
    notes: str = ""

GAMES_HELP_DATA = [
    GameHelpEntry("Mines", "💣", ".mines [amount] [mines]", 
                  "Click tiles to reveal safe spots without hitting mines! The more tiles you reveal, the higher your multiplier. Cash out anytime or risk it all. Choose 3-24 mines for varying difficulty levels.",
                  "Rewards climb with every safe tile revealed—cash out anytime to secure your gains!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Tower", "🏰", ".tower [amount] [difficulty]", 
                  "Climb the tower by choosing the correct tile on each floor! Each successful climb increases your multiplier. Choose difficulty 1-4 to control risk vs reward. Cash out anytime before you fall!",
                  "Rewards escalate as you climb higher—higher difficulty means bigger prizes!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Blackjack", "🃏", ".blackjack [amount]", 
                  "Classic card game! Get closer to 21 than the dealer without going over. Hit to draw cards, stand to keep your hand. Dealer stands on 17. Blackjack (21 with 2 cards) pays extra!",
                  "Beat the dealer to win! Natural blackjack pays premium. Ties refund your wager.",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Roulette", "🎡", ".roulette [amount]", 
                  "Spin the wheel of fortune! Bet on red/black, odd/even, high/low, dozens, or specific numbers (0-36). Interactive betting interface guides you through all options.",
                  "Payouts vary by bet type—single numbers offer the highest rewards!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Coinflip", "🪙", ".coinflip [amount]", 
                  "Simple and classic! Choose heads or tails, flip the coin, and win double your bet. Pure 50/50 chance with fair odds.",
                  "Winning flips pay back more than you wagered!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Slots", "🎰", ".slots [amount]", 
                  "Spin the classic 3-reel slot machine! Match symbols across the payline to win. Get 3 sevens for the jackpot! Features cherries, lemons, bells, bars, and lucky sevens.",
                  "Premium symbol lines deliver the best prizes—sevens unlock the jackpot tier!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Dice", "🎲", ".dice [amount] [number]", 
                  "Guess the dice roll! Pick a number from 1 to 6, roll the dice, and win big if you guess correctly. Number is optional (defaults to 6). Usage: .dice 10 4 (bet 10, guess 4)",
                  "Correct predictions earn generous returns!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Plinko", "🎯", ".plinko [amount] [drops]", 
                  "Drop balls and watch them bounce through pegs! Specify how many balls to drop (1-10). Each ball lands in a multiplier slot. More drops = more chances to win! Usage: .plinko 10 5 (bet 10 pts per drop, drop 5 balls)",
                  "More drops give you more chances! Each ball can multiply your bet.",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Keno", "🎰", ".keno [amount] [numbers]", 
                  "Pick 1-10 numbers from 1-40, then 20 random numbers are drawn. More matches = bigger payout! Use space-separated numbers like: .keno 10 5 12 23 35 (NOT commas!)",
                  "More matches unlock richer reward tiers—full matches earn the most!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Horse Racing", "🐴", ".horseracing [amount] [horse]", 
                  "Bet on horses 1-6 to win the race! Each horse has equal odds. Watch the race unfold and cheer for your horse to cross the finish line first!",
                  "Winning horse selections earn solid returns!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("HiLo", "📈", ".hilo [amount]", 
                  "Interactive card game! A card is revealed. Guess if the next card will be higher or lower. Chain correct guesses for progressive multipliers. Cash out anytime or push your luck!",
                  "Consecutive correct guesses multiply your winnings—cash out or risk it all!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Crash", "🎈", ".crash [amount] [target]", 
                  "Watch the multiplier rise! Set your target multiplier (1.05x-5.5x) and hope the crash doesn't happen before it reaches your target. Higher targets = higher risk!",
                  "Reaching your target before the crash pays you that multiplier!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Rock-Paper-Scissors", "✂️", ".rps [amount] [choice]", 
                  "Classic game against the bot! Choose rock, paper, or scissors. Rock beats scissors, scissors beats paper, paper beats rock. Ties return your bet.",
                  "Victories pay back more than you bet. Ties refund your wager.",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Guess The Number", "🔢", ".gtn [amount] [guess]", 
                  "Guess a number between 1-100! Exact match wins big! Close guess (within 5) wins medium. Near guess (within 10) wins small. Test your intuition!",
                  "Closer guesses unlock richer tiers of rewards—exact matches pay the most!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Case Opening", "📦", ".case [amount]", 
                  "Unbox mystery cases for random rewards! Each case contains items with different rarity levels. Higher rarity = bigger multipliers. Will you get legendary?",
                  "Rarer items deliver better rewards—legendary drops unlock premium prizes!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Baccarat", "🎴", ".baccarat [amount] [bet]", 
                  "Elegant card game! Bet on Player, Banker, or Tie. Two hands are dealt. Closest to 9 wins. Banker bet has slight edge but pays 1.9x. Player and Tie pay 2x. Usage: .baccarat 10 player",
                  "Winning bets earn returns. Banker has slight edge with modest payout.",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Wheel", "🎡", ".wheel [amount]", 
                  "Spin the fortune wheel! Land on multiplier segments ranging from 0x to 10x. Pure luck-based game with various prize tiers distributed around the wheel.",
                  "Landing on higher segments unlocks better prizes—pure luck gameplay!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Blackjack Dice", "🎲", ".blackjackdice [amount]", 
                  "Blackjack meets dice! Roll dice to get close to 21 without going over. Each die shows 1-6. Decide to roll more dice or stand. Dealer plays automatically.",
                  "Beat the dealer to earn back more than you wager. Ties refund.",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Cards", "🃏", ".cards [amount]", 
                  "High-low card game with multiplier tiers! Draw cards and build your score. Higher card values = better multipliers. Strategic game with luck elements.",
                  "Better card combinations unlock stronger reward tiers!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Classic Dice", "🎲", ".classicdice [amount]", 
                  "Traditional dice betting! Roll 2 dice and bet on the outcome. Choose your prediction: sum, doubles, specific numbers. Multiple betting options available!",
                  "Payouts vary by prediction type—rarer outcomes earn more!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Poker", "🃏", ".poker [amount]", 
                  "Video poker style! Get dealt 5 cards, choose which to keep, and redraw the rest. Form poker hands to win. Royal Flush pays the jackpot!",
                  "Premium hands deliver the best prizes—Royal Flush unlocks jackpot tier!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Chicken Road", "🐔", ".chickenroad [amount]", 
                  "Help the chicken cross the road! Each step has a chance of danger. The further you go, the higher your multiplier. Cash out before disaster strikes!",
                  "Rewards grow with each safe step—cash out before disaster!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Progressive Coinflip", "🪙", ".progressivecoinflip [amount]", 
                  "Chain coinflips for exponential growth! Each win doubles your multiplier. Keep flipping or cash out. One wrong flip loses everything. How far can you go?",
                  "Consecutive wins multiply rewards exponentially—cash out or lose it all!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Balloon", "🎈", ".balloon [amount]", 
                  "Pop balloons to reveal prizes! Each balloon contains a random multiplier. Choose which balloon to pop. Some balloons pop your winnings!",
                  "Random prizes inside each balloon—some pop your winnings!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Tic-Tac-Toe", "⭕", ".ttt [amount] or .ttt @user [amount]", 
                  "Classic Tic-Tac-Toe! Play against bot for fixed payout or challenge another player for PvP betting. First to get 3 in a row wins!",
                  "Beat the bot to win returns! PvP: victor claims nearly the entire stake.",
                  "NO DAILY LIMIT - Multiplayer PvP game"),
    
    GameHelpEntry("Naval War", "🚢", ".navalwar [amount] or .navalwar @user [amount]", 
                  "Battleship-style game! Place your ships and try to sink your opponent's fleet. Strategic gameplay with hidden ship positions. Sink all ships to win!",
                  "Sink all ships to win! PvP: victor claims nearly the entire stake.",
                  "NO DAILY LIMIT - Multiplayer PvP game"),
    
    GameHelpEntry("Connect 4", "🔴", ".connect [amount]", 
                  "Drop checkers and connect four in a row! Play against the bot in this strategic game. Vertical, horizontal, or diagonal - get 4 connected to win!",
                  "Connect 4 to win returns against the bot!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Chess", "♟️", ".chess [amount]", 
                  "Classic chess game! Play against the bot or challenge other players. Full chess rules apply. Checkmate your opponent to claim victory!",
                  "Checkmate to win! Draws refund your wager.",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Classic Slots", "🎰", ".classicslots [amount]", 
                  "Traditional 3-disk slot machine! Old-school fruit machine with classic symbols. Line up three matching symbols to win. Nostalgic gameplay!",
                  "Premium symbol lines deliver the best prizes—sevens unlock top tier!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Darts", "🎯", ".darts [amount]", 
                  "Throw darts at the dartboard! Hit different zones for different multipliers. Bullseye wins big! Outer ring pays small. Test your aim!",
                  "Precision hits deliver better rewards—bullseye unlocks maximum prize!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Diamonds", "💎", ".diamonds [amount]", 
                  "5-reel diamond slots! Match sparkling diamonds across multiple paylines. More diamonds = bigger payouts. Cascading reels for extra chances!",
                  "More diamond matches unlock richer prizes—full lines pay the most!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Dice War", "🎲", ".dicewar [amount]", 
                  "Roll dice against the bot! Highest total wins. You roll multiple dice, bot rolls multiple dice. Simple but exciting dice battle!",
                  "Higher total wins! Ties refund your wager.",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Easter", "🐰", ".easter [amount]", 
                  "Easter egg hunt themed slots! Find matching Easter eggs and bunnies. Seasonal fun with spring-themed symbols and festive payouts!",
                  "Premium egg matches deliver the best prizes—golden eggs unlock top tier!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Evil Jokers", "🃏", ".eviljokers [amount]", 
                  "Avoid the evil jokers! Draw cards to build your score, but if you draw a joker, you lose everything! Strategic risk management game.",
                  "More cards drawn without jokers earn bigger rewards—but jokers end it all!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Fight", "⚔", ".fight [amount]", 
                  "PvP battle simulation! Your fighter battles the opponent in an automated combat sequence. Attack, defense, and critical hits determine the winner!",
                  "Defeat your opponent to win! Battle outcomes vary by combat performance.",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Ghosts", "👻", ".ghosts [amount]", 
                  "Halloween ghost hunting! Search rooms for friendly ghosts while avoiding scary ones. Each room reveals a ghost with a multiplier or a loss!",
                  "Friendly ghosts deliver rewards—scary ghosts take it all!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Guess Number PvP", "🔢", ".gn [amount]", 
                  "Compete with other players to guess the secret number (1-100)! First correct guess or closest after time limit wins the pot!",
                  "Winner takes the pot! Multiple players compete for the prize.",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Treasure Hunt", "🗺️", ".treasurehunt [amount]", 
                  "Pick treasure chests to find hidden riches! 5 chests contain different multipliers. Choose wisely - one chest might be empty, but others hold great treasures!",
                  "Choose wisely—some chests hide great treasures, others are empty!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Valentines", "💘", ".valentines [amount]", 
                  "Valentine's Day themed 3-reel slots! Spin hearts, roses, and cupids for romantic wins. Spread the love and win big with matching symbols!",
                  "Premium symbol matches deliver the best prizes—hearts unlock top tier!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("War", "🃏", ".war [amount]", 
                  "Classic card war vs dealer! Both draw one card. Highest card wins. Ties return your bet. Simple, fast, and fair!",
                  "Higher card wins! Ties refund your wager.",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Wheelcolor", "🎡", ".wheelcolor [amount] [color]", 
                  "Bet on colors in a 48-slot wheel! Blue (24 slots) = 2x, Red (20 slots) = 2.5x, Green (4 slots) = 6x. Choose your color and spin!",
                  "Different colors offer different rewards—rarer colors pay more!",
                  "5 plays/day (regular) • 10 plays/day (VIP)"),
    
    GameHelpEntry("Wordly", "🔤", ".wordly", 
                  "Skill-based word guessing game! No wager required. Guess the 5-letter word in 6 tries. Green = correct, Yellow = wrong position, Gray = not in word. Sharpen your vocabulary!",
                  "No monetary payout - Play for fun and bragging rights! Rewards XP and achievements.",
                  "60-second cooldown between plays • NO WAGER REQUIRED",
                  "Free-to-play skill game!")
]

class GamesHelpView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, parent_view):
        super().__init__(timeout=180)
        self.interaction = interaction
        self.parent_view = parent_view
        self.current_index = 0
        self.update_buttons()
    
    def update_buttons(self):
        self.first_btn.disabled = self.current_index == 0
        self.prev_btn.disabled = self.current_index == 0
        self.next_btn.disabled = self.current_index == len(GAMES_HELP_DATA) - 1
        self.last_btn.disabled = self.current_index == len(GAMES_HELP_DATA) - 1
    
    def build_embed(self):
        game = GAMES_HELP_DATA[self.current_index]
        embed = discord.Embed(
            title=f"{game.emoji} {game.name}",
            description=f"**Command:** `{game.command}`\n\n{game.description}",
            color=0x3498db
        )
        embed.add_field(name="💰 Payouts", value=game.payout, inline=False)
        embed.add_field(name="📅 Daily Limits", value=game.limits, inline=False)
        if game.notes:
            embed.add_field(name="ℹ️ Special Notes", value=game.notes, inline=False)
        embed.set_footer(text=f"Page {self.current_index + 1}/{len(GAMES_HELP_DATA)} • Use ⬅️➡️ to navigate • 🔙 Back to menu")
        return embed
    
    @discord.ui.button(label="⏮️", style=discord.ButtonStyle.secondary, row=0)
    async def first_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_index = 0
        self.update_buttons()
        await interaction.response.edit_message( embed=self.build_embed(), view=self)
    
    @discord.ui.button(label="◀️", style=discord.ButtonStyle.primary, row=0)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_index = max(0, self.current_index - 1)
        self.update_buttons()
        await interaction.response.edit_message( embed=self.build_embed(), view=self)
    
    @discord.ui.button(label="▶️", style=discord.ButtonStyle.primary, row=0)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_index = min(len(GAMES_HELP_DATA) - 1, self.current_index + 1)
        self.update_buttons()
        await interaction.response.edit_message( embed=self.build_embed(), view=self)
    
    @discord.ui.button(label="⏭", style=discord.ButtonStyle.secondary, row=0)
    async def last_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_index = len(GAMES_HELP_DATA) - 1
        self.update_buttons()
        await interaction.response.edit_message( embed=self.build_embed(), view=self)
    
    @discord.ui.button(label="🔙 Back to Menu", style=discord.ButtonStyle.danger, row=1)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        main_embed = discord.Embed(
            title="🎰 Casino Bot Help Center",
            description="Welcome to the complete casino bot guide! Select a category below to learn more.",
            color=0x00ff00
        )
        main_embed.add_field(name="💰 Economy", value="Balance, rewards, tips, and conversions", inline=False)
        main_embed.add_field(name="🎮 Games", value="All 46 casino games with detailed guides", inline=False)
        main_embed.add_field(name="🏆 Stats & Ranks", value="Rankings, leaderboards, and achievements", inline=False)
        main_embed.add_field(name="🎫 Lottery", value="Daily lottery system and tickets", inline=False)
        main_embed.add_field(name="⭐ VIP & Settings", value="VIP benefits, language, and privacy", inline=False)
        main_embed.set_footer(text="🎲 46 Total Games • 5/10 Daily Plays System • VIP 1.15x Multiplier")
        await interaction.response.edit_message( embed=main_embed, view=self.parent_view)
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.interaction.edit_original_response(view=self)
        except:
            pass

class HelpView(discord.ui.View):
    def __init__(self, is_admin=False):
        super().__init__(timeout=180)
        self.is_admin = is_admin
        
        # Add admin button only if user is admin
        if is_admin:
            admin_btn = discord.ui.Button(label="🛡 Admin", style=discord.ButtonStyle.danger, row=2, emoji="👑")
            admin_btn.callback = self.admin_button
            self.add_item(admin_btn)
    
    @discord.ui.button(label="💰 Economy", style=discord.ButtonStyle.success, row=0)
    async def economy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="💰 Economy Commands", color=0x00ff00)
        embed.add_field(name=".balance", value="Check your point balance", inline=False)
        embed.add_field(name=".balhistory", value="View your last 10 balance changes with reasons and timestamps", inline=False)
        embed.add_field(name=".convert [amount]", value="Convert EUR to points (shows conversion only, doesn't add points)", inline=False)
        embed.add_field(name=".daily", value="Claim daily reward (1 point, requires 10+ points balance)", inline=False)
        embed.add_field(name=".monthly", value="Claim monthly reward (0.01% of points wagered, requires 30 days since first points)", inline=False)
        embed.add_field(name=".rakeback", value="Check your rakeback percentage and available amount", inline=False)
        embed.add_field(name=".claimrakeback", value="Claim your accumulated rakeback", inline=False)
        embed.add_field(name=".tip [@user] [amount]", value="Tip points to another user", inline=False)
        embed.add_field(name=".rain [amount]", value="Make it rain! Share points with everyone (60s)", inline=False)
        embed.add_field(name=".price", value="View point pricing (1 point = €0.01)", inline=False)
        embed.set_footer(text="💡 Use 'half' or 'all' for amounts in games!")
        await interaction.response.edit_message( embed=embed, view=self)
    
    @discord.ui.button(label="🎮 Games", style=discord.ButtonStyle.primary, row=0)
    async def games_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        games_view = GamesHelpView(interaction, self)
        embed = games_view.build_embed()
        await interaction.response.edit_message( embed=embed, view=games_view)
    
    @discord.ui.button(label="🏆 Stats & Ranks", style=discord.ButtonStyle.secondary, row=0)
    async def stats_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🏆 Stats & Ranking System", color=0x9b59b6)
        embed.add_field(name=".rank", value="View your current rank and progress", inline=False)
        embed.add_field(name=".ranks", value="List all available ranks and requirements", inline=False)
        embed.add_field(name=".leaderboard", value="View top players by total wagered", inline=False)
        embed.add_field(name=".stats [@user]", value="View detailed statistics for yourself or another user", inline=False)
        embed.add_field(name=".achievements", value="View all achievements and your progress", inline=False)
        embed.add_field(name="📊 Rank Tiers", value="🎯 Beginner → 🥉 Bronze → 🥈 Silver → 🥇 Gold → 💎 Platinum → 🔮 Diamond → 💍 Ruby → 🔵 Sapphire → 💚 Emerald → 👑 Legendary → 🌟 God → ⚡ Ultimate", inline=False)
        await interaction.response.edit_message( embed=embed, view=self)
    
    @discord.ui.button(label="🎫 Lottery", style=discord.ButtonStyle.danger, row=1)
    async def lottery_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🎫 Interactive Lottery System", color=0xFFD700)
        embed.add_field(name=".lottery", value="🎟 **Buy tickets with interactive buttons!**\nChoose: 1, 10, 100, or 1000 tickets", inline=False)
        embed.add_field(name=".lotteryinfo", value="View lottery pool, your tickets, and next draw time", inline=False)
        embed.add_field(name=".lottery opening", value="👑 **Admin only** - Opens lottery with announcement in lottery channel", inline=False)
        embed.add_field(name="💰 Ticket Pricing", value="• 1 ticket = 1 point (€0.01)\n• 10 tickets = 10 points (€0.10)\n• 100 tickets = 100 points (€1.00)\n• 1000 tickets = 1,000 points (€10.00)", inline=True)
        embed.add_field(name="ℹ️ How It Works", value="• Draw at **7 PM HKT** (11:00 UTC) daily\n• Winner gets **100% of prize pool**\n• More tickets = Better chance\n• Prize funded by players (Casino takes 0%)", inline=True)
        embed.add_field(name="🏆 Prize Pool", value="All ticket purchases go into the prize pool. One random winner takes everything!", inline=False)
        embed.set_footer(text="🎊 Use .lottery to see interactive buttons! Good luck!")
        await interaction.response.edit_message( embed=embed, view=self)
    
    @discord.ui.button(label="⭐ VIP & Settings", style=discord.ButtonStyle.success, row=1)
    async def vip_settings_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="⭐ VIP & Settings", color=0xFFD700)
        embed.add_field(name=".vipinfo", value="View VIP benefits and check your VIP status", inline=False)
        embed.add_field(name=".language", value="Change bot language (12 languages available)", inline=False)
        embed.add_field(name=".privacy on/off", value="Toggle privacy mode (hide/show your stats from others)", inline=False)
        embed.add_field(name="💎 VIP Benefits", value="• **1.15x multiplier** on all games\n• **10 daily plays per game** (vs 5 for regular users)\n• Double daily rewards (2 points base)\n• Exclusive VIP badge\n• Priority support\n• 2x more gameplay every day!", inline=False)
        embed.add_field(name="🚀 Boost System", value="• Boost 1: +1.10x multiplier\n• Boost 2: +1.15x multiplier\n• Boost 3: +1.20x multiplier\n• Stack with VIP for max wins!", inline=False)
        embed.set_footer(text="🌍 Languages: EN, IT, ES, FR, DE, PT, RU, TR, PL, NL, AR, ZH")
        await interaction.response.edit_message( embed=embed, view=self)
    
    @discord.ui.button(label="🧵 Threads", style=discord.ButtonStyle.primary, row=1)
    async def threads_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🧵 Thread Management - Private Gambling Spaces", color=0x5865F2)
        embed.description = "Create your own private casino threads for exclusive gambling sessions!"
        embed.add_field(name=".thread create", value="🎰 Create a new private thread for gambling\n• Your own private casino space\n• All casino games work inside threads\n• Invite-only (private threads)", inline=False)
        embed.add_field(name=".thread add @user", value="➕ Add someone to your current thread\n• Invite friends to your private casino\n• Only works inside threads", inline=False)
        embed.add_field(name=".thread remove @user", value="➖ Remove someone from your current thread\n• Kick users from your thread\n• Can't remove the thread owner", inline=False)
        embed.add_field(name=".thread close", value="🔒 Close and archive the current thread\n• Locks the thread permanently\n• 5 second countdown before closing", inline=False)
        embed.add_field(name="✨ Features", value="• All casino commands work in threads!\n• Private space for you and invited users\n• Auto-archives after 60 minutes of inactivity\n• Perfect for private gambling sessions", inline=False)
        embed.set_footer(text="💡 Create your own exclusive casino space with .thread create!")
        await interaction.response.edit_message( embed=embed, view=self)
    
    @discord.ui.button(label="📖 How to Use", style=discord.ButtonStyle.secondary, row=2)
    async def usage_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="📖 Command Usage Guide", color=0x3498db, description="Learn how to use commands with examples!")
        
        embed.add_field(name="💰 BETTING AMOUNTS", value="All games support flexible betting:\n"
                        "• **Numbers**: `.coinflip 100` (bet 100 points)\n"
                        "• **Half**: `.slots half` (bet half your balance)\n"
                        "• **All**: `.mines all` (bet everything)\n"
                        "• **Decimals**: `.roulette 0.5` (bet 0.5 points)", inline=False)
        
        embed.add_field(name="🎯 MULTIPLAYER GAMES", value="Two ways to play:\n"
                        "• **vs Bot**: `.ttt 10` or `.navalwar 5`\n"
                        "• **vs Player**: `.ttt @friend 25` or `.navalwar @enemy 50`\n"
                        "• **PvP**: 1% house edge, winner gets 99% of pot\n"
                        "• **PvE**: Fixed payouts (TicTacToe 2x, NavalWar 1.2x)", inline=False)
        
        embed.add_field(name="🎮 INTERACTIVE GAMES", value="Click buttons to play:\n"
                        "• `.mines 10 5` → 10 points bet, 5 mines\n"
                        "• `.tower 20 3` → 20 points, difficulty 3\n"
                        "• `.blackjack 15` → Start with 15 points\n"
                        "• `.hilo 50` → Interactive card game, cash out anytime\n"
                        "• `.roulette 10` → Step-by-step betting on red/black, etc", inline=False)
        
        embed.add_field(name="🎰 INSTANT GAMES", value="Quick games with instant results:\n"
                        "• `.plinko 10 5` → Drop 5 balls, 10 pts each (interactive!)\n"
                        "• `.keno 10 5 12 23 35` → Pick 1-10 numbers (space-separated!)\n"
                        "• `.horseracing 20 3` → Bet on horse 1-6\n"
                        "• `.crash 15 2.5` → Target multiplier 1.05x-5.5x\n"
                        "• `.rps 30 rock` → Choice: rock/paper/scissors\n"
                        "• `.gtn 40 75` → Guess number 1-100\n"
                        "• `.case 50` → Open random case\n"
                        "• `.baccarat 20 player` → Bet: player/banker/tie\n"
                        "• `.wheel 100` → Spin for random multiplier", inline=False)
        
        embed.add_field(name="🎮 DAILY LIMITS", value="**All games limited:**\n"
                        "• Regular users: **5 plays/day per game**\n"
                        "• VIP users: **10 plays/day per game**\n"
                        "• Limits reset at midnight UTC\n"
                        "• Applies to ALL 30+ casino games!", inline=False)
        
        embed.add_field(name="💸 ECONOMY", value="Managing your points:\n"
                        "• `.balance` → Check your points\n"
                        "• `.daily` → Claim 1 point (requires 10+ balance)\n"
                        "• `.monthly` → 0.01% of wagered (after 30 days)\n"
                        "• `.tip @user 50` → Send 50 points to someone\n"
                        "• `.rain 100` → Share 100 points with everyone!", inline=False)
        
        embed.add_field(name="🎫 LOTTERY", value="Buy tickets and win big:\n"
                        "• `.lottery 10` → Buy 10 tickets (10 points)\n"
                        "• `.lotteryinfo` → Check pool and your tickets\n"
                        "• Daily draw at **18:00 UTC**\n"
                        "• Winner takes entire prize pool!", inline=False)
        
        embed.set_footer(text="💡 Prefix: '.' | ⏰ Cooldown: 10s | 🎮 Daily limits: 5 (regular) / 10 (VIP)")
        await interaction.response.edit_message( embed=embed, view=self)
    
    async def admin_button(self, interaction: discord.Interaction):
        """Admin button callback (added dynamically in __init__)"""
        embed = discord.Embed(title="🛡 Admin Commands", color=0xe74c3c)
        embed.add_field(name="💰 ECONOMY ADMIN", value="Manage user balances and points", inline=False)
        embed.add_field(name=".addpoints [@user] [amount]", value="Add points to a user's balance", inline=False)
        embed.add_field(name=".setbalance [@user] [amount]", value="Set a user's balance to specific amount", inline=False)
        embed.add_field(name=".setwager [@user] [amount]", value="Set a user's total wager amount", inline=False)
        embed.add_field(name="⭐ VIP & BOOST ADMIN", value="Manage VIP and boost status", inline=False)
        embed.add_field(name=".addvip [@user] [days]", value="Grant VIP status (1.15x multiplier)", inline=False)
        embed.add_field(name=".removevip [@user]", value="Remove VIP status from user", inline=False)
        embed.add_field(name=".addboost [@user] [days] [1/2/3]", value="Grant boost (1.10x/1.15x/1.20x)", inline=False)
        embed.add_field(name=".removeboost [@user] [1/2/3]", value="Remove specific boost from user", inline=False)
        embed.add_field(name="🎮 GAME LIMITS", value="Manage daily play limits", inline=False)
        embed.add_field(name=".addgameunlimit [@user] [days]", value="Grant unlimited daily plays for X days", inline=False)
        embed.add_field(name=".removegameunlimit [@user]", value="Remove unlimited plays (back to 5/10 limit)", inline=False)
        embed.add_field(name="🚫 MODERATION", value="Ban and manage users", inline=False)
        embed.add_field(name=".ban [@user] [reason]", value="Ban user from bot (reason optional)", inline=False)
        embed.add_field(name=".unban [@user]", value="Unban user from bot", inline=False)
        embed.add_field(name=".checkban [@user]", value="Check if user is banned", inline=False)
        embed.add_field(name="📢 ANNOUNCEMENTS", value="Send messages to channels", inline=False)
        embed.add_field(name=".announcement [opening/custom] [text]", value="Send announcement (templates or custom)", inline=False)
        embed.add_field(name=".update [text]", value="Send update with auto-date insertion", inline=False)
        embed.add_field(name=".ad [description]", value="Send server advertisement with description", inline=False)
        embed.add_field(name="⚙️ BOT MANAGEMENT", value="Bot statistics and backups", inline=False)
        embed.add_field(name=".botstats", value="View comprehensive bot statistics", inline=False)
        embed.add_field(name=".backup", value="Create database backup manually", inline=False)
        embed.add_field(name=".recover", value="Restore from latest backup file", inline=False)
        embed.add_field(name=".forcelottery", value="Force immediate lottery draw", inline=False)
        embed.set_footer(text="🛡 Admin commands require administrator role")
        await interaction.response.edit_message( embed=embed, view=self)

# ========== LANGUAGE SELECTION ==========
@require_guild()
@bot.command(aliases=['lang'])
async def language(ctx, lang_code: str = None):
    """Change your language preference. Usage: .language <code> or .lang <code>"""
    user_id = ctx.author.id
    
    if lang_code is None:
        # Show current language and available options
        current_lang = await localization.get_user_language(user_id, db)
        lang_name = localization.supported_languages.get(current_lang, 'English')
        
        embed = discord.Embed(
            title="🌍 Language Selection",
            description=f"Your current language: **{lang_name}** ({current_lang})",
            color=0x00AAFF
        )
        
        # Add available languages
        langs_list = "\n".join([f"`{code}` - {name}" for code, name in localization.supported_languages.items()])
        embed.add_field(name="Available Languages", value=langs_list, inline=False)
        embed.add_field(name="How to Change", value="Use `.language <code>` or `.lang <code>`\nExample: `.lang es` for Spanish", inline=False)
        embed.set_footer(text="Translations are loaded from locales/ directory")
        
        await ctx.send(embed=embed)
        return
    
    # Validate and set language
    lang_code = lang_code.lower()
    if lang_code not in localization.supported_languages:
        valid_codes = ", ".join(localization.supported_languages.keys())
        await ctx.send(f"❌ Invalid language code! Valid codes: {valid_codes}")
        return
    
    # Set user's language
    success = await localization.set_user_language(user_id, lang_code, db)
    if success:
        lang_name = localization.supported_languages[lang_code]
        await ctx.send(f"✅ Language changed to **{lang_name}**!")
    else:
        await ctx.send("❌ Failed to update language. Please try again.")

@require_guild()
@bot.command()
@cooldown_check()
async def help(ctx):
    is_admin = await is_bot_admin().predicate(ctx)
    
    embed = discord.Embed(
        title="🎰 AfterBet Casino Bot",
        description="Welcome to **AfterBet**! The ultimate Discord casino experience.\n\n"
                    "💰 **1 point = €0.01**\n"
                    "🎮 Play interactive games with buttons\n"
                    "🏆 Climb ranks and unlock achievements\n"
                    "⭐ VIP & Boost systems for extra rewards\n"
                    "🎫 Daily lottery draws at 18:00 UTC\n\n"
                    "**Click the buttons below to explore different commands!**",
        color=0xFFD700
    )
    embed.set_footer(text=f"⏰ Command cooldown: {COMMAND_COOLDOWN}s | 💡 Use 'half' or 'all' for bet amounts!")
    
    view = HelpView(is_admin=is_admin)
    await ctx.send(embed=embed, view=view)

# ========== ANNOUNCEMENT COMMANDS ==========
@require_guild()
@bot.command()
@is_bot_admin()
async def announcement(ctx, announcement_type: str = "opening", *, custom_text: str = None):
    """
    Send announcements to the announcement channel
    Usage: .announcement opening
           .announcement custom Your custom message here
    """
    announcement_channel_id = ANNOUNCEMENT_CHANNEL_ID
    announcement_channel = bot.get_channel(announcement_channel_id)
    
    if not announcement_channel:
        await ctx.send(f"❌ Announcement channel not found! (ID: {announcement_channel_id})")
        return
    
    if announcement_type.lower() == "opening":
        # Casino opening announcement
        embed = discord.Embed(
            title="🎰 AFTERBET CASINO IS NOW OPEN! 🎰",
            description="**Welcome to the most exciting Discord casino experience!**\n\n"
                        "The wait is over! AfterBet Casino is officially open for business. "
                        "Play interactive games, win big, and exchange your winnings for amazing rewards!",
            color=0xFFD700,
            timestamp=datetime.datetime.utcnow()
        )
        
        embed.add_field(
            name="🎮 Interactive Games",
            value="💣 **Mines** - Click tiles to find diamonds\n"
                  "🏰 **Tower** - Climb levels and cash out\n"
                  "🃏 **Blackjack** - Beat the dealer\n"
                  "🎡 **Roulette** - Step-by-step betting\n"
                  "🪙 **Coinflip** - Interactive heads or tails\n"
                  "🎰 **Slots** - Spin to win\n"
                  "🎲 **Dice** - Roll the dice",
            inline=False
        )
        
        embed.add_field(
            name="💰 Exchange Your Points For:",
            value="💵 **Real Money** - Cash out your winnings!\n"
                  "🎮 **Gaming Accounts** - Premium accounts\n"
                  "💎 **Discord Nitro** - Monthly or yearly\n"
                  "🟡 **Robux** - For Roblox enthusiasts\n"
                  "🎁 **Aftermath Loot** - Exclusive items\n"
                  "⭐ **Rare Collectibles** - Limited edition items",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Point Values",
            value="**4 points** = Small rewards\n"
                  "**10 points** = Medium rewards\n"
                  "**50+ points** = Premium rewards\n"
                  "**100+ points** = Exclusive items",
            inline=True
        )
        
        embed.add_field(
            name="⭐ Special Features",
            value="🎁 **Daily Rewards** - Free points every day\n"
                  "👑 **VIP System** - 1.15x multiplier\n"
                  "🚀 **Boost System** - Up to 1.20x extra\n"
                  "🎫 **Daily Lottery** - Win the jackpot\n"
                  "🏆 **Rank System** - 12 ranks to unlock\n"
                  "💸 **1% Rakeback** - Get cashback on bets",
            inline=True
        )
        
        embed.add_field(
            name="🚀 How to Start",
            value="Type `.help` to see all commands!\n"
                  "Type `.balance` to check your points\n"
                  "Type `.daily` to claim free points\n\n"
                  "**Use 'half' or 'all' to bet flexibly!**",
            inline=False
        )
        
        embed.set_footer(text="AfterBet Casino | Play responsibly!")
        embed.set_thumbnail(url="https://em-content.zobj.net/thumbs/160/apple/354/slot-machine_1f3b0.png")
        
        await announcement_channel.send("@everyone", embed=embed)
        await ctx.send(f"✅ Casino opening announcement sent to <#{announcement_channel_id}>!")
    
    elif announcement_type.lower() == "custom":
        if not custom_text:
            await ctx.send("❌ Please provide custom text! Usage: `.announcement custom Your message here`")
            return
        
        embed = discord.Embed(
            title="📢 AfterBet Announcement",
            description=custom_text,
            color=0x00ff00,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text="AfterBet Casino")
        
        await announcement_channel.send(embed=embed)
        await ctx.send(f"✅ Custom announcement sent to <#{announcement_channel_id}>!")
    
    else:
        await ctx.send("❌ Invalid announcement type! Use: `opening` or `custom`")

@require_guild()
@bot.command()
@is_bot_admin()
async def update(ctx, *, update_text: str):
    """
    Send update announcement with automatic date insertion
    Usage: .update Your update message here
    """
    announcement_channel_id = UPDATE_CHANNEL_ID
    announcement_channel = bot.get_channel(announcement_channel_id)
    
    if not announcement_channel:
        await ctx.send(f"❌ Announcement channel not found! (ID: {announcement_channel_id})")
        return
    
    if not update_text:
        await ctx.send("❌ Please provide update text! Usage: `.update Your message here`")
        return
    
    # Get current date in format: November 04, 2025
    current_date = datetime.datetime.utcnow().strftime("%B %d, %Y")
    
    embed = discord.Embed(
        title="🔔 AfterBet Update",
        description=f"**{current_date}**\n\n{update_text}",
        color=0x3498db,
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text="AfterBet Casino")
    
    await announcement_channel.send("@everyone", embed=embed)
    await ctx.send(f"✅ Update announcement sent to <#{announcement_channel_id}>!\n📅 Date: **{current_date}**")
    
    # Log admin command
    await ModLogger.log_command(ctx.author, "update",
                                action_details="Sent update announcement",
                                result=f"Message: {update_text[:100]}...")

@require_guild()
@bot.command()
@is_bot_admin()
async def ad(ctx, *, description: str = None):
    """
    Send a server advertisement with description
    Usage: .ad Your server description here
    """
    announcement_channel_id = AD_CHANNEL_ID
    announcement_channel = bot.get_channel(announcement_channel_id)
    
    if not announcement_channel:
        await ctx.send(f"❌ Announcement channel not found! (ID: {announcement_channel_id})")
        return
    
    if not description:
        description = "Join our casino server for the best gaming experience! Play interactive games, win points, and enjoy exclusive rewards!"
    
    # Get server information
    server = ctx.guild
    server_name = server.name if server else "AfterBet Casino"
    member_count = server.member_count if server else 0
    
    embed = discord.Embed(
        title=f"🎰 {server_name} - Casino Server",
        description=description,
        color=0xFFD700,
        timestamp=datetime.datetime.utcnow()
    )
    
    embed.add_field(
        name="🎮 What We Offer",
        value="🎲 **10+ Casino Games (PvP & PvE)**\n"
              "💰 **Point Economy System**\n"
              "⭐ **VIP & Boost Features**\n"
              "🎫 **Daily Lottery System**\n"
              "🏆 **Rank Progression**\n"
              "🎁 **Daily & Monthly Rewards**",
        inline=True
    )
    
    embed.add_field(
        name="💎 Games Available",
        value="⭕ Tic Tac Toe | 🚢 Naval War\n"
              "💣 Mines | 🏰 Tower\n"
              "🃏 Blackjack | 🎡 Roulette\n"
              "🪙 Coinflip | 🎰 Slots\n"
              "🎲 Dice",
        inline=True
    )
    
    embed.add_field(
        name="📊 Server Stats",
        value=f"👥 **Members:** {member_count:,}\n"
              f"🎰 **Games:** 10+\n"
              f"💰 **1 Point** = €0.01\n"
              f"🎮 **Type:** Casino Bot",
        inline=False
    )
    
    embed.add_field(
        name="🚀 Join Us!",
        value="Type `.help` to get started!\n"
              "Claim your free daily points with `.daily`\n"
              "Start playing and winning today!",
        inline=False
    )
    
    embed.set_footer(text=f"AfterBet Casino | {server_name}")
    
    if server and server.icon:
        embed.set_thumbnail(url=server.icon.url)
    else:
        embed.set_thumbnail(url="https://em-content.zobj.net/thumbs/160/apple/354/slot-machine_1f3b0.png")
    
    # Create copyable text version
    text_version = f"""╔═══════════════════════════════════════╗
║  🎰 **{server_name} - Casino Server**  
╚═══════════════════════════════════════╝

{description}

🎮 **What We Offer:**
🎲 10+ Casino Games (PvP & PvE)
💰 Point Economy System
⭐ VIP & Boost Features
🎫 Daily Lottery System
🏆 Rank Progression
🎁 Daily & Monthly Rewards

💎 **Games Available:**
⭕ Tic Tac Toe | 🚢 Naval War
💣 Mines | 🏰 Tower
🃏 Blackjack | 🎡 Roulette
🪙 Coinflip | 🎰 Slots
🎲 Dice

📊 **Server Stats:**
👥 Members: {member_count:,}
🎰 Games: 10+
💰 1 Point = €0.01
🎮 Type: Casino Bot

🚀 **Join Us!**
Type `.help` to get started!
Claim your free daily points with `.daily`
Start playing and winning today!

━━━━━━━━━━━━━━━━━━━━━━━━━
AfterBet Casino | {server_name}"""
    
    await announcement_channel.send(embed=embed)
    await announcement_channel.send(f"**📋 Copyable Version:**\n```\n{text_version}\n```")
    await ctx.send(f"✅ Advertisement sent to <#{announcement_channel_id}>!\n💡 Includes both embed and copyable text version.")

# ========== FLASK WEB SERVER (for Replit deployment health check) ==========
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ AfterBet Casino Bot is running!"

@app.route('/health')
def health():
    return {"status": "online", "bot": str(bot.user) if bot.user else "connecting", "guilds": len(bot.guilds) if bot.guilds else 0}

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve game images from attached_assets/stock_images/"""
    return send_from_directory('attached_assets/stock_images', filename)

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

# ========== BOT STARTUP ==========
if __name__ == "__main__":
    BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    
    if not BOT_TOKEN:
        print("=" * 60)
        print("❌ ERROR: DISCORD_BOT_TOKEN environment variable is not set!")
        print("=" * 60)
        print("🔧 In Replit:")
        print("   1. Go to 'Tools' → 'Secrets'")
        print("   2. Add a secret named: DISCORD_BOT_TOKEN")
        print("   3. Set the value to your Discord bot token")
        print("=" * 60)
        exit(1)
    
    # Start Flask web server in background thread (for deployment health check)
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print('🌐 Web server started on port 5000 (health check endpoint)')
    
    print("✅ DISCORD_BOT_TOKEN found, starting bot...")
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        exit(1)
