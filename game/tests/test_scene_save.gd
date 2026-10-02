extends SceneTree

const MAIN_SCENE = preload("res://main.tscn")
const STATE = preload("res://scripts/sim_state.gd")

var checks := 0
var failures: Array[String] = []
var created_files: Array[String] = []
var test_directory: String
var save_file: String


func _initialize() -> void:
	call_deferred("_run")


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error("SCENE_SAVE_TEST: " + message)


func _read_save() -> Dictionary:
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(save_file))
	_check(data is Dictionary, "Saved file is valid JSON object")
	return data if data is Dictionary else {}


func _same(left: Variant, right: Variant) -> bool:
	# JSON has untyped arrays and float numbers; compare the persisted values.
	if typeof(left) in [TYPE_INT, TYPE_FLOAT] and typeof(right) in [TYPE_INT, TYPE_FLOAT]:
		return float(left) == float(right)
	if left is Dictionary and right is Dictionary:
		if left.size() != right.size():
			return false
		for key: Variant in left:
			if not right.has(key) or not _same(left[key], right[key]):
				return false
		return true
	if left is Array and right is Array:
		if left.size() != right.size():
			return false
		for index: int in range(left.size()):
			if not _same(left[index], right[index]):
				return false
		return true
	return left == right


func _run() -> void:
	root.size = Vector2i(1280, 800)
	test_directory = ProjectSettings.globalize_path("res://tests/")
	var nonce := str(Time.get_ticks_usec()) + "-" + str(randi())
	save_file = ProjectSettings.globalize_path("res://tests/scene-save-" + nonce + ".json")
	_check(not FileAccess.file_exists(save_file), "Unique temporary save does not overwrite an existing file")
	if FileAccess.file_exists(save_file):
		_finish()
		return
	created_files.append(save_file)
	created_files.append(save_file + ".tmp")
	var game: Variant = MAIN_SCENE.instantiate()
	game.testing = true
	root.add_child(game)
	await process_frame
	await process_frame
	game.set_process(false)
	game.set_physics_process(false)
	game.testing = false
	game.save_path = save_file
	_check(game.state.level == 1 and game.state.xp == 0 and game.state.cash == 25, "Actual scene starts at level 1 with zero XP and 25 credits")
	_check(game.selected == 0 and game.state.selected == 0, "Scene and domain start with pot 1 selected")
	_check(not game.grow_rack.visible and not game.fan_art.visible, "Starter scene hides advanced equipment")
	game._save_game()
	_check(FileAccess.file_exists(save_file), "Root save method writes a real file")
	_check(not FileAccess.file_exists(save_file + ".tmp"), "Committed save leaves no temporary file")
	var initial: Dictionary = _read_save()
	_check(_same(initial, game.state.to_dict()), "Initial save preserves every state field")
	for field: String in ["version", "level", "xp", "cash", "selected", "pots", "lamp_on", "upgraded_light", "fan", "total_harvests"]:
		_check(initial.has(field), "Saved object contains " + field)

	# Emit actual HUD signals: this tests the callbacks connected by main._ready.
	# Persistence fixtures stand at the pot; route and animation timing have their own tests.
	game.player.position = game.APPROACH_POSITIONS[0]
	game.hud._buttons["plant"].pressed.emit()
	_check(game.state.cash == 20 and game.state.pots[0]["state"] == "seedling", "Plant HUD button reaches the actual game action")
	game.hud._buttons["light"].pressed.emit()
	game.care_timer = 0.0
	game.hud._buttons["water"].pressed.emit()
	_check(game.state.lamp_on and game.state.pots[0]["moisture"] == 80.0, "Light and water HUD buttons update the actual game")
	var cared: Dictionary = _read_save()
	_check(cared["cash"] == 20 and cared["lamp_on"] and cared["pots"][0]["moisture"] == 80.0, "Action saves replace an existing file with current progress")
	_check(_same(cared, game.state.to_dict()), "Overwritten file exactly matches cared-for state")
	game.state = STATE.new()
	game.state.cash = 999
	game.selected = 2
	game._load_game()
	_check(_same(game.state.to_dict(), cared), "Root load restores actual saved state after mutation")
	_check(game.selected == 0 and game.state.selected == 0 and game.state.cash == 20, "Root load restores both selection fields and cash")

	# A purchased pot and an owned selection must survive the file round trip.
	game.state.xp = 20
	game.state.level = 2
	game.state.cash = 100
	var purchase: Dictionary = game.state.buy_upgrade("pot2")
	_check(purchase["ok"], "Fixture purchases the second pot legally at level 2")
	game.hud._pot_buttons[1].pressed.emit()
	_check(game.selected == 1 and game.state.selected == 1, "Second selector button updates both selection fields")
	_check(game.pot_nodes[1].visible and game.hud._pot_title.text == "POT 2", "Selector signal refreshes both world and HUD")
	game._save_game()
	var expanded: Dictionary = _read_save()
	_check(expanded["selected"] == 1 and expanded["pots"][1]["owned"], "Owned selection and upgrade are written")
	game.state = STATE.new()
	game.selected = 0
	game._load_game()
	_check(game.selected == 1 and game.state.selected == 1, "Owned pot 2 remains selected on load")
	_check(_same(game.state.to_dict(), expanded) and game.state.cash == 65, "Expanded setup restores exactly")
	game.hud._pot_buttons[2].pressed.emit()
	_check(game.selected == 2 and game.hud._stage_label.text.begins_with("LOCKED"), "Locked selector can be inspected without buying it")
	game._save_game()
	_check(_read_save()["selected"] == 2, "Locked inspection selection reaches the file")
	game.state = STATE.new()
	game.selected = 2
	game._load_game()
	_check(game.selected == 0 and game.state.selected == 0, "Load normalizes a locked selection back to the first owned pot")
	_check(game.state.pots[1]["owned"] and not game.state.pots[2]["owned"], "Selection normalization preserves purchases")

	# Pause must stop actions and simulation, while its HUD button still resumes.
	game.hud._pot_buttons[0].pressed.emit()
	game.paused = true
	game.hud.refresh(game.state, game.selected, game.paused)
	var before_pause: Dictionary = game.state.to_dict()
	game.hud._buttons["plant"].pressed.emit()
	game.hud._buttons["water"].pressed.emit()
	game.hud._buttons["light"].pressed.emit()
	game.hud._buttons["lamp"].pressed.emit()
	_check(game.state.to_dict() == before_pause, "Pause guard blocks care, lamp toggles, and purchases")
	game._process(1.0)
	_check(game.state.to_dict() == before_pause, "Paused root process does not advance plant growth or water")
	var player_position: Vector3 = game.player.position
	game._physics_process(0.2)
	_check(game.player.position == player_position, "Paused root physics leaves the player still")
	_check(game.hud._buttons["pause"].text == "RESUME", "Paused HUD displays resume")
	game.hud._buttons["pause"].pressed.emit()
	_check(not game.paused and game.hud._buttons["pause"].text == "PAUSE", "Pause HUD signal resumes the real scene")

	# Invalid progress is copied before the next legitimate save replaces it.
	var old_files := DirAccess.get_files_at(test_directory)
	var invalid_text := "{\"version\":999,\"reason\":\"scene save test fixture\"}"
	var invalid_file := FileAccess.open(save_file, FileAccess.WRITE)
	_check(invalid_file != null, "Invalid-save fixture opens its own temporary file")
	if invalid_file:
		invalid_file.store_string(invalid_text)
		invalid_file.close()
	game.state = STATE.new()
	game.selected = 0
	game._load_game()
	_check(game.state.to_dict() == STATE.new().to_dict(), "Invalid load leaves the fresh session intact")
	_check(FileAccess.get_file_as_string(save_file) == invalid_text, "Invalid original remains intact immediately after load")
	var backups: Array[String] = []
	var save_name := save_file.get_file()
	for filename: String in DirAccess.get_files_at(test_directory):
		if filename.begins_with(save_name + ".invalid-") and not old_files.has(filename):
			var backup_path := test_directory.path_join(filename)
			backups.append(backup_path)
			created_files.append(backup_path)
	_check(backups.size() == 1, "Invalid load creates exactly one owned backup")
	for backup: String in backups:
		_check(FileAccess.get_file_as_string(backup) == invalid_text, "Backup preserves the complete invalid original")
	_check(not game.testing, "Successful backup permits legitimate saves")
	game._save_game()
	_check(_same(_read_save(), game.state.to_dict()), "New legitimate save succeeds after invalid backup")
	for backup: String in backups:
		_check(FileAccess.get_file_as_string(backup) == invalid_text, "New save leaves the preserved invalid backup untouched")
	game.testing = true
	game.queue_free()
	await process_frame
	await process_frame
	_finish()


func _finish() -> void:
	# Every cleanup target is an exact path owned by this run inside res://tests.
	for path: String in created_files:
		var resolved := ProjectSettings.globalize_path(path)
		if resolved.get_base_dir() != test_directory.trim_suffix("/").trim_suffix("\\"):
			_check(false, "Cleanup target remains inside the test directory")
			continue
		if FileAccess.file_exists(resolved):
			var remove_error := DirAccess.remove_absolute(resolved)
			_check(remove_error == OK, "Cleanup removes only this run's file: " + resolved.get_file())
	if failures.is_empty():
		print("SCENE_SAVE_TEST_PASS: %d checks; real save overwrite/load, selection, HUD signals, pause guard, invalid backup, isolated cleanup" % checks)
		quit(0)
	else:
		print("SCENE_SAVE_TEST_FAIL: %d failures / %d checks" % [failures.size(), checks])
		quit(1)
