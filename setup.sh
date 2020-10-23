mkdir -p ~/.streamlit/

echo "\
[general]
email = \"jermnelson@gmail.com\"\n\
" > ~/.streamlit/credentails.toml

echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
" > ~/.streamlit/config.toml

python -m spacy download en_core_web_sm
