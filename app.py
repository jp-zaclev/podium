# app.py – VERSION 100% FONCTIONNELLE
import streamlit as st
import os
import shutil
import tempfile
from io import StringIO
import contextlib
import sys

# === AJOUT DU CHEMIN CORE ===
sys.path.append(os.path.dirname(__file__))

# === IMPORT CORE ===
try:
    from core import main as generate_palmares
except ImportError as e:
    st.error(f"Erreur import core.py : {e}")
    st.stop()

# === CONFIG PAGE ===
st.set_page_config(page_title="Podium Échecs 44", page_icon="♟️", layout="centered")

# === TITRE ===
st.title("Podium Échecs – Générateur de Palmarès")
st.markdown("Libre-service • PDF + TXT en 1 clic")

# === UPLOAD ===
uploaded_file = st.file_uploader("Fichier config (.txt)", type="txt")

if uploaded_file is not None:
    # Fichier temporaire
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        tmp.write(uploaded_file.getvalue())
        config_path = tmp.name

    # Copie vers fichier attendu
    target_config = "config_rewards_champ.txt"
    shutil.copyfile(config_path, target_config)

    # Chemins sortie
    pdf_path = "palmares.pdf"
    txt_path = "palmares.txt"

    if st.button("Générer le palmarès"):
        with st.spinner("Génération..."):
            try:
                log_capture = StringIO()
                with contextlib.redirect_stdout(log_capture), contextlib.redirect_stderr(log_capture):
                    generate_palmares()

                logs = log_capture.getvalue()

                if os.path.exists(pdf_path) and os.path.exists(txt_path):
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    with open(txt_path, "rb") as f:
                        txt_bytes = f.read()

                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button("PDF", pdf_bytes, "palmares.pdf", "application/pdf")
                    with col2:
                        st.download_button("TXT", txt_bytes, "palmares.txt", "text/plain")

                    st.success("Palmarès généré !")
                    if logs.strip():
                        with st.expander("Logs"):
                            st.text(logs)
                else:
                    st.error("Fichiers non générés.")
                    with st.expander("Logs"):
                        st.text(logs or "Aucun log")

            except Exception as e:
                st.error(f"Erreur : {e}")
            finally:
                for f in [config_path, target_config, pdf_path, txt_path]:
                    if os.path.exists(f):
                        try:
                            os.remove(f)
                        except:
                            pass
else:
    st.info("Upload ton fichier config pour commencer")
