# app.py – Interface Web Streamlit (VERSION FINALE)
import streamlit as st
import os
import shutil
import tempfile
from io import StringIO
import contextlib
import sys

# === AJOUT CHEMIN CORE ===
sys.path.append(os.path.dirname(__file__))

# === IMPORT CORE ===
try:
    from core import main as generate_palmares
except ImportError as e:
    st.error(f"Erreur d'import core.py : {e}")
    st.stop()

# === PAGE CONFIG ===
st.set_page_config(
    page_title="Podium Rezé Échecs",
    page_icon="♟️",
    layout="centered"
)

# === TITRE ===
st.title("Podium Échecs – Générateur de Palmarès")
st.markdown("### Libre-service • PDF + TXT en 1 clic")

# === EXEMPLE CONFIG ===
example_config = """URLS: https://echecs.asso.fr/Resultats.aspx?URL=Tournois/Id/65456/65456&Action=Cl

CATEGORIE: Test
RANG: 1-1
PRIX: 1er Test
CONDITION: none
ORDRE: 1
"""

# === SIDEBAR ===
with st.sidebar:
    st.header("Mode d'emploi")
    st.markdown("1. Télécharge l'exemple\n2. Modifie les URLs\n3. Upload ton fichier\n4. Génère")
    st.download_button(
        label="Télécharger exemple",
        data=example_config,
        file_name="exemple.txt",
        mime="text/plain"
    )

# === UPLOAD ===
uploaded_file = st.file_uploader("Fichier config (.txt)", type="txt")

if uploaded_file is not None:
    # === FICHIER TEMPORAIRE ===
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        tmp.write(uploaded_file.getvalue())
        config_path = tmp.name

    # === COPIE VERS FICHIER ATTENDU ===
    target_config = "config_rewards_champ.txt"
    shutil.copyfile(config_path, target_config)

    # === DÉFINIR LES CHEMINS À L'AVANCE (pour finally) ===
    pdf_path = "palmares.pdf"
    txt_path = "palmares.txt"

    if st.button("Générer le palmarès"):
        with st.spinner("Génération en cours..."):
            try:
                # === CAPTURE LOGS ===
                log_capture = StringIO()
                with contextlib.redirect_stdout(log_capture), contextlib.redirect_stderr(log_capture):
                    generate_palmares()

                logs = log_capture.getvalue()

                # === VÉRIFIER FICHIERS ===
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
                # === NETTOYAGE SÉCURISÉ ===
                for f in [config_path, target_config, pdf_path, txt_path]:
                    if os.path.exists(f):
                        try:
                            os.remove(f)
                        except:
                            pass
else:
    st.info("Upload ton fichier config pour commencer")
