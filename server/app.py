# 📄 app.py (analysis_api/app.py) 수정본

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from ultralytics import YOLO
from openai import OpenAI
import tempfile
import os
import base64
from gtts import gTTS
import uuid
from dotenv import load_dotenv
from PIL import Image
import numpy as np

# 현재 경로 기준
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "static", "audio")
MODEL_PATH = os.path.join(BASE_DIR, "model", "yolov8n.pt")  # 수정된 모델 경로
os.makedirs(AUDIO_DIR, exist_ok=True)

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)
openai_api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openai_api_key)

app = Flask(__name__)
CORS(app)

model = YOLO(MODEL_PATH)

# 클래스 이름 매핑 (YOLO 라벨 순서)
CLASS_NAMES = ['face', 'left_eye', 'right_eye', 'nose', 'mouth']

# 얼굴, 눈, 코, 입 감지
def detect_face_parts(image_path):
    img = Image.open(image_path).convert("RGB")
    img = np.array(img)

    results = model.predict(source=image_path, save=False)
    face_data = []

    for result in results:
        for box in result.boxes.xyxy:
            x1, y1, x2, y2 = box.tolist()
            box_dict = {
                "x": int(x1),
                "y": int(y1),
                "width": int(x2 - x1),
                "height": int(y2 - y1)
            }
            face_data.append({
                "face_box": box_dict,
                "eyes": [],
                "nose": None,
                "mouth": None
            })

    return face_data


# GPT-4 Vision 설명 생성
def describe_with_gpt(image_path):
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "당신은 박물관 도슨트입니다. 명화에 대해 친절히 설명해주세요."},
            {"role": "user", "content": [
                {"type": "text", "text": "이 그림을 간략하게 설명해줘."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
            ]}
        ],
        max_tokens=600
    )
    return response.choices[0].message.content

# TTS 생성
def generate_tts(text):
    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    tts = gTTS(text, lang='ko')
    tts.save(filepath)
    return filename

# API 엔드포인트
@app.route("/analyze", methods=["POST"])
def analyze():
    if 'image' not in request.files:
        return jsonify({"error": "이미지 파일 없음"}), 400

    image_file = request.files['image']
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        image_file.save(tmp)
        image_path = tmp.name

    try:
        face_data = detect_face_parts(image_path)
        description = describe_with_gpt(image_path)
        audio_filename = generate_tts(description)
    except Exception as e:
        os.remove(image_path)
        return jsonify({"error": str(e)}), 500

    os.remove(image_path)
    return jsonify({
        "faces": face_data,
        "result": description,
        "audio_url": f"/static/audio/{audio_filename}"
    })

@app.route("/static/audio/<path:filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        ssl_context=('cert.pem', 'key.pem')
    )


