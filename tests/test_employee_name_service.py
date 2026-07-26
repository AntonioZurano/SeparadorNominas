"""Tests de reconocimiento de nombre por reglas locales."""

from __future__ import annotations

from separador_nominas.employee_name_service import recognize_page


class TestRecognizePage:
    def test_high_confidence_same_line_label(self) -> None:
        text = "Empresa Demo S.L.\nTRABAJADOR: Ana Perez Garcia\nPeriodo: Enero"
        result = recognize_page(page_index=0, page_text=text)

        assert result.confidence == "high"
        assert result.page_number == 1
        assert result.display_name == "Ana Perez Garcia"
        assert result.normalized_key == "ana perez garcia"

    def test_label_on_next_line(self) -> None:
        text = "NOMBRE Y APELLIDOS\nPedro Ruiz Martin\nIBAN ES00"
        result = recognize_page(page_index=2, page_text=text)

        assert result.confidence == "high"
        assert result.page_number == 3
        assert result.normalized_key == "pedro ruiz martin"

    def test_no_text(self) -> None:
        result = recognize_page(page_index=0, page_text="")
        assert result.confidence == "none"
        assert result.warning_code == "no_text"
        assert result.has_text is False

    def test_company_rejected(self) -> None:
        text = "TRABAJADOR: Acme Servicios S.L."
        result = recognize_page(page_index=0, page_text=text)
        assert result.confidence == "none"

    def test_ambiguous_two_people(self) -> None:
        text = (
            "TRABAJADOR: Ana Perez Garcia\n"
            "TRABAJADOR: Laura Gomez Diaz"
        )
        result = recognize_page(page_index=0, page_text=text)
        assert result.confidence == "none"
        assert result.warning_code == "ambiguous_candidates"

    def test_accent_variants_normalize(self) -> None:
        text = "PERCEPTOR: MARÍA LÓPEZ SÁNCHEZ"
        result = recognize_page(page_index=0, page_text=text)
        assert result.confidence == "high"
        assert result.normalized_key == "maria lopez sanchez"

    def test_surname_nieto_not_rejected_as_nie(self) -> None:
        text = "TRABAJADOR: Ivan Nieto Torres"
        result = recognize_page(page_index=0, page_text=text)
        assert result.confidence == "high"
        assert result.normalized_key == "ivan nieto torres"

    def test_explicit_nie_token_still_rejected(self) -> None:
        from separador_nominas.recognition_rules import contains_negative_fragment

        assert contains_negative_fragment("Titular NIE extranjero")
        assert not contains_negative_fragment("Ivan Nieto Torres")
