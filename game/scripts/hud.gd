extends CanvasLayer
class_name GrowHUD

signal action_requested(action: String, index: int)

const CREAM := Color("eee9d4")
const MUTED := Color("b3b8a8")
const TEAL := Color("8fc59b")
const GOLD := Color("efc778")
const RED := Color("cc6b61")
const DARK := Color("262925")
const PANEL := Color(0.085, 0.09, 0.08, 0.95)
const WARNING := Color("f2997d")

var _built := false
var _selected := 0
var _level_label: Label
var _cash_label: Label
var _xp_label: Label
var _xp_bar: ProgressBar
var _objective_label: Label
var _pot_title: Label
var _stage_label: Label
var _growth_label: Label
var _growth_bar: ProgressBar
var _water_label: Label
var _water_bar: ProgressBar
var _health_label: Label
var _health_bar: ProgressBar
var _care_note: Label
var _pot_buttons: Array[Button] = []
var _buttons: Dictionary = {}
var _toast: PanelContainer
var _toast_label: Label
var _toast_time := 0.0
var _reward_label: Label
var _reward_time := 0.0


func _ready() -> void:
	setup()


func setup() -> void:
	if _built:
		return
	_built = true
	layer = 10
	var overlay := Control.new()
	overlay.name = "HUD"
	overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	overlay.theme = _make_theme()
	add_child(overlay)
	_build_top(overlay)
	_build_sidebar(overlay)
	_build_messages(overlay)
	var hints := _label("WASD  move / cancel walk   •   Click pot  walk   •   E  interact   •   Space  pause   •   Wheel  zoom", 12, MUTED)
	hints.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hints.offset_left = 22
	hints.offset_right = -324
	hints.offset_top = -37
	hints.offset_bottom = -18
	hints.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hints.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	overlay.add_child(hints)


func _build_top(overlay: Control) -> void:
	var top := PanelContainer.new()
	top.name = "ProgressCard"
	top.anchor_right = 1.0
	top.offset_left = 20
	top.offset_right = -324
	top.offset_top = 20
	top.mouse_filter = Control.MOUSE_FILTER_STOP
	var box := _panel_content(top, 15)
	box.add_theme_constant_override("separation", 8)
	overlay.add_child(top)
	_add_stripe(box)
	var heading := HBoxContainer.new()
	heading.add_theme_constant_override("separation", 18)
	box.add_child(heading)
	var title := _label("BEDROOM ROOTS", 22, CREAM)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	heading.add_child(title)
	_level_label = _label("LEVEL 1", 16, TEAL)
	heading.add_child(_level_label)
	_cash_label = _label("$0", 21, GOLD)
	_cash_label.custom_minimum_size.x = 73
	_cash_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	heading.add_child(_cash_label)
	var xp_row := HBoxContainer.new()
	xp_row.add_theme_constant_override("separation", 10)
	box.add_child(xp_row)
	_xp_label = _label("0 / 20 XP", 12, MUTED)
	_xp_label.custom_minimum_size.x = 106
	xp_row.add_child(_xp_label)
	_xp_bar = _bar(TEAL, 8)
	_xp_bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_xp_bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	xp_row.add_child(_xp_bar)
	_objective_label = _label("Plant your first seed.", 14, CREAM)
	_objective_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(_objective_label)


func _build_sidebar(overlay: Control) -> void:
	var sidebar := PanelContainer.new()
	sidebar.name = "PotControls"
	sidebar.anchor_left = 1.0
	sidebar.anchor_right = 1.0
	sidebar.anchor_bottom = 1.0
	sidebar.offset_left = -304
	sidebar.offset_right = -20
	sidebar.offset_top = 20
	sidebar.offset_bottom = -20
	sidebar.mouse_filter = Control.MOUSE_FILTER_STOP
	overlay.add_child(sidebar)
	var margin := MarginContainer.new()
	for edge in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_" + edge, 14)
	sidebar.add_child(margin)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	margin.add_child(scroll)
	var box := VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.add_theme_constant_override("separation", 8)
	scroll.add_child(box)
	_add_stripe(box)
	box.add_child(_label("YOUR FIRST ROOM", 11, MUTED))
	_pot_title = _label("POT 1", 21, CREAM)
	box.add_child(_pot_title)
	var selectors := HBoxContainer.new()
	selectors.add_theme_constant_override("separation", 6)
	box.add_child(selectors)
	for index in range(3):
		var button := _button("POT %d" % (index + 1))
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.custom_minimum_size.y = 36
		button.pressed.connect(_request.bind("select", index))
		selectors.add_child(button)
		_pot_buttons.append(button)
	_stage_label = _label("EMPTY • READY FOR A SEED", 12, TEAL)
	box.add_child(_stage_label)
	_growth_label = _label("GROWTH     0%", 12, MUTED)
	box.add_child(_growth_label)
	_growth_bar = _bar(TEAL, 11)
	box.add_child(_growth_bar)
	_water_label = _label("WATER     0%", 12, MUTED)
	box.add_child(_water_label)
	_water_bar = _bar(Color("72bcd5"), 9)
	box.add_child(_water_bar)
	_health_label = _label("HEALTH     0%", 12, MUTED)
	box.add_child(_health_label)
	_health_bar = _bar(GOLD, 9)
	box.add_child(_health_bar)
	_care_note = _label("A tiny start. Plant a seed to begin.", 12, MUTED)
	_care_note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_care_note.custom_minimum_size.y = 35
	box.add_child(_care_note)
	var care_grid := GridContainer.new()
	care_grid.columns = 2
	care_grid.add_theme_constant_override("h_separation", 6)
	care_grid.add_theme_constant_override("v_separation", 6)
	box.add_child(care_grid)
	_add_action(care_grid, "plant", "WALK & PLANT", "Walk to the selected pot, then plant a $5 seed.")
	_add_action(care_grid, "water", "WALK & WATER", "Walk to the selected pot, then refill its water meter.")
	_add_action(care_grid, "harvest", "WALK & HARVEST", "Walk to the selected pot, then collect cash and XP.")
	_add_action(care_grid, "light", "LAMP: ON", "The lamp helps your game plants grow.")
	_add_action(box, "pause", "PAUSE", "Pause plant timers. Space also pauses.")
	var separator := HSeparator.new()
	separator.add_theme_color_override("separator", Color(0.4, 0.6, 0.55, 0.2))
	box.add_child(separator)
	box.add_child(_label("BUILD UP YOUR SETUP", 11, GOLD))
	_add_action(box, "pot2", "SECOND POT   $35  /  LV 2", "Unlock level 2 and spend $35 to grow a second plant.")
	_add_action(box, "lamp", "BETTER LAMP   $45  /  LV 2", "Unlock level 2 and spend $45 for faster game growth.")
	_add_action(box, "fan", "ROOM FAN   $30  /  LV 3", "Unlock level 3 and spend $30 for steadier game health.")
	_add_action(box, "pot3", "THIRD POT   $55  /  LV 3", "Unlock level 3 and spend $55 for a third plant.")
	var footer := _label("Small room. Big plans.\nCare / harvest / sell / upgrade.", 12, MUTED)
	footer.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(footer)


func _build_messages(overlay: Control) -> void:
	_toast = PanelContainer.new()
	_toast.name = "Feedback"
	_toast.anchor_top = 1.0
	_toast.anchor_bottom = 1.0
	_toast.anchor_right = 1.0
	_toast.offset_left = 20
	_toast.offset_right = -324
	_toast.offset_top = -94
	_toast.offset_bottom = -49
	_toast.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_toast.add_theme_stylebox_override("panel", _style(Color(0.08, 0.18, 0.17, 0.97), TEAL, 1))
	var box := _panel_content(_toast, 12)
	_toast_label = _label("", 15, CREAM)
	_toast_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_toast_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(_toast_label)
	_toast.hide()
	overlay.add_child(_toast)
	_reward_label = _label("", 24, GOLD)
	_reward_label.anchor_left = 0.0
	_reward_label.anchor_right = 1.0
	_reward_label.anchor_top = 0.5
	_reward_label.anchor_bottom = 0.5
	_reward_label.offset_left = 20
	_reward_label.offset_right = -324
	_reward_label.offset_top = -50
	_reward_label.offset_bottom = -8
	_reward_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_reward_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_reward_label.add_theme_color_override("font_shadow_color", Color(0.03, 0.06, 0.06, 0.85))
	_reward_label.add_theme_constant_override("shadow_offset_x", 2)
	_reward_label.add_theme_constant_override("shadow_offset_y", 2)
	_reward_label.hide()
	overlay.add_child(_reward_label)


func refresh(state: SimState, selected: int, paused: bool, near_pot: bool = false, is_walking: bool = false, interaction_text: String = "") -> void:
	setup()
	_selected = clampi(selected, 0, maxi(0, state.pots.size() - 1))
	var pot: Dictionary = state.pots[_selected]
	var owned: bool = bool(pot.get("owned", false))
	var stage: String = str(pot.get("state", "empty"))
	var growth: float = float(pot.get("growth", 0.0)) * 100.0
	var moisture: float = float(pot.get("moisture", 0.0))
	var health: float = float(pot.get("health", 0.0))
	var active := owned and stage != "empty"
	_level_label.text = "LEVEL %d" % state.level
	_cash_label.text = "$%d" % state.cash
	var xp_target: int = state.xp_target()
	_xp_label.text = "%d XP • MAX" % state.xp if state.level >= 3 else "%d / %d XP" % [state.xp, xp_target]
	_xp_bar.max_value = maxi(1, xp_target)
	_xp_bar.value = state.xp
	_objective_label.text = "NEXT: " + state.objective()
	if paused:
		_objective_label.text = "PAUSED  •  " + state.objective()
	_pot_title.text = "POT %d" % (_selected + 1)
	for index in range(_pot_buttons.size()):
		var slot_owned := index < state.pots.size() and bool(state.pots[index].get("owned", false))
		_pot_buttons[index].text = "POT %d" % (index + 1) if slot_owned else "LOCKED"
		_pot_buttons[index].tooltip_text = "Walk to pot %d. WASD cancels the route." % (index + 1) if slot_owned else "Buy this pot after unlocking its level."
		_pot_buttons[index].add_theme_color_override("font_color", TEAL if index == _selected else CREAM)
		_pot_buttons[index].add_theme_stylebox_override("normal", _style(Color("234844") if index == _selected else DARK, TEAL if index == _selected else Color("35504b"), 1))
	var stage_text := stage.to_upper()
	if not owned:
		stage_text = "LOCKED • UPGRADE YOUR ROOM"
	elif stage == "empty":
		stage_text = "EMPTY • READY FOR A SEED"
	elif stage == "ready":
		stage_text = "READY • TIME TO HARVEST"
	_stage_label.text = stage_text
	_stage_label.modulate = GOLD if stage == "ready" else TEAL
	_growth_label.text = "GROWTH     %d%%" % roundi(growth)
	_water_label.text = "WATER     %d%%" % roundi(moisture)
	_health_label.text = "HEALTH     %d%%" % roundi(health)
	_growth_bar.value = growth if active else 0
	_water_bar.value = moisture if active else 0
	_health_bar.value = health if active else 0
	_water_label.modulate = WARNING if active and moisture < 25 else Color.WHITE
	_health_label.modulate = WARNING if active and health < 40 else Color.WHITE
	var care_action := "plant" if stage == "empty" else ("harvest" if stage == "ready" else "water")
	_care_note.modulate = GOLD if near_pot else TEAL
	if not owned:
		_care_note.text = "Unlock this space in the upgrades below."
	elif paused:
		_care_note.text = "Paused. Resume to walk or care for plants."
	elif not interaction_text.is_empty():
		_care_note.text = interaction_text
	elif is_walking:
		_care_note.text = "Walking to pot %d…\nWASD cancels the route." % (_selected + 1)
	elif near_pot:
		_care_note.text = "E: %s  ·  POT %d" % [care_action.to_upper(), _selected + 1]
	else:
		_care_note.text = "Walk to pot %d · E to %s" % [_selected + 1, care_action]
	_buttons["plant"].text = "PLANT SEED  $5" if near_pot else "WALK & PLANT"
	_buttons["water"].text = "WATER" if near_pot else "WALK & WATER"
	_buttons["harvest"].text = "HARVEST & SELL" if near_pot else "WALK & HARVEST"
	_buttons["plant"].tooltip_text = "Plant a $5 seed here (E)." if near_pot else "Walk to pot %d, then plant a $5 seed. WASD cancels." % (_selected + 1)
	_buttons["water"].tooltip_text = "Refill this plant's water meter (E)." if near_pot else "Walk to pot %d, then water it. WASD cancels." % (_selected + 1)
	_buttons["harvest"].tooltip_text = "Harvest here for cash and XP (E)." if near_pot else "Walk to pot %d, then harvest it. WASD cancels." % (_selected + 1)
	_buttons["plant"].disabled = not owned or stage != "empty" or state.cash < 5
	_buttons["water"].disabled = not active or stage == "ready" or moisture >= 99
	_buttons["harvest"].disabled = not owned or stage != "ready"
	_buttons["light"].text = "LAMP: ON" if state.lamp_on else "LAMP: OFF"
	_buttons["pause"].text = "RESUME" if paused else "PAUSE"
	var second_owned := state.pots.size() > 1 and bool(state.pots[1].get("owned", false))
	var third_owned := state.pots.size() > 2 and bool(state.pots[2].get("owned", false))
	_refresh_upgrade("pot2", "SECOND POT", 35, 2, second_owned, state)
	_refresh_upgrade("lamp", "BETTER LAMP", 45, 2, state.upgraded_light, state)
	_refresh_upgrade("fan", "ROOM FAN", 30, 3, state.fan, state)
	_refresh_upgrade("pot3", "THIRD POT", 55, 3, third_owned, state)
	_buttons["pot3"].disabled = _buttons["pot3"].disabled or not second_owned


func _refresh_upgrade(id: String, title: String, price: int, level: int, bought: bool, state: SimState) -> void:
	var button: Button = _buttons[id]
	button.disabled = bought or state.level < level or state.cash < price
	if bought:
		button.text = title + "   ✓ OWNED"
	elif state.level < level:
		button.text = "%s   $%d  /  LV %d" % [title, price, level]
	else:
		button.text = "%s   $%d" % [title, price]


func show_message(message: String, good: bool = true) -> void:
	setup()
	_toast_label.text = message
	_toast_label.modulate = CREAM if good else WARNING
	_toast.modulate.a = 1.0
	_toast.show()
	_toast_time = 4.0


func show_reward(text: String) -> void:
	setup()
	_reward_label.text = text
	_reward_label.modulate.a = 1.0
	_reward_label.show()
	_reward_time = 2.8


func _process(delta: float) -> void:
	if _toast_time > 0.0:
		_toast_time = maxf(0.0, _toast_time - delta)
		_toast.modulate.a = minf(1.0, _toast_time * 2.0)
		if _toast_time == 0.0:
			_toast.hide()
	if _reward_time > 0.0:
		_reward_time = maxf(0.0, _reward_time - delta)
		_reward_label.modulate.a = minf(1.0, _reward_time)
		if _reward_time == 0.0:
			_reward_label.hide()


func _add_action(parent: Control, action: String, caption: String, tooltip: String) -> void:
	var button := _button(caption)
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.custom_minimum_size.y = 36
	button.tooltip_text = tooltip
	button.pressed.connect(_request_selected.bind(action))
	parent.add_child(button)
	_buttons[action] = button


func _request_selected(action: String) -> void:
	_request(action, _selected)


func _request(action: String, index: int) -> void:
	action_requested.emit(action, index)


func _label(caption: String, font_size: int = 14, color: Color = CREAM) -> Label:
	var label := Label.new()
	label.text = caption
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", color)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return label


func _button(caption: String) -> Button:
	var button := Button.new()
	button.text = caption
	button.add_theme_font_size_override("font_size", 12)
	button.mouse_filter = Control.MOUSE_FILTER_STOP
	button.focus_mode = Control.FOCUS_NONE
	return button


func _bar(color: Color, height: float) -> ProgressBar:
	var bar := ProgressBar.new()
	bar.min_value = 0
	bar.max_value = 100
	bar.show_percentage = false
	bar.custom_minimum_size.y = height
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var background := _style(Color("263b38"), Color.TRANSPARENT, 0, 2)
	var fill := _style(color, Color.TRANSPARENT, 0, 2)
	for style: StyleBoxFlat in [background, fill]:
		style.content_margin_left = 0
		style.content_margin_right = 0
		style.content_margin_top = 0
		style.content_margin_bottom = 0
	bar.add_theme_stylebox_override("background", background)
	bar.add_theme_stylebox_override("fill", fill)
	return bar


func _panel_content(panel: PanelContainer, inset: int) -> VBoxContainer:
	var margin := MarginContainer.new()
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for edge in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_" + edge, inset)
	panel.add_child(margin)
	var box := VBoxContainer.new()
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_child(box)
	return box


func _add_stripe(parent: VBoxContainer) -> void:
	var stripe := HBoxContainer.new()
	stripe.custom_minimum_size.y = 3
	stripe.add_theme_constant_override("separation", 2)
	stripe.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for color: Color in [RED, GOLD, TEAL]:
		var part := ColorRect.new()
		part.color = color
		part.custom_minimum_size.y = 3
		part.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		part.mouse_filter = Control.MOUSE_FILTER_IGNORE
		stripe.add_child(part)
	parent.add_child(stripe)


func _style(background: Color, border: Color = Color.TRANSPARENT, width: int = 0, radius: int = 7) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = background
	style.border_color = border
	style.set_border_width_all(width)
	style.set_corner_radius_all(radius)
	style.content_margin_left = 9
	style.content_margin_right = 9
	style.content_margin_top = 7
	style.content_margin_bottom = 7
	return style


func _make_theme() -> Theme:
	var result := Theme.new()
	result.default_font_size = 14
	result.set_color("font_color", "Label", CREAM)
	result.set_stylebox("panel", "PanelContainer", _style(PANEL, Color(0.32, 0.52, 0.46, 0.45), 1, 8))
	result.set_color("font_color", "Button", CREAM)
	result.set_color("font_hover_color", "Button", Color.WHITE)
	result.set_color("font_pressed_color", "Button", Color.WHITE)
	result.set_color("font_disabled_color", "Button", Color("617970"))
	result.set_stylebox("normal", "Button", _style(DARK, Color("35504b"), 1, 4))
	result.set_stylebox("hover", "Button", _style(Color("2b5049"), TEAL, 1, 4))
	result.set_stylebox("pressed", "Button", _style(Color("347267"), TEAL, 1, 4))
	result.set_stylebox("disabled", "Button", _style(Color("132422"), Color("263a35"), 1, 4))
	result.set_stylebox("focus", "Button", _style(Color.TRANSPARENT, GOLD, 1, 4))
	result.set_stylebox("panel", "TooltipPanel", _style(Color("203c36"), TEAL, 1, 4))
	result.set_color("font_color", "TooltipLabel", CREAM)
	return result
