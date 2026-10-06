# K0 rebuild with stock TB323FU GKI trust

This branch prepares a repeat of K0 from AOSP `kernel/common` commit
`1750f757fabea014ecc59d327c0c9d3c15ab1e6d` with a reserved marker in the
existing custom-kernel-options input:
the public certificate verified from the actual TB323FU `.043` `boot.img`.
The existing kernel-signature and protected-symbol settings remain enabled.
The action rejects a different source commit, kernel line, feature profile,
or a non-empty device/localversion label. The empty label matches the prior
K0 build inputs and avoids changing its release string.

Dispatch `.github/workflows/kernel-source.yml` on this branch with:

| Input | Value |
| --- | --- |
| `source_repo` | `https://android.googlesource.com/kernel/common` |
| `source_ref` | `1750f757fabea014ecc59d327c0c9d3c15ab1e6d` |
| `source_layout` | `common` |
| `source_private` | `false` |
| `defconfigs` | `gki_defconfig` |
| `version_overrides` | `{"os_patch_level":"2025-06","kernel_version_override":""}` |
| `kernelsu_variant` | `None` |
| `kernelsu_branch` | `Stable(标准)` |
| `version` | empty |
| `kernel_localversion_override` | empty |
| `build_time` | `N` |
| `virtualization_support` | `off` |
| `use_zram`, `use_bbg`, `use_ddk`, `use_ntsync` | `false` |
| `use_networking`, `use_kpm`, `use_rekernel` | `false` |
| `cancel_susfs` | `true` |
| `zram_full_algo` | `false` |
| `zram_extra_algos`, `custom_external_modules` | empty |
| `custom_kernel_options` | `TB323FU043_STOCK_GKI_TRUST` |

Before considering hardware use, inspect the run's `.config`, source manifest,
`Module.symvers`, `vmlinux`, signer certificate set, raw `Image`, and signed
bundles. Compare stock-module CRCs to the previous K0 contract. Verify that
the certificate in the built kernel validates the signature of stock
`system_dlkm/modules/rfkill.ko`; verify that its protected exports remain
protected. Pack the boot separately with the established `.043` GBL-preserve
path and keep the boot partition as the only possible flash target.

The workflow YAML parses and the guarded shell step passes `bash -n`. This
document is dispatch configuration, not evidence that a new run has started
or that the built candidate passes runtime verification.
