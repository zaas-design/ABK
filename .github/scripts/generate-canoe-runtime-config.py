#!/usr/bin/env python3
"""Generate a small Canoe DDK config from the donor module dependency graph.

The donor's canoe_perf fragment enables the entire downstream/Oplus profile.
This generator keeps only the Canoe platform modules implicated by the TB323FU
logs and the transitive DDK dependencies needed to compile them.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Module:
    name: str
    config: str
    deps: tuple[str, ...]


REGISTER_RE = re.compile(r"registry\.register\(\s*(.*?)\n\s*\)", re.S)
FIELD_RE = {
    key: re.compile(rf'^\s*{key}\s*=\s*"([^"]+)"', re.M)
    for key in ("name", "config")
}
DEPS_RE = re.compile(r"^\s*deps\s*=\s*\[(.*?)\]", re.S | re.M)
STRING_RE = re.compile(r'"([^"]+)"')
CONFIG_RE = re.compile(r'^\s*"(CONFIG_[A-Z0-9_]+)"\s*:\s*"([ymn])"', re.M)

# The donor registry attaches this optional virtualization-backed memory
# buffer to a large number of otherwise unrelated DDK modules.  It is not a
# TB323FU hardware dependency: the stock .043 module inventory and the boot
# failure logs contain no Gunyah, mem_buf, or dma-buf heap provider.  Keep it
# out of the selective runtime closure until device evidence requires it.
EXCLUDED_MODULE_PREFIXES = (
    "drivers/virt/gunyah/",
    "arch/arm64/gunyah/",
    "drivers/soc/qcom/mem_buf/",
    "drivers/dma-buf/heaps/",
    # The donor's minidump implementation is downstream-only: it references
    # stack/suspend registration APIs that are not present in kernel/common.
    # It is diagnostic-only and is not required by the TB323FU runtime path.
    "drivers/soc/qcom/minidump",
)
EXCLUDED_CONFIG_PREFIXES = (
    "CONFIG_GH_",
    "CONFIG_QCOM_MEM_BUF",
    "CONFIG_QCOM_DMABUF_HEAPS",
    "CONFIG_QCOM_MINIDUMP",
)
EXCLUDED_CONFIGS = {
    "CONFIG_QCOM_LAZY_MAPPING",
    "CONFIG_QCOM_MEM_BUF_DEV",
    "CONFIG_QCOM_MEM_BUF_DEV_GH",
}


def is_excluded(module: Module) -> bool:
    return module.name.startswith(EXCLUDED_MODULE_PREFIXES) or (
        module.config in EXCLUDED_CONFIGS
        or any(module.config.startswith(prefix) for prefix in EXCLUDED_CONFIG_PREFIXES)
    )


def parse_modules(soc_repo: Path) -> dict[str, Module]:
    modules: dict[str, Module] = {}
    for path in soc_repo.rglob("modules.bzl"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for match in REGISTER_RE.finditer(text):
            block = match.group(1)
            name_match = FIELD_RE["name"].search(block)
            config_match = FIELD_RE["config"].search(block)
            if not name_match or not config_match:
                continue
            deps_match = DEPS_RE.search(block)
            deps = tuple(STRING_RE.findall(deps_match.group(1))) if deps_match else ()
            module = Module(name_match.group(1), config_match.group(1), deps)
            previous = modules.get(module.name)
            if previous and previous != module:
                raise SystemExit(f"conflicting module registration: {module.name}")
            modules[module.name] = module
    if not modules:
        raise SystemExit(f"no registry modules found below {soc_repo}")
    return modules


def parse_config(path: Path) -> dict[str, str]:
    return {key: value for key, value in CONFIG_RE.findall(path.read_text(encoding="utf-8"))}


def select_roots(modules: dict[str, Module], donor_config: dict[str, str]) -> set[str]:
    roots = set()
    for name in modules:
        module = modules[name]
        if name.startswith("vendor/oplus") or name.startswith("//vendor/oplus"):
            continue
        lowered = name.lower()
        if (
            "canoe" in lowered
            or "qcom_q6v5_pas" in lowered
            or "wcd939x-i2c" in lowered
            or "wcd_" in lowered
            or "wcd-usbss" in lowered
            or "soundwire" in lowered
            or "/swr" in lowered
            or "lpass" in lowered
            or "pcie" in lowered
            or name.endswith("/pci-msm-drv")
        ) and "ufs" not in lowered and module.config in donor_config:
            roots.add(name)
    required = {
        "drivers/pinctrl/qcom/pinctrl-canoe",
        "drivers/interconnect/qcom/qnoc-canoe",
        "drivers/remoteproc/qcom_q6v5_pas",
    }
    missing = sorted(required - roots)
    if missing:
        raise SystemExit("required Canoe roots missing: " + ", ".join(missing))
    return roots


def dependency_closure(
    modules: dict[str, Module],
    roots: set[str],
    donor_config: dict[str, str],
) -> tuple[set[str], set[str]]:
    selected = set()
    unresolved = set()
    pending = list(sorted(roots))
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        module = modules.get(name)
        if module is None:
            # External Oplus labels are intentionally excluded: the runtime
            # profile must not pull the Oplus vendor feature layer into Kconfig.
            if name.startswith("vendor/oplus") or name.startswith("//vendor/oplus"):
                continue
            # A few donor registry entries list source-only helper names
            # (for example hab/hab) that are compiled as part of another
            # module and do not have their own registry entry. Keep them out
            # of the generated config; Bazel will still validate the actual
            # source closure during analysis.
            unresolved.add(name)
            continue
        if is_excluded(module):
            continue
        if module.config.startswith("CONFIG_OPLUS_") or "aizerofs" in module.name:
            continue
        if module.config not in donor_config:
            unresolved.add(f"{name} ({module.config})")
            continue
        selected.add(name)
        pending.extend(module.deps)
    return selected, unresolved


def write_config(
    output: Path,
    modules: dict[str, Module],
    selected: set[str],
    unresolved: set[str],
    donor_config: dict[str, str],
) -> None:
    configs = {modules[name].config for name in selected}
    configs.update(
        {
            "CONFIG_ARCH_CANOE",
            "CONFIG_CFG80211",
            "CONFIG_MAC80211",
            "CONFIG_PCI_MSM",
            "CONFIG_PINCTRL_MSM",
            "CONFIG_COMMON_CLK_QCOM",
            "CONFIG_INTERCONNECT_QCOM_RPMH",
        }
    )
    missing = sorted(config for config in configs if config not in donor_config)
    if missing:
        raise SystemExit("selected configs absent from canoe_perf.bzl: " + ", ".join(missing))

    values = {config: donor_config[config] for config in configs}
    excluded = sorted(
        config
        for config in values
        if config in EXCLUDED_CONFIGS
        or any(config.startswith(prefix) for prefix in EXCLUDED_CONFIG_PREFIXES)
    )
    if excluded:
        raise SystemExit("excluded configs leaked into runtime closure: " + ", ".join(excluded))
    values["CONFIG_ARCH_CANOE"] = "y"
    output.write_text(
        "# Generated by generate-canoe-runtime-config.py; do not edit.\n"
        "# This is a dependency closure, not the full canoe_perf profile.\n"
        + ("# Unregistered source-only deps: " + ", ".join(sorted(unresolved)) + "\n" if unresolved else "")
        + "canoe_runtime_config = {\n"
        + "".join(f'    "{key}": "{values[key]}",\n' for key in sorted(values))
        + "}\n",
        encoding="utf-8",
    )
    print(f"generated {output}: roots/closure configs={len(values)} modules={len(selected)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--soc-repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    modules = parse_modules(args.soc_repo)
    donor_config = parse_config(args.soc_repo / "configs/canoe_perf.bzl")
    roots = select_roots(modules, donor_config)
    selected, unresolved = dependency_closure(modules, roots, donor_config)
    if unresolved:
        print("unregistered source-only deps omitted: " + ", ".join(sorted(unresolved)))
    write_config(args.output, modules, selected, unresolved, donor_config)


if __name__ == "__main__":
    main()
