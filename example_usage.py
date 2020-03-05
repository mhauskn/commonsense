import sys
from jericho import *
from jericho.template_action_generator import TemplateActionGenerator
from tqdm import tqdm
import json
import pickle
import uuid
import os
from os.path import join as pjoin
from jericho import util as utl
from random import choice


def load_dataset(fname='data.json'):
    with open(fname, 'r') as f:
        data = json.load(f)
    return data


def predict_walkthrough_actions():
    """ Given the observation, predict the next action from the walkthrough. """
    action_predictor = lambda obs: choice(['n','s','e','w'])

    rom = '/home/matthew/workspace/text_agents/roms/zork1.z5'
    bindings = load_bindings(rom)
    env = FrotzEnv(rom, seed=bindings['seed'])

    data = load_dataset()
    correct = 0
    for example in data:
        state = pickle.load(open(example['state'],'rb'))
        env.set_state(state)
        gold_diff = example['walkthrough_diff']
        action_prediction = action_predictor(example['obs'])
        env.step(action_prediction)
        actual_diff = str(env._get_world_diff())
        if actual_diff == gold_diff:
            correct += 1
    print('Correctly predicted {} out of {} walkthrough actions'.format(correct, len(data)))


def predict_examinable_objects():
    """ Given an observation, predict which objects are examinable.

        Note that it's possible to do the same task for predicting inventory
        objects from the inv_desc, and it should be much easier.
    """
    obj_identifier = lambda obs: [choice(obs.split())] # Dumb object identifier

    rom = '/home/matthew/workspace/text_agents/roms/zork1.z5'
    bindings = load_bindings(rom)
    env = FrotzEnv(rom, seed=bindings['seed'])

    data = load_dataset()

    total_precision, total_recall = 0, 0
    for example in data:
        state = pickle.load(open(example['state'],'rb'))
        env.set_state(state)

        # Get description by examining each predicted object
        predicted_objects = obj_identifier(example['obs'])
        pred_obj_descriptions = []
        for predicted_obj in predicted_objects:
            obj_desc, _, _, _ = env.step('examine ' + predicted_obj)
            pred_obj_descriptions.append(utl.clean(obj_desc))
            env.set_state(state)

        gt_obj_descriptions = example['surrounding_objs'].keys()

        if len(gt_obj_descriptions) <= 0:
            continue

        # Computer recall over GT predictions
        correct, total = 0, 0
        for gt_obj_desc in gt_obj_descriptions:
            total += 1
            if gt_obj_desc in pred_obj_descriptions:
                correct += 1
        recall = correct / total
        total_recall += recall

        # Compute precision of predictions
        correct, total = 0, 0
        for pred_obj_desc in pred_obj_descriptions:
            total += 1
            if pred_obj_desc in gt_obj_descriptions:
                correct += 1
        precision = correct / total
        total_precision += precision

    print('Average Precision {} and Recall {} for predicting observed objects.'.format(total_precision/len(data), total_recall/len(data)))


def predict_valid_actions():
    """ Given the observation (and inventory?), predict the valid actions. """
    valid_action_predictor = lambda obs: ['take ' + choice(obs.split())] # Dumb action predictor

    rom = '/home/matthew/workspace/text_agents/roms/zork1.z5'
    bindings = load_bindings(rom)
    env = FrotzEnv(rom, seed=bindings['seed'])

    data = load_dataset()

    total_precision, total_recall = 0, 0
    for example in data:
        state = pickle.load(open(example['state'],'rb'))
        env.set_state(state)

        # Get description by examining each predicted object
        predicted_actions = valid_action_predictor(example['obs'])
        pred_action_diffs = []
        for predicted_act in predicted_actions:
            env.step(predicted_act)
            diff = str(env._get_world_diff())
            if diff not in pred_action_diffs:
                pred_action_diffs.append(diff)
            env.set_state(state)

        gt_valid_diffs = example['valid_acts'].keys()

        # Computer recall over GT predictions
        correct, total = 0, 0
        for gt_act_diff in gt_valid_diffs:
            total += 1
            if gt_act_diff in pred_action_diffs:
                correct += 1
        recall = correct / total
        total_recall += recall

        # Compute precision of predictions
        correct, total = 0, 0
        for pred_act_diff in pred_action_diffs:
            total += 1
            if pred_act_diff in gt_valid_diffs:
                correct += 1
        precision = correct / total
        total_precision += precision

    print('Average Precision {} and Recall {} for predicting valid actions.'.format(total_precision/len(data), total_recall/len(data)))



predict_walkthrough_actions()
predict_examinable_objects()
predict_valid_actions()
