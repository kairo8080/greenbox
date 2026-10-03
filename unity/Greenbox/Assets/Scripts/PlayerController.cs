using System;
using System.Collections.Generic;
using UnityEngine;

namespace Greenbox
{
    [RequireComponent(typeof(CharacterController))]
    public sealed class PlayerController : MonoBehaviour
    {
        public GrowGameController Game;
        public Camera ViewCamera;
        public Transform Visual;
        public bool Walking { get; private set; }
        public float speed = 2.1f;

        private CharacterController capsule;
        private readonly List<Vector3> route = new List<Vector3>();
        private readonly Dictionary<string, Transform> joints = new Dictionary<string, Transform>();
        private readonly Dictionary<string, Quaternion> restRotations = new Dictionary<string, Quaternion>();
        private Action arrival;
        private Transform handCan;
        private float verticalSpeed, progressTimer, gaitClock;
        private Vector3 progressPosition;

        private void Awake() { capsule = GetComponent<CharacterController>(); }

        public void InitializeJoints(Transform canSource)
        {
            foreach (string name in new[] { "torso", "head", "arm_left", "arm_right", "leg_left", "leg_right" })
            {
                Transform joint = GrowGameController.FindDeep(Visual, name);
                if (joint == null) continue;
                joints[name] = joint;
                restRotations[name] = joint.localRotation;
            }
            Transform arm;
            if (canSource != null && joints.TryGetValue("arm_right", out arm))
            {
                handCan = Instantiate(canSource.gameObject, arm, false).transform;
                handCan.name = "Held Watering Can";
                handCan.localPosition = new Vector3(0, -.40f, .13f);
                handCan.localRotation = Quaternion.Euler(0, Game.mirrorX ? 90 : -90, 0);
                handCan.localScale = Vector3.one * .45f;
                handCan.gameObject.SetActive(false);
            }
        }

        public void FollowPath(List<Vector3> points, Action onArrival)
        {
            route.Clear();
            route.AddRange(points);
            arrival = onArrival;
            Walking = route.Count > 0;
            progressTimer = 0;
            progressPosition = transform.position;
        }
        public void CancelWalk()
        {
            route.Clear();
            arrival = null;
            Walking = false;
            progressTimer = 0;
            if (Game != null) Game.CancelPendingCare();
        }
        public void Face(Vector3 point)
        {
            if (Visual == null) return;
            Vector3 direction = point - transform.position;
            direction.y = 0;
            if (direction.sqrMagnitude > .001f) Visual.rotation = Quaternion.LookRotation(direction.normalized, Vector3.up);
        }

        private void Update()
        {
            if (Game == null || ViewCamera == null || Game.Paused) return;
            float delta = Time.deltaTime;
            Vector2 input = Vector2.zero;
            if (Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow)) input.y += 1;
            if (Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow)) input.y -= 1;
            if (Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow)) input.x -= 1;
            if (Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow)) input.x += 1;
            Vector3 movement = Vector3.zero;
            if (input.sqrMagnitude > .01f)
            {
                CancelWalk();
                Vector3 right = ViewCamera.transform.right;
                Vector3 forward = ViewCamera.transform.forward;
                right.y = forward.y = 0;
                movement = (right.normalized * input.x + forward.normalized * input.y).normalized;
            }
            else if (Walking && Game.CareTimer <= 0)
            {
                while (route.Count > 0 && GrowGameController.HorizontalDistance(transform.position, route[0]) < .11f) route.RemoveAt(0);
                if (route.Count > 0)
                {
                    movement = route[0] - transform.position;
                    movement.y = 0;
                    movement.Normalize();
                }
                else
                {
                    Walking = false;
                    Action callback = arrival;
                    arrival = null;
                    if (callback != null) callback();
                }
            }
            if (Game.CareTimer > 0) movement = Vector3.zero;
            verticalSpeed = capsule.isGrounded ? -1.5f : verticalSpeed - 9.8f * delta;
            capsule.Move((movement * speed + Vector3.up * verticalSpeed) * delta);
            Vector3 canonical = Game.Canonical(transform.position);
            canonical.x = Mathf.Clamp(canonical.x, .35f, 6.9f);
            canonical.z = Mathf.Clamp(canonical.z, -5.7f, -.3f);
            transform.position = Game.Map(canonical);
            if (Walking)
            {
                progressTimer += delta;
                if (progressTimer > 1.5f)
                {
                    if (GrowGameController.HorizontalDistance(transform.position, progressPosition) < .08f)
                    {
                        CancelWalk();
                        Game.Hud.ShowMessage("Path blocked. Use WASD to step around the obstacle.", false);
                    }
                    progressPosition = transform.position;
                    progressTimer = 0;
                }
            }
            bool moving = movement.sqrMagnitude > .01f;
            if (Visual != null && moving)
            {
                Visual.rotation = Quaternion.Slerp(Visual.rotation, Quaternion.LookRotation(movement, Vector3.up), Mathf.Min(1, delta * 12));
                Visual.localPosition = Vector3.up * (Mathf.Abs(Mathf.Sin(gaitClock * 10)) * .025f);
            }
            else if (Visual != null) Visual.localPosition = Vector3.zero;
            gaitClock += delta;
            AnimateJoints(delta, moving);
        }

        private void AnimateJoints(float delta, bool moving)
        {
            float swing = moving ? Mathf.Sin(gaitClock * 10) * 34 : 0;
            foreach (string name in new[] { "arm_left", "arm_right", "leg_left", "leg_right" })
            {
                Transform joint;
                if (!joints.TryGetValue(name, out joint)) continue;
                float angle = (name == "arm_left" || name == "leg_right") ? swing : -swing;
                if (Game.CareTimer > 0)
                {
                    if (name == "arm_right") angle = -52 + Mathf.Sin(Game.CareTimer * 9) * 7;
                    if (name == "arm_left") angle = -26;
                }
                joint.localRotation = Quaternion.Slerp(joint.localRotation, restRotations[name] * Quaternion.Euler(angle, 0, 0), Mathf.Min(1, delta * 12));
            }
            if (handCan != null) handCan.gameObject.SetActive(Game.CareTimer > 0 && Game.CareAction == "water");
        }
    }
}
