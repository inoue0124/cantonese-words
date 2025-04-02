import os
import re
from pycantonese import characters_to_jyutping

input_path = "output_file.txt"
output_path = "index.html"


def remove_english_from_japanese(text):
    return re.sub(r'[（(][a-zA-Z0-9\s　.,;:/!?\-\'"()&【】]+[)）]', "", text).strip()


def convert_sentence_with_jyutping(sentence):
    result = ""
    for char, jyut in characters_to_jyutping(sentence):
        if jyut:
            result += (
                f"<span class='char-with-rt'>"
                f"<span class='base-char'>{char}</span>"
                f"<span class='under-rt'>{jyut}</span>"
                f"</span>"
            )
        else:
            result += f"<span class='char-with-rt'>"
            result += f"<span class='base-char'>{char}</span>"
            result += f"<span class='under-rt'>&nbsp;</span>"
            result += f"</span>"
    return result


def extract_word_and_example(cols):
    word = re.sub(r"[（(][^）)]+[)）]", "", cols[0]).strip()
    jp_meaning = remove_english_from_japanese(cols[1])
    jyutping = cols[2].strip()
    example = cols[3].strip()

    match = re.search(r"(.*?)[（(](.*?)[)）]?$", example)
    chinese_part = match.group(1).strip() if match else example
    jp_translation = match.group(2).strip() if match and match.group(2) else ""

    chinese_part_with_jyutping = convert_sentence_with_jyutping(chinese_part)

    example_html = (
        f"{chinese_part_with_jyutping}<br>{jp_translation}"
        if jp_translation
        else chinese_part_with_jyutping
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
<html lang=\"ja\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>広東語 単語リスト</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #f9fafb; margin: 2rem; color: #111; }
        .section { margin-bottom: 3rem; }
        .section-title { font-size: 1.2rem; font-weight: bold; margin-bottom: 1rem; color: #555; }
        table { width: 100%; border-collapse: collapse; background: #fff; box-shadow: 0 2px 6px rgba(0,0,0,0.06); border-radius: 8px; overflow: hidden; table-layout: fixed; }
        th, td {
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #eee;
            text-align: left;
            vertical-align: middle;
        }
        th:first-child, td:first-child {
            width: 180px;
            font-weight: bold;
            color: #e11d48;
            white-space: nowrap;
            font-size: 1.5rem;
            line-height: 1.2;
        }
        td:nth-child(2) { color: #555; }
        td:nth-child(3) {
            width: 50%;
            color: #333;
            font-size: 1.1rem;
            line-height: 1.6;
        }
        .jyutping {
            font-size: 0.9rem;
            color: #e11d48;
            display: block;
            margin-top: 0.2rem;
        }
        .audio-player { margin-bottom: 1rem; }
        .search-bar { margin-bottom: 2rem; width: 100%; }
        input[type=\"text\"] { padding: 16px; width: -webkit-fill-available; border: 0.5px solid #ccc; border-radius: 6px; font-size: 1.2rem; }
        .section-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        ruby { ruby-position: over; }
        rt {
            font-size: 0.7em;
            line-height: 1.4;
            padding-top: 2px;
            color: #666;
            font-weight: normal;
        }
        .char-with-rt {
            display: inline-block;
            text-align: center;
            margin: 0 1px;
        }
        .base-char { display: block; font-size: 1.1rem; }
        .under-rt { display: block; font-size: 0.7rem; color: #666; margin-top: 2px; }
        .plain-char { display: inline-block; font-size: 1.1rem; margin: 0 1px; }
    </style>
    <script>
        function filterEntries() {
            const keyword = document.getElementById(\"search\").value.toLowerCase();
            const sections = document.querySelectorAll(\".section\");
            sections.forEach(section => {
                const rows = section.querySelectorAll(\"tbody tr\");
                let visibleCount = 0;
                rows.forEach(row => {
                    const text = row.innerText.toLowerCase();
                    const match = text.includes(keyword);
                    row.style.display = match ? \"\" : \"none\";
                    if (match) visibleCount++;
                });
                section.style.display = visibleCount > 0 ? \"\" : \"none\";
            });
        }
        function playAllAudios() {
            const players = Array.from(document.querySelectorAll(\".audio-player\"));
            if (players.length === 0) return;
            let current = 0;
            const playNext = () => {
                if (current < players.length) {
                    const player = players[current];
                    player.currentTime = 0;
                    player.play();
                    player.onended = () => {
                        current++;
                        playNext();
                    };
                }
            };
            playNext();
        }
    </script>
</head>
<body>
    <div class=\"search-bar\">
        <input type=\"text\" id=\"search\" oninput=\"filterEntries()\" placeholder=\"単語・読み・意味・例文で検索...\">
    </div>
    <div style=\"margin-bottom: 1rem;\">
        <button onclick=\"playAllAudios()\" style=\"padding: 10px 20px; font-size: 1rem;\">🔊 連続再生</button>
    </div>"""
    ]

    for i in range(0, len(entries), 10):
        section_title = f"Audio #{i // 10 + 1}"
        audio_file = f"audio/output_batch_{(i) // 10 + 1}.mp3"
        html_parts.append(f'<div class="section">')
        html_parts.append(
            f"""
    <div class="section-header">
        <div class="section-title">{section_title}</div>
        <audio class="audio-player" controls src="{audio_file}" data-index="{i // 10}"></audio>
    </div>
    """
        )
        html_parts.append(
            "<table><thead><tr><th>単語・拼音</th><th>日本語訳</th><th>例文</th></tr></thead><tbody>"
        )

        for word, jp_meaning, jyutping, example_html in entries[i : i + 10]:
            word_with_jyutping = f"{word}<span class='jyutping'>{jyutping}</span>"
            html_parts.append(
                f"<tr><td>{word_with_jyutping}</td><td>{jp_meaning}</td><td>{example_html}</td></tr>"
            )
        html_parts.append("</tbody></table></div>")

    html_parts.append("</body>\n</html>")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))

    print(f"✅ HTMLを書き出しました: {output_path}")
