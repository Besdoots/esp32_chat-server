from flask import Flask, request, jsonify, send_file
import os
from datetime import datetime
import wave
import openai

app = Flask(__name__)

UPLOAD_FOLDER = 'recordings'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

openai.api_key = "YOUR_OPENAI_API_KEY"  # ✉️ Thay bằng API key của bạn

def save_raw_to_wav(raw_path, wav_path):
    with open(raw_path, 'rb') as raw_file:
        raw_data = raw_file.read()

    with wave.open(wav_path, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # 16-bit = 2 byte
        wav_file.setframerate(8000)
        wav_file.writeframes(raw_data)

def transcribe_audio(file_path):
    with open(file_path, "rb") as f:
        transcript = openai.Audio.transcribe("whisper-1", f)
    return transcript['text']

def chatgpt_reply(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Bạn là trợ lý thân thiện."},
            {"role": "user", "content": text}
        ]
    )
    return response['choices'][0]['message']['content']

@app.route("/")
def home():
    return "✅ ESP32 Voice Server dang chay!"

@app.route("/audio", methods=["POST"])
def receive_audio():
    raw_data = request.data
    if not raw_data:
        return "❌ Khong co du lieu!", 400

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_path = os.path.join(UPLOAD_FOLDER, f"audio_{timestamp}.raw")
    wav_path = raw_path.replace(".raw", ".wav")

    with open(raw_path, 'ab') as f:
        f.write(raw_data)

    # Chuyển đổi sang WAV
    save_raw_to_wav(raw_path, wav_path)

    # Nhận diện giọng nói
    try:
        text = transcribe_audio(wav_path)
        print("👊 Van ban nhan duoc:", text)

        # ChatGPT trả lời
        reply = chatgpt_reply(text)
        print("🔊 Tra loi:", reply)

        return jsonify({"transcript": text, "reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/playback", methods=["GET"])
def playback():
    # Gửi file WAV mới nhất
    files = sorted(
        [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(".wav")],
        key=lambda x: os.path.getmtime(os.path.join(UPLOAD_FOLDER, x)),
        reverse=True
    )
    if not files:
        return "❌ Khong co file de phat!", 404

    latest = os.path.join(UPLOAD_FOLDER, files[0])
    return send_file(latest, mimetype="audio/wav")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
