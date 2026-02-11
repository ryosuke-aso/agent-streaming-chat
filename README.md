# agent-streaming-chat

Strands Agents + FastAPI + Streamlit によるストリーミングチャットアプリ。

## 構成

| サービス | 技術 | ポート |
|----------|------|--------|
| API | FastAPI + Strands Agents (Amazon Bedrock) | 8000 |
| Frontend | Streamlit | 8501 |

## セットアップ

### 環境変数

`.env` ファイルを作成し、AWS 認証情報を設定する。

```
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### 起動

```bash
docker compose up --build
```

`http://localhost:8501` でチャット画面にアクセスできる。
