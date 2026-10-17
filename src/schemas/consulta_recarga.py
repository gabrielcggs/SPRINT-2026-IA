import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Sprint 04: o validador deixou de aceitar so CG-01..CG-04 (base simulada da Sprint 03).
# Agora aceita qualquer id no formato CG-NN; quem decide se o carregador existe e a
# base de conhecimento recuperada pelo RAG, nao o schema.
PADRAO_CARREGADOR = re.compile(r"^CG-\d{2}$")


class ConsultaRecarga(BaseModel):
    resposta: str = Field(min_length=1)

    escopo: str = "goodwe_ev"

    carregador_id: str | None = None
    estado: str | None = None
    potencia_kw: float | None = None
    consumo_kwh: float | None = None
    tarifa_kwh: float | None = None
    custo_estimado: float | None = None

    # Sprint 04: citacao de fonte (ex.: "tabela_tarifaria.pdf, p. 1, seção 1 Tarifa padrao")
    fontes: list[str] = Field(default_factory=list)

    @field_validator("escopo", mode="before")
    @classmethod
    def validar_escopo(cls, value):
        if value in (None, ""):
            return "goodwe_ev"

        value = str(value).strip().lower()

        if value in {"goodwe", "ev", "recarga", "chargegrid"}:
            return "goodwe_ev"

        if value in {"fora", "fora de escopo", "out_of_scope"}:
            return "fora_escopo"

        if value in {"segurança", "seguranca", "safety", "security"}:
            return "seguranca"

        return value

    @field_validator("carregador_id")
    @classmethod
    def validar_carregador(cls, value):
        if value is None:
            return value

        value = value.upper().replace(" E ", ",")

        ids = [item.strip() for item in value.split(",")]

        if any(not PADRAO_CARREGADOR.match(item) for item in ids):
            raise ValueError("carregador_id deve seguir o formato CG-NN")

        return ", ".join(ids)

    @field_validator(
        "potencia_kw",
        "consumo_kwh",
        "tarifa_kwh",
        "custo_estimado"
    )
    @classmethod
    def validar_numeros(cls, value):
        if value is not None and value < 0:
            raise ValueError("valor numérico não pode ser negativo")

        return value
