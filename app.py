# app.py – Interface Web Streamlit
import streamlit as st
import os
import shutil
import tempfile
from io import StringIO
import contextlib
import sys

# Ajouter le chemin du script core
sys.path.append(os.path.dirname(__file__))

# Importer ton script principal
try:
    from core import main as generate_palmares
except ImportError as e:
    st.error(f"Erreur d'import : {e}")
    st.stop()

# === CONFIGURATION PAGE ===
st.set_page_config(
    page_title="Podium Échecs 44",
    page_icon="♟️",
    layout="centered"
)

# === TITRE ===
st.title("🏆 Podium Échecs – Générateur de Palmarès")
st.markdown("### Libre-service • PDF + TXT en 1 clic")

# === EXEMPLE DE CONFIG ===
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

# === UPLOAD FICHIER ===
uploaded_file = st.file_uploader("Choisir ton fichier config (.txt)", type="txt")

if uploaded_file is not None:
    # Sauvegarde temporaire
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        config_path = tmp_file.name

    # Copier vers le fichier attendu par core.py
    target_config = "config_rewards_champ.txt"
    shutil.copyfile(config_path, target_config)

    if st.button("🚀 Générer le palmarès"):
        with st.spinner("Scraping des tournois et génération en cours..."):
            try:
                log_capture = StringIO()
                with contextlib.redirect_stdout(log_capture):
                    with contextlib.redirect_stderr(log_capture):
                        generate_palmares()  # core.py lit config_rewards_champ.txt

                logs = log_capture.getvalue()

                # === FICHIERS GÉNÉRÉS ===
                pdf_path = "palmares.pdf"
                txt_path = "palmares.txt"

                if os.path.exists(pdf_path) and os.path.exists(txt_path):
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    with open(txt_path, "rb") as f:
                        txt_bytes = f.read()

                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📄 Télécharger PDF",
                            data=pdf_bytes,
                            file_name="palmares.pdf",
                            mime="application/pdf"
                        )
                    with col2:
                        st.download_button(
                            label="📄 Télécharger TXT",
                            data=txt_bytes,
                            file_name="palmares.txt",
                            mime="text/plain"
                        )

                    st.success("✅ Palmarès généré avec succès !")
                    if logs:
                        with st.expander("📜 Logs du traitement"):
                            st.text(logs)
                else:
                    st.error("❌ Fichiers non générés. Vérifie les logs.")
                    if logs:
                        with st.expander("Logs d'erreur"):
                            st.text(logs)

            except Exception as e:
                st.error(f"Erreur : {e}")
            finally:
                # Nettoyage sécurisé
                for f in [config_path, target_config, pdf_path, txt_path]:
                    if os.path.exists(f):
                        try:
                            os.remove(f)
                        except:
                            pass
else:
    st.info("👆 Upload ton fichier config pour commencer")
