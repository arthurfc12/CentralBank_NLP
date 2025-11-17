# Relevant Links

Meetings number 21-199 do not have pdf associated, scraping was used (file downloadTextPages.py). Meetings 200-273 have pdfs, downloaded from pdfs (downloadfiles.py) and converted to txt files (pdf_to_txt.py). Renamed every txt file so each file becomes YYYY-MM-DD.txt (renameTxt.py)

## Used in this Repository

- [Reuniões Banco Central](https://www.bcb.gov.br/publicacoes/atascopom/cronologicos)

## For future implementation

- [Reuniões colegiado CVM](https://www.gov.br/cvm/pt-br/centrais-de-conteudo/publicacoes/reunioes-do-colegiado)
- [Reuniões colegiado CVM - DataList](https://conteudo.cvm.gov.br/decisoes/index.html?lastNameShow=&lastName=&filtro=todos&dataInicio=&dataFim=&buscadoDecisao=false&categoria=decisao)
- [Atas Reuniões](https://www.gov.br/cvm/pt-br/centrais-de-conteudo/atas-de-comites/cge)

## Variáveis para analisar

- DF vai ficar: título, data, local, horário de início e de término, sumário, membros da diretoria, chefes de departamento, demais participantes, Corpo do texto
- A partir dessa dataframe, prever taxa selic -> testar métodos diferentes, curvas de erro, acurácia, etc.
