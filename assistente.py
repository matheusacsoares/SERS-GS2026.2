"""Assistente de consumo de energia (SERS - GS 2026.2).

Uso:
    python src/assistente.py          menu interativo
    python src/assistente.py --demo   mostra todas as analises sem perguntar nada
"""
import sys

import calculos as c


def reais(valor):
    """Formata em R$ no padrao brasileiro (1.234,56)."""
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def numero(valor, casas=1):
    """Numero com virgula decimal."""
    return f"{valor:.{casas}f}".replace(".", ",")


def ler_numero(pergunta, minimo=0.0, maximo=None):
    """Pergunta ate receber um numero valido (trata texto, vazio e fora da faixa)."""
    while True:
        bruto = input(pergunta).strip().replace(",", ".")
        try:
            valor = float(bruto)
        except ValueError:
            print("  Valor invalido: digite apenas numeros (ex.: 250).")
            continue
        if valor < minimo or (maximo is not None and valor > maximo):
            faixa = f"maior ou igual a {numero(minimo)}" if maximo is None \
                else f"entre {numero(minimo)} e {numero(maximo)}"
            print(f"  Valor fora da faixa: informe um numero {faixa}.")
            continue
        return valor


# ------------------------------------------------------------ telas
def mostrar_consumo(aparelhos, p):
    print("\n=== CONSUMO POR APARELHO (E = P x t) ===")
    print(f"{'Aparelho':<52}{'kWh/mes':>9}{'R$/mes':>11}{'%':>7}")
    for linha in c.ranking(aparelhos, p["tarifa_rs_kwh"]):
        print(f"{linha['aparelho'][:50]:<52}{numero(linha['kwh']):>9}"
              f"{numero(linha['custo'], 2):>11}{numero(linha['pct']):>7}")
    total = c.consumo_total_kwh(aparelhos)
    print(f"{'TOTAL':<52}{numero(total):>9}{numero(c.custo_rs(total, p['tarifa_rs_kwh']), 2):>11}")


def mostrar_diagnostico(aparelhos, p):
    d = c.diagnostico(aparelhos, p)
    pot = d["potencias"]
    print("\n=== DIAGNOSTICO ===")
    print(f"Consumo: {numero(d['total_kwh'])} kWh/mes ({reais(d['custo'])}).")
    sentido = "acima" if d["vs_media_pct"] > 0 else "abaixo"
    print(f"Isso esta {numero(abs(d['vs_media_pct']))}% {sentido} da media nacional "
          f"({numero(p['media_nacional_kwh_mes'])} kWh/mes).")
    print(f"Maior consumo: {d['maior']['aparelho']} ({numero(d['maior']['pct'])}% da conta).")
    print(f"Consumo base (aparelhos sempre ligados): {numero(d['base_w'], 0)} W em media, "
          f"{numero(d['base_kwh'])} kWh/mes ({numero(d['base_pct'])}% do total).")
    print(f"Standby: {numero(d['standby_kwh'])} kWh/mes ({numero(d['standby_pct'])}% do total).")
    if d["standby_alto"]:
        print(f"  ATENCAO: acima do teto de {numero(p['limite_standby_pct'], 0)}% citado pelo Procel. "
              "Vale cortar aparelhos em espera (regua com chave).")
    else:
        print("  Standby dentro da faixa esperada.")
    print(f"Potencias medias da casa: P = {numero(pot['p_w'], 0)} W, Q = {numero(pot['q_var'], 0)} VAr, "
          f"S = {numero(pot['s_va'], 0)} VA, fator de potencia = {numero(pot['fp'], 2)}.")


def mostrar_comparacao(consumo, p, titulo="CASA DE EXEMPLO"):
    s = c.dimensionar_solar(consumo, p)
    print(f"\n=== COMPARACAO: REDE x SOLAR ({titulo}, {numero(consumo)} kWh/mes) ===")
    print(f"{'':<28}{'So rede':>16}{'Rede + solar':>16}")
    print(f"{'Conta de luz por mes':<28}{reais(s['conta_rede']):>16}{reais(s['conta_solar']):>16}")
    print(f"{'Investimento':<28}{reais(0):>16}{reais(s['investimento']):>16}")
    print(f"{'Emissoes por mes (kg CO2)':<28}{numero(s['co2_rede_kg']):>16}{numero(s['co2_solar_kg']):>16}")
    print(f"Sistema dimensionado: {numero(s['kwp'], 2)} kWp (gera ~{numero(s['geracao_kwh'], 0)} kWh/mes).")
    if s["payback_anos"] is None:
        print("Consumo abaixo do custo de disponibilidade: o solar nao compensa.")
    else:
        print(f"Economia estimada: {reais(s['economia_mes'])}/mes. Retorno estimado (payback simples): "
              f"{numero(s['payback_anos'])} anos.")
        print(f"Saldo estimado em {int(p['vida_util_anos'])} anos de vida util: {reais(s['saldo_vida_util'])} "
              "(sem juros nem reajuste de tarifa).")
        print(f"CO2 evitado: {numero(s['co2_evitado_kg'])} kg/mes.")
    print("Valores estimados. Confirme com orcamento e com a sua conta de luz.")


def simular_medidas(aparelhos, p, medidas, escolhidas=None):
    print("\n=== MEDIDAS DE EFICIENCIA ===")
    for i, m in enumerate(medidas, start=1):
        print(f" {i}) {m['medida']} (reduz {numero(m['reducao_pct'], 0)}% de '{m['aparelho'][:30]}')")
    if escolhidas is None:
        bruto = input("Quais aplicar? (ex.: 1,2 ou 0 para nenhuma): ").strip()
        try:
            escolhidas = [int(x) - 1 for x in bruto.replace(" ", "").split(",") if x and x != "0"]
        except ValueError:
            print("  Entrada invalida: use numeros separados por virgula.")
            return aparelhos
        if any(i < 0 or i >= len(medidas) for i in escolhidas):
            print("  Numero de medida inexistente.")
            return aparelhos
    novos = c.aplicar_medidas(aparelhos, medidas, escolhidas)
    antes, depois = c.consumo_total_kwh(aparelhos), c.consumo_total_kwh(novos)
    t = p["tarifa_rs_kwh"]
    print(f"Antes: {numero(antes)} kWh/mes ({reais(antes * t)}).")
    print(f"Depois: {numero(depois)} kWh/mes ({reais(depois * t)}).")
    print(f"Economia estimada: {numero(antes - depois)} kWh/mes = {reais((antes - depois) * t)} por mes, sem investir em solar.")
    return novos


def analisar_conta(p):
    print("\n=== ANALISE DA SUA CONTA ===")
    consumo = ler_numero("Consumo mensal da sua conta (kWh): ", minimo=1, maximo=5000)
    d = 100 * (consumo / p["media_nacional_kwh_mes"] - 1)
    sentido = "acima" if d > 0 else "abaixo"
    print(f"Voce esta {numero(abs(d))}% {sentido} da media nacional ({numero(p['media_nacional_kwh_mes'])} kWh/mes).")
    mostrar_comparacao(consumo, p, "SUA CASA")


# ------------------------------------------------------------- main
def demo(aparelhos, p, medidas):
    mostrar_consumo(aparelhos, p)
    mostrar_diagnostico(aparelhos, p)
    mostrar_comparacao(c.consumo_total_kwh(aparelhos), p)
    novos = simular_medidas(aparelhos, p, medidas, escolhidas=[0, 1, 3])
    mostrar_comparacao(c.consumo_total_kwh(novos), p, "CASA APOS AS MEDIDAS 1, 2 E 4")


def menu(aparelhos, p, medidas):
    atual = aparelhos
    while True:
        print("\n--- Assistente de energia ---")
        print("1) Consumo por aparelho   2) Diagnostico   3) Rede x solar")
        print("4) Simular medidas        5) Minha conta     0) Sair")
        opcao = input("Escolha: ").strip()
        if opcao == "1":
            mostrar_consumo(atual, p)
        elif opcao == "2":
            mostrar_diagnostico(atual, p)
        elif opcao == "3":
            mostrar_comparacao(c.consumo_total_kwh(atual), p)
        elif opcao == "4":
            atual = simular_medidas(aparelhos, p, medidas)
        elif opcao == "5":
            analisar_conta(p)
        elif opcao == "0":
            print("Ate mais!")
            return
        else:
            print("Opcao invalida. Digite um numero do menu.")


def main():
    try:
        p = c.ler_parametros()
        aparelhos = c.ler_aparelhos()
        medidas = c.ler_medidas()
    except (OSError, ValueError) as erro:
        print(f"Erro ao ler os dados: {erro}")
        sys.exit(1)
    if "--demo" in sys.argv:
        demo(aparelhos, p, medidas)
    else:
        menu(aparelhos, p, medidas)


if __name__ == "__main__":
    main()
