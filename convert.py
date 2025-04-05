import os
import re
from pycantonese import characters_to_jyutping

input_path = "output_file.txt"
output_path = "index.html"


def remove_english_from_japanese(text):
    return re.sub(r'[（(][a-zA-Z0-9\s　.,;:/!?\-\'"()&【】]+[)）]', "", text).strip()


def convert_sentence_with_jyutping(sentence):
    chars = []
    jyuts = []
    for char, jyut in characters_to_jyutping(sentence):
        chars.append(char)
        jyuts.append(jyut if jyut else " ")

    return "".join(chars), " ".join(jyuts)


def extract_word_and_example(cols):
    word = re.sub(r"[（(][^）)]+[)）]", "", cols[0]).strip()
    jp_meaning = remove_english_from_japanese(cols[1])
    jyutping = cols[2].strip()
    example = cols[3].strip()

    match = re.search(r"(.*?)[（(](.*?)[)）]?$", example)
    chinese_part = match.group(1).strip() if match else example
    jp_translation = match.group(2).strip() if match and match.group(2) else ""

    hanzi, jyut = convert_sentence_with_jyutping(chinese_part)

    # HTML構造をしっかり分離
    example_html = (
        f"<div class='example-block'>"
        f"<div class='hanzi'>{hanzi}</div>"
        f"<div class='jyutping-line'>{jyut}</div>"
        f"<div class='translation'>{jp_translation}</div>"
        f"</div>"
    )

    return word, jp_meaning, jyutping, example_html


if __name__ == "__main__":
    with open(input_path, "r", encoding="utf-8") as f:
        lines = [
            line.strip()
            for line in f
            if line.startswith("|") and "---" not in line and "単語" not in line
        ]

    entries = []
    for line in lines:
        cols = [col.strip() for col in line.strip("|").split("|")]
        if len(cols) == 4:
            entries.append(extract_word_and_example(cols))

    html_parts = [
        """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>広東語 単語リスト</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #f9fafb; margin: 2rem; color: #111; }
        .section { margin-bottom: 3rem; }
        .section-title { font-size: 1.2rem; font-weight: bold; margin-bottom: 1rem; color: #555; }
        table { width: 100%; border-collapse: collapse; background: #fff; box-shadow: 0 2px 6px rgba(0,0,0,0.06); border-radius: 8px; overflow: hidden; table-layout: auto; }
        th, td {
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #eee;
            text-align: left;
            vertical-align: middle;
        }
        th:first-child, td:first-child {
            width: 30px;
            color: #888;
            font-size: 0.8rem;
        }
        td:nth-child(2) {
            font-weight: bold;
            color: #e11d48;
            white-space: nowrap;
            font-size: 1.5rem;
        }
        td:nth-child(3) { color: #555; }
        td:nth-child(4) {
            width: 50%;
            color: #333;
            font-size: 1.1rem;
        }
        .jyutping {
            font-size: 0.8rem;
            color: #e11d48;
            display: block;
            margin-top: 0.2rem;
        }
        .jyutping-line {
            font-size: 0.8rem;
            color: #666;
            margin-top: 0.2rem;
            letter-spacing: 1px;
        }
        .translation {
            margin-top: 0.3rem;
            font-size: 1rem;
            color: #333;
        }
        .example-block {
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
        }
        .audio-player { margin-bottom: 1rem; }
        .search-bar { margin-bottom: 2rem; width: 100%; }
        input[type="text"] { padding: 16px; width: -webkit-fill-available; border: 0.5px solid #ccc; border-radius: 6px; font-size: 1.2rem; }
        .section-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .audio-button {
            cursor: pointer;
            border: none;
            background: none;
            font-size: 1.2rem;
            color: #e11d48;
            transition: transform 0.2s;
        }
        .audio-button:hover {
            transform: scale(1.2);
        }
        .audio-text {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .audio-buttons-column {
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
            margin-right: 0.5rem;
        }

        @media print {
            body {
                background: white;
                margin: 0.5cm;
                font-size: 10pt;
                line-height: 1.2;
            }

            .search-bar,
            .audio-player,
            .custom-audio-button,
            .audio-button,
            .section-header audio,
            button,
            a[href$=".zip"] {
                display: none !important;
            }

            .section {
                margin-bottom: 1rem;
            }

            /* 印刷のときだけページの下で途切れないように */
            tr, td {
                page-break-inside: avoid;
            }
        }


    </style>
    <script>
        function filterEntries() {
            const keyword = document.getElementById("search").value.toLowerCase();
            const sections = document.querySelectorAll(".section");
            sections.forEach(section => {
                const rows = section.querySelectorAll("tbody tr");
                let visibleCount = 0;
                rows.forEach(row => {
                    const text = row.innerText.toLowerCase();
                    const match = text.includes(keyword);
                    row.style.display = match ? "" : "none";
                    if (match) visibleCount++;
                });
                section.style.display = visibleCount > 0 ? "" : "none";
            });
        }
        document.addEventListener("DOMContentLoaded", () => {
            const audio = new Audio();
            let currentBtn = null;
            document.querySelectorAll(".custom-audio-button").forEach(button => {
                button.addEventListener("click", () => {
                    const src = button.dataset.src;
                    if (audio.src !== location.href + src) audio.src = src;

                    if (audio.paused || currentBtn !== button) {
                        audio.play();
                        if (currentBtn) currentBtn.classList.remove("playing");
                        button.classList.add("playing");
                        currentBtn = button;
                    } else {
                        audio.pause();
                        audio.currentTime = 0;
                        button.classList.remove("playing");
                        currentBtn = null;
                    }

                    audio.onended = () => {
                        if (currentBtn) currentBtn.classList.remove("playing");
                        currentBtn = null;
                    };
                });
            });
        });
    </script>
</head>
<body>
    <div class="search-bar">
        <input type="text" id="search" oninput="filterEntries()" placeholder="単語・読み・意味・例文で検索...">
    </div>
    <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem;">
        <a href="download/audio.zip" download style="padding: 10px 20px; font-size: 1rem; background-color: #e11d48; color: white; border-radius: 6px; text-decoration: none;">📥 音声ファイルDL</a>
    </div>"""
    ]

    total_sections = (len(entries) + 9) // 10

    for i in range(0, len(entries), 10):
        section_index = i // 10 + 1
        section_title = f"セクション {section_index}/{total_sections}"
        audio_file_male = f"audio/male/batch/output_batch_{section_index}.mp3"
        audio_file_female = f"audio/female/batch/output_batch_{section_index}.mp3"

        html_parts.append(f'<div class="section">')
        html_parts.append(
            f"""
        <div class="section-header">
            <div class="section-title">{section_title}</div>
            <audio class="audio-player" controls src="{audio_file_male}" title="男性バッチ音声"></audio>
            <audio class="audio-player" controls src="{audio_file_female}" title="女性バッチ音声"></audio>
        </div>
        """
        )

        html_parts.append(
            "<table><thead><tr><th>#</th><th>単語・拼音</th><th>日本語訳</th><th>例文</th></tr></thead><tbody>"
        )

        for j, (word, jp_meaning, jyutping, example_html) in enumerate(entries[i : i + 10]):
            entry_index = i + j + 1
            word_with_jyutping = f"{word}<span class='jyutping'>{jyutping}</span>"

            word_audio_male = f"audio/male/words/word_{entry_index:03d}.mp3"
            word_audio_female = f"audio/female/words/word_{entry_index:03d}.mp3"
            example_audio_male = f"audio/male/examples/example_{entry_index:03d}.mp3"
            example_audio_female = f"audio/female/examples/example_{entry_index:03d}.mp3"

            html_parts.append(
                f"<tr>"
                f"<td>{entry_index:03d}</td>"
                f"<td><div class='audio-text'>"
                f"<div class='audio-buttons-column'>"
                f"<button class='audio-button custom-audio-button' data-src='{word_audio_male}' title='男性音声'>👨‍🦱</button>"
                f"<button class='audio-button custom-audio-button' data-src='{word_audio_female}' title='女性音声'>👩</button>"
                f"</div><div>{word_with_jyutping}</div></div></td>"
                f"<td>{jp_meaning}</td>"
                f"<td><div class='audio-text'>"
                f"<div class='audio-buttons-column'>"
                f"<button class='audio-button custom-audio-button' data-src='{example_audio_male}' title='男性音声'>👨‍🦱</button>"
                f"<button class='audio-button custom-audio-button' data-src='{example_audio_female}' title='女性音声'>👩</button>"
                f"</div><div>{example_html}</div></div></td>"
                f"</tr>"
            )


        html_parts.append("</tbody></table></div>")

    html_parts.append("</body>\n</html>")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))

    print(f"✅ HTMLを書き出しました: {output_path}")
