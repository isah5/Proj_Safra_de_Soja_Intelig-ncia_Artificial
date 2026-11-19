"""
Previsão de Produtividade Municipal da Soja no RS — pipeline de modelagem (N2)

Integrantes: Isabelle Franco (RA 10425395), Gustavo Rodrigues (RA 10403091),
             Pedro Henrique (RA 10388298), Lorenzo Tadeo (RA 10420067)
Orientador: Prof. Dr. Ivan Carlos Alcântara de Oliveira
Disciplina: Inteligência Artificial — Universidade Presbiteriana Mackenzie (FCI)

Síntese do conteúdo deste arquivo:
    Funções reutilizáveis do projeto, usadas pelo notebook
    `notebooks/modelagem_n2.ipynb` e pelo script `src/prever_safra.py`:
    (1) leitura dos dados brutos (IBGE/SIDRA, NOAA/ONI, INMET, coordenadas);
    (2) agregação do clima diário do INMET por safra, com atributos do
        período crítico (dez–fev) e escolha da estação VÁLIDA mais próxima;
    (3) agregação do ONI em uma janela pré-safra (ASO+SON) e na safra (OND–JFM);
    (4) atributos de histórico produtivo sem vazamento (lags e média expandida);
    (5) atributos de adubação fosfatada (dose de P2O5 recomendada pela
        CQFS-RS/SC e quantidade equivalente de MAP, SS, ST e DAP);
    (6) linhas de base, modelos (Regressão Linear, Random Forest, Gradient
        Boosting) e validação temporal walk-forward (janela expandida).

Histórico de alterações:
Data       | Autor             | Descrição
-----------|-------------------|--------------------------------------------
2026-11-19 | Isabelle Franco   | Criação do módulo: clima por safra com estação válida mais próxima e atributos dez–fev
2026-11-19 | Gustavo Rodrigues | Atributos de histórico produtivo sem vazamento e janela pré-safra do ONI
2026-11-19 | Pedro Henrique    | Integração da adubação fosfatada (hipótese de classe de teor "Médio") e produtos MAP/SS/ST/DAP
2026-11-19 | Lorenzo Tadeo     | Baselines, modelos, validação walk-forward e métricas
2026-11-19 | Isabelle Franco   | Remoção de ano_safra dos atributos (diagnóstico via SHAP, confirmado na validação); alerta de quebra, SHAP e prever_safra
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RAIZ = Path(__file__).resolve().parents[1]
RAW = RAIZ / "dataset" / "raw"
PROCESSED = RAIZ / "dataset" / "processed"

SEMENTE = 42

# ---------------------------------------------------------------------------
# 1. Leitura dos dados brutos
# ---------------------------------------------------------------------------


def carregar_ibge() -> pd.DataFrame:
    df = pd.read_csv(RAW / "ibge_sidra_1612_soja_rs_2000_2025.csv")
    df["ano_safra"] = df["ano_safra"].astype(int)
    df["codigo_ibge_municipio"] = df["codigo_ibge_municipio"].astype(int)
    return df


def carregar_coordenadas() -> pd.DataFrame:
    df = pd.read_csv(RAW / "municipios_brasil_coords.csv")
    df = df[df["codigo_uf"] == 43][["codigo_ibge", "latitude", "longitude"]]
    return df.rename(columns={"codigo_ibge": "codigo_ibge_municipio"})


def carregar_estacoes() -> pd.DataFrame:
    df = pd.read_csv(RAW / "inmet_estacoes_metadados.csv", sep=";", encoding="utf-8-sig")
    return df.rename(columns={
        "Codigo Estacao": "codigo_estacao", "Nome Estacao": "nome_estacao",
        "Latitude": "lat_estacao", "Longitude": "lon_estacao", "Situacao": "situacao",
    })[["codigo_estacao", "nome_estacao", "lat_estacao", "lon_estacao", "situacao"]]


def _num_ptbr(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie.astype(str).str.replace(",", ".", regex=False), errors="coerce")


def carregar_inmet_diario() -> pd.DataFrame:
    cols = {
        "Codigo Estacao": "codigo_estacao",
        "Data Medicao": "data",
        "PRECIPITACAO TOTAL, DIARIO (AUT)(mm)": "precip_mm",
        "TEMPERATURA MEDIA, DIARIA (AUT)(°C)": "tmed_c",
        "TEMPERATURA MAXIMA, DIARIA (AUT)(°C)": "tmax_c",
        "TEMPERATURA MINIMA, DIARIA (AUT)(°C)": "tmin_c",
        "Latitude": "lat_estacao",
    }
    df = pd.read_csv(RAW / "inmet_estacoes_RS_consolidado_2000_2025.csv", sep=";",
                     encoding="utf-8-sig", usecols=list(cols), dtype=str)
    df = df.rename(columns=cols)
    for c in ["precip_mm", "tmed_c", "tmax_c", "tmin_c", "lat_estacao"]:
        df[c] = _num_ptbr(df[c])
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df = df.dropna(subset=["data"])
    df["eto_mm"] = eto_hargreaves(df["tmax_c"], df["tmin_c"], df["tmed_c"],
                                  df["lat_estacao"], df["data"].dt.dayofyear)
    return df


def eto_hargreaves(tmax, tmin, tmed, lat_graus, dia_do_ano):
    """Evapotranspiração de referência diária (mm/dia) pelo método de
    Hargreaves-Samani (1985), que exige apenas temperatura e latitude —
    adequado às estações automáticas do INMET (radiação com muitas falhas).
    Ra = radiação extraterrestre (FAO-56, eq. 21), convertida para mm/dia."""
    phi = np.radians(lat_graus)
    j = np.asarray(dia_do_ano, float)
    dr = 1 + 0.033 * np.cos(2 * np.pi * j / 365)
    delta = 0.409 * np.sin(2 * np.pi * j / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(delta), -1, 1))
    ra = (24 * 60 / np.pi) * 0.0820 * dr * (ws * np.sin(phi) * np.sin(delta)
                                             + np.cos(phi) * np.cos(delta) * np.sin(ws))
    ra_mm = 0.408 * ra
    amp = np.sqrt(np.clip(tmax - tmin, 0, None))
    return 0.0023 * ra_mm * (tmed + 17.8) * amp


# ---------------------------------------------------------------------------
# 2. Clima por estação e safra (INMET)
# ---------------------------------------------------------------------------

# Janela da safra: out–dez do ano anterior + jan–mar do ano da safra (~182 dias).
# Período crítico: dez–fev (floração e enchimento de grãos da soja no RS),
# quando déficit hídrico e calor causam as maiores perdas.
MIN_DIAS_SAFRA = 150      # de ~182 (mesmo critério da N1)
MIN_DIAS_CRITICO = 75     # de ~90
LIMIAR_DIA_SECO_MM = 1.0
LIMIAR_CALOR_C = 32.0


def _maior_sequencia(bool_arr: np.ndarray) -> int:
    melhor = atual = 0
    for v in bool_arr:
        atual = atual + 1 if v else 0
        melhor = max(melhor, atual)
    return melhor


def clima_por_estacao_safra(diario: pd.DataFrame) -> pd.DataFrame:
    d = diario.copy()
    m = d["data"].dt.month
    d["ano_safra"] = np.where(m >= 10, d["data"].dt.year + 1,
                              np.where(m <= 3, d["data"].dt.year, -1))
    d = d[d["ano_safra"] > 0]
    d["critico"] = d["data"].dt.month.isin([12, 1, 2])

    linhas = []
    for (est, safra), g in d.groupby(["codigo_estacao", "ano_safra"]):
        g = g.sort_values("data")
        c = g[g["critico"]]
        n_safra = int(g["precip_mm"].notna().sum())
        n_crit = int(c["precip_mm"].notna().sum())
        reg = {"codigo_estacao": est, "ano_safra": int(safra),
               "dias_validos_safra": n_safra, "dias_validos_critico": n_crit}
        if n_safra >= MIN_DIAS_SAFRA:
            reg["precip_safra_mm"] = g["precip_mm"].sum()
            reg["tmed_safra_c"] = g["tmed_c"].mean()
        if n_crit >= MIN_DIAS_CRITICO:
            # dias sem registro não contam como secos (conservador)
            seco = (c["precip_mm"] < LIMIAR_DIA_SECO_MM).to_numpy()
            reg["precip_dez_fev_mm"] = c["precip_mm"].sum() * 90.0 / n_crit  # normalizado p/ 90 dias
            # balanço hídrico climático simplificado: P - ETo (mm), dias com ambos
            ok = c["precip_mm"].notna() & c["eto_mm"].notna()
            if ok.sum() >= MIN_DIAS_CRITICO:
                reg["balanco_hidrico_dez_fev_mm"] = (
                    (c.loc[ok, "precip_mm"] - c.loc[ok, "eto_mm"]).sum() * 90.0 / ok.sum())
            reg["tmax_dez_fev_c"] = c["tmax_c"].mean()
            reg["dias_calor_dez_fev"] = int((c["tmax_c"] >= LIMIAR_CALOR_C).sum())
            reg["max_dias_secos_dez_fev"] = _maior_sequencia(seco)
        # chuva mensal (nov–mar), normalizada por 30 dias se o mês tiver >= 25 dias
        for mes, nome in [(11, "nov"), (12, "dez"), (1, "jan"), (2, "fev"), (3, "mar")]:
            pm = g.loc[g["data"].dt.month == mes, "precip_mm"]
            if pm.notna().sum() >= 25:
                reg[f"precip_{nome}_mm"] = pm.sum() * 30.0 / pm.notna().sum()
        linhas.append(reg)
    out = pd.DataFrame(linhas).sort_values(["codigo_estacao", "ano_safra"])
    # anomalia da chuva dez–fev em relação à "normal" da própria estação,
    # calculada SOMENTE com safras anteriores (média expandida, sem vazamento)
    normal = out.groupby("codigo_estacao")["precip_dez_fev_mm"].transform(
        lambda s: s.shift(1).expanding(min_periods=3).mean())
    out["anomalia_precip_dez_fev_pct"] = (out["precip_dez_fev_mm"] / normal - 1) * 100
    return out


def _haversine(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def distancias_municipio_estacao(coords: pd.DataFrame, estacoes: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for _, mu in coords.iterrows():
        for _, es in estacoes.dropna(subset=["lat_estacao"]).iterrows():
            linhas.append((int(mu["codigo_ibge_municipio"]), es["codigo_estacao"],
                           _haversine(mu["latitude"], mu["longitude"],
                                      es["lat_estacao"], es["lon_estacao"])))
    return pd.DataFrame(linhas, columns=["codigo_ibge_municipio", "codigo_estacao", "dist_km"])


DIST_MAX_KM = 100.0


def clima_por_municipio_safra(dist: pd.DataFrame, clima_est: pd.DataFrame) -> pd.DataFrame:
    """Para cada município e safra, usa a estação MAIS PRÓXIMA QUE TENHA DADO
    VÁLIDO no período crítico naquela safra (até DIST_MAX_KM).

    Na N1 era usada sempre a estação mais próxima, mesmo quando ela estava em
    pane — o que deixava ~45% do painel sem clima. Aqui, se a mais próxima
    falhou, recorre-se à seguinte (registrando a distância efetiva)."""
    validos = clima_est.dropna(subset=["precip_dez_fev_mm"])
    cand = dist[dist["dist_km"] <= DIST_MAX_KM].merge(validos, on="codigo_estacao")
    cand = cand.sort_values(["codigo_ibge_municipio", "ano_safra", "dist_km"])
    escolhido = cand.groupby(["codigo_ibge_municipio", "ano_safra"], as_index=False).first()
    return escolhido.rename(columns={"dist_km": "dist_estacao_km"})


# ---------------------------------------------------------------------------
# 3. ONI (NOAA)
# ---------------------------------------------------------------------------


def oni_por_safra() -> pd.DataFrame:
    """oni_pre_safra: média de ASO e SON do ano anterior (conhecida em
    dezembro, na semeadura) -> utilizável numa previsão ANTECIPADA.
    oni_media_safra: média OND, NDJ (ano anterior) + DJF, JFM (ano da safra),
    igual à N1."""
    oni = pd.read_csv(RAW / "noaa_oni_1999_2025.csv")
    reg = []
    for _, r in oni.iterrows():
        ano, s = int(r["ano"]), r["seas"]
        if s in ("ASO", "SON"):
            reg.append((ano + 1, "pre", r["oni_anom"]))
        if s in ("OND", "NDJ"):
            reg.append((ano + 1, "safra", r["oni_anom"]))
        if s in ("DJF", "JFM"):
            reg.append((ano, "safra", r["oni_anom"]))
    t = pd.DataFrame(reg, columns=["ano_safra", "janela", "oni"])
    t = t.pivot_table(index="ano_safra", columns="janela", values="oni", aggfunc="mean")
    return t.rename(columns={"pre": "oni_pre_safra", "safra": "oni_media_safra"}).reset_index()


def fase_enos(oni: float) -> str | None:
    if pd.isna(oni):
        return None
    if oni >= 0.5:
        return "El Niño"
    if oni <= -0.5:
        return "La Niña"
    return "Neutro"


# ---------------------------------------------------------------------------
# 4. Histórico produtivo (sem vazamento)
# ---------------------------------------------------------------------------


def atributos_historicos(df: pd.DataFrame) -> pd.DataFrame:
    """Todos os atributos usam SOMENTE safras anteriores à safra prevista."""
    df = df.sort_values(["codigo_ibge_municipio", "ano_safra"]).copy()
    g = df.groupby("codigo_ibge_municipio")
    df["rend_lag1"] = g["rendimento_kg_ha"].shift(1)
    df["rend_lag2"] = g["rendimento_kg_ha"].shift(2)
    anterior = g["rendimento_kg_ha"].shift(1)
    df["rend_media_hist"] = anterior.groupby(df["codigo_ibge_municipio"]).transform(
        lambda s: s.expanding().mean())
    df["rend_media_5safras"] = anterior.groupby(df["codigo_ibge_municipio"]).transform(
        lambda s: s.rolling(5, min_periods=3).mean())
    df["rend_max_hist"] = anterior.groupby(df["codigo_ibge_municipio"]).transform(
        lambda s: s.expanding().max())
    df["n_safras_hist"] = anterior.groupby(df["codigo_ibge_municipio"]).transform(
        lambda s: s.notna().cumsum())
    df["log_area_lag1"] = np.log1p(g["area_plantada_ha"].shift(1))
    return df


# ---------------------------------------------------------------------------
# 5. Adubação fosfatada (Embrapa / CQFS-RS/SC)
# ---------------------------------------------------------------------------

# Teores de P2O5 dos fertilizantes fosfatados usuais no RS (garantias mínimas
# usuais de mercado; MAP 11-52-00, DAP 18-46-00, SS 18% P2O5, ST 41% P2O5).
TEOR_P2O5 = {"map": 0.52, "ss": 0.18, "st": 0.41, "dap": 0.46}

# Hipótese simplificadora explícita (não há base pública de teor de P por
# município): solo com teor de P "Médio", 2º cultivo após correção — a
# situação mais comum em lavouras de grãos consolidadas. Pode ser alterada
# para análise de sensibilidade.
CLASSE_TEOR_P = "Medio"
CULTIVO = "2o"
ACRESCIMO_P2O5_POR_T = 15.0   # kg/ha de P2O5 por t/ha acima de 2 t/ha
ACRESCIMO_K2O_POR_T = 25.0


def atributos_adubacao(df: pd.DataFrame, classe: str = CLASSE_TEOR_P,
                       cultivo: str = CULTIVO) -> pd.DataFrame:
    """Dose recomendada = dose-base da Tabela 2.4 (para 2 t/ha) + acréscimo
    por t/ha de rendimento ESPERADO acima de 2 t/ha. O rendimento esperado é
    a média histórica do município ANTES da safra (sem vazamento)."""
    tab = pd.read_csv(RAW / "embrapa_tabela_2.4_recomendacao_p2o5_k2o_soja.csv")
    tab = tab.set_index("interpretacao_teor_p_k")
    base_p = float(tab.loc[classe, f"p2o5_kg_ha_{cultivo}_cultivo"])
    base_k = float(tab.loc[classe, f"k2o_kg_ha_{cultivo}_cultivo"])

    df = df.copy()
    esperado_t = df["rend_media_hist"] / 1000.0
    extra = np.clip(esperado_t - 2.0, 0, None)
    df["dose_p2o5_recomendada"] = base_p + ACRESCIMO_P2O5_POR_T * extra
    df["dose_k2o_recomendada"] = base_k + ACRESCIMO_K2O_POR_T * extra
    for prod, teor in TEOR_P2O5.items():
        df[f"kg_{prod}_ha_equiv"] = df["dose_p2o5_recomendada"] / teor
    return df


# ---------------------------------------------------------------------------
# 6. Construção do painel de modelagem
# ---------------------------------------------------------------------------


def construir_painel(verbose: bool = True) -> pd.DataFrame:
    ibge = carregar_ibge()
    coords = carregar_coordenadas()
    est = carregar_estacoes()
    clima_est = clima_por_estacao_safra(carregar_inmet_diario())
    dist = distancias_municipio_estacao(coords, est)
    clima_mun = clima_por_municipio_safra(dist, clima_est)

    df = ibge.merge(coords, on="codigo_ibge_municipio", how="left")
    df = df.merge(clima_mun, on=["codigo_ibge_municipio", "ano_safra"], how="left")
    df = df.merge(oni_por_safra(), on="ano_safra", how="left")
    df["fase_enos"] = df["oni_media_safra"].apply(fase_enos)
    df = atributos_historicos(df)
    df = atributos_adubacao(df)
    if verbose:
        print("Painel de modelagem:", df.shape)
        print("Pares com rendimento:", df["rendimento_kg_ha"].notna().sum())
        print("Pares com clima dez-fev:", df["precip_dez_fev_mm"].notna().sum())
    return df


# ---------------------------------------------------------------------------
# 7. Conjuntos de atributos (cenários de previsão)
# ---------------------------------------------------------------------------

# `ano_safra` NÃO entra como atributo: na primeira rodada da N2 o SHAP mostrou
# que, como árvores não extrapolam no tempo, a safra prevista cai sempre na
# "última folha" do treino e herda o regime das safras mais recentes (ex.:
# após a seca de 2020, a previsão de 2021 era puxada para baixo). Removê-lo
# reduziu o MAE de validação (2010–2015) dos três modelos; a tendência
# tecnológica continua representada por rend_media_5safras e rend_max_hist.
ATR_HIST = ["rend_lag1", "rend_lag2", "rend_media_hist", "rend_media_5safras",
            "rend_max_hist", "n_safras_hist", "log_area_lag1",
            "latitude", "longitude"]
ATR_ADUBACAO = ["dose_p2o5_recomendada", "dose_k2o_recomendada", "kg_map_ha_equiv",
                "kg_ss_ha_equiv", "kg_st_ha_equiv", "kg_dap_ha_equiv"]
ATR_ONI_PRE = ["oni_pre_safra"]
ATR_ONI_SAFRA = ["oni_media_safra"]
ATR_CLIMA = ["precip_safra_mm", "tmed_safra_c", "precip_dez_fev_mm",
             "balanco_hidrico_dez_fev_mm", "anomalia_precip_dez_fev_pct", "tmax_dez_fev_c",
             "dias_calor_dez_fev", "max_dias_secos_dez_fev",
             "precip_nov_mm", "precip_dez_mm", "precip_jan_mm", "precip_fev_mm",
             "precip_mar_mm", "dist_estacao_km"]

CENARIOS = {
    # Cenário A: previsão na semeadura (dezembro) — só o que já é conhecido.
    "A_pre_safra": ATR_HIST + ATR_ADUBACAO + ATR_ONI_PRE,
    # Cenário B: previsão no fim da safra (abril), antes da divulgação oficial
    # do IBGE (setembro do ano seguinte) — inclui o clima observado.
    "B_fim_safra": ATR_HIST + ATR_ADUBACAO + ATR_ONI_PRE + ATR_ONI_SAFRA + ATR_CLIMA,
}


# ---------------------------------------------------------------------------
# 8. Modelos
# ---------------------------------------------------------------------------


PARAMS_PADRAO = {
    "Regressão Linear": {"alpha": 1.0},
    "Random Forest": {"min_samples_leaf": 5, "max_features": 0.5},
    "Gradient Boosting": {"learning_rate": 0.05, "max_leaf_nodes": 31, "min_samples_leaf": 20},
}

# Grade (pequena, de propósito: poucas safras -> risco de sobreajuste na
# própria seleção) avaliada SOMENTE nas safras de validação.
GRADE = {
    "Regressão Linear": [{"alpha": a} for a in (0.1, 1.0, 10.0, 100.0)],
    "Random Forest": [{"min_samples_leaf": l, "max_features": f}
                      for l in (5, 20) for f in (0.33, 0.6)],
    "Gradient Boosting": [{"learning_rate": lr, "max_leaf_nodes": n, "min_samples_leaf": 20}
                          for lr in (0.03, 0.1) for n in (15, 31)],
}


def criar_modelo(nome: str, atributos: list[str], params: dict | None = None):
    p = {**PARAMS_PADRAO[nome], **(params or {})}
    if nome == "Regressão Linear":
        # Ridge = regressão linear com regularização L2 (estabiliza os
        # coeficientes diante de atributos colineares, ex.: doses de adubo)
        return Pipeline([
            ("imp", SimpleImputer(strategy="median", add_indicator=True)),
            ("esc", StandardScaler()),
            ("reg", Ridge(alpha=p["alpha"])),
        ])
    if nome == "Random Forest":
        return Pipeline([
            ("imp", SimpleImputer(strategy="median", add_indicator=True)),
            ("reg", RandomForestRegressor(n_estimators=300, n_jobs=-1, random_state=SEMENTE,
                                          min_samples_leaf=p["min_samples_leaf"],
                                          max_features=p["max_features"])),
        ])
    if nome == "Gradient Boosting":
        # HistGradientBoosting trata valores ausentes nativamente
        return HistGradientBoostingRegressor(max_iter=400, l2_regularization=1.0,
                                             early_stopping=False, random_state=SEMENTE,
                                             learning_rate=p["learning_rate"],
                                             max_leaf_nodes=p["max_leaf_nodes"],
                                             min_samples_leaf=p["min_samples_leaf"])
    raise ValueError(nome)


MODELOS = ["Regressão Linear", "Random Forest", "Gradient Boosting"]


def criar_modelos(atributos: list[str], params: dict | None = None) -> dict:
    params = params or {}
    return {n: criar_modelo(n, atributos, params.get(n)) for n in MODELOS}


def baselines(teste: pd.DataFrame) -> dict:
    return {
        "Baseline: média histórica": teste["rend_media_hist"].to_numpy(),
        "Baseline: safra anterior": teste["rend_lag1"].to_numpy(),
        # baseline mais exigente: acompanha a tendência tecnológica recente
        "Baseline: média 5 safras": teste["rend_media_5safras"].fillna(
            teste["rend_media_hist"]).to_numpy(),
    }


def metricas(y, yhat) -> dict:
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    return {"MAE": mean_absolute_error(y, yhat),
            "RMSE": math.sqrt(mean_squared_error(y, yhat)),
            "R2": r2_score(y, yhat),
            "MAPE_%": float(np.mean(np.abs(y - yhat) / y) * 100)}


def base_modelavel(df: pd.DataFrame, min_hist: int = 3, exigir_clima: bool = True) -> pd.DataFrame:
    """Linhas com alvo observado e pelo menos `min_hist` safras anteriores
    com rendimento (necessário para as baselines e os lags).

    exigir_clima=True mantém só linhas com clima observado no período crítico.
    Motivo: em 2003–2006 menos da metade dos municípios tem estação INMET
    operando; imputar o clima dessas safras (que incluem a seca de 2005)
    ensinaria ao modelo que uma quebra ocorreu com clima 'normal'."""
    b = df[df["rendimento_kg_ha"].notna() & (df["n_safras_hist"] >= min_hist)
           & df["rend_lag1"].notna()]
    if exigir_clima:
        b = b[b["precip_dez_fev_mm"].notna()]
    return b.copy().reset_index(drop=True)


COLS_ID = ["codigo_ibge_municipio", "municipio", "ano_safra", "rendimento_kg_ha",
           "fase_enos", "latitude", "longitude", "area_plantada_ha", "dist_estacao_km"]


def walk_forward(base: pd.DataFrame, atributos: list[str], anos_teste: list[int],
                 params: dict | None = None, modelos: list[str] | None = None,
                 guardar_modelos: bool = False):
    """Validação temporal com janela expandida: para cada safra t de teste,
    treina com todas as safras < t e prevê t. Nenhuma informação futura é
    usada no treino. Retorna as previsões fora da amostra (uma linha por
    município-safra de teste e uma coluna por modelo)."""
    params = params or {}
    modelos = modelos or MODELOS
    saidas, treinados = [], {}
    for t in anos_teste:
        tr = base[base["ano_safra"] < t]
        te = base[base["ano_safra"] == t]
        if te.empty:
            continue
        out = te[COLS_ID].copy()
        for nome, pred in baselines(te).items():
            out[nome] = pred
        for nome in modelos:
            mdl = criar_modelo(nome, atributos, params.get(nome))
            mdl.fit(tr[atributos], tr["rendimento_kg_ha"])
            out[nome] = mdl.predict(te[atributos])
            if guardar_modelos:
                treinados[(t, nome)] = mdl
        saidas.append(out)
    prev = pd.concat(saidas, ignore_index=True)
    return (prev, treinados) if guardar_modelos else prev


def ajustar_hiperparametros(base: pd.DataFrame, atributos: list[str],
                            anos_validacao: list[int]) -> tuple[dict, pd.DataFrame]:
    """Escolhe, para cada modelo, a configuração da GRADE com menor MAE no
    walk-forward das safras de VALIDAÇÃO (as safras de teste não são vistas)."""
    linhas, melhores = [], {}
    for nome in MODELOS:
        for cfg in GRADE[nome]:
            prev = walk_forward(base, atributos, anos_validacao, params={nome: cfg},
                                modelos=[nome])
            m = metricas(prev["rendimento_kg_ha"], prev[nome])
            linhas.append({"modelo": nome, "params": str(cfg), **m})
        tab = pd.DataFrame([l for l in linhas if l["modelo"] == nome])
        melhores[nome] = GRADE[nome][int(tab["MAE"].to_numpy().argmin())]
    return melhores, pd.DataFrame(linhas)


NOMES_BASELINES = ["Baseline: média histórica", "Baseline: safra anterior",
                   "Baseline: média 5 safras"]
NOMES_PREVISORES = NOMES_BASELINES + ["Regressão Linear", "Random Forest", "Gradient Boosting"]


def tabela_metricas(prev: pd.DataFrame, por: str | None = None) -> pd.DataFrame:
    linhas = []
    grupos = [(None, prev)] if por is None else prev.groupby(por, observed=True)
    for chave, g in grupos:
        for nome in NOMES_PREVISORES:
            if nome in g:
                reg = {"modelo": nome, **metricas(g["rendimento_kg_ha"], g[nome]), "n": len(g)}
                if por is not None:
                    reg[por] = chave
                linhas.append(reg)
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# 9. Alerta de quebra de safra (uso aplicado da regressão)
# ---------------------------------------------------------------------------

LIMIAR_QUEBRA = 0.80   # rendimento < 80% da média histórica do município


def avaliar_alerta_quebra(prev: pd.DataFrame, limiar: float = LIMIAR_QUEBRA) -> pd.DataFrame:
    """Transforma cada previsão em alerta binário ('quebra' se previsto <
    limiar x média histórica) e compara com a quebra observada."""
    ref = prev["Baseline: média histórica"]
    real = prev["rendimento_kg_ha"] < limiar * ref
    linhas = []
    for nome in NOMES_PREVISORES[1:]:
        alerta = prev[nome] < limiar * ref
        tp = int((alerta & real).sum()); fp = int((alerta & ~real).sum())
        fn = int((~alerta & real).sum()); tn = int((~alerta & ~real).sum())
        prec = tp / (tp + fp) if tp + fp else float("nan")
        rec = tp / (tp + fn) if tp + fn else float("nan")
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else float("nan")
        linhas.append({"modelo": nome, "VP": tp, "FP": fp, "FN": fn, "VN": tn,
                       "precisao": prec, "revocacao": rec, "F1": f1,
                       "acuracia": (tp + tn) / len(prev)})
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# 10. Explicabilidade (SHAP) e artefato de previsão
# ---------------------------------------------------------------------------


def matriz_para_shap(modelo, X: pd.DataFrame):
    """Devolve (estimador de árvores, X transformado, nomes) para o SHAP.
    Para o Random Forest em Pipeline, aplica o imputador antes."""
    if isinstance(modelo, Pipeline):
        imp = modelo.named_steps["imp"]
        Xt = pd.DataFrame(imp.transform(X), columns=imp.get_feature_names_out(), index=X.index)
        return modelo.named_steps["reg"], Xt
    return modelo, X


def shap_valores(modelo, X: pd.DataFrame, max_linhas: int | None = None):
    import shap
    est, Xt = matriz_para_shap(modelo, X)
    if max_linhas and len(Xt) > max_linhas:
        Xt = Xt.sample(max_linhas, random_state=SEMENTE)
    expl = shap.TreeExplainer(est)
    sv = expl(Xt, check_additivity=False)
    return sv


def prever_safra(df: pd.DataFrame, safra: int, cenario: str = "B_fim_safra",
                 modelo: str = "Gradient Boosting", params: dict | None = None,
                 limiar: float = LIMIAR_QUEBRA) -> pd.DataFrame:
    """Artefato: treina com todas as safras anteriores a `safra` e devolve,
    para cada município, a previsão, a referência histórica, o desvio (%) e
    o alerta de risco de quebra, ordenado do maior para o menor risco."""
    atr = CENARIOS[cenario]
    base = base_modelavel(df, exigir_clima=cenario.startswith("B"))
    tr = base[base["ano_safra"] < safra]
    alvo = df[(df["ano_safra"] == safra) & (df["n_safras_hist"] >= 3) & df["rend_lag1"].notna()]
    if cenario.startswith("B"):
        alvo = alvo[alvo["precip_dez_fev_mm"].notna()]
    mdl = criar_modelo(modelo, atr, (params or {}).get(modelo))
    mdl.fit(tr[atr], tr["rendimento_kg_ha"])
    out = alvo[["codigo_ibge_municipio", "municipio", "ano_safra", "rend_media_hist",
                "rendimento_kg_ha"]].copy()
    out["previsto_kg_ha"] = mdl.predict(alvo[atr])
    out["desvio_vs_media_hist_pct"] = (out["previsto_kg_ha"] / out["rend_media_hist"] - 1) * 100
    out["alerta_quebra"] = out["previsto_kg_ha"] < limiar * out["rend_media_hist"]
    out = out.rename(columns={"rendimento_kg_ha": "observado_kg_ha (se já divulgado)"})
    return out.sort_values("desvio_vs_media_hist_pct").reset_index(drop=True), mdl
