
import requests
import streamlit as st
import re
import fitz
import docx
from io import BytesIO
from fpdf import FPDF
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

st.set_page_config(page_title="RefCheck - CGB UNESP", layout="centered")

# Leitura de arquivos
def ler_pdf(arquivo):
    texto = ""
    with fitz.open(stream=arquivo.read(), filetype="pdf") as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto

def ler_docx(arquivo):
    doc = docx.Document(arquivo)
    return "\n".join([par.text for par in doc.paragraphs])

# Extrações
def extrair_dois(texto):
    padrao = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
    return padrao.findall(texto)

def extrair_isbns(texto):
    padrao = re.compile(r"\b(?:ISBN[- ]*)?(?=\d{10,13}\b)[0-9\-]{10,17}\b")
    return [re.sub(r'[^0-9X]', '', isbn) for isbn in padrao.findall(texto)]

def extrair_titulos_autores_simples(texto):
    linhas = texto.split('\n')
    referencias = []
    for linha in linhas:
        linha = linha.strip()
        if len(linha.split()) > 4 and any(c in linha for c in ['.', ':', ';']):
            partes = re.split(r'[.:-]', linha)
            if len(partes) > 1:
                autor = partes[0].strip()
                titulo = partes[1].strip()
                referencias.append({'autor': autor, 'titulo': titulo})
    return referencias

# Verificações
def buscar_por_doi(doi):
    url = f"https://api.crossref.org/works/{doi}"
    r = requests.get(url)
    if r.status_code == 200:
        dados = r.json()
        titulo = dados['message'].get('title', [''])[0]
        return {'status': 'confirmado', 'titulo': titulo, 'fonte': 'CrossRef'}
    return {'status': 'nao_encontrado', 'fonte': 'CrossRef'}

def buscar_por_isbn(isbn):
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    r = requests.get(url)
    dados = r.json()
    if f"ISBN:{isbn}" in dados:
        titulo = dados[f"ISBN:{isbn}"].get('title', '')
        return {'status': 'confirmado', 'titulo': titulo, 'fonte': 'OpenLibrary'}
    return {'status': 'nao_encontrado', 'fonte': 'OpenLibrary'}

def buscar_por_scielo(titulo, autor):
    try:
        url = f"https://search.scielo.org/?q={titulo.replace(' ', '+')}"
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        resultados = soup.find_all("div", class_="item")
        for item in resultados:
            t = item.find("h2").text.strip()
            a = item.find("p", class_="authors").text.strip()
            if fuzz.token_set_ratio(titulo.lower(), t.lower()) > 80 and autor.lower() in a.lower():
                return {'status': 'confirmado', 'titulo': t, 'fonte': 'SciELO'}
    except:
        pass
    return {'status': 'nao_encontrado', 'fonte': 'SciELO'}

# Streamlit
st.title("🔎 RefCheck (Versão Leve) – CGB UNESP")
st.markdown("Verifique se suas referências existem em bases confiáveis como CrossRef, OpenLibrary e SciELO.")

entrada = st.radio("Como deseja inserir o conteúdo?", ["Colar texto", "Enviar arquivo"])
texto = ""

if entrada == "Colar texto":
    texto = st.text_area("Cole aqui o conteúdo")
else:
    arquivo = st.file_uploader("Envie um arquivo .txt, .pdf ou .docx", type=["txt", "pdf", "docx"])
    if arquivo:
        if arquivo.name.endswith(".txt"):
            texto = arquivo.read().decode("utf-8", errors='ignore')
        elif arquivo.name.endswith(".pdf"):
            texto = ler_pdf(arquivo)
        elif arquivo.name.endswith(".docx"):
            texto = ler_docx(arquivo)

if texto:
    dois = extrair_dois(texto)
    isbns = extrair_isbns(texto)
    titulos_autores = extrair_titulos_autores_simples(texto)

    st.markdown("### Resultados da Verificação")

    for doi in dois:
        r = buscar_por_doi(doi)
        st.write(f"🔗 DOI {doi} → {r['status'].upper()} ({r['fonte']})")

    for isbn in isbns:
        r = buscar_por_isbn(isbn)
        st.write(f"📘 ISBN {isbn} → {r['status'].upper()} ({r['fonte']})")

    for ref in titulos_autores:
        r = buscar_por_scielo(ref['titulo'], ref['autor'])
        entrada = f"{ref['autor']}: {ref['titulo']}"
        st.write(f"📝 {entrada} → {r['status'].upper()} ({r['fonte']})")
