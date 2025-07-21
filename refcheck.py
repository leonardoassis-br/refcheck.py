
# RefCheck - Verificador Inteligente de Referências (MVP com Streamlit)

import requests
import streamlit as st

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
            'link': f"https://doi.org/{doi}"
        }
    else:
        return {
            'status': 'nao_encontrado',
            'mensagem': f"DOI {doi} não encontrado na CrossRef."
        }

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
            'link': livro.get('url')
        }
    else:
        return {
            'status': 'nao_encontrado',
            'mensagem': f"ISBN {isbn} não encontrado no OpenLibrary."
        }

# Interface Streamlit
st.title("🔎 RefCheck - Verificador de Referências")

opcao = st.radio("Escolha o tipo de referência a verificar:", ["DOI", "ISBN"])

entrada = st.text_input("Digite o DOI ou ISBN:")

if st.button("Verificar"):
    if opcao == "DOI":
        resultado = buscar_por_doi(entrada.strip())
    else:
        resultado = buscar_por_isbn(entrada.strip())

    if resultado['status'] == 'confirmado':
        st.success("✅ Referência confirmada!")
        st.markdown(f"**Título:** {resultado['titulo']}")
        st.markdown(f"**Autores:** {', '.join(resultado['autores'])}")
        st.markdown(f"[Acessar referência]({resultado['link']})")
    else:
        st.error("❌ " + resultado['mensagem'])
