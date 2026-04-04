"""PDF export generator — produces minimal valid PDF from finalized content."""

from datetime import UTC, datetime
from typing import Any

from deskai.domain.export.value_objects import ExportFormat, ExportResult
from deskai.ports.export_generator import ExportGenerator


class PdfExportGenerator(ExportGenerator):
    """Generate PDF exports from finalized consultation content."""

    def generate(
        self,
        consultation_id: str,
        fmt: ExportFormat,
        metadata: dict[str, Any],
        medical_history: dict[str, Any],
        summary: dict[str, Any],
        accepted_insights: list[dict[str, Any]],
    ) -> ExportResult:
        lines: list[str] = []

        lines.append("=" * 60)
        lines.append("REGISTRO DE CONSULTA MEDICA")
        lines.append("=" * 60)
        lines.append("")

        lines.append("DADOS DA CONSULTA")
        lines.append("-" * 40)
        lines.append(f"ID: {consultation_id}")
        lines.append(f"Data: {metadata.get('scheduled_date', 'N/A')}")
        lines.append(f"Especialidade: {metadata.get('specialty', 'N/A')}")
        lines.append(f"Finalizado em: {metadata.get('finalized_at', 'N/A')}")
        lines.append("")

        lines.append("HISTORIA CLINICA")
        lines.append("-" * 40)
        lines.extend(self._format_dict(medical_history))
        lines.append("")

        lines.append("RESUMO DA CONSULTA")
        lines.append("-" * 40)
        lines.extend(self._format_dict(summary))
        lines.append("")

        if accepted_insights:
            lines.append("OBSERVACOES ACEITAS")
            lines.append("-" * 40)
            for i, insight in enumerate(accepted_insights, 1):
                lines.append(f"  {i}. {insight.get('descricao', 'N/A')}")
                lines.append(f"     Categoria: {insight.get('categoria', 'N/A')}")
                lines.append(f"     Severidade: {insight.get('severidade', 'N/A')}")
                evidence = insight.get("evidencia", {})
                if evidence:
                    lines.append(f'     Evidencia: "{evidence.get("trecho", "")}"')
                lines.append("")

        lines.append("-" * 60)
        lines.append("Documento gerado por DeskAI. Revisado e aprovado pelo medico responsavel.")
        lines.append(f"Gerado em: {datetime.now(tz=UTC).isoformat()}")

        text_content = "\n".join(lines)
        pdf_bytes = self._text_to_pdf(text_content)

        return ExportResult(
            consultation_id=consultation_id,
            format=fmt,
            data=pdf_bytes,
            filename=f"consulta_{consultation_id}.pdf",
        )

    def _format_dict(self, data: dict[str, Any], indent: int = 2) -> list[str]:
        lines: list[str] = []
        prefix = " " * indent
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.extend(self._format_dict(value, indent + 2))
            elif isinstance(value, list):
                lines.append(f"{prefix}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.extend(self._format_dict(item, indent + 4))
                        lines.append("")
                    else:
                        lines.append(f"{prefix}  - {item}")
            else:
                lines.append(f"{prefix}{key}: {value}")
        return lines

    def _text_to_pdf(self, text: str) -> bytes:
        """Convert text to a minimal valid PDF without external dependencies."""
        text_lines = text.split("\n")

        def _escape(s: str) -> str:
            return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

        stream_parts = ["BT", "/F1 10 Tf"]
        y = 750
        for line in text_lines:
            if y < 50:
                break
            stream_parts.append(f"1 0 0 1 50 {y} Tm")
            stream_parts.append(f"({_escape(line)}) Tj")
            y -= 14
        stream_parts.append("ET")

        stream = "\n".join(stream_parts)
        stream_bytes = stream.encode("latin-1", errors="replace")

        objs: list[str] = []
        objs.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")
        objs.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj")
        objs.append(
            "3 0 obj\n<< /Type /Page /Parent 2 0 R "
            "/MediaBox [0 0 612 792] "
            "/Contents 4 0 R "
            "/Resources << /Font << /F1 5 0 R >> >> >>\nendobj"
        )
        objs.append(
            f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n{stream}\nendstream\nendobj"
        )
        objs.append("5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\nendobj")

        header = "%PDF-1.4\n"
        body = "\n".join(objs)
        xref_offset = len(header) + len(body) + 1

        xref = "xref\n0 6\n0000000000 65535 f \n"
        offset = len(header)
        for obj in objs:
            xref += f"{offset:010d} 00000 n \n"
            offset += len(obj) + 1

        trailer = f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF"

        return f"{header}{body}\n{xref}{trailer}".encode("latin-1", errors="replace")
