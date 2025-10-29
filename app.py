# main.py – VERSION SANS OS/SHUTIL/TEMPFILE (100% COMPATIBLE RENDER)
import streamlit as st
from io import StringIO
import contextlib

# === IMPORT CORE ===
try:
    import core
    from core import main as generate_palmares
except ImportError as e:
    st.error(f"Erreur import core.py : {e}")
    st.stop()

# === PAGE CONFIG ===
st.set_page_config(page_title="Podium Rezé Échecs", page_icon="♟️", layout="centered")

# === TITRE ===
st.title("Podium Rezé Échecs – Générateur de Palmarès")
st.markdown("Libre-service • PDF + TXT en 1 clic")

# === UPLOAD ===
uploaded_file = st.file_uploader("Fichier config (.txt)", type="txt")

if uploaded_file is not None:
    # === ÉCRIRE DIRECTEMENT LE FICHIER ATTENDU ===
    with open("config_rewards_champ.txt", "wb") as f:
        f.write(uploaded_file.getvalue())

    # Injecter le chemin dans core.py
    core.CONFIG_PATH = "config_rewards_champ.txt"

    if st.button("Générer le palmarès"):
        with st.spinner("Génération en cours..."):
            try:
                log_capture = StringIO()
                with contextlib.redirect_stdout(log_capture), contextlib.redirect_stderr(log_capture):
                    generate_palmares()

                logs = log_capture.getvalue()

                # === LIRE LES FICHIERS ===
                pdf_path = "palmares.pdf"
                txt_path = "palmares.txt"

                try:
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
                except FileNotFoundError:
                    st.error("Fichiers PDF/TXT non générés.")
                    with st.expander("Logs"):
                        st.text(logs or "Aucun log")

            except Exception as e:
                st.error(f"Erreur : {e}")
else:
    st.info("Upload ton fichier config pour commencer")
