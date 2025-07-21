# RefCheck - CGB UNESP

Este é o RefCheck - Verificador de Referências, criado para analisar a credibilidade de textos e artigos acadêmicos com base na existência real das obras citadas.

## Funcionalidades:
- Verificação por DOI (CrossRef)
- Verificação por ISBN (OpenLibrary)
- Verificação por título/autor (SciELO)
- Suporte a arquivos .txt, .pdf e .docx
- Interface visual clara para o usuário final

## Como rodar localmente:
```bash
pip install -r requirements.txt
streamlit run refcheck.py
```

## Como publicar no Streamlit Cloud:
1. Suba este código para um repositório público no GitHub
2. Vá em https://streamlit.io/cloud
3. Clique em "New app" e selecione o repositório
