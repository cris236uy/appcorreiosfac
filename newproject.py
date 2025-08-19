import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# Configuração da página
st.set_page_config(page_title="Automação Kaggle", layout="centered")
st.title("🤖 Automação Selenium no Kaggle")

# Escolha do modo
modo = st.radio("Escolha o modo de execução do Selenium:", ["Normal (visível)", "Headless (oculto)"])

if st.button("Executar Automação"):
    st.write("🔍 Iniciando automação no Kaggle...")

    try:
        # Configura o Chrome
        chrome_options = Options()
        if modo == "Headless (oculto)":
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")

        # Inicializa o navegador
        service = Service()
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Abre a página do Titanic no Kaggle
        driver.get("https://www.kaggle.com/c/titanic")
        time.sleep(3)

        # Pega o título da competição
        feito = driver.find_element(By.XPATH,
            '//*[@id="site-content"]/div[2]/div/div/div[2]/div[2]/div[1]/h1'
        ).text

        st.success(f"✅ Deu tudo certo! O título da competição é: **{feito}**")

        # Fecha o navegador
        driver.quit()

    except Exception as e:
        st.error(f"❌ Ocorreu um erro: {e}")
