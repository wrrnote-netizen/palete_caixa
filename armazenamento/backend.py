"""
Seleciona o backend de armazenamento das soluções.

Variável de ambiente ``ARMAZENAMENTO`` (também lida de db_palete_caixa.env):
    local (padrão) : pasta local do projeto (armazenamento/local.py)
    s3             : bucket S3 da AWS (armazenamento/s3.py)

O boto3 só é importado quando o backend s3 é escolhido.
"""

import os

from dotenv import load_dotenv

load_dotenv("db_palete_caixa.env")

TIPO = os.getenv("ARMAZENAMENTO", "local").strip().lower()

if TIPO == "s3":
    from armazenamento.s3 import salvar_solucao, listar_solucoes, baixar_imagem, baixar_metadata
    NOME = "S3"
elif TIPO == "local":
    from armazenamento.local import salvar_solucao, listar_solucoes, baixar_imagem, baixar_metadata
    NOME = "pasta local"
else:
    raise ValueError(f"ARMAZENAMENTO inválido: {TIPO!r} (use 'local' ou 's3').")

__all__ = ["salvar_solucao", "listar_solucoes", "baixar_imagem", "baixar_metadata", "NOME", "TIPO"]
