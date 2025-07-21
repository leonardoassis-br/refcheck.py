
import streamlit as st
import requests
import pandas as pd
import time
from difflib import SequenceMatcher

st.set_page_config(page_title="RefCheck Avançado", layout="wide")
st.title("📚 RefCheck Avançado – Verificador de Referências com Fontes Múltiplas")

# --- Funções de busca simplificadas (em breve: SciELO, Scite.ai, PubMed, Google Scholar via scholarly) ---

def buscar_crossref_por_doi(doi):
    url = f"https://api.crossref.org/works/{doi}"
    r = requests.get(url)
    if r.status_code == 200:
        d = r.json()["message"]
        return True, d.get("title", [""])[0], ", ".join(a.get("family", "") for a in d.get("author", [])), f"https://doi.org/{doi}"
    return False, "", "", ""

def buscar_openlibrary_por_isbn(isbn):
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    r = requests.get(url)
    d = r.json()
    if f"ISBN:{isbn}" in d:
        livro = d[f"ISBN:{isbn}"]
        return True, livro.get("title", ""), ", ".join(a["name"] for a in livro.get("authors", [])), livro.get("url", "")
    return False, "", "", ""

def similaridade(t1, t2):
    return SequenceMatcher(None, t1.lower(), t2.lower()).ratio()

def simular_busca_por_titulo(titulo):
    # Simulação para placeholder (futuro: scholarly, scielo, pubmed, scite.ai)
    titulos_fake = ["A biblioteca pública no século XXI", "Inteligência artificial e ciência da informação"]
    for tf in titulos_fake:
        if similaridade(titulo, tf) > 0.8:
            return True, tf, "Autor Exemplo", "https://exemplo.org"
    return False, "", "", ""

# --- Lógica principal ---

def verificar_referencia(entrada):
    entrada = entrada.strip()
    if entrada.startswith("10."):  # DOI
        ok, titulo, autor, link = buscar_crossref_por_doi(entrada)
        return entrada, "DOI", "✅ Encontrado" if ok else "❌ Não encontrado", titulo, autor, link
    elif entrada.replace("-", "").isdigit() and len(entrada) in [10, 13]:  # ISBN
        ok, titulo, autor, link = buscar_openlibrary_por_isbn(entrada)
        return entrada, "ISBN", "✅ Encontrado" if ok else "❌ Não encontrado", titulo, autor, link
    else:
        ok, titulo, autor, link = simular_busca_por_titulo(entrada)
        return entrada, "Título", "✅ Encontrado" if ok else "❌ Não encontrado", titulo, autor, link

# --- Upload e processamento ---


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

arquivo = st.file_uploader("📎 Envie um arquivo .txt, .pdf ou .docx com DOIs, ISBNs ou títulos (um por linha):", type=["txt", "pdf", "docx"])


if arquivo:
    linhas = arquivo.read().decode("utf-8").strip().split("\n")
    resultados = []

    progresso = st.progress(0)
    total = len(linhas)

    for i, linha in enumerate(linhas):
        resultado = verificar_referencia(linha)
        resultados.append(resultado)
        progresso.progress((i + 1) / total)
        time.sleep(0.2)

    progresso.empty()

    df = pd.DataFrame(resultados, columns=["Entrada", "Tipo", "Status", "Título", "Autores", "Link"])
    st.success("✅ Verificação concluída")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Baixar relatório CSV", csv, "relatorio_refcheck_avancado.csv", "text/csv")
else:
    st.info("Envie um arquivo contendo as referências.")
