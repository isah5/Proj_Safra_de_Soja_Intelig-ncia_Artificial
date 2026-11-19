<!--
Integrantes: Isabelle Franco (RA 10425395), Gustavo Rodrigues (RA 10403091),
Pedro Henrique (RA 10388298), Lorenzo Tadeo (RA 10420067) | Orientador: Prof. Dr. Ivan Carlos Alcântara de Oliveira

Síntese do conteúdo deste arquivo: descreve as fontes de dados usadas no
projeto, os arquivos brutos já baixados em `dataset/raw/`, o dicionário de
variáveis planejado para a base final e as limitações conhecidas.

HISTÓRICO DE ALTERAÇÕES
Data       | Autor           | Descrição
-----------|-----------------|--------------------------------------------
2026-09-24 | Isabelle Franco  | Criação do template de descrição do dataset
2026-09-24 | Gustavo Rodrigues | Download dos dados reais do IBGE/SIDRA (Tabela 1612) e do ONI/NOAA; documentação atualizada
2026-09-24 | Pedro Henrique  | Adicionados dados diários do INMET (45 estações do RS, 2000-2023), baixados manualmente via portal BDMEP
2026-09-25 | Lorenzo Tadeo   | Estendido o range do IBGE e do ONI de 2000-2023 para 2000-2025 (a API do IBGE já publica dados até 2025); INMET segue em 2000-2023, atualização pendente
2026-09-25 | Isabelle Franco | Estendido o INMET para 2000-2025 (download manual complementar via BDMEP, mesmas 45 estações, período 2024-2025); base completa nas 3 fontes
2026-11-19 | Pedro Henrique  | N2: painel de modelagem `painel_modelagem_n2.csv` (estação válida mais próxima, clima dez–fev, ONI pré-safra, histórico sem vazamento e adubação fosfatada integrada); dicionário completo
2026-11-19 | Isabelle Franco | Seção do recorte geográfico (dados do RS e por que o RS)
-->

> **Resumo do dataset (N2):** painel município × safra do RS, 2000–2025,
> com 12.922 linhas (497 municípios × 26 safras) e 42 colunas. Junta o
> rendimento da soja (IBGE/SIDRA), o clima diário de 45 estações INMET
> agregado por safra, o índice ONI (NOAA) e atributos de adubação fosfatada
> (Embrapa/CQFS-RS/SC). Arquivo: `processed/painel_modelagem_n2.csv`, gerado
> por `notebooks/modelagem_n2.ipynb` a partir de `raw/`. Todos os dados são
> públicos e agregados, sem dados pessoais.

## Recorte geográfico: Rio Grande do Sul

Todos os dados são do **estado do Rio Grande do Sul**:

- **Produção (IBGE):** os 497 municípios gaúchos. Destes, 454 produziram
  soja em pelo menos uma safra entre 2000 e 2025, e 440 entram na modelagem
  (é preciso ter pelo menos 3 safras de histórico e clima válido).
- **Clima (INMET):** 45 estações automáticas instaladas no RS. Cada
  município usa, em cada safra, a estação válida mais próxima, a até 100 km.
- **Adubação (Embrapa/CQFS-RS/SC):** o manual de calagem e adubação dos
  estados do RS e de SC.
- **ENOS (NOAA/ONI):** índice global, igual para todos os municípios.

Por que o RS:

1. **Relevância produtiva:** a área colhida de soja passou de 3,0 para 6,8
   milhões de ha entre 2000 e 2025, e a cultura está em mais de 90% dos
   municípios.
2. **Exposição ao risco climático:** a soja gaúcha é quase toda de sequeiro.
   O rendimento médio varia 29% entre safras, e a produção caiu de 20,4 Mt
   (2021) para 9,4 Mt (2022). O sul do Brasil é uma das regiões com maior
   efeito do El Niño e da La Niña sobre a soja.
3. **Dados públicos homogêneos:** há séries municipais completas no IBGE,
   estações INMET com dados diários e uma recomendação de adubação
   (CQFS-RS/SC) válida só para RS e SC.
4. **Calendário agrícola único:** a semeadura vai de outubro a dezembro e o
   período crítico de dezembro a fevereiro, o que permite os mesmos
   atributos climáticos para todos os municípios.

Os resultados valem para o RS e não devem ser generalizados diretamente para
outros estados.

# Dataset — descrição

## Fontes

| Fonte | Conteúdo | Período | Granularidade | Link | Status |
|---|---|---|---|---|---|
| IBGE/SIDRA — Tabela 1612 | Área plantada, área colhida, produção e rendimento médio de soja | 2000–2025 | Município (RS) | https://sidra.ibge.gov.br/tabela/1612 | ✅ baixado — `dataset/raw/ibge_sidra_1612_soja_rs_2000_2025.csv` |
| NOAA/CPC — ONI | Índice trimestral (médias móveis de 3 meses) do ENOS (El Niño/La Niña) | 1999–2025 | Trimestral (a agregar por safra) | https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt | ✅ baixado — `dataset/raw/noaa_oni_1999_2025.csv` |
| INMET — BDMEP | Precipitação total diária e temperatura (máx/média/mín) diária, por estação automática | 2000-01-01 a 2025-12-31 | Estação meteorológica (diário) | https://bdmep.inmet.gov.br/ | ✅ baixado (manual, via portal BDMEP, em duas etapas) — `dataset/raw/inmet_estacoes_RS_consolidado_2000_2025.csv` (dados diários) + `dataset/raw/inmet_estacoes_metadados.csv` (lat/long/situação de cada estação) |
| Embrapa / CQFS-RS/SC | Recomendação de adubação fosfatada e potássica para soja, por classe de teor de P/K no solo | — | Classe de teor de P/K no solo (não por município) | https://www.infoteca.cnptia.embrapa.br/infoteca/handle/doc/1011192 | ✅ baixado — `dataset/raw/embrapa_tabela_2.3_interpretacao_teor_p_k.csv` + `dataset/raw/embrapa_tabela_2.4_recomendacao_p2o5_k2o_soja.csv` |

### Como os dados do IBGE foram obtidos

Via API pública do SIDRA (sem necessidade de token), tabela 1612, variáveis
109 (área plantada), 216 (área colhida), 214 (quantidade produzida) e 112
(rendimento médio), classificação 81 categoria 2713 (Soja em grão), para
todos os municípios do RS (`N6[N3[43]]`). A API do IBGE já publica dados até
2025 (a PAM de um ano costuma sair por volta de setembro do ano seguinte),
então usamos o range completo disponível, não só até 2023 como na primeira
versão desta base. Por limite de tamanho da API, a busca foi feita em duas
chamadas e depois unida:

```
https://servicodados.ibge.gov.br/api/v3/agregados/1612/periodos/2000-2023/variaveis/109|216|214|112?localidades=N6[N3[43]]&classificacao=81[2713]
https://servicodados.ibge.gov.br/api/v3/agregados/1612/periodos/2024-2025/variaveis/109|216|214|112?localidades=N6[N3[43]]&classificacao=81[2713]
```

(pedir os 26 anos de uma vez só retorna erro 500 do servidor do IBGE — é
mais confiável dividir a consulta.) O JSON bruto unido está em
`dataset/raw/ibge_sidra_1612_soja_rs_2000_2025_raw.json` e a versão já
tabulada (município × ano, uma linha por combinação) em
`dataset/raw/ibge_sidra_1612_soja_rs_2000_2025.csv` (12.922 linhas = 497
municípios × 26 safras). Valores ausentes (município sem produção de soja
naquele ano) aparecem como célula vazia.

### Como os dados do ONI foram obtidos

Arquivo ASCII oficial da NOAA/CPC (sem necessidade de API key):

```
https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
```

Cada linha é uma janela móvel de 3 meses (ex.: `DJF` = dez–jan–fev).
`dataset/raw/noaa_oni_1999_2025.csv` traz a série filtrada para 1999–2025
com colunas `seas`, `ano`, `total_sst`, `oni_anom` (o `oni_anom` é o índice
ONI propriamente dito). A NOAA já disponibiliza observações além de 2025,
mas cortamos em 2025 porque é o último ano com dado de safra do IBGE. O
notebook agrega essas janelas trimestrais em uma métrica por safra (média
do ONI nas janelas que cobrem out–mar de cada safra no RS).

### Como os dados do INMET foram obtidos

Baixados manualmente pelo portal BDMEP (https://bdmep.inmet.gov.br/), já que
a API automática (`apitempo.inmet.gov.br`) não respondeu nas tentativas via
script. Feito em **duas etapas**: primeiro 2000-01-01 a 2023-12-31, depois
(quando o IBGE e o ONI foram estendidos) o complemento 2024-01-01 a
2025-12-31, para as mesmas **45 estações automáticas** distribuídas pelo RS
(ex.: Porto Alegre, Rio Grande, Santa Maria, Uruguaiana, Bagé, Erechim,
Passo Fundo, Bento Gonçalves). O segundo download trouxe também dados de
outras ~37 estações novas da rede do INMET, que foram descartados para
manter o mesmo conjunto de 45 estações ao longo de toda a série — misturar
estações com históricos de tamanhos muito diferentes complicaria a
interpretação sem ganho real de cobertura.

**Mudança na N2:** em vez de usar sempre a estação mais próxima (que podia
estar em pane), cada município recebe, em cada safra, a estação **válida**
mais próxima, até 100 km. Com isso, a cobertura climática dos pares com
rendimento subiu de 55,7% para 79,2%. A distância efetiva fica registrada em
`dist_estacao_km` (mediana de 36,7 km).

- `dataset/raw/inmet_estacoes_metadados.csv` — uma linha por estação, com
  código, nome, latitude, longitude, altitude e situação (`Operante`,
  `Pane` ou `Desativada`).
- `dataset/raw/inmet_estacoes_RS_consolidado_2000_2025.csv` — 280.641
  linhas (estação × dia), 2000-01-01 a 2025-12-31, com precipitação total
  diária, temperatura máxima/média/mínima diária, e variáveis extras
  (pressão, umidade, ponto de orvalho, vento).

O notebook faz: (1) cálculo, para cada município, da estação mais próxima
(Haversine, usando as coordenadas de `inmet_estacoes_metadados.csv` e
`municipios_brasil_coords.csv`); (2) agregação dos dados diários por safra
(soma de precipitação, média de temperatura, na janela
semeadura–colheita); (3) tratamento de qualquer combinação estação-safra
com menos de 150 dos ~182 dias esperados (por `Pane` ou por a estação ainda
não estar instalada) como ausente, em vez de soma parcial enganosa.

### Como os dados de adubação fosfatada foram obtidos

O manual original da CQFS-RS/SC (2016), citado nas Referências do artigo, é
comercializado como livro impresso pela SBCS-Núcleo Regional Sul
(sbcs-nrs.org.br) e **não tem PDF gratuito oficial**. As mesmas tabelas de
recomendação (a base técnica é a mesma comissão/manual) são reproduzidas
livremente pela Embrapa em "Indicações Técnicas para a Cultura da Soja no
Rio Grande do Sul e em Santa Catarina", disponível sem custo no repositório
oficial Infoteca-e da Embrapa:
<https://www.infoteca.cnptia.embrapa.br/infoteca/handle/doc/1011192>
(edição safras 2014/2015 e 2015/2016, que cita "MANUAL... (2004)" como
fonte primária das tabelas — a estrutura de classes e doses é a mesma usada
nas edições posteriores do manual, incluindo a de 2016).

Duas tabelas foram transcritas dessas páginas (Tabela 2.3 e Tabela 2.4 do
documento):

- `dataset/raw/embrapa_tabela_2.3_interpretacao_teor_p_k.csv` — classifica o
  teor de P e K do solo (mg/dm³) em Muito baixo/Baixo/Médio/Alto/Muito alto,
  variando conforme a classe textural do solo (argila) e a CTC a pH 7,0.
- `dataset/raw/embrapa_tabela_2.4_recomendacao_p2o5_k2o_soja.csv` — dose de
  P₂O₅ e K₂O (kg/ha) recomendada por classe de teor, para 1º e 2º cultivo
  após a adubação corretiva, considerando rendimento esperado de 2 t/ha
  (para rendimentos maiores, soma-se 15 kg/ha de P₂O₅ e 25 kg/ha de K₂O por
  tonelada adicional). Há também uma recomendação pontual de enxofre (20 kg
  S/ha quando o teor no solo é menor que 10 mg/dm³), registrada aqui como
  nota e não como tabela.

**Importante — isto não é uma série por município/ano**: ao contrário do
IBGE, ONI e INMET, esta fonte é uma **tabela de referência agronômica**
(dose recomendada em função do teor de P/K no solo), não uma medição
histórica. Não existe base pública de "quanto fósforo foi realmente
aplicado" por município e safra. Para usar isso no painel município–safra,
o grupo precisará de uma **hipótese simplificadora explícita** — por
exemplo, assumir uma classe de teor de solo típica por região do RS (com
base em levantamentos de fertilidade do solo já publicados, citando a
fonte) e aplicar a dose correspondente da Tabela 2.4 como atributo fixo ou
por região, deixando claro no artigo que é uma aproximação, não um dado
observado.

**Hipótese adotada na N2** (implementada em `src/soja_pipeline.py`,
função `atributos_adubacao`): solo com teor de P "Médio" em 2º cultivo
(dose-base de 30 kg/ha de P₂O₅ e 45 kg/ha de K₂O para 2 t/ha), acrescida de
15 kg/ha de P₂O₅ e 25 kg/ha de K₂O por tonelada de rendimento **esperado**
acima de 2 t/ha. O rendimento esperado é a média histórica do município
antes da safra, sem vazamento. A dose é convertida em quantidade equivalente
de produto: MAP (52% de P₂O₅), Superfosfato Simples (18%), Superfosfato
Triplo (41%) e DAP (46%). A ablação do artigo (seção 4.5) mostra que esses
atributos **não acrescentam informação preditiva**. É o esperado por
construção: a dose é função monótona da média histórica (Spearman de 0,94).
Para ganhar valor, eles precisariam de dados **observados** de fertilidade
do solo por município.

### Coordenadas dos municípios (auxiliar, para casar com o INMET)

O IBGE não expõe latitude/longitude na API usada para a Tabela 1612, mas o
notebook de análise exploratória precisa disso para achar a estação INMET
mais próxima de cada município. Usamos a base pública
[kelvins/municipios-brasileiros](https://github.com/kelvins/municipios-brasileiros)
(código IBGE → lat/long/UF, licença MIT), filtrada para o RS: `dataset/raw/municipios_brasil_coords.csv`.

## Chaves e formato final

- Chave primária da base final: `codigo_ibge_municipio` + `ano_safra`
- Arquivo(s) brutos: `dataset/raw/`
- `dataset/processed/painel_municipio_safra.csv` (N1): gerado por
  `notebooks/analise_exploratoria.ipynb`; junta IBGE, o clima INMET da
  estação mais próxima e o ONI por safra.
- `dataset/processed/painel_modelagem_n2.csv` (**N2, usado nos modelos**):
  gerado por `notebooks/modelagem_n2.ipynb`, via
  `src/soja_pipeline.construir_painel()`. São 12.922 linhas e 42 colunas
  (dicionário abaixo). A base efetivamente modelada é um subconjunto: pares
  com rendimento, ≥ 3 safras anteriores e clima válido, ou seja, 7.951
  pares de 440 municípios, safras 2003–2025.

## Dicionário de variáveis (painel N2)

Todas as variáveis de histórico usam **somente safras anteriores** à safra
da linha, para evitar vazamento. Janela da safra: out–dez do ano anterior e
jan–mar do ano da safra. Período crítico: dez–fev.

| Coluna | Descrição | Unidade | Fonte |
|---|---|---|---|
| `codigo_ibge_municipio`, `municipio` | Código IBGE e nome do município | — | IBGE |
| `ano_safra` | Ano da safra (colheita) | ano | IBGE |
| `area_plantada_ha`, `area_colhida_ha`, `producao_ton` | Área e produção | ha / t | IBGE/SIDRA |
| `rendimento_kg_ha` | Rendimento médio (**variável-alvo**) | kg/ha | IBGE/SIDRA |
| `latitude`, `longitude` | Centróide do município | graus | kelvins/municipios-brasileiros |
| `codigo_estacao`, `dist_estacao_km` | Estação INMET válida mais próxima e distância | — / km | INMET |
| `dias_validos_safra`, `dias_validos_critico` | Dias com chuva registrada na safra e em dez–fev | dias | INMET |
| `precip_safra_mm`, `tmed_safra_c` | Chuva acumulada e temperatura média, out–mar (≥ 150 dias) | mm / °C | INMET |
| `precip_dez_fev_mm` | Chuva em dez–fev (≥ 75 dias; normalizada para 90 dias) | mm | INMET |
| `balanco_hidrico_dez_fev_mm` | Chuva − ETo (Hargreaves-Samani) em dez–fev | mm | INMET (calculado) |
| `anomalia_precip_dez_fev_pct` | Chuva dez–fev frente à média das safras anteriores da estação | % | INMET (calculado) |
| `tmax_dez_fev_c` | Média da temperatura máxima diária, dez–fev | °C | INMET |
| `dias_calor_dez_fev` | Dias com Tmax ≥ 32 °C em dez–fev | dias | INMET |
| `max_dias_secos_dez_fev` | Maior sequência de dias com chuva < 1 mm em dez–fev | dias | INMET |
| `precip_nov_mm` … `precip_mar_mm` | Chuva mensal de nov a mar (normalizada para 30 dias) | mm | INMET |
| `oni_pre_safra` | ONI médio ASO + SON do ano anterior (conhecido na semeadura) | índice | NOAA/CPC |
| `oni_media_safra` | ONI médio OND, NDJ, DJF e JFM | índice | NOAA/CPC |
| `fase_enos` | El Niño (ONI ≥ 0,5), La Niña (≤ −0,5) ou Neutro | categoria | calculado |
| `rend_lag1`, `rend_lag2` | Rendimento nas safras t−1 e t−2 | kg/ha | IBGE (calculado) |
| `rend_media_hist`, `rend_media_5safras`, `rend_max_hist` | Média expandida, média das 5 anteriores e máximo histórico | kg/ha | IBGE (calculado) |
| `n_safras_hist` | Nº de safras anteriores com rendimento | safras | IBGE (calculado) |
| `log_area_lag1` | log(1 + área plantada na safra anterior) | — | IBGE (calculado) |
| `dose_p2o5_recomendada`, `dose_k2o_recomendada` | Dose recomendada pela hipótese descrita acima | kg/ha | Embrapa/CQFS (calculado) |
| `kg_map_ha_equiv`, `kg_ss_ha_equiv`, `kg_st_ha_equiv`, `kg_dap_ha_equiv` | Quantidade equivalente de MAP, SS, ST e DAP | kg/ha | Embrapa/CQFS (calculado) |

Colunas brutas disponíveis em `inmet_estacoes_RS_consolidado_2000_2025.csv` (antes da
agregação por safra): `Codigo Estacao`, `Nome Estacao`, `Latitude`,
`Longitude`, `Altitude`, `Situacao`, `Data Medicao`, `PRECIPITACAO TOTAL,
DIARIO (AUT)(mm)`, `PRESSAO ATMOSFERICA MEDIA DIARIA (AUT)(mB)`,
`TEMPERATURA DO PONTO DE ORVALHO MEDIA DIARIA (AUT)(°C)`, `TEMPERATURA
MAXIMA, DIARIA (AUT)(°C)`, `TEMPERATURA MEDIA, DIARIA (AUT)(°C)`,
`TEMPERATURA MINIMA, DIARIA (AUT)(°C)`, `UMIDADE RELATIVA DO AR, MEDIA
DIARIA (AUT)(%)`, `UMIDADE RELATIVA DO AR, MINIMA DIARIA (AUT)(%)`, `VENTO,
RAJADA MAXIMA DIARIA (AUT)(m/s)`, `VENTO, VELOCIDADE MEDIA DIARIA
(AUT)(m/s)`. O arquivo usa `;` como separador e `,` como separador decimal
(padrão INMET) — atenção ao ler com pandas (`sep=';', decimal=','`).

## Limitações conhecidas

- Dados de adubação são **recomendações agronômicas por classe de solo**, não
  consumo real por produtor/município/ano.
- Municípios criados por desmembramento ao longo do período (2000–2025)
  podem ter séries históricas incompletas.
- A estação INMET usada por município é a mais próxima disponível, podendo
  não representar exatamente o microclima local.
- Várias estações do INMET aparecem como `Pane` em parte do período (falha
  de equipamento) — os dias correspondentes ficam com valor ausente na
  série e devem ser tratados como dado faltante, não como zero.
- A rede automática do INMET no RS começou a operar de forma escalonada
  (algumas estações só têm dados a partir de 2006-2007), então nem todo
  município tem cobertura climática completa desde 2000. Na N2, as safras
  sem clima válido (concentradas em 2003–2006) ficam **fora** da base de
  modelagem, em vez de imputadas, porque imputar a seca de 2005 com clima
  "normal" ensinaria uma relação falsa ao modelo.
- Municípios pequenos têm na PAM valores de rendimento frequentemente
  repetidos entre safras (estimativas administrativas), o que reduz a
  qualidade do alvo nesses casos.
- Representatividade regional: a soja é mais recente no Sul do estado (séries
  mais curtas); nessa região o ganho do modelo sobre a baseline é pequeno
  (ver artigo, Tabela 7).

## Licença de uso dos dados originais

Todas as fontes são públicas (governamentais/institucionais). Citar a fonte
original ao reutilizar os dados.
