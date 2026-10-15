"""Independent asset coverage checks for A; no production adoption."""
import ast
import hashlib
import json
import unittest
from pathlib import Path
from decimal import Decimal


ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"data-source/carbon_accounting/business-rules"
PLAN=ROOT/"docs/architecture/business-rules/APPROVED_IMPLEMENTATION_V1_2.md"

class CandidateAssetCoverageTests(unittest.TestCase):
    def documents(self):
        paths=(SOURCE/"common/gbt_32150_2025.json",SOURCE/"standards/gbt_32151_34_2024.json",SOURCE/"software_policy.json")
        self.assertTrue(all(p.is_file() for p in paths), "三份候选Canonical资产必须齐全")
        return [json.loads(p.read_text(encoding="utf-8"),parse_float=Decimal) for p in paths]

    def test_approved_plan_bytes_remain_identical(self):
        self.assertEqual(hashlib.sha256(PLAN.read_bytes()).hexdigest(),"98abf84ea7f7af3887d60c3c1e128c272d73ccbf73892d76581ad1771bfad876")

    def test_business_policies_link_existing_mapping_without_internal_mirrors(self):
        documents=self.documents()
        fields=[f for d in documents for f in d['fields']]
        self.assertTrue(fields)
        self.assertEqual(documents[2]['fields'],[], '软件内部属性不是长期业务政策')
        mapping=(ROOT/'specs/carbon_accounting/GB_T_32151_34_2024_MAPPING.md').read_text(encoding='utf-8')
        for field in fields:
            with self.subTest(field=field['id']):
                self.assertFalse(field['id'].startswith('domain.'))
                self.assertTrue(field['mapping_refs'])
                for reference in field['mapping_refs']:self.assertIn('`'+reference+'`',mapping)
                self.assertTrue(all(p['binding']=='business:'+field['id'] for p in field['channel_projections']))
                self.assertTrue(field['basis'])

    def test_default_review_is_business_summary_and_matrix_is_developer_only(self):
        from packages.application.business_rules_candidate import load_bundle
        paths=(SOURCE/'common/gbt_32150_2025.json',SOURCE/'standards/gbt_32151_34_2024.json',SOURCE/'software_policy.json')
        bundle=load_bundle(paths)
        review=bundle.review_rows()
        defined={f['id'] for d in self.documents() for f in d['fields']}
        self.assertEqual({f['field_id'] for f in review['fields']},defined)
        self.assertEqual(len(review['fields']),len(defined))
        self.assertGreater(len(bundle.technical_review_rows()['fields']),len(review['fields']))
        for row in review['fields']:
            self.assertFalse({'channels','consumers','cases','condition_id','evaluation_status'} & row.keys())
            self.assertTrue(row['mapping_refs'])

    def test_candidate_has_no_production_import(self):
        for folder in (ROOT/"apps",ROOT/"packages"):
            for p in folder.rglob("*.py"):
                if p.name=="business_rules_candidate.py":
                    continue
                tree=ast.parse(p.read_text(encoding="utf-8"),filename=str(p))
                for node in ast.walk(tree):
                    if isinstance(node,ast.ImportFrom):
                        self.assertNotIn("business_rules_candidate",node.module or "",str(p))
                    elif isinstance(node,ast.Import):
                        self.assertTrue(all("business_rules_candidate" not in a.name for a in node.names),str(p))

    def test_actual_g05_snapshots_and_existing_resolver_remain_identical(self):
        from packages.application.business_rules_candidate import load_bundle
        from packages.core.parameter_resolution import default_g05_rules
        from packages.core import EffectiveRuleResolver, RuleContext
        paths=(SOURCE/"common/gbt_32150_2025.json",SOURCE/"standards/gbt_32151_34_2024.json",SOURCE/"software_policy.json")
        bundle=load_bundle(paths)
        common, industry=default_g05_rules()
        loaded={key:rule for package in bundle.packages for key,rule in package.rules.items()}
        for original in (*common,*industry):
            with self.subTest(rule=original.rule_id):
                self.assertEqual(loaded[original.rule_id],original)
        context=RuleContext(standard_id="gbt_32151_34_2024")
        expected=EffectiveRuleResolver().resolve(common,industry,context)
        self.assertEqual(bundle.resolve_rules(context),expected,
                         "已由行业覆写解决的共同冲突不能在候选层再次全局阻断")

    def test_default_parameter_and_verified_binding_ids_are_real_catalog_assets(self):
        catalog=json.loads((ROOT/"data-source/carbon_accounting/catalog.json").read_text(encoding="utf-8"))
        parameters={p["parameter_id"] for p in catalog["parameters"]}
        assets={a["asset_id"]:a for a in catalog["reference_data_assets"]}
        bindings={b["binding_id"]:b for b in catalog["reference_data_bindings"]}
        for doc in self.documents():
            states=[f["default"] for f in doc["fields"]]
            for policy in doc["policies"]:
                for branch in policy["branches"]:
                    states.append(branch["value"])
                    tags=branch["when"]["tags"]
                    if tags.get("binding_status")=="VERIFIED":
                        with self.subTest(policy=policy["id"],branch=branch["id"]):
                            self.assertIn(tags.get("binding_id"),bindings,"不能用非空伪绑定代替资格")
                            binding=bindings[tags["binding_id"]]
                            self.assertEqual(binding["review_status"],"VERIFIED")
                            # Existing registry semantics: empty is no standard filter, not proof of applicability.
                            # Formal eligibility is separately checked by adopted rules/Resolver and dependency states.
                            if binding["applicable_standard_ids"]:
                                self.assertIn("gbt_32151_34_2024",binding["applicable_standard_ids"])
                            self.assertEqual(assets[binding["asset_id"]]["parameter_id"],tags["parameter_id"])
            for state in states:
                if state.get("state")=="BINDING":
                    self.assertIn(state["parameter_id"],parameters,"默认值必须引用真实参数身份")

    def test_review_workbook_matches_current_canonical_projection(self):
        from packages.application.business_rules_candidate import load_bundle, _json_safe
        from openpyxl import load_workbook
        paths=(SOURCE/"common/gbt_32150_2025.json",SOURCE/"standards/gbt_32151_34_2024.json",SOURCE/"software_policy.json")
        review=_json_safe(load_bundle(paths).review_rows())
        expected_hash=hashlib.sha256((json.dumps(review,ensure_ascii=False,indent=2)+"\n").encode("utf-8")).hexdigest()
        path=ROOT/"docs/architecture/business-rules/evidence/业务规则审阅表.xlsx"
        self.assertTrue(path.is_file(),"必须提供实际生成的三页审阅表")
        workbook=load_workbook(path,read_only=True,data_only=False)
        try:
            self.assertEqual(workbook.sheetnames,["业务规则","操作与影响","本次变化"])
            for name,kind in zip(workbook.sheetnames,("fields","operations","changes")):
                self.assertTrue(review[kind],f"{name}不能只建空页")
                sheet=workbook[name]
                self.assertEqual(sheet["A1"].value,"审阅数据SHA256："+expected_hash,"审阅表不得落后于候选定义")
                headers=[c.value for c in sheet[5]]
                self.assertEqual(headers.count("稳定审阅键"),1)
                self.assertTrue({"审阅意见","处理状态","审阅编号"}<=set(headers))
                key_column=headers.index("稳定审阅键")
                data=[row for row in sheet.iter_rows(min_row=6,values_only=True) if row[key_column]]
                keys=[row[key_column] for row in data]
                expected={r["review_key"] for r in review[kind]}
                self.assertTrue(expected<=set(keys))
                extra=set(keys)-expected
                if extra:
                    self.assertEqual(kind,"changes","旧修订意见只应进入明确的保留变化行")
                    category=headers.index("变化类型")
                    feedback=[headers.index(h) for h in ("审阅意见","处理状态","审阅编号")]
                    for row in data:
                        if row[key_column] in extra:
                            self.assertEqual(row[category],"未完成审阅意见保留")
                            self.assertTrue(any(row[i] for i in feedback))
                self.assertEqual(len(keys),len(set(keys)))
        finally:
            workbook.close()

    def test_all_packages_remain_candidate_and_reference_explicit_revisions(self):
        for doc in self.documents():
            self.assertEqual(doc["status"],"CANDIDATE")
            for adopted in doc["adopts"]:
                for value in adopted.values():
                    if isinstance(value,str):
                        self.assertNotIn(value.lower(),{"latest","*","all"})

    def test_actual_candidate_property_branches_are_structurally_composable(self):
        from packages.application.business_rules_candidate import load_bundle
        paths=(SOURCE/"common/gbt_32150_2025.json",SOURCE/"standards/gbt_32151_34_2024.json",SOURCE/"software_policy.json")
        rows=load_bundle(paths).technical_review_rows()["fields"]
        unexpected=[(row["field_id"],row.get("condition_id"),row["evaluation_status"])
                    for row in rows if row["evaluation_status"] not in {"READY","BLOCKED"}]
        self.assertEqual(unexpected,[],
            "真实候选资产可明确阻断非法/待核来源，但不应留下策略间无法组合的结构缺项")
