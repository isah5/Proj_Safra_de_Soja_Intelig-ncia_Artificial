<!--
Grupo: Isabelle Franco (RA 10425395), Gustavo Rodrigues (RA 10403091),
Pedro Henrique (RA 10388298), Lorenzo Tadeo (RA 10420067) | Orientador: Prof. Dr. Ivan Carlos Alcântara de Oliveira

Síntese do conteúdo deste arquivo: descreve os arquivos do artigo (PDF, LaTeX,
Word, rubrica) e como recompilá-los.

HISTÓRICO DE ALTERAÇÕES
Data       | Autor           | Descrição
-----------|-----------------|--------------------------------------------
2026-09-24 | Isabelle Franco | Criação da pasta do artigo + fonte LaTeX inicial
2026-11-19 | Lorenzo Tadeo   | Artigo final da N2 (PDF), versão Word N2 e rubrica preenchida
-->

# Artigo

| Arquivo | Conteúdo |
|---|---|
| `artigo-grupo.pdf` | **Artigo final (N2)** no template da SBC, compilado de `latex/artigo-grupo.tex` |
| `latex/artigo-grupo.tex` | Fonte LaTeX (com `sbc-template.sty` e `caption2.sty`, necessários para compilar) |
| `latex/figuras/` | Figuras 1–3 (análise exploratória, N1) e 4–9 (arquitetura e resultados, N2), geradas pelos notebooks |
| `word/Relatorio_N2_Soja_RS.docx` | Versão Word do artigo final, com o mesmo conteúdo do `.tex` |
| `word/Relatorio_N1_Soja_RS.docx` | Versão Word do artigo parcial (N1), mantida como histórico |
| `word/Rubrica_IA_Parte3_N2_Soja_RS_preenchida.docx` | Rubrica analítica da N2 com integrantes e título preenchidos (a pontuação é a autoavaliação do grupo) |
| `word/Rubrica_IA_Parte3_N2_20262_vFinal.docx` | Rubrica original, em branco |
| `modelosparapublicaodeartigos/` | Template original da SBC (fonte: sbc.org.br) |

## Como compilar

1. Suba os arquivos de `latex/` (incluindo `figuras/`) a um projeto novo no
   Overleaf, ou compile localmente com `pdflatex artigo-grupo.tex` (duas vezes,
   para resolver as referências cruzadas) ou com `tectonic artigo-grupo.tex`.
2. Salve o PDF nesta pasta como `artigo-grupo.pdf`.
3. Antes da entrega no AVA, insira o link do vídeo do YouTube na seção 4.7 do
   `.tex` (procure `INSERIR-LINK-DO-VIDEO`) e recompile.
