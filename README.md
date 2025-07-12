# Prepare environment
## install uv

```bash
curl -Ls https://astral.sh/uv/install.sh | bash
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```
```bash
cd wc-streamlit-form
uv venv --python=3.11
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
uv pip install -r requirements.txt
```

## install new dependencies
```bash
uv pip install python-dotenv==1.0.1
uv pip freeze > requirements.txt
```

## add a .env data with your secrets
template
```text
WC_URL=https://xxxx.com
WC_CONSUMER_KEY=ck_xxxxxxx
WC_CONSUMER_SECRET=cs_xxxxxxx

WP_USERNAME=xxxxxx
WP_APPLICATION_PASSWORD=xxxxx
```

## run the app
```bash
streamlit run app.py
```
