extends SceneTree

const MAIN_SCENE = preload("res://main.tscn")

var checks := 0
var failures: Array[String] = []
var route_steps := 0
var unsafe_positions := 0


func _initialize() -> void:
	call_deferred("_run")


func _check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error("CHARACTER_INTERACTION_TEST: " + message)


func _xz(position: Vector3) -> Vector2:
	return Vector2(position.x, position.z)


func _player_is_clear(game: Variant) -> bool:
	var capsule_node: CollisionShape3D
	for child: Node in game.player.get_children():
		if child is CollisionShape3D and child.shape is CapsuleShape3D:
			capsule_node = child
			break
	if not capsule_node:
		return false
	var capsule: CapsuleShape3D = capsule_node.shape
	var center: Vector3 = capsule_node.global_position
	var bottom: float = center.y - capsule.height * 0.5
	var top: float = center.y + capsule.height * 0.5
	var radius: float = capsule.radius
	for body: Node in game.get_children():
		if not body is StaticBody3D:
			continue
		for child: Node in body.get_children():
			if not child is CollisionShape3D or not child.shape is BoxShape3D:
				continue
			if child.disabled:
				continue
			var box: BoxShape3D = child.shape
			var half_size: Vector3 = box.size * 0.5
			var box_center: Vector3 = child.global_position
			if box.size.y < 0.3 and box.size.x > 5.0:
				if bottom < box_center.y + half_size.y - 0.035:
					return false
				continue
			if top <= box_center.y - half_size.y + 0.015 or bottom >= box_center.y + half_size.y - 0.015:
				continue
			var closest_x := clampf(center.x, box_center.x - half_size.x, box_center.x + half_size.x)
			var closest_z := clampf(center.z, box_center.z - half_size.z, box_center.z + half_size.z)
			var separation := Vector2(center.x - closest_x, center.z - closest_z).length()
			if separation < radius - 0.018:
				return false
	return true


func _drive_walk(game: Variant, maximum_steps: int = 720) -> bool:
	for step: int in range(maximum_steps):
		if not game.walking:
			return true
		await physics_frame
		game._physics_process(1.0 / 60.0)
		route_steps += 1
		if not _player_is_clear(game):
			unsafe_positions += 1
	return not game.walking


func _run() -> void:
	root.size = Vector2i(1280, 800)
	var game: Variant = MAIN_SCENE.instantiate()
	game.testing = true
	root.add_child(game)
	await process_frame
	await process_frame
	game.set_process(false)
	game.set_physics_process(false)
	game.testing = true
	game.paused = false
	var spawn: Vector3 = game.player.position
	_check(not game.is_near_pot(0), "Bedroom spawn starts outside pot interaction range")
	_check(game.state.cash == 25 and game.state.pots[0]["state"] == "empty", "Starter state is unplanted")
	var fresh: Dictionary = game.state.to_dict()
	game._interact_nearest()
	_check(game.state.to_dict() == fresh, "E cannot plant remotely or spend cash")
	_check(not game.walking, "Distant E interaction does not queue a care action")
	game._perform_care("plant", 0)
	_check(game.state.to_dict() == fresh, "Direct care also rejects distant interaction")
	game.hud.refresh(game.state, 0, false, false, false)
	_check(game.hud._care_note.text.contains("Walk to pot 1"), "Far HUD shows where to walk")
	_check(game.hud._buttons["plant"].text == "WALK & PLANT" and not game.hud._buttons["plant"].disabled, "Valid distant care stays clickable and describes walking")
	game.hud._buttons["plant"].pressed.emit()
	_check(game.walking and game.pending_care == "plant" and game.pending_pot == 0, "Actual plant button queues an approach and care action")
	_check(game.state.to_dict() == fresh, "Queued planting does not mutate state before arrival")
	var completed: bool = await _drive_walk(game)
	_check(completed, "Player reaches the first pot through the actual physics route")
	_check(game.is_near_pot(0), "Arrival is within the 1.3m interaction range")
	_check(game.state.cash == 20 and game.state.pots[0]["state"] == "seedling", "Arrival executes the queued planting once")
	_check(game.pending_care.is_empty(), "Executed care clears its pending action")
	for step: int in range(20):
		await physics_frame
		game._physics_process(1.0 / 60.0)
	_check(game.state.cash == 20, "Idle physics does not repeat planting")
	game.hud.refresh(game.state, 0, false, true, false)
	_check(game.hud._care_note.text.begins_with("E: WATER") and game.hud._buttons["water"].text == "WATER", "Near HUD presents the direct E action")

	# Upgrade fixtures retain the first plant while making nearby slots usable.
	game.state.level = 3
	game.state.xp = 60
	game.state.cash = 300
	_check(game.state.buy_upgrade("pot2")["ok"], "Second pot fixture is legally unlocked")
	_check(game.state.buy_upgrade("pot3")["ok"], "Third pot fixture is legally unlocked")
	game._sync_visuals()
	game._cancel_walk()
	game.care_timer = 0.0
	game.player.position = game.POT_POSITIONS[1] + Vector3(0.95, 0, 0)
	game.selected = 0
	game.state.selected = 0
	var before_near: int = game.state.cash
	game._interact_nearest()
	_check(game.selected == 1 and game.state.selected == 1, "E selects the nearest owned pot instead of a distant selection")
	_check(game.state.pots[1]["state"] == "seedling" and game.state.cash == before_near - 5, "Near E plants in the actual nearest pot")
	_check(game.state.pots[2]["state"] == "empty", "Nearest interaction leaves other pots alone")

	# Cancelling a queued route must discard the pending action too.
	game.player.position = spawn
	game.player.velocity = Vector3.ZERO
	game.care_timer = 0.0
	game.selected = 0
	game.state.selected = 0
	var before_cancel: Dictionary = game.state.to_dict()
	game.approach_pot(0, "water")
	_check(game.walking and game.pending_care == "water", "Water can be queued from across the room")
	game._cancel_walk()
	_check(not game.walking and game.walk_path.is_empty() and game.pending_care.is_empty(), "Manual movement cancellation clears route and pending care")
	var cancelled_position: Vector2 = _xz(game.player.position)
	for step: int in range(3):
		await physics_frame
		game._physics_process(1.0 / 60.0)
	_check(_xz(game.player.position).distance_to(cancelled_position) < 0.01, "Cancelled auto-walk stays cancelled")
	_check(game.state.to_dict() == before_cancel, "Cancelling a route never executes pending care")
	game.approach_pot(0, "water")
	var manual_key := InputEventKey.new()
	manual_key.physical_keycode = KEY_W
	manual_key.keycode = KEY_W
	manual_key.pressed = true
	Input.parse_input_event(manual_key)
	await physics_frame
	game._physics_process(1.0 / 60.0)
	_check(not game.walking and game.pending_care.is_empty(), "W movement cancels the queued route through the actual input branch")
	manual_key.pressed = false
	Input.parse_input_event(manual_key)
	_check(game.state.to_dict() == before_cancel, "Manual walking does not perform cancelled care")

	# Pausing freezes a live route and protects every care entry point.
	game.approach_pot(0, "water")
	game._action("pause", game.selected)
	var paused_position: Vector3 = game.player.position
	var paused_state: Dictionary = game.state.to_dict()
	for step: int in range(8):
		await physics_frame
		game._physics_process(1.0 / 60.0)
	game._perform_care("water", 0)
	game._action("water", 0)
	_check(game.paused and game.player.position == paused_position, "Pause freezes the queued walk")
	_check(game.state.to_dict() == paused_state, "Pause protects both care entry points")
	game.hud._buttons["pause"].pressed.emit()
	_check(not game.paused, "HUD pause signal resumes character interaction")
	game._cancel_walk()

	# Harvest also walks first, and rewards are issued once at arrival.
	game.state.pots[0]["state"] = "ready"
	game.state.pots[0]["growth"] = 1.0
	game.state.pots[0]["moisture"] = 80.0
	game.player.position = spawn
	game.player.velocity = Vector3.ZERO
	game.care_timer = 0.0
	game._sync_visuals()
	var cash_before_harvest: int = game.state.cash
	var xp_before_harvest: int = game.state.xp
	game._action("harvest", 0)
	_check(game.walking and game.state.cash == cash_before_harvest, "Distant harvest queues walking without early rewards")
	completed = await _drive_walk(game)
	_check(completed and game.is_near_pot(0), "Harvest approach reaches interaction distance")
	_check(game.state.cash == cash_before_harvest + 30 and game.state.xp == xp_before_harvest + 20, "Harvest arrival grants one cash and XP reward")
	_check(game.state.pots[0]["state"] == "empty" and game.pending_care.is_empty(), "Harvest arrival clears the crop and pending action")
	for step: int in range(15):
		await physics_frame
		game._physics_process(1.0 / 60.0)
	_check(game.state.cash == cash_before_harvest + 30, "Idle physics never repeats the harvest reward")

	# The front pot and upgraded rack change the rear approach routes.
	game.state.level = 3
	game.state.xp = 60
	game.state.cash = 100
	game.state.upgraded_light = true
	for pot: Dictionary in game.state.pots:
		pot["owned"] = true
	game._cancel_walk()
	game.care_timer = 0.0
	game._sync_visuals()
	await physics_frame
	await physics_frame
	for index: int in range(3):
		game._cancel_walk()
		game.player.position = Vector3(3.35, 0.2, -1.95)
		game.player.velocity = Vector3.ZERO
		game.care_timer = 0.0
		var unsafe_before: int = unsafe_positions
		game.approach_pot(index)
		_check(game.walking, "Expanded setup starts approach to pot %d" % (index + 1))
		completed = await _drive_walk(game, 250)
		_check(completed, "Expanded setup reaches pot %d within 250 physics steps" % (index + 1))
		_check(game.is_near_pot(index), "Expanded setup arrival is near pot %d" % (index + 1))
		_check(unsafe_positions == unsafe_before and _player_is_clear(game), "Expanded route to pot %d clears the floor, furniture, pots and rack" % (index + 1))
	_check(unsafe_positions == 0, "Walk routes keep the capsule above the floor and outside furniture")
	game.queue_free()
	await process_frame
	await process_frame
	if failures.is_empty():
		print("CHARACTER_INTERACTION_TEST_PASS: %d checks; %d actual physics route steps; remote E guard, queued care, nearest pot, cancellation, pause, collision clearance" % [checks, route_steps])
		quit(0)
	else:
		print("CHARACTER_INTERACTION_TEST_FAIL: %d failures / %d checks; unsafe positions=%d" % [failures.size(), checks, unsafe_positions])
		quit(1)
