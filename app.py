import streamlit as st
import subprocess
import os
import tempfile
import zipfile

# Configuración básica de la página
st.set_page_config(page_title="Convertidor Jupyter a PDF", layout="centered")

st.title("Convertidor de .ipynb a PDF 📄")
st.write("Arrastra tus archivos de Jupyter aquí y descárgalos en PDF.")

# Zona de arrastrar y soltar
archivos_subidos = st.file_uploader(
    "Selecciona o arrastra múltiples archivos .ipynb", 
    type=["ipynb"], 
    accept_multiple_files=True
)

if archivos_subidos:
    if st.button("🚀 Convertir a PDF"):
        # Usamos una carpeta temporal para no ensuciar tu ordenador
        with st.spinner("Convirtiendo... Esto puede tardar unos segundos."):
            with tempfile.TemporaryDirectory() as temp_dir:
                pdfs_generados = []
                errores = []

                for archivo in archivos_subidos:
                    # 1. Guardar el archivo subido en la carpeta temporal
                    ruta_ipynb = os.path.join(temp_dir, archivo.name)
                    with open(ruta_ipynb, "wb") as f:
                        f.write(archivo.read())

                    # 2. Ejecutar la conversión a PDF
                    try:
                        subprocess.run(
                            ["jupyter", "nbconvert", "--to", "pdf", ruta_ipynb], 
                            check=True, 
                            capture_output=True
                        )
                        # Si va bien, Jupyter crea un archivo con el mismo nombre pero .pdf
                        nombre_pdf = archivo.name.replace(".ipynb", ".pdf")
                        ruta_pdf = os.path.join(temp_dir, nombre_pdf)
                        
                        if os.path.exists(ruta_pdf):
                            pdfs_generados.append(ruta_pdf)
                            
                    except subprocess.CalledProcessError:
                        errores.append(archivo.name)

                # Mostrar resultados
                if errores:
                    st.error(f"✗ Hubo un error al convertir: {', '.join(errores)}")
                    st.warning("💡 Recuerda: Necesitas tener instalado **MiKTeX** (LaTeX) y **Pandoc** en tu Windows para que la conversión a PDF funcione.")
                
                if pdfs_generados:
                    st.success(f"✓ ¡Se han convertido {len(pdfs_generados)} archivos correctamente!")
                    
                    # 3. Preparar la descarga
                    if len(pdfs_generados) == 1:
                        # Si es solo un archivo, se descarga el PDF directo
                        with open(pdfs_generados[0], "rb") as f:
                            st.download_button(
                                label="⬇️ Descargar PDF",
                                data=f,
                                file_name=os.path.basename(pdfs_generados[0]),
                                mime="application/pdf"
                            )
                    else:
                        # Si son varios, los empaquetamos en un ZIP
                        ruta_zip = os.path.join(temp_dir, "Archivos_PDF.zip")
                        with zipfile.ZipFile(ruta_zip, "w") as zipf:
                            for pdf in pdfs_generados:
                                zipf.write(pdf, os.path.basename(pdf))
                                
                        with open(ruta_zip, "rb") as f:
                            st.download_button(
                                label="⬇️ Descargar todos los PDFs (ZIP)",
                                data=f,
                                file_name="Archivos_PDF.zip",
                                mime="application/zip"
                            )