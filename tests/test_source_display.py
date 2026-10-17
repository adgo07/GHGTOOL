from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
import unittest

from packages.application.source_display import (
    electricity_factor_short_labels,
    format_source_reference,
    strip_source_page_numbers,
)


class SourceDisplayTests(unittest.TestCase):
    def test_short_source_prefers_structured_locator_and_keeps_original_evidence(self):
        frozen_location = (
            "GB/T 32151.34—2024 第5.2.6.1条、附录D.1.1；"
            "PDF第30页；印刷页22"
        )

        short = format_source_reference(frozen_location, "青舟标准目录")

        self.assertEqual(
            short,
            "GB/T32151.34—2024 第5.2.6.1条；附录D.1.1",
        )
        self.assertNotIn("PDF", short)
        self.assertNotIn("印刷页", short)
        self.assertEqual(frozen_location, (
            "GB/T 32151.34—2024 第5.2.6.1条、附录D.1.1；"
            "PDF第30页；印刷页22"
        ))

    def test_missing_structured_locator_falls_back_to_source_name(self):
        self.assertEqual(
            format_source_reference("PDF第30页；印刷页22", "GB/T 32151.34—2024 官方文本"),
            "GB/T 32151.34—2024 官方文本",
        )

    def test_explanatory_source_notes_hide_only_pdf_and_printed_pages(self):
        frozen_note = (
            "官方原文外置。C.4定位：PDF第27～28页、印刷页19～20；"
            "C.5定位：PDF第29页、印刷页21。完整蒸汽表由版本化Calculator负责。"
        )

        visible = strip_source_page_numbers(frozen_note)

        self.assertEqual(visible, "官方原文外置。完整蒸汽表由版本化Calculator负责")
        self.assertIn("PDF第27～28页", frozen_note)
        self.assertEqual(
            format_source_reference("", "标准目录", table_number="C.4"),
            "C.4",
        )

    def test_electricity_labels_remove_table_prefix_and_disambiguate_years(self):
        def option(year: int, value: str):
            return SimpleNamespace(
                label="表1 · 全国电力平均排放因子 2025年",
                table_number="表1",
                source_document_name="电力排放因子公告",
                factor=SimpleNamespace(
                    factor_year=year,
                    value=Decimal(value),
                    unit="tCO2/MWh",
                ),
            )

        labels = electricity_factor_short_labels((option(2023, "0.5703"), option(2024, "0.5366")))

        self.assertEqual(len(labels), 2)
        self.assertTrue(all("表1" not in label for label in labels))
        self.assertIn("0.5703 tCO2/MWh", labels[0])
        self.assertIn("（2023年）", labels[0])
        self.assertIn("0.5366 tCO2/MWh", labels[1])
        self.assertIn("（2024年）", labels[1])


if __name__ == "__main__":
    unittest.main()
