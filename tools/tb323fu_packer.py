#!/usr/bin/env python3
"""Pack an ABK kernel into the stock Lenovo TB323FU boot container.

TB323FU uses a 96 MiB boot partition with a zero-ramdisk Android boot image.
The stock image is kept as the container: its header is preserved, only the
kernel payload is replaced, and a fresh AVB hash footer is added.
"""

from __future__ import annotations

import argparse
import os
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path


ANDROID_MAGIC = b"ANDROID!"
ARM64_IMAGE_MAGIC = b"ARMd"
AVB_FOOTER_MAGIC = b"AVBf"
KERNEL_START = 4096
KERNEL_SIZE_OFFSET = 8
RAMDISK_SIZE_OFFSET = 12
KERNEL_MAGIC_OFFSET = 56
AVB_FOOTER_SIZE = 64
TB323FU_PARTITION_SIZE = 96 * 1024 * 1024


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_boot(path: Path, label: str) -> bytes:
    data = path.read_bytes()
    require(data[:8] == ANDROID_MAGIC, f"{label}: not an Android boot image")
    require(len(data) >= 4096 + KERNEL_MAGIC_OFFSET + 4, f"{label}: image is truncated")
    require(
        data[KERNEL_START + KERNEL_MAGIC_OFFSET : KERNEL_START + KERNEL_MAGIC_OFFSET + 4]
        == ARM64_IMAGE_MAGIC,
        f"{label}: kernel is not an ARM64 Image",
    )
    return data


def avb_command(avbtool: Path, args: list[str]) -> list[str]:
    if avbtool.suffix == ".py":
        return [sys.executable, str(avbtool), *args]
    return [str(avbtool), *args]


def stock_avb_arguments(avbtool: Path, stock_path: Path) -> list[str]:
    result = subprocess.run(
        avb_command(avbtool, ["info_image", "--image", str(stock_path)]),
        check=True,
        capture_output=True,
        text=True,
    )
    output = result.stdout
    rollback = re.search(r"^Rollback Index:\s*(\d+)$", output, re.MULTILINE)
    rollback_location = re.search(r"^Rollback Index Location:\s*(\d+)$", output, re.MULTILINE)
    require(rollback is not None, "stock boot: AVB rollback index is missing")
    require(rollback_location is not None, "stock boot: AVB rollback index location is missing")

    avb_args = [
        "--rollback_index",
        rollback.group(1),
        "--rollback_index_location",
        rollback_location.group(1),
    ]
    for line in output.splitlines():
        line = line.strip()
        if not line.startswith("Prop: ") or " -> '" not in line or not line.endswith("'"):
            continue
        key, value = line[6:].split(" -> '", 1)
        avb_args.extend(["--prop", f"{key}:{value[:-1]}"])
    return avb_args


def pack(args: argparse.Namespace) -> None:
    stock_path = Path(args.stock_boot).resolve()
    kernel_boot_path = Path(args.kernel_boot).resolve()
    output_path = Path(args.output).resolve()
    avbtool_path = Path(args.avbtool).resolve()
    key_path = Path(args.key).resolve()

    stock = read_boot(stock_path, "stock boot")
    kernel_boot = read_boot(kernel_boot_path, "kernel boot")
    partition_size = args.partition_size

    require(len(stock) == partition_size, f"stock boot: expected {partition_size} bytes, got {len(stock)}")
    require(kernel_boot_path != output_path, "output must not overwrite the kernel input")
    require(avbtool_path.is_file(), f"avbtool not found: {avbtool_path}")
    require(key_path.is_file(), f"AVB key not found: {key_path}")
    stock_avb_args = stock_avb_arguments(avbtool_path, stock_path)

    stock_kernel_size = u32(stock, KERNEL_SIZE_OFFSET)
    stock_ramdisk_size = u32(stock, RAMDISK_SIZE_OFFSET)
    kernel_size = u32(kernel_boot, KERNEL_SIZE_OFFSET)

    require(stock_ramdisk_size == 0, f"stock boot: expected empty ramdisk, got {stock_ramdisk_size} bytes")
    require(stock_kernel_size > 0, "stock boot: empty kernel")
    require(kernel_size > 0, "kernel boot: empty kernel")
    require(KERNEL_START + kernel_size + AVB_FOOTER_SIZE < partition_size, "kernel does not fit in TB323FU boot partition")

    kernel_start = KERNEL_START
    new_kernel = kernel_boot[KERNEL_START : KERNEL_START + kernel_size]
    require(len(new_kernel) == kernel_size, "kernel boot: kernel payload is truncated")
    require(new_kernel[KERNEL_MAGIC_OFFSET : KERNEL_MAGIC_OFFSET + 4] == ARM64_IMAGE_MAGIC, "kernel boot: invalid ARM64 payload")

    packed = bytearray(stock[: kernel_start + kernel_size])
    packed[KERNEL_SIZE_OFFSET : KERNEL_SIZE_OFFSET + 4] = struct.pack("<I", kernel_size)
    packed[kernel_start : kernel_start + kernel_size] = new_kernel

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent)
    os.close(fd)
    temporary_path = Path(temporary_name)
    try:
        temporary_path.write_bytes(packed)
        command = avb_command(
            avbtool_path,
            [
                "add_hash_footer",
                "--image",
                str(temporary_path),
                "--partition_name",
                args.partition_name,
                "--partition_size",
                str(partition_size),
                "--algorithm",
                args.algorithm,
                "--key",
                str(key_path),
                *stock_avb_args,
            ],
        )
        subprocess.run(command, check=True)
        result = temporary_path.read_bytes()
        require(len(result) == partition_size, f"packed boot: expected {partition_size} bytes, got {len(result)}")
        require(result[-AVB_FOOTER_SIZE:-AVB_FOOTER_SIZE + 4] == AVB_FOOTER_MAGIC, "packed boot: AVB footer is missing")
        output_path.unlink(missing_ok=True)
        os.replace(temporary_path, output_path)
    finally:
        temporary_path.unlink(missing_ok=True)

    print(f"packed {output_path} ({partition_size} bytes)")
    print(f"kernel: {stock_kernel_size} -> {kernel_size} bytes")
    print(f"partition: {args.partition_name}, AVB: {args.algorithm}")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--stock-boot", required=True, help="stock TB323FU image/boot.img")
    result.add_argument("--kernel-boot", required=True, help="ABK-generated Android boot image")
    result.add_argument("--output", required=True, help="packed boot image to create")
    result.add_argument("--avbtool", required=True, help="AOSP avbtool executable or avbtool.py")
    result.add_argument("--key", required=True, help="AVB signing key in PEM format")
    result.add_argument("--partition-name", default="boot")
    result.add_argument("--algorithm", default="SHA256_RSA2048")
    result.add_argument("--partition-size", type=int, default=TB323FU_PARTITION_SIZE)
    return result


if __name__ == "__main__":
    try:
        pack(parser().parse_args())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
