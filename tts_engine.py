import requests
import json
import os
from config_manager import config

def generate_tts(text, output_path="output.mp3"):
    """
    Calls Xiaomi MiMo TTS API.
    Returns the path to the generated audio file if successful, None otherwise.
    """
    api_key = config.get("api_key")
    api_url = config.get("api_url")
    model = config.get("model")
    voice = config.get("voice")
    speed = config.get("speed")
    dialect = config.get("dialect", "无")
    emotion = config.get("emotion", "无")

    if not api_key:
        print("Missing API key. Set MIMO_API_KEY or add api_key to config.json.")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = []
    
    # Use natural language for dialect, emotion, and speed since voice is handled structurally
    style_prompt = ""
    if speed < 0.8:
        style_prompt += "请把语速放得非常慢。"
    elif speed < 1.0:
        style_prompt += "请把语速稍微放慢一点。"
    elif speed > 1.5:
        style_prompt += "请用非常快的语速朗读。"
    elif speed > 1.0:
        style_prompt += "请用较快的语速朗读。"
        
    if dialect != "普通话" and dialect != "无":
        style_prompt += f"请使用{dialect}口音。"
    if emotion != "默认" and emotion != "无":
        style_prompt += f"请带有{emotion}的情感。"
        
    if style_prompt:
        messages.append({"role": "user", "content": style_prompt})
        
    messages.append({"role": "assistant", "content": text})

    payload = {
        "model": model,
        "messages": messages,
        "audio": {
            "voice": voice,
            "format": "mp3"
        }
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        # Check if the response is directly an audio file or JSON
        content_type = response.headers.get('Content-Type', '')
        if 'audio' in content_type:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return output_path
        else:
            data = response.json()
            
            # Clean print: deep copy to avoid modifying original data
            debug_data = json.loads(json.dumps(data))
            try:
                audio_str = debug_data.get("choices", [{}])[0].get("message", {}).get("audio", {}).get("data", "")
                if audio_str and len(audio_str) > 40:
                    debug_data["choices"][0]["message"]["audio"]["data"] = audio_str[:20] + "......"
            except Exception:
                pass
            print("API returned JSON:", json.dumps(debug_data, ensure_ascii=False))

            # Extract base64 audio and save it
            try:
                import base64
                audio_b64 = data["choices"][0]["message"]["audio"]["data"]
                if audio_b64:
                    with open(output_path, 'wb') as f:
                        f.write(base64.b64decode(audio_b64))
                    return output_path
            except Exception as e:
                print(f"Failed to extract audio from JSON: {e}")
                
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"TTS API Request failed: {e}")
        if e.response is not None:
            print("Response:", e.response.text)
        return None
