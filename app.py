import streamlit as st
import subprocess
import os
import tempfile
import zipfile

st.set_page_config(page_title="Convertidor Jupyter a PDF", layout="centered")

st.title("Convertidor de .ipynb a PDF 📄")
st.write("Arrastra tus archivos de Jupyter aquí y descárgalos en PDF.")

archivos_subidos = st.file_uploader(
    "Selecciona o arrastra múltiples archivos .ipynb", 
    type=["ipynb"], 
    accept_multiple_files=True
)

if archivos_subidos:
    if st.button("🚀 Convertir a PDF"):
        with st.spinner("Convirtiendo... Esto puede tardar unos segundos."):
            with tempfile.TemporaryDirectory() as temp_dir:
                pdfs_generados = []
                errores = []

                for archivo in archivos_subidos:
                    ruta_ipynb = os.path.join(temp_dir, archivo.name)
                    with open(ruta_ipynb, "wb") as f:
                        f.write(archivo.read())

                    try:
                        # Ejecutar la conversión
                        resultado = subprocess.run(
                            ["jupyter", "nbconvert", "--to", "pdf", ruta_ipynb], 
                            check=True, 
                            capture_output=True,
                            text=True # Permite leer el error como texto
                        )
                        
                        nombre_pdf = archivo.name.replace(".ipynb", ".pdf")
                        ruta_pdf = os.path.join(temp_dir, nombre_pdf)
                        
                        if os.path.exists(ruta_pdf):
                            pdfs_generados.append(ruta_pdf)
                            
                    except subprocess.CalledProcessError as e:
                        # ¡AQUÍ ESTÁ LA MAGIA! Capturamos el error real de la consola
                        error_real = e.stderr if e.stderr else "Error desconocido de Jupyter"
                        errores.append((archivo.name, error_real))

                # Mostrar errores detallados si los hay
                if errores:
                    st.error("✗ Hubo problemas con algunos archivos:")
                    for nombre, detalle in errores:
                        st.warning(f"**{nombre}** falló. Detalle del sistema:")
                        # Mostramos el error técnico en un bloque de código
                        st.code(detalle[-1000:], language="bash") # Mostramos los últimos 1000 caracteres
                
                # Mostrar PDFs exitosos
                if pdfs_generados:
                    st.success(f"✓ ¡Se han convertido {len(pdfs_generados)} archivos correctamente!")
                    
                    if len(pdfs_generados) == 1:
                        with open(pdfs_generados[0], "rb") as f:
                            st.download_button(
                                label="⬇️ Descargar PDF",
                                data=f,
                                file_name=os.path.basename(pdfs_generados[0]),
                                mime="application/pdf"
                            )
                    else:
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
