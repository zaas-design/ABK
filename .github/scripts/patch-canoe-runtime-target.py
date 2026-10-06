#!/usr/bin/env python3
"""Add the generated selective Canoe runtime target to a donor checkout."""

from __future__ import annotations

import argparse
from pathlib import Path


RUNTIME_LOAD = 'load(":configs/canoe_runtime.bzl", "canoe_runtime_config")'
RUNTIME_FUNCTION = '''

def define_canoe_runtime():
    runtime_perf_opts = boot_image_opts(
        earlycon_addr = "qcom_geni,0x00a9c000",
        kernel_vendor_cmdline_extras = ["bootconfig", "nosoftlockup console=ttynull qcom_geni_serial.con_enabled=0"],
        board_kernel_cmdline_extras = ["nosoftlockup console=ttynull qcom_geni_serial.con_enabled=0"],
        board_bootconfig_extras = ["androidboot.serialconsole=0"],
    )
    define_typical_android_build(
        name = "canoe_runtime",
        consolidate_config = canoe_runtime_config,
        perf_config = canoe_runtime_config,
        consolidate_build_img_opts = runtime_perf_opts,
        perf_build_img_opts = runtime_perf_opts,
    )
'''


def add_once(text: str, needle: str, addition: str) -> str:
    if addition.strip() in text:
        return text
    if needle not in text:
        raise SystemExit(f"cannot find insertion point: {needle}")
    return text.replace(needle, needle + addition, 1)


def patch_canoe(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if RUNTIME_LOAD not in text:
        text = text.replace(
            'load(":configs/canoe_perf.bzl", "canoe_perf_config")',
            'load(":configs/canoe_perf.bzl", "canoe_perf_config")\n' + RUNTIME_LOAD,
            1,
        )
    if "def define_canoe_runtime():" not in text:
        text += RUNTIME_FUNCTION
    path.write_text(text, encoding="utf-8")


def patch_build(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    load = '    "define_canoe_runtime",\n'
    if '"define_canoe_runtime"' not in text:
        text = text.replace('    "define_canoe_tuivm",\n', '    "define_canoe_tuivm",\n' + load, 1)
    if "define_canoe_runtime()" not in text:
        text = add_once(text, "define_canoe()\n", "define_canoe_runtime()\n")
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canoe", type=Path, required=True)
    parser.add_argument("--build", type=Path, required=True)
    args = parser.parse_args()
    patch_canoe(args.canoe)
    patch_build(args.build)
    print(f"patched selective Canoe target in {args.canoe} and {args.build}")


if __name__ == "__main__":
    main()
