#!/usr/bin/env python3
"""Normalize the donor Canoe device-tree labels for the ABK kernel workspace."""

from __future__ import annotations

import sys
import re
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
OLD_OPLUS_PREFIX = "//build/kernel/oplus:"
NEW_OPLUS_PREFIX = "//oplus/bazel:"
QCOM_DT_MAKEFILE = ("qcom", "opensource", "devicetree", "Makefile")
QCOM_PLATFORM_DT_MAKEFILE = ("qcom", "opensource", "devicetree", "qcom", "Makefile")
QCOM_DT_BUILD = ("qcom", "opensource", "devicetree", "BUILD.bazel")
QCOM_SUBDIR_LINE = "subdir-y += qcom"
OPLUS_DT_LINES = {
    "subdir-y += oplus",
    '"oplus/Makefile",',
    '"oplus/**/*.dtsi",',
    '"oplus/**/*.dts",',
    '"oplus/**/*.dtso",',
}


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
    elif path.parts[-5:] == QCOM_PLATFORM_DT_MAKEFILE:
        # Bazel's Canoe target requests separate base DTBs and DTBOs.  The
        # donor Kbuild also adds every composite base+overlay DTB, but those
        # composites are not outputs of this target and some board overlays
        # cannot be applied to the generic base DTB.
        normalized = re.sub(
            r"(?m)^(\s*)dtb-y \+= \$\([A-Za-z0-9_-]+-dtb-y\) \$\(([A-Za-z0-9_-]+-overlays-dtb-y)\)\s*$",
            r"\1dtb-y += $(\2)",
            text,
        )
    elif path.parts[-4:] == QCOM_DT_MAKEFILE:
        # This donor carries no qcom/opensource/devicetree/oplus tree.  The
        # upstream Makefile nevertheless unconditionally adds it, which makes
        # the otherwise valid Canoe DT package fail during Kbuild.
        if not (path.parent / "oplus" / "Makefile").is_file():
            lines = []
            for line in text.splitlines():
                stripped = line.strip()
                if stripped in OPLUS_DT_LINES:
                    continue
                if stripped == "#subdir-y += qcom":
                    line = QCOM_SUBDIR_LINE
                lines.append(line)
            normalized = "\n".join(lines) + "\n"
            if (path.parent / "qcom").is_dir() and QCOM_SUBDIR_LINE not in normalized.splitlines():
                raise SystemExit("Canoe DT Makefile does not enable the available qcom DT directory")
        else:
            normalized = text
    elif path.parts[-4:] == QCOM_DT_BUILD:
        # Keep Bazel's source list consistent with the Kbuild Makefile when
        # the optional Oplus DT overlay is absent from the donor checkout.
        if not (path.parent / "oplus" / "Makefile").is_file():
            normalized = "\n".join(
                line for line in text.splitlines() if line.strip() not in OPLUS_DT_LINES
            ) + "\n"
        else:
            normalized = text
    else:
        normalized = text.replace(OLD_OPLUS_PREFIX, NEW_OPLUS_PREFIX)
        if OLD_OPLUS_PREFIX in normalized:
            raise SystemExit("stale Oplus Bazel label remains after Canoe normalization")
        if OLD_OPLUS_PREFIX not in text:
            raise SystemExit(f"unsupported Bazel file for Canoe normalization: {path.name}")
    path.write_text(normalized, encoding="utf-8")
    print(f"normalized Canoe donor file in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
