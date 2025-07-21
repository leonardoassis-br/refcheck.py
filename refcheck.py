import requests
import streamlit as st
import re
import fitz  # PyMuPDF
import docx
from io import BytesIO
from fpdf import FPDF
from bs4 import BeautifulSoup
from scholarly import scholarly
from fuzzywuzzy import fuzz
from Bio import Entrez

Entrez.email = "leonardo@unesp.br"  # seu e-mail de identificação para PubMed

st.set_page_config(page_title="RefCheck - CGB UNESP", layout="centered")

# === Funções de extração e leitura ===

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
        if len(linha.split()) > 4 and any(c in linha for c in ['.', ':', ';']) and not linha.lower().startswith('doi'):
            partes = re.split(r'[“”\"].*?[“”\"]|[.:-]', linha)
            if len(partes) > 1:
                autor = partes[0].strip()
                titulo = partes[1].strip()
                referencias.append({'autor': autor, 'titulo': titulo})
    return referencias

def ler_pdf(arquivo):
    texto = ""
    with fitz.open(stream=arquivo.read(), filetype="pdf") as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto

def ler_docx(arquivo):
    doc = docx.Document(arquivo)
    return "\n".join([par.text for par in doc.paragraphs])

# === Funções de verificação ===

def buscar_por_doi(doi):
    url = f"https://api.crossref.org/works/{doi}"
    resposta = requests.get(url)
    if resposta.status_code == 200:
        dados = resposta.json()
        titulo = dados['message'].get('title', [''])[0]
        autores = [autor.get('family', '') for autor in dados['message'].get('author', [])]
        return {
            'status': 'confirmado',
            'titulo': titulo,
            'autores': autores,
            'link': f"https://doi.org/{doi}",
            'fonte': 'CrossRef'
        }
    return {'status': 'nao_encontrado', 'mensagem': f"DOI {doi} não encontrado", 'fonte': 'CrossRef'}

def buscar_por_isbn(isbn):
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    resposta = requests.get(url)
    dados = resposta.json()
    if f"ISBN:{isbn}" in dados:
        livro = dados[f"ISBN:{isbn}"]
        titulo = livro.get('title', '')
        autores = [autor.get('name') for autor in livro.get('authors', [])]
        return {
            'status': 'confirmado',
            'titulo': titulo,
            'autores': autores,
            'link': livro.get('url'),
            'fonte': 'OpenLibrary'
        }
    return {'status': 'nao_encontrado', 'mensagem': f"ISBN {isbn} não encontrado", 'fonte': 'OpenLibrary'}

def buscar_por_scite(doi):
    url = f"https://api.scite.ai/works/{doi}"
    resposta = requests.get(url)
    if resposta.status_code == 200:
        dados = resposta.json()
        titulo = dados.get('title', '---')
        return {
            'status': 'confirmado',
            'titulo': titulo,
            'autores': [],
            'link': f"https://scite.ai/works/{doi}",
            'fonte': 'Scite.ai'
        }
    return {'status': 'nao_encontrado', 'mensagem': f"DOI {doi} não encontrado", 'fonte': 'Scite.ai'}

def buscar_em_scielo(titulo, autor):
    try:
        url = f"https://search.scielo.org/?q={titulo.replace(' ', '+')}"
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        resultados = soup.find_all("div", class_="item")
        for item in resultados:
            t = item.find("h2").text.strip()
            a = item.find("p", class_="authors").text.strip()
            if fuzz.token_set_ratio(titulo.lower(), t.lower()) > 80 and autor.lower() in a.lower():
                return {
                    'status': 'confirmado',
                    'titulo': t,
                    'autores': a,
                    'link': item.find('a')['href'],
                    'fonte': 'SciELO'
                }
    except:
        pass
    return {'status': 'nao_encontrado', 'mensagem': f"Não encontrado na SciELO", 'fonte': 'SciELO'}

def buscar_em_pubmed(titulo, autor):
    try:
        handle = Entrez.esearch(db="pubmed", term=f"{titulo} {autor}", retmax=1)
        record = Entrez.read(handle)
        if record["IdList"]:
            pub_id = record["IdList"][0]
            resumo = Entrez.efetch(db="pubmed", id=pub_id, rettype="medline", retmode="text").read()
            return {
                'status': 'confirmado',
                'titulo': titulo,
                'autores': autor,
                'link': f"https://pubmed.ncbi.nlm.nih.gov/{pub_id}/",
                'fonte': 'PubMed'
            }
    except:
        pass
    return {'status': 'nao_encontrado', 'mensagem': f"Não encontrado no PubMed", 'fonte': 'PubMed'}

def buscar_no_scholar(titulo, autor):
    try:
        resultados = scholarly.search_pubs(titulo)
        for r in resultados:
            titulo_encontrado = r.get('bib', {}).get('title', '')
            autores_encontrados = r.get('bib', {}).get('author', '')
            if fuzz.token_set_ratio(titulo.lower(), titulo_encontrado.lower()) > 80 and autor.lower() in autores_encontrados.lower():
                return {
                    'status': 'confirmado',
                    'titulo': titulo_encontrado,
                    'autores': autores_encontrados,
                    'link': r.get('pub_url', ''),
                    'fonte': 'Google Scholar'
                }
    except:
        pass
    return {'status': 'nao_encontrado', 'mensagem': f"Não encontrado no Google Scholar", 'fonte': 'Google Scholar'}

# === Relatório PDF ===

def gerar_relatorio_pdf(resultados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Relatório de Verificação de Referências - CGB UNESP", ln=True, align='C')
    pdf.ln(10)
    for item in resultados:
        pdf.set_font("Arial", 'B', size=11)
        pdf.cell(200, 10, txt=f"{item['tipo'].upper()}: {item['entrada']}", ln=True)
        pdf.set_font("Arial", size=10)
        if item['status'] == 'confirmado':
            pdf.multi_cell(0, 10, txt=f"Fonte: {item['fonte']}\nTítulo: {item.get('titulo', '---')}\nLink: {item.get('link', '')}\n")
        else:
            pdf.cell(200, 10, txt=f"Não encontrado em {item['fonte']}", ln=True)
        pdf.ln(5)
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return BytesIO(pdf_bytes)

# === Interface ===

st.title("🔎 RefCheck - Verificador de Referências | CGB UNESP")
st.markdown("Verifique automaticamente se as referências citadas em seu texto realmente existem em fontes confiáveis e indexadas. Ideal para avaliar a credibilidade de artigos e pesquisadores.")

entrada = st.radio("Como deseja inserir o conteúdo?", ["Colar texto", "Enviar arquivo (.txt, .pdf, .docx)"])
texto = ""

if entrada == "Colar texto":
    texto = st.text_area("Cole aqui seu texto completo ou a lista de referências", height=300)
else:
    arquivo = st.file_uploader("Envie um arquivo contendo o texto ou referências", type=["txt", "pdf", "docx"])
    if arquivo:
        if arquivo.name.endswith(".txt"):
            texto = arquivo.read().decode("utf-8", errors='ignore')
        elif arquivo.name.endswith(".pdf"):
            texto = ler_pdf(arquivo)
        elif arquivo.name.endswith(".docx"):
            texto = ler_docx(arquivo)


if texto:
    st.markdown("### 🔍 Referências encontradas e em verificação...")

    # Extração automática
    dois = extrair_dois(texto)
    isbns = extrair_isbns(texto)
    refs_extras = extrair_titulos_autores_simples(texto)

    resultados = []

    # Verificar DOIs
    for doi in dois:
        resultado = buscar_por_doi(doi)
        resultado.update({"entrada": doi, "tipo": "DOI"})
        resultados.append(resultado)

        resultado_scite = buscar_por_scite(doi)
        resultado_scite.update({"entrada": doi, "tipo": "DOI"})
        resultados.append(resultado_scite)

    # Verificar ISBNs
    for isbn in isbns:
        resultado = buscar_por_isbn(isbn)
        resultado.update({"entrada": isbn, "tipo": "ISBN"})
        resultados.append(resultado)

    # Verificar títulos/autores
    for ref in refs_extras:
        titulo = ref['titulo']
        autor = ref['autor']
        entrada = f"{autor}: {titulo}"

        for buscador in [buscar_em_scielo, buscar_no_scholar, buscar_em_pubmed]:
            r = buscador(titulo, autor)
            r.update({"entrada": entrada, "tipo": "TÍTULO/AUTOR"})
            resultados.append(r)

    # Exibir resultados
    for r in resultados:
        if r['status'] == 'confirmado':
            st.success(f"✅ {r['tipo']}: {r['entrada']} ({r['fonte']})")
            st.markdown(f"- **Título encontrado:** {r.get('titulo', '---')}")
            if r.get('link'):
                st.markdown(f"- [Acessar referência]({r['link']})")
        else:
            st.warning(f"❌ {r['tipo']}: {r['entrada']} não encontrado em {r['fonte']}")

    # Gerar e baixar relatório
    if resultados:
        relatorio = gerar_relatorio_pdf(resultados)
        st.download_button("📄 Baixar Relatório PDF", data=relatorio, file_name="relatorio_refcheck.pdf", mime="application/pdf")
    else:
        st.info("Nenhuma referência foi identificada no conteúdo enviado.")

