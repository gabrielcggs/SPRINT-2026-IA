from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ConsultaRecarga(BaseModel):
    resposta: str = Field(min_length=1)

    escopo: str = "goodwe_ev"

    carregador_id: str | None = None
    estado: str | None = None
    potencia_kw: float | None = None
    consumo_kwh: float | None = None
    tarifa_kwh: float | None = None
    custo_estimado: float | None = None

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

        permitido = {"CG-01", "CG-02", "CG-03", "CG-04"}

        value = value.upper().replace(" E ", ",")

        ids = [item.strip() for item in value.split(",")]

        if any(item not in permitido for item in ids):
            raise ValueError("carregador fora da base simulada")

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
