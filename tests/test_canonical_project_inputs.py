from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from packages.application.canonical_input_codec import (
    CanonicalInputCodecError,
    decode_canonical_input,
    encode_canonical_input,
)
from packages.application.project_workspaces import (
    AccountingUnitType,
    AccountingUnitWorkspace,
    ProjectWorkspaceService,
)
from packages.core.models import (
    AccountingPeriod,
    ActivityDataSource,
    ActivitySourceLevel,
    ElectricityAcquisitionMode,
    ElectricityAttribute,
    ElectricityProofStatus,
    ElectricityProofType,
    PeriodType,
)
from packages.core.parameter_resolution import ElectricityConsumptionDetail
from packages.persistence import (
    ProjectWorkspaceRepositoryError,
    SQLiteProjectWorkspaceRepository,
    build_all_databases,
)
from packages.standards.carbon_material import (
    ActivityDataEvidence,
    BakingInput,
    CarbonMaterialInput,
    CarbonReportingData,
    CarbonateComponent,
    CalcinationInput,
    EmissionSourceState,
    EmissionSourceStatus,
    ElectricityOutputLine,
    FGDInput,
    FuelInput,
    FuelPath,
    FuelType,
    FumeIncinerationInput,
    GraphitizationInput,
    HeatFactorMode,
    HeatInput,
    InputValue,
    MaterialBasis,
    MaterialComponentKind,
    MeasuredFactorEvidence,
    ParameterSourceKind,
    ParameterValue,
    SteamKind,
)
from packages.standards.carbon_material_normalization import (
    MaterialDataSource,
    MaterialInputLine,
    MaterialRole,
)


PERIOD = AccountingPeriod(PeriodType.ANNUAL, date(2025, 1, 1), date(2025, 12, 31))


def _measured(parameter_id: str, value: str, unit: str) -> ParameterValue:
    return ParameterValue(
        parameter_id,
        Decimal(value),
        unit,
        source_kind=ParameterSourceKind.MEASURED,
        source_id="source.lab-report",
        source_version="lab-report-2025-v2",
        source_location="检测报告第3页",
        selection_reason="采用留存的企业实测值。",
        factor_id=f"factor.{parameter_id}",
        factor_year=2025,
        evidence_ref_ids=("evidence.factor.preexisting",),
    )


def _rich_input(input_id: str = "input.canonical") -> CarbonMaterialInput:
    reporting = CarbonReportingData(
        organization_nature="有限责任公司",
        industry="炭素材料制造",
        boundary_description="主生产系统",
        activity_evidence=(
            ActivityDataEvidence(
                evidence_id="evidence.activity.fuel",
                applies_to="年度焦炭计量",
                source_ids=("CAR-SRC-FUEL-001",),
                source_reference="燃料台账第1页",
                monitoring_location="入厂计量点",
                monitoring_method="连续计量",
                instrument="地磅 A",
                accuracy="0.5级",
                recording_frequency="每日",
                acquisition_time="2025年度",
                note="复核完成",
            ),
        ),
        measured_factor_evidence=(
            MeasuredFactorEvidence(
                evidence_id="evidence.factor.fuel",
                applies_to="焦炭含碳量",
                source_ids=("CAR-SRC-FUEL-001", "CAR-SRC-PURCHASED-HEAT-001"),
                source_reference="检测报告第3页",
                sampling_method="分层取样",
                sampling_frequency="每批次",
                testing_method="实验室检测",
                testing_frequency="每批次",
                referenced_standard="检测依据标准",
                reason="采用企业实测值",
            ),
        ),
    )
    fuel_activity = InputValue(
        Decimal("12.3400"),
        "t",
        ActivityDataSource.METER,
        ActivitySourceLevel.SECONDARY,
        "燃料台账第1页",
        ("activity.ref.original",),
    )
    calcination = CalcinationInput(
        gc=InputValue("20.00", "t", ActivityDataSource.PRODUCTION_LEDGER),
        wfc=InputValue("85.250", "ratio", source_reference="检测报告 A"),
        mass_basis=MaterialBasis.RECEIVED,
        composition_basis=MaterialBasis.DRY,
        normalized_basis=MaterialBasis.RECEIVED,
        component_kind=MaterialComponentKind.TOTAL_CARBON,
        moisture_evidence=True,
        conversion_evidence=True,
        carbon_output_included_in_input=False,
        material_rows=(
            MaterialInputLine(
                "material.calcination.feed.1",
                MaterialRole.CALCINATION_FEED,
                "煅烧原料",
                "20.00",
                "85.250",
                MaterialDataSource.MEASURED,
                "4.50",
                MaterialDataSource.CHEMICAL_CALCULATION,
            ),
        ),
    )
    baking = BakingInput(
        bpm=InputValue("1.200", "t"),
        bpmfc=InputValue("90.00", "ratio"),
        mass_basis=MaterialBasis.DRY,
        fixed_carbon_component_kind=MaterialComponentKind.FIXED_CARBON,
        material_rows=(
            MaterialInputLine(
                "material.baking.filler.1",
                MaterialRole.BAKING_FILLER,
                "焙烧填充料",
                "1.200",
                "90.00",
                MaterialDataSource.MEASURED,
            ),
        ),
    )
    graphitization = GraphitizationInput(
        gpm=InputValue("2.50", "t"),
        gpmfc=InputValue("91.00", "ratio"),
        furnace_loss_included=True,
        material_rows=(
            MaterialInputLine(
                "material.graphitization.packing.1",
                MaterialRole.GRAPHITIZATION_PACKING,
                "石墨化保温料",
                "2.50",
                "91.00",
                MaterialDataSource.MEASURED,
            ),
        ),
    )
    fume = FumeIncinerationInput(
        q=InputValue("10.50", "Nm3/h"),
        qvar=InputValue("0.25", "mg/Nm3"),
        duration=InputValue("300", "d"),
        fch=_measured("parameter.fume.carbon", "0.0100", "tC/GJ"),
    )
    component = CarbonateComponent(
        amount=InputValue("0.500", "t"),
        carbonate_fraction=_measured("parameter.carbonate.fraction", "0.9850", "ratio"),
        emission_factor=_measured("parameter.carbonate.factor", "0.44", "tCO2/t"),
        conversion_rate=InputValue("0.990", "ratio"),
        carbonate_type="石灰石",
    )
    fgd = FGDInput(components=(component,), instance_id="fgd.unit.1")
    electricity = ElectricityConsumptionDetail(
        detail_id="electricity.line.1",
        enterprise_id="enterprise.canonical",
        standard_id="gbt_32151_34_2024",
        accounting_period=PERIOD,
        electricity_amount=Decimal("3.2100"),
        electricity_unit="MWh",
        acquisition_mode=ElectricityAcquisitionMode.PURCHASED,
        attribute=ElectricityAttribute.NONFOSSIL,
        proof_type=ElectricityProofType.GEC,
        proof_status=ElectricityProofStatus.VALID,
    )
    output_electricity = ElectricityOutputLine(
        "electricity.output.1",
        InputValue("0.1250", "MWh", ActivityDataSource.METER),
        factor=_measured("parameter.output.factor", "0.050", "tCO2/MWh"),
    )
    purchased_heat = HeatInput(
        line_id="heat.purchased.1",
        amount=InputValue("5.600", "GJ", ActivityDataSource.ENERGY_BILL),
        enthalpy=InputValue("2780.00", "kJ/kg"),
        factor=_measured("parameter.heat.factor", "0.1100", "tCO2/GJ"),
        unit="kg",
        steam_kind=SteamKind.SUPERHEATED,
        pressure_mpa=InputValue("1.70", "MPa"),
        temperature_c=InputValue("300.0", "C"),
        manual_enthalpy=True,
        factor_mode=HeatFactorMode.MEASURED,
        factor_source_note="企业供热检测报告",
        steam_amount_t=InputValue("1.250", "t"),
    )
    exported_heat = HeatInput(
        line_id="heat.exported.1",
        amount=InputValue("1.20", "GJ"),
        unit="GJ",
        factor_mode=HeatFactorMode.STANDARD_DEFAULT,
    )
    return CarbonMaterialInput(
        input_id=input_id,
        enterprise_id="enterprise.canonical",
        enterprise_name="炭素材料企业",
        period=PERIOD,
        boundary_confirmed=True,
        boundary_component_ids=("boundary.main", "boundary.utility"),
        source_states=(
            EmissionSourceState("CAR-SRC-FUEL-001", EmissionSourceStatus.INVOLVED),
            EmissionSourceState("CAR-SRC-FGD-001", EmissionSourceStatus.NOT_INVOLVED),
        ),
        fuel_inputs=(
            FuelInput(
                "fuel.coke.1",
                FuelPath.MASS,
                fuel_activity,
                _measured("parameter.fuel.carbon", "0.012300", "tC/t"),
                _measured("parameter.fuel.oxidation", "0.9800", "ratio"),
                _measured("parameter.fuel.lhv", "28.500", "GJ/t"),
                fuel_type=FuelType.COKE,
                fuel_label="冶金焦",
            ),
        ),
        calcinations=(calcination,),
        bakings=(baking,),
        graphitizations=(graphitization,),
        fume_incinerations=(fume,),
        fgd_units=(fgd,),
        electricity_details=(electricity,),
        exported_electricity=(output_electricity,),
        purchased_heat=(purchased_heat,),
        exported_heat=(exported_heat,),
        other_activity_present=True,
        transport_present=False,
        reporting_data=reporting,
    )


def _provenance(label: str) -> dict[str, object]:
    return {
        "schema": "ghgtool.excel.ingress_provenance.v1",
        "rows": [
            {
                "sheet": "燃料活动数据",
                "source_row": 7,
                "source_type": "METER",
                "activity": "fuel.coke.1.activity",
                "raw_lexical": "1.234E+1",
                "normalized_lexical": "12.340",
                "source_cell": "C7",
                "unit_mapping": {"source": "吨", "canonical": "t"},
                "label": label,
            },
        ],
    }


class CanonicalProjectInputTests(unittest.TestCase):
    def test_typed_codec_round_trips_all_input_shapes_and_decimal_lexemes(self) -> None:
        input_value = _rich_input()
        decoded = decode_canonical_input(encode_canonical_input(input_value))
        self.assertEqual(decoded, input_value)
        self.assertEqual(decoded.period.start, date(2025, 1, 1))
        self.assertEqual(decoded.fuel_inputs[0].activity.source_type, ActivityDataSource.METER)
        self.assertEqual(decoded.fuel_inputs[0].activity.source_level, ActivitySourceLevel.SECONDARY)
        self.assertEqual(decoded.fuel_inputs[0].activity.value.as_tuple(), Decimal("12.3400").as_tuple())
        self.assertEqual(decoded.fuel_inputs[0].carbon_content.value.as_tuple(), Decimal("0.012300").as_tuple())
        self.assertEqual(decoded.electricity_details[0].electricity_amount.as_tuple(), Decimal("3.2100").as_tuple())
        self.assertEqual(
            decoded.calcinations[0].material_rows[0].fixed_carbon_percent,
            "85.250",
        )
        self.assertIn("evidence.activity.fuel", decoded.fuel_inputs[0].activity.evidence_ref_ids)
        self.assertIn("evidence.factor.fuel", decoded.purchased_heat[0].factor.evidence_ref_ids)

    def test_codec_rejects_float_and_nonfinite_decimal_values(self) -> None:
        input_value = _rich_input()
        source_line = input_value.calcinations[0].material_rows[0]
        for invalid_value in (1.25, Decimal("NaN"), Decimal("Infinity")):
            with self.subTest(invalid_value=invalid_value):
                invalid_line = replace(source_line, mass_t=invalid_value)
                invalid_calcination = replace(
                    input_value.calcinations[0],
                    material_rows=(invalid_line,),
                )
                invalid_input = replace(
                    input_value,
                    calcination=invalid_calcination,
                    calcinations=(invalid_calcination,),
                )
                with self.assertRaises(CanonicalInputCodecError):
                    encode_canonical_input(invalid_input)

        float_tag = json.dumps({
            "codec": "ghgtool.carbon_material_input",
            "version": 1,
            "value": {"$kind": "float", "hex": "0x1.4000000000000p+0"},
        })
        with self.assertRaisesRegex(CanonicalInputCodecError, "unknown canonical value tag: float"):
            decode_canonical_input(float_tag)

        def replace_first_decimal(node: object, lexical: str) -> bool:
            if isinstance(node, dict):
                if node.get("$kind") == "decimal":
                    node["value"] = lexical
                    return True
                for child in node.values():
                    if replace_first_decimal(child, lexical):
                        return True
            elif isinstance(node, list):
                for child in node:
                    if replace_first_decimal(child, lexical):
                        return True
            return False

        for lexical in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(decimal_tag=lexical):
                document = json.loads(encode_canonical_input(input_value))
                self.assertTrue(replace_first_decimal(document, lexical))
                with self.assertRaisesRegex(CanonicalInputCodecError, "Decimal values must be finite"):
                    decode_canonical_input(json.dumps(document))

    def test_codec_rejects_unknown_dynamic_types(self) -> None:
        payload = json.dumps({
            "codec": "ghgtool.carbon_material_input",
            "version": 1,
            "value": {"$kind": "dataclass", "type": "os.system", "fields": {}},
        })
        with self.assertRaisesRegex(CanonicalInputCodecError, "unknown dataclass type"):
            decode_canonical_input(payload)

    def test_001_and_002_databases_upgrade_without_losing_projects_or_links_schema(self) -> None:
        migration_directory = Path(__file__).resolve().parents[1] / "migrations" / "projects"
        migration_files = sorted(migration_directory.glob("*.sql"))
        for starting_version in (1, 2):
            with self.subTest(starting_version=starting_version), tempfile.TemporaryDirectory() as directory:
                database = Path(directory) / "projects.sqlite"
                connection = sqlite3.connect(database)
                try:
                    for migration in migration_files:
                        version = int(migration.name.split("_", 1)[0])
                        if version > starting_version:
                            continue
                        connection.executescript(migration.read_text(encoding="utf-8"))
                        connection.execute(
                            "INSERT INTO schema_migrations(version,name,applied_at) VALUES(?,?,?)",
                            (version, migration.stem.split("_", 1)[1], "2026-10-01T00:00:00+00:00"),
                        )
                    connection.execute(
                        "INSERT INTO projects(project_id,name,active_unit_id,created_at,updated_at) VALUES(?,?,?,?,?)",
                        ("project.legacy", "旧项目", "unit.legacy", "created", "updated"),
                    )
                    connection.execute(
                        "INSERT INTO accounting_units(unit_id,project_id,unit_name,unit_type,position,form_state_json,"
                        "result_snapshot_json,record_ids_json,input_fingerprint) VALUES(?,?,?,?,?,?,?,?,?)",
                        ("unit.legacy", "project.legacy", "全厂", "WHOLE_SITE", 0, '{"legacy":"kept"}', None, "[]", None),
                    )
                    connection.commit()
                finally:
                    connection.close()

                repository = SQLiteProjectWorkspaceRepository(database)
                restored = repository.get("project.legacy")
                self.assertIsNotNone(restored)
                assert restored is not None
                self.assertEqual(restored.units[0].form_state, {"legacy": "kept"})
                self.assertIsNone(restored.units[0].canonical_input)
                self.assertIsNone(restored.units[0].ingress_provenance)
                connection = sqlite3.connect(database)
                try:
                    self.assertEqual(
                        connection.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall(),
                        [(1,), (2,), (3,)],
                    )
                    self.assertEqual(
                        connection.execute("SELECT COUNT(*) FROM pending_record_links").fetchone()[0],
                        0,
                    )
                    columns = {row[1] for row in connection.execute("PRAGMA table_info(accounting_units)")}
                    self.assertIn("canonical_input_json", columns)
                    self.assertIn("ingress_provenance_json", columns)
                finally:
                    connection.close()

    def test_project_save_restarts_with_canonical_input_and_never_creates_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = build_all_databases(directory)
            service = ProjectWorkspaceService(SQLiteProjectWorkspaceRepository(paths["projects"]))
            workspace = service.new_workspace("Excel正式导入项目")
            unit = replace(
                workspace.units[0],
                canonical_input=_rich_input(),
                ingress_provenance=_provenance("第一版来源"),
            )
            workspace = replace(workspace, units=(unit,))
            service.save(workspace)

            restarted = SQLiteProjectWorkspaceRepository(paths["projects"])
            loaded = restarted.get(workspace.project_id)
            self.assertEqual(loaded, workspace)
            assert loaded is not None
            self.assertEqual(loaded.units[0].ingress_provenance, _provenance("第一版来源"))
            records = sqlite3.connect(paths["records"])
            try:
                self.assertEqual(records.execute("SELECT COUNT(*) FROM accounting_records").fetchone()[0], 0)
            finally:
                records.close()
            self.assertNotEqual(workspace.units[0].unit_id, service.new_workspace().units[0].unit_id)

    def test_corrupt_canonical_or_provenance_json_is_reported_not_blank(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "projects.sqlite"
            repository = SQLiteProjectWorkspaceRepository(database)
            workspace = ProjectWorkspaceService.new_workspace("损坏项目")
            workspace = replace(
                workspace,
                units=(replace(workspace.units[0], canonical_input=_rich_input(), ingress_provenance=_provenance("原始")),),
            )
            repository.save(workspace)
            for column, bad_payload in (
                ("canonical_input_json", "not-json"),
                ("ingress_provenance_json", "[]"),
            ):
                with self.subTest(column=column):
                    connection = sqlite3.connect(database)
                    try:
                        connection.execute(
                            f"UPDATE accounting_units SET {column}=? WHERE unit_id=?",
                            (bad_payload, workspace.units[0].unit_id),
                        )
                        connection.commit()
                    finally:
                        connection.close()
                    with self.assertRaises(ProjectWorkspaceRepositoryError):
                        repository.get(workspace.project_id)
                    with self.assertRaises(ProjectWorkspaceRepositoryError):
                        repository.list_all()
                    repository.save(workspace)

    def test_provenance_rejects_floats_on_save_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "projects.sqlite"
            repository = SQLiteProjectWorkspaceRepository(database)
            workspace = ProjectWorkspaceService.new_workspace("来源数值词法项目")

            finite_float = _provenance("float")
            finite_float["rows"][0]["raw_lexical"] = 1.25
            invalid_workspace = replace(
                workspace,
                units=(replace(workspace.units[0], ingress_provenance=finite_float),),
            )
            with self.assertRaises(ProjectWorkspaceRepositoryError):
                repository.save(invalid_workspace)

            valid_workspace = replace(
                workspace,
                units=(replace(workspace.units[0], ingress_provenance=_provenance("valid")),),
            )
            repository.save(valid_workspace)
            for bad_json in ('{"raw_value":1.25}', '{"raw_value":NaN}', '{"raw_value":Infinity}'):
                with self.subTest(bad_json=bad_json):
                    connection = sqlite3.connect(database)
                    try:
                        connection.execute(
                            "UPDATE accounting_units SET ingress_provenance_json=? WHERE unit_id=?",
                            (bad_json, workspace.units[0].unit_id),
                        )
                        connection.commit()
                    finally:
                        connection.close()
                    with self.assertRaises(ProjectWorkspaceRepositoryError):
                        repository.get(workspace.project_id)
                    repository.save(valid_workspace)

    def test_pending_recovery_preserves_canonical_input_and_latest_saved_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "projects.sqlite"
            repository = SQLiteProjectWorkspaceRepository(database)
            initial = ProjectWorkspaceService.new_workspace("恢复项目")
            latest_input = _rich_input("input.latest")
            pending_unit = replace(
                initial.units[0],
                canonical_input=_rich_input("input.pending"),
                ingress_provenance=_provenance("待恢复快照"),
                result_snapshot={"record_id": "record.pending", "total": "3.10"},
                record_ids=("record.pending",),
                input_fingerprint="fingerprint.pending",
            )
            pending = replace(initial, units=(pending_unit,))
            original_save = repository.save
            repository.save = lambda _workspace: (_ for _ in ()).throw(
                ProjectWorkspaceRepositoryError("simulated project write failure")
            )  # type: ignore[method-assign]
            with self.assertRaisesRegex(ProjectWorkspaceRepositoryError, "queued for recovery"):
                repository.save_after_record(pending, "record.pending")
            repository.save = original_save  # type: ignore[method-assign]

            latest_unit = replace(
                initial.units[0],
                canonical_input=latest_input,
                ingress_provenance=_provenance("最新已保存来源"),
                form_state={"latest": "kept"},
            )
            latest = replace(initial, units=(latest_unit,))
            repository.save(latest)
            recovered = SQLiteProjectWorkspaceRepository(database).get(initial.project_id)
            self.assertIsNotNone(recovered)
            assert recovered is not None
            self.assertEqual(recovered.units[0].canonical_input, latest_input)
            self.assertEqual(recovered.units[0].ingress_provenance, _provenance("最新已保存来源"))
            self.assertEqual(recovered.units[0].form_state, {"latest": "kept"})
            self.assertEqual(recovered.units[0].record_ids, ("record.pending",))
            self.assertEqual(recovered.units[0].result_snapshot, {"record_id": "record.pending", "total": "3.10"})

    def test_pending_recovery_uses_full_canonical_snapshot_if_project_row_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "projects.sqlite"
            repository = SQLiteProjectWorkspaceRepository(database)
            initial = ProjectWorkspaceService.new_workspace("待恢复项目")
            linked = replace(
                initial,
                units=(replace(
                    initial.units[0],
                    canonical_input=_rich_input(),
                    ingress_provenance=_provenance("挂起来源"),
                    result_snapshot={"record_id": "record.full-recovery", "total": "1"},
                    record_ids=("record.full-recovery",),
                ),),
            )
            original_save = repository.save
            repository.save = lambda _workspace: (_ for _ in ()).throw(
                ProjectWorkspaceRepositoryError("simulated project write failure")
            )  # type: ignore[method-assign]
            with self.assertRaises(ProjectWorkspaceRepositoryError):
                repository.save_after_record(linked, "record.full-recovery")
            repository.save = original_save  # type: ignore[method-assign]

            recovered = SQLiteProjectWorkspaceRepository(database).get(initial.project_id)
            self.assertIsNotNone(recovered)
            assert recovered is not None
            self.assertEqual(recovered.units[0].canonical_input, linked.units[0].canonical_input)
            self.assertEqual(recovered.units[0].ingress_provenance, linked.units[0].ingress_provenance)


if __name__ == "__main__":
    unittest.main()