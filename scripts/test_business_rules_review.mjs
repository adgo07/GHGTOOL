#!/usr/bin/env node
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { spawnSync } from "node:child_process";
import fs from "node:fs/promises";

const scriptPath = fileURLToPath(import.meta.url);
if ((await fs.readFile(scriptPath)).includes("\r\n")) {
  throw new Error("审阅夹具须按仓库LF换行保存；拒绝生成不匹配Git字节的raw哈希。");
}
const repoRoot = path.dirname(path.dirname(scriptPath));
const args = parseArgs(process.argv.slice(2));
const builderPath = args.builder ? path.resolve(args.builder) : path.join(repoRoot, "scripts", "build_business_rules_review.mjs");
const inputPath = args.input ? path.resolve(args.input) : null;
const technicalPath = args["technical-input"] ? path.resolve(args["technical-input"]) : null;
const nodeModulesPath = await findNodeModules(args["node-modules"]);
const tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "ghg-business-rules-review-fixture-"));
let nodeModulesJunctionPath = null;
let succeeded = false;

function parseArgs(argv) {
  const result = { "keep-temp": false };
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    if (key === "--keep-temp") {
      result["keep-temp"] = true;
      continue;
    }
    if (key === "--help" || key === "-h") {
      process.stdout.write("Usage: node scripts/test_business_rules_review.mjs [--builder PATH] [--input PATH] [--technical-input PATH] [--node-modules PATH] [--output PATH] [--keep-temp]\n");
      process.exit(0);
    }
    if (!key.startsWith("--") || !argv[i + 1] || argv[i + 1].startsWith("--")) throw new Error("Invalid argument: " + key);
    result[key.slice(2)] = argv[i + 1];
    i += 1;
  }
  return result;
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonical(value[key])]));
  }
  return value;
}

function canonicalHash(value) {
  return sha256(Buffer.from(JSON.stringify(canonical(value)), "utf8"));
}

function normalizedFileHash(text) {
  return sha256(Buffer.from(text.replace(/\r\n/g, "\n"), "utf8"));
}

function clone(value) {
  return structuredClone(value);
}

function fieldProjection(row, revision) {
  return "field|" + row.rule_set_id + "|" + revision + "|" + row.field_id + "|SUMMARY";
}

function operationProjection(row, revision) {
  return "operation|" + row.rule_set_id + "|" + revision + "|" + row.operation_id;
}

function changeProjection(row, revision) {
  return "change|" + row.rule_set_id + "|" + revision + "|" + row.key;
}

function setRevision(payload, revision) {
  payload.metadata = { ...(payload.metadata || {}), revision };
  for (const row of payload.fields) {
    row.revision = revision;
    row.review_key = fieldProjection(row, revision);
  }
  for (const row of payload.operations) {
    row.revision = revision;
    row.review_key = operationProjection(row, revision);
  }
  for (const row of payload.changes) {
    row.revision = revision;
    row.review_key = changeProjection(row, revision);
  }
}

function makeCondition(sourcePath, direction) {
  return { tags: { source_path: sourcePath, direction }, ranges: {} };
}

function makeSummary(property, outcome, conditions) {
  return { property, groups: [{ outcome, conditions }] };
}

function syntheticPayload() {
  const fieldSet = "qz.carbon_accounting.industry.fixture";
  const policySet = "qz.carbon_accounting.software_policy.fixture";
  const condition = { tags: { origin: "CATALOG", business_source: "STANDARD_DEFAULT" }, ranges: {} };
  const field = {
    field_id: "fuel.lhv", rule_set_id: fieldSet, revision: "synthetic-v0", review_key: "",
    name: "燃料低位发热量（合成样例）", mapping_refs: ["synthetic-fixture"], unit: "MJ/t",
    source: makeSummary("source", { state: "FIXED", values: ["STANDARD_DEFAULT", "ENTERPRISE_MEASURED"] }, [condition]),
    default_source: makeSummary("default_source", { state: "FIXED", source: "STANDARD_DEFAULT" }, [condition]),
    default: makeSummary("default", { state: "BINDING", parameter_id: "fixture-lhv", binding_id: "fixture-lhv-binding" }, [condition]),
    locking: makeSummary("locking", { value_state: "LOCKED", source_state: "LOCKED" }, [condition]),
    pending: [], basis: ["synthetic fixture only"],
  };
  const electricityConditions = [
    makeCondition("CATALOGUE_TABLE_1", "PURCHASED"),
    makeCondition("CATALOGUE_TABLE_1", "EXPORTED"),
  ];
  const electric = {
    field_id: "electricity.factor", rule_set_id: fieldSet, revision: "synthetic-v0", review_key: "",
    name: "购入/输出电力因子（合成样例）", mapping_refs: ["synthetic-fixture"], unit: "tCO2/MWh",
    source: makeSummary("source", { state: "FIXED", values: ["STANDARD_DEFAULT"] }, electricityConditions),
    default_source: makeSummary("default_source", { state: "FIXED", source: "STANDARD_DEFAULT" }, electricityConditions),
    default: makeSummary("default", { state: "BINDING", parameter_id: "fixture-electricity", binding_id: "fixture-electricity-binding" }, electricityConditions),
    locking: makeSummary("locking", { value_state: "LOCKED", source_state: "LOCKED" }, electricityConditions),
    pending: [], basis: ["synthetic fixture only"],
  };
  const payload = {
    metadata: { revision: "synthetic-v0", rule_set_id: fieldSet, status: "SYNTHETIC_FIXTURE" },
    fields: [field, electric],
    operations: [{
      rule_set_id: policySet, operation_id: "initialize_fixture", revision: "synthetic-v0", review_key: "",
      name: "初始化测试操作", initial_context: { channel: "fixture" }, action: "fixture action",
      changes: ["fixture change"], preserves: ["fixture preserve"], invalidates: [],
      confirmation: ["fixture confirmation"], pending: [], basis: ["synthetic fixture only"],
    }],
    changes: [{
      rule_set_id: policySet, key: "fixture.change", revision: "synthetic-v0", review_key: "",
      change_type: "SYNTHETIC_FIXTURE_CHANGE", before: "before fixture", after: "after fixture",
      reason: "synthetic fixture", pending: [],
    }],
  };
  setRevision(payload, "synthetic-source-v0");
  return payload;
}

function allElectricityContexts(row) {
  const values = new Map();
  for (const property of ["source", "default_source", "default", "locking"]) {
    for (const group of row[property]?.groups || []) {
      for (const condition of group.conditions || []) {
        for (const sourcePath of [condition.tags?.source_path].flat().filter(Boolean)) {
          for (const direction of [condition.tags?.direction].flat().filter(Boolean)) {
            values.set(sourcePath + "|" + direction, { sourcePath, direction });
          }
        }
      }
    }
  }
  return [...values.values()];
}

function selectElectricityContexts(row) {
  const all = allElectricityContexts(row);
  const sourcePath = (all.find((item) => item.sourcePath === "CATALOGUE_TABLE_1") || all[0])?.sourcePath;
  assert.ok(sourcePath, "electricity.factor must include source_path");
  const purchased = all.find((item) => item.sourcePath === sourcePath && item.direction === "PURCHASED");
  const exported = all.find((item) => item.sourcePath === sourcePath && item.direction === "EXPORTED");
  assert.ok(purchased && exported, "electricity.factor must include PURCHASED and EXPORTED contexts");
  return [purchased, exported];
}

function trimElectricity(row, contexts) {
  const keep = new Set(contexts.map((item) => item.sourcePath + "|" + item.direction));
  for (const property of ["source", "default_source", "default", "locking"]) {
    row[property] = {
      ...row[property],
      groups: (row[property]?.groups || []).map((group) => ({
        ...group,
        conditions: (group.conditions || []).filter((condition) => {
          const paths = [condition.tags?.source_path].flat().filter(Boolean);
          const directions = [condition.tags?.direction].flat().filter(Boolean);
          return paths.some((sourcePath) => directions.some((direction) => keep.has(sourcePath + "|" + direction)));
        }),
      })).filter((group) => group.conditions.length),
    };
  }
}

function cloneField(template, fieldId, label) {
  const result = clone(template);
  result.field_id = fieldId;
  result.name = String(template.name) + "（" + label + "）";
  result.review_key = "";
  result.revision = "";
  return result;
}

function mutateDefault(summary, suffix) {
  const group = summary?.groups?.find((item) => item.outcome);
  assert.ok(group, "A default outcome is required for the property mutation");
  const outcome = group.outcome;
  if (outcome.binding_id || outcome.parameter_id || outcome.state === "BINDING") {
    outcome.binding_id = String(outcome.binding_id || "fixture-binding") + "-" + suffix;
    outcome.parameter_id = String(outcome.parameter_id || "fixture-parameter") + "-" + suffix;
  } else if (Object.hasOwn(outcome, "value")) {
    outcome.value = String(outcome.value) + "-" + suffix;
  } else {
    outcome.fixture_mutation = suffix;
  }
}

function mutateLocking(row) {
  const outcome = row.locking.groups[0].outcome;
  outcome.value_state = outcome.value_state === "LOCKED" ? "EDITABLE" : "LOCKED";
}

function moveCondition(row) {
  const condition = row.default.groups[0].conditions[0];
  condition.tags = { ...(condition.tags || {}), fixture_condition_scope: "moved" };
}

function fieldStableKey(row, condition) {
  return "field|" + row.rule_set_id + "|" + row.field_id + "|" + (condition || "整体");
}

function makeFixture(base, sourceDetails) {
  const sourceField = base.fields.find((row) => row.field_id === "fuel.lhv")
    || base.fields.find((row) => row.field_id !== "electricity.factor");
  const sourcePower = base.fields.find((row) => row.field_id === "electricity.factor");
  const sourceOperation = base.operations?.[0];
  const sourceChange = base.changes?.[0];
  assert.ok(sourceField && sourcePower && sourceOperation && sourceChange,
    "Input must contain a non-electric field, electricity.factor, one operation, and one change");
  const contexts = selectElectricityContexts(sourcePower);
  const revisionV1 = "fixture-v1";
  const revisionV2 = "fixture-v2";
  const ids = {
    same: sourceField.field_id,
    sourceTarget: "fixture.source_target",
    defaultTarget: "fixture.default_target",
    conditionTarget: "fixture.condition_target",
    conditionMoved: "fixture.condition_moved",
    technicalTarget: "fixture.technical_target",
    technicalConditionTarget: "fixture.technical_condition_target",
    deleted: "fixture.deleted_object",
    legacySummary: "fixture.legacy_summary",
    legacyCondition: "fixture.legacy_condition",
    unknownAttribute: "fixture.unknown_attribute",
    unknownCondition: "fixture.unknown_condition",
    electricity: sourcePower.field_id,
    directoryScope: "fixture.directory_scope",
    customScope: "fixture.custom_scope",
    purchasedScope: "fixture.visible_electricity_purchased",
    exportedScope: "fixture.visible_electricity_exported",
    overallOperation: "fixture.overall_operation",
  };
  function build(revision, changed) {
    const same = clone(sourceField);
    const electric = clone(sourcePower);
    trimElectricity(electric, contexts);
    const directoryScope = cloneField(sourceField, ids.directoryScope, "目录对象可见范围目标");
    const customScope = cloneField(sourceField, ids.customScope, "自定义可见范围目标");
    const purchasedScope = cloneField(sourcePower, sourcePower.field_id, "购入电力可见范围目标");
    purchasedScope.rule_set_id = ids.purchasedScope;
    trimElectricity(purchasedScope, [contexts[0]]);
    const exportedScope = cloneField(sourcePower, sourcePower.field_id, "输出电力可见范围目标");
    exportedScope.rule_set_id = ids.exportedScope;
    trimElectricity(exportedScope, [contexts[1]]);
    const sourceTarget = cloneField(sourceField, ids.sourceTarget, "允许来源目标");
    const defaultTarget = cloneField(sourceField, ids.defaultTarget, "数值默认目标");
    const conditionTarget = cloneField(sourceField, ids.conditionTarget, "条件属性目标");
    conditionTarget.default.groups = conditionTarget.default.groups.slice(0, 1).map((group) => ({
      ...group, conditions: (group.conditions || []).slice(0, 1),
    }));
    const conditionMoved = cloneField(sourceField, ids.conditionMoved, "条件变化目标");
    conditionMoved.default.groups = conditionMoved.default.groups.slice(0, 1).map((group) => ({
      ...group, conditions: (group.conditions || []).slice(0, 1),
    }));
    const deleted = cloneField(sourceField, ids.deleted, "删除后保留目标");
    const technicalTarget = cloneField(sourceField, ids.technicalTarget, "技术绑定属性目标");
    const technicalConditionTarget = cloneField(sourceField, ids.technicalConditionTarget, "技术绑定精确条件目标");
    const legacySummary = cloneField(sourceField, ids.legacySummary, "legacy SUMMARY目标");
    const legacyCondition = cloneField(sourceField, ids.legacyCondition, "legacy 条件级目标");
    const unknownAttribute = cloneField(sourceField, ids.unknownAttribute, "未知属性目标");
    const unknownCondition = cloneField(sourceField, ids.unknownCondition, "未知条件目标");
    if (changed) {
      mutateDefault(sourceTarget.default, "unrelated");
      mutateDefault(defaultTarget.default, "targeted");
      mutateLocking(conditionTarget);
      moveCondition(conditionMoved);
    }
    const fields = [same, electric, directoryScope, customScope, purchasedScope, exportedScope,
      sourceTarget, defaultTarget, conditionTarget, conditionMoved, technicalTarget, technicalConditionTarget];
    if (revision === revisionV1) fields.push(deleted);
    fields.push(legacySummary, legacyCondition, unknownAttribute, unknownCondition);
    const overallOperation = clone(sourceOperation);
    overallOperation.operation_id = ids.overallOperation;
    const result = {
      metadata: { ...(base.metadata || {}), revision, status: "FIXTURE_ONLY" },
      fields,
      operations: [clone(sourceOperation), overallOperation],
      changes: [clone(sourceChange)],
    };
    setRevision(result, revision);
    return result;
  }
  const v1 = build(revisionV1, false);
  const v2 = build(revisionV2, true);
  const rows = new Map();
  for (const row of v1.fields) if (!rows.has(row.field_id)) rows.set(row.field_id, row);
  const purchasedScopeRow = v1.fields.find((row) => row.rule_set_id === ids.purchasedScope);
  const exportedScopeRow = v1.fields.find((row) => row.rule_set_id === ids.exportedScope);
  const suffix = (context) => "source_path=" + context.sourcePath + ";direction=" + context.direction;
  const cases = [
    { id: "same-content-field", sheet: "业务规则", key: fieldStableKey(rows.get(ids.same)), property: "整体", condition: "整体", expected: "继续关联" },
    { id: "allowed-source-unaffected-by-default-change", sheet: "业务规则", key: fieldStableKey(rows.get(ids.sourceTarget)), property: "允许来源", condition: "当前行", expected: "继续关联" },
    { id: "numeric-default-changed", sheet: "业务规则", key: fieldStableKey(rows.get(ids.defaultTarget)), property: "数值默认", condition: "当前行", expected: "需复核" },
    { id: "condition-scope-keeps-default-opinion", sheet: "业务规则", key: fieldStableKey(rows.get(ids.conditionTarget)), property: "数值默认", condition: "__AUTO__", expected: "继续关联" },
    { id: "visible-directory-object-scope", sheet: "业务规则", key: fieldStableKey(rows.get(ids.directoryScope)), property: "允许来源", condition: "__AUTO_VISIBLE__对象类别=目录对象", expected: "继续关联", input_source: "rendered HTML directory-object condition" },
    { id: "visible-custom-object-scope", sheet: "业务规则", key: fieldStableKey(rows.get(ids.customScope)), property: "允许来源", condition: "__AUTO_VISIBLE__对象类别=自定义", expected: "继续关联", input_source: "rendered HTML custom-object condition" },
    { id: "visible-electricity-purchased-scope", sheet: "业务规则", key: fieldStableKey(purchasedScopeRow, suffix(contexts[0])), property: "默认来源", condition: "__AUTO_VISIBLE__方向=购入", expected: "继续关联", input_source: "rendered HTML purchased-electricity condition" },
    { id: "visible-electricity-exported-scope", sheet: "业务规则", key: fieldStableKey(exportedScopeRow, suffix(contexts[1])), property: "默认来源", condition: "__AUTO_VISIBLE__方向=输出", expected: "需复核", input_source: "rendered HTML exported-electricity condition" },
    { id: "changed-condition-is-retained", sheet: "业务规则", key: fieldStableKey(rows.get(ids.conditionMoved)), property: "数值默认", condition: "__AUTO__", expected: "待映射", retention: true },
    ...(sourceDetails ? [
      { id: "technical-binding-property-change", sheet: "业务规则", key: fieldStableKey(rows.get(ids.technicalTarget)), property: "默认来源", condition: "当前行", expected: "需复核" },
      { id: "technical-binding-exact-condition-change", sheet: "业务规则", key: fieldStableKey(rows.get(ids.technicalConditionTarget)), property: "默认来源", condition: "__AUTO_PROPERTY__", expected: "需复核" },
    ] : []),
    { id: "deleted-object-is-retained", sheet: "业务规则", key: fieldStableKey(rows.get(ids.deleted)), property: "整体", condition: "整体", expected: "待映射", retention: true, reviewStatus: "已落实" },
    { id: "legacy-summary-unique-field", sheet: "业务规则", key: fieldStableKey(rows.get(ids.legacySummary)), property: "整体", condition: "整体", expected: "需复核", override: fieldProjection(rows.get(ids.legacySummary), revisionV1) },
    { id: "legacy-condition-level-not-guessed", sheet: "业务规则", key: fieldStableKey(rows.get(ids.legacyCondition)), property: "整体", condition: "COMBINED", expected: "待映射", retention: true, override: "field|" + rows.get(ids.legacyCondition).rule_set_id + "|" + revisionV1 + "|" + ids.legacyCondition + "|COMBINED|legacy-condition-id" },
    { id: "unknown-attribute-is-retained", sheet: "业务规则", key: fieldStableKey(rows.get(ids.unknownAttribute)), property: "未知属性", condition: "当前行", expected: "待映射", retention: true },
    { id: "unknown-condition-is-retained", sheet: "业务规则", key: fieldStableKey(rows.get(ids.unknownCondition)), property: "数值默认", condition: "不存在的条件", expected: "待映射", retention: true },
    { id: "electricity-purchased-stable-row", sheet: "业务规则", key: fieldStableKey(rows.get(ids.electricity), suffix(contexts[0])), property: "整体", condition: "当前行", expected: "继续关联" },
    { id: "electricity-export-legacy-summary-ambiguous", sheet: "业务规则", key: fieldStableKey(rows.get(ids.electricity), suffix(contexts[1])), property: "整体", condition: "整体", expected: "待映射", retention: true, override: fieldProjection(rows.get(ids.electricity), revisionV1) },
    { id: "operation-property-target", sheet: "操作与影响", key: "operation|" + v1.operations[0].rule_set_id + "|" + v1.operations[0].operation_id + "|整体", property: "操作", condition: "当前行", expected: "继续关联" },
    { id: "operation-overall-workbook-scope", sheet: "操作与影响", key: "operation|" + v1.operations[1].rule_set_id + "|" + ids.overallOperation + "|整体", property: "整体", condition: "整体", expected: "继续关联", input_source: "actual workbook operation row and allowed dropdown value" },
    { id: "change-overall-feedback", sheet: "本次变化", key: "change|" + v1.changes[0].rule_set_id + "|" + v1.changes[0].key + "|整体", property: "整体", condition: "整体", expected: "继续关联", input_source: "actual workbook change row and allowed dropdown value" },
  ];
  const directionIsolationCases = sourceDetails ? [
    { id: "electricity-purchased-technical-isolation", sheet: "业务规则", key: fieldStableKey(rows.get(ids.electricity), suffix(contexts[0])), property: "默认来源", condition: "当前行", expected: "继续关联" },
    { id: "electricity-exported-technical-isolation", sheet: "业务规则", key: fieldStableKey(rows.get(ids.electricity), suffix(contexts[1])), property: "默认来源", condition: "当前行", expected: "需复核" },
  ] : [];
  return {
    v1, v2, cases, directionIsolationCases, contexts, ids, revisionV1, revisionV2, sourceDetails,
    selected: {
      non_electric_field_id: sourceField.field_id,
      electricity_field_id: sourcePower.field_id,
      visible_scope_fixture_ids: [ids.directoryScope, ids.customScope, ids.purchasedScope, ids.exportedScope],
      electricity_contexts: contexts.map((item) => ({ source_path: item.sourcePath, direction: item.direction })),
      operation_id: sourceOperation.operation_id,
      change_id: sourceChange.key,
      synthetic_source: base.metadata?.status === "SYNTHETIC_FIXTURE",
    },
  };
}

function technicalRows(rows, kind, id, contexts) {
  let selected = rows.filter((row) => kind === "field" ? row.field_id === id : kind === "operation" ? row.operation_id === id : row.key === id);
  if (kind !== "field" || id !== "electricity.factor" || !contexts) return selected;
  const allow = new Set(contexts.map((item) => item.sourcePath + "|" + item.direction));
  const filtered = selected.filter((row) => {
    const conditions = [row.condition, ...Object.values(row.conditions_by_property || {})];
    return conditions.some((condition) => {
      const paths = [condition?.tags?.source_path].flat().filter(Boolean);
      const directions = [condition?.tags?.direction].flat().filter(Boolean);
      return paths.some((sourcePath) => directions.some((direction) => allow.has(sourcePath + "|" + direction)));
    });
  });
  return filtered.length ? filtered : selected;
}

function exactConditionMatches(compactCondition, technicalCondition) {
  if (!compactCondition || !technicalCondition) return false;
  if (!Object.entries(compactCondition.tags || {}).every(([key, value]) => [value].flat().includes(technicalCondition.tags?.[key]))) return false;
  return JSON.stringify(canonical(compactCondition.ranges || {})) === JSON.stringify(canonical(technicalCondition.ranges || {}));
}

function alternateBinding(sourceDetails, fieldId, direction, sourcePath, excludedFieldId = null) {
  const rows = (sourceDetails.fields || []).filter((row) => (!fieldId || row.field_id === fieldId) && row.field_id !== excludedFieldId);
  for (const row of rows) {
    const tags = row.conditions_by_property?.default_source?.tags || {};
    if (!tags.binding_id || !tags.parameter_id) continue;
    if (direction && tags.direction !== direction) continue;
    if (sourcePath && tags.source_path === sourcePath) continue;
    return { binding_id: tags.binding_id, parameter_id: tags.parameter_id };
  }
  throw new Error("No alternate real technical binding found for " + fieldId);
}

function mutateTechnicalBinding(row, property, replacement, reasonSuffix) {
  const when = row.conditions_by_property?.[property];
  const branch = row.policy_branch_values?.[property];
  assert.ok(when?.tags?.binding_id && when?.tags?.parameter_id, "Technical target must have a real binding identity");
  assert.ok(typeof branch?.reason === "string", "Technical target must include a branch reason");
  const before = { binding_id: when.tags.binding_id, parameter_id: when.tags.parameter_id, reason: branch.reason };
  assert.notEqual(replacement.binding_id, before.binding_id, "Replacement binding must be a different real binding");
  when.tags.binding_id = replacement.binding_id;
  when.tags.parameter_id = replacement.parameter_id;
  branch.reason += reasonSuffix;
  return { before, after: { binding_id: when.tags.binding_id, parameter_id: when.tags.parameter_id, reason: branch.reason } };
}

function applyTechnicalOnlyMutations(sourceDetails, payload, fixture, details) {
  if (!sourceDetails) return [];
  const log = [];
  const generalReplacement = alternateBinding(sourceDetails, null, null, null, fixture.selected.non_electric_field_id);
  const mutateOne = (fieldId, conditionPredicate, label, replacement = generalReplacement, ruleSetId = null) => {
    const allRows = details.fields.filter((row) => row.field_id === fieldId && (!ruleSetId || row.rule_set_id === ruleSetId));
    const candidates = allRows.filter((row) => {
      const when = row.conditions_by_property?.default_source;
      return when?.tags?.binding_id && when.tags.parameter_id &&
        typeof row.policy_branch_values?.default_source?.reason === "string" && conditionPredicate(when);
    });
    assert.ok(candidates.length, label + " must identify a real technical binding row");
    const beforeCount = allRows.length;
    const beforeBoundCount = allRows.filter((row) => row.conditions_by_property?.default_source?.tags?.binding_id).length;
    const target = candidates[0];
    const mutation = mutateTechnicalBinding(target, "default_source", replacement, "（fixture technical binding review: " + label + "）");
    const afterBoundCount = allRows.filter((row) => row.conditions_by_property?.default_source?.tags?.binding_id).length;
    assert.equal(allRows.length, beforeCount, label + " must preserve technical row count");
    assert.equal(afterBoundCount, beforeBoundCount, label + " must preserve binding-bearing row count");
    log.push({
      scenario: label,
      fixture_field_id: fieldId,
      changed_property: "default_source",
      technical_rows: beforeCount,
      binding_rows_before_after: [beforeBoundCount, afterBoundCount],
      replacement_binding_is_from_real_source_row: true,
      ...mutation,
    });
  };

  const firstCondition = payload.fields.find((row) => row.field_id === fixture.ids.technicalConditionTarget)
    ?.default_source?.groups?.flatMap((group) => group.conditions || [])[0];
  assert.ok(firstCondition, "Exact-condition fixture needs a compact default_source condition");
  mutateOne(fixture.ids.technicalTarget,
    (when) => when.tags.origin === "CATALOG" && when.tags.binding_status === "VERIFIED",
    "technical-property-target");
  mutateOne(fixture.ids.technicalConditionTarget,
    (when) => exactConditionMatches(firstCondition, when),
    "technical-exact-condition-target");

  const exported = fixture.contexts.find((item) => item.direction === "EXPORTED");
  assert.ok(exported, "Electricity fixture must include EXPORTED context");
  const exportReplacement = alternateBinding(sourceDetails, "electricity.factor", "EXPORTED", exported.sourcePath);
  const exportedCondition = (when) => when.tags.source_path === exported.sourcePath && when.tags.direction === exported.direction;
  mutateOne(fixture.ids.electricity, exportedCondition,
    "electricity-exported-context-only", exportReplacement);
  mutateOne(fixture.ids.electricity, exportedCondition,
    "visible-exported-electricity-scope", exportReplacement, fixture.ids.exportedScope);
  return log;
}

function reverseTechnicalRows(details) {
  for (const collection of [details.fields, details.operations, details.changes]) {
    if (Array.isArray(collection)) collection.reverse();
  }
}

function makeDetails(sourceDetails, payload, fixture, technicalOnly = false) {
  if (!sourceDetails) {
    const result = clone(payload);
    result.fields[0].fixture_review_marker = "fixture-details-marker";
    return result;
  }
  const sourceFieldId = fixture.selected.non_electric_field_id;
  const baseFieldRows = technicalRows(sourceDetails.fields || [], "field", sourceFieldId);
  assert.ok(baseFieldRows.length, "technical_review_rows must include the selected field");
  const result = {
    metadata: { ...(sourceDetails.metadata || {}), revision: payload.metadata.revision },
    fields: [], operations: [], changes: [],
  };
  for (const row of payload.fields) {
    const sourceId = row.field_id.startsWith("fixture.") ? sourceFieldId : row.field_id;
    const contexts = row.field_id === fixture.ids.electricity
      ? fixture.contexts
      : row.rule_set_id === fixture.ids.purchasedScope ? [fixture.contexts[0]]
      : row.rule_set_id === fixture.ids.exportedScope ? [fixture.contexts[1]]
      : undefined;
    const sourceRows = technicalRows(sourceDetails.fields || [], "field", sourceId, contexts);
    for (const source of sourceRows) {
      const copy = clone(source);
      copy.field_id = row.field_id;
      copy.rule_set_id = row.rule_set_id;
      copy.revision = payload.metadata.revision;
      copy.review_key = row.review_key;
      if (copy.key) copy.key = String(copy.key).replaceAll(sourceId, row.field_id);
      result.fields.push(copy);
    }
  }
  for (const row of payload.operations) {
    const sourceId = row.operation_id === fixture.ids.overallOperation
      ? fixture.selected.operation_id
      : row.operation_id;
    const sourceRows = technicalRows(sourceDetails.operations || [], "operation", sourceId);
    for (const source of sourceRows.length ? sourceRows : [row]) {
      result.operations.push({ ...clone(source), operation_id: row.operation_id,
        rule_set_id: row.rule_set_id, revision: payload.metadata.revision, review_key: row.review_key });
    }
  }
  for (const row of payload.changes) {
    const sourceRows = technicalRows(sourceDetails.changes || [], "change", row.key);
    for (const source of sourceRows.length ? sourceRows : [row]) {
      result.changes.push({ ...clone(source), rule_set_id: row.rule_set_id, revision: payload.metadata.revision, review_key: row.review_key });
    }
  }
  if (result.fields.length) result.fields[0].fixture_review_marker = "fixture-details-marker";
  else if (result.operations.length) result.operations[0].fixture_review_marker = "fixture-details-marker";
  if (technicalOnly) fixture.technicalMutations = applyTechnicalOnlyMutations(sourceDetails, payload, fixture, result);
  return result;
}

async function findNodeModules(explicitPath) {
  if(explicitPath){
    const candidate=path.resolve(explicitPath);
    try {await fs.access(path.join(candidate,"@oai","artifact-tool","package.json"));return candidate;}
    catch(error){throw new Error("显式 --node-modules 路径缺少 @oai/artifact-tool，未回退到其他bundle："+candidate,{cause:error});}
  }
  const candidates = [process.env.ARTIFACT_TOOL_NODE_MODULES,path.resolve(path.dirname(process.execPath),"..","node_modules")].filter(Boolean);
  for (const candidate of candidates) {
    try {
      await fs.access(path.join(candidate, "@oai", "artifact-tool"));
      return candidate;
    } catch {
      // Continue to the next bundled runtime location.
    }
  }
  throw new Error("缺少开发工具 @oai/artifact-tool；请调用 load_workspace_dependencies 获取 packages 目录并以 --node-modules 明确传入。它不是产品运行依赖。检查位置："+candidates.join("; "));
}

async function loadArtifactTool(tempRoot) {
  const modulePath = path.join(tempRoot, "artifact-tool-loader.mjs");
  await fs.writeFile(modulePath, 'export { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";\n', "utf8");
  return import(pathToFileURL(modulePath).href);
}

async function runBuilder(builderCopy, input, details, output, cwd, previous) {
  const commandArgs = [builderCopy, "--input", input, "--details", details, "--output", output, "--skip-preview", "1"];
  if (previous) commandArgs.push("--previous", previous);
  const run = spawnSync(process.execPath, commandArgs, { cwd, encoding: "utf8", maxBuffer: 16 * 1024 * 1024 });
  if (run.error) throw run.error;
  if (run.status !== 0) throw new Error("Builder failed (" + run.status + ")\nstdout:\n" + run.stdout + "\nstderr:\n" + run.stderr);
  return run.stdout.trim();
}

async function tableFor(workbook, sheetName) {
  const sheet = workbook.worksheets.getItem(sheetName);
  const items = sheet.tables.items;
  assert.equal(items.length, 1, sheetName + " must have exactly one Table");
  const table = items[0];
  const range = table.getRange();
  const matrix = range.values.map((row) => Array.from(row));
  const headers = matrix[0];
  assert.ok(headers.length && headers.every((value) => String(value ?? "").trim()), sheetName + " has an empty Table header");
  return { sheet, table, range, matrix, headers, idx: Object.fromEntries(headers.map((value, i) => [value, i])) };
}

function findStableRow(table, stableKey) {
  const row = table.matrix.find((value, index) => index > 0 && value[table.idx["稳定审阅键"]] === stableKey);
  assert.ok(row, "Missing stable key " + stableKey);
  return row;
}

function scopeKey(property, condition) {
  return ["当前行", "整体"].includes(condition) ? property : property + "@@" + condition;
}

async function seedAndReverse(artifact, workbookPath, fixture, tempRoot) {
  const workbook = await artifact.SpreadsheetFile.importXlsx(await artifact.FileBlob.load(workbookPath));
  const seeded = new Map();
  const visibleHtml=await fs.readFile(path.join(path.dirname(workbookPath),"业务规则审阅详情.html"),"utf8");
  const decodeHtml=value=>value.replaceAll("&quot;",'"').replaceAll("&gt;",">").replaceAll("&lt;","<").replaceAll("&amp;","&");
  const visibleScopes=[...visibleHtml.matchAll(/<pre data-review-row="([^"]+)" data-review-property="([^"]+)">([\s\S]*?)<\/pre>/g)].map(m=>({key:decodeURIComponent(decodeHtml(m[1])),property:decodeHtml(m[2]),condition:decodeHtml(m[3])}));
  for (const item of fixture.cases) {
    const table = await tableFor(workbook, item.sheet);
    const row = findStableRow(table, item.key);
    const idx = table.idx;
    const fingerprints = JSON.parse(String(row[idx["内容指纹"]]));
    let condition = item.condition;
    const visibleSelector = condition.startsWith("__AUTO_VISIBLE__")
      ? condition.slice("__AUTO_VISIBLE__".length)
      : null;
    if (condition === "__AUTO__" || condition === "__AUTO_PROPERTY__" || visibleSelector !== null) {
      let matches=visibleScopes.filter(v=>v.key===item.key&&v.property===item.property);
      if (visibleSelector !== null) matches=matches.filter(v=>v.condition.includes(visibleSelector));
      assert.ok(matches.length,item.id+" needs the requested condition from the actual visible HTML, not hidden fingerprints");
      condition=matches[0].condition;
      assert.ok(Object.hasOwn(fingerprints,scopeKey(item.property,condition)),"Visible condition must map exactly to a registered scope");
    }
    const oldKey = item.override || item.key;
    const originalProjection = item.override || row[idx["当前投影键"]];
    const opinion = "fixture:" + item.id;
    row[idx["审阅意见"]] = opinion;
    row[idx["处理状态"]] = item.reviewStatus || "待处理";
    row[idx["审阅编号"]] = "FX-" + item.id;
    row[idx["意见针对属性"]] = item.property;
    row[idx["意见针对条件"]] = condition;
    row[idx["原审阅版本"]] = fixture.revisionV1;
    row[idx["原审阅投影"]] = row[idx["原审阅投影"]] || fixture.v1Hash;
    row[idx["原投影键"]] = originalProjection;
    row[idx["稳定审阅键"]] = oldKey;
    table.range.values = table.matrix;
    seeded.set(item.id, {
      ...item, condition, oldKey, originalProjection, opinion,
      opinionId: "FX-" + item.id,
      reviewStatus: row[idx["处理状态"]],
      originalRevision: fixture.revisionV1,
      originalHash: row[idx["原审阅投影"]],
      fingerprints,
      scope: scopeKey(item.property, condition),
    });
  }

  const expected = new Map();
  for (const sheetName of ["业务规则", "操作与影响", "本次变化"]) {
    const table = await tableFor(workbook, sheetName);
    const reversed = [table.matrix[0], ...table.matrix.slice(1).reverse()];
    expected.set(sheetName, reversed.map((row) => [
      row[table.idx["稳定审阅键"]], row[table.idx["审阅意见"]], row[table.idx["审阅编号"]],
    ]));
    table.range.values = reversed;
  }
  const previousPath = path.join(tempRoot, "previous-reversed.xlsx");
  await (await artifact.SpreadsheetFile.exportXlsx(workbook)).save(previousPath);
  const reopened = await artifact.SpreadsheetFile.importXlsx(await artifact.FileBlob.load(previousPath));
  const tableRefs = {};
  for (const sheetName of ["业务规则", "操作与影响", "本次变化"]) {
    const table = await tableFor(reopened, sheetName);
    const actual = table.matrix.map((row) => [
      row[table.idx["稳定审阅键"]], row[table.idx["审阅意见"]], row[table.idx["审阅编号"]],
    ]);
    assert.deepEqual(actual, expected.get(sheetName), sheetName + " Table data order must survive xlsx save/reopen");
    tableRefs[sheetName] = table.table.address || table.range.address;
    assert.ok(typeof tableRefs[sheetName] === "string", sheetName + " must expose the actual Table ref");
  }
  for (const item of seeded.values()) {
    const table = await tableFor(reopened, item.sheet);
    const row = table.matrix.find((value, index) => index > 0 && value[table.idx["审阅编号"]] === item.opinionId);
    assert.ok(row, item.id + " feedback remains after sorting and reopen");
    assert.equal(row[table.idx["稳定审阅键"]], item.oldKey);
    assert.equal(row[table.idx["审阅意见"]], item.opinion);
  }
  return { previousPath, seeded, reopened, tableRefs };
}

function currentProjection(payload, item) {
  if (item.sheet === "操作与影响") {
    const operationId = item.key.split("|")[2];
    return payload.operations.find((row) => row.operation_id === operationId)?.review_key;
  }
  if (item.sheet === "本次变化") return payload.changes.find((row) => row.key === item.key.split("|")[2])?.review_key;
  const [, ruleSetId, fieldId] = item.key.split("|");
  return payload.fields.find((row) => row.rule_set_id === ruleSetId && row.field_id === fieldId)?.review_key;
}

async function verifyOutput(artifact, workbookPath, detailsPath, detailsPayload, fixture, seeded) {
  const workbook = await artifact.SpreadsheetFile.importXlsx(await artifact.FileBlob.load(workbookPath));
  const sheetNames = workbook.worksheets.items.map((sheet) => sheet.name);
  assert.deepEqual(sheetNames, ["业务规则", "操作与影响", "本次变化"], "The workbook must keep exactly three review sheets");
  const technicalHeaders = ["意见针对属性", "意见针对条件", "原审阅版本", "原审阅投影", "意见关联状态", "稳定审阅键",
    "内容指纹", "意见基线指纹", "原投影键", "当前投影键", "规则修订"];
  const tables = new Map();
  const tableRefs = {};
  for (const name of sheetNames) {
    const table = await tableFor(workbook, name);
    for (const header of ["审阅意见", "处理状态", "审阅编号", ...technicalHeaders]) {
      assert.ok(table.idx[header] !== undefined, name + " lacks " + header);
    }
    tables.set(name, table);
    tableRefs[name] = table.table.address || table.range.address;
  }
  const outputRows = [];
  for (const [sheetName, table] of tables) {
    for (const row of table.matrix.slice(1)) outputRows.push({ sheetName, row, idx: table.idx });
  }
  const results = [];
  for (const expected of seeded.values()) {
    const hits = outputRows.filter((entry) => entry.row[entry.idx["审阅编号"]] === expected.opinionId);
    assert.equal(hits.length, 1, expected.id + " feedback must appear exactly once");
    const found = hits[0];
    const row = found.row;
    const idx = found.idx;
    assert.equal(row[idx["审阅意见"]], expected.opinion);
    assert.equal(row[idx["处理状态"]], expected.reviewStatus, expected.id + " must preserve review status");
    assert.equal(row[idx["意见针对属性"]], expected.property);
    assert.equal(row[idx["意见针对条件"]], expected.condition);
    assert.equal(row[idx["原审阅版本"]], expected.originalRevision);
    assert.equal(row[idx["原审阅投影"]], expected.originalHash);
    assert.equal(row[idx["意见关联状态"]], expected.expected, expected.id + " association status");
    if (expected.retention) {
      assert.equal(found.sheetName, "本次变化");
      assert.equal(row[idx["变化类型"]], "未完成审阅意见保留");
      assert.ok(String(row[idx["稳定审阅键"]]).startsWith("retention|"));
      assert.equal(row[idx["原投影键"]], expected.originalProjection);
      assert.equal(row[idx["当前投影键"]], expected.originalProjection);
    } else {
      assert.equal(found.sheetName, expected.sheet);
      assert.equal(row[idx["稳定审阅键"]], expected.key);
      assert.equal(row[idx["原投影键"]], expected.originalProjection);
      assert.equal(row[idx["当前投影键"]], currentProjection(fixture.v2, expected));
      assert.equal(row[idx["规则修订"]], fixture.revisionV2);
    }
    if (expected.scope && expected.fingerprints[expected.scope] !== undefined) {
      const current = JSON.parse(String(row[idx["内容指纹"]]));
      if (expected.id === "allowed-source-unaffected-by-default-change") {
        assert.equal(current[expected.scope], expected.fingerprints[expected.scope]);
        assert.notEqual(current["整体"], expected.fingerprints["整体"]);
      }
      if (expected.id === "same-content-field") {
        assert.equal(current[expected.scope], expected.fingerprints[expected.scope],
          "Reversing technical rows must leave the same-content fingerprint unchanged");
      }
      if (expected.id === "numeric-default-changed") {
        assert.notEqual(current[expected.scope], expected.fingerprints[expected.scope]);
      }
      if (expected.id === "condition-scope-keeps-default-opinion") {
        assert.equal(current[expected.scope], expected.fingerprints[expected.scope]);
        assert.notEqual(current["读写锁定"], expected.fingerprints["读写锁定"]);
      }
      if (["technical-binding-property-change", "technical-binding-exact-condition-change", "electricity-exported-technical-isolation"].includes(expected.id)) {
        assert.notEqual(current[expected.scope], expected.fingerprints[expected.scope], expected.id + " must fingerprint changed technical bindings");
      }
      if (expected.id === "electricity-purchased-technical-isolation") {
        assert.equal(current[expected.scope], expected.fingerprints[expected.scope], "PURCHASED fingerprint must not inherit EXPORTED technical changes");
      }
    }
    results.push({
      id: expected.id,
      association_status: expected.expected,
      input_source: expected.input_source || "fixture-entered opinion scope",
      sheet: found.sheetName,
      stable_key: row[idx["稳定审阅键"]],
      original_projection_key: row[idx["原投影键"]],
      current_projection_key: row[idx["当前投影键"]],
    });
  }
  const fields = tables.get("业务规则");
  assert.ok(fields.idx["业务条件"] !== undefined && fields.idx["同源详情入口"] !== undefined,
    "Business field table needs conditions and same-source HTML links");
  const html = await fs.readFile(detailsPath, "utf8");
  const baseRow = fixture.v2.fields[0];
  const detailIdentity = "field|" + baseRow.rule_set_id + "|" + baseRow.field_id;
  assert.ok(html.includes('id="review-scope"'));
  assert.ok(html.includes('id="' + detailIdentity + '"'));
  assert.ok(html.includes("fixture-details-marker"));
  const detailIds=new Set();
  const collectIds=value=>{if(Array.isArray(value)){value.forEach(collectIds);return;}if(!value||typeof value!=="object")return;for(const [key,item] of Object.entries(value)){if(["parameter_id","binding_id","field_id","condition_id"].includes(key)&&typeof item==="string"&&item)detailIds.add(item);collectIds(item);}};
  collectIds(detailsPayload);
  const escaped=value=>value.replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");
  for(const id of detailIds)assert.ok(html.includes(escaped(id)),"Shared/unique HTML must preserve detail identity "+id);

  const detailsHash = canonicalHash(detailsPayload);
  assert.ok(html.includes("详情输入SHA256：" + detailsHash), "HTML must carry the digest of the exact details JSON");
  assert.ok(html.includes("目录参考值未核对"),
    "A build without --catalog-snapshot must tell reviewers that catalog values are not checked");
  const manifestPath = path.join(path.dirname(workbookPath), "review-view-manifest.json");
  const manifest = JSON.parse(await fs.readFile(manifestPath, "utf8"));
  assert.equal(manifest.details_projection_bound, true, "Manifest must bind technical details to this fixture projection");
  assert.equal(manifest.details_sha256, detailsHash, "Manifest and HTML must use the same canonical details digest");
  for (const entry of outputRows) {
    if (String(entry.row[entry.idx["稳定审阅键"]]).startsWith("retention|")) continue;
    assert.ok(String(entry.row[entry.idx["同源详情入口"]] || "").startsWith("业务规则审阅详情.html#"));
    const locator=String(entry.row[entry.idx["同源详情入口"]]);
    const identity=decodeURIComponent(locator.slice(locator.indexOf("#")+1));
    assert.ok(html.includes('id="'+escaped(identity)+'"'),"Every workbook detail locator must resolve to an HTML object");
  }
  return { results, sheetNames, detailsHash, tableRefs, manifest };
}

async function saveAssociationStatus(artifact, workbookPath, opinionId, status, outputPath) {
  const workbook = await artifact.SpreadsheetFile.importXlsx(await artifact.FileBlob.load(workbookPath));
  const table = await tableFor(workbook, "业务规则");
  const row = table.matrix.find((value, index) => index > 0 && value[table.idx["审阅编号"]] === opinionId);
  assert.ok(row, "Cannot change association status for " + opinionId);
  row[table.idx["意见关联状态"]] = status;
  table.range.values = table.matrix;
  await (await artifact.SpreadsheetFile.exportXlsx(workbook)).save(outputPath);
  return outputPath;
}

async function feedbackRow(artifact, workbookPath, opinionId) {
  const workbook = await artifact.SpreadsheetFile.importXlsx(await artifact.FileBlob.load(workbookPath));
  const table = await tableFor(workbook, "业务规则");
  const row = table.matrix.find((value, index) => index > 0 && value[table.idx["审阅编号"]] === opinionId);
  assert.ok(row, "Missing feedback row " + opinionId);
  return {
    status: row[table.idx["意见关联状态"]],
    reviewStatus: row[table.idx["处理状态"]],
    opinion: row[table.idx["审阅意见"]],
    opinionId: row[table.idx["审阅编号"]],
    originalRevision: row[table.idx["原审阅版本"]],
    originalHash: row[table.idx["原审阅投影"]],
    baseline: JSON.parse(String(row[table.idx["意见基线指纹"]] || "{}")),
    current: JSON.parse(String(row[table.idx["内容指纹"]] || "{}")),
  };
}

async function writeFixturePair(runDirectory, label, payload, details) {
  const outDir = path.join(runDirectory, label);
  await fs.mkdir(outDir, { recursive: true });
  const input = path.join(outDir, "fixture.json");
  const detailsPath = path.join(outDir, "technical-details.json");
  const inputText = JSON.stringify(payload, null, 2) + "\n";
  await fs.writeFile(input, inputText, "utf8");
  const projectionHash = normalizedFileHash(inputText);
  details.metadata = {
    ...(details.metadata || {}),
    revision: payload.metadata.revision,
    source_compact_sha256: projectionHash,
  };
  await fs.writeFile(detailsPath, JSON.stringify(details, null, 2) + "\n", "utf8");
  return { outDir, input, detailsPath, projectionHash, output: path.join(outDir, "review.xlsx") };
}

async function assertStickyReview(artifact, workbookPath, seeded, expectedCurrentHash, expectedBaselineHash, label) {
  const current = await feedbackRow(artifact, workbookPath, seeded.opinionId);
  assert.equal(current.status, "需复核", label + " must keep review sticky");
  assert.equal(current.current["数值默认"], expectedCurrentHash, label + " current property hash");
  assert.equal(current.baseline["数值默认"], expectedBaselineHash, label + " original opinion baseline");
  assert.equal(current.originalRevision, seeded.originalRevision, label + " must preserve original review version");
  assert.equal(current.originalHash, seeded.originalHash, label + " must preserve original review projection");
  return current;
}

async function main() {
  const builderSource = await fs.readFile(builderPath);
  const builderHash = sha256(builderSource);
  const workspace = path.join(tempRoot, "workspace");
  const scripts = path.join(workspace, "scripts");
  const runDirectory = path.join(workspace, "run");
  await fs.mkdir(scripts, { recursive: true });
  await fs.mkdir(runDirectory, { recursive: true });
  const copiedBuilder = path.join(scripts, "build_business_rules_review.mjs");
  await fs.copyFile(builderPath, copiedBuilder);
  assert.equal(sha256(await fs.readFile(copiedBuilder)), builderHash, "Temporary builder copy hash must match source");
  nodeModulesJunctionPath = path.join(tempRoot, "node_modules");
  await fs.symlink(nodeModulesPath, nodeModulesJunctionPath, "junction");

  let base;
  let sourceDetails = null;
  let formalHash = null;
  let technicalHash = null;
  if (Boolean(inputPath)!==Boolean(technicalPath)) throw new Error("正式复验必须同时传 --input 与 --technical-input；无输入仅为 synthetic smoke，不能替代正式20场景。");
  if (inputPath) {
    const sourceText = await fs.readFile(inputPath, "utf8");
    base = JSON.parse(sourceText);
    formalHash = normalizedFileHash(sourceText);
    if (technicalPath) {
      const detailsText = await fs.readFile(technicalPath, "utf8");
      sourceDetails = JSON.parse(detailsText);
      technicalHash = normalizedFileHash(detailsText);
    }
  } else {
    process.stderr.write("提示：无正式投影输入，本次只运行synthetic smoke，场景数与正式输入不同；详见PREFLIGHT。\n");
    base = syntheticPayload();
  }
  const fixture = makeFixture(base, sourceDetails);
  const detailsV1 = makeDetails(sourceDetails, fixture.v1, fixture);
  const summaryProjection = (row) => {
    const result = clone(row);
    delete result.revision;
    delete result.review_key;
    return result;
  };
  if (sourceDetails) {
    for (const fieldId of [fixture.ids.technicalTarget, fixture.ids.technicalConditionTarget, fixture.ids.electricity]) {
      assert.deepEqual(
        summaryProjection(fixture.v1.fields.find((row) => row.field_id === fieldId)),
        summaryProjection(fixture.v2.fields.find((row) => row.field_id === fieldId)),
        "Technical-only scenario must keep compact business summary identical for " + fieldId,
      );
    }
  }
  const detailsV2 = makeDetails(sourceDetails, fixture.v2, fixture, Boolean(sourceDetails));
  reverseTechnicalRows(detailsV2);
  const v1Pair = await writeFixturePair(runDirectory, "v1", fixture.v1, detailsV1);
  const v2Pair = await writeFixturePair(runDirectory, "v2", fixture.v2, detailsV2);
  const artifact = await loadArtifactTool(tempRoot);
  await runBuilder(copiedBuilder, v1Pair.input, v1Pair.detailsPath, v1Pair.output, workspace);
  const v1WorkbookPath = v1Pair.output;
  const seededResult = await seedAndReverse(artifact, v1WorkbookPath, fixture, tempRoot);
  const firstSheet = seededResult.reopened.worksheets.getItem("业务规则");
  fixture.v1Hash = String(firstSheet.getRange("A1").values[0][0]).replace("审阅数据SHA256：", "");
  assert.equal(fixture.v1Hash, v1Pair.projectionHash, "Builder's input projection hash must match normalized fixture input bytes");
  await runBuilder(copiedBuilder, v2Pair.input, v2Pair.detailsPath, v2Pair.output, workspace, seededResult.previousPath);
  const verified = await verifyOutput(artifact, v2Pair.output, path.join(v2Pair.outDir, "业务规则审阅详情.html"),
    detailsV2, fixture, seededResult.seeded);

  // Exercise the user's visible copy/paste entry before and after a targeted content change.
  const visibleOpinion=seededResult.seeded.get("condition-scope-keeps-default-opinion");
  assert.ok(visibleOpinion?.condition,"Visible-entry case must have copied a rendered legal condition");
  const unchangedPair=await writeFixturePair(runDirectory,"visible-unchanged",fixture.v1,makeDetails(sourceDetails,fixture.v1,fixture));
  await runBuilder(copiedBuilder,unchangedPair.input,unchangedPair.detailsPath,unchangedPair.output,workspace,seededResult.previousPath);
  const visibleUnchanged=await feedbackRow(artifact,unchangedPair.output,visibleOpinion.opinionId);
  assert.equal(visibleUnchanged.status,"继续关联","Copied visible condition must associate when rules are unchanged");
  const visibleChanged=clone(fixture.v1);
  mutateDefault(visibleChanged.fields.find(r=>r.field_id===fixture.ids.conditionTarget).default,"visible-condition-content-change");
  const changedPair=await writeFixturePair(runDirectory,"visible-changed",visibleChanged,makeDetails(sourceDetails,visibleChanged,fixture));
  await runBuilder(copiedBuilder,changedPair.input,changedPair.detailsPath,changedPair.output,workspace,seededResult.previousPath);
  const visibleReviewed=await feedbackRow(artifact,changedPair.output,visibleOpinion.opinionId);
  assert.equal(visibleReviewed.status,"需复核","The copied visible scope must require review when its content changes");
  assert.equal(visibleReviewed.opinion,visibleOpinion.opinion);
  const visibleResults=[{id:"visible-condition-copy-unchanged",status:visibleUnchanged.status,input_source:"rendered HTML legal condition"},{id:"visible-condition-copy-changed",status:visibleReviewed.status,input_source:"same rendered HTML condition; changed scoped outcome"}];

  let directionSeededResult = null;
  let directionVerified = { results: [], tableRefs: {} };
  if (sourceDetails) {
    const directionDir = path.join(runDirectory, "electricity-direction-isolation");
    await fs.mkdir(directionDir, { recursive: true });
    const directionFixture = { ...fixture, cases: fixture.directionIsolationCases };
    directionSeededResult = await seedAndReverse(artifact, v1WorkbookPath, directionFixture, directionDir);
    const directionOutput = path.join(directionDir, "review.xlsx");
    await runBuilder(copiedBuilder, v2Pair.input, v2Pair.detailsPath, directionOutput, workspace, directionSeededResult.previousPath);
    directionVerified = await verifyOutput(artifact, directionOutput, path.join(directionDir, "业务规则审阅详情.html"),
      detailsV2, directionFixture, directionSeededResult.seeded);
  }

  const defaultOpinion = seededResult.seeded.get("numeric-default-changed");
  const v2Feedback = await feedbackRow(artifact, v2Pair.output, defaultOpinion.opinionId);
  assert.equal(v2Feedback.status, "需复核");
  assert.equal(v2Feedback.baseline["数值默认"], defaultOpinion.fingerprints["数值默认"],
    "The opinion baseline must remain the original v1 property fingerprint");
  assert.notEqual(v2Feedback.current["数值默认"], v2Feedback.baseline["数值默认"]);
  const stickyHash = v2Feedback.current["数值默认"];
  const baselineHash = v2Feedback.baseline["数值默认"];

  const v3Payload = clone(fixture.v2);
  setRevision(v3Payload, "fixture-v3");
  const v3Details = makeDetails(sourceDetails, v3Payload, fixture);
  const v3Pair = await writeFixturePair(runDirectory, "v3-sticky", v3Payload, v3Details);
  await runBuilder(copiedBuilder, v3Pair.input, v3Pair.detailsPath, v3Pair.output, workspace, v2Pair.output);
  const v3Feedback = await assertStickyReview(artifact, v3Pair.output, defaultOpinion, stickyHash, baselineHash, "second generation");

  const v4Payload = clone(v3Payload);
  setRevision(v4Payload, "fixture-v4");
  const v4Details = makeDetails(sourceDetails, v4Payload, fixture);
  const v4Pair = await writeFixturePair(runDirectory, "v4-sticky", v4Payload, v4Details);
  await runBuilder(copiedBuilder, v4Pair.input, v4Pair.detailsPath, v4Pair.output, workspace, v3Pair.output);
  const v4Feedback = await assertStickyReview(artifact, v4Pair.output, defaultOpinion, stickyHash, baselineHash, "third generation");

  const confirmedPrevious = path.join(runDirectory, "explicit-confirmation-previous.xlsx");
  await saveAssociationStatus(artifact, v4Pair.output, defaultOpinion.opinionId, "已复核本版", confirmedPrevious);
  const v5Payload = clone(v4Payload);
  setRevision(v5Payload, "fixture-v5-confirmed");
  const v5Details = makeDetails(sourceDetails, v5Payload, fixture);
  const v5Pair = await writeFixturePair(runDirectory, "v5-explicit-confirmation", v5Payload, v5Details);
  await runBuilder(copiedBuilder, v5Pair.input, v5Pair.detailsPath, v5Pair.output, workspace, confirmedPrevious);
  const v5Feedback = await feedbackRow(artifact, v5Pair.output, defaultOpinion.opinionId);
  assert.equal(v5Feedback.status, "继续关联", "Explicit confirmation of the unchanged current hash must accept this version");
  assert.deepEqual(v5Feedback.baseline, v5Feedback.current, "Explicit confirmation must move the opinion baseline to the reviewed current hash");
  assert.equal(v5Feedback.originalRevision, defaultOpinion.originalRevision);
  assert.equal(v5Feedback.originalHash, defaultOpinion.originalHash);
  assert.equal(v5Feedback.opinion, defaultOpinion.opinion);
  assert.equal(v5Feedback.reviewStatus, defaultOpinion.reviewStatus);

  const staleConfirmedPrevious = path.join(runDirectory, "stale-confirmation-previous.xlsx");
  await saveAssociationStatus(artifact, v4Pair.output, defaultOpinion.opinionId, "已复核本版", staleConfirmedPrevious);
  const stalePayload = clone(v4Payload);
  const staleDefault = stalePayload.fields.find((row) => row.field_id === fixture.ids.defaultTarget);
  mutateDefault(staleDefault.default, "changed-after-confirmation");
  setRevision(stalePayload, "fixture-v5-stale-confirmation");
  const staleDetails = makeDetails(sourceDetails, stalePayload, fixture);
  const stalePair = await writeFixturePair(runDirectory, "v5-stale-confirmation", stalePayload, staleDetails);
  await runBuilder(copiedBuilder, stalePair.input, stalePair.detailsPath, stalePair.output, workspace, staleConfirmedPrevious);
  const staleFeedback = await feedbackRow(artifact, stalePair.output, defaultOpinion.opinionId);
  assert.equal(staleFeedback.status, "需复核", "A confirmation for an older current hash must not approve newer content");
  assert.notEqual(staleFeedback.current["数值默认"], v4Feedback.current["数值默认"]);
  assert.equal(staleFeedback.baseline["数值默认"], baselineHash, "Stale confirmation must not move the original baseline");
  assert.equal(staleFeedback.originalRevision, defaultOpinion.originalRevision);
  assert.equal(staleFeedback.originalHash, defaultOpinion.originalHash);

  const mutations = [
    { type: "revision-only", object: fixture.ids.same, from: fixture.revisionV1, to: fixture.revisionV2, expected: "继续关联" },
    { type: "unrelated-property-change", object: fixture.ids.sourceTarget, changed_property: "数值默认", opinion_property: "允许来源", expected: "继续关联" },
    { type: "targeted-property-change", object: fixture.ids.defaultTarget, changed_property: "数值默认", opinion_property: "数值默认", expected: "需复核" },
    { type: "sticky-review-across-two-regenerations", object: fixture.ids.defaultTarget, states: [v2Feedback.status, v3Feedback.status, v4Feedback.status], expected: "需复核, 需复核, 需复核" },
    { type: "explicit-confirmation-of-current-hash", object: fixture.ids.defaultTarget, status: v5Feedback.status, expected: "更新意见基线后继续关联" },
    { type: "stale-explicit-confirmation", object: fixture.ids.defaultTarget, status: staleFeedback.status, expected: "新内容仍需复核" },
    { type: "condition-fingerprint-isolation", object: fixture.ids.conditionTarget, changed_property: "读写锁定", opinion_property: "数值默认", expected: "继续关联" },
    { type: "condition-text-change", object: fixture.ids.conditionMoved, expected: "待映射" },
    ...(sourceDetails ? [
      { type: "technical-only-binding-and-reason-change-property-target", object: fixture.ids.technicalTarget, compact_summary_unchanged: true, technical_mutations: fixture.technicalMutations.filter((item) => item.fixture_field_id === fixture.ids.technicalTarget), expected: "需复核" },
      { type: "technical-only-binding-and-reason-change-exact-condition", object: fixture.ids.technicalConditionTarget, compact_summary_unchanged: true, technical_mutations: fixture.technicalMutations.filter((item) => item.fixture_field_id === fixture.ids.technicalConditionTarget), expected: "需复核" },
      { type: "technical-only-electricity-direction-isolation", object: fixture.ids.electricity, changed_direction: "EXPORTED", unchanged_direction: "PURCHASED", feedback_results: directionVerified.results, technical_mutations: fixture.technicalMutations.filter((item) => item.fixture_field_id === fixture.ids.electricity), expected: "EXPORTED需复核; PURCHASED继续关联" },
      { type: "reverse-technical-row-order", collections: ["fields", "operations", "changes"], expected: "same-content-field continues association" },
    ] : []),
    { type: "object-deletion", object: fixture.ids.deleted, expected: "待映射; feedback status and number preserved" },
    { type: "legacy-summary-unique-field", object: fixture.ids.legacySummary, expected: "unique mapping; needs review" },
    { type: "legacy-condition-level", object: fixture.ids.legacyCondition, expected: "retained for mapping; no guessed target" },
    { type: "unknown-attribute-and-condition", objects: [fixture.ids.unknownAttribute, fixture.ids.unknownCondition], expected: "待映射" },
    { type: "electricity-context-split", object: fixture.ids.electricity, contexts: fixture.selected.electricity_contexts, expected: "PURCHASED continues; ambiguous SUMMARY retained" },
    { type: "reverse-table-data-save-and-reopen", sheets: ["业务规则", "操作与影响", "本次变化"], expected: "feedback remains attached to the same business row" },
  ];
  const executedCases = [...verified.results, ...directionVerified.results, ...visibleResults];
  const report = {
    status: "PASS",
    builder_sha256: builderHash,
    artifact_tool_version: JSON.parse(await fs.readFile(path.join(nodeModulesPath,"@oai","artifact-tool","package.json"),"utf8")).version,
    builder_copy_sha256: sha256(await fs.readFile(copiedBuilder)),
    formal_projection_sha256: formalHash,
    formal_details_sha256: technicalHash,
    fixture_projection_v1_sha256: v1Pair.projectionHash,
    fixture_projection_v2_sha256: v2Pair.projectionHash,
    fixture_details_sha256: verified.detailsHash,
    actual_scenario_count: executedCases.length,
    input_mode: sourceDetails ? "formal compact and technical projection" : "synthetic smoke only; excludes technical binding/direction scenarios",
    visible_scope_scenario_count: visibleResults.length,
    actual_html_scope_input_count: executedCases.filter((item) => String(item.input_source || "").includes("HTML")).length,
    main_scenario_count: verified.results.length + visibleResults.length,
    direction_isolation_scenario_count: directionVerified.results.length,
    details_projection_bound: verified.manifest.details_projection_bound,
    selected_object_ids: {
      ...fixture.selected,
      legacy_fixture_field_ids: [fixture.ids.legacySummary, fixture.ids.legacyCondition],
      deleted_fixture_field_id: fixture.ids.deleted,
    },
    mutation_list: mutations,
    cases: executedCases,
    table_sheets: verified.sheetNames,
    previous_table_refs: seededResult.tableRefs,
    output_table_refs: verified.tableRefs,
    direction_isolation_output_table_refs: directionVerified.tableRefs,
    sticky_review: {
      second_generation: v3Feedback.status,
      third_generation: v4Feedback.status,
      explicit_confirmation: v5Feedback.status,
      stale_confirmation_after_new_change: staleFeedback.status,
      original_opinion_revision_preserved: staleFeedback.originalRevision === defaultOpinion.originalRevision,
      original_opinion_projection_preserved: staleFeedback.originalHash === defaultOpinion.originalHash,
    },
    table_reversal_verified: true,
    technical_rows_reversed: true,
    technical_only_summary_unchanged: Boolean(sourceDetails),
    technical_mutations: fixture.technicalMutations || [],
    xlsx_saved_and_reopened: true,
    test_engine: "@oai/artifact-tool xlsx export/import; native Excel/WPS was not run",
    official_workbook_modified: false,
    temporary_workbooks_removed: !args["keep-temp"],
    temp_directory: args["keep-temp"] ? tempRoot : null,
  };
  const json = JSON.stringify(report, null, 2) + "\n";
  if (args.output) {
    const out = path.resolve(args.output);
    await fs.mkdir(path.dirname(out), { recursive: true });
    await fs.writeFile(out, json, "utf8");
  }
  process.stdout.write(json);
  succeeded = true;
}

async function removeFixtureTempSafely() {
  const realTemp = await fs.realpath(tempRoot);
  const realSystemTemp = await fs.realpath(os.tmpdir());
  const relative = path.relative(realSystemTemp, realTemp);
  assert.ok(relative && relative !== ".." && !relative.startsWith(".." + path.sep) && !path.isAbsolute(relative),
    "Refusing recursive fixture cleanup outside os.tmpdir(): " + realTemp);
  assert.ok(path.basename(realTemp).startsWith("ghg-business-rules-review-fixture-"),
    "Refusing recursive fixture cleanup for an unexpected directory: " + realTemp);

  if (nodeModulesJunctionPath) {
    const junctionStat = await fs.lstat(nodeModulesJunctionPath);
    assert.ok(junctionStat.isSymbolicLink(), "Refusing cleanup because the fixture node_modules junction is not a link");
    try {
      await fs.unlink(nodeModulesJunctionPath);
    } catch (error) {
      if (!junctionStat.isSymbolicLink() || !["EPERM", "EISDIR", "ENOTDIR"].includes(error?.code)) throw error;
      await fs.rmdir(nodeModulesJunctionPath);
    }
    await assert.rejects(fs.lstat(nodeModulesJunctionPath), { code: "ENOENT" }, "Fixture junction must be unlinked before recursive removal");
  }
  await fs.rm(realTemp, { recursive: true, force: true });
}

try {
  await main();
} catch (error) {
  process.stderr.write(String(error?.stack || error) + "\nTemporary fixture retained at: " + tempRoot + "\n");
  process.exitCode = 1;
} finally {
  if (succeeded && !args["keep-temp"]) await removeFixtureTempSafely();
}
