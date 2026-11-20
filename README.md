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
2026-11-19 | Isabelle Franco    | Recorte do RS (por que o RS) e relação com as metas dos ODS 2 e 13
-->

Projeto da disciplina de **Inteligência Artificial** (Universidade Presbiteriana
Mackenzie, FCI — Prof. Dr. Ivan Carlos Alcântara de Oliveira).

**Integrantes:** Isabelle Franco (RA 10425395) · Gustavo Rodrigues (RA 10403091) ·
Pedro Henrique (RA 10388298) · Lorenzo Tadeo (RA 10420067)

**Problema:** estimar a produtividade da soja (kg/ha) de cada município do
**Rio Grande do Sul** em cada safra, a partir de dados públicos de produção
(IBGE), clima (INMET), ENOS (NOAA/ONI) e adubação fosfatada
(Embrapa/CQFS-RS/SC). O projeto trata dos **ODS 2 (Fome Zero e Agricultura
Sustentável)** e **13 (Ação contra a Mudança Global do Clima)**.

**Por que o RS:** todos os dados são do estado: 497 municípios no IBGE (440
modelados) e 45 estações do INMET no RS. O recorte foi escolhido por quatro
razões:

- **Relevância produtiva:** a área colhida passou de 3,0 para 6,8 milhões
  de ha entre 2000 e 2025.
- **Risco climático:** a soja gaúcha é quase toda de sequeiro, e a
  produção caiu 54% de 2021 para 2022.
- **Dados públicos homogêneos:** a recomendação de adubação da CQFS-RS/SC
  vale só para RS e SC.
- **Calendário agrícola único:** o período crítico, de dezembro a
  fevereiro, é o mesmo em todo o estado.

## Relação com os ODS 2 e 13

| Meta ODS | O que foi modelado | Resultado (teste 2016–2025) | Impacto esperado |
|---|---|---|---|
| **2.4**: produção de alimentos sustentável e resiliente a secas | Produtividade municipal da soja (kg/ha) com histórico, clima, ENOS e adubação | MAE 17–19% menor que a média das 5 últimas safras; maior ganho em La Niña (743 → 559 kg/ha) | Mostra, por município, onde a produção tende a cair, para orientar assistência técnica e apoio aos produtores |
| **2.c**: informação de mercado oportuna, contra a volatilidade de preços | Previsão no fim da safra (abril) | Estimativa cerca de 17 meses antes do dado oficial do IBGE | Informação antecipada sobre a oferta de soja do estado |
| **13.1**: resiliência e adaptação a riscos climáticos | Balanço hídrico, calor e dias secos de dez–fev; ONI; SHAP | O balanço hídrico de dez–fev é o fator mais influente; em Cruz Alta (2022), o déficit tirou 822 kg/ha da previsão | Mede a sensibilidade de cada município à seca e indica onde a adaptação é mais urgente |
| **13.3**: alerta precoce e capacidade institucional | Alerta de quebra e ranking de risco (`src/prever_safra.py`) | Precisão 0,62 e revocação 0,17 no limiar de 80%; em 2025, 27 de 41 alertas confirmados | Alerta municipal explicável, com limiar ajustável pelo gestor |

**Limites:**
- Na semeadura, o modelo ainda não supera a baseline.
- Ele subestima secas sem precedente.
- A adubação não melhorou a previsão.

Os detalhes estão nas seções 1.2 e 1.5 do artigo.

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
| Vídeo no YouTube | **https://youtu.be/uREzIrezDgs** |

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
└── resultados/                   # métricas, previsões, ablação, SHAP, hiperparâmetros (CSV/JSON)
```

## Como reproduzir

Requisitos: Python 3.12 (testado com 3.12.15). A execução completa leva cerca de
3 minutos num computador pessoal e não precisa de GPU.

```bash
git clone https://github.com/isah5/Proj_Safra_de_Soja_Intelig-ncia_Artificial.git
cd Proj_Safra_de_Soja_Intelig-ncia_Artificial
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
