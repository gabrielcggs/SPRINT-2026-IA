from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ConsultaRecarga(BaseModel):
    resposta: str = Field(min_length=1)
    escopo: Literal["goodwe_ev", "fora_escopo", "seguranca"]
    carregador_id: str | None = None
    estado: str | None = None
    potencia_kw: float | None = None
    consumo_kwh: float | None = None
    tarifa_kwh: float | None = None
    custo_estimado: float | None = None

    @field_validator("carregador_id")
    @classmethod
    def validar_carregador(cls, value):
        if value is None:
            return value
        permitido = {"CG-01", "CG-02", "CG-03", "CG-04"}
        if value not in permitido:
            raise ValueError("carregador fora da base simulada")
        return value

    @field_validator("potencia_kw", "consumo_kwh", "tarifa_kwh", "custo_estimado")
    @classmethod
    def validar_numeros(cls, value):
        if value is not None and value < 0:
            raise ValueError("valor numérico não pode ser negativo")
        return value
