# Open House 2025 - Gemini Audio Chat Client

## Instructions

### 1. Setup a virtual environment. (仮想環境をセットアップします。)

```bash
python3 -m venv venv

source venv/bin/activate
```

### 2. Install requirements.(必要なパッケージをインストールします。)

```bash
pip3 install -r requirements.txt
```

### 3. Create a `.env` file in the project root and set the environment variable `GEMINI_API_KEY` to your Gemini API key. (プロジェクトのルートに `.env` ファイルを作成し、環境変数 `GEMINI_API_KEY` に Gemini API キーを設定します。)

```env
GEMINI_API_KEY=<Your API key>
```

### 4. Run ```main.py```(`main.py`を実行します。)

```bash
cd app

python3 main.py
```

## How to read source code (ソースコードの読み方)

Start by reading ```utils/chataudioclient.py``` and then read ```exampleclient.py```.

(まず `utils/chataudioclient.py` を読み、次に `exampleclient.py` を読みます。)

The main application is found under the `app` folder and in the file `main.py`.
