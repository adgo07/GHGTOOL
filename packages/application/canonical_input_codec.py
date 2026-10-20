"""Versioned local project envelope; standard payloads use registered codecs."""
from __future__ import annotations
import json
from .canonical_input_errors import CanonicalInputCodecError
from .standard_registry import default_standard_registry

CANONICAL_INPUT_CODEC_VERSION = 2
_CODEC_ID = "ghgtool.standard_input"


def _object_without_duplicate_keys(pairs):
    result = {}
    for key,value in pairs:
        if key in result:
            raise CanonicalInputCodecError(f"duplicate JSON key: {key}")
        result[key]=value
    return result


def _reject_constant(value):
    raise CanonicalInputCodecError(f"invalid JSON constant: {value}")


def _loads(payload):
    if not isinstance(payload,str):
        raise CanonicalInputCodecError("canonical input payload must be text")
    try:
        return json.loads(payload,parse_constant=_reject_constant,object_pairs_hook=_object_without_duplicate_keys)
    except (json.JSONDecodeError,RecursionError) as exc:
        raise CanonicalInputCodecError(f"invalid canonical input JSON: {exc}") from exc


def registered_input_implementation(value, registry=None):
    registry=registry or default_standard_registry()
    matches=[item for item in registry.implementations if item.accepts_input is not None and item.input_codec_factory is not None and item.accepts_input(value)]
    if len(matches)!=1:
        raise CanonicalInputCodecError("输入类型未登记或标准身份不唯一。")
    return matches[0]


def encode_canonical_input(input_value, *, standard_registry=None):
    implementation=registered_input_implementation(input_value,standard_registry)
    codec=implementation.input_codec_factory()
    document={"codec":_CODEC_ID,"version":2,"standard_id":implementation.standard_id,
              "standard_version":implementation.version,"input_version":codec.CANONICAL_INPUT_CODEC_VERSION,
              "payload":_loads(codec.encode_canonical_input(input_value))}
    return json.dumps(document,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)


def decode_canonical_input(payload, *, standard_registry=None):
    document=_loads(payload)
    registry=standard_registry or default_standard_registry()
    if not isinstance(document,dict):
        raise CanonicalInputCodecError("invalid canonical input envelope")
    # Exact historical codec identity only; no guessing from values or filenames.
    if document.get("codec")=="ghgtool.carbon_material_input":
        try:
            implementation=registry.require("gbt_32151_34_2024","2024")
        except ValueError as exc:
            raise CanonicalInputCodecError(str(exc)) from exc
        return implementation.input_codec_factory().decode_canonical_input(payload)
    expected={"codec","version","standard_id","standard_version","input_version","payload"}
    if set(document)!=expected or document["codec"]!=_CODEC_ID or type(document["version"]) is not int or document["version"]!=2:
        raise CanonicalInputCodecError("invalid or unsupported canonical input envelope")
    try:
        implementation=registry.require(document["standard_id"],document["standard_version"])
        codec=implementation.input_codec_factory()
    except (ValueError,TypeError) as exc:
        raise CanonicalInputCodecError("保存项目的标准或版本尚未开放。") from exc
    if type(document["input_version"]) is not int or document["input_version"] not in getattr(codec,"SUPPORTED_INPUT_CODEC_VERSIONS",(codec.CANONICAL_INPUT_CODEC_VERSION,)):
        raise CanonicalInputCodecError("unsupported standard input version")
    if not isinstance(document['payload'],dict) or type(document['payload'].get('version')) is not int or document['payload']['version']!=document['input_version']:
        raise CanonicalInputCodecError('封套input_version与行业payload版本不一致。')
    value=codec.decode_canonical_input(json.dumps(document["payload"],ensure_ascii=False,allow_nan=False))
    if not implementation.accepts_input(value):
        raise CanonicalInputCodecError("项目载荷与登记标准身份不一致。")
    return value


__all__=["CANONICAL_INPUT_CODEC_VERSION","CanonicalInputCodecError","encode_canonical_input","decode_canonical_input"]
