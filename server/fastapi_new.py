import sys, os
current_dir = os.path.dirname(__file__)
workspace_root = os.path.abspath(os.path.join(current_dir, os.pardir))
if workspace_root not in sys.path:
    sys.path.append(workspace_root)

import multiprocessing as mp
if __name__ != "__main__":
    try:
        mp.set_start_method("spawn", force=True)
        print("✅ (Main) Multiprocessing start method set to 'spawn'.")
    except RuntimeError:
        pass

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse, FileResponse
from openai import OpenAI
import base64, re, random, requests, time, asyncio, shutil, uuid, hashlib
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
import torch
from multiprocessing import Process, Queue, Manager
from SadTalker111.inference_module import (init_models, run_inference_fast)

# --- 경로 및 환경 변수 설정 ---
ffmpeg_path = os.path.expanduser("~/ffmpeg-7.0.2-amd64-static")
if os.path.exists(ffmpeg_path):
    os.environ["PATH"] = f"{ffmpeg_path}:{os.environ['PATH']}"
else:
    print("⚠️ 경고: 지정된 ffmpeg 경로를 찾을 수 없습니다.")

dotenv_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path)
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ELEVEN_KEY = os.getenv("ELEVEN_API_KEY")

BASE_DIR = Path(__file__).parent.resolve()
RESULTS_DIR = BASE_DIR / "results"
GREET_DIR = BASE_DIR / "greet_audios" 
RESULTS_DIR.mkdir(exist_ok=True)
GREET_DIR.mkdir(exist_ok=True) 

client = OpenAI(api_key=OPENAI_KEY)

# ✨✨✨ [업데이트] 요청하신 5종 보이스를 포함하여 전체 보이스 목록을 업데이트했습니다. ✨✨✨
MY_VOICE_IDS = {
    # --- 기본 보이스 ---
    "bong_pal": {"id": "PLfpgtLkFW07fDYbUiRJ", "tags": ["남", "노년", "차분"]},
    "min_ho":   {"id": "U1cJYS4EdbaHmfR7YzHd", "tags": ["남", "중년", "단정"]},
    "hyuk":     {"id": "ZJCNdZEjYwkOElxugmW2", "tags": ["남", "중년", "편안"]},
    
    # --- 1차 추가 보이스 ---
    "anna_teacher": {"id": "Cx2PEJFdr8frSuUVB6yZ", "tags": ["여", "청년", "활발", "긍정적"]},
    "richard_narrator": {"id": "6pVydnYcVtMsrrSeUKs6", "tags": ["남", "중년", "내레이션"]},
    "sarah_character": {"id": "emSmWzY0c0xtx5IFMCVv", "tags": ["여", "청년", "활발", "캐릭터"]},
    "brittney_peppy": {"id": "XiPS9cXxAVbaIWtGDHDh", "tags": ["여", "청년", "활발", "정보성"]},
    "shelby_british": {"id": "rfkTsdZrVWEVhDycUYn9", "tags": ["여", "청년", "차분", "정보성", "내레이션"]},
    "brittney_social": {"id": "kPzsL2i3teMYv0FxEYQ6", "tags": ["여", "청년", "활발", "정보성"]},
    "grandfather_namchun_kind": {"id": "5ON5Fnz24cnOozEQfGAm", "tags": ["남", "노년", "차분", "친절한", "내레이션"]},
    "grandfather_namchun_dark": {"id": "FQ3MuLxZh0jHcZmA5vW1", "tags": ["남", "노년", "진지한", "속삭이는"]},
    "deoksu_character": {"id": "IAETYMYM3nJvjnlkVTKI", "tags": ["남", "중년", "캐릭터", "귀여운"]},
    "jangho_husky": {"id": "UmYoqGlufKxhJ6NCx5Mv", "tags": ["남", "중년", "거친", "허스키"]},
    "annakim_narrator": {"id": "uyVNoMrnUku1dZyVEXwD", "tags": ["여", "청년", "내레이션"]},
    "kkc_narrator": {"id": "1W00IGEmNmwmsDeYy7ag", "tags": ["남", "청년", "활발", "안정적인", "내레이션"]},
    "kyungduk_authoritative": {"id": "2gbExjiWDnG1DMGr81Bx", "tags": ["남", "중년", "권위적인", "진지한", "정보성"]},
    "hunmin_soft": {"id": "MpbDJfQJUYUnp0i1QvOZ", "tags": ["남", "청년", "차분", "부드러운", "내레이션"]},
    "deokpal_rough": {"id": "wzMVIc8FAFmgMxFpN0uM", "tags": ["남", "중년", "거친", "남성적인", "내레이션"]},
    "jennie_informative": {"id": "z6Kj0hecH20CdetSElRT", "tags": ["여", "청년", "정보성", "활발"]},
    "seulki_calm": {"id": "ksaI0TCD9BstzEzlxj4q", "tags": ["여", "청년", "차분", "내레이션"]},
    "seer_morganna": {"id": "7NsaqHdLuKNFvEfjpUno", "tags": ["여", "노년", "신비로운", "캐릭터"]},
    
    # --- 2차 추가 보이스 ---
    "lola_storyteller": {"id": "gILcvhAz18uV9ARSsU4u", "tags": ["여", "중년", "활발", "캐릭터", "내레이션"]},
    "nanay_avelina": {"id": "HXiggO6rHDAxWaFMzhB7", "tags": ["여", "중년", "차분", "따뜻한", "친절한"]},
    "jacqui_aussie": {"id": "lNABL6eI3BpPT8BvSqjK", "tags": ["여", "청년", "편안", "내레이션"]},
    "tosca_deep": {"id": "fNmw8sukfGuvWVOp33Ge", "tags": ["여", "노년", "차분", "진지한", "내레이션"]},
    "angelina_storyteller": {"id": "MLpDWJvrjFIdb63xbJp8", "tags": ["여", "청년", "차분", "부드러운", "따뜻한", "내레이션"]},
}

try:
    VOICE_CACHE = requests.get("https://api.elevenlabs.io/v1/voices", headers={"xi-api-key": ELEVEN_KEY, "Accept": "application/json"}, timeout=15).json()["voices"]
    print(f"✅ ElevenLabs에서 {len(VOICE_CACHE)}개의 목소리를 로드했습니다.")
except Exception as e:
    print(f"Error fetching ElevenLabs voices: {e}")
    VOICE_CACHE = []

# --- 헬퍼 함수 ---
def parse_profile(text: str):
    t = text.lower()
    gender = "여" if re.search(r"여성|여자", t) else "남" if re.search(r"남성|남자", t) else None
    if re.search(r"아이|어린|소년|소녀", t): age = "아동"
    elif re.search(r"10대|20대|청년|젊", t): age = "청년"
    elif re.search(r"30대|40대|중년", t): age = "중년"
    elif re.search(r"50대|60대|70대|노인|노년", t): age = "노년"
    else: age = None
    pers_list = ["차분", "침착", "활발", "밝", "쾌활", "지적", "학구", "긍정적", "친절한", "진지한", "신비로운", "권위적인", "부드러운", "편안", "속삭이는", "거친", "허스키", "남성적인", "귀여운", "내레이션", "캐릭터", "정보성", "단정", "따뜻한"]
    found_pers = [p for p in pers_list if p in t]
    personality = found_pers[0] if found_pers else None
    return gender, age, personality

def choose_voice_unified(profile_txt: str):
    g, a, p = parse_profile(profile_txt)
    print(f"\n🕵️  프로필 분석 시작: 성별='{g}', 나이='{a}', 성격='{p}'")
    all_voices = []
    for name, details in MY_VOICE_IDS.items(): all_voices.append({"voice_id": details["id"], "labels_txt": " ".join(details["tags"]), "is_my_voice": True, "name": f"(내 목소리) {name}"})
    for voice in VOICE_CACHE:
        labels_txt = (voice.get("name", "") + " " + " ".join(map(str, voice.get("labels", {}).values()))).lower()
        all_voices.append({"voice_id": voice["voice_id"], "labels_txt": labels_txt, "is_my_voice": False, "name": voice.get("name", "Unknown")})
    
    gender_map = {"여": ["female", "woman", "girl", "여"], "남": ["male", "man", "boy", "남"]}
    age_map = {"아동": ["child", "kid", "아동"], "청년": ["young", "teen", "청년"], "중년": ["middle", "middle-aged", "중년"], "노년": ["old", "elder", "노년"]}
    pers_map = {
        "차분": ["calm", "soft", "차분", "침착"], "활발": ["bright", "cheerful", "활발", "밝", "쾌활"], "지적": ["smart", "intelligent", "지적", "학구"],
        "긍정적": ["positive", "긍정적"], "친절한": ["kind", "friendly", "친절한"], "진지한": ["serious", "진지한"], "신비로운": ["mysterious", "신비로운"],
        "권위적인": ["authoritative", "권위적인"], "부드러운": ["soft", "부드러운"], "편안": ["comfortable", "편안"], "속삭이는": ["whispering", "속삭이는"],
        "거친": ["rough", "거친"], "허스키": ["husky", "허스키"], "남성적인": ["masculine", "남성적인"], "귀여운": ["cute", "귀여운"],
        "내레이션": ["narration", "내레이션"], "캐릭터": ["character", "캐릭터"], "정보성": ["informative", "정보성"], "단정": ["neat", "단정"], "따뜻한": ["warm", "따뜻한"]
    }
    best_voices, best_score = [], -1.0
    for voice in all_voices:
        labels, score = voice["labels_txt"], 0.0
        if g and any(k in labels for k in gender_map.get(g, [])): score += 1
        if a and any(k in labels for k in age_map.get(a, [])): score += 1
        if p and p in pers_map and any(k in labels for k in pers_map[p]): score += 1
        if voice["is_my_voice"] and score > 0: score += 0.5
        if score > best_score: best_score, best_voices = score, [voice]
        elif score == best_score and score > 0: best_voices.append(voice)
    
    if best_voices:
        chosen_voice = random.choice(best_voices)
        print(f"🏆 최종 선택된 목소리: '{chosen_voice['name']}' (ID: {chosen_voice['voice_id']}), 점수: {best_score:.1f}\n")
        return chosen_voice['voice_id']
    else:
        print(f"⚠️ 매칭되는 목소리를 찾지 못해 기본 목소리('bong_pal')를 사용합니다.\n")
        return MY_VOICE_IDS['bong_pal']['id']

def get_profile(img): 
    prompt = """
너는 그림 속 인물에 어울리는 목소리를 찾아주는 '보이스 캐스팅 AI'다.
아래 분류 기준에 따라 그림 속 인물의 프로필을 반드시 추측해서, 가장 가능성 높은 조합으로 한 문장으로 설명해라.
---분류 기준---
1.  **성별:** 남, 여
2.  **나이대:** 아동, 청년, 중년, 노년
3.  **성격 (아래 목록에서 가장 어울리는 것을 1~2개 선택):**
    - **분위기:** 차분, 활발, 긍정적, 친절한, 진지한, 신비로운, 권위적인, 부드러운, 편안, 따뜻한
    - **목소리 특징:** 속삭이는, 거친, 허스키, 남성적인, 귀여운
    - **용도:** 내레이션, 캐릭터, 정보성, 단정
---출력 형식---
- 반드시 한 문장으로 요약해서 설명해라.
- 예시: '이 인물은 내레이션에 어울리는, 차분하고 권위적인 목소리의 노년 남성입니다.'
- '모르겠다' 또는 '추측하기 어렵다'와 같은 답변은 절대 하면 안 된다. 무조건 추측해서 답해라.
"""
    return client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, img]}]).choices[0].message.content.strip()
def get_dialogue(img): return client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": [{"type": "text", "text": "너는 이 미술 작품 그림 속의 인물이야. 설명 없이 바로 어린이에게 말을 건네는 1인칭 대사로 작품설명과 작가에대한 설명을 간단히 2줄로 말해.\n- GPT처럼 '죄송하지만' 혹은 설명·서론 절대 쓰지 마.\n- '안녕 나는 ~ 이/가 그린 ~야' 같은 말투로 무조건 아이에게 말하듯이 따뜻하고 친절하게."}, img]}]).choices[0].message.content.strip()
def get_artist_name(img): return client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": [{"type": "text", "text": "이 그림의 작가 이름만 정확하게 말해줘. 딱 작가 이름만 정확히 한 줄로. 예시: 빈센트 반 고흐"}, img]}]).choices[0].message.content.strip()
def has_batchim(korean_name: str) -> bool:
    if not korean_name: return False
    ch = korean_name[-1]
    if '가' <= ch <= '힣': return (ord(ch) - 0xAC00) % 28 != 0
    return False
def vocative(name: str) -> str: return f"{name}{'아' if has_batchim(name) else '야'}"

# ✨✨✨ [수정] 워커 프로세스 함수를 수정했습니다. ✨✨✨
def worker_process_loop(job_queue: Queue, greet_video_cache: dict, final_video_cache: dict, sadtalker_paths: dict, device: str):
    print("✅ (Worker) 워커 프로세스 시작")
    from SadTalker111.src.test_audio2coeff import Audio2Coeff
    from SadTalker111.src.facerender.animate import AnimateFromCoeff
    audio_to_coeff, animate_from_coeff = Audio2Coeff(sadtalker_paths, device), AnimateFromCoeff(sadtalker_paths, device)
    print(f"✅ (Worker) 모델 로딩 완료 (Device: {device}). 작업 대기 중...")
    while True:
        try:
            job_details = job_queue.get()
            if job_details is None: break
            job_id, job_type = job_details['job_id'], job_details['type']
            print(f"[{job_id}] (Worker) ▶▶▶ '{job_type}' 영상 생성 작업 시작")
            
            # ✨ [수정] run_inference_fast에 필요한 인자만 정확히 골라서 전달합니다.
            inference_args = {
                'audio_to_coeff': audio_to_coeff, 
                'animate_from_coeff': animate_from_coeff,
                'source_image_path': job_details['source_image_path'], 
                'crop_pic_path': job_details['crop_pic_path'],
                'coeff_path': job_details['coeff_path'], 
                'audio_path': job_details['audio_path'],
                'crop_info': job_details['crop_info'],
            }
            temp_video_path = run_inference_fast(**inference_args)
            
            dest_video_path = job_details['job_dir'] / f"{job_type}_video.mp4"
            shutil.move(temp_video_path, dest_video_path)
            print(f"[{job_id}] (Worker) 결과 영상 저장: {dest_video_path}")
            
            if job_type == "final": final_video_cache[job_id] = str(dest_video_path)
            else: greet_video_cache[job_id] = str(dest_video_path)
        except Exception as e:
            print(f"(Worker) ERROR: {e}")
            if 'job_id' in locals():
                job_type = locals().get('job_type', 'unknown')
                if job_type == "final": final_video_cache[job_id] = {"error": str(e)}
                else: greet_video_cache[job_id] = {"error": str(e)}
    print("⚠️ (Worker) 워커 프로세스 종료.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    manager = Manager()
    app.state.GREET_VIDEO_CACHE, app.state.FINAL_VIDEO_CACHE, app.state.DESC_TTS_CACHE = manager.dict(), manager.dict(), manager.dict()
    app.state.job_queue = Queue()
    print("✅ (Main) 프로세스 공유 캐시 및 큐 생성 완료.")
    print("⏳ (Main) SadTalker 모델을 백그라운드에서 로딩합니다...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    checkpoint_dir = "/home/team06/workspace/SadTalker111/checkpoints"
    if not os.path.exists(checkpoint_dir): raise FileNotFoundError(f"SadTalker 체크포인트 디렉토리({checkpoint_dir})를 찾을 수 없습니다.")
    sadtalker_init_data = await asyncio.to_thread(init_models, checkpoint_dir, device, 256, False, "full")
    app.state.preprocess_model = sadtalker_init_data["preprocess_model"]
    app.state.sadtalker_paths = sadtalker_init_data["sadtalker_paths"]
    print("✅ (Main) Preprocess 모델 로딩 완료.")
    worker = Process(target=worker_process_loop, args=(app.state.job_queue, app.state.GREET_VIDEO_CACHE, app.state.FINAL_VIDEO_CACHE, app.state.sadtalker_paths, device), daemon=True)
    worker.start()
    app.state.worker = worker
    yield
    print("⚠️ (Main) 서버 종료 절차 시작...")
    app.state.job_queue.put(None)
    app.state.worker.join(timeout=5)
    print("✅ (Main) 워커 프로세스 정상 종료.")

async def background_content_pipeline(job_id: str, nickname: str, job_dir: Path, source_image_path: Path, crop_pic_path: Path, coeff_path: str, crop_info: list, app_state):
    try:
        print(f"[{job_id}] (Main) ▶▶▶ '설명' 콘텐츠 준비 시작")
        with open(crop_pic_path, "rb") as f: b64img = base64.b64encode(f.read()).decode("ascii")
        img_payload = {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64img}"}}
        with ThreadPoolExecutor() as executor:
            f_profile = executor.submit(get_profile, img_payload)
            f_dialogue = executor.submit(get_dialogue, img_payload)
            f_artist = executor.submit(get_artist_name, img_payload)
            profile_text, dialogue_text, artist_name = f_profile.result(), f_dialogue.result(), f_artist.result()
            print(f"[{job_id}] (Main) [GPT] 프로필 텍스트: '{profile_text}'")
            voice_id = choose_voice_unified(profile_text)
            print(f"[{job_id}] (Main) 🚀 '설명' TTS 요청 시작 (Voice ID: {voice_id})")
            headers = {"xi-api-key": ELEVEN_KEY, "Content-Type": "application/json"}
            tts_settings = {"stability": 0.3, "similarity_boost": 0.85}
            body = {"text": dialogue_text, "model_id": "eleven_multilingual_v2", "voice_settings": tts_settings}
            desc_audio_content = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}", headers=headers, json=body).content
            print(f"[{job_id}] (Main) ✅ '설명' TTS 처리 완료")
        desc_audio_path = job_dir / "description_audio.mp3"
        desc_audio_path.write_bytes(desc_audio_content)
        app_state.DESC_TTS_CACHE[job_id] = {"result": dialogue_text, "profile": profile_text, "artist": artist_name}
        common_job_data = {'coeff_path': coeff_path, 'crop_pic_path': str(crop_pic_path), 'crop_info': crop_info, 'source_image_path': str(source_image_path), 'job_dir': job_dir}
        app_state.job_queue.put({**common_job_data, 'job_id': job_id, 'type': 'final', 'audio_path': str(desc_audio_path)})
        print(f"[{job_id}] (Main) ✅ '최종' 영상 작업을 큐에 추가했습니다.")
    except Exception as e:
        print(f"(Main) [background_content_pipeline] ERROR: {e}")
        app_state.FINAL_VIDEO_CACHE[job_id] = {"error": str(e)}

app = FastAPI(lifespan=lifespan)

@app.post("/create-greet")
def create_greet(nickname: str = Form(...)):
    nick_clean = nickname.strip()
    hash8 = hashlib.sha1(nick_clean.encode()).hexdigest()[:8]
    mp3_path = GREET_DIR / f"greet_{hash8}.mp3"
    if not mp3_path.exists():
        text = f"{vocative(nick_clean)} 아안녕? 퀴즈를 맞추면 내 이야기를 들려주마"
        headers = {"xi-api-key": ELEVEN_KEY, "accept": "audio/mpeg", "Content-Type": "application/json"}
        # ✨✨✨ [업데이트] 인사말 목소리를 'Tosca'로 변경했습니다. ✨✨✨
        voice_id = 'fNmw8sukfGuvWVOp33Ge' # Tosca
        body = {"model_id": "eleven_multilingual_v2", "text": text, "voice_settings": {}}
        try:
            r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream", headers=headers, json=body, timeout=20)
            r.raise_for_status()
            mp3_path.write_bytes(r.content)
            print(f"✅ (Main) 인사말 오디오 생성 완료: {mp3_path}")
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
    return {"ok": True}

@app.post("/preprocess")
async def preprocess(request: Request, background_tasks: BackgroundTasks, image: UploadFile = File(...), nickname: str = Form(...)):
    job_id = uuid.uuid4().hex
    job_dir = RESULTS_DIR / job_id
    job_dir.mkdir(exist_ok=True)
    source_image_path = job_dir / "source.jpg"
    await image.seek(0)
    source_image_path.write_bytes(await image.read())
    print(f"\n[{job_id}] (Main) 새 작업 시작. Job Directory: {job_dir}")
    while not hasattr(request.app.state, 'preprocess_model'):
        await asyncio.sleep(0.1)
    coeff_path, crop_pic_path, crop_info = request.app.state.preprocess_model.generate(str(source_image_path), str(job_dir), "full", source_image_flag=True, pic_size=256)
    nick_clean = nickname.strip()
    hash8 = hashlib.sha1(nick_clean.encode()).hexdigest()[:8]
    greet_audio_path = GREET_DIR / f"greet_{hash8}.mp3"
    common_job_data = {'coeff_path': coeff_path, 'crop_pic_path': str(crop_pic_path), 'crop_info': crop_info, 'source_image_path': str(source_image_path), 'job_dir': job_dir}
    request.app.state.job_queue.put({**common_job_data, 'job_id': job_id, 'type': 'greet', 'audio_path': str(greet_audio_path)})
    print(f"[{job_id}] (Main) ✅ '인사' 영상 작업을 큐에 추가했습니다.")
    background_tasks.add_task(background_content_pipeline, job_id, nickname, job_dir, source_image_path, Path(crop_pic_path), coeff_path, crop_info, request.app.state)
    print(f"[{job_id}] (Main) ✅ '설명' 콘텐츠 파이프라인을 백그라운드에 등록.")
    return {"job_id": job_id}

# (GET 엔드포인트들은 기존과 동일합니다.)
@app.get("/get-greet-video")
async def get_greet_video(request: Request, job_id: str):
    for _ in range(200): 
        if job_id in request.app.state.GREET_VIDEO_CACHE:
            result = request.app.state.GREET_VIDEO_CACHE.get(job_id)
            if isinstance(result, str) and os.path.exists(result): return FileResponse(result, media_type="video/mp4")
            elif isinstance(result, dict) and 'error' in result: raise HTTPException(500, f"Video generation failed: {result['error']}")
        await asyncio.sleep(0.1)
    raise HTTPException(408, "Greet video not ready or timed out.")

@app.get("/get-description")
async def get_description(request: Request, job_id: str):
    for _ in range(150):
        if job_id in request.app.state.DESC_TTS_CACHE:
            result = request.app.state.DESC_TTS_CACHE.get(job_id)
            if result and 'error' not in result: return JSONResponse(result)
            elif result and 'error' in result: raise HTTPException(500, f"Description generation failed: {result['error']}")
        await asyncio.sleep(0.1)
    raise HTTPException(408, "Description not ready or timed out.")

@app.get("/get-final-video")
async def get_final_video(request: Request, job_id: str):
    for _ in range(450): 
        if job_id in request.app.state.FINAL_VIDEO_CACHE:
            result = request.app.state.FINAL_VIDEO_CACHE.get(job_id)
            if isinstance(result, str) and os.path.exists(result): return FileResponse(result, media_type="video/mp4")
            elif isinstance(result, dict) and 'error' in result: raise HTTPException(500, f"Video generation failed: {result['error']}")
        await asyncio.sleep(0.1)
    raise HTTPException(408, "Final video not ready or timed out.")


# --- 서버 실행 (터미널에서 실행) ---
# uvicorn fastapi_new:app --host 0.0.0.0 --port 5058