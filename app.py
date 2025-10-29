# main.py – VERSION FINALE AVEC SIDEBAR (100% COMPATIBLE RENDER)
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
st.title("Podium Échecs – Générateur de Palmarès")
st.markdown("Libre-service • PDF + TXT en 1 clic")

# === EXEMPLE CONFIG ===
example_config = """URLS: https://echecs.asso.fr/Resultats.aspx?URL=Tournois/Id/65456/65456&Action=Cl

CATEGORIE: Podium Petits Poussins
RANG: 1-3
PRIX: 1er Petit Poussin|2ème Petit Poussin|3ème Petit Poussin
CONDITION: category == "ppo"
ORDRE: 1

CATEGORIE: Podium Petites Poussines
RANG: 1-3
PRIX: 1er Petite Poussine|2ème Petite Poussine|3ème Petite Poussine
CONDITION: category == "ppo" et genre == "f"
ORDRE: 2

CATEGORIE: Meilleure féminine
RANG: best
PRIX: Coupe Féminine
CONDITION: genre == "f"
ORDRE: 3
"""

# === SIDEBAR ===
with st.sidebar:
    st.header("📋 Mode d'emploi")
    st.markdown("""
    1. **Télécharge** l'exemple ci-dessous  
    2. **Modifie** les URLs et catégories  
    3. **Upload** ton fichier `.txt`  
    4. **Clique** sur Générer  
    """)
    st.download_button(
        label="📥 Télécharger exemple config",
        data=example_config,
        file_name="exemple_config.txt",
        mime="text/plain"
    )

# === UPLOAD ===
uploaded_file = st.file_uploader("Fichier config (.txt)", type="txt")

if uploaded_file is not None:
    # === ÉCRITURE DIRECTE ===
    with open("config_rewards_champ.txt", "wb") as f:
        f.write(uploaded_file.getvalue())

    # Injecter le chemin
    core.CONFIG_PATH = "config_rewards_champ.txt"

    if st.button("Générer le palmarès"):
        with st.spinner("Génération en cours..."):
            try:
                log_capture = StringIO()
                with contextlib.redirect_stdout(log_capture), contextlib.redirect_stderr(log_capture):
                    generate_palmares()

                logs = log_capture.getvalue()

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
                    st.error("Fichiers non générés.")
                    with st.expander("Logs"):
                        st.text(logs or "Aucun log")

            except Exception as e:
                st.error(f"Erreur : {e}")
else:
    st.info("Upload ton fichier config pour commencer")
