"""Categorias, regras de classificacao e normalizacao das descricoes."""
import re
import unicodedata

import pandas as pd

A_CLASSIFICAR = "A classificar"
ENTRE_CONTAS = "Entre contas próprias"
CARTAO_INTER = "Cartão Inter (fatura sem detalhe)"
FATURA_DETALHADA = "Pagamento de fatura detalhada"

CATEGORIAS_PADRAO = [
    ("Mercado", "despesa"),
    ("Alimentação fora", "despesa"),
    ("Transporte", "despesa"),
    ("Veículo", "despesa"),
    ("Saúde", "despesa"),
    ("Farmácia", "despesa"),
    ("Moradia", "despesa"),
    ("Energia", "despesa"),
    ("Internet e TV", "despesa"),
    ("Telefone", "despesa"),
    ("Educação", "despesa"),
    ("Doações", "despesa"),
    ("Compras online", "despesa"),
    ("Assinaturas", "despesa"),
    ("Lazer e esporte", "despesa"),
    ("Vestuário e beleza", "despesa"),
    ("Pet", "despesa"),
    ("Viagem", "despesa"),
    ("Seguros", "despesa"),
    ("Impostos e taxas", "despesa"),
    ("Família", "despesa"),
    ("Saques", "despesa"),
    ("Cartão Nubank", "despesa"),
    ("Cartão Itaú", "despesa"),
    (CARTAO_INTER, "despesa"),
    ("Outros", "despesa"),
    ("Salário", "receita"),
    ("Outras receitas", "receita"),
    (ENTRE_CONTAS, "transferencia"),
    ("Investimentos", "transferencia"),
    (FATURA_DETALHADA, "transferencia"),
]

# (texto contido na descricao normalizada, categoria). Vence o padrao mais longo.
REGRAS_PADRAO = [
    ("SUPERMERC", "Mercado"),
    ("ATACADAO", "Mercado"),
    ("BIG BOM", "Mercado"),
    ("SAVEGNAGO", "Mercado"),
    ("ROFATTO", "Mercado"),
    ("PANIF", "Alimentação fora"),
    ("PIZZARIA", "Alimentação fora"),
    ("RESTAURANTE", "Alimentação fora"),
    ("ROTISSERIE", "Alimentação fora"),
    ("CHURRASCARIA", "Alimentação fora"),
    ("PASTELARIA", "Alimentação fora"),
    ("ESPETINHO", "Alimentação fora"),
    ("LANCHONE", "Alimentação fora"),
    ("SORVE", "Alimentação fora"),
    ("ESKIMO", "Alimentação fora"),
    ("MR MIX", "Alimentação fora"),
    ("CASA DE SUCOS", "Alimentação fora"),
    ("IFOOD", "Alimentação fora"),
    ("ZAMP", "Alimentação fora"),
    ("99* ", "Transporte"),
    ("*99 RIDE", "Transporte"),
    ("99APP", "Transporte"),
    ("99 TECNOLOGIA", "Transporte"),
    ("UBIZ CAR", "Transporte"),
    ("UBER *", "Transporte"),
    ("UBER*", "Transporte"),
    ("POSTO", "Veículo"),
    ("MECANICA", "Veículo"),
    ("AUTO PECAS", "Veículo"),
    ("PECAS PARA VEICULOS", "Veículo"),
    ("PNEU", "Veículo"),
    ("UNIMED", "Saúde"),
    ("SERVICOS MEDICOS", "Saúde"),
    ("RDSAUDE", "Farmácia"),
    ("RD SAUDE", "Farmácia"),
    ("RAIA", "Farmácia"),
    ("DROGA", "Farmácia"),
    ("COMPANHIA DE IMOVEL", "Moradia"),
    ("ELEKTRO", "Energia"),
    ("NET SERVI", "Internet e TV"),
    ("VIVO", "Telefone"),
    ("TELEFONICA", "Telefone"),
    ("TIM*", "Telefone"),
    ("CLARO", "Telefone"),
    ("EDUCACAO", "Educação"),
    ("ESCOTEIRO", "Educação"),
    ("PAPELARIA", "Educação"),
    ("PAROQUIA", "Doações"),
    ("DIOCESE", "Doações"),
    ("AMAZON", "Compras online"),
    ("MERCADOLIVRE", "Compras online"),
    ("SHOPEE", "Compras online"),
    ("MAGALU", "Compras online"),
    ("AMERICANAS", "Compras online"),
    ("AMAZONPRIME", "Assinaturas"),
    ("DISNEY PLUS", "Assinaturas"),
    ("NETFLIX", "Assinaturas"),
    ("SPOTIFY", "Assinaturas"),
    ("ACADEMIA", "Lazer e esporte"),
    ("RI HAPPY", "Lazer e esporte"),
    ("BILHETERIA", "Lazer e esporte"),
    ("MODA INT", "Vestuário e beleza"),
    ("SOBRANCELHAS", "Vestuário e beleza"),
    ("PETZ", "Pet"),
    ("AZUL WE", "Viagem"),
    ("LATAM AIR", "Viagem"),
    ("PORTO S COMP DE S GERAIS", "Seguros"),
    ("SEFAZ", "Impostos e taxas"),
    ("DARF", "Impostos e taxas"),
    ("SERVICO REGISTRAL", "Impostos e taxas"),
    ("SAQUE", "Saques"),
    ("NU PAGAMENTOS", "Cartão Nubank"),
    ("ITAU UNIBANCO", "Cartão Itaú"),
    ("FATURA CARTAO INTER", CARTAO_INTER),
    ("PAGAMENTO FATURA", CARTAO_INTER),
    ("SALARIO RECEBIDO", "Salário"),
    ("ACTIVTRADES", "Investimentos"),
]

_RE_HORA = re.compile(r"\s*\d{2}[A-Z]{3} \d{2}H\d{2}MIN.*")
_RE_PARCELA = re.compile(r"\s*\(PARCELA \d+ DE \d+\)")


def norm(texto: str | None) -> str:
    """Maiusculas, sem acento e com espacos colapsados."""
    texto = unicodedata.normalize("NFKD", texto if isinstance(texto, str) else "")  # None/NaN -> ""
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.upper().split())


def base(tipo: str | None, descricao: str | None, origem: str) -> str:
    """Nome do favorecido sem data/hora, cidade e parcela, para agrupar lancamentos iguais."""
    d = norm(descricao) and descricao.strip() or (tipo if isinstance(tipo, str) else "")
    if origem == "conta" and "DEBITO" in norm(tipo):
        d = re.split(r"\s{2,}", d)[0]  # compra no debito vem como 'loja   cidade   pais'
    return _RE_PARCELA.sub("", _RE_HORA.sub("", norm(d)))


def classificar(
    df: pd.DataFrame, regras: pd.DataFrame, categorias: pd.DataFrame, faturas: pd.DataFrame
) -> pd.DataFrame:
    """Acrescenta as colunas base, categoria e fluxo ('entrada', 'saida' ou 'transferencia')."""
    tipos = dict(zip(categorias["nome"], categorias["tipo"]))
    exatas = {(r.padrao, r.sinal): r.categoria for r in regras.itertuples() if r.modo == "exata"}
    contem = sorted(
        ((norm(r.padrao), r.sinal, r.categoria) for r in regras.itertuples() if r.modo == "contem"),
        key=lambda r: -len(r[0]),
    )
    fats = [(pd.Timestamp(f.vencimento), round(f.total, 2)) for f in faturas.itertuples()]

    def compativel(cat: str, t) -> bool:
        tipo_cat = tipos.get(cat)
        if tipo_cat == "despesa" and t.valor > 0:
            # entrada so recebe categoria de despesa se for estorno/devolucao
            return t.origem == "cartao" or "DEVOLVIDO" in norm(t.tipo)
        return not (tipo_cat == "receita" and t.valor < 0)

    bases, cats, fluxos = [], [], []
    for t in df.itertuples():
        b = base(t.tipo, t.descricao, t.origem)
        sinal = "+" if t.valor > 0 else "-"
        cat = t.categoria_manual if isinstance(t.categoria_manual, str) else None
        if not cat:
            cat = exatas.get((b, sinal)) or exatas.get((b, ""))
            if not cat:
                texto = f"{norm(t.tipo)} {norm(t.descricao)}"
                cat = next(
                    (c for p, s, c in contem if p in texto and s in ("", sinal) and compativel(c, t)),
                    A_CLASSIFICAR,
                )
            # pagamento de fatura cujas compras foram importadas: vira transferencia
            if cat == CARTAO_INTER and any(
                abs(t.valor + total) < 0.01 and abs((t.data - venc).days) <= 7 for venc, total in fats
            ):
                cat = FATURA_DETALHADA
        tipo_cat = tipos.get(cat)
        if tipo_cat == "transferencia":
            fluxo = "transferencia"
        elif tipo_cat == "despesa" or (tipo_cat != "receita" and (t.valor < 0 or t.origem == "cartao")):
            fluxo = "saida"
        else:
            fluxo = "entrada"
        bases.append(b)
        cats.append(cat)
        fluxos.append(fluxo)
    return df.assign(base=bases, categoria=cats, fluxo=fluxos)
