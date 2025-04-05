import os
import re
import io
from dotenv import load_dotenv
from pydub import AudioSegment
import azure.cognitiveservices.speech as speechsdk

# .envからAzureキーとリージョンを読み込み
load_dotenv()
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

# 音声設定
VOICES = {
    "male": "zh-HK-WanLungNeural",
    "female": "zh-HK-HiuMaanNeural"
}

def extract_word_and_example(line):
    cols = [col.strip() for col in line.strip("|").split("|")]
    if len(cols) != 5:
        return None
    word = re.sub(r"[（(][^）)]+[)）]", "", cols[0]).strip()
    example_match = re.search(r"^(.*?)[（(](.*?)[)）]?$", cols[3])
    example = example_match.group(1).strip() if example_match else cols[3].strip()
    return word, example

def synthesize(text, voice_name):
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    speech_config.speech_synthesis_voice_name = voice_name
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3
    )
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return AudioSegment.from_file(io.BytesIO(result.audio_data), format="mp3")
    else:
        raise Exception(f"音声合成失敗: {result.reason}")

def main():
    # フォルダ構成を男女別で作成
    for gender in VOICES:
        os.makedirs(f"audio/{gender}/words", exist_ok=True)
        os.makedirs(f"audio/{gender}/examples", exist_ok=True)
        os.makedirs(f"audio/{gender}/batch", exist_ok=True)

    with open("output_file.txt", "r", encoding="utf-8") as f:
        lines = [line for line in f if line.startswith("|") and not "---" in line and not "単語" in line]

    # 男女別にキャッシュを保持
    word_audio_cache = {gender: {} for gender in VOICES}
    example_audio_cache = {gender: {} for gender in VOICES}

    for i in range(0, len(lines), 10):
        batch_lines = lines[i:i + 10]
        batch_index = i // 10 + 1

        for gender, voice_name in VOICES.items():
            batch_path = f"audio/{gender}/batch/output_batch_{batch_index}.mp3"

            # すでにバッチファイルが存在する場合はスキップ
            if os.path.exists(batch_path):
                print(f"⏭ バッチスキップ: {batch_path} は既に存在します")
                continue

            combined = AudioSegment.silent(duration=0)

            for j, line in enumerate(batch_lines):
                idx = i + j + 1
                result = extract_word_and_example(line)
                if not result:
                    print(f"⚠️ スキップ: 行 {idx} に不正な形式")
                    continue
                word, example = result

                word_path = f"audio/{gender}/words/word_{idx:03d}.mp3"
                example_path = f"audio/{gender}/examples/example_{idx:03d}.mp3"

                if os.path.exists(word_path):
                    word_audio_cache[gender][idx] = AudioSegment.from_file(word_path)
                else:
                    try:
                        word_audio_cache[gender][idx] = synthesize(word, voice_name)
                        word_audio_cache[gender][idx].export(word_path, format="mp3", bitrate="192k")
                    except Exception as e:
                        print(f"❌ 単語 {idx} ({word}) のTTS失敗: {e}")
                        continue

                if os.path.exists(example_path):
                    example_audio_cache[gender][idx] = AudioSegment.from_file(example_path)
                else:
                    try:
                        example_audio_cache[gender][idx] = synthesize(example, voice_name)
                        example_audio_cache[gender][idx].export(example_path, format="mp3", bitrate="192k")
                    except Exception as e:
                        print(f"❌ 例文 {idx} ({example}) のTTS失敗: {e}")
                        continue

                combined += word_audio_cache[gender][idx] + AudioSegment.silent(duration=1000)
                combined += example_audio_cache[gender][idx] + AudioSegment.silent(duration=500)

            combined.export(batch_path, format="mp3", bitrate="192k")
            print(f"✔ バッチ出力: {batch_path}")

if __name__ == "__main__":
    main()
