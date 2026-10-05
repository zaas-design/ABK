#!/usr/bin/env python3
"""Normalize the donor Canoe device-tree labels for the ABK kernel workspace."""

from __future__ import annotations

import sys
from pathlib import Path


QCOM_LOAD = (
    'load("//qcom/opensource/devicetree:qcom/platform_map.bzl", '
    '_get_dtb_list = "get_dtb_list", '
    '_get_dtbo_list = "get_dtbo_list")'
)
QCOM_DTSTREE = 'return "//qcom/opensource/devicetree:msm_dt"'
OLD_DTSTREE = 'return "//soc-repo/arch/arm64/boot/dts/vendor:msm_dt"'
OLD_OPLUS_LOAD = 'load("//build/kernel/oplus:oplus_modules.bzl", "define_oplus_ddk_modules")'
NEW_OPLUS_LOAD = 'load("//oplus/bazel:oplus_modules.bzl", "define_oplus_ddk_modules")'


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: normalize-canoe-dt.py PATH_TO_MSM_KERNEL_EXTENSIONS")

    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    if path.name == "msm_kernel_extensions.bzl":
        lines = [line for line in text.splitlines() if "platform_map.bzl" not in line]
        normalized = QCOM_LOAD + "\n" + "\n".join(lines) + "\n"
        normalized = normalized.replace(OLD_DTSTREE, QCOM_DTSTREE)
        if QCOM_LOAD not in normalized or QCOM_DTSTREE not in normalized:
            raise SystemExit("Canoe DT label normalization did not produce expected Bazel labels")
        if "soc-repo/arch/arm64/boot/dts/vendor" in normalized:
            raise SystemExit("stale vendor DT label remains after Canoe normalization")
    elif path.name == "android_build.bzl":
        normalized = text.replace(OLD_OPLUS_LOAD, NEW_OPLUS_LOAD)
        if OLD_OPLUS_LOAD in normalized:
            raise SystemExit("stale Oplus Bazel label remains after Canoe normalization")
        if NEW_OPLUS_LOAD not in normalized:
            raise SystemExit("Canoe Oplus Bazel label was not found")
    else:
        raise SystemExit(f"unsupported Bazel file for Canoe normalization: {path.name}")

    path.write_text(normalized, encoding="utf-8")
    print(f"normalized Canoe DT labels in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
