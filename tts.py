import os
import re
import io
from google.cloud import texttospeech
from pydub import AudioSegment

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"
client = texttospeech.TextToSpeechClient()

def extract_word_and_example(line):
    cols = [col.strip() for col in line.strip("|").split("|")]
    if len(cols) != 5:
        return None
    word = re.sub(r"[（(][^）)]+[)）]", "", cols[0]).strip()
    example_match = re.search(r"^(.*?)[（(](.*?)[)）]?$", cols[3])
    example = example_match.group(1).strip() if example_match else cols[3].strip()
    return word, example

def synthesize(text, voice_name="yue-HK-Standard-A"):
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code="yue-HK", name=voice_name)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = client.synthesize_speech(input=input_text, voice=voice, audio_config=audio_config)
    return AudioSegment.from_file(io.BytesIO(response.audio_content), format="mp3")

def main():
    # ディレクトリ作成
    os.makedirs("audio/words", exist_ok=True)
    os.makedirs("audio/examples", exist_ok=True)
    os.makedirs("audio/batch", exist_ok=True)

    # 入力データ読み込み
    with open("output_file.txt", "r", encoding="utf-8") as f:
        lines = [line for line in f if line.startswith("|") and not "---" in line and not "単語" in line]

    # 音声キャッシュ（indexをキーに）
    word_audio_cache = {}
    example_audio_cache = {}

    # バッチごとの音声合成
    for i in range(0, len(lines), 10):
        batch_lines = lines[i:i + 10]
        combined = AudioSegment.silent(duration=0)

        for j, line in enumerate(batch_lines):
            idx = i + j + 1
            result = extract_word_and_example(line)
            if not result:
                continue
            word, example = result

            # 単語・例文の音声がキャッシュになければ生成
            if idx not in word_audio_cache:
                word_audio_cache[idx] = synthesize(word)
                word_audio_cache[idx].export(f"audio/words/word_{idx:03d}.mp3", format="mp3")
            if idx not in example_audio_cache:
                example_audio_cache[idx] = synthesize(example)
                example_audio_cache[idx].export(f"audio/examples/example_{idx:03d}.mp3", format="mp3")

            # バッチ合成に追加
            combined += word_audio_cache[idx] + AudioSegment.silent(duration=1000) \
                        + example_audio_cache[idx] + AudioSegment.silent(duration=500)

        combined.export(f"audio/batch/output_batch_{i // 10 + 1}.mp3", format="mp3")
        print(f"✔ バッチ出力: output_batch_{i // 10 + 1}.mp3")

if __name__ == "__main__":
    main()
