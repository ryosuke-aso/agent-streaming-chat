import os
import streamlit as st
import requests


# --- Configuration ---
USER_ID="test-user"
API_ENDPOINT=os.getenv("API_ENDPOINT", "http://localhost:8000")

# Streamlit UI
st.title("Strands + Streamlit 会話アプリ")

# セッション状態の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# 既存のメッセージ履歴を読み込む
if not st.session_state.messages:
    try:
        res = requests.get(f"{API_ENDPOINT}/chats?user_id={USER_ID}")
        for msg in res.json():
            role = msg["message"]["role"]
            content = msg["message"]["content"][0].get("text", "") if msg["message"]["content"] else ""
            st.session_state.messages.append({"role": role, "content": content})
    except:
        pass

# チャット履歴の表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザー入力の受け取り
if prompt := st.chat_input("メッセージを入力してください..."):
    # ユーザーメッセージを表示
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        try:
            response = requests.post(
                f"{API_ENDPOINT}/chats",
                json={"user_id": USER_ID, "message": prompt},
                stream=True
            )
            response.raise_for_status()
            
            def stream():
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        yield chunk.decode('utf-8')
            
            full_response = st.write_stream(stream())
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            error_msg = f"エラー: {str(e)}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
