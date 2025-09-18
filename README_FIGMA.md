# Figma API Helper and Plugin

このフォルダには、Figmaのアートボード毎の読み取りとコンテキスト反映を支援するための2つの手段（Python CLI と Figmaプラグイン）を同梱しています。

## 概要

- Python CLI: `figma/figma_fetch.py`
  - アートボード一覧（ページ/トップレベルFrame）取得
  - 任意のnode-id配列からノードJSON取得
  - 画像URLの取得（images/image-fills）
  - ファイルメタデータ取得

- Figmaプラグイン: `figma_plugin/`
  - 選択中のオブジェクト/フレームから `node-id` を動的に取得
  - `fileKey` と `node-id` を含むJSONと cURL をクリップボードへコピー

## 事前準備

- Figma Personal Access Token を用意し、環境変数 `FIGMA_TOKEN` を設定するか、CLI引数 `--token` で渡してください。

```bash
export FIGMA_TOKEN=figd_xxxxxxxxxxxxxxxxx
```

## Python CLI の使い方

インストール（`requests` が必要）:

```bash
pip install -r requirements.txt
```

### 1) アートボード一覧（ページ/トップレベルFrame）

```bash
python3 figma/figma_fetch.py artboards --url "https://www.figma.com/file/<file_key>/<name>"
# もしくは
python3 figma/figma_fetch.py artboards --file-key <file_key>
```

出力: ページ名・ページIDと、その配下のトップレベルFrame（FRAME/COMPONENT/COMPONENT_SET）の `name` と `id` をJSONで返します。

### 2) ノードJSON取得（選択ノードのサブツリー含む）

```bash
# node-id をカンマ区切りで指定
python3 figma/figma_fetch.py nodes --file-key <file_key> --ids 1:2,3:4 --depth 1 -o nodes.json

# FigmaノードURLからnode-id抽出
python3 figma/figma_fetch.py nodes --url "https://www.figma.com/file/<file_key>/<name>?node-id=1%3A2" --depth 1
```

補足:
- `--depth` は選択ノード基準での深さ（例: `--depth 1` は選択直下の子まで）。
- ベクター情報が必要なら `--geometry paths` を付与。

### 3) ファイル全体/部分取得

```bash
# ページやトップレベルまでの構造だけ得たい場合（contextの把握）
python3 figma/figma_fetch.py file --file-key <file_key> --depth 2 -o file_top.json
```

### 4) 画像URLの取得（レンダリング）

```bash
python3 figma/figma_fetch.py images --file-key <file_key> --ids 1:2,1:3 --format png --scale 2 -o images.json
```

### 5) 画像フィルの元画像URL一覧

```bash
python3 figma/figma_fetch.py image-fills --file-key <file_key> -o fills.json
```

### 6) ファイルメタデータ

```bash
python3 figma/figma_fetch.py meta --file-key <file_key>
```

## Figmaプラグインの使い方

1. Figma で Plugins → Development → New Plugin → "Link existing plugin" を選択し、`figma_plugin/manifest.json` を選択します。
2. 任意のファイルで、抽出したいオブジェクト/フレームを選択します。
3. Plugins → Development → Node ID Extractor を実行します。
   - 選択情報（`fileKey`、`page`、`selection: [{ name, id, type, parent }]`）と、`/v1/files/:key/nodes` 用の cURL がクリップボードにコピーされます。

## 運用のヒント（アートボード毎の読み取りとコンテキスト反映）

- アートボード = ページ直下のトップレベルFrameとして扱うと設計しやすいです。
- コンテキスト反映の基本フロー:
  1) プラグインで対象アートボード/要素の `node-id` を収集
  2) CLIで `nodes` を取得（`--depth` で適切な階層まで）
  3) 取得JSON内の `name` や `styles`、`components` を基にデザイン要素や文脈（コンテンツ差し替え、注釈付与など）を適用

## 例: ブレスト（node-idを基準にデザイン要素を指定）

- HeroセクションのFrame `12:34` のみ取得して、文言と画像差し替え案を作る
  - プラグインで `12:34` を取得
  - `python3 figma/figma_fetch.py nodes --file-key <key> --ids 12:34 --depth 2`
  - JSON内の `TEXT` レイヤー名/階層に沿ってコピー改善案を列挙
  - `IMAGE` や `VECTOR` の置換案を `images` エンドポイントでレンダリングして比較

---

トークンエラーが出る場合は、`FIGMA_TOKEN` が正しいか、有効期限が切れていないかをご確認ください。HTTP 403 は無効/期限切れトークン、404 はファイルキー/権限の問題です。

