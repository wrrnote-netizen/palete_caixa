"""
Módulo de armazenamento em pasta local (substitui o S3 sem depender da AWS).

Mesma API e mesma estrutura do módulo s3.py, usando diretórios:
    {raiz}/{nome_usuario}/{slug_pedido}_{timestamp}/solucoes.png
    {raiz}/{nome_usuario}/{slug_pedido}_{timestamp}/metadata.json

A raiz é a pasta ``solucoes_salvas`` do projeto, ou o caminho definido na
variável de ambiente ``ARMAZENAMENTO_DIR`` (caminhos relativos partem da raiz
do projeto; caminhos absolutos são usados como estão).
"""

import json
import os
import re
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parent.parent

# Caminhos relativos em ARMAZENAMENTO_DIR são resolvidos a partir da raiz do
# projeto (não do diretório de execução), para funcionar em qualquer máquina.
RAIZ = (RAIZ_PROJETO / (os.getenv("ARMAZENAMENTO_DIR") or "solucoes_salvas")).resolve()


def _nome_seguro(nome: str) -> str:
    """Valida um componente de caminho, impedindo '..', separadores e vazios."""
    if not nome or nome in {".", ".."} or not re.fullmatch(r"[\w\-.@ ]+", nome):
        raise ValueError(f"Nome inválido para armazenamento: {nome!r}")
    return nome


def _pasta(nome_usuario: str, prefixo: str) -> Path:
    return RAIZ / _nome_seguro(nome_usuario) / _nome_seguro(prefixo)


# ─── Escrita ──────────────────────────────────────────────────────────────────

def salvar_solucao(nome_usuario: str, prefixo: str, img_bytes: bytes, meta: dict) -> str:
    """
    Grava a imagem (bytes PNG) e o metadata.json na pasta local.

    Retorno
    -------
    Caminho da pasta da solução (relativo à raiz de armazenamento).
    """
    pasta = _pasta(nome_usuario, prefixo)
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "solucoes.png").write_bytes(img_bytes)
    (pasta / "metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return f"{nome_usuario}/{prefixo}"


# ─── Leitura ──────────────────────────────────────────────────────────────────

def listar_solucoes(nome_usuario: str) -> list:
    """Lista prefixos de soluções de um usuário em ordem decrescente."""
    pasta_usuario = RAIZ / _nome_seguro(nome_usuario)
    if not pasta_usuario.is_dir():
        return []
    return sorted((p.name for p in pasta_usuario.iterdir() if p.is_dir()), reverse=True)


def baixar_imagem(nome_usuario: str, prefixo: str) -> bytes | None:
    """Retorna os bytes da imagem PNG. Retorna None se não encontrada."""
    arquivo = _pasta(nome_usuario, prefixo) / "solucoes.png"
    return arquivo.read_bytes() if arquivo.is_file() else None


def baixar_metadata(nome_usuario: str, prefixo: str) -> dict | None:
    """Retorna o dict de metadados. Retorna None se não encontrado ou inválido."""
    arquivo = _pasta(nome_usuario, prefixo) / "metadata.json"
    try:
        return json.loads(arquivo.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
