
import streamlit as st
import requests
import pandas as pd
import time
from difflib import SequenceMatcher
from docx import Document
from PyPDF2 import PdfReader
from scholarly import scholarly  # Google Scholar
from urllib.parse import quote

st.set_page_config(page_title="RefCheck MultiFonte", layout="wide")
st.title("📚 RefCheck – Verificador de Referências com Múltiplas Fontes")


# --- Funções de busca em várias fontes ---

import bs4

def buscar_scite_por_titulo(titulo, scite_key):
    try:
        headers = {"x-api-key": scite_key}
        r = requests.get(f"https://api.scite.ai/search?q={quote(titulo)}", headers=headers, timeout=10)
        if r.status_code == 200 and r.json()["results"]:
            item = r.json()["results"][0]
            return "✅ Encontrado", "Scite.ai", item.get("title", ""), ", ".join(item.get("authors", [])), f"https://scite.ai/papers/{item.get('id', '')}"
    except:
        pass
    return "❌ Não encontrado", "", "", "", ""

def buscar_scielo_por_titulo(titulo):
    try:
        r = requests.get(f"https://search.scielo.org/?q={quote(titulo)}&lang=pt", timeout=10)
        soup = bs4.BeautifulSoup(r.text, "html.parser")
        results = soup.select(".item .title")
        for item in results:
            texto = item.get_text(strip=True)
            if similaridade(titulo, texto) > 0.8:
                link = item.find_parent("a")["href"]
                return "✅ Encontrado", "SciELO", texto, "", link
    except:
        pass
    return "❌ Não encontrado", "", "", "", ""


def buscar_crossref(doi):
    try:
        r = requests.get(f"https://api.crossref.org/works/{doi}", timeout=10)
        if r.status_code == 200:
            d = r.json()["message"]
            return "✅ Encontrado", "CrossRef", d.get("title", [""])[0], ", ".join(a.get("family", "") for a in d.get("author", [])), f"https://doi.org/{doi}"
    except:
        pass
    return "❌ Não encontrado", "", "", "", ""

def buscar_openlibrary(isbn):
    try:
        r = requests.get(f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data", timeout=10)
        d = r.json()
        if f"ISBN:{isbn}" in d:
            l = d[f"ISBN:{isbn}"]
            return "✅ Encontrado", "OpenLibrary", l.get("title", ""), ", ".join(a["name"] for a in l.get("authors", [])), l.get("url", "")
    except:
        pass
    return "❌ Não encontrado", "", "", "", ""

def buscar_pubmed_por_titulo(titulo):
    try:
        base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        search = requests.get(f"{base}esearch.fcgi?db=pubmed&term={quote(titulo)}&retmode=json", timeout=10).json()
        ids = search.get("esearchresult", {}).get("idlist", [])
        if ids:
            id = ids[0]
            fetch = requests.get(f"{base}esummary.fcgi?db=pubmed&id={id}&retmode=json", timeout=10).json()
            rec = fetch["result"][id]
            return "✅ Encontrado", "PubMed", rec["title"], rec.get("source", ""), f"https://pubmed.ncbi.nlm.nih.gov/{id}"
    except:
        pass
    return "❌ Não encontrado", "", "", "", ""

def buscar_scholar_por_titulo(titulo):
    try:
        resultado = next(scholarly.search_pubs(titulo), None)
        if resultado:
            return "✅ Encontrado", "Google Scholar", resultado.get("bib", {}).get("title", ""), resultado.get("bib", {}).get("author", ""), resultado.get("pub_url", "")
    except:
        pass
    return "❌ Não encontrado", "", "", "", ""

# Função central

def verificar_referencia(entrada, scite_api_key=""):
    entrada = entrada.strip()
    if entrada.startswith("10."):
        return (entrada,) + buscar_crossref(entrada)
    elif entrada.replace("-", "").isdigit() and len(entrada) in [10, 13]:
        return (entrada,) + buscar_openlibrary(entrada)

    fontes = [
        lambda t: buscar_pubmed_por_titulo(t),
        lambda t: buscar_scholar_por_titulo(t),
        lambda t: buscar_scielo_por_titulo(t),
        lambda t: buscar_scite_por_titulo(t, scite_api_key)
    ]
    for fonte in fontes:
        status, origem, titulo, autor, link = fonte(entrada)
        if status.startswith("✅"):
            return (entrada, status, origem, titulo, autor, link)
    return (entrada, "❌ Não encontrado", "", "", "", "")

    entrada = entrada.strip()
    if entrada.startswith("10."):
        return (entrada,) + buscar_crossref(entrada)
    elif entrada.replace("-", "").isdigit() and len(entrada) in [10, 13]:
        return (entrada,) + buscar_openlibrary(entrada)
    
else:
        fontes = [
            lambda t: buscar_pubmed_por_titulo(t),
            lambda t: buscar_scholar_por_titulo(t),
            lambda t: buscar_scielo_por_titulo(t),
            lambda t: buscar_scite_por_titulo(t, scite_api_key)
        ]
        for fonte in fontes:

            status, origem, titulo, autor, link = fonte(entrada)
            if status.startswith("✅"):
                return (entrada, status, origem, titulo, autor, link)
        return (entrada, "❌ Não encontrado", "", "", "", "")

# Extração de texto
def extrair_texto(arquivo, tipo):
    if tipo == "txt":
        return arquivo.read().decode("utf-8")
    elif tipo == "pdf":
        reader = PdfReader(arquivo)
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    elif tipo == "docx":
        doc = Document(arquivo)
        return "\n".join(p.text for p in doc.paragraphs)
    return ""

# Upload e processamento

scite_api_key = st.text_input("🔑 API Key do Scite.ai (opcional, mas necessário para usar)", type="password")
arquivo = st.file_uploader("📎 Envie um arquivo .txt, .pdf ou .docx com referências:", type=["txt", "pdf", "docx"])


if arquivo:
    tipo = arquivo.name.split(".")[-1].lower()
    texto = extrair_texto(arquivo, tipo)
    linhas = texto.strip().split("\n")

    resultados = []
    progresso = st.progress(0)

    for i, linha in enumerate(linhas):
        if not linha.strip():
            continue
        resultado = verificar_referencia(linha)
        if resultado[1] == "✅ Encontrado":
            resultados.append(resultado)
        progresso.progress((i + 1) / len(linhas))
        time.sleep(0.1)

    progresso.empty()

    if resultados:
        df = pd.DataFrame(resultados, columns=["Entrada", "Status", "Fonte", "Título", "Autores", "Link"])
        st.success("✅ Referências encontradas:")
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Baixar CSV", csv, "referencias_encontradas.csv", "text/csv")
    else:
        st.warning("Nenhuma referência encontrada nas fontes verificadas.")
else:
    st.info("Envie um arquivo para começar.")
