import os
import json
import streamlit as st
import speech_recognition as sr
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. ページ初期設定
st.set_page_config(
    page_title="2言語同時翻訳 & カタカナ発音",
    page_icon="🔤",
    layout="centered"
)

# 2. セッション状態（実行回数カウンター）の初期化
if "translation_count" not in st.session_state:
    st.session_state.translation_count = 0

# 3. 環境変数の読み込みとGeminiクライアントの初期化
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("エラー: .env ファイルに GEMINI_API_KEY が設定されていません。")
    st.stop()

client = genai.Client(api_key=api_key)

def process_translation(text: str):
    """Gemini APIを呼び出してJSON形式で翻訳結果を取得する関数"""
    prompt = f"""
    以下の入力文を翻訳し、指定されたJSONフォーマットのみで出力してください。

    入力文: "{text}"

    【出力フォーマット】
    {{
        "english": "英語翻訳文",
        "phonetic_katakana": "英語の発音に近いカタカナ表記（例: ウェア イズ ザ ステーション）",
        "japanese": "日本語翻訳文"
    }}
    """
    try:
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        # 成功したらカウントアップ
        st.session_state.translation_count += 1
        return json.loads(response.text)
    except Exception as e:
        st.error(f"APIエラーが発生しました: {e}")
        return None

def record_audio():
    """マイクから音声を拾って文字起こしする関数"""
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.info("🎤 聞き取り中... マイクに向かって話してください")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            st.warning("⏳ 音声認識中...")
            text = recognizer.recognize_google(audio, language="ja-JP")
            return text
    except sr.WaitTimeoutError:
        st.error("音が検出されませんでした。もう一度お試しください。")
    except sr.UnknownValueError:
        st.error("音声を読み取れませんでした。")
    except sr.RequestError as e:
        st.error(f"音声認識サービスエラー: {e}")
    except Exception as e:
        st.error(f"マイクエラー: {e}")
    return None

# --- UI画面の構築 ---
st.title("🔤 2言語同時翻訳 ＆ カタカナ発音")
st.caption("EVEN G2 搭載を見据えたリアルタイム翻訳プロトタイプ")

st.markdown("---")

# 入力モードの選択
input_mode = st.radio("入力方法を選択:", ("🎤 マイク音声入力", "⌨️ テキスト手入力"), horizontal=True)

target_text = ""

if input_mode == "🎤 マイク音声入力":
    # 2カラムでボタンと使用回数表示を配置
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("音声聞き取りスタート", type="primary", use_container_width=True):
            target_text = record_audio()
            if target_text:
                st.success(f"認識結果: 「{target_text}」")

    with col2:
        # ボタンの右下に回数・上限目安を表示
        st.metric(label="現在の実行回数", value=f"{st.session_state.translation_count} 回")
        st.caption("※無料枠目安: 15回/分, 1500回/日")

else:
    target_text = st.text_input("翻訳したい日本語を入力してください:", placeholder="例: 一番近い駅はどこですか？")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("翻訳を実行", type="primary", use_container_width=True):
            pass
    with col2:
        st.metric(label="現在の実行回数", value=f"{st.session_state.translation_count} 回")
        st.caption("※無料枠目安: 15回/分, 1500回/日")

# 翻訳処理と結果のUI表示
if target_text:
    with st.spinner("Geminiで翻訳処理中..."):
        translation = process_translation(target_text)

    if translation:
        st.subheader("🖥️ 表示イメージ（EVEN G2 上下画面想定）")
        
        # 英語・カタカナカード（上段表示用）
        st.info(
            f"**[上段 ➔ EN]**\n### {translation.get('english')}\n"
            f"*{translation.get('phonetic_katakana')}*"
        )
        
        # 日本語カード（下段表示用）
        st.success(
            f"**[下段 ➔ JP]**\n### {translation.get('japanese')}"
        )