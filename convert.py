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

    html_parts = ["""<!DOCTYPE html>
    <html lang="ja">
    <head>
    <meta charset="UTF-8">
    <title>広東語 単語リスト</title>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap">
    <style>
    body { font-family: 'Segoe UI', sans-serif; background-color: #f9fafb; margin: 2rem; color: #111; }
    .page-header { background: #fff; border: 1px solid #eee; border-radius: 10px; padding: 1.5rem; box-shadow: 0 2px 5px rgba(0,0,0,0.04); }
    .page-header h2 { font-size: 1.4rem; color: #333; margin-bottom: 1rem; }
    .page-header ul { margin-bottom: 1rem; color: #444; }
    .search-bar { padding: 0.5rem 0; margin: 0 auto 1.5rem auto; }
    .sticky-search { position: sticky; top: 0; background-color: #f9fafb; z-index: 100; }
    input[type="text"] { padding: 16px; width: -webkit-fill-available; border: 0.5px solid #ccc; border-radius: 6px; font-size: 1.2rem; }
    .section { margin-bottom: 3rem; }
    .section-title { font-size: 1.2rem; font-weight: bold; margin-bottom: 1rem; color: #555; }
    .section-header { padding-bottom: 1rem; margin-bottom: 1rem; border-bottom: 1px solid #ddd; }
    .section-controls { margin: 1.2rem 0; }
    .control-button { background-color: #f9fafb; border: 1px solid #ccc; border-radius: 6px; padding: 6px 12px; margin-right: 0.5rem; font-size: 0.95rem; display: inline-flex; align-items: center; gap: 0.4rem; cursor: pointer; transition: background 0.2s; text-decoration: none; color: #111; }
    .control-button:hover { background-color: #e5e7eb; }
    table { width: 100%; border-collapse: collapse; background: #fff; box-shadow: 0 2px 6px rgba(0,0,0,0.06); border-radius: 8px; overflow: hidden; }
    th, td { padding: 1.2rem 1rem; border-bottom: 1px solid #eee; text-align: left; vertical-align: middle; }
    td:nth-child(2) { font-weight: bold; color: #e11d48; font-size: 1.5rem; white-space: nowrap; }
    td:nth-child(4) { width: 50%; }
    .jyutping { font-size: 0.8rem; color: #e11d48; display: block; margin-top: 0.2rem; }
    .jyutping-line { font-size: 0.8rem; color: #666; margin-top: 0.2rem; letter-spacing: 1px; }
    .translation { margin-top: 0.3rem; font-size: 1rem; color: #333; }
    .example-block { display: flex; flex-direction: column; gap: 0.4rem; }
    .audio-button { cursor: pointer; background: none; border: none; font-size: 1.2rem; color: #e11d48; transition: transform 0.2s; padding-left: 0; }
    .audio-button:hover { transform: scale(1.2); }
    .hidden-cell { opacity: 0; pointer-events: auto; }
    .toggle-word, .toggle-meaning, .toggle-jyutping { cursor: pointer; }
    .seg-button {
    background: #f3f4f6;
    border: 1px solid #ccc;
    padding: 0.4rem 1rem;
    font-size: 0.9rem;
    cursor: pointer;
    outline: none;
    transition: background 0.2s;
    border-right: none;
    }
    .seg-button:last-child {
    border-right: 1px solid #ccc;
    border-radius: 0 6px 6px 0;
    }
    .seg-button:first-child {
    border-radius: 6px 0 0 6px;
    }
    .seg-button.active {
    background: #e11d48;
    color: white;
    font-weight: bold;
    }
    .seg-button:hover {
    background: #e5e7eb;
    }
    .seg-button.active:hover {
    background: #e11d48;
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
    function toggleSectionVisibility(button, className) {
        const section = button.closest('.section');
        const targets = section.querySelectorAll('.toggle-' + className + ', .' + className);
        if (targets.length === 0) return;

        // 1つでも非表示があれば「表示」、全て表示中なら「非表示」に切り替える
        const shouldHide = !Array.from(targets).some(el => el.classList.contains("hidden-cell"));

        targets.forEach(el => {
            if (shouldHide) {
                el.classList.add("hidden-cell");
            } else {
                el.classList.remove("hidden-cell");
            }
        });
    }
    function toggleSelf(el) {
        el.classList.toggle("hidden-cell");
    }
    function saveCheckboxState() {
        const checkboxes = document.querySelectorAll(".check-word");
        const checkedStates = {};
        checkboxes.forEach(cb => {
            checkedStates[cb.dataset.index] = cb.checked;
        });
        localStorage.setItem("wordChecks", JSON.stringify(checkedStates));
    }
    function loadCheckboxState() {
        const data = localStorage.getItem("wordChecks");
        if (!data) return;
        const checkedStates = JSON.parse(data);
        document.querySelectorAll(".check-word").forEach(cb => {
            if (checkedStates[cb.dataset.index]) {
                cb.checked = true;
            }
        });
    }
    function clearAllChecks(confirmAll = false, section = null) {
        if (confirmAll) {
            if (!confirm("すべてのチェックを解除しますか？")) return;
        }
        const selector = section ? section.querySelectorAll(".check-word") : document.querySelectorAll(".check-word");
        selector.forEach(cb => cb.checked = false);
        saveCheckboxState();
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
    function filterByCheck(type, buttonEl) {
        const rows = document.querySelectorAll("tbody tr");
        rows.forEach(row => {
            const checkbox = row.querySelector(".check-word");
            if (!checkbox) return;

            if (type === 'checked' && checkbox.checked) {
                row.style.display = "";
            } else if (type === 'unchecked' && !checkbox.checked) {
                row.style.display = "";
            } else if (type === 'all') {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        });
                  
        document.querySelectorAll(".seg-button").forEach(btn => btn.classList.remove("active"));
        if (buttonEl) buttonEl.classList.add("active");
    };
    document.addEventListener("DOMContentLoaded", () => {
        loadCheckboxState();
        document.querySelectorAll(".check-word").forEach(cb => {
            cb.addEventListener("change", saveCheckboxState);
        });
    });
    </script>
    </head>
    <body>
    <div class="page-header">
        <h2>このページの使い方</h2>                  
        <div>📘 単語表示切替ボタンで単語表示をまとめて切り替え</div>
        <div>🈶 日本語訳表示切替ボタンで訳の表示をまとめて切り替え</div>
        <div style="margin-bottom: 1.2rem;">✔ チェックボックスで「覚えた単語」を管理（保存されます）</div>
        <a href="download/audio.zip" download class="control-button">📥 音声ダウンロード</a>
        <button class="control-button" onclick="clearAllChecks(true)">☑ 全チェック解除</button>
        <div class="segmented-control" style="display: inline-flex; gap: 0; margin-bottom: 1.5rem;">
        <button class="seg-button active" onclick="filterByCheck('all', this)">🔄 すべて</button>
        <button class="seg-button" onclick="filterByCheck('checked', this)">✔ あり</button>
        <button class="seg-button" onclick="filterByCheck('unchecked', this)">✔ なし</button>
        </div>
    </div>
    </div>
    <div class="search-bar sticky-search">
        <input type="text" id="search" oninput="filterEntries()" placeholder="単語・読み・意味・例文で検索...">
    </div>
    """]

    # ========== セクション出力 ==========
    total_sections = (len(entries) + 9) // 10

    for i in range(0, len(entries), 10):
        section_index = i // 10 + 1
        section_title = f"セクション {section_index}/{total_sections}"
        audio_file_male = f"audio/male/batch/output_batch_{section_index}.mp3"
        audio_file_female = f"audio/female/batch/output_batch_{section_index}.mp3"

        html_parts.append(
            f'<div class="section">'
            f'<div class="section-header"><div class="section-title">{section_title}</div>'
            f'<audio class="audio-player" controls src="{audio_file_male}" title="男性バッチ音声"></audio>'
            f'<audio class="audio-player" controls src="{audio_file_female}" title="女性バッチ音声"></audio></div>'
            f'<div class="section-controls">'
            f'<button class="control-button" onclick="toggleSectionVisibility(this, \'word\')">📘 単語切替</button>'
            f'<button class="control-button" onclick="toggleSectionVisibility(this, \'jyutping\')">🈺 拼音切替</button>'
            f'<button class="control-button" onclick="toggleSectionVisibility(this, \'meaning\')">🈶 日本語訳切替</button>'
            f'<button class="control-button" onclick="clearAllChecks(false, this.closest(\'.section\'))">☑ セクションチェック解除</button>'
            f'</div>'
            f'<table><thead><tr>'
            f'<th style="width:4rem;">#</th><th>単語・拼音</th><th>日本語訳</th><th>例文</th>'
            f'</tr></thead><tbody>'
        )

        for j, (word, jp_meaning, jyutping, example_html) in enumerate(entries[i:i+10]):
            entry_index = i + j + 1
            word_with_jyutping = f"<span class='toggle-word' onclick='toggleSelf(this)'>{word}</span><span class='jyutping toggle-jyutping' onclick='toggleSelf(this)'>{jyutping}</span>"
            word_audio_male = f"audio/male/words/word_{entry_index:03d}.mp3"
            word_audio_female = f"audio/female/words/word_{entry_index:03d}.mp3"
            example_audio_male = f"audio/male/examples/example_{entry_index:03d}.mp3"
            example_audio_female = f"audio/female/examples/example_{entry_index:03d}.mp3"

            html_parts.append(
                f"<tr>"
                f"<td><div style='display:flex; align-items:center; gap:0.5rem;'>"
                f"<input type='checkbox' class='check-word' data-index='{entry_index:03d}'>"
                f"<span>{entry_index:03d}</span></div></td>"
                f"<td><div class='audio-text'><div class='audio-buttons-column'>"
                f"<button class='audio-button custom-audio-button' data-src='{word_audio_male}'>👨‍🦱</button>"
                f"<button class='audio-button custom-audio-button' data-src='{word_audio_female}'>👩</button></div>"
                f"<div>{word_with_jyutping}</div></div></td>"
                f"<td><div class='toggle-meaning' onclick='toggleSelf(this)'>{jp_meaning}</div></td>"
                f"<td><div class='audio-text'><div class='audio-buttons-column'>"
                f"<button class='audio-button custom-audio-button' data-src='{example_audio_male}'>👨‍🦱</button>"
                f"<button class='audio-button custom-audio-button' data-src='{example_audio_female}'>👩</button></div>"
                f"<div class='example-block'>{example_html}</div></div></td></tr>"
            )

        html_parts.append("</tbody></table>")
        html_parts.append(
            f'<div class="section-controls">'
            f'<button class="control-button" onclick="toggleSectionVisibility(this, \'word\')">📘 単語切替</button>'
            f'<button class="control-button" onclick="toggleSectionVisibility(this, \'meaning\')">🈶 日本語訳切替</button>'
            f'<button class="control-button" onclick="clearAllChecks(false, this.closest(\'.section\'))">☑ セクションチェック解除</button>'
            f'</div>'
            f'</div>'
        )

    # 終了
    html_parts.append("</body></html>")

    # 書き出し
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))

    print(f"✅ HTMLを書き出しました: {output_path}")
