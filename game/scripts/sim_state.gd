class_name SimState
extends RefCounted

# Fictional, compressed game rules. A healthy crop takes roughly one minute.
const GROW_SECONDS: float = 75.0
const SEED_COST: int = 5
const HARVEST_REVENUE: int = 30
const HARVEST_XP: int = 20
const SAVE_VERSION: int = 1
const STATES: Array[String] = ["empty", "seedling", "growing", "flowering", "ready"]

var level: int = 1
var xp: int = 0
var cash: int = 25
var selected: int = 0
var lamp_on: bool = false
var upgraded_light: bool = false
var fan: bool = false
var total_harvests: int = 0
var pots: Array[Dictionary] = [_new_pot(true), _new_pot(false), _new_pot(false)]


static func _new_pot(owned: bool) -> Dictionary:
	return {"owned": owned, "state": "empty", "growth": 0.0, "moisture": 0.0, "health": 100.0}


static func _result(ok: bool, message: String, event: String = "") -> Dictionary:
	return {"ok": ok, "message": message, "event": event}


func tick(delta: float) -> void:
	if not is_finite(delta) or delta <= 0.0:
		return
	# Small steps keep dry-soil stress consistent when frame rates vary.
	var remaining: float = minf(delta, 3600.0)
	while remaining > 0.0:
		var step: float = minf(remaining, 1.0)
		_tick_step(step)
		remaining -= step


func _tick_step(delta: float) -> void:
	for index: int in range(pots.size()):
		var pot: Dictionary = pots[index]
		if not bool(pot["owned"]) or String(pot["state"]) == "empty":
			continue
		var moisture: float = float(pot["moisture"])
		var health: float = float(pot["health"])
		var growth: float = float(pot["growth"])
		var drain: float = 0.6 if not fan else 0.48
		moisture = maxf(0.0, moisture - drain * delta)
		if moisture < 12.0:
			health = maxf(10.0, health - 0.9 * delta)
		elif moisture >= 25.0:
			health = minf(100.0, health + (0.35 if not fan else 0.6) * delta)
		if lamp_on and growth < 1.0:
			var moisture_factor: float = 1.0 if moisture >= 12.0 else 0.25
			var health_factor: float = 0.5 + health / 200.0
			var light_factor: float = 1.4 if upgraded_light else 1.0
			growth = minf(1.0, growth + delta / GROW_SECONDS * moisture_factor * health_factor * light_factor)
		pot["growth"] = growth
		pot["moisture"] = moisture
		pot["health"] = health
		pot["state"] = _stage(growth)


static func _stage(growth: float) -> String:
	if growth >= 1.0:
		return "ready"
	if growth >= 0.72:
		return "flowering"
	if growth >= 0.25:
		return "growing"
	return "seedling"


func _pot_problem(index: int) -> String:
	if index < 0 or index >= pots.size():
		return "That pot does not exist."
	if not bool(pots[index]["owned"]):
		return "Unlock this pot in the upgrade shop."
	return ""


func plant(index: int) -> Dictionary:
	var problem: String = _pot_problem(index)
	if not problem.is_empty():
		return _result(false, problem)
	if String(pots[index]["state"]) != "empty":
		return _result(false, "This pot already has a plant.")
	if cash < SEED_COST:
		return _result(false, "A seed costs 5 credits. Harvest a crop to earn more.")
	cash -= SEED_COST
	pots[index] = {"owned": true, "state": "seedling", "growth": 0.0, "moisture": 35.0, "health": 100.0}
	selected = index
	return _result(true, "Seed planted! Water it and switch on the lamp.", "planted")


func water(index: int) -> Dictionary:
	var problem: String = _pot_problem(index)
	if not problem.is_empty():
		return _result(false, problem)
	if String(pots[index]["state"]) == "empty":
		return _result(false, "Plant a seed before watering.")
	pots[index]["moisture"] = 80.0
	pots[index]["health"] = minf(100.0, float(pots[index]["health"]) + 8.0)
	selected = index
	return _result(true, "Watered. Keep the moisture gauge out of the red.", "watered")


func harvest(index: int) -> Dictionary:
	var problem: String = _pot_problem(index)
	if not problem.is_empty():
		return _result(false, problem)
	if String(pots[index]["state"]) != "ready":
		return _result(false, "This plant is still growing.")
	var previous_level: int = level
	cash += HARVEST_REVENUE
	xp += HARVEST_XP
	total_harvests += 1
	level = _level_for_xp(xp)
	pots[index] = _new_pot(true)
	selected = index
	var message: String = "Harvest sold: +30 credits and +20 XP."
	if level > previous_level:
		message += " Level %d! New upgrades unlocked." % level
	var result: Dictionary = _result(true, message, "harvested")
	result["xp_added"] = HARVEST_XP
	result["revenue"] = HARVEST_REVENUE
	result["levelup"] = level > previous_level
	return result


func toggle_light() -> Dictionary:
	lamp_on = not lamp_on
	if lamp_on:
		return _result(true, "Lamp on. Plants grow while they have water.", "light_on")
	return _result(true, "Lamp off. Growth is paused.", "light_off")


func buy_upgrade(id: String) -> Dictionary:
	var upgrade: String = id
	if id == "second_pot":
		upgrade = "pot2"
	elif id == "better_light" or id == "upgraded_light":
		upgrade = "lamp"
	elif id == "third_pot":
		upgrade = "pot3"
	var price: int = 0
	var required_level: int = 1
	var owned: bool = false
	var label: String = ""
	match upgrade:
		"pot2":
			price = 35
			required_level = 2
			owned = bool(pots[1]["owned"])
			label = "Second pot"
		"lamp":
			price = 45
			required_level = 2
			owned = upgraded_light
			label = "Better grow light"
		"fan":
			price = 30
			required_level = 3
			owned = fan
			label = "Desk fan"
		"pot3":
			price = 55
			required_level = 3
			owned = bool(pots[2]["owned"])
			label = "Third pot"
		_:
			return _result(false, "Unknown upgrade.")
	if owned:
		return _result(false, "You already own this upgrade.")
	if level < required_level:
		return _result(false, "%s unlocks at level %d." % [label, required_level])
	if upgrade == "pot3" and not bool(pots[1]["owned"]):
		return _result(false, "Buy the second pot first.")
	if cash < price:
		return _result(false, "%s costs %d credits." % [label, price])
	cash -= price
	match upgrade:
		"pot2": pots[1] = _new_pot(true)
		"pot3": pots[2] = _new_pot(true)
		"lamp": upgraded_light = true
		"fan": fan = true
	var result: Dictionary = _result(true, "%s installed!" % label, "upgraded")
	result["upgrade"] = upgrade
	return result


func objective() -> String:
	var planted: bool = false
	for pot: Dictionary in pots:
		if bool(pot["owned"]) and String(pot["state"]) == "ready":
			return "Harvest your ready crop for credits and XP."
		if bool(pot["owned"]) and String(pot["state"]) != "empty":
			planted = true
	if not planted:
		return "Plant your first seed (5 credits)." if total_harvests == 0 else "Plant another crop and keep building your bedroom setup."
	if not lamp_on:
		return "Switch on your lamp to start growing."
	for pot: Dictionary in pots:
		if bool(pot["owned"]) and String(pot["state"]) != "empty" and float(pot["moisture"]) < 35.0:
			return "Water the thirsty plant."
	if level == 1:
		return "Grow and harvest your first crop to reach level 2."
	if level == 2 and not bool(pots[1]["owned"]):
		return "Save 35 credits for your second pot."
	if not upgraded_light:
		return "Save 45 credits for a faster grow light."
	if level < 3:
		return "Earn 60 total XP to unlock level 3 equipment."
	if not fan:
		return "Add a fan to help plants recover and conserve water."
	if not bool(pots[2]["owned"]):
		return "Unlock the third pot and complete your bedroom setup."
	return "Your starter room is complete. Keep growing and earning!"


func xp_target() -> int:
	return 20 if level == 1 else 60


static func _level_for_xp(amount: int) -> int:
	if amount >= 60:
		return 3
	return 2 if amount >= 20 else 1


func to_dict() -> Dictionary:
	return {"version": SAVE_VERSION, "level": level, "xp": xp, "cash": cash, "selected": selected,
		"pots": pots.duplicate(true), "lamp_on": lamp_on, "upgraded_light": upgraded_light,
		"fan": fan, "total_harvests": total_harvests}


static func _number(value: Variant) -> bool:
	return (typeof(value) == TYPE_INT or typeof(value) == TYPE_FLOAT) and is_finite(float(value))


static func _whole_number(value: Variant) -> bool:
	return _number(value) and float(value) == floorf(float(value))


func load_dict(data: Dictionary) -> bool:
	# Validate into locals first: failed loads never damage the current game.
	for field: String in ["version", "level", "xp", "cash", "selected", "total_harvests"]:
		if not data.has(field) or not _whole_number(data[field]):
			return false
	if float(data["version"]) != float(SAVE_VERSION) or float(data["xp"]) < 0.0 or float(data["cash"]) < 0.0 or float(data["total_harvests"]) < 0.0:
		return false
	for field: String in ["lamp_on", "upgraded_light", "fan"]:
		if not data.has(field) or typeof(data[field]) != TYPE_BOOL:
			return false
	if not data.has("pots") or typeof(data["pots"]) != TYPE_ARRAY or data["pots"].size() != 3:
		return false
	var loaded_xp: int = int(minf(float(data["xp"]), 1000000000.0))
	var loaded_level: int = _level_for_xp(loaded_xp)
	if float(data["level"]) != float(loaded_level):
		return false
	if (bool(data["upgraded_light"]) and loaded_level < 2) or (bool(data["fan"]) and loaded_level < 3):
		return false
	var loaded_pots: Array[Dictionary] = []
	for index: int in range(3):
		if typeof(data["pots"][index]) != TYPE_DICTIONARY:
			return false
		var raw: Dictionary = data["pots"][index]
		if not raw.has("owned") or typeof(raw["owned"]) != TYPE_BOOL or not raw.has("state") or typeof(raw["state"]) != TYPE_STRING:
			return false
		if not STATES.has(String(raw["state"])):
			return false
		for field: String in ["growth", "moisture", "health"]:
			if not raw.has(field) or not _number(raw[field]):
				return false
		var owned: bool = bool(raw["owned"])
		var state: String = String(raw["state"])
		if (index == 0 and not owned) or (index > 0 and owned and loaded_level < index + 1):
			return false
		if not owned and state != "empty":
			return false
		var growth: float = clampf(float(raw["growth"]), 0.0, 1.0)
		var moisture: float = clampf(float(raw["moisture"]), 0.0, 100.0)
		var health: float = clampf(float(raw["health"]), 10.0, 100.0)
		if state == "empty":
			loaded_pots.append(_new_pot(owned))
		else:
			loaded_pots.append({"owned": owned, "state": _stage(growth), "growth": growth, "moisture": moisture, "health": health})
	if bool(loaded_pots[2]["owned"]) and not bool(loaded_pots[1]["owned"]):
		return false
	var loaded_selected: int = int(clampf(float(data["selected"]), 0.0, 2.0))
	if not bool(loaded_pots[loaded_selected]["owned"]):
		loaded_selected = 0
	xp = loaded_xp
	level = loaded_level
	cash = int(minf(float(data["cash"]), 1000000000.0))
	selected = loaded_selected
	lamp_on = bool(data["lamp_on"])
	upgraded_light = bool(data["upgraded_light"])
	fan = bool(data["fan"])
	total_harvests = int(minf(float(data["total_harvests"]), 1000000000.0))
	pots = loaded_pots
	return true
