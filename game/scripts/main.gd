extends Node3D

const ROOM = preload("res://assets/rasta_bedroom.glb")
const AVATAR = preload("res://assets/rasta_character.glb")
const PROPS = preload("res://assets/starter_props.glb")
const STATE = preload("res://scripts/sim_state.gd")
const HUD = preload("res://scripts/hud.gd")
const POT_POSITIONS: Array[Vector3] = [Vector3(4.60, .20, -4.60), Vector3(5.60, .20, -4.60), Vector3(5.10, .20, -3.60)]
const APPROACH_POSITIONS: Array[Vector3] = [Vector3(4.60,.20,-3.50),Vector3(5.70,.20,-3.50),Vector3(5.10,.20,-2.60)]
const INTERACTION_RANGE: float = 1.30
const FOLIAGE_NAMES = {"seedling":"foliage_seedling", "growing":"foliage_small", "flowering":"foliage_medium", "ready":"foliage_bushy"}

var state: SimState = STATE.new()
var hud: GrowHUD
var room: Node3D
var prop_library: Node3D
var camera: Camera3D
var player: CharacterBody3D
var player_art: Node3D
var lamp: Node3D
var grow_rack: Node3D
var fan_art: Node3D
var grow_light: OmniLight3D
var pot_nodes: Array[Node3D] = []
var foliage_nodes: Array[Node3D] = []
var rings: Array[Node3D] = []
var labels: Array[Label3D] = []
var last_stages: Array[String] = ["", "", ""]
var selected: int = 0
var paused: bool = false
var muted: bool = false
var clock: float = 0.0
var save_timer: float = 0.0
var ui_timer: float = 0.0
var testing: bool = false
var save_path: String = "user://save.json"
var frames: Array[float] = []
var profile_seconds: float = 0.0
var capture_path: String = ""
var previous_frame_usec: int = 0
var walking: bool = false
var walk_path := PackedVector3Array()
var walk_target := Vector3.ZERO
var pending_care: String = ""
var pending_pot: int = -1
var navigation := AStarGrid2D.new()
var obstacles: Array[Dictionary] = []
var pot_colliders: Array[CollisionShape3D] = []
var budget_collider: CollisionShape3D
var rack_colliders: Array[CollisionShape3D] = []
var last_layout: String = ""
var care_timer: float = 0.0
var care_action: String = ""
var hand_can: Node3D
var joints: Dictionary = {}
var walk_progress_timer: float = 0.0
var walk_previous_position := Vector3.ZERO
var web_lifecycle_callback: Variant = null
var web_document: Variant = null
var web_window: Variant = null

func _ready() -> void:
	Engine.max_fps = 60
	for arg in OS.get_cmdline_user_args():
		if arg in ["--smoke-test","--fresh-preview","--care-preview"]:
			testing = true
		if arg == "--busy-preview":
			testing = true
			state.xp = 60
			state.level = 3
			state.cash = 100
			state.total_harvests = 3
			state.lamp_on = true
			state.upgraded_light = true
			state.fan = true
			for i in range(3):
				state.pots[i] = {"owned":true,"state":"ready","growth":1.0,"moisture":80.0,"health":100.0}
		if arg.begins_with("--save-path="):
			save_path = arg.trim_prefix("--save-path=")
		if arg.begins_with("--capture="):
			capture_path = arg.trim_prefix("--capture=")
		if arg.begins_with("--profile-seconds="):
			profile_seconds = float(arg.trim_prefix("--profile-seconds="))
			testing = true
	if not testing:
		_load_game()
	_build_world()
	hud = HUD.new()
	add_child(hud)
	hud.setup()
	hud.action_requested.connect(_action)
	_sync_visuals()
	_refresh_hud()
	hud.show_message("WASD to move. Click a pot to walk there, then press E to plant.")
	_setup_web_lifecycle()
	get_tree().auto_accept_quit = false
	if OS.get_cmdline_user_args().has("--smoke-test"):
		_run_smoke.call_deferred()
	elif OS.get_cmdline_user_args().has("--care-preview"):
		_run_care_preview.call_deferred()
	elif not capture_path.is_empty():
		_capture_after_delay.call_deferred()

func _build_world() -> void:
	room = ROOM.instantiate()
	add_child(room)
	prop_library = PROPS.instantiate()
	# Library nodes are detached copies, never rendered as a second scene.
	for n in ["cannabis_plant_small", "cannabis_plant_medium", "cannabis_plant_bushy", "water_reservoir"]:
		var old: Node3D = room.find_child(n, true, false) as Node3D
		if old:
			old.hide()
	grow_rack = room.find_child("grow_light_rack", true, false) as Node3D
	fan_art = room.find_child("small_fan", true, false) as Node3D
	if grow_rack:
		grow_rack.hide()
	if fan_art:
		fan_art.hide()
	lamp = _copy_prop("lamp_budget")
	add_child(lamp)
	lamp.position = POT_POSITIONS[0]
	lamp.rotation.y = PI
	var seed_packet: Node3D = _copy_prop("seed_packet")
	add_child(seed_packet)
	seed_packet.position = Vector3(3.35, .20, -2.7)
	for i in range(3):
		var root := Node3D.new()
		root.position = POT_POSITIONS[i]
		add_child(root)
		var pot: Node3D = _copy_prop("pot_empty")
		root.add_child(pot)
		pot_nodes.append(root)
		pot_colliders.append(_collision(POT_POSITIONS[i]+Vector3(0,.225,0),Vector3(.55,.45,.55)))
		var foliage := Node3D.new()
		foliage.position.y = .4
		root.add_child(foliage)
		foliage_nodes.append(foliage)
		var ring: Node3D = _make_ring()
		add_child(ring)
		ring.position = POT_POSITIONS[i] + Vector3(0, .015, 0)
		rings.append(ring)
		var label := Label3D.new()
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.no_depth_test = true
		label.font_size = 36
		label.pixel_size = .004
		label.outline_size = 8
		label.modulate = Color("f1e9cf")
		label.position = POT_POSITIONS[i] + Vector3(0, 1.65, 0)
		add_child(label)
		labels.append(label)
	_setup_player()
	# A handful of simple collision boxes keep movement inexpensive.
	_collision(Vector3(3.6, .1, -3.0), Vector3(7.2, .2, 6.0))
	_obstacle(Vector3(.075,1.7,-3.0),Vector3(.15,3.0,6.0))
	_obstacle(Vector3(3.6,1.7,-5.925),Vector3(7.2,3.0,.15))
	_obstacle(Vector3(1.175,.70,-4.5),Vector3(1.45,1.0,2.2))
	_obstacle(Vector3(6.05,.70,-1.25),Vector3(1.30,1.0,.70))
	_obstacle(Vector3(6.05,.50,-.55),Vector3(.50,.60,.50))
	_obstacle(Vector3(2.25,.65,-5.30),Vector3(.50,.90,.50))
	_obstacle(Vector3(.90,.65,-2.475),Vector3(1.20,.90,.65))
	# Budget lamp is rotated so its foot clears the second pot.
	budget_collider = _collision(POT_POSITIONS[0]+Vector3(-.55,.09,0),Vector3(.50,.18,.65))
	for x in [4.15,5.95]:
		for z in [-5.15,-4.15]:
			rack_colliders.append(_collision(Vector3(x,1.35,z),Vector3(.10,2.3,.10)))
	camera = Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 12.1
	camera.position = Vector3(13.6, 10.4, 9.3)
	add_child(camera)
	camera.look_at(Vector3(3.6, .9, -3.0))
	camera.h_offset = 2.10
	camera.v_offset = .75
	camera.current = true
	var env := WorldEnvironment.new()
	var settings := Environment.new()
	settings.background_mode = Environment.BG_COLOR
	settings.background_color = Color("182b2e")
	settings.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	settings.ambient_light_color = Color("c8ddd3")
	settings.ambient_light_energy = .45
	settings.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.environment = settings
	add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-55, -25, 0)
	sun.light_color = Color("fff1d3")
	sun.light_energy = .8
	sun.shadow_enabled = true
	add_child(sun)
	grow_light = OmniLight3D.new()
	grow_light.position = Vector3(5.1, 2.1, -4.35)
	grow_light.light_color = Color("ffa3dc")
	grow_light.omni_range = 2.5
	grow_light.light_energy = 0.0
	add_child(grow_light)
	var fill := OmniLight3D.new()
	fill.position = Vector3(2.25, 1.45, -5.3)
	fill.light_color = Color("ffcb83")
	fill.light_energy = .45
	fill.omni_range = 2.3
	add_child(fill)
	var plinth := MeshInstance3D.new()
	var plinth_mesh := BoxMesh.new()
	plinth_mesh.size = Vector3(7.45, .17, 6.25)
	plinth.mesh = plinth_mesh
	plinth.position = Vector3(3.6, -.09, -3.0)
	plinth.material_override = _mat(Color("122528"))
	add_child(plinth)
	var ground := MeshInstance3D.new()
	var ground_mesh := PlaneMesh.new()
	ground_mesh.size = Vector2(200, 200)
	ground.mesh = ground_mesh
	ground.position.y = -.2
	ground.material_override = _mat(Color("182b2e"))
	add_child(ground)

func _setup_player() -> void:
	var old_character: Node3D = room.find_child("home_grower_character",true,false) as Node3D
	if old_character:
		old_character.hide()
	player = CharacterBody3D.new()
	player.name = "Player"
	player.position = Vector3(3.35, .20, -1.95)
	add_child(player)
	player_art = AVATAR.instantiate()
	player.add_child(player_art)
	for joint_name in ["torso","head","arm_left","arm_right","leg_left","leg_right"]:
		joints[joint_name] = player_art.find_child(joint_name,true,false)
	var can_source: Node3D = room.find_child("watering_can",true,false) as Node3D
	if can_source and joints["arm_right"]:
		hand_can = can_source.duplicate() as Node3D
		joints["arm_right"].add_child(hand_can)
		hand_can.position = Vector3(0,-.40,.13)
		hand_can.rotation.y = -PI/2
		hand_can.scale = Vector3.ONE * .45
		hand_can.hide()
	var collider := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = .21
	capsule.height = 1.60
	collider.shape = capsule
	collider.position.y = .80
	player.add_child(collider)

func _copy_prop(prop_name: String) -> Node3D:
	var original: Node3D = prop_library.find_child(prop_name, true, false) as Node3D
	assert(original != null, "Missing voxel prop: " + prop_name)
	var copy: Node3D = original.duplicate() as Node3D
	copy.position = Vector3.ZERO
	copy.show()
	return copy

func _collision(pos: Vector3, bounds: Vector3) -> CollisionShape3D:
	var body := StaticBody3D.new()
	var shape := BoxShape3D.new()
	shape.size = bounds
	var collider := CollisionShape3D.new()
	collider.shape = shape
	body.add_child(collider)
	body.position = pos
	add_child(body)
	return collider

func _obstacle(pos: Vector3, bounds: Vector3) -> void:
	_collision(pos,bounds)
	obstacles.append({"position":pos,"size":bounds})

func _mat(color: Color, unshaded: bool = false) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = .9
	if unshaded:
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	return material

func _make_ring() -> Node3D:
	var root := Node3D.new()
	for side in range(4):
		var part := MeshInstance3D.new()
		var box := BoxMesh.new()
		box.size = Vector3(.65, .015, .035) if side < 2 else Vector3(.035, .015, .65)
		part.mesh = box
		part.position = [Vector3(0,0,-.31),Vector3(0,0,.31),Vector3(-.31,0,0),Vector3(.31,0,0)][side]
		part.material_override = _mat(Color("88d6b1"), true)
		root.add_child(part)
	return root

func _process(delta: float) -> void:
	clock += delta
	var now_usec: int = Time.get_ticks_usec()
	if profile_seconds > 0:
		if clock > 1.0 and previous_frame_usec > 0:
			frames.append(float(now_usec - previous_frame_usec) / 1000.0)
		if clock >= profile_seconds:
			_write_profile()
			get_tree().quit()
	previous_frame_usec = now_usec
	if not paused:
		state.tick(delta)
		care_timer = maxf(0.0,care_timer-delta)
		if fan_art and state.fan:
			# Gentle art motion; no simulation or expensive per-voxel updates.
			fan_art.rotation.y = sin(clock * 1.1) * .16
	ui_timer += delta
	save_timer += delta
	if ui_timer >= .1:
		ui_timer = 0.0
		_sync_visuals()
		_refresh_hud()
	if save_timer >= 5.0:
		save_timer = 0.0
		_save_game()
	for i in range(3):
		rings[i].scale = Vector3.ONE * (1.0 + .025 * sin(clock * 3.0)) if i == selected else Vector3.ONE

func _physics_process(delta: float) -> void:
	if paused or not player:
		return
	var direction := Vector2.ZERO
	if Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP):
		direction.y -= 1
	if Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN):
		direction.y += 1
	if Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT):
		direction.x -= 1
	if Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT):
		direction.x += 1
	var right := camera.global_basis.x
	var forward := camera.global_basis.z
	right.y = 0
	forward.y = 0
	var movement: Vector3 = (right.normalized() * direction.x + forward.normalized() * direction.y).normalized()
	if direction.length_squared() > .01:
		_cancel_walk()
	elif walking and care_timer <= 0:
		while not walk_path.is_empty() and _flat_distance(player.position,walk_path[0]) < .12:
			walk_path.remove_at(0)
		if not walk_path.is_empty():
			movement = (walk_path[0]-player.position)
			movement.y = 0
			movement = movement.normalized()
		else:
			walking = false
			var requested: String = pending_care
			var pot: int = pending_pot
			pending_care = ""
			pending_pot = -1
			if not requested.is_empty():
				_perform_care(requested,pot)
	if care_timer > 0:
		movement = Vector3.ZERO
	player.velocity.x = movement.x * 2.1
	player.velocity.z = movement.z * 2.1
	if not player.is_on_floor():
		player.velocity.y -= 9.8 * delta
	else:
		player.velocity.y = 0
	player.move_and_slide()
	player.position.x = clampf(player.position.x, .35, 6.90)
	player.position.z = clampf(player.position.z, -5.70, -.30)
	if walking:
		walk_progress_timer += delta
		if walk_progress_timer > 1.5:
			if _flat_distance(player.position,walk_previous_position) < .08:
				_cancel_walk()
				hud.show_message("Path blocked. Use WASD to step around the obstacle.",false)
			walk_previous_position = player.position
			walk_progress_timer = 0.0
	if player_art and movement.length_squared() > .01:
		player_art.rotation.y = lerp_angle(player_art.rotation.y, atan2(movement.x, movement.z), delta * 12)
		player_art.position.y = abs(sin(clock * 12)) * .025
	elif player_art:
		player_art.position.y = 0
	_animate_character(delta,movement.length_squared() > .01)

func _animate_character(delta: float, moving: bool) -> void:
	var swing: float = sin(clock*10.0)*.60 if moving else 0.0
	for part in ["arm_left","arm_right","leg_left","leg_right"]:
		var joint: Node3D = joints.get(part) as Node3D
		if not joint:
			continue
		var desired: float = swing * (1.0 if part in ["arm_left","leg_right"] else -1.0)
		if care_timer > 0:
			if part == "arm_right":
				desired = -.9 + sin(care_timer*9)*.12
			elif part == "arm_left":
				desired = -.45
		joint.rotation.x = lerpf(joint.rotation.x,desired,minf(delta*12.0,1.0))
	if hand_can:
		hand_can.visible = care_timer > 0 and care_action == "water"

func _flat_distance(a: Vector3,b: Vector3) -> float:
	return Vector2(a.x,a.z).distance_to(Vector2(b.x,b.z))

func is_near_pot(index: int) -> bool:
	return player != null and index >= 0 and index < 3 and _flat_distance(player.position,POT_POSITIONS[index]) <= INTERACTION_RANGE

func _rebuild_navigation() -> void:
	navigation.region = Rect2i(0,0,36,30)
	navigation.cell_size = Vector2(.2,.2)
	navigation.offset = Vector2(.1,.1)
	navigation.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	navigation.update()
	var active: Array[Dictionary] = obstacles.duplicate()
	for i in range(3):
		if state.pots[i]["owned"]:
			active.append({"position":POT_POSITIONS[i],"size":Vector3(.55,.45,.55)})
	if not state.upgraded_light:
		active.append({"position":POT_POSITIONS[0]+Vector3(-.55,0,0),"size":Vector3(.50,.18,.65)})
	else:
		for x in [4.15,5.95]:
			for z in [-5.15,-4.15]:
				active.append({"position":Vector3(x,0,z),"size":Vector3(.10,2.3,.10)})
	for x in range(36):
		for z in range(30):
			var p := Vector3(float(x)*.2+.1,.2,-(float(z)*.2+.1))
			var blocked: bool = p.x < .35 or p.x > 6.85 or p.z < -5.65 or p.z > -.35
			for obstacle: Dictionary in active:
				var position: Vector3 = obstacle["position"]
				var size: Vector3 = obstacle["size"]
				if absf(p.x-position.x) < size.x*.5+.24 and absf(p.z-position.z) < size.z*.5+.24:
					blocked = true
					break
			navigation.set_point_solid(Vector2i(x,z),blocked)

func _nearest_walkable(position: Vector3) -> Vector2i:
	var closest := Vector2i(-1,-1)
	var distance: float = INF
	for x in range(36):
		for z in range(30):
			var cell := Vector2i(x,z)
			if navigation.is_point_solid(cell):
				continue
			var p := Vector3(float(x)*.2+.1,.2,-(float(z)*.2+.1))
			var d: float = _flat_distance(position,p)
			if d < distance:
				distance = d
				closest = cell
	return closest

func approach_pot(index: int,requested_care: String = "") -> void:
	if index < 0 or index >= 3 or paused or care_timer > 0:
		return
	selected = index
	state.selected = index
	_walk_to(APPROACH_POSITIONS[index],requested_care,index)

func _walk_to(position: Vector3,requested_care: String = "",index: int = -1) -> void:
	if paused or care_timer > 0:
		return
	var start: Vector2i = _nearest_walkable(player.position)
	var finish: Vector2i = _nearest_walkable(position)
	if start.x < 0 or finish.x < 0:
		return
	var path: PackedVector2Array = navigation.get_point_path(start,finish)
	_cancel_walk()
	if path.is_empty():
		hud.show_message("No clear route. Use WASD to walk around the furniture.",false)
		return
	for point in path:
		walk_path.append(Vector3(point.x,.2,-point.y))
	walk_target = walk_path[-1]
	walking = true
	pending_care = requested_care
	pending_pot = index
	walk_previous_position = player.position
	if hud:
		hud.show_message("Walking to pot %s — WASD cancels." % (index+1) if index >= 0 else "Walking — WASD cancels.")
	_refresh_hud()

func _cancel_walk() -> void:
	walking = false
	walk_path.clear()
	pending_care = ""
	pending_pot = -1
	walk_progress_timer = 0.0

func _interact_nearest() -> void:
	if paused or care_timer > 0:
		return
	var index: int = selected if state.pots[selected]["owned"] and is_near_pot(selected) else -1
	if index < 0:
		var distance: float = INTERACTION_RANGE
		for i in range(3):
			if not state.pots[i]["owned"]:
				continue
			var d: float = _flat_distance(player.position,POT_POSITIONS[i])
			if d <= distance:
				distance = d
				index = i
	if index < 0:
		hud.show_message("Walk closer to a pot, or click it to walk over.",false)
		return
	selected = index
	state.selected = index
	var stage: String = state.pots[index]["state"]
	_perform_care("plant" if stage == "empty" else ("harvest" if stage == "ready" else "water"),index)

func _interaction_prompt() -> String:
	if care_timer > 0:
		return {"plant":"Planting a seed…","water":"Watering…","harvest":"Harvesting…"}.get(care_action,"Caring for your plant…")
	if walking:
		return "Walking to pot %s · WASD cancels" % (pending_pot+1) if pending_pot >= 0 else "Walking · WASD cancels"
	if not state.pots[selected]["owned"]:
		return "This space unlocks at level %s" % (selected+1)
	if not is_near_pot(selected):
		return "Click pot %s to walk over · or use WASD" % (selected+1)
	var stage: String = state.pots[selected]["state"]
	return "E: %s pot %s" % ["Plant in" if stage == "empty" else ("Harvest" if stage == "ready" else "Water"),selected+1]

func _refresh_hud() -> void:
	if hud:
		hud.refresh(state,selected,paused,is_near_pot(selected),walking,_interaction_prompt())

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_1: _action("select", 0)
			KEY_2: _action("select", 1)
			KEY_3: _action("select", 2)
			KEY_SPACE, KEY_ESCAPE: _action("pause", selected)
			KEY_L: _action("light", selected)
			KEY_M:
				muted = not muted
				hud.show_message("Sound muted" if muted else "Sound on")
			KEY_E:
				_interact_nearest()
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			camera.size = maxf(8.0, camera.size - .35)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			camera.size = minf(14.0, camera.size + .35)
		elif event.button_index == MOUSE_BUTTON_LEFT:
			var nearest: int = -1
			var distance: float = 65.0
			for i in range(3):
				var screen: Vector2 = camera.unproject_position(POT_POSITIONS[i] + Vector3(0,.45,0))
				var d: float = screen.distance_to(event.position)
				if d < distance:
					distance = d
					nearest = i
			if nearest >= 0:
				_action("select", nearest)
			elif not paused:
				var point: Variant = Plane(Vector3.UP,.2).intersects_ray(camera.project_ray_origin(event.position),camera.project_ray_normal(event.position))
				if point is Vector3 and point.x > .3 and point.x < 6.9 and point.z > -5.7 and point.z < -.3:
					_walk_to(point)

func _action(action: String, index: int) -> void:
	if action == "pause":
		paused = not paused
		_refresh_hud()
		hud.show_message("Paused — your plants can wait." if paused else "Back in the bedroom.")
		return
	if action == "select":
		selected = clampi(index, 0, 2)
		state.selected = selected
		_sync_visuals()
		if not paused:
			approach_pot(selected)
		_refresh_hud()
		return
	if paused:
		hud.show_message("Resume before caring for plants or buying equipment.", false)
		return
	if action in ["plant","water","harvest"]:
		if is_near_pot(index):
			_perform_care(action,index)
		else:
			approach_pot(index,action)
		return
	var result: Dictionary = {}
	match action:
		"light": result = state.toggle_light()
		"pot2", "lamp", "fan", "pot3": result = state.buy_upgrade(action)
		_: return
	_show_action_result(result,action,index)

func _perform_care(action: String,index: int) -> void:
	if paused or care_timer > 0 or index < 0 or index >= 3:
		return
	if not is_near_pot(index):
		hud.show_message("Walk closer to that plant first.",false)
		return
	_cancel_walk()
	var result: Dictionary = {}
	match action:
		"plant": result = state.plant(index)
		"water": result = state.water(index)
		"harvest": result = state.harvest(index)
		_: return
	if result.get("ok",false):
		selected = index
		state.selected = index
		care_timer = 1.05
		care_action = action
		var direction: Vector3 = POT_POSITIONS[index]-player.position
		player_art.rotation.y = atan2(direction.x,direction.z)
		_animate_character(.15,false)
		if action == "water":
			_water_stream(index)
	_show_action_result(result,action,index)

func _show_action_result(result: Dictionary,action: String,index: int) -> void:
	hud.show_message(str(result.get("message", "")), bool(result.get("ok", false)))
	if result.get("ok", false):
		_tone(720.0 if action == "harvest" else 480.0)
		if action in ["water", "plant", "harvest"]:
			_burst(POT_POSITIONS[index] + Vector3(0,.55,0), Color("83d8e4") if action == "water" else Color("f6ce78"))
		if action == "harvest":
			hud.show_reward("+%s XP  ·  +$%s%s" % [result.get("xp_added",20), result.get("revenue",30), "  ·  LEVEL UP!" if result.get("levelup",false) else ""])
		_save_game()
	_sync_visuals()
	_refresh_hud()

func _sync_visuals() -> void:
	for i in range(3):
		var pot: Dictionary = state.pots[i]
		pot_nodes[i].visible = bool(pot["owned"])
		var stage: String = str(pot["state"])
		if stage != last_stages[i]:
			for old in foliage_nodes[i].get_children():
				foliage_nodes[i].remove_child(old)
				old.queue_free()
			if stage != "empty":
				var art: Node3D = _copy_prop(str(FOLIAGE_NAMES[stage]))
				foliage_nodes[i].add_child(art)
				art.scale = Vector3.ONE * .85
				create_tween().tween_property(art, "scale", Vector3.ONE, .3).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
			last_stages[i] = stage
		for mesh in rings[i].get_children():
			(mesh as MeshInstance3D).material_override.albedo_color = Color("91dfb7") if i == selected else Color("4a6964")
		if not pot["owned"]:
			labels[i].text = "LV %s" % (2 if i == 1 else 3)
		elif i != selected:
			labels[i].text = str(i+1)
		elif stage == "empty":
			labels[i].text = "POT %s" % (i+1)
		else:
			labels[i].text = "%s · %s" % [i+1, "READY" if stage == "ready" else "%s%%" % roundi(float(pot["growth"]) * 100)]
		labels[i].modulate = Color("ffe08f") if stage == "ready" else Color("efead7")
		labels[i].position.y = POT_POSITIONS[i].y + (1.95 if stage in ["flowering", "ready"] else 1.35)
	lamp.visible = not state.upgraded_light
	if grow_rack:
		grow_rack.visible = state.upgraded_light
	if fan_art:
		fan_art.visible = state.fan
	grow_light.light_energy = (1.3 if state.upgraded_light else .55) if state.lamp_on else 0.0
	for i in range(3):
		pot_colliders[i].set_deferred("disabled",not state.pots[i]["owned"])
	budget_collider.set_deferred("disabled",state.upgraded_light)
	for collider: CollisionShape3D in rack_colliders:
		collider.set_deferred("disabled",not state.upgraded_light)
	var layout: String = str(state.pots[0]["owned"])+str(state.pots[1]["owned"])+str(state.pots[2]["owned"])+str(state.upgraded_light)
	if layout != last_layout:
		last_layout = layout
		_rebuild_navigation()

func _burst(pos: Vector3, color: Color) -> void:
	for i in range(14):
		var particle := MeshInstance3D.new()
		var box := BoxMesh.new()
		box.size = Vector3.ONE * .045
		particle.mesh = box
		particle.material_override = _mat(color, true)
		particle.position = pos
		add_child(particle)
		var finish: Vector3 = pos + Vector3(randf_range(-.32,.32),randf_range(.3,.85),randf_range(-.32,.32))
		var tween := create_tween().set_parallel(true)
		tween.tween_property(particle, "position", finish, .7).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		tween.tween_property(particle, "scale", Vector3.ZERO, .7)
		tween.chain().tween_callback(particle.queue_free)

func _water_stream(index: int) -> void:
	if not hand_can:
		return
	for i in range(10):
		var drop := MeshInstance3D.new()
		var cube := BoxMesh.new()
		cube.size = Vector3(.035,.06,.035)
		drop.mesh = cube
		drop.material_override = _mat(Color("79d1e7"),true)
		add_child(drop)
		drop.position = hand_can.global_position+Vector3(0,.15,0)
		drop.hide()
		var target: Vector3 = POT_POSITIONS[index]+Vector3(randf_range(-.10,.10),.42,randf_range(-.10,.10))
		var tween := create_tween()
		tween.tween_interval(float(i)*.055)
		tween.tween_callback(drop.show)
		tween.tween_property(drop,"position",target,.35)
		tween.tween_callback(drop.queue_free)

func _tone(frequency: float) -> void:
	if muted or DisplayServer.get_name() == "headless":
		return
	var audio := AudioStreamPlayer.new()
	var wave := AudioStreamWAV.new()
	wave.format = AudioStreamWAV.FORMAT_16_BITS
	wave.mix_rate = 22050
	var samples := PackedByteArray()
	samples.resize(4410)
	for i in range(2205):
		var amplitude: float = sin(TAU * frequency * float(i) / 22050.0) * (1.0-float(i)/2205.0) * .20
		samples.encode_s16(i * 2, int(amplitude * 32767))
	wave.data = samples
	audio.stream = wave
	audio.volume_db = -12
	add_child(audio)
	audio.finished.connect(audio.queue_free)
	audio.play()

func _save_game() -> void:
	if testing:
		return
	var data: Dictionary = state.to_dict()
	state.selected = selected
	data["selected"] = selected
	var file: FileAccess = FileAccess.open(save_path + ".tmp", FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(data, "", true, true))
		file.close()
		var commit_error: Error = DirAccess.rename_absolute(save_path + ".tmp", save_path)
		if commit_error != OK:
			push_warning("Save commit failed; temporary progress retained: " + error_string(commit_error))
	else:
		push_warning("Could not save progress: " + error_string(FileAccess.get_open_error()))

func _load_game() -> void:
	if not FileAccess.file_exists(save_path):
		return
	var file: FileAccess = FileAccess.open(save_path, FileAccess.READ)
	if not file:
		return
	var data: Variant = JSON.parse_string(file.get_as_text())
	if data is Dictionary and state.load_dict(data):
		selected = state.selected
	else:
		file.close()
		var backup: String = save_path + ".invalid-" + str(Time.get_unix_time_from_system()).replace(".","-")
		var backup_error: Error = DirAccess.copy_absolute(save_path, backup)
		if backup_error != OK:
			# Preserve the original if a backup cannot be made.
			testing = true
		push_warning("Invalid save preserved. Starting a new session; backup status: " + error_string(backup_error))

func _setup_web_lifecycle() -> void:
	if not OS.has_feature("web"):
		return
	var bridge: Object = Engine.get_singleton("JavaScriptBridge")
	# Keep the callback alive for as long as its browser listeners are registered.
	web_lifecycle_callback = bridge.call("create_callback", _on_web_lifecycle)
	web_document = bridge.call("get_interface", "document")
	web_window = bridge.call("get_interface", "window")
	web_document.addEventListener("visibilitychange", web_lifecycle_callback)
	web_window.addEventListener("pagehide", web_lifecycle_callback)
	if not OS.is_userfs_persistent():
		hud.show_message("Browser storage is unavailable. Progress lasts for this session only.", false)

func _on_web_lifecycle(arguments: Array) -> void:
	if not OS.has_feature("web") or arguments.is_empty():
		return
	if str(arguments[0].type) == "pagehide" or bool(web_document.hidden):
		_pause_and_save()

func _pause_and_save() -> void:
	if testing or not is_instance_valid(hud):
		return
	paused = true
	_save_game()
	_refresh_hud()

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		_save_game()
		prop_library.free()
		get_tree().quit()
	elif what in [NOTIFICATION_APPLICATION_FOCUS_OUT, NOTIFICATION_WM_WINDOW_FOCUS_OUT]:
		_pause_and_save()

func _exit_tree() -> void:
	if OS.has_feature("web") and web_lifecycle_callback != null:
		web_document.removeEventListener("visibilitychange", web_lifecycle_callback)
		web_window.removeEventListener("pagehide", web_lifecycle_callback)
		web_lifecycle_callback = null
		web_document = null
		web_window = null
	if is_instance_valid(prop_library):
		prop_library.free()

func _capture_after_delay() -> void:
	await get_tree().create_timer(1.5).timeout
	await RenderingServer.frame_post_draw
	var image: Image = get_viewport().get_texture().get_image()
	var err: Error = image.save_png(capture_path)
	print("PREVIEW_CAPTURE: ", err, " ", capture_path)

func _run_care_preview() -> void:
	await get_tree().create_timer(.3).timeout
	_action("plant",0)
	for frame in range(600):
		await get_tree().physics_frame
		if not walking:
			break
	await get_tree().create_timer(1.1).timeout
	_action("light",0)
	state.tick(25.0)
	_action("water",0)
	await get_tree().create_timer(.15).timeout
	await RenderingServer.frame_post_draw
	if not capture_path.is_empty():
		get_viewport().get_texture().get_image().save_png(capture_path)
	print("CARE_PREVIEW_CAPTURE: actual walk, plant, turn and water animation")
	get_tree().quit()

func _run_smoke() -> void:
	await get_tree().create_timer(.3).timeout
	if not _smoke_expect(state.level == 1 and state.xp == 0,"starter XP"): return
	if not _smoke_expect(not state.pots[1]["owned"] and not grow_rack.visible and not fan_art.visible,"starter equipment"): return
	_interact_nearest()
	if not _smoke_expect(state.cash == 25 and state.pots[0]["state"] == "empty","far E does not plant"): return
	_action("plant",0)
	if not _smoke_expect(walking and state.cash == 25,"care queues walk first"): return
	for frame in range(600):
		await get_tree().physics_frame
		if not walking:
			break
	if not _smoke_expect(state.pots[0]["state"] == "seedling" and is_near_pot(0),"character arrives and plants once"): return
	await get_tree().create_timer(1.1).timeout
	_action("light",0)
	_action("water",0)
	await get_tree().create_timer(1.1).timeout
	for i in range(100):
		if float(state.pots[0]["moisture"]) < 45:
			state.water(0)
		state.tick(1.0)
	if not _smoke_expect(state.pots[0]["state"] == "ready","crop completes"): return
	_sync_visuals()
	_action("harvest",0)
	if not _smoke_expect(state.level == 2 and state.xp == 20,"harvest level-up"): return
	_action("pot2",1)
	if not _smoke_expect(state.pots[1]["owned"],"second pot purchase"): return
	var snapshot: Dictionary = state.to_dict()
	var restored: SimState = STATE.new()
	if not _smoke_expect(restored.load_dict(snapshot),"load valid progress"): return
	if not _smoke_expect(restored.to_dict() == snapshot,"progress roundtrip"): return
	paused = true
	var before: Dictionary = state.to_dict()
	_action("plant",1)
	if not _smoke_expect(state.to_dict() == before,"pause guard"): return
	paused = false
	if not capture_path.is_empty():
		await get_tree().create_timer(.7).timeout
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(capture_path)
	print("INTEGRATION_SMOKE_PASS: starter -> far E guard -> walk to pot -> plant -> light -> water animation -> growth -> harvest -> level2 -> upgrade -> progress roundtrip -> pause guard")
	get_tree().quit()

func _smoke_expect(condition: bool, check: String) -> bool:
	if not condition:
		push_error("INTEGRATION_SMOKE_FAIL: " + check)
		get_tree().quit(1)
	return condition

func _write_profile() -> void:
	frames.sort()
	var mean: float = 0.0
	for value in frames:
		mean += value
	mean /= maxf(float(frames.size()),1)
	var report := {"frames":frames.size(), "mean_ms":mean, "p95_ms":frames[int(frames.size()*.95)] if not frames.is_empty() else 0, "fps_from_mean":1000.0/mean if mean > 0 else 0, "render_objects":Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME), "draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), "primitives":Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME), "engine":Engine.get_version_info()["string"], "renderer":RenderingServer.get_current_rendering_method(), "gpu":RenderingServer.get_video_adapter_name()}
	print("PERFORMANCE_REPORT: ",JSON.stringify(report))
