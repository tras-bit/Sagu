# SUBSISTENCE — HIGHPOLY TRACKER (хай-поли пасс по всем 159 моделям)

Порядок из ANSWERS_V3 (14а): **монстры → оружие → персонажи → предметы → пропсы**.
Метод (8а): AAA-пайплайн — хай-поли деталь → запекание нормалей/AO (11а: 2K крупные / 1K мелочь) →
игровая сетка + 2–3 LOD (12а). Пайплайн: `tools/blender/hp_pipeline.py`, интеграция в `build_models.sh` (13а).

Статусы: ⬜ очередь · 🔨 в работе · ✅ готово (FBX + нормаль + AO в `Assets/Subsistence/ModelsHP/`)

## Спринт 1 — Монстры (первый, стартовал 2026-09-17)
| Модель | Статус | Заметка |
|---|---|---|
| MN_smiler | ✅ готово | HP 271k → карты 2K + LOD (12 мин) |
| MN_hound | ✅ готово | HP 370k → карты 2K + LOD |
| MN_partygoer | ✅ готово | HP 942k → карты 2K + LOD, самый тяжёлый |
| MN_skinstealer | ✅ готово | HP 274k → карты 2K + LOD |
| MN_whisperer | ✅ готово | HP 48k → карты 2K + LOD |
| MN_drowned | ✅ готово | HP 57k → карты 2K + LOD · уже в коде: Drowned (18а) |
| MN_spark | ✅ готово | HP 61k → карты 2K + LOD · уже в коде: Spark (18а) |
| MN_bacteria | ⬜ очередь | архив, босс отменён (17в) |

## Спринт 1.2 — Оружие (9 стволов, 21а — доводим эти)
| Модель | Статус | Заметка |
|---|---|---|
| EX_explosive_timed | ✅ готово | LP 2.1k · HP 12.3k, фаски 0.4 мм |
| EX_grenade_f1 | ✅ готово | LP 5.4k · HP 32.6k, фаски 0.4 мм (тёмный металл — так и задумано) |
| W_lmg_m249 | ✅ готово | LP 8.8k · HP 94.6k, фаски 1.9 мм; обвесы — спринт 3 (23а) |
| W_rifle_ak | ✅ готово | LP 10.2k · HP 38.7k, фаски 1.9 мм; обвесы — спринт 3 (23а) |
| W_rifle_bolt | ✅ готово | LP 8.0k · HP 30.2k, фаски 2.1 мм; обвесы — спринт 3 (23а) |
| W_rifle_m4 | ✅ готово | LP 13.4k · HP 58.7k, фаски 1.6 мм; обвесы — спринт 3 (23а) |
| W_rocket_launcher | ✅ готово | LP 4.8k · HP 58.0k; ⚠ LOD2 не ужался (топология трубы) — перегенерить |
| W_shotgun_pump | ✅ готово | LP 4.9k · HP 19.9k, фаски 2.0 мм |
| W_smg_mp5 | ✅ готово | LP 7.0k · HP 25.8k, фаски 1.2 мм |

## Спринт 1.3 — Персонажи и предметы
| Модель | Статус | Заметка |
|---|---|---|
| CH_hazmat_suit | ✅ очередь | лёгкий апгрейд деталей (20б) |
| CH_trader_npc | ✅ очередь | лёгкий апгрейд деталей (20б) |
| IT_ammo_556 | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_ammo_shell | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_antidote | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_apple | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_arrow_bundle | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_bandage | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_boots_hide | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_boots_rubber | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_bucket | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_can_beans | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_can_tuna | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_chlorine | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_chocolate | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_cloth_roll | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_diving_mask | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_duct_tape | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_flashlight | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_flippers | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_fuse_hi | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_geiger | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_glow_mushroom | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_hide_vest | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_lamp_portable | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_meat_raw | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_medkit_large | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_oxygen_tank | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_respirator | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_rubber_gloves | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_scrap_pile | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_stone_pile | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_sulfur_lump | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_torch_lantern | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_water_bottle | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_wood_chestplate | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_wood_helmet | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_wood_pile | ✅ готово | карты 1K + фаски/органика + 2 LOD |
| IT_wrench_insulated | ✅ готово | карты 1K + фаски/органика + 2 LOD |

## Спринт 1.4 — Пропсы (103 элемента)

### BD — Стройка (Rust-style база) (18)
| Модель | Статус | Заметка |
|---|---|---|
| BD_door_armored | ✅ готово | карты 1K + фаски + LOD |
| BD_door_metal | ✅ готово | карты 1K + фаски + LOD |
| BD_doorway | ✅ готово | карты 1K + фаски + LOD |
| BD_elevator_car | ✅ готово | HP 33.6k · карты **2K** + фаски + LOD |
| BD_floor | ✅ готово | карты 1K + фаски + LOD |
| BD_floor_tri | ✅ готово | карты 1K + фаски + LOD |
| BD_foundation | ✅ готово | карты 1K + фаски + LOD |
| BD_foundation_tri | ✅ готово | карты 1K + фаски + LOD |
| BD_high_wall | ✅ готово | карты 1K + фаски + LOD |
| BD_pillar | ✅ готово | карты 1K + фаски + LOD |
| BD_railing | ✅ готово | карты 1K + фаски + LOD |
| BD_ramp | ✅ готово | карты 1K + фаски + LOD |
| BD_ramp_corner | ✅ готово | карты 1K + фаски + LOD |
| BD_roof | ✅ готово | карты 1K + фаски + LOD |
| BD_shutters | ✅ готово | карты 1K + фаски + LOD |
| BD_stairs | ✅ готово | карты 1K + фаски + LOD |
| BD_wall | ✅ готово | карты 1K + фаски + LOD |
| BD_window | ✅ готово | карты 1K + фаски + LOD |

### DD — Деплой-объекты (34)
| Модель | Статус | Заметка |
|---|---|---|
| DD_autoturret | ✅ готово | карты 1K + фаски + LOD |
| DD_barricade_concrete | ✅ готово | карты 1K + фаски + LOD |
| DD_barricade_metal | ✅ готово | карты 1K + фаски + LOD |
| DD_bed | ✅ готово | карты 1K + фаски + LOD |
| DD_cupboard | ✅ готово | карты 1K + фаски + LOD |
| DD_door_armored | ✅ готово | карты 1K + фаски + LOD |
| DD_door_metal | ✅ готово | карты 1K + фаски + LOD |
| DD_door_wood | ✅ готово | карты 1K + фаски + LOD |
| DD_furnace | ✅ готово | карты 1K + фаски + LOD |
| DD_furnace_large | ✅ готово | карты 1K + фаски + LOD |
| DD_lock_code | ✅ готово | карты 1K + фаски + LOD |
| DD_lock_key | ✅ готово | карты 1K + фаски + LOD |
| DD_purifier | ✅ готово | карты 1K + фаски + LOD |
| DD_repair_bench | ✅ готово | карты 1K + фаски + LOD |
| DD_research_table | ✅ готово | карты 1K + фаски + LOD |
| DD_samsite | ✅ готово | карты 1K + фаски + LOD |
| DD_sign | ✅ готово | карты 1K + фаски + LOD |
| DD_sleepingbag | ✅ готово | карты 1K + фаски + LOD |
| DD_trap_bear | ✅ готово | карты 1K + фаски + LOD |
| DD_trap_spikes | ✅ готово | карты 1K + фаски + LOD |
| DD_wind_generator | ✅ готово | карты 1K + фаски + LOD |
| DD_workbench | ✅ готово | карты 1K + фаски + LOD |
| DD_workbench1 | ✅ готово | карты 1K + фаски + LOD |
| DD_workbench1_L0 | ✅ готово | карты 1K + фаски + LOD |
| DD_workbench1_L3 | ✅ готово | карты 1K + фаски + LOD |
| DD_workbench1_L37 | ✅ готово | карты 1K + фаски + LOD |
| DD_workbench2 | ✅ готово | карты 1K + фаски + LOD |
| DD_workbench2_L0 | ✅ готово | карты 1K + фаски + LOD |
| DD_workbench2_L3 | ✅ готово | карты 1K + фаски + LOD |
| DD_workbench2_L37 | ✅ готово | карты 1K + фаски + LOD |
| DD_workbench3 | ✅ готово | карты 1K + фаски + LOD |
| DD_workbench3_L0 | ✅ готово | карты 1K + фаски + LOD |
| DD_workbench3_L3 | ✅ готово | карты 1K + фаски + LOD |
| DD_workbench3_L37 | ✅ готово | карты 1K + фаски + LOD |

### LV — Декор уровней (Poolrooms) (27)
| Модель | Статус | Заметка |
|---|---|---|
| LV_breaker_cabinet | ✅ готово | карты 1K + фаски + LOD |
| LV_cable_spool | ✅ готово | карты 1K + фаски + LOD |
| LV_cardboard_stack | ✅ готово | карты 1K + фаски + LOD |
| LV_ceiling_light | ✅ готово | карты 1K + фаски + LOD |
| LV_control_panel | ✅ готово | карты 1K + фаски + LOD |
| LV_coolant_tank | ✅ готово | карты 1K + фаски + LOD |
| LV_corridor_panel | ✅ готово | карты 1K + фаски + LOD |
| LV_deck_chair | ✅ готово | карты 1K + фаски + LOD |
| LV_desk_fan | ✅ готово | карты 1K + фаски + LOD |
| LV_exit_sign | ✅ готово | карты 1K + фаски + LOD |
| LV_filing_cabinet | ✅ готово | карты 1K + фаски + LOD |
| LV_inflatable_ring | ✅ готово | карты 1K + фаски + LOD |
| LV_lifebuoy | ✅ готово | карты 1K + фаски + LOD |
| LV_mop_bucket | ✅ готово | карты 1K + фаски + LOD |
| LV_office_chair | ✅ готово | карты 1K + фаски + LOD |
| LV_pipe_flange | ✅ готово | карты 1K + фаски + LOD |
| LV_pipe_valve | ✅ готово | карты 1K + фаски + LOD |
| LV_pool_ladder | ✅ готово | карты 1K + фаски + LOD |
| LV_pool_pump | ✅ готово | карты 1K + фаски + LOD |
| LV_pool_tile_panel | ✅ готово | карты 1K + фаски + LOD |
| LV_shower_head | ✅ готово | карты 1K + фаски + LOD |
| LV_transformer | ✅ готово | карты 1K + фаски + LOD |
| LV_turbine_housing | ✅ готово | карты 1K + фаски + LOD |
| LV_valve_wheel | ✅ готово | карты 1K + фаски + LOD |
| LV_warning_sign | ✅ готово | карты 1K + фаски + LOD |
| LV_water_cooler | ✅ готово | карты 1K + фаски + LOD |
| LV_wet_floor_sign | ✅ готово | карты 1K + фаски + LOD |

### PR — Пропсы/транспорт/лут (24)
| Модель | Статус | Заметка |
|---|---|---|
| PR_airdrop_crate | ✅ готово | карты 1K + фаски + LOD |
| PR_barrel | ✅ готово | карты 1K + фаски + LOD |
| PR_barrel_radioactive | ✅ готово | карты 1K + фаски + LOD |
| PR_carpet_tile_L0 | ✅ готово | карты 1K + фаски + LOD |
| PR_crate_wood | ✅ готово | карты 1K + фаски + LOD |
| PR_electrical_panel | ✅ готово | карты 1K + фаски + LOD |
| PR_filing_cabinet | ✅ готово | карты 1K + фаски + LOD |
| PR_lamp_panel_L0 | ✅ готово | карты 1K + фаски + LOD |
| PR_locker | ✅ готово | карты 1K + фаски + LOD |
| PR_loot_bag | ✅ готово | карты 1K + фаски + LOD |
| PR_loot_cart | ✅ готово | HP 34.5k · карты **2K** + фаски + LOD |
| PR_medical_cabinet | ✅ готово | карты 1K + фаски + LOD |
| PR_minecart | ✅ готово | HP 43.5k · карты **2K** + фаски + LOD |
| PR_pipe_kit | ✅ готово | карты 1K + фаски + LOD |
| PR_pool_tile_block | ✅ готово | карты 1K + фаски + LOD |
| PR_reactor | ✅ готово | HP  · карты **2K** + фаски + LOD |
| PR_safe_box | ✅ готово | карты 1K + фаски + LOD |
| PR_scooter | ✅ готово | HP 40.8k · карты **2K** + фаски + LOD |
| PR_supply_crate | ✅ готово | карты 1K + фаски + LOD |
| PR_toolbox | ✅ готово | карты 1K + фаски + LOD |
| PR_transformer | ✅ готово | карты 1K + фаски + LOD |
| PR_turbine | ✅ готово | карты 1K + фаски + LOD |
| PR_vending_machine | ✅ готово | HP 46.5k · карты **2K** + фаски + LOD |
| PR_wall_panel_L0 | ✅ готово | карты 1K + фаски + LOD |

**Итого: 159 моделей. Готово: 159/159 — хай-поли пасс 40а ЗАВЕРШЁН (перегенерирован после двух сбоев снапшота).** 🎉
(монстры 8 · оружие 9 · персонажи 2 · предметы 37 · стройка 18 · деплои 34 · декор уровней 27 · пропсы 24)
Листы: `_hp_sheet_monsters.png`, `_hp_sheet_weapons.png`, `_hp_sheet_characters.png`, `_hp_sheet_items.png`, `_hp_sheet_build.png`, `_hp_sheet_deployables.png`, `_hp_sheet_props.png`.
Карты 2K у крупных (11а): BD_elevator_car, PR_reactor, PR_vending_machine, PR_scooter, PR_minecart, PR_loot_cart; остальным пропсам 1K.

### Хвосты 40а / смежные задачи — все закрыты (18.09, сборка 1.1.0)
- W_rocket_launcher: LOD1/LOD2 ПОЧИНЕНЫ — меш состоял из разорванных оболочек (1245 дублей вершин);
  make_lod теперь сам сваривает и пережимает, LOD2 = 475 трис (LOD1 1047).
- 24а ✅ иконки 256px: 66 из HP-рендеров + 114 апскейл (см. docs/previews/_icons256_3d.png).
- 20б ✅ хазмат/торговец: органика 0.030 + слой строчек, ребейк 2K.
- 25а ✅ скины: 10 рендеров 2K + 4 карточки, магазин с превью и ↑↓/Enter (Skins.cs).
- 37в/39а ✅ звук: 11 .wav (лупы L0/L3/L37 + выстрелы 9 стволов + взрыв), ProcAudio сэмплы-приоритет.
