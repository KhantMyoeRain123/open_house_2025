# Instructions
1. Setup a virtual environment. (仮想環境をセットアップします。)
```
python3 -m venv venv

source venv/bin/activate
```
2. Install requirements.(必要なパッケージをインストールします。)

```
pip3 install -r requirements.txt
```
3. Create a `.env` file in the project root and set the environment variable `GEMINI_API_KEY` to your Gemini API key.
```
GEMINI_API_KEY=<Your API key>
```
4. Run ```exampleclient.py```(`exampleclient.py`を実行します。)

```
python3 exampleclient.py
```


# How to read source code (ソースコードの読み方)

Start by reading ```utils/chataudioclient.py``` and then read ```exampleclient.py```.

(まず `utils/chataudioclient.py` を読み、次に `exampleclient.py` を読みます。)

The main application is found under the `app` folder and in the file `main.py`.




