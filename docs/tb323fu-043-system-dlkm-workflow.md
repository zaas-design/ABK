# TB323FU `.043`: сборка согласованного Binder-модуля

Для профиля с совместимыми `boot` и `system_dlkm` workflow `Android 内核构建-类 LineageOS 源码` распознаёт маркер `TB323FU043_STOCK_GKI_TRUST` в поле `custom_kernel_options`. Маркер занимает отдельную строку, а настройки ядра можно указать рядом:

```text
TB323FU043_STOCK_GKI_TRUST
USER_NS=y
```

Маркер добавляет сертификат штатных GKI-модулей TB323FU в kernel trust store и удаляется до разбора Kconfig-настроек. Прежнее значение, состоящее только из маркера, также поддерживается.

Флаг применим только к закреплённому `android16`/`6.12` исходнику `kernel/common` на commit `1750f757fabea014ecc59d327c0c9d3c15ab1e6d`, с выключенной виртуализацией. KPM и SUSFS можно включить вместе с ним при выбранном закреплённом ReSukiSU Stable. ZRAM, BBG, DDK, NTsync, network enhancements, Re-Kernel и пользовательские внешние модули для этого профиля должны оставаться выключенными.

Для запуска GitHub Actions проверено: default branch репозитория — `dev`, и в ней уже есть `.github/workflows/kernel-source.yml` с `workflow_dispatch`, так что отсутствие workflow-файла в default branch не является причиной. Однако обе версии workflow имеют по 25 inputs, но наборы не совпадают: `dev` содержит `custom_ref` и `device_label`, целевая ветка — `source_layout` и `kernel_localversion_override`. Для надёжного ручного запуска через UI input-схему нужно синхронизировать с default branch. Ранее API-авторизация запуска вернула `Must have admin rights to Repository`; секреты forked PR к этому ручному запуску публичного репозитория не относятся.

При включённом флаге сборка берёт `rust_binder.ko` только из `system_dlkm_staging_archive.tar.gz` того же dist, что и финальный `Image`. Проверяются `vermagic`, криптографическая подпись модуля штатным сертификатом, наличие DER-сертификата в итоговом `vmlinux` и настройки Kconfig. `BUILD_INFO.txt` связывает Binder с полным `kernel.release` и SHA-256 финального `Image`; метаданные также входят в `*-Images.zip`. После KPM workflow заново создаёт `Image.lz4` из финального `Image` и проверяет распаковку gzip и lz4 побайтно. Созданный подписанный bundle классифицируется как `SYSTEM_DLKM_MODULES`.

`SystemDlkmModules.zip` содержит только новый Binder-модуль и метаданные сборки; это не готовый образ `system_dlkm.img`. Для его включения в стоковый набор ещё требуется собрать и проверить ext4-образ с остальными штатными модулями, а также решить проверку AVB/dm-verity и процедуру отката. Наличие артефактов само по себе не разрешает запись разделов устройства.
