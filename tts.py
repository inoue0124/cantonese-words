import os
import re
import io
from google.cloud import texttospeech
from pydub import AudioSegment

# ✅ 認証キーを指定（同階層にある service_account.json を使用）
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"
client = texttospeech.TextToSpeechClient()


def extract_word_and_example(line):
    cols = [col.strip() for col in line.strip("|").split("|")]
    if len(cols) != 5:
        return None
    word = re.sub(r"[（(][^）)]+[)）]", "", cols[0]).strip()  # 単語内の英訳削除
    example_match = re.search(r"^(.*?)[（(](.*?)[)）]?$", cols[3])
    example = example_match.group(1).strip() if example_match else cols[3].strip()
    return word, example


def synthesize(text, voice_name="yue-HK-Standard-A"):
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code="yue-HK", name=voice_name)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )
    return AudioSegment.from_file(io.BytesIO(response.audio_content), format="mp3")


def synthesize_batch(lines, batch_index):
    os.makedirs("audio", exist_ok=True)  # 🔹 audio フォルダを作成（なければ）
    combined = AudioSegment.silent(duration=0)
    for line in lines:
        result = extract_word_and_example(line)
        print(line)
        if result:
            word, example = result
            word_audio = synthesize(word)
            pause = AudioSegment.silent(duration=1000)
            example_audio = synthesize(example)
            combined += (
                word_audio + pause + example_audio + AudioSegment.silent(duration=500)
            )
    combined.export(f"audio/output_batch_{batch_index}.mp3", format="mp3")


# 入力Markdownファイルの読み込み
markdown_file = "output_file.txt"
with open(markdown_file, "r", encoding="utf-8") as f:
    lines = [
        line
        for line in f
        if line.startswith("|") and not "---" in line and not "単語" in line
    ]

# 10行ごとに分けて音声生成
for i in range(0, len(lines), 10):
    batch_lines = lines[i : i + 10]
    synthesize_batch(batch_lines, i // 10 + 1)
