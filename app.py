import streamlit as st
import requests
import time
from urllib.parse import urlparse
import re

PROMPTS = """\
================================================================
WebpagePack Output File
================================================================

Purpose:
--------
This file contains a packed content of the multiple web pages' contents about a specific topic.
It is designed to be easily consumable by AI systems for analysis, summarize, or other automated processes.

File Format:
------------
The content is organized as follows:
1. This header section
2. Multiple web page entries, each consisting of:
  a. A separator line (================)
  b. The title of web page (Title: )
  c. The URL of web page (URL: )
  d. Another separator line
  e. The full text contents of the web page formatted with Markdown
  f. A blank line

Usage Guidelines:
-----------------
1. This file should be treated as read-only.
2. When processing this file, use the separators and "Title:" and "URL:" markers to distinguish contexts between different web pages in this analysis.

Notes:
------
- Some pages may have useless information such as page header, page footer, website menus and links to other pages. You should ignore these as needed.
- Binary data are not included in this packed representation.

================================================================
Web Pages Contents
================================================================
"""

SEP = "================"
OUTPUT_FILE_NAME = "webpagepack-output.txt"
SLEEP = 1


def is_valid_url(url):
    """URLが有効かどうかをチェックする"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def extract_info(text):
    """取得したWebページの内容からタイトル、URL、コンテンツを抽出する"""
    title_match = re.search(r'Title: (.+)', text)
    title = title_match.group(1) if title_match else "Title not found"

    url_match = re.search(r'URL Source: (.+)', text)
    url = url_match.group(1) if url_match else "URL not found"

    content_match = re.search(r'Markdown Content:\n([\s\S]+)$', text, re.DOTALL)
    content = content_match.group(1).strip() if content_match else "Content not found"

    return {
        "Title": title,
        "URL Source": url,
        "Markdown Content": content,
    }


def pack_output(urls_content):
    """複数のWebページの内容を1つのテキストにパックする"""
    output_text_all = PROMPTS
    for u in urls_content:
        output_text_each = f"""
{SEP}
Title: {u['Title']}
URL: {u['URL Source']}
{SEP}

{u['Markdown Content']}

"""
        output_text_all += output_text_each

    return output_text_all


def read_url(url, api_key):
    """Jina ReaderでURLのコンテンツを取得する"""
    try:
        response = requests.get(
            f"https://r.jina.ai/{url}",
            headers={
                "Authorization": f"Bearer {api_key}"
            },
            timeout=10  # タイムアウトを設定
        )
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        st.error(f"URL '{url}' の読み込み中にエラーが発生しました: {e}")
        return None


def main():
    st.title("WebpagePack-Jina")
    st.write("複数のWebページの内容をJina Readerで1つのファイルにパックしてAI処理用にします。")

    # セッション状態の初期化
    if 'packed_output' not in st.session_state:
        st.session_state.packed_output = None

    api_key = st.text_input("JinaのAPIキーを入力してください:", type="password")
    urls = st.text_area("URLを入力してください（1行に1つ）:", height=100)
    
    if st.button("URLを処理"):
        # 出力を初期化
        st.session_state.packed_output = None

        if not api_key:
            st.error("JinaのAPIキーを入力してください。")
            return

        # URLチェック
        url_list = urls.strip().split("\n")
        invalid_urls = [url for url in url_list if not is_valid_url(url.strip())]

        if invalid_urls:
            st.error("以下のURLは無効です:  \n" + "  \n".join(invalid_urls))
            return

        # スクレイピング
        urls_content = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, url in enumerate(url_list, 1):
            status_text.text(f"処理中 {i}/{len(url_list)}: {url}")
            content = read_url(url.strip(), api_key)
            if content:
                urls_content.append(extract_info(content))
            progress_bar.progress(i / len(url_list))
            time.sleep(SLEEP)

        if urls_content:
            st.session_state.packed_output = pack_output(urls_content)
            st.success("処理が完了しました。下部に結果が表示されています。")
        else:
            st.error("コンテンツを取得できませんでした。URLとAPIキーを確認してください。")

    # 処理結果の表示とダウンロードボタン
    if st.session_state.packed_output:
        st.text_area("パックされたコンテンツ", st.session_state.packed_output, height=300)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="ダウンロード",
                data=st.session_state.packed_output,
                file_name=OUTPUT_FILE_NAME,
                mime="text/plain"
            )
        
        with col2:
            st.markdown(f"合計文字数: {len(st.session_state.packed_output)}")

if __name__ == "__main__":
    main()
