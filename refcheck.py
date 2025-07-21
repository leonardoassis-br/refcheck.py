
import streamlit as st
import requests
import pandas as pd
import io
from PyPDF2 import PdfReader
from docx import Document

st.set_page_config(page_title="RefCheck PRO", layout="wide")

st.title("📚 RefCheck PRO - Verificador de Referências Inteligente")

def buscar_doi(doi):
    url = f"https://api.crossref.org/works/{doi}"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        titulo = data["message"].get("title", [""])[0]
        autores = [a.get("family", "") for a in data["message"].get("author", [])]
        return "✅ Encontrado", titulo, ", ".join(autores), f"https://doi.org/{doi}"
    else:
        return "❌ Não encontrado", "", "", ""

def buscar_isbn(isbn):
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    r = requests.get(url)
    data = r.json()
    if f"ISBN:{isbn}" in data:
        livro = data[f"ISBN:{isbn}"]
        titulo = livro.get("title", "")
        autores = [a["name"] for a in livro.get("authors", [])]
        return "✅ Encontrado", titulo, ", ".join(autores), livro.get("url", "")
    else:
        return "❌ Não encontrado", "", "", ""

def extrair_texto(arquivo, tipo):
    if tipo == "txt":
        return arquivo.read().decode("utf-8")
    elif tipo == "pdf":
        reader = PdfReader(arquivo)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() + "\n"
        return texto
    elif tipo == "docx":
        doc = Document(arquivo)
        return "\n".join([p.text for p in doc.paragraphs])
    else:
        return ""

def processar_linhas(texto):
    linhas = texto.strip().split("\n")
    resultados = []
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
        if linha.startswith("10."):  # DOI
            status, titulo, autores, link = buscar_doi(linha)
            tipo = "DOI"
        elif linha.replace("-", "").isdigit() and len(linha) in [10, 13]:  # ISBN
            status, titulo, autores, link = buscar_isbn(linha)
            tipo = "ISBN"
        else:
            status, titulo, autores, link = "⚠️ Tipo desconhecido", "", "", ""
            tipo = "Outro"
        resultados.append({
            "Entrada": linha,
            "Tipo": tipo,
            "Status": status,
            "Título": titulo,
            "Autores": autores,
            "Link": link
        })
    return resultados

arquivo = st.file_uploader("📎 Envie um arquivo .txt, .pdf ou .docx com DOIs ou ISBNs:", type=["txt", "pdf", "docx"])

if arquivo:
    tipo_arquivo = arquivo.name.split(".")[-1].lower()
    conteudo = extrair_texto(arquivo, tipo_arquivo)
    with st.spinner("Verificando referências..."):
        dados = processar_linhas(conteudo)
        df = pd.DataFrame(dados)
        st.success("Verificação concluída!")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Baixar relatório CSV", csv, "relatorio_refcheck.csv", "text/csv")
else:
    st.info("Envie um arquivo para começar.")
