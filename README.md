# RefCheck - CGB UNESP

Este projeto permite verificar automaticamente se as referências citadas em um texto ou lista (em .txt, .pdf, .docx ou colado manualmente) existem de fato, com base nas principais bases de dados científicas.

## Funcionalidades:
- Extração automática de DOI, ISBN, título e autor
- Verificação em:
  - CrossRef
  - Scite.ai
  - OpenLibrary
  - SciELO
  - Google Scholar
  - PubMed
- Apresentação visual clara (ícones, cores e status)
- Geração de relatório em PDF
- Barra de progresso e tempo estimado de checagem

## Como usar:
1. Instale o Streamlit:
   pip install streamlit

2. Execute localmente:
   streamlit run refcheck.py

3. Ou envie para o [Streamlit Cloud](https://streamlit.io/cloud) com um repositório público.

Desenvolvido para a CGB/UNESP por Leonardo Assis com suporte de IA.
