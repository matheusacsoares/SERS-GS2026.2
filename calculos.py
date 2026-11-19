"""Calculos do SERS (GS 2026.2): consumo, diagnostico e comparacao rede x solar.

Base teorica da aula de SERS ("Energia, Potencia, Consumo e Demanda"):
    E = P x t                        energia = potencia x tempo
    P = U x I x cos(fi)              potencia ativa (W)
    Q = U x I x sen(fi)              potencia reativa (VAr)
    S = U x I   e   S^2 = P^2 + Q^2  potencia aparente (VA)
    fator de potencia = P / S

So usa a biblioteca padrao do Python (csv, pathlib, math).
"""
import csv
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"
HORAS_MES = 720  # 24 h x 30 dias, usado para converter kWh/mes em potencia media


# ---------------------------------------------------------------- leitura
def ler_parametros(caminho=None):
    """Le dados/parametros.csv e devolve {nome: valor}."""
    caminho = caminho or DADOS / "parametros.csv"
    parametros = {}
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            parametros[linha["nome"]] = float(linha["valor"])
    return parametros


def validar_aparelho(a, numero_linha=0):
    """Rejeita valores que nao fazem sentido fisico (entrada invalida)."""
    if a["potencia_w"] < 0:
        raise ValueError(f"linha {numero_linha}: potencia negativa em '{a['aparelho']}'")
    if not 0 <= a["horas_dia"] <= 24:
        raise ValueError(f"linha {numero_linha}: horas/dia deve estar entre 0 e 24 em '{a['aparelho']}'")
    if not 0 <= a["dias_mes"] <= 31:
        raise ValueError(f"linha {numero_linha}: dias/mes deve estar entre 0 e 31 em '{a['aparelho']}'")
    if not 0 <= a["fator_ciclo"] <= 1:
        raise ValueError(f"linha {numero_linha}: fator de ciclo deve estar entre 0 e 1 em '{a['aparelho']}'")
    if not 0 < a["fp"] <= 1:
        raise ValueError(f"linha {numero_linha}: fator de potencia deve estar entre 0 e 1 em '{a['aparelho']}'")
    if a["tipo"] not in ("uso", "base", "standby"):
        raise ValueError(f"linha {numero_linha}: tipo invalido em '{a['aparelho']}'")


def ler_aparelhos(caminho=None):
    """Le dados/aparelhos.csv e valida cada linha."""
    caminho = caminho or DADOS / "aparelhos.csv"
    aparelhos = []
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        for numero, linha in enumerate(csv.DictReader(arquivo), start=2):
            try:
                a = {
                    "aparelho": linha["aparelho"],
                    "tipo": linha["tipo"],
                    "potencia_w": float(linha["potencia_w"]),
                    "horas_dia": float(linha["horas_dia"]),
                    "dias_mes": float(linha["dias_mes"]),
                    "fator_ciclo": float(linha["fator_ciclo"]),
                    "fp": float(linha["fp"]),
                    "origem": linha["origem"],
                }
            except (ValueError, KeyError) as erro:
                raise ValueError(f"linha {numero}: valor invalido ({erro})") from erro
            validar_aparelho(a, numero)
            aparelhos.append(a)
    if not aparelhos:
        raise ValueError("a tabela de aparelhos esta vazia")
    return aparelhos


def ler_medidas(caminho=None):
    caminho = caminho or DADOS / "medidas.csv"
    medidas = []
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            medidas.append({
                "medida": linha["medida"],
                "aparelho": linha["aparelho"],
                "reducao_pct": float(linha["reducao_pct"]),
                "origem": linha["origem"],
            })
    return medidas


# ------------------------------------------------------------- consumo
def consumo_kwh_mes(a):
    """E = P x t, em kWh/mes. O fator de ciclo representa o tempo em que o
    aparelho realmente puxa a potencia (ex.: compressor da geladeira)."""
    return a["potencia_w"] * a["horas_dia"] * a["dias_mes"] * a["fator_ciclo"] / 1000


def custo_rs(kwh, tarifa):
    return kwh * tarifa


def consumo_total_kwh(aparelhos):
    return sum(consumo_kwh_mes(a) for a in aparelhos)


def ranking(aparelhos, tarifa):
    """Lista de aparelhos ordenada do que mais consome para o que menos consome."""
    total = consumo_total_kwh(aparelhos)
    linhas = []
    for a in aparelhos:
        kwh = consumo_kwh_mes(a)
        linhas.append({
            "aparelho": a["aparelho"],
            "kwh": kwh,
            "custo": custo_rs(kwh, tarifa),
            "pct": 100 * kwh / total if total else 0,
        })
    return sorted(linhas, key=lambda x: x["kwh"], reverse=True)


# --------------------------------------------------------- diagnostico
def consumo_base(aparelhos):
    """Consumo dos aparelhos que ficam ligados o tempo todo (tipo base e standby)."""
    kwh = sum(consumo_kwh_mes(a) for a in aparelhos if a["tipo"] in ("base", "standby"))
    watts = kwh * 1000 / HORAS_MES
    return kwh, watts


def consumo_standby_kwh(aparelhos):
    return sum(consumo_kwh_mes(a) for a in aparelhos if a["tipo"] == "standby")


def potencias_da_casa(aparelhos):
    """Soma as potencias medias (ativa P, reativa Q) e calcula S e o fator de
    potencia da casa. Cada carga tem Q = P x tan(fi), com cos(fi) = fp."""
    p_total = 0.0
    q_total = 0.0
    for a in aparelhos:
        p = consumo_kwh_mes(a) * 1000 / HORAS_MES  # potencia ativa media em W
        q = p * math.sqrt(1 / a["fp"] ** 2 - 1)    # S^2 = P^2 + Q^2
        p_total += p
        q_total += q
    s_total = math.sqrt(p_total ** 2 + q_total ** 2)
    fp_casa = p_total / s_total if s_total else 1.0
    return {"p_w": p_total, "q_var": q_total, "s_va": s_total, "fp": fp_casa}


def diagnostico(aparelhos, p):
    """Junta os indicadores usados pelo assistente."""
    total = consumo_total_kwh(aparelhos)
    base_kwh, base_w = consumo_base(aparelhos)
    standby = consumo_standby_kwh(aparelhos)
    standby_pct = 100 * standby / total if total else 0
    maior = ranking(aparelhos, p["tarifa_rs_kwh"])[0]
    return {
        "total_kwh": total,
        "custo": custo_rs(total, p["tarifa_rs_kwh"]),
        "vs_media_pct": 100 * (total / p["media_nacional_kwh_mes"] - 1),
        "maior": maior,
        "base_kwh": base_kwh,
        "base_w": base_w,
        "base_pct": 100 * base_kwh / total if total else 0,
        "standby_kwh": standby,
        "standby_pct": standby_pct,
        "standby_alto": standby_pct > p["limite_standby_pct"],
        "potencias": potencias_da_casa(aparelhos),
    }


# -------------------------------------------------------------- medidas
def aplicar_medidas(aparelhos, medidas, indices):
    """Devolve uma copia da lista de aparelhos com as medidas escolhidas
    aplicadas (a reducao e feita sobre o fator de ciclo do aparelho)."""
    novos = [dict(a) for a in aparelhos]
    for i in indices:
        m = medidas[i]
        achou = False
        for a in novos:
            if a["aparelho"] == m["aparelho"]:
                a["fator_ciclo"] *= 1 - m["reducao_pct"] / 100
                achou = True
        if not achou:
            raise ValueError(f"aparelho '{m['aparelho']}' da medida nao existe na tabela")
    return novos


# ---------------------------------------------------------------- solar
def dimensionar_solar(consumo_kwh, p):
    """Dimensiona um sistema para compensar o consumo acima do custo de
    disponibilidade e calcula custo, economia, retorno e emissoes.

    Payback simples: sem juros, sem reajuste de tarifa, sem degradacao.
    """
    a_compensar = max(consumo_kwh - p["disponibilidade_kwh"], 0)
    kwp = a_compensar / p["geracao_kwh_kwp_mes"]
    investimento = kwp * p["custo_rs_kwp"]
    economia_mes = a_compensar * p["tarifa_rs_kwh"] * p["fator_economia_solar"]
    conta_rede = consumo_kwh * p["tarifa_rs_kwh"]
    payback_anos = investimento / (economia_mes * 12) if economia_mes > 0 else None
    saldo_vida_util = economia_mes * 12 * p["vida_util_anos"] - investimento
    co2_rede = consumo_kwh * p["fator_emissao_rede"]
    co2_solar = (consumo_kwh - a_compensar) * p["fator_emissao_rede"] \
        + a_compensar * p["fator_emissao_solar"]
    return {
        "kwp": kwp,
        "geracao_kwh": a_compensar,
        "investimento": investimento,
        "conta_rede": conta_rede,
        "conta_solar": conta_rede - economia_mes,
        "economia_mes": economia_mes,
        "payback_anos": payback_anos,
        "saldo_vida_util": saldo_vida_util,
        "co2_rede_kg": co2_rede,
        "co2_solar_kg": co2_solar,
        "co2_evitado_kg": co2_rede - co2_solar,
    }
