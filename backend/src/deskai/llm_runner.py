"""LangChain runner for Docker Model Runner (OpenAI-compatible endpoint).

Connects to a local model served by Docker Model Runner and sends
a medical-scribe chat prompt for testing the AI summarization pipeline.

Environment variables (loaded from .env):
    MODEL_RUNNER_BASE_URL  — OpenAI-compatible base URL
    MODEL_RUNNER_MODEL     — Model identifier (e.g. ai/mistral-small3.1)
"""

from __future__ import annotations

import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


def build_llm() -> ChatOpenAI:
    """Create a ChatOpenAI instance pointing at Docker Model Runner."""
    base_url = os.environ.get(
        "MODEL_RUNNER_BASE_URL",
        "http://host.docker.internal:12434/engines/llama.cpp/v1",
    )
    model = os.environ.get("MODEL_RUNNER_MODEL", "ai/mistral-small3.1")

    return ChatOpenAI(
        base_url=base_url,
        model=model,
        api_key="not-needed",  # Docker Model Runner does not require a key
        temperature=0.2,
    )


def build_prompt() -> ChatPromptTemplate:
    """Build a medical scribe summarization prompt (pt-BR).

    The system message enforces the 'report only' rule: summarize
    what was said, never diagnose or interpret.
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Voce e um assistente de transcricao medica para medicos brasileiros. "
                    "Sua funcao e APENAS relatar o que foi dito durante a consulta. "
                    "Nunca interprete, nunca sugira diagnosticos, nunca inclua codigos CID. "
                    "Resuma de forma objetiva em portugues brasileiro (pt-BR). "
                    "Se alguma parte estiver incerta, sinalize como '[trecho incerto]'."
                ),
            ),
            (
                "human",
                (
                    "Resuma as seguintes anotacoes de consulta de forma estruturada:\n\n"
                    "{consultation_notes}"
                ),
            ),
        ]
    )


def main() -> None:
    """Run a test prompt against Docker Model Runner."""
    llm = build_llm()
    prompt = build_prompt()
    chain = prompt | llm

    sample_notes = (
        "Paciente relata dor de cabeca frequente ha duas semanas, "
        "principalmente no periodo da tarde. Nega febre ou nauseas. "
        "Menciona que esta sob estresse no trabalho. "
        "Medico solicita exames de sangue e orienta retorno em 15 dias."
    )

    print(f"Model:    {llm.model_name}")
    print(f"Endpoint: {llm.openai_api_base}")
    print("-" * 60)

    response = chain.invoke({"consultation_notes": sample_notes})
    print(response.content)


if __name__ == "__main__":
    main()
