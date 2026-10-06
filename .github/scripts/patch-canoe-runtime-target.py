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
        dtb_target = "canoe",
        module_list_target = "canoe",
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


def patch_android_build(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    old_single_signature = "        implicit_config_fragment = None,\n        config_path = None):"
    new_single_signature = "        implicit_config_fragment = None,\n        config_path = None,\n        module_list_target = None):"
    if old_single_signature in text:
        text = text.replace(old_single_signature, new_single_signature, 1)
    elif new_single_signature not in text:
        raise SystemExit("cannot find define_single_android_build signature")
    old_stem = '    stem = "{}_{}".format(name, variant)\n'
    new_stem = old_stem + '    module_target = module_list_target if module_list_target != None else name\n'
    if new_stem not in text:
        if old_stem in text:
            text = text.replace(old_stem, new_stem, 1)
        else:
            raise SystemExit("cannot find define_single_android_build stem")
    old_signature = "        consolidate_build_img_opts = None,\n        perf_build_img_opts = None,\n        **kwargs):"
    new_signature = "        consolidate_build_img_opts = None,\n        perf_build_img_opts = None,\n        dtb_target = None,\n        **kwargs):"
    if old_signature in text:
        text = text.replace(old_signature, new_signature, 1)
    elif new_signature not in text:
        raise SystemExit("cannot find define_typical_android_build signature")
    old_call = "        dtb_target = name,\n        **kwargs"
    new_call = "        dtb_target = dtb_target if dtb_target != None else name,\n        **kwargs"
    if old_call in text:
        text = text.replace(old_call, new_call, 1)
    elif new_call not in text:
        raise SystemExit("cannot find define_typical_android_build dtb call")
    for module_file in ("modules.list.msm", "modules.vendor_blocklist.msm", "modules.systemdlkm_blocklist.msm"):
        old = '"modules-lists/{}.{{}}".format(name)'.format(module_file)
        new = '"modules-lists/{}.{{}}".format(module_target)'.format(module_file)
        if old in text:
            text = text.replace(old, new)
        elif new not in text:
            raise SystemExit(f"cannot find module-list reference: {module_file}")
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canoe", type=Path, required=True)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--android-build", type=Path, required=True)
    args = parser.parse_args()
    patch_canoe(args.canoe)
    patch_build(args.build)
    patch_android_build(args.android_build)
    print(f"patched selective Canoe target in {args.canoe}, {args.build}, and {args.android_build}")


if __name__ == "__main__":
    main()
