# Open House 2025 - Gemini Audio Chat Client

## Prerequisites (前提条件)

This project requires a relatively recent version of Python. Therefore, while not mandatory, it is recommended to use `pyenv` for Python version management.
（このプロジェクトでは新しめのPythonバージョンが必要となります。従って、必須ではありませんが、`pyenv`を使用してPythonのバージョン管理を行うことを推奨します。）

### pyenv installation (pyenvのインストール)

#### macOS

```bash
brew install pyenv
```

#### WSL（Ubuntu/Debian）

```bash
curl https://pyenv.run | bash
```

After installation, add the following to your shell configuration file (e.g., `~/.bashrc`, `~/.zshrc`):
インストール後、シェルの設定ファイル（`~/.bashrc`, `~/.zshrc`など）に以下を追加：

- **.bashrcの場合：**

```bash
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - bash)"
eval "$(pyenv virtualenv-init -)"
```

- **.zshrcの場合：**

```bash
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - zsh)"
eval "$(pyenv virtualenv-init -)"
```

設定を反映：

```bash
source ~/.bashrc  # または ~/.zshrc
```

## Instructions

### 1. Install the specified Python version (指定されたPythonバージョンをインストール)

```bash
pyenv install 3.11.11
```

### 2. Verify Python version (Pythonバージョンの確認)

Check if pyenv automatically loaded the correct Python version (if you have a `.python-version` file in the project):
（プロジェクトディレクトリに移動すると、pyenvが自動的に`.python-version`ファイルを読み込み、指定されたPythonバージョンを使用します：）

```bash
cd /path/to/open_house_2025
python --version  # Python 3.11.11
```

### 3. Setup a virtual environment (仮想環境のセットアップ)

```bash
python -m venv venv

source venv/bin/activate
```

### 4. Install requirements（必要なパッケージのインストール）

```bash
pip install -r requirements.txt
```

#### For WSL environments, use the following command（WSL環境では以下のコマンドを使用）

```bash
pip install -r requirements_wsl.txt
```

### 5. Create a `.env` file in the project root and set the environment variable `GEMINI_API_KEY` to your Gemini API key. (プロジェクトのルートに `.env` ファイルを作成し、環境変数 `GEMINI_API_KEY` に Gemini API キーを設定する。)

```env
GEMINI_API_KEY=<Your API key>
```

### 6. Run `main.py`（`main.py`の実行）

```bash
cd app

python main.py
```

## How to read source code（ソースコードの読み方）

Start by reading `utils/chataudioclient.py` and then read `exampleclient.py`.

(まず `utils/chataudioclient.py` を読み、次に `exampleclient.py` を読みます。)

The main application is found under the `app` folder and in the file `main.py`.


New process!!

(Linux ver)
フォントを使うために... (to use font)
mkdir -p ~/.fonts
フォント用のフォルダを作る (make folder for font)

https://fonts.google.com/specimen/Kosugi+Maru
ここにアクセスして、ダウンロードして、.fontsにおく (access this URL. download and place in the .fonts)

.fontsで (go .fonts and do this)
fc-cache -fv
を実行


(mac ver)

https://fonts.google.com/specimen/Kosugi+Maru
ここにアクセスして、ダウンロードして、Library/Fontsにおく (access this URL. download and place in the Library/Fonts)

これをやると今設定しているフォントが使えるようになるはず
