"""
Previsão de Produtividade Municipal da Soja no RS — artefato de previsão (N2)

Integrantes: Isabelle Franco (RA 10425395), Gustavo Rodrigues (RA 10403091),
             Pedro Henrique (RA 10388298), Lorenzo Tadeo (RA 10420067)
Orientador: Prof. Dr. Ivan Carlos Alcântara de Oliveira
Disciplina: Inteligência Artificial — Universidade Presbiteriana Mackenzie (FCI)

Síntese do conteúdo deste arquivo:
    Interface de linha de comando do modelo. Treina o modelo escolhido com
    todas as safras ANTERIORES à safra alvo (mesmo protocolo da avaliação) e
    gera, para cada município do RS, a produtividade prevista, a referência
    histórica, o desvio percentual e o alerta de risco de quebra de safra
    (previsto < 80% da média histórica). Opcionalmente lista os fatores que
    mais pesaram (SHAP) para um município. Salva o ranking em CSV.

    Exemplos:
        python src/prever_safra.py --safra 2025
        python src/prever_safra.py --safra 2023 --modelo "Gradient Boosting"
        python src/prever_safra.py --safra 2022 --explicar "Cruz Alta"
        python src/prever_safra.py --safra 2025 --cenario A_pre_safra

Histórico de alterações:
Data       | Autor             | Descrição
-----------|-------------------|--------------------------------------------
2026-11-19 | Lorenzo Tadeo     | Criação do script (ranking de risco por município)
2026-11-19 | Isabelle Franco   | Opção --explicar com os principais fatores SHAP
"""

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import soja_pipeline as sp  # noqa: E402

warnings.filterwarnings("ignore")


def main() -> None:
    ap = argparse.ArgumentParser(description="Previsão municipal da produtividade da soja no RS")
    ap.add_argument("--safra", type=int, required=True, help="ano da safra (colheita), ex.: 2025")
    ap.add_argument("--cenario", default="B_fim_safra", choices=list(sp.CENARIOS))
    ap.add_argument("--modelo", default="Random Forest", choices=sp.MODELOS)
    ap.add_argument("--limiar", type=float, default=sp.LIMIAR_QUEBRA,
                    help="alerta se previsto < limiar x média histórica (padrão 0.80)")
    ap.add_argument("--top", type=int, default=15, help="quantos municípios mostrar")
    ap.add_argument("--explicar", default=None, help="parte do nome de um município para explicar")
    ap.add_argument("--saida", default=None, help="CSV de saída (padrão resultados/previsao_safra_<ano>.csv)")
    a = ap.parse_args()

    hp = sp.RAIZ / "resultados" / "hiperparametros.json"
    params = json.loads(hp.read_text(encoding="utf-8")) if hp.exists() else None

    print(f"Construindo o painel a partir de dataset/raw ... (cenário {a.cenario}, modelo {a.modelo})")
    df = sp.construir_painel(verbose=False)
    if a.safra not in set(df["ano_safra"]):
        sys.exit(f"Safra {a.safra} fora do período com dados (2000–2025).")

    ranking, modelo = sp.prever_safra(df, a.safra, a.cenario, a.modelo, params, a.limiar)
    saida = Path(a.saida) if a.saida else sp.RAIZ / "resultados" / f"previsao_safra_{a.safra}.csv"
    saida.parent.mkdir(exist_ok=True)
    ranking.to_csv(saida, index=False)

    obs_col = "observado_kg_ha (se já divulgado)"
    print(f"\nSafra {a.safra}: {len(ranking)} municípios previstos; "
          f"{int(ranking['alerta_quebra'].sum())} com alerta de quebra (limiar {a.limiar:.0%}).")
    if ranking[obs_col].notna().any():
        r = ranking.dropna(subset=[obs_col])
        mae = np.mean(np.abs(r[obs_col] - r["previsto_kg_ha"]))
        real = r[obs_col] < a.limiar * r["rend_media_hist"]
        print(f"Conferência com o IBGE: MAE = {mae:.0f} kg/ha; "
              f"alertas confirmados = {int((r['alerta_quebra'] & real).sum())} de {int(r['alerta_quebra'].sum())}.")
    print(f"\nTop {a.top} municípios com maior risco (menor previsão relativa à média histórica):")
    cols = ["municipio", "rend_media_hist", "previsto_kg_ha", "desvio_vs_media_hist_pct",
            "alerta_quebra", obs_col]
    print(ranking[cols].head(a.top).round(0).to_string(index=False))
    print(f"\nRanking completo salvo em {saida}")

    if a.explicar:
        alvo = df[(df["ano_safra"] == a.safra) & df["municipio"].str.contains(a.explicar, case=False)]
        if alvo.empty:
            print(f"\nMunicípio contendo '{a.explicar}' não encontrado na safra {a.safra}.")
            return
        linha = alvo.iloc[[0]]
        sv = sp.shap_valores(modelo, linha[sp.CENARIOS[a.cenario]])
        contrib = sorted(zip(sv.feature_names, sv.values[0], sv.data[0]),
                         key=lambda t: -abs(t[1]))
        contrib = [c for c in contrib if not c[0].startswith("missingindicator")][:8]
        prev = float(modelo.predict(linha[sp.CENARIOS[a.cenario]])[0])
        print(f"\nExplicação SHAP — {linha['municipio'].iloc[0]}, safra {a.safra}")
        print(f"  valor base (média do treino): {float(sv.base_values[0]):.0f} kg/ha -> previsto: {prev:.0f} kg/ha")
        for nome, v, x in contrib:
            print(f"  {nome:30s} = {x:10.1f}   contribuição {v:+7.0f} kg/ha")


if __name__ == "__main__":
    main()
