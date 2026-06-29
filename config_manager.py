import json
import os
import sys


def get_app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


CONFIG_FILE = os.path.join(get_app_dir(), "config.json")

ENV_KEYS = {
    "api_key": "MIMO_API_KEY",
    "api_url": "MIMO_API_URL",
    "model": "MIMO_TTS_MODEL",
}

DEFAULT_CONFIG = {
    "api_key": "",
    "api_url": "https://api.xiaomimimo.com/v1/chat/completions",
    "model": "mimo-v2.5-tts",
    "voice": "mimo_default",
    "speed": 1.0,
    "dialect": "无",
    "emotion": "无"
}

VOICES = ["mimo_default", "冰糖", "茉莉", "苏打", "白桦", "Mia", "Chloe", "Milo", "Dean"]
DIALECTS = ["无", "东北话", "四川话", "河南话", "粤语", "台湾腔"]
EMOTIONS = ["无", "开心", "悲伤", "生气"]

class ConfigManager:
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
            except Exception as e:
                print(f"Error loading config: {e}")

    def save_config(self):
        try:
            disk_config = self.config.copy()
            for key, env_name in ENV_KEYS.items():
                if os.environ.get(env_name):
                    disk_config[key] = DEFAULT_CONFIG.get(key, "")

            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(disk_config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        env_name = ENV_KEYS.get(key)
        if env_name:
            env_value = os.environ.get(env_name)
            if env_value:
                return env_value

        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

config = ConfigManager()
