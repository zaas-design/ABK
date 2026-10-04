# TB323FU / ZUXOS 2.0.11.043 — kernel handoff

Дата обновления: 2026-10-04

Этот файл — единственный рабочий handoff для Lenovo TB323FU (Legion Y700 Gen 5) на ZUXOS `2.0.11.043`. Исторический журнал экспериментов с `.088` находится отдельно: `docs/tb323fu-handoff-088-history.md`.

## Цель проекта

Подготовить и проверять device-specific GKI-ядро для TB323FU `.043` с:

- встроенным KernelSU/ReSukiSU;
- SUSFS;
- поддержкой DroidSpaces, включая только подтверждённые для kernel `6.12` kABI-патчи;
- AnyKernel3-архивом для установки в `boot_a`/активный `boot_<slot>`;
- воспроизводимым откатом через EDL/QDL.

Порядок работ: сначала подтвердить штатную `.043`-цепочку, затем проверять ядро на этой же версии прошивки. Не смешивать образы `.043` и `.088`.

## Согласованный план от 3 октября

Подробный рабочий план: [tb323fu-043-kernel-plan-2026-10-03.md](tb323fu-043-kernel-plan-2026-10-03.md). Пользователь одобрил последовательность: штатная `.043` → контроль GBL со штатным ядром → пересборка baseline K0 → встроенный ReSukiSU K1 → Droidspaces K2. SUSFS, предусмотренный целью этого handoff, добавляется отдельным K3 после проверки основной версии.

Восстановление правильного `init_boot_a` подтверждено пользователем; локальный baseline повторно сравнен с пакетом `.043` побайтно. `edl-before-03` сохраняется как исторический снимок до G1. После последнего отката актуальный сохранённый комплект — `artifacts/tb323fu-043-ltbox-crash-recovery-20261004/sessions/restore-02/`; перед новым аппаратным тестом снять свежие GPT и девять разделов. Чистый QFIL-пакет `.043` сохраняется отдельно как источник полного stock-восстановления.

После уточнения пользователя первым проверен точный PRC EFI LTBox `6.2.192-mod2` со штатными boot/init_boot `.043`; результат G1 и последующее LTBox-восстановление описаны ниже. Подготовлен [пакет первого теста](../artifacts/tb323fu-043-ltbox-gbl-test-20261003/README.md): оригинальный EFI с проверенным pin SHA, входы `.043`, release-исходники и host-отчёт. Статический detector LTBox для ABL `.043` вернул Yes; host-патчер изменил 43 байта и выдал tracking fallback warning. Multi-image Sahara loader проверен при чтении и восстановлении. GBL записывался; наше новое ядро не проверялось на планшете.

## Каноническое состояние и baseline

- Устройство: Lenovo TB323FU, Baldur, Legion Y700 Gen 5, PRC.
- Bootloader: разблокирован.
- Прошивка: Android 16, ZUXOS `2.0.11.043`.
- Наблюдавшийся build ID: `TB323FU_CN_OPEN_USER_Q00020.0_A16_ZUXOS_2.0.11.043_ST_260309`.
- Последний подтверждённый активный слот: `A`.
- Рабочая директория: `/Users/alex/Documents/Android/ABK-dev`.
- Папка прошивки: `/Users/alex/Documents/Android/Lenovo_Legion_Y700_TB323FU_ZUXOS_2.0.11.043_090326_QFIL`.
- QDL: `/private/tmp/qdl-tb323fu/build/qdl`.
- Firehose programmer из `.043`: `Firmware/prog_firehose_ddr.elf`.

Основной baseline для `init_boot_a`:

    backups/tb323fu-043-current-baseline/init_boot_a.img

SHA-256:

    14f5920ff67de5c53d3436949644d5d6d5d49e74b475d34a9670a197bc85e224

Этот файл является стоковым `.043` `init_boot_a`, считанным обратно после записи и проверенным побайтно. Это не OTE-патч LTBox. Если LTBox меняет `init_boot`, результат сохраняется отдельным файлом с датой, режимом и SHA-256.

### Текущий backup устройства

Последний сохранённый post-restore комплект: `artifacts/tb323fu-043-ltbox-crash-recovery-20261004/sessions/restore-02/`. Его девять readback повторно проверены против QFIL `.043` плюс нулевое заполнение; `efisp` пустой. Это подтверждённые файлы отката, но в этом каталоге нет свежей GPT. Перед записью нужен новый снимок подключённого устройства.

Исторический current-state backup до G1: `artifacts/tb323fu-043-ltbox-gbl-test-20261003/sessions/edl-before-03/`. В нём сохранены GPT, `efisp`, `boot_a`, `init_boot_a`, `vendor_boot_a`, `vbmeta_a` и `abl_a`.

`boot_a`, `init_boot_a`, `vendor_boot_a` и ABL соответствуют stock `.043`. `vbmeta_a` сохранён именно в наблюдаемом виде, SHA-256 `412a6edc25d79b5ebfabc6a22d07181bc233b7c098535e387bb943588a7e852a`, и отличается от чистого QFIL `vbmeta.img` (`75dc402c80cff702dc123b927d1e608c7b5f234cff44c826a89b2eb323a175df`). Этот вариант не считать повреждённым: он является backup текущего состояния. Для полного чистого восстановления использовать QFIL-пакет `.043`.

Пользователь сообщил, что через LTBox отключал OTA-обновления. По исходникам LTBox это действие меняет OTA-настройки и пакеты Android через ADB; прямое изменение `vbmeta` этим действием не доказано. Поэтому происхождение отличия `vbmeta_a` пока не утверждается, но образ обязательно сохраняется в current-state backup.

Последний LTBox/crashdump current-state backup сохранён отдельно:
`artifacts/tb323fu-043-ltbox-crash-recovery-20261004/sessions/edl-readback-02/`.
Он содержит GPT и readback `efisp`, `abl_a`, `boot_a`, `init_boot_a`,
`vendor_boot_a`, `vbmeta_a`, `vbmeta_system_a`, `dtbo_a` и `recovery_a` до
отката. Не смешивать этот снимок с более ранним `edl-before-03`.

### Результат первого GBL-теста

В [g1-crash-rollback-01](../artifacts/tb323fu-043-ltbox-gbl-test-20261003/sessions/g1-crash-rollback-01/README.md) записан только оригинальный EFI в `efisp`. Readback прошёл, но после reset планшет ушёл в `900e` Crash Dump и Android не загрузился через этот путь. При появлении `9008` current-state `efisp` был восстановлен, readback совпал, затем stock Android `.043` снова загрузился через ADB. Тест не воспроизводит процедуру LTBox полностью: запись выполнялась в оставшийся Firehose после readback, без `reset_to_edl` и новой Sahara-сессии. Это подтверждённое отличие, но не установленная причина падения. Наблюдение «efisp изменён → Crash Dump → efisp восстановлен → Android» сохраняет диагностическую ценность. Следующий контроль требует чистого stock AVB и корректного разделения read и write сессий.

Проверенный образ стокового `boot` из QFIL-пакета:

    Firmware/boot.img
    SHA-256: f83604375fe2398c09f489fb2b2a8e566a879fb025f0bce59d3dda7c2e9495dd

## LTBox crashdump и восстановление `.043` (2026-10-04)

После запуска LTBox планшет появился в Qualcomm EDL/Crash Dump. На экране
зафиксирован ранний ramdump Qualcomm:

    RAMDUMP BUILD ... Mar 9 2026
    IMAGE VERSION STRING-BOOT MXP.2.5.3-00187-KAANAPALI-1
    UFS INQUIRY ID: HICRON NT5126BGBB4U41 0101
    UFS Boot LUN: 1
    UFS Total Size: 512 GB

UFS был обнаружен успешно; падение произошло после ранней инициализации PM/UFS
и до обычной загрузки Android. Это не доказательство сбоя Linux-ядра.

До восстановления сохранены следующие отличия от чистого `.043`:

- `boot_a` имел другой AVB-footer, но распакованное ядро совпадало со стоком
  побайтно: SHA-256 `c77d542d1620dc3d2fb94e1eaecc7384fb1884615e6d03f5a7b6a9c525fe335d`.
- `recovery_a` имел стоковый payload/ramdisk, но другой AVB-footer и ключ.
- `vbmeta_a` и `vbmeta_system_a` использовали не стоковый AVB public-key SHA-1
  `2597c218aae470a130f61162feaae70afd97f011`; у стока `.043` —
  `8fcb864f11f53ed11284615fb67685522085d3a2`.
- `efisp` содержал точный `generic_superfastboot_prc.efi` с нулевым хвостом,
  то есть был provisioned GBL/EFI, а не чистым пустым stock-состоянием.
- `init_boot_a`, `vendor_boot_a`, `dtbo_a` и `abl_a` до отката совпадали со
  стоком.

Точная причина не изолирована, поскольку для восстановления одновременно
возвращались `efisp`, AVB-метаданные и основные A-разделы. Наиболее вероятные
кандидаты — provisioned `efisp` и AVB-путь; изменённое ядро кандидатом не
считается.

### Откат и подтверждение загрузки

В свежей Sahara/Firehose-сессии восстановлены и перечитаны:

    abl_a
    boot_a
    init_boot_a
    vendor_boot_a
    vbmeta_a
    vbmeta_system_a
    dtbo_a
    recovery_a
    efisp

Все девять readback-файлов совпали с подготовленным stock `.043` побайтно.
После одного финального reset планшет загрузился:

- активный слот: `_a`;
- `sys.boot_completed=1`;
- ADB: `HA2JS494`, состояние `device`;
- build: `TB323FU_CN_OPEN_USER_Q00020.0_A16_ZUXOS_2.0.11.043_ST_260309`;
- kernel: `6.12.30-android16-5-g1750f757fabe-ab13938768-4k`.

Подробный отчёт: `artifacts/tb323fu-043-ltbox-crash-recovery-20261004/LTBOX-ANALYSIS.md`.
Лог restore/readback: `artifacts/tb323fu-043-ltbox-crash-recovery-20261004/sessions/restore-02/qdl-restore-readback.log`.

### Правило для следующего теста

Начинать следующий эксперимент только с подтверждённого stock Android `.043`.
Изменять одну переменную за раз: ближайший контроль меняет только `efisp`,
сохраняя подписанные stock AVB-образы и boot. После подтверждения этого пути
тестировать один `boot_a`-артефакт за раз. Между read-фазой и
write обязательно делать свежий `reset_to_edl` и открывать новую Sahara-сессию.
После записи — немедленный readback; reset выполнять только после совпадения.

### Офлайн-аудит ABL после восстановления (2026-10-04)

[Отчёт и скрипт нового baseline](../artifacts/tb323fu-043-abl-audit-20261004/README.md). PE повторно извлечён из `restore-02/abl_a.img` и совпал с прежним входом патчера. Release PRC host-патчер воспроизвёл те же 43 изменённых байта: 13 инструкций и одну UTF-16-строку. Проверены кодировки, branch/ADR targets, локальный поток boot-state и все девять сохранённых post-restore разделов против QFIL `.043`.

Fallback по `0x191B0` выбрал sink значения W8 из ближайшей условной ветки. Линейный tracker теряет X21, проходя через соседний путь обработки ошибки; успешные CBZ-переходы обходят overwrite `0x17D48`. Явной неправильной инструкции или неверного target среди изменений не найдено. Это статический вывод, не доказательство принятия состояния ABL/TEE или исправления Crash Dump.

Следующий контроль: свежие GPT/девять разделов → новая Sahara write-сессия → только оригинальный `efisp` LTBox на чистом `.043`, AVB/boot/ABL сохраняются штатными. При повторной неудаче — diagnostic EFI с видимыми этапами и отдельной проверкой групп патчей. В bundled QDL нет CLI `reset_to_edl`; обычный `qdl reset` не считать эквивалентом. Возможный возврат в stock Android и повторный вход в EDL фиксировать как отдельный способ получения свежей Sahara-сессии.

В сеансе аудита ADB и QDL list не нашли подключённого устройства. Новых чтений разделов, записей и reset не выполнялось. `read-baseline-nine.sh` подготовлен для нового подключения; verifier проверен на офлайн-fixture и отверг повреждённый `vbmeta_system_a`.

## Архитектура тестирования ядра

Для TB323FU GKI-маршрут LTBox работает с `boot_<slot>` и при необходимости с `efisp` через GBL. В этом маршруте `init_boot` не является целевым разделом ядра.

Правила:

1. GKI-ядро заменяет kernel payload в `boot`, а не в `init_boot`.
2. `init_boot_a` baseline используется для восстановления и сравнения, но не модифицируется при обычном GKI-тесте.
3. LTBox OTE/block option — отдельный эксперимент: он может менять `init_boot`; после него обязателен readback и новый SHA-256.
4. Не прошивать собранный 64-MiB `boot*.img` напрямую, если артефакт предназначен для AnyKernel3. Для установки использовать проверенный `AnyKernel3.zip` с `block=boot` и без неподтверждённого device check.
5. Перед каждой записью фиксировать: источник, SHA-256, целевой раздел, активный слот и режим (`GKI`, `LKM`, `OTE`).
6. После каждой записи делать readback. При несовпадении SHA или при неясном целевом разделе дальнейшие записи остановить.

Целевой результат сборки:

- kernel release и конфигурация должны быть сопоставлены со стоковым `.043`;
- KMI/kABI совместимость должна быть проверена до включения проприетарных vendor-модулей;
- встроенные KernelSU/SUSFS должны соответствовать выбранному ReSukiSU Manager;
- DroidSpaces-патчи добавлять по одному и проверять отдельно от root-интеграции;
- перед реальным flash проверять `AnyKernel3`-скрипт, слот и список разделов.

Последний известный full GKI build ABK: [GitHub Actions run 37022452071](https://github.com/zaas-design/ABK/actions/runs/37022452071). Этот run относится к `.043`-ветке подготовки, но каждый новый артефакт нужно проверять заново; старые локальные ZIP не считать каноническими без SHA и отчёта.

## EDL/QDL: обнаружение и права

EDL на macOS определяется как Qualcomm `QUSB_BULK`, обычно vendor `05c6`, product `9008`.

Проверка без записи:

    ioreg -p IOUSB -l -w 0 | rg -i -C 3 'QUSB_BULK|Qualcomm|05c6|9008'

Ожидаемый признак — `QUSB_BULK` и серийный номер Qualcomm. Пока его нет, QDL не запускать повторно в нескольких экземплярах.

QDL должен получить доступ к USB-устройству. В Codex-команде это означает запуск с разрешением elevated/USB access; при ручном запуске использовать терминал с доступом к USB. Не запускать параллельно два QDL.

Если предыдущая команда была прервана, сначала проверить процессы:

    pgrep -af qdl

Зависший процесс завершать только если нет активной записи:

    kill -TERM <PID>

Перед записью проверить, что существует именно `.043` programmer:

    ls -lh /Users/alex/Documents/Android/Lenovo_Legion_Y700_TB323FU_ZUXOS_2.0.11.043_090326_QFIL/Firmware/prog_firehose_ddr.elf

## QDL: чтение, запись и reset

Команды ниже используют только `.043` programmer. Путь вывода каждый раз менять на новый файл, чтобы не перепутать readback.

Readback `init_boot_a`:

    /private/tmp/qdl-tb323fu/build/qdl --backend=usb --storage=ufs --skip-reset \
      /Users/alex/Documents/Android/Lenovo_Legion_Y700_TB323FU_ZUXOS_2.0.11.043_090326_QFIL/Firmware/prog_firehose_ddr.elf \
      read init_boot_a /Users/alex/Documents/Android/ABK-dev/artifacts/<run>/init_boot_a-readback.img

Проверка источника и readback:

    shasum -a 256 <source.img> <readback.img>
    cmp -s <source.img> <readback.img> && echo BYTE_COMPARE=OK

Запись stock `.043` `init_boot_a` — только для восстановления смешанной или повреждённой цепочки:

    /private/tmp/qdl-tb323fu/build/qdl --backend=usb --storage=ufs --skip-reset \
      /Users/alex/Documents/Android/Lenovo_Legion_Y700_TB323FU_ZUXOS_2.0.11.043_090326_QFIL/Firmware/prog_firehose_ddr.elf \
      write init_boot_a \
      /Users/alex/Documents/Android/Lenovo_Legion_Y700_TB323FU_ZUXOS_2.0.11.043_090326_QFIL/Firmware/init_boot.img

После записи сразу выполнить readback и сравнение с SHA `14f5920ff67de5c53d3436949644d5d6d5d49e74b475d34a9670a197bc85e224`.

Безопасный reset из EDL:

    /private/tmp/qdl-tb323fu/build/qdl --backend=usb reset

`reset` не прошивает разделы. После него ждать загрузку и проверять состояние:

    /Users/alex/Documents/Android/platform-tools/adb devices
    /Users/alex/Documents/Android/platform-tools/fastboot devices

Для перехода из Android в EDL:

    /Users/alex/Documents/Android/platform-tools/adb reboot edl

После команды снова проверять `QUSB_BULK` через `ioreg`, а не полагаться только на звук подключения.

## Минимальный безопасный цикл теста

1. Загрузить штатный Android `.043` и убедиться, что ADB видит устройство.
2. Сохранить SHA исходного артефакта и записать план теста: `GKI` или `LKM`, целевой раздел, слот, `efisp`/OTE.
3. Для GKI менять только `boot_a` или активный `boot_<slot>`; `init_boot_a` не трогать.
4. Если LTBox предлагает OTE/block option, считать его отдельным изменением и сохранить `init_boot` readback отдельно.
5. После flash дождаться результата. При bootloop не делать factory reset до восстановления согласованной пары `.043` `boot`/`init_boot`.
6. При неудаче войти в EDL, восстановить только известный stock-раздел, сделать readback и затем отправить QDL reset. Между readback и записью всегда возвращать Firehose в Sahara/EDL и открывать свежую сессию; не использовать оставшийся Firehose от read-фазы.
7. Новый kernel-тест начинать только после подтверждения, что stock Android снова загружается.

## Ссылки

- [ABK](https://github.com/zaas-design/ABK)
- [Последний известный full GKI build](https://github.com/zaas-design/ABK/actions/runs/37022452071)
- [LTBox](https://github.com/miner7222/LTBox)
- [GBL Root Baldur](https://github.com/miner7222/gbl_root_baldur)
- [DroidSpaces](https://github.com/ravindu644/Droidspaces-OSS)
- [ReSukiSU](https://github.com/ReSukiSU/ReSukiSU)
- [SukiSU Ultra](https://github.com/SukiSU-Ultra/SukiSU-Ultra)
- [SukiSU patch](https://github.com/ShirkNeko/SukiSU_patch)
- [AnyKernel3](https://github.com/osm0sis/AnyKernel3)
- [Пример DroidSpaces для TB322FC/Gen4](https://github.com/ll1zt/tb322fc-droidspaces-kernel/blob/main/README_EN.md)

Пример для Gen4 не считать готовым решением для TB323FU Gen5: он используется только как источник идей по интеграции DroidSpaces и kABI.

## Canoe chainload-only `.043` (2026-10-04)

Подготовлен отдельный офлайн-вариант Canoe без fake-lock. Из точного PE ABL `.043` патчер меняет только UTF-16 `efisp` → `nulls`, чтобы chainload-копия ABL не запускала BDS повторно. Патчи состояния `unlocked/locked`, boot-state и KeyMaster не применяются.

Артефакт: `artifacts/tb323fu-043-canoe-chainload-only-20261004/`.

- оригинальный EFI: SHA-256 `586d6700ee975faac809755b7fe42d6bd053d5564b5e862fac0dc506aa8d750f`;
- chainload-only EFI: SHA-256 `b9f1572962aca864255b3e1a95c0aba143f08f750372df312cb56e38f6da6b6d`;
- изменены только пять младших байтов строки `efisp → nulls`;
- `BDS.efi` взят из официального Canoe toolkit 6.2.192;
- в `Android Tools` добавлен ранее проверенный `RebootTools-EDL.efi`, SHA-256 `59b6b9bdf3ddd097bb21eb68e59fdd7fbfd35e9efeb13f884d202deea5452faa`.

План первого аппаратного теста: свежий EDL-backup `efisp` и `persist`, затем запись только BDS/boot-root, без изменения `abl_a`, `boot_a`, `init_boot_a`, `vbmeta_a`, `dtbo_a` и ядра. Форматирование `Data` в этот вариант не входит. Сначала проверяются меню BDS и пункт `Android Tools → Reboot to EDL`, затем загрузка стокового Android.

### Аппаратный результат

Тест выполнен 4 октября 2026 года. Свежий baseline через Sahara/EDL прошёл. В `persist` добавлены только шесть файлов boot-root; raw `efisp` получил только `BDS.efi`. Readback подтвердил совпадение `persist` и `efisp` с кандидатами; `abl_a`, `boot_a`, `init_boot_a` и `vbmeta_a` после записи совпали с prewrite-read.

После reset планшет штатно загрузил Android:

- `ro.boot.slot_suffix=_a`;
- `sys.boot_completed=1`;
- build `TB323FU_CN_OPEN_USER_Q00020.0_A16_ZUXOS_2.0.11.043_ST_260309`;
- `ro.boot.flash.locked=0`;
- `ro.boot.verifiedbootstate=orange`.

Форматирование `Data` не выполнялось. Post-boot snapshot: `artifacts/tb323fu-043-canoe-chainload-only-20261004/sessions/android-after-01/`. Пункт `Android Tools → Reboot to EDL` включён в boot-root; отдельное нажатие пункта пока не выполнялось, поэтому EDL EFI подтверждён прежним standalone-тестом, а не новым выбором из BDS.

## GKI boot через Canoe chainload-only: запись и откат (2026-10-04)

После успешной загрузки Android через chainload-only Canoe проверен ранее не
запускавшийся образ:

- `artifacts/ltbox-gki-test-20261001-latest/TB323FU-ltbox-gki-boot.img`;
- SHA-256: `93c409e3c033984591cd8411ad7e4e0c68e2ed732a8f6ab7377810511d4bea58`;
- записан только активный `boot_a` в свежей Sahara-сессии;
- readback совпал с кандидатом побайтно;
- после reset устройство ушло в bootloop, Android не появился;
- `boot_a` восстановлен из свежего prewrite-readback, SHA-256
  `f83604375fe2398c09f489fb2b2a8e566a879fb025f0bce59d3dda7c2e9495dd`;
- readback отката совпал побайтно, после reset Android снова загрузился
  (`slot=_a`, `sys.boot_completed=1`).

Причина, установленная локальной проверкой: `avbtool verify_image` у GKI-
образа подтверждает подпись встроенной vbmeta-структуры, но отвергает hash
descriptor — digest в нём не соответствует изменённому содержимому `boot`.
Стоковый `boot` проходит полную проверку. Следовательно, этот тест не
отделяет несовместимость kernel от ошибки AVB-пересборки: сначала нужен
корректный AVB-образ с обновлённым digest и допустимой для устройства
подписью/режимом проверки. Canoe chainload-only меняет только маршрут
`efisp`; он не отключает AVB для `boot` и не делает произвольный kernel
загрузочным.

Сессия, readback и откат сохранены в:
`artifacts/tb323fu-043-canoe-chainload-only-20261004/sessions/edl-gki-boot-01/`.

## Контрольный non-original boot со стоковым kernel (2026-10-04)

Для разделения проблем AVB и kernel подготовлен контрольный образ:
`artifacts/tb323fu-043-stock-null-repack-20261004/stock-kernel-padding-control/boot.img`.
Он отличается от stock `boot.img` одним байтом в неиспользуемом padding после
vbmeta; kernel, ramdisk, DTB и AVB-проверяемая область не изменены.

- stock boot SHA-256: `f83604375fe2398c09f489fb2b2a8e566a879fb025f0bce59d3dda7c2e9495dd`;
- control boot SHA-256: `5fb90432ff8f4a5f1ff8f1fffd6734915a73a468cf61f3aec431e601282a0a52`;
- полный `avbtool verify_image`: успешно;
- запись выполнена только в активный `boot_a`;
- readback совпал с контрольным образом;
- после reset Android загрузился (`slot=_a`, `sys.boot_completed=1`).

Вывод: Canoe chainload-only действительно запускает побайтно неоригинальный
`boot.img` с тем же стоковым kernel. Это контроль записи и загрузочного пути,
но не тест изменённого kernel.

## K1: ReSukiSU-only kernel на точном AOSP GKI (2026-10-04)

Проверен runner `37226152918`. Это был минимальный K1, а не сборка с
Droidspaces: источник — AOSP `kernel/common`, commit
`1750f757fabea014ecc59d327c0c9d3c15ab1e6d`, `6.12.30`,
`gki_defconfig`, встроенный ReSukiSU; Droidspaces, SUSFS, networking,
виртуализация и остальные дополнительные опции были выключены.

Образ:
`artifacts/tb323fu-043-k1-run-37226152918/TB323FU-K1-gbl-preserve-boot.img`,
SHA-256 `2956390a8f0d9887bee9a4bf4480e03bfeb078491cba5707ec0b77405d1a9a9a`.
Немедленный readback `boot_a` совпал с образом. Kernel запустился и был виден
через ADB, но Android завис на заставке ZUXOS: `sys.boot_completed` не появился,
`system_server` перезапускался, а watchdog зафиксировал зависание.

В логах повторяются `Audioserver died`, невозможность запустить
`vendor.qti.hardware.pal.IPAL/default`, переход `hwservicemanager` к fake
`HwNoService`, а также ошибки `wificond`/`NL80211`. Это указывает на вероятную
несовместимость kernel/vendor ABI или downstream-интерфейсов, но не доказывает
конкретный неисправный символ. Полный post-boot snapshot:
`artifacts/tb323fu-043-k1-gbl-test-20261004/sessions/android-after-k1-01/`.

Нормализованное сравнение штатного `.043` конфига с точным AOSP
`gki_defconfig` K1 дало 0 различий. Поэтому проблему нельзя объяснить простым
расхождением базовых Kconfig-опций; тот же K1-образ повторно не использовать.

Следующий этап — ABI/source compatibility gate: снять со штатной системы
vendor/system_dlkm-модули, `modules.*`, `Module.symvers` и vermagic, найти
точную vendor-базу Lenovo либо зафиксировать извлечённый ABI-контракт, затем
собрать отдельный K0/K1R без Droidspaces и проверить CRC до прошивки. План и
перечень артефактов находятся в
`docs/tb323fu-043-k1-vendor-compat-plan.md`.

Безопасный capture со штатного Android уже выполнен: в
`artifacts/tb323fu-043-k1-gbl-test-20261004/sessions/stock-abi-capture-01/proc-modules.txt`
сохранены 504 строки `/proc/modules`, SHA-256
`9f4c5fbd2de82b31f79c31c71c34f4a956749aa72be481298767bb60c38f1b25`.
Сами `.ko` и `modules.*` production ADB-shell не отдаёт, поэтому для полного
CRC-сравнения их нужно извлекать из stock-разделов, а не угадывать по Kconfig.
Из локальной `.043` прошивки уже извлечены все нужные классы:

- `vendor_dlkm`: 305 модулей, штатный vermagic
  `6.12.30-android16-5-maybe-dirty-4k`;
- `system_dlkm`: 103 модуля, все с appended signature и vermagic
  `6.12.30-android16-5-g1750f757fabe-ab13938768-4k`;
- `vendor_boot`: 324 модуля из vendor ramdisk, vermagic
  `6.12.30-android16-5-maybe-dirty-4k`, без appended signature.

Сохранены также metadata `modules.dep`, `modules.alias`, `modules.load`,
`modules.softdep`, `modules.blocklist` и `first_stage_ramdisk/fstab.qcom`.
Отсутствие подписи у vendor-модулей само по себе не является ошибкой. Локальная
ABI-проверка stock `.043` завершена: все 504 модуля из штатного `/proc/modules`
найдены среди извлечённых наборов; проверено 41 540 записей CRC, 36 577
совпали со штатным `vmlinux`, ещё 4 962 — с экспортами модулей, несовпадений
нет. Остался один нерешённый импорт `goodix_ts → qts_client_register`, но
`goodix_ts` отсутствует в штатном списке загруженных модулей.

В проверенном загрузчике наличие `__versions` означает, что строка vermagic не
является самостоятельным доказательством отказа модуля; главным gate остаются
CRC/расширенные таблицы modversions и фактические dmesg. Поэтому
`kernel_localversion_override` сохраняем для воспроизводимости, но больше не
выдаём mismatch `TB323FU-K1` за установленную причину зависания.

Для следующего runner подготовлен отдельный `kernel_localversion_override`,
чтобы не повторить ошибку K1 с release `6.12.30TB323FU-K1`. Новый runner после
K1 не запускался.
