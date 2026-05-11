import platform
import pyautogui
import time
import random
import cv2
import numpy as np
import os
import webbrowser
import logging
import signal
import sys
import subprocess
from colorama import init, Fore, Back, Style
import requests

# Initialize Colorama for colored console output
init(autoreset=True)

try:
    import pygetwindow as gw
except ImportError:
    gw = None

# PyAutoGUI settings
pyautogui.FAILSAFE = True  # Move mouse to top-left to abort
pyautogui.PAUSE = 0.05  # Small pause between actions

# Configuration
GAME_TITLE = "Roblox"
GAME_URL = "roblox://placeId=110309181318869"
DISCONNECT_IMAGE = "disconnect_button.png"
CLIENT_BROKE_IMAGE = "client_broke.png"
CHECK_INTERVAL = 3  # Seconds between disconnect checks
AFK_ACTIONS = ["w", "a", "s", "d", "space"]  # Keys for AFK actions
ACTION_INTERVAL = (3, 10)  # Random delay range for AFK actions
MOUSE_MOVE_CHANCE = 0  # Probability of mouse movement (0 = disabled)
LAUNCH_DELAY = 10  # Seconds to wait for Roblox to launch
RESPONSE_TIMEOUT = 10  # Seconds to verify game is loaded
LOG_FILE = "afk_bot.log"
RETRY_ATTEMPTS = 3  # Number of retries for launching/joining
MAX_RELAUNCH_ATTEMPTS = 7  # Max relaunch attempts before exiting
RELAUNCH_DELAY = 5  # Seconds to wait between relaunch attempts (NEW)
ROBLOX_EXECUTABLE_WINDOWS = r"C:\Program Files (x86)\Roblox\Versions\RobloxPlayerBeta.exe"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1365846443201532027/us03qfh2-XQPuL6_c1M9pGj0SNvJCHkyAcT7oCWMT84_JrvjmL3dT1Y4PXWyeHX6HDNB"

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()

# Discord webhook function
def send_discord_webhook(message, level="info"):
    """Send a log message to a Discord webhook."""
    if not DISCORD_WEBHOOK_URL or "YOUR_DISCORD_WEBHOOK_URL_HERE" in DISCORD_WEBHOOK_URL:
        return
    try:
        color = 0x00FF00 if level == "info" else 0xFF0000
        data = {
            "embeds": [
                {
                    "title": f"AFK Bot {'Info' if level == 'info' else 'Error'}",
                    "description": message,
                    "color": color,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
            ]
        }
        response = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=5)
        if response.status_code != 204:
            print(Fore.YELLOW + f"Failed to send Discord webhook: {response.status_code}")
    except Exception as e:
        print(Fore.YELLOW + f"Error sending Discord webhook: {e}")

# Log function with console output and Discord webhook
def log(message, level="info"):
    """Log message to file, console, and Discord webhook."""
    if level == "error":
        logger.error(message)
        print(Back.WHITE + Fore.BLUE + message + Style.RESET_ALL)
    else:
        logger.info(message)
        print(Back.WHITE + Fore.CYAN + message + Style.RESET_ALL)
    send_discord_webhook(message, level)

# ASCII art with icy blue gradient effect
def print_gradient_ascii(ascii_art):
    """Print ASCII art with an icy blue gradient."""
    lines = ascii_art.splitlines()
    for i, line in enumerate(lines):
        ratio = i / len(lines)
        color = Fore.CYAN if ratio < 0.5 else Fore.BLUE
        print(Back.WHITE + color + line + Style.RESET_ALL)

zenith_text = '''
███████╗███████╗███╗░░██╗██╗████████╗██╗░░██╗
╚════██║██╔════╝████╗░██║██║╚══██╔══╝██║░░██║
░░███╔═╝█████╗░░██╔██╗██║██║░░░██║░░░███████║
██╔══╝░░██╔══╝░░██║╚████║██║░░░██║░░░██╔══██║
███████╗███████╗██║░╚███║██║░░░██║░░░██║░░██║
╚══════╝╚══════╝╚═╝░░╚══╝╚═╝░░░╚═╝░░░╚═╝░░╚═╝
'''
print_gradient_ascii(zenith_text)

# Signal handler for graceful exit
def signal_handler(sig, frame):
    log("Bot stopped by signal.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# System checks
def is_roblox_running():
    """Check if Roblox process is running."""
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                'tasklist /FI "IMAGENAME eq RobloxPlayerBeta.exe" /FO CSV /NH',
                capture_output=True, text=True, shell=True, timeout=1
            )
            return "RobloxPlayerBeta.exe" in result.stdout
        except:
            return False
    elif platform.system() == "Linux":
        try:
            result = subprocess.run(["pgrep", "-f", "Roblox"], capture_output=True, timeout=1)
            return result.returncode == 0
        except:
            return False
    return False

def is_roblox_window_open():
    """Check if Roblox window exists."""
    if platform.system() == "Windows" and gw:
        try:
            return bool(gw.getWindowsWithTitle(GAME_TITLE))
        except:
            return False
    elif platform.system() == "Linux":
        try:
            result = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, timeout=1)
            return GAME_TITLE in result.stdout
        except:
            return False
    return False

def focus_roblox():
    """Focus on the Roblox window."""
    if platform.system() == "Windows" and gw:
        try:
            windows = gw.getWindowsWithTitle(GAME_TITLE)
            if windows:
                windows[0].activate()
                time.sleep(0.2)
                return True
            return False
        except:
            return False
    elif platform.system() == "Linux":
        try:
            os.system(f"wmctrl -a {GAME_TITLE}")
            time.sleep(0.2)
            return True
        except:
            return False
    return False

def is_roblox_active():
    """Check if Roblox window is active."""
    if platform.system() == "Windows" and gw:
        try:
            active_window = gw.getActiveWindow()
            return active_window and GAME_TITLE in active_window.title
        except:
            return False
    elif platform.system() == "Linux":
        try:
            active_window = subprocess.check_output(
                ["xdotool", "getactivewindow", "getwindowname"], timeout=1
            ).decode().strip()
            return GAME_TITLE in active_window
        except:
            return False
    return False

def close_roblox():
    """Close all Roblox processes."""
    if platform.system() == "Windows":
        os.system("taskkill /IM RobloxPlayerBeta.exe /F >nul 2>&1")
        os.system("taskkill /IM RobloxPlayerLauncher.exe /F >nul 2>&1")
    elif platform.system() == "Linux":
        os.system("pkill -f Roblox > /dev/null 2>&1")
    time.sleep(1)

# Game launching and verification
def verify_game_loaded():
    """Verify Roblox has loaded the game."""
    start_time = time.time()
    while time.time() - start_time < RESPONSE_TIMEOUT:
        if is_roblox_running() and is_roblox_window_open() and not detect_disconnect():
            return True
        time.sleep(0.5)
    return False

def launch_game(is_relaunch=False):
    """Launch Roblox and join the game using the URL."""
    # Add delay for relaunches (NEW)
    if is_relaunch:
        log(f"Waiting {RELAUNCH_DELAY} seconds before relaunch...")
        time.sleep(RELAUNCH_DELAY)

    for attempt in range(RETRY_ATTEMPTS):
        log(f"Launching Roblox (Attempt {attempt + 1}/{RETRY_ATTEMPTS})")
        close_roblox()  # Ensure no existing Roblox processes
        webbrowser.open(GAME_URL)  # Open the game URL
        time.sleep(1)  # Brief pause to let the URL handler start

        # Fallback: Launch Roblox executable with URL (Windows only)
        if platform.system() == "Windows" and not is_roblox_running() and os.path.exists(ROBLOX_EXECUTABLE_WINDOWS):
            try:
                subprocess.Popen([ROBLOX_EXECUTABLE_WINDOWS, f"--play -t 0 -j {GAME_URL}"])
            except Exception as e:
                log(f"Failed to launch Roblox executable: {e}", level="error")

        # Wait for Roblox to launch
        start_time = time.time()
        while time.time() - start_time < LAUNCH_DELAY:
            if is_roblox_running() and is_roblox_window_open():
                break
            time.sleep(0.5)
        else:
            log("Roblox failed to launch or open window.", level="error")
            continue

        # Focus Roblox window
        if not focus_roblox() or not is_roblox_active():
            log("Failed to focus Roblox window.", level="error")
            continue

        # Verify game is loaded
        if verify_game_loaded():
            log("Roblox launched and game joined successfully.")
            return True

        log("Game failed to load.", level="error")

    log(f"Failed to launch Roblox after {RETRY_ATTEMPTS} attempts.", level="error")
    return False

# Disconnect detection
def capture_screen():
    """Capture the screen for image matching."""
    if not focus_roblox() or not is_roblox_active():
        return None
    try:
        screenshot = pyautogui.screenshot()
        screen = np.array(screenshot)
        return cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
    except:
        return None

def find_button(image_path):
    """Locate a button on the screen using image matching."""
    if not os.path.exists(image_path):
        log(f"Image file {image_path} not found.", level="error")
        return None
    screen = capture_screen()
    if screen is None:
        return None
    template = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if template is None:
        log(f"Failed to load image {image_path}.", level="error")
        return None
    try:
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= 0.8:
            x, y = max_loc
            h, w = template.shape[:2]
            return x + w // 2, y + h // 2
        return None
    except:
        return None

def detect_disconnect():
    """Detect if the game is disconnected."""
    for image in [DISCONNECT_IMAGE, CLIENT_BROKE_IMAGE]:
        coords = find_button(image)
        if coords:
            log(f"Detected {image} on screen.")
            return True
    return False

def reconnect():
    """Attempt to reconnect to the game."""
    log("Attempting to reconnect...")
    if detect_disconnect():
        button_coords = find_button(DISCONNECT_IMAGE) or find_button(CLIENT_BROKE_IMAGE)
        if button_coords:
            pyautogui.click(*button_coords)
            time.sleep(1)
            if not detect_disconnect():
                log("Reconnected successfully.")
                return True
    # Launch game with relaunch delay (MODIFIED)
    return launch_game(is_relaunch=True)

# AFK actions
def perform_afk_action():
    """Perform a random AFK action."""
    if not is_roblox_running() or not is_roblox_window_open() or not focus_roblox() or not is_roblox_active():
        return
    if random.random() < MOUSE_MOVE_CHANCE:
        x, y = pyautogui.position()
        pyautogui.moveTo(x + random.randint(-50, 50), y + random.randint(-50, 50), duration=0.3)
    else:
        action = random.choice(AFK_ACTIONS)
        duration = random.uniform(0.1, 0.3)
        pyautogui.keyDown(action)
        time.sleep(duration)
        pyautogui.keyUp(action)

# Game status checking
def check_game_status(relaunch_attempts):
    """Check if Roblox is closed or disconnected and relaunch if necessary."""
    if not is_roblox_running() or not is_roblox_window_open():
        log("Roblox closed or window not found. Relaunching...")
        close_roblox()
        # Launch game with relaunch delay (MODIFIED)
        if not launch_game(is_relaunch=True):
            relaunch_attempts += 1
            log(f"Relaunch failed. Attempt {relaunch_attempts}/{MAX_RELAUNCH_ATTEMPTS}.", level="error")
            if relaunch_attempts >= MAX_RELAUNCH_ATTEMPTS:
                log("Max relaunch attempts reached. Exiting...", level="error")
                sys.exit(1)
        else:
            relaunch_attempts = 0
    return relaunch_attempts

# Main loop
def main():
    log("Starting AFK bot. Move mouse to top-left to abort.")
    time.sleep(2)

    if not launch_game():  # Initial launch without delay
        log("Initial launch failed. Exiting...", level="error")
        sys.exit(1)

    relaunch_attempts = 0
    last_check = time.time()
    last_relaunch_time = time.time()

    while True:
        try:
            # Perform AFK action
            perform_afk_action()

            # Check game status
            relaunch_attempts = check_game_status(relaunch_attempts)

            # Delay between AFK actions
            time.sleep(random.uniform(*ACTION_INTERVAL))

            # Check for disconnect periodically
            if time.time() - last_check >= CHECK_INTERVAL:
                if detect_disconnect():
                    reconnect()
                    relaunch_attempts = check_game_status(relaunch_attempts)
                last_check = time.time()

            # Relaunch every 15 minutes for stability
            if time.time() - last_relaunch_time >= 15 * 60:
                log("15 minutes passed. Relaunching Roblox...")
                # Launch game with relaunch delay (MODIFIED)
                if launch_game(is_relaunch=True):
                    last_relaunch_time = time.time()
                    relaunch_attempts = 0

        except Exception as e:
            log(f"Main loop error: {e}.", level="error")
            time.sleep(2)
            relaunch_attempts = check_game_status(relaunch_attempts)
            if relaunch_attempts >= MAX_RELAUNCH_ATTEMPTS:
                log("Max relaunch attempts reached. Exiting...", level="error")
                sys.exit(1)

if __name__ == "__main__":
    main()
