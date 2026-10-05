"""Banco SQLite local (financas.db) com transacoes, categorias, regras e programados."""
import os
import sqlite3
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_DB = Path(os.environ.get("FINANCAS_DB", RAIZ / "financas.db"))
PASTA_EXTRATO = RAIZ / "extrato"
PASTA_FATURAS = RAIZ / "faturas-cartao"

SCHEMA = """
CREATE TABLE IF NOT EXISTS transacoes (
    id TEXT PRIMARY KEY,
    origem TEXT NOT NULL,          -- 'conta' ou 'cartao'
    data TEXT NOT NULL,            -- data do lancamento / da compra
    mes_ref TEXT NOT NULL,         -- mes em que o dinheiro sai da conta (cartao: mes do vencimento)
    tipo TEXT,
    descricao TEXT,
    valor REAL NOT NULL,           -- negativo = saida, positivo = entrada
    cartao TEXT,
    parcela TEXT,                  -- 'atual/total'
    fatura_venc TEXT,
    categoria_manual TEXT,
    arquivo TEXT
);
CREATE TABLE IF NOT EXISTS categorias (
    nome TEXT PRIMARY KEY,
    tipo TEXT NOT NULL,            -- 'despesa', 'receita' ou 'transferencia'
    meta REAL                      -- meta mensal opcional (R$)
);
CREATE TABLE IF NOT EXISTS regras (
    padrao TEXT NOT NULL,
    modo TEXT NOT NULL,            -- 'contem' ou 'exata'
    sinal TEXT NOT NULL DEFAULT '',-- '', '+' ou '-'
    categoria TEXT NOT NULL,
    PRIMARY KEY (padrao, modo, sinal)
);
CREATE TABLE IF NOT EXISTS programados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ativo INTEGER NOT NULL DEFAULT 1,
    descricao TEXT NOT NULL,
    tipo TEXT NOT NULL,            -- 'despesa' ou 'receita'
    categoria TEXT,
    valor REAL NOT NULL,
    frequencia TEXT NOT NULL,      -- 'mensal', 'anual' ou 'unica'
    dia INTEGER,
    inicio TEXT NOT NULL,
    fim TEXT,
    padrao TEXT                    -- texto para localizar o lancamento realizado
);
CREATE TABLE IF NOT EXISTS faturas (
    vencimento TEXT PRIMARY KEY,
    total REAL NOT NULL,
    arquivo TEXT
);
CREATE TABLE IF NOT EXISTS meta (chave TEXT PRIMARY KEY, valor TEXT);
"""


def conectar(caminho: Path | str = CAMINHO_DB) -> sqlite3.Connection:
    from . import categorias

    con = sqlite3.connect(caminho)
    con.executescript(SCHEMA)
    if not con.execute("SELECT 1 FROM categorias LIMIT 1").fetchone():
        con.executemany("INSERT INTO categorias VALUES (?, ?, NULL)", categorias.CATEGORIAS_PADRAO)
        con.executemany(
            "INSERT OR IGNORE INTO regras VALUES (?, 'contem', '', ?)", categorias.REGRAS_PADRAO
        )
        con.commit()
    return con


def tabela(con: sqlite3.Connection, nome: str) -> pd.DataFrame:
    return pd.read_sql_query(f"SELECT * FROM {nome}", con)


def ler_meta(con: sqlite3.Connection, chave: str) -> str | None:
    linha = con.execute("SELECT valor FROM meta WHERE chave = ?", (chave,)).fetchone()
    return linha[0] if linha else None


def gravar_meta(con: sqlite3.Connection, chave: str, valor: str) -> None:
    con.execute("INSERT OR REPLACE INTO meta VALUES (?, ?)", (chave, valor))
