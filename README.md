# Assistente de Consumo de Energia — SERS (Global Solution 2026.2)

**Disciplina:** Soluções em Energias Renováveis e Sustentáveis (SERS) — FIAP, Ciência da Computação (1CCPQ)
**Projeto da GS:** Citizen Assist AI

**Integrantes**

| Nome completo | RM |
|---|---|
| Giovanna Ferreira Almeida | 571822 |
| Maria Luiza Vieira de Freitas | 571535 |
| Matheus Arruda Camara Soares | 571594 |

> **Contribuição do SERS neste repositório:** tudo que está aqui (dados, cálculos, assistente, análise e
> documentação). O assistente de energia é **independente** de qualquer outra entrega do grupo e roda
> sozinho, apenas com Python.

---

## 1. Problema, público e necessidade

**Público:** famílias de casa própria ou alugada, com conta de luz alta, que não sabem **para onde a energia está indo** e se **vale instalar energia solar**.

**Necessidade:** entender o consumo da casa (qual aparelho pesa mais, quanto é desperdício em standby)
e decidir com números entre **continuar só na rede** ou **instalar solar**, antes de gastar com orçamento.

**Por que é útil e não genérico:** o assistente parte de uma tabela de aparelhos com potência, horas de uso e
origem do dado. Ele devolve diagnóstico, ranking, medidas de economia que não exigem investimento e a
comparação rede × solar com custo, retorno e emissões. O usuário também pode digitar o consumo da própria conta.

**Ligação com o ODS 7 (energia limpa e acessível) e com consumo consciente:** reduzir desperdício primeiro e
dimensionar o solar depois, já com o consumo menor.

## 2. O que o assistente faz

| Opção | Função | Base |
|---|---|---|
| 1 | Consumo por aparelho: kWh/mês, R$/mês e % da conta | E = P × t |
| 2 | Diagnóstico: vs. média nacional, maior consumo, consumo base, standby, potências P, Q, S e fator de potência | Aula de SERS (triângulo das potências) |
| 3 | Comparação **rede × solar**: conta, investimento, retorno, CO₂ | Premissas em `parametros.csv` |
| 4 | Simula medidas de eficiência e recalcula o consumo e o solar necessário | `medidas.csv` |
| 5 | Analisa **a conta do usuário** (digita os kWh/mês) | Mesmo modelo |

Entradas inválidas (texto, negativo, fora da faixa) são tratadas com mensagem de erro e nova pergunta.

### Integração com o Citizen Assist AI

O módulo de energia roda sozinho (`assistente.py`) e foi organizado para ser chamado por outro assistente:
`calculos.py` é uma biblioteca sem dependências, e o `assistente.py` mostra como as respostas são montadas
(diagnóstico, comparação rede × solar, medidas, conta do usuário). Para usar as mesmas contas em outro programa,
basta importar as funções, por exemplo:

```python
from calculos import ler_parametros, dimensionar_solar
resposta = dimensionar_solar(consumo_kwh=250, p=ler_parametros())  # dicionário com kWp, custo, payback, CO2
```

Neste repositório a contribuição de SERS é demonstrada pelo próprio `assistente.py`. A ligação com os módulos das
outras disciplinas não está implementada aqui.

## 3. Como rodar

Requisito: **Python 3.9+** (só biblioteca padrão).

```bash
# menu interativo
python assistente.py

# mostra todas as análises sem perguntar nada
python assistente.py --demo
```

Os arquivos `aparelhos.csv`, `parametros.csv` e `medidas.csv` precisam estar na mesma pasta de `calculos.py`
e `assistente.py`.

> Os textos do terminal não usam acentos de propósito, para funcionar em qualquer terminal do Windows.

## 4. Estrutura do repositório

```
README.md         este arquivo
assistente.py     menu interativo e modo --demo
calculos.py       fórmulas, validação dos dados, diagnóstico, solar
aparelhos.csv     cenário da residência (potência, horas, dias, fator de ciclo, fp, origem)
parametros.csv    tarifa, média nacional, solar, emissões (com origem e data de consulta)
medidas.csv       medidas de eficiência e premissa de redução
```

## 5. Cenário estimado (tabela de entrada)

> **Procel:** Programa Nacional de Conservação de Energia Elétrica, do governo federal. Publica o consumo médio
> dos aparelhos e concede o Selo Procel aos mais eficientes. Usado aqui como fonte de potência e consumo típicos.

Residência de exemplo: família pequena, casa com chuveiro elétrico, um ar-condicionado split e geladeira antiga.
**Os valores são estimativas justificadas, não medições.** A coluna *origem* de `aparelhos.csv` diz de onde
veio cada número. O usuário pode trocar a tabela pelos aparelhos da própria casa.

| Aparelho | Tipo | Potência (W) | Horas/dia | Dias/mês | Fator de ciclo | kWh/mês |
|---|---|---:|---:|---:|---:|---:|
| Chuveiro elétrico | uso | 5500 | 0,5 | 30 | 1,0 | 82,5 |
| Ar-condicionado split 12000 BTU | uso | 1450 | 2 | 30 | 0,6 | 52,2 |
| Geladeira 2 portas antiga | base | 150 | 24 | 30 | 0,4 | 43,2 |
| Standby (aparelhos em espera) | standby | 55 | 24 | 30 | 1,0 | 39,6 |
| Computador desktop | uso | 150 | 4 | 30 | 1,0 | 18,0 |
| Televisão LED 50" | uso | 100 | 5 | 30 | 1,0 | 15,0 |
| Iluminação LED (10 lâmpadas) | uso | 90 | 5 | 30 | 1,0 | 13,5 |
| Ventilador | uso | 60 | 6 | 30 | 1,0 | 10,8 |
| Roteador e modem | base | 12 | 24 | 30 | 1,0 | 8,6 |
| Micro-ondas | uso | 1200 | 0,2 | 30 | 1,0 | 7,2 |
| Máquina de lavar roupa | uso | 500 | 1 | 12 | 1,0 | 6,0 |
| Ferro de passar | uso | 1000 | 0,5 | 8 | 1,0 | 4,0 |
| **Total** | | | | | | **300,6** |

*Fator de ciclo:* fração do tempo em que o aparelho realmente puxa a potência (compressor da geladeira e do
ar-condicionado desliga pelo termostato). É uma **estimativa**.

## 6. Cálculos (base teórica da aula de SERS)

| Grandeza | Fórmula | Onde é usada |
|---|---|---|
| Energia | E = P × t | consumo mensal de cada aparelho (kWh) |
| Custo | R$ = kWh × tarifa | conta de luz |
| Potência ativa | P = U × I × cos φ | potência média da casa |
| Potência reativa | Q = P × tan φ | cargas indutivas (geladeira, ar-condicionado, motores) |
| Potência aparente | S² = P² + Q² | triângulo das potências |
| Fator de potência | FP = P / S | diagnóstico |

**Solar** (função `dimensionar_solar`):

```
kWh a compensar   = consumo − custo de disponibilidade (50 kWh)
potência (kWp)    = kWh a compensar ÷ 127 kWh/kWp/mês
investimento      = kWp × R$ 3.800/kWp
economia por mês  = kWh a compensar × tarifa × 0,7
payback (anos)    = investimento ÷ (economia por mês × 12)
```

## 7. Resultados do cenário

Resultados do modo `python assistente.py --demo`. Resumo:

**Diagnóstico**

| Indicador | Resultado |
|---|---|
| Consumo | 300,6 kWh/mês (R$ 255,84 com a tarifa sem impostos) |
| Em relação à média nacional (181,8 kWh/mês) | 65,4% acima |
| Maior consumo | Chuveiro elétrico, 27,4% da conta |
| Consumo base (sempre ligado) | 127 W em média, 91,4 kWh/mês, 30,4% do total |
| Standby | 39,6 kWh/mês, 13,2% do total, **acima** do teto de 12% citado pelo Procel |
| Potências médias da casa | P = 418 W, Q = 179 VAr, S = 454 VA, FP = 0,92 |

**Comparação rede × solar (alternativa renovável)**

| | Só rede | Rede + solar |
|---|---:|---:|
| Conta de luz por mês | R$ 255,84 | R$ 106,54 |
| Investimento | R$ 0,00 | R$ 7.499,46 (1,97 kWp) |
| Emissões por mês | 18,0 kg CO₂ | 13,8 kg CO₂ |
| Payback simples | — | 4,2 anos |
| Saldo em 25 anos (modelo simples) | — | R$ 37.292,41 |

**Medidas sem investir em solar** (régua para o standby, banho de 20 min, geladeira Selo Procel A):
de 300,6 para 236,7 kWh/mês, economia de **R$ 54,42/mês**. Com o consumo menor, o solar necessário cai
de 1,97 para 1,47 kWp e o investimento de R$ 7.499 para R$ 5.586.

**Leituras do resultado**

1. Antes de pensar em solar, **reduzir desperdício custa pouco e já economiza**: 21% do consumo.
2. O ganho ambiental do solar nesse cenário é **pequeno** (4,2 kg CO₂/mês evitados), porque a rede brasileira já
   tem fator de emissão baixo. O argumento forte do solar, aqui, é financeiro.
3. O standby passa do teto esperado e vale tratar.

## 8. Alternativas comparadas

| Alternativa | Custo | Viabilidade | Impacto ambiental |
|---|---|---|---|
| **Só rede elétrica** (situação atual) | Sem investimento; conta mensal sujeita a reajuste de tarifa e bandeiras | Imediata | Emissão da rede: 59,9 kg CO₂/MWh |
| **Rede + solar fotovoltaico** (renovável) | Investimento inicial; conta cai para o custo de disponibilidade e o que não é compensado | Depende de telhado, orçamento real e distribuidora | Emissão de ciclo de vida do solar de 43 g CO₂/kWh, **menor** que a rede, mas a diferença é pequena no Brasil |

## 9. Premissas, origem dos dados e limitações

As origens e datas de consulta estão em `parametros.csv`. **Todas as fontes numéricas abaixo vieram de
fontes secundárias (notícias e tabelas que citam ANEEL, EPE, MCTI, Procel) e não foram conferidas nas
fontes primárias.**

| Parâmetro | Valor | Observação |
|---|---|---|
| Tarifa | R$ 0,851/kWh | sem impostos; a conta real é maior (ICMS, PIS/COFINS, bandeiras) |
| Média nacional | 181,8 kWh/mês | EPE |
| Geração solar | 127 kWh/kWp/mês | média; varia com a região |
| Custo do solar | R$ 3.800/kWp | meio da faixa de R$ 3.400–4.200; sistemas pequenos costumam custar mais por kWp |
| Fator de economia do solar | 0,7 | **premissa conservadora, a validar** (Fio B da Lei 14.300 e custos que continuam) |
| Custo de disponibilidade | 50 kWh | bifásico (monofásico 30, trifásico 100) |
| Emissão da rede | 59,9 kg CO₂/MWh | BEN 2025 (ano-base 2024); o fator mensal do MCTI varia bastante |
| Emissão do solar | 43 g CO₂/kWh | NREL 2021 (faixa de 25 a 43) |

**Limitações**

- **O cenário é estimado, não medido.** A potência real varia por marca, modelo e uso.
- **O payback simples não considera** juros, reajuste de tarifa, degradação dos módulos, manutenção nem troca de inversor.
- **O payback sai sempre igual (4,2 anos) por construção:** custo por kWp e economia por kWp são constantes no modelo.
  Na vida real, sistemas menores custam mais por kWp e o retorno muda.
- O fator de potência de cada aparelho (coluna `fp`) é **estimado**. Em residência não há cobrança por reativo
  como na indústria (ANEEL 414, limite de 0,92); no assistente ele serve para entender as cargas indutivas.
- A tarifa sem impostos **subestima** a economia real; o valor de partida é conservador.
- A redução de cada medida de eficiência é premissa (a da geladeira e a do banho têm base; a do standby e a do ar-condicionado são **a validar**).
- O assistente não substitui orçamento de instalador, estudo da distribuidora nem laudo técnico.

## 10. Testes com usuários

- **Situação testada:** o assistente foi apresentado a familiares e amigos, sem registro individual. A impressão geral foi de que a ideia é útil e tem uso real no dia a dia. Pediram mais clareza nos dados e acharam alguns termos muito técnicos; explicamos que isso é requisito da disciplina. Também sugeriram uma interface mais amigável no futuro.
- **Próximos passos:** simplificar a linguagem para o usuário final e criar uma interface (tela ou aplicativo).

## 11. Referências

Consultadas em **nov/2026**.

- Aula de SERS: *Energia, Potência, Consumo e Demanda*, Prof. André Tritiack de Farias, FIAP, 19/03/2026.
- ANEEL, tarifas residenciais (B1) e Resolução Normativa nº 414/2010 (fator de potência mínimo de 0,92): https://www.aneel.gov.br
- ANEEL, REN 1000/2021 (custo de disponibilidade) e Lei nº 14.300/2022 (geração distribuída, Fio B).
- EPE, consumo residencial médio: https://www.epe.gov.br
- MCTI, fatores de emissão do Sistema Interligado Nacional (SIRENE) e BEN 2025 (EPE).
- Procel/Eletrobras, tabelas de consumo de eletrodomésticos: https://igce.rc.unesp.br/Home/ComissaoSupervisora-old/ConservacaodeEnergiaCICE/tabela_consumo.pdf (cópia da tabela) e https://valorfinal.com.br/tabela-potencia-aparelhos
- IDEC, cartilha de energia (consumo de geladeiras): https://idec.org.br/print/24463
- Chuveiro de 5.500 W por 30 min = 88 kWh/mês (Procel, via imprensa): https://concursosnobrasil.com/10-aparelhos-e-eletrodomesticos-que-consomem-muita-energia-veja-quais-sao/
- NREL, *Life Cycle Greenhouse Gas Emissions from Solar Photovoltaics*: https://www.nrel.gov/docs/fy13osti/56487.pdf ; NREL 2021 (43 g CO₂e/kWh, via https://skepticalscience.com/news.php?n=6109 ) ; Drawdown, solar distribuído (25,5–42,9 g CO₂e/kWh): https://drawdown.org/explorer/deploy-distributed-solar-pv
- Procel, standby de até 12% do consumo residencial (fonte secundária).
