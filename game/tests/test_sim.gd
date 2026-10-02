extends SceneTree

const Model = preload("res://scripts/sim_state.gd")
var checks: int = 0
var failures: Array[String] = []


func _initialize() -> void:
	_test_starter_and_first_harvest()
	_test_upgrades_and_progression()
	_test_stress_and_faster_light()
	_test_save_validation()
	_test_persisted_json()
	if failures.is_empty():
		print("SIM TESTS PASSED: %d checks" % checks)
		quit(0)
	else:
		for failure: String in failures:
			push_error(failure)
		print("SIM TESTS FAILED: %d of %d checks" % [failures.size(), checks])
		quit(1)


func _check(condition: bool, label: String) -> void:
	checks += 1
	if not condition:
		failures.append(label)


func _complete_crop(sim: Model, index: int = 0) -> Dictionary:
	sim.plant(index)
	sim.water(index)
	if not sim.lamp_on:
		sim.toggle_light()
	sim.tick(80.0)
	return sim.harvest(index)


func _test_starter_and_first_harvest() -> void:
	var sim: Model = Model.new()
	_check(sim.level == 1 and sim.xp == 0 and sim.cash == 25, "Starts at level 1, 0 XP, and 25 credits")
	_check(sim.pots.size() == 3 and sim.pots[0]["owned"] and not sim.pots[1]["owned"] and not sim.pots[2]["owned"], "Exactly one starter pot owned")
	_check(not sim.lamp_on and not sim.upgraded_light and not sim.fan, "Starter equipment is basic and switched off")
	_check(sim.xp_target() == 20, "First XP threshold is 20")
	_check(not sim.water(0)["ok"] and not sim.harvest(0)["ok"], "Empty pots cannot be watered or harvested")
	_check(not sim.plant(-1)["ok"] and not sim.plant(3)["ok"] and not sim.plant(1)["ok"], "Bad and locked pot indices are safely denied")
	_check(sim.plant(0)["ok"] and sim.cash == 20 and sim.pots[0]["state"] == "seedling", "Planting spends exactly five credits")
	_check(not sim.plant(0)["ok"] and sim.cash == 20, "Occupied pot denies duplicate planting without spending")
	sim.tick(5.0)
	_check(is_zero_approx(float(sim.pots[0]["growth"])), "Lamp off pauses crop growth")
	_check(not sim.harvest(0)["ok"], "Immature crop cannot be harvested")
	_check(sim.water(0)["ok"] and is_equal_approx(float(sim.pots[0]["moisture"]), 80.0), "Watering restores the moisture gauge")
	for count: int in range(20):
		sim.water(0)
	_check(sim.xp == 0 and sim.cash == 20, "Repeated watering cannot farm XP or money")
	_check(sim.toggle_light()["ok"] and sim.lamp_on, "Lamp can be switched on")
	sim.tick(20.0)
	_check(sim.pots[0]["state"] == "growing" and float(sim.pots[0]["growth"]) > 0.25, "Growth progresses to the growing stage")
	sim.tick(40.0)
	_check(sim.pots[0]["state"] == "flowering", "Growth progresses to the flowering stage")
	sim.tick(20.0)
	_check(sim.pots[0]["state"] == "ready" and is_equal_approx(float(sim.pots[0]["growth"]), 1.0), "A cared-for crop becomes ready")
	var reward: Dictionary = sim.harvest(0)
	_check(reward["ok"] and reward["revenue"] == 30 and reward["xp_added"] == 20 and reward["levelup"], "First harvest reports exact rewards and level-up")
	_check(sim.cash == 50 and sim.xp == 20 and sim.level == 2 and sim.total_harvests == 1, "Harvest applies rewards exactly once")
	_check(sim.pots[0]["state"] == "empty" and sim.xp_target() == 60, "Harvest frees the pot and exposes the next XP target")
	_check(not sim.harvest(0)["ok"] and sim.cash == 50 and sim.xp == 20, "Double harvest cannot duplicate rewards")
	var poor: Model = Model.new()
	poor.cash = 4
	_check(not poor.plant(0)["ok"] and poor.cash == 4 and poor.pots[0]["state"] == "empty", "Insufficient seed money does not alter the pot")


func _test_upgrades_and_progression() -> void:
	var sim: Model = Model.new()
	for id: String in ["pot2", "lamp", "fan", "pot3"]:
		_check(not sim.buy_upgrade(id)["ok"] and sim.cash == 25, "Level 1 gate denies " + id)
	_check(not sim.buy_upgrade("invalid")["ok"], "Unknown upgrade is safely denied")
	_complete_crop(sim)
	_check(sim.buy_upgrade("pot2")["ok"] and sim.pots[1]["owned"] and sim.cash == 15, "Level 2 second pot purchase succeeds")
	_check(not sim.buy_upgrade("pot2")["ok"] and sim.cash == 15, "Duplicate upgrade cannot spend money")
	_check(not sim.buy_upgrade("lamp")["ok"] and not sim.upgraded_light and sim.cash == 15, "Unaffordable lamp does not charge or install")
	_check(not sim.buy_upgrade("fan")["ok"], "Level 2 cannot buy the level 3 fan")
	_complete_crop(sim)
	_check(sim.level == 2 and sim.xp == 40, "Second harvest remains level 2")
	var third: Dictionary = _complete_crop(sim)
	_check(sim.level == 3 and sim.xp == 60 and third["levelup"], "Third harvest unlocks level 3")
	_check(sim.buy_upgrade("lamp")["ok"] and sim.upgraded_light and sim.cash == 20, "Better lamp spends its exact price")
	_complete_crop(sim)
	_check(sim.buy_upgrade("fan")["ok"] and sim.fan and sim.cash == 15, "Fan purchase works after earning its price")
	_complete_crop(sim)
	_complete_crop(sim)
	_check(sim.buy_upgrade("pot3")["ok"] and sim.pots[2]["owned"] and sim.cash == 10, "Third pot purchase completes the starter room")
	_check(sim.level == 3, "Prototype caps progression at level 3")
	var prerequisite: Model = Model.new()
	prerequisite.level = 3
	prerequisite.xp = 60
	prerequisite.cash = 100
	_check(not prerequisite.buy_upgrade("pot3")["ok"] and prerequisite.cash == 100, "Third pot requires the second pot first")


func _test_stress_and_faster_light() -> void:
	var dry: Model = Model.new()
	dry.plant(0)
	dry.toggle_light()
	dry.tick(65.0)
	_check(float(dry.pots[0]["moisture"]) == 0.0 and float(dry.pots[0]["health"]) < 100.0 and dry.pots[0]["state"] != "ready", "Dry-soil stress slows growth and reduces health")
	dry.water(0)
	var watered_health: float = float(dry.pots[0]["health"])
	dry.tick(10.0)
	_check(float(dry.pots[0]["health"]) > watered_health, "A neglected plant recovers after watering")
	dry.tick(3600.0)
	_check(float(dry.pots[0]["health"]) >= 10.0 and float(dry.pots[0]["growth"]) <= 1.0, "Long ticks preserve safe bounds and avoid permanent failure")
	var normal: Model = Model.new()
	var faster: Model = Model.new()
	normal.plant(0)
	normal.water(0)
	normal.toggle_light()
	faster.plant(0)
	faster.water(0)
	faster.toggle_light()
	faster.upgraded_light = true
	normal.tick(54.0)
	faster.tick(54.0)
	_check(faster.pots[0]["state"] == "ready" and normal.pots[0]["state"] != "ready", "Upgraded light visibly shortens the crop cycle")
	var with_fan: Model = Model.new()
	with_fan.plant(0)
	with_fan.water(0)
	with_fan.fan = true
	with_fan.tick(20.0)
	_check(float(with_fan.pots[0]["moisture"]) > 68.0, "Fan upgrade conserves moisture")
	var invalid_tick: Dictionary = normal.to_dict()
	normal.tick(-1.0)
	normal.tick(INF)
	_check(normal.to_dict() == invalid_tick, "Negative and non-finite ticks are ignored")
	var frame_a: Model = Model.new()
	var frame_b: Model = Model.new()
	for sim: Model in [frame_a, frame_b]:
		sim.plant(0)
		sim.water(0)
		sim.toggle_light()
	frame_a.tick(30.0)
	for count: int in range(300):
		frame_b.tick(0.1)
	_check(is_equal_approx(float(frame_a.pots[0]["growth"]), float(frame_b.pots[0]["growth"])), "Healthy growth agrees across frame sizes")


func _test_save_validation() -> void:
	var sim: Model = Model.new()
	_complete_crop(sim)
	sim.buy_upgrade("pot2")
	sim.plant(1)
	sim.water(1)
	sim.tick(12.5)
	var saved: Dictionary = sim.to_dict()
	var loaded: Model = Model.new()
	_check(loaded.load_dict(saved) and loaded.to_dict() == saved, "Valid saves round trip exactly")
	var json_data: Variant = JSON.parse_string(JSON.stringify(saved))
	_check(typeof(json_data) == TYPE_DICTIONARY and loaded.load_dict(json_data), "JSON numeric representation loads correctly")
	saved["pots"][1]["growth"] = 0.99
	_check(not is_equal_approx(float(sim.pots[1]["growth"]), 0.99), "Save dictionaries do not share live plant references")
	var baseline: Dictionary = loaded.to_dict()
	var bad_cases: Array[Dictionary] = [{}]
	var malformed: Dictionary = baseline.duplicate(true)
	malformed["version"] = 999
	bad_cases.append(malformed)
	malformed = baseline.duplicate(true)
	malformed["pots"] = []
	bad_cases.append(malformed)
	malformed = baseline.duplicate(true)
	malformed["cash"] = "lots"
	bad_cases.append(malformed)
	malformed = baseline.duplicate(true)
	malformed["cash"] = -1
	bad_cases.append(malformed)
	malformed = baseline.duplicate(true)
	malformed["cash"] = INF
	bad_cases.append(malformed)
	malformed = baseline.duplicate(true)
	malformed["lamp_on"] = 1
	bad_cases.append(malformed)
	malformed = baseline.duplicate(true)
	malformed["pots"][0]["state"] = "banana"
	bad_cases.append(malformed)
	malformed = baseline.duplicate(true)
	malformed["pots"][1]["growth"] = INF
	bad_cases.append(malformed)
	malformed = baseline.duplicate(true)
	malformed["pots"][1]["health"] = false
	bad_cases.append(malformed)
	malformed = baseline.duplicate(true)
	malformed["level"] = 3
	bad_cases.append(malformed)
	malformed = baseline.duplicate(true)
	malformed["fan"] = true
	bad_cases.append(malformed)
	malformed = baseline.duplicate(true)
	malformed["pots"][2]["owned"] = true
	bad_cases.append(malformed)
	for index: int in range(bad_cases.size()):
		_check(not loaded.load_dict(bad_cases[index]) and loaded.to_dict() == baseline, "Malformed save %d is rejected atomically" % index)
	var clamped: Dictionary = baseline.duplicate(true)
	clamped["selected"] = 999
	clamped["pots"][1]["growth"] = 5.0
	clamped["pots"][1]["moisture"] = -20.0
	clamped["pots"][1]["health"] = 500.0
	_check(loaded.load_dict(clamped), "Finite plant ranges are safely normalized")
	_check(loaded.selected == 0 and loaded.pots[1]["state"] == "ready" and loaded.pots[1]["growth"] == 1.0 and loaded.pots[1]["moisture"] == 0.0 and loaded.pots[1]["health"] == 100.0, "Loaded plant gauges clamp and selected locked pot falls back")


func _test_persisted_json() -> void:
	var sim: Model = Model.new()
	_complete_crop(sim)
	sim.buy_upgrade("pot2")
	sim.plant(1)
	sim.water(1)
	sim.tick(15.0)
	var path: String = "res://tests/.sim_roundtrip.json"
	var file: FileAccess = FileAccess.open(path, FileAccess.WRITE)
	_check(file != null, "Disk persistence opens an isolated test save")
	if not file:
		return
	file.store_string(JSON.stringify(sim.to_dict()))
	var write_error: Error = file.get_error()
	file.close()
	_check(write_error == OK, "Disk persistence writes JSON successfully")
	file = FileAccess.open(path, FileAccess.READ)
	_check(file != null, "Disk persistence reopens saved JSON")
	if not file:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	file.close()
	var restored: Model = Model.new()
	_check(parsed is Dictionary and restored.load_dict(parsed), "Disk JSON can restore a live model")
	_check(_same_save(restored.to_dict(), sim.to_dict()) and restored.selected == 1, "Persisted owned-pot selection and gameplay state round trip")
	var locked_selection: Dictionary = sim.to_dict()
	locked_selection["selected"] = 2
	_check(restored.load_dict(locked_selection) and restored.selected == 0, "Persisted locked-pot selection normalizes to the starter pot")
	_check(DirAccess.remove_absolute(path) == OK, "Isolated persistence test removes its temporary file")


func _same_save(first: Dictionary, second: Dictionary) -> bool:
	var a: Dictionary = first.duplicate(true)
	var b: Dictionary = second.duplicate(true)
	for index: int in range(3):
		for field: String in ["growth", "moisture", "health"]:
			if not is_equal_approx(float(a["pots"][index][field]), float(b["pots"][index][field])):
				return false
			a["pots"][index][field] = 0.0
			b["pots"][index][field] = 0.0
	return a == b
