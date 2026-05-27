import streamlit as st
import subprocess
import os
import tempfile
import zipfile
import json
import re

st.set_page_config(page_title="Convertidor Jupyter a PDF", layout="centered")

def sanear_notebook(ruta_ipynb):
    """
    Abre el archivo Jupyter y corrige automáticamente los errores de sintaxis 
    matemática de LaTeX que hacen que nbconvert falle.
    """
    try:
        with open(ruta_ipynb, "r", encoding="utf-8") as f:
            notebook = json.load(f)
            
        def quitar_lineas_vacias(match):
            block = match.group(0)
            lines = block.split('\n')
            cleaned_lines = [l for l in lines if l.strip() != '']
            return '\n'.join(cleaned_lines)

        def arreglar_ampersands_sobrantes(match):
            block = match.group(0)
            lines = block.split('\n')
            for i, line in enumerate(lines):
                if line.count('&') > 1:
                    parts = line.split('&')
                    lines[i] = parts[0] + '&' + ' '.join(parts[1:])
            return '\n'.join(lines)

        for cell in notebook.get('cells', []):
            if cell.get('cell_type') == 'markdown':
                source = cell.get('source', [])
                text = "".join(source) if isinstance(source, list) else source
                
                # 1. Quitar líneas vacías dentro de bloques matemáticos
                text = re.sub(r'\$\$.*?\$\$', quitar_lineas_vacias, text, flags=re.DOTALL)
                text = re.sub(r'\\begin\{[a-zA-Z\*]+\}.*?\\end\{[a-zA-Z\*]+\}', quitar_lineas_vacias, text, flags=re.DOTALL)
                
                # 2. Arreglar el exceso de tabulaciones (&) en bloques de casos
                text = re.sub(r'\\begin\{cases\}.*?\\end\{cases\}', arreglar_ampersands_sobrantes, text, flags=re.DOTALL)
                
                # 3. Arreglo directo para el error específico "& \text{si} &"
                text = re.sub(r'&\s*\\text\{si\}\s*&', r'& \\text{si} ', text)
                
                # 4. NUEVO: Eliminar el anidamiento prohibido por LaTeX (ej. $$ \begin{align*} ... \end{align*} $$)
                # Extrae solo la parte del begin/end y borra los $$ o \[ \] externos
                text = re.sub(r'(?s)(?:\$\$|\\\[)\s*(\\begin\{(?:align|eqnarray|equation|gather)\*?\}.*?\\end\{(?:align|eqnarray|equation|gather)\*?\})\s*(?:\$\$|\\\])', r'\1', text)
                
                # Guardar el texto corregido en la celda
                cell['source'] = text.splitlines(True)
                
        with open(ruta_ipynb, "w", encoding="utf-8") as f:
            json.dump(notebook, f, indent=1)
            
    except Exception as e:
        pass


st.title("Convertidor de .ipynb a PDF 📄")
st.write("Arrastra tus archivos de Jupyter aquí y descárgalos en PDF.")

archivos_subidos = st.file_uploader(
    "Selecciona o arrastra múltiples archivos .ipynb", 
    type=["ipynb"], 
    accept_multiple_files=True
)

if archivos_subidos:
    if st.button("🚀 Convertir a PDF"):
        with st.spinner("Limpiando código y convirtiendo a PDF..."):
            with tempfile.TemporaryDirectory() as temp_dir:
                pdfs_generados = []
                errores = []

                for archivo in archivos_subidos:
                    ruta_ipynb = os.path.join(temp_dir, archivo.name)
                    
                    with open(ruta_ipynb, "wb") as f:
                        f.write(archivo.read())

                    sanear_notebook(ruta_ipynb)

                    try:
                        resultado = subprocess.run(
                            ["jupyter", "nbconvert", "--to", "pdf", ruta_ipynb], 
                            check=True, 
                            capture_output=True,
                            text=True
                        )
                        
                        nombre_pdf = archivo.name.replace(".ipynb", ".pdf")
                        ruta_pdf = os.path.join(temp_dir, nombre_pdf)
                        
                        if os.path.exists(ruta_pdf):
                            pdfs_generados.append(ruta_pdf)
                            
                    except subprocess.CalledProcessError as e:
                        error_real = e.stderr if e.stderr else "Error desconocido."
                        errores.append((archivo.name, error_real))

                if errores:
                    st.error("✗ Cuidado, un archivo es demasiado complejo y no pudo ser parcheado:")
                    for nombre, detalle in errores:
                        st.warning(f"**{nombre}**")
                        with st.expander("Ver error técnico completo"):
                            st.code(detalle[-1000:], language="bash")
                
                if pdfs_generados:
                    st.success(f"✓ ¡Se han procesado y convertido {len(pdfs_generados)} archivos correctamente!")
                    
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
