# TB323FU `.043` — vendor_dlkm extraction

Дата: 2026-10-05

## Источник

QFIL-прошивка:

`/Users/alex/Documents/Android/Lenovo_Legion_Y700_TB323FU_ZUXOS_2.0.11.043_090326_QFIL/Firmware/`

QFIL описывает `super` восемью кусками в `rawprogram_unsparse0.xml`. Временный
raw-образ был собран с началом super-раздела в offset 0; его размер составил
15 759 126 528 байт. После извлечения временный raw-образ и остальные logical
partitions удалены. Исходные `super_1.img`…`super_8.img` не изменялись.

Распаковка подтвердила LP metadata v10.2: 7 logical partitions, включая
`vendor_dlkm_a`.

## Сохранённые результаты

- точный образ: `vendor_dlkm_a.img`, 114 372 608 байт;
- SHA-256 образа: `5fabff9258b30bd211587daca755ac7fa6d0c51f43873b682e697a56611f842c`;
- извлечённые файлы: `vendor_dlkm/modules/`;
- kernel modules: 305 файлов `.ko`;
- metadata: `modules.dep`, `modules.alias`, `modules.load`, `modules.softdep`,
  `modules.blocklist`, `system_dlkm.modules.blocklist`.

У всех 305 штатных модулей одинаковый vermagic:

`6.12.30-android16-5-maybe-dirty-4k SMP preempt mod_unload modversions aarch64`

В `vendor_dlkm` нет `Module.symvers` или `modules.symbols`, поэтому это уже
достаточная база для проверки release/vermagic и списка модулей, но не полный
CRC-gate. Для CRC остаётся использовать штатный `vmlinux` из той же прошивки и
таблицы `__versions` модулей либо точный vendor source.

Полная host-проверка ABI stock `.043` выполнена отдельно: все 504 модуля из
штатного `/proc/modules` найдены, проверено 41 540 записей CRC. 36 577 CRC
совпали со штатным `vmlinux`, ещё 4 962 — с экспортами модулей; несовпадений
нет. Единственный нерешённый импорт — `goodix_ts → qts_client_register`;
`goodix_ts` не входит в штатный список загруженных модулей, поэтому этот импорт
не связываем с зависанием K1.

## Остальные наборы модулей

Из того же `super` извлечён `system_dlkm_a.img`:

- размер: 14 565 376 байт;
- SHA-256: `25129dba405aeffa89fd3b4fcc2f11d75263771f318e3151df1d7a9dc3b4f7b5`;
- 103 модуля в `system_dlkm/modules/`;
- все 103 имеют vermagic
  `6.12.30-android16-5-g1750f757fabe-ab13938768-4k SMP preempt mod_unload modversions aarch64`;
- все 103 содержат appended module signature.

Из vendor ramdisk `vendor_boot.img` извлечены 324 модуля и metadata:

`vendor_boot-modules/modules/`

Все 324 имеют vermagic
`6.12.30-android16-5-maybe-dirty-4k SMP preempt mod_unload modversions aarch64`;
appended signature у них не обнаружена. Сохранён также
`first_stage_ramdisk/fstab.qcom`.

Это различающиеся классы модулей: system_dlkm — GKI-модули с подписью, а
vendor_dlkm/vendor_boot — vendor-модули с отдельным ABI-контрактом. В штатной
конфигурации при этом включены `CONFIG_MODVERSIONS=y`,
`CONFIG_EXTENDED_MODVERSIONS=y`, `CONFIG_MODULE_SIG=y`,
`CONFIG_MODULE_SIG_ALL=y` и `CONFIG_MODULE_SIG_PROTECT=y`;
`CONFIG_MODULE_SIG_FORCE` не включён. Поэтому отсутствие appended signature у
vendor-модулей само по себе не доказывает ошибку.

## Подготовленная доработка workflow

В `.github/workflows/build.yml` и `.github/workflows/kernel-custom.yml` добавлен
отдельный параметр `kernel_localversion_override`.

Для следующего минимального K1R-кандидата:

```text
version: TB323FU
kernel_localversion_override: -android16-5-maybe-dirty-4k
ksu_variant: ReSukiSU
use_zram: false
use_bbg: false
use_ddk: false
use_ntsync: false
use_networking: false
use_kpm: false
use_rekernel: false
enable_susfs: false
virtualization_support: off
```

Это должно дать release `6.12.30-android16-5-maybe-dirty-4k`, не смешивая
device label `TB323FU` с kernel release. Runner и прошивка после этой правки не
запускались.

Перед запуском следующего runner обязательны отдельные проверки:

1. Для каждого набора сравнить vermagic, зависимости и `__versions` либо
   `__version_ext_names`/`__version_ext_crcs` с новым `vmlinux`/`Module.symvers`.
2. Для system_dlkm проверить, что новое ядро доверяет штатной цепочке GKI-
   подписей и не ломает protected-module policy.
3. Для vendor_dlkm и vendor_boot проверить загрузку по `modules.dep`,
   `modules.softdep` и `modules.load`; особенно аудио, Wi-Fi и Qualcomm IPC.
4. В артефакты сборки сохранить `.config`, `vmlinux`, `Module.symvers`,
   manifest, compiler/toolchain и commit ReSukiSU.
