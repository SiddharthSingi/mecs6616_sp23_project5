import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
from geometry import polar2cartesian


class ArmEnv(gym.Env):
    def __init__(self, arm):
        self.arm = arm  # DONOT modify
        self.goal = None  # Use for computing observation
        self.observation_space = None  # You will need to set this appropriately
        self.action_space = None  # You will need to set this appropriately
        self.np_random = np.random

        self.step_duration = 0.01
        self.episode_length = 200
        self.num_links = self.arm.dynamics.num_links
        self.timestep = self.arm.dynamics.dt
        self.observation_space = spaces.Box(-np.inf, np.inf, shape=(2 * self.num_links + 4,))
        self.action_space = spaces.Box(-1, 1, shape=(self.num_links,))
        self.num_steps = 0

    # We will be calling this function to set the goal for your arm during testing.
    def set_goal(self, goal):
        self.goal = goal
        self.arm.goal = goal

    def step(self, action):
        max_torque = 4
        action = np.clip(action * max_torque, -max_torque, max_torque)
        self.num_steps += 1
        self.arm.set_action(action)
        for _ in range(int(self.step_duration / self.timestep)):
            self.arm.advance()

        new_state = self.arm.get_state()
        # Compute reward
        pos_ee = self.arm.dynamics.compute_fk(new_state)
        dist = np.linalg.norm(pos_ee - self.goal)
        reward = -dist ** 2

        obs = self.get_obs()

        done = False
        if self.num_steps >= self.episode_length:
            done = True

        # required for terminal logging, mention this in project description
        info = dict(reward=reward, done=done)

        return obs, reward, done, info

    def reset(self, goal=None):
        self.num_steps = 0

        # reset arm
        self.arm.reset()

        # random goal
        radius_max = 2.0
        radius_min = 1.5
        angle_max = 0.5
        angle_min = -0.5
        radius = (radius_max - radius_min) * self.np_random.random_sample() + radius_min
        angle = (angle_max - angle_min) * self.np_random.random_sample() + angle_min
        angle -= np.pi / 2
        goal = polar2cartesian(radius, angle)
        self.set_goal(goal)

        return self.get_obs()

    def get_obs(self):
        state = self.arm.get_state()
        pos_ee = self.arm.dynamics.compute_fk(state)
        obs = np.vstack([self.arm.get_state(), pos_ee, self.goal]).reshape(-1)
        return obs

    # For repeatable stochasticity
    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]
