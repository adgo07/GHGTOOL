from __future__ import annotations

from datetime import date, datetime, timezone
import unittest

from packages.core import (
    AccountingInput,
    AccountingPeriod,
    AccountingRecord,
    CalculationLine,
    CalculationResult,
    Factor,
    OfficialStatus,
    Parameter,
    ParameterType,
    PeriodType,
    RecordStatus,
    ReviewStatus,
    SettingEntry,
    Settings,
    Standard,
    ValueType,
)
from packages.core.repositories import ParameterRepository, RecordRepository, SettingsRepository, StandardRepository


NOW = datetime(2026, 9, 10, tzinfo=timezone.utc)


class MemoryStandardRepository:
    def __init__(self, standard: Standard):
        self.standard = standard

    def get(self, standard_id: str) -> Standard | None:
        return self.standard if standard_id == self.standard.standard_id else None

    def list_all(self) -> list[Standard]:
        return [self.standard]


class MemoryParameterRepository:
    def __init__(self, parameter: Parameter, factor: Factor):
        self.parameter = parameter
        self.factor = factor

    def get_parameter(self, parameter_id: str) -> Parameter | None:
        return self.parameter if parameter_id == self.parameter.parameter_id else None

    def get_factor(self, factor_id: str) -> Factor | None:
        return self.factor if factor_id == self.factor.factor_id else None

    def list_factors(self, parameter_id: str) -> list[Factor]:
        return [self.factor] if parameter_id == self.parameter.parameter_id else []


class MemoryRecordRepository:
    def __init__(self):
        self.records: dict[str, AccountingRecord] = {}

    def create(self, record: AccountingRecord) -> None:
        if record.record_id in self.records:
            raise ValueError("record IDs are immutable and cannot be overwritten")
        self.records[record.record_id] = record

    def get(self, record_id: str) -> AccountingRecord | None:
        return self.records.get(record_id)

    def list_all(self) -> list[AccountingRecord]:
        return list(self.records.values())


class MemorySettingsRepository:
    def __init__(self, settings: Settings):
        self.settings = settings

    def load(self) -> Settings:
        return self.settings

    def save(self, settings: Settings) -> None:
        self.settings = settings


class RepositoryContractTest(unittest.TestCase):
    def test_in_memory_fakes_satisfy_all_repository_contracts(self) -> None:
        standard = Standard(
            "std.carbon.2024",
            "std.carbon",
            "GB/T 32151.34-2024",
            "炭素材料生产企业",
            "2024",
            official_status=OfficialStatus.ACTIVE,
        )
        parameter = Parameter("param.lhv.ng", "fuel.ng", ParameterType.LOWER_HEATING_VALUE, "低位发热量", "GJ", "2024")
        factor = Factor(
            "factor.lhv.ng.2024",
            parameter.parameter_id,
            parameter.subject_id,
            parameter.parameter_type,
            "389.31",
            "GJ",
            "2024",
            ValueType.STANDARD_DEFAULT,
            ReviewStatus.VERIFIED,
            source_id="src.standard.2024",
        )
        standard_repo = MemoryStandardRepository(standard)
        parameter_repo = MemoryParameterRepository(parameter, factor)
        settings_repo = MemorySettingsRepository(Settings("settings.local"))

        self.assertIsInstance(standard_repo, StandardRepository)
        self.assertIs(standard_repo.get("std.carbon.2024"), standard)
        self.assertEqual(standard_repo.list_all(), [standard])
        self.assertIsInstance(parameter_repo, ParameterRepository)
        self.assertIs(parameter_repo.get_parameter("param.lhv.ng"), parameter)
        self.assertIs(parameter_repo.get_factor("factor.lhv.ng.2024"), factor)
        self.assertEqual(parameter_repo.list_factors("param.lhv.ng"), [factor])
        self.assertIsInstance(settings_repo, SettingsRepository)
        settings_repo.save(Settings("settings.local", (SettingEntry("window.width", "960"),)))
        self.assertEqual(settings_repo.load().entries[0].key, "window.width")

        accounting_input = AccountingInput(
            "input.001",
            standard.standard_id,
            AccountingPeriod(PeriodType.ANNUAL, date(2025, 1, 1), date(2025, 12, 31)),
        )
        result = CalculationResult(
            "result.001",
            standard.standard_id,
            "1.0",
            (CalculationLine("line.001", "source.energy", "CO2", "1", "tCO2"),),
            "1",
            "tCO2",
            NOW,
        )
        record = AccountingRecord("record.001", standard.standard_id, "1.0", NOW, accounting_input, result, RecordStatus.COMPLETED)
        record_repo = MemoryRecordRepository()
        self.assertIsInstance(record_repo, RecordRepository)
        record_repo.create(record)
        self.assertIs(record_repo.get("record.001"), record)
        self.assertEqual(record_repo.list_all(), [record])
        with self.assertRaises(ValueError):
            record_repo.create(record)


if __name__ == "__main__":
    unittest.main()

