# TB323FU `.043`: сборка согласованного Binder-модуля

Для профиля с совместимыми `boot` и `system_dlkm` workflow `Android 内核构建-类 LineageOS 源码` распознаёт маркер `TB323FU043_STOCK_GKI_TRUST` в поле `custom_kernel_options`. Маркер занимает отдельную строку, а настройки ядра можно указать рядом:

```text
TB323FU043_STOCK_GKI_TRUST
USER_NS=y
```

Маркер добавляет сертификат штатных GKI-модулей TB323FU в kernel trust store и удаляется до разбора Kconfig-настроек. Binder подписывается штатным объявленным Kleaf build key `certs/signing_key.pem`; парный `certs/signing_key.x509` экспортёр извлекает из той же сборки и использует для криптографической проверки подписи. Оба сертификата — GKI и ключа сборки — должны находиться в итоговом `vmlinux`. Прежнее значение, состоящее только из маркера, также поддерживается.

Флаг применим только к закреплённому `android16`/`6.12` исходнику `kernel/common` на commit `1750f757fabea014ecc59d327c0c9d3c15ab1e6d`. На этом 6.12 workflow поддерживает `virtualization_support=off` или `on`; `on` включает закреплённый набор DroidSpaces. KPM и SUSFS можно включить вместе с ним при выбранном закреплённом ReSukiSU Stable. ZRAM, BBG, DDK, NTsync, network enhancements, Re-Kernel и пользовательские внешние модули для этого профиля должны оставаться выключенными.

Для запуска GitHub Actions проверено: default branch репозитория — `dev`, и в ней уже есть `.github/workflows/kernel-source.yml` с `workflow_dispatch`, так что отсутствие workflow-файла в default branch не является причиной. Однако обе версии workflow имеют по 25 inputs, но наборы не совпадают: `dev` содержит `custom_ref` и `device_label`, целевая ветка — `source_layout` и `kernel_localversion_override`. Для надёжного ручного запуска через UI input-схему нужно синхронизировать с default branch. Ранее API-авторизация запуска вернула `Must have admin rights to Repository`; секреты forked PR к этому ручному запуску публичного репозитория не относятся.

При включённом флаге сборка сохраняет `BUILD_SYSTEM_DLKM=1` и штатный порядок GKI-модулей, затем материализует Kleaf dist в `out/kernel_aarch64/dist`. Экспортёр берёт единственный `rust_binder.ko` из `system_dlkm_staging_archive.tar.gz` этого dist; финальный `Image` после KPM берётся из `bazel-bin/common/kernel_aarch64/Image`. Оба результата относятся к одной Bazel-сборке. Проверяются `vermagic`, CMS-подпись Binder сертификатом того же Kleaf build и присутствие DER сертификатов GKI и сборки в итоговом `vmlinux`. `BUILD_INFO.txt` связывает Binder с полным `kernel.release` и SHA-256 финального `Image`; метаданные также входят в `*-Images.zip`. KPM считается применённым только при наличии изменённого `oImage`, маркеров успешной упаковки в логах и неизменного banner релиза. Если интеграция KPM откатывается, экспортёр останавливает доверенную финальную сборку. После KPM workflow заново создаёт `Image.lz4` из финального `Image` и проверяет распаковку gzip и lz4 побайтно. Созданный подписанный bundle классифицируется как `SYSTEM_DLKM_MODULES`.

Run `37620143917` остановился ещё до компиляции: защитная проверка ожидала буквальную строку `BUILD_SYSTEM_DLKM=1`, но не нашла её в файле build config на момент запуска. Исправление нормализует все присваивания этих двух параметров и добавляет явные значения в конец файла (`1` и stock `MODULES_ORDER` для доверенного профиля; `0` для остальных). Проверены YAML, shell-синтаксис и три формы исходного присваивания на временных fixtures. Следующая пересборка ещё не запущена.

Run `37642717723` был ошибочно отправлен с `virtualization_support=off`, а затем упал на не объявленном в Kleaf signing key; его артефакты не считать финальными.

Финальный dispatch `37649518516` на commit `41a2109ce466dbd63977fc6fe5641a089fb16660` завершился успешно. В нём включены pinned ReSukiSU Stable, SUSFS, KPM и DroidSpaces commit `2ac9f5af650ae20149d9d46606526d5b003ca626`; компиляция, применение KPM, экспорт и проверка подписанного `rust_binder.ko`, упаковка и загрузка артефактов прошли. [Run и артефакты](https://github.com/zaas-design/ABK/actions/runs/37649518516); основной архив `ReSukiSU_kernel-android16-6.12-30.zip`, SHA-256 `55382a48c3927b256d974284be78367d5993e412d657d66b1c9bbbeb65bb3794`.

`SystemDlkmModules.zip` содержит только новый Binder-модуль и метаданные сборки; это не готовый образ `system_dlkm.img`. Для его включения в стоковый набор ещё требуется собрать и проверить ext4-образ с остальными штатными модулями, а также решить проверку AVB/dm-verity и процедуру отката. Наличие артефактов само по себе не разрешает запись разделов устройства.
