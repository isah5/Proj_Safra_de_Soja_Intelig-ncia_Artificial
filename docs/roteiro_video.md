<!--
Integrantes: Isabelle Franco (RA 10425395), Gustavo Rodrigues (RA 10403091),
Pedro Henrique (RA 10388298), Lorenzo Tadeo (RA 10420067) | Orientador: Prof. Dr. Ivan Carlos Alcântara de Oliveira

Síntese do conteúdo deste arquivo: roteiro do vídeo de apresentação da N2
(máximo de 5 minutos), com divisão de falas, telas a mostrar e comandos da
demonstração.

HISTÓRICO DE ALTERAÇÕES
Data       | Autor           | Descrição
-----------|-----------------|--------------------------------------------
2026-11-19 | Isabelle Franco | Criação do roteiro
-->


| # | Tempo | Quem | topicos | O que mostrar |
|---|---|---|---|---|
| 1 | 0:00–0:30 | Gustavo| "Olá! Somos Isabelle Franco, Gustavo Rodrigues, Pedro Henrique e Lorenzo Tadeo, do 7º semestre de Ciência da Computação da Universidade Presbiteriana Mackenzie. Este é o projeto da disciplina de Inteligência Artificial, com o Prof. Dr. Ivan Carlos Alcântara de Oliveira: *Previsão de Produtividade da Soja com Machine Learning*." | Primeira página do artigo (título, integrantes, instituição) |
| 2 | 0:30–1:10 | Pedro | **Problema:** o rendimento da soja no RS oscila muito. Em 2005 caiu para 662 kg/ha e, nas secas de 2020 e 2022, os municípios renderam em média 64% e 58% do normal. O IBGE só publica o número oficial cerca de 17 meses depois da colheita. A pergunta do projeto: dá para estimar antes, por município e só com dados públicos? Alinhado aos ODS 2 e 13. | Figura 1 (rendimento por safra) |
| 3 | 1:10–2:00 | Pedro | **Dados e preparação:** IBGE (497 municípios, 2000–2025), ONI da NOAA, 45 estações do INMET e as tabelas de adubação da Embrapa. Melhorias da N2: estação *válida* mais próxima (cobertura de 56% para 79%); atributos do período crítico dez–fev, como o balanço hídrico chuva − evapotranspiração; e histórico calculado só com safras passadas, para não haver vazamento. | Figura 4 (arquitetura) e seção 3 do notebook |
| 4 | 2:00–2:50 | Isabelle | **IA usada (fundamentos da disciplina):** aprendizado supervisionado de regressão. Comparamos Regressão Linear Ridge, Random Forest (bagging de árvores) e Gradient Boosting (árvores sequenciais nos resíduos) contra três baselines. A validação é temporal, walk-forward: cada safra é prevista só com as anteriores. Hiperparâmetros foram escolhidos em 2010–2015, e o teste é 2016–2025. **Resultado:** com o clima da safra, o MAE cai 12 a 19% frente à melhor baseline. Na semeadura, nenhum modelo vence, e mostramos isso com honestidade. | Tabela 5 do artigo; Figura 5 (erro por safra) |
| 5 | 2:50–3:30 | Isabelle| **Explicabilidade (XAI):** o SHAP mostra que o balanço hídrico de dez–fev é o fator mais importante. Também usamos o SHAP para achar um erro do modelo: o atributo "ano da safra" era espúrio e foi removido. A ablação mostra que a adubação, por só existir como recomendação normativa, não acrescenta informação. | Figura 7 (SHAP) e Figura 8 (ablação) |
| 6 | 3:30–4:15 | Lorenzo | **Demonstração do artefato:** roda no terminal `python src/prever_safra.py --safra 2025` e mostra o ranking de risco e a conferência com o IBGE (27 de 41 alertas confirmados). Depois roda `--safra 2022 --explicar "Cruz Alta"` e lê a explicação: o déficit hídrico tirou cerca de 820 kg/ha da previsão. Fecha com a ética: o resultado é um sinal de risco, não uma decisão de crédito ou seguro; o erro é maior no Sul; e o limiar do alerta fica com o gestor. | Terminal com as duas execuções |
| 7 | 4:15–4:40 | Lorenzo | **GitHub e conclusão:** percorre o repositório (artigo em PDF, `dataset/` com README, notebooks da N1 e da N2, `src/`, `resultados/`, `requirements.txt` e o passo a passo de reprodução). "O objetivo foi alcançado, com limites bem medidos: secas sem precedente ainda são subestimadas. Obrigado!" | Página do GitHub (README e pastas) |

## Comandos da demonstração

```bash
python src/prever_safra.py --safra 2025 --top 10
python src/prever_safra.py --safra 2022 --explicar "Cruz Alta" --top 5
```

Cada execução leva cerca de 15 s. Se preferir, rode antes e só mostre a saída
na gravação.

## Checklist antes de publicar

- [ ] Duração ≤ 5:00 (confira no editor)
- [ ] Título, integrantes, professor, disciplina, curso e instituição aparecem no início
- [ ] Problema, IA usada, solução funcionando e GitHub aparecem no vídeo
- [ ] Vídeo publicado no YouTube como "Não listado" ou "Público"
- [ ] Link colado em `artigo/latex/artigo-grupo.tex` (`INSERIR-LINK-DO-VIDEO`), no `README.md` e no Word; PDF recompilado
