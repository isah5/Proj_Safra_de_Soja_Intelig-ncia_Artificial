# Previsão de Produtividade Municipal da Soja no Rio Grande do Sul com Aprendizado de Máquina e Variáveis Agrometeorológicas

<!--
CABEÇALHO DE IDENTIFICAÇÃO DO GRUPO
Integrantes: Isabelle Franco (RA 10425395), Gustavo Rodrigues (RA 10403091),
             Pedro Henrique (RA 10388298), Lorenzo Tadeo (RA 10420067)
Prof: Dr. Ivan Carlos Alcântara de Oliveira
Disciplina: Inteligência Artificial — 7º CC
Instituição: Universidade Presbiteriana Mackenzie - FCI

Síntese do conteúdo deste arquivo: visão geral do projeto, estrutura do
repositório, como reproduzir os resultados e resumo dos resultados da N2.

HISTÓRICO DE ALTERAÇÕES
Data       | Autor              | Descrição
-----------|--------------------|--------------------------------------------
2026-09-24 | Isabelle Franco    | Criação inicial do repositório (estrutura N1)
2026-11-19 | Gustavo Rodrigues  | Atualização para a N2: modelagem, resultados, artefato, instruções de reprodução
-->

Projeto da disciplina de **Inteligência Artificial** (Universidade Presbiteriana
Mackenzie, FCI — Prof. Dr. Ivan Carlos Alcântara de Oliveira).

**Integrantes:** Isabelle Franco (RA 10425395) · Gustavo Rodrigues (RA 10403091) ·
Pedro Henrique (RA 10388298) · Lorenzo Tadeo (RA 10420067)

**Problema:** estimar a produtividade da soja (kg/ha) de cada município do RS em
cada safra, a partir de dados públicos de produção (IBGE), clima (INMET), ENOS
(NOAA/ONI) e adubação fosfatada (Embrapa/CQFS-RS/SC). Alinhado aos ODS 2 e 13.

**Técnicas de IA:** aprendizado supervisionado (regressão): Regressão Linear
(Ridge), Random Forest e Gradient Boosting; validação temporal *walk-forward*;
IA Explicável com **SHAP**.

| Entrega | Onde |
|---|---|
| Artigo final (PDF, template SBC) | [`artigo/artigo-grupo.pdf`](artigo/artigo-grupo.pdf) |
| Fonte LaTeX do artigo | [`artigo/latex/artigo-grupo.tex`](artigo/latex/artigo-grupo.tex) |
| Versão Word do artigo | [`artigo/word/Relatorio_N2_Soja_RS.docx`](artigo/word/Relatorio_N2_Soja_RS.docx) |
| Dataset + descrição | [`dataset/`](dataset/) · [`dataset/README.md`](dataset/README.md) |
| Notebook N1 — análise exploratória | [`notebooks/analise_exploratoria.ipynb`](notebooks/analise_exploratoria.ipynb) |
| Notebook N2 — modelagem, avaliação e SHAP | [`notebooks/modelagem_n2.ipynb`](notebooks/modelagem_n2.ipynb) |
| Código-fonte (pipeline e artefato) | [`src/`](src/) |
| Tabelas de resultados | [`resultados/`](resultados/) |
| Roteiro do vídeo (≤ 5 min) | [`docs/roteiro_video.md`](docs/roteiro_video.md) |
| Vídeo no YouTube | **[inserir link após a gravação]** |

## Resultados principais (teste fora da amostra, safras 2016–2025)

Cenário B = previsão no fim da safra (abril), com clima observado; cerca de 17
meses antes da divulgação oficial do IBGE.

| Previsor | MAE (kg/ha) | R² | Ganho sobre a melhor baseline |
|---|---:|---:|---:|
| Baseline: média das 5 últimas safras | 695,7 | −0,04 | — |
| Regressão Linear (Ridge) | 611,6 | 0,20 | 12,1% |
| Random Forest (selecionado na validação) | 576,0 | 0,25 | 17,2% |
| Gradient Boosting | **560,7** | **0,28** | **19,4%** |

- Na **semeadura** (cenário A: histórico + adubação + ONI), nenhum modelo supera
  a baseline.
- **Ablação:** todo o ganho vem do clima INMET do período crítico (dez–fev). A
  adubação, que só pode ser derivada de recomendações normativas, não altera o
  erro.
- **SHAP:** o balanço hídrico de dez–fev é o fator mais influente. O SHAP também
  foi usado para remover um atributo espúrio (`ano_safra`).
- **Limitação:** a magnitude de secas sem precedente (2020, 2022) é subestimada.
  Como alerta de quebra, o modelo tem precisão de cerca de 0,6 e revocação de
  cerca de 0,17 no limiar de 80%; o limiar é ajustável.

## Estrutura do repositório

```
.
├── artigo/
│   ├── artigo-grupo.pdf          # artigo final (N2), compilado do LaTeX
│   ├── latex/                    # fonte .tex (template SBC) + figuras 1–9
│   └── word/                     # versões Word (N1 e N2) e rubrica preenchida
├── dataset/
│   ├── raw/                      # dados brutos baixados (IBGE, NOAA, INMET, Embrapa, coordenadas)
│   ├── processed/                # painel N1 e painel de modelagem N2 (gerados pelos notebooks)
│   └── README.md                 # origem, dicionário de variáveis e limitações
├── notebooks/
│   ├── analise_exploratoria.ipynb  # N1
│   ├── modelagem_n2.ipynb          # N2
│   ├── requirements.txt            # dependências com versões
│   └── CABECALHO_PADRAO.md         # modelo de cabeçalho/histórico dos arquivos
├── src/
│   ├── soja_pipeline.py          # preparação, atributos, modelos, validação, SHAP
│   └── prever_safra.py           # artefato: ranking municipal de risco (linha de comando)
├── resultados/                   # métricas, previsões, ablação, SHAP, hiperparâmetros (CSV/JSON)
└── docs/roteiro_video.md
```

## Como reproduzir

Requisitos: Python 3.12 (testado com 3.12.15). A execução completa leva cerca de
3 minutos num computador pessoal e não precisa de GPU.

```bash
git clone https://github.com/isah5/Projeto_Safra_de_Soja.git
cd Projeto_Safra_de_Soja
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Linux/macOS: source .venv/bin/activate
python -m pip install -r notebooks/requirements.txt

# 1) Análise exploratória (N1) e 2) modelagem completa (N2), com saídas e figuras
cd notebooks
jupyter nbconvert --to notebook --execute --inplace analise_exploratoria.ipynb
jupyter nbconvert --to notebook --execute --inplace modelagem_n2.ipynb
cd ..

# 3) Artefato: previsão e ranking de risco para uma safra
python src/prever_safra.py --safra 2025
python src/prever_safra.py --safra 2022 --modelo "Gradient Boosting" --explicar "Cruz Alta"
```

O notebook da N2 regrava `dataset/processed/painel_modelagem_n2.csv`, as
figuras 4–9 em `artigo/latex/figuras/` e as tabelas em `resultados/`. Todas as
sementes aleatórias são fixas (`SEMENTE = 42`), então os números se repetem.

Para compilar o artigo: suba `artigo/latex/` ao Overleaf ou rode `pdflatex`
(ou `tectonic`) em `artigo-grupo.tex`.

## Licença / uso dos dados

O projeto usa apenas dados públicos (IBGE/SIDRA, NOAA, INMET,
Embrapa/CQFS-RS/SC), agregados por município ou por estação, sem dados
pessoais. Ao reutilizar os dados, cite as fontes originais (ver
`dataset/README.md`). As previsões são um indicador regional de apoio à
decisão: não devem ser usadas como critério automático de crédito, seguro ou
recomendação de adubação (ver a seção de ética do artigo).
