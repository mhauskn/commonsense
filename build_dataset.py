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


def identify_interactive_objects(env, obs_desc, inv_desc, state):
    surr_objs, inv_objs = set(), set()
    state = env.get_state()

    # Extract objects from observation
    obs = utl.extract_objs(obs_desc)
    surr_objs = surr_objs.union(obs)

    # Extract objects from inventory description
    inv = utl.extract_objs(inv_desc)
    inv_objs = inv_objs.union(inv)

    inv = utl.get_subtree(env.get_player_object().child, env.get_world_objects())
    surrounding = utl.get_subtree(env.get_player_location().child, env.get_world_objects())
    player_obj = env.get_player_object()
    if player_obj in surrounding:
        surrounding.remove(player_obj)
    for i in inv:
        surrounding.remove(i)
    surr_objs = surr_objs.union(' '.join([o.name for o in surrounding]).split())
    inv_objs = inv_objs.union(' '.join([o.name for o in inv]).split())

    # Filter out the objects that aren't in the dictionary
    def filter_words(objs):
        dict_words = [w.word for w in env.get_dictionary()]
        max_word_length = max([len(w) for w in dict_words])
        to_remove = set()
        for obj in objs:
            if obj[:max_word_length] not in dict_words:
                to_remove.add(obj)
        objs.difference_update(to_remove)
        return objs

    surr_objs = filter_words(surr_objs)
    inv_objs = filter_words(inv_objs)

    def filter_examinable(objs):
        desc2obj = {}
        # Filter out objs that aren't examinable
        for obj in objs:
            env.set_state(state)
            ex = utl.clean(env.step('examine ' + obj)[0])
            if utl.recognized(ex):
                if ex in desc2obj:
                    desc2obj[ex].append(obj)
                else:
                    desc2obj[ex] = [obj]
        env.set_state(state)
        return desc2obj

    surr_objs_final = filter_examinable(surr_objs)
    inv_objs_final = filter_examinable(inv_objs)
    return surr_objs_final, inv_objs_final


def get_objs(env):
    inv_objs = utl.get_subtree(env.get_player_object().child, env.get_world_objects())
    surrounding = utl.get_subtree(env.get_player_location().child, env.get_world_objects())
    player_obj = env.get_player_object()
    if player_obj in surrounding:
        surrounding.remove(player_obj)
    for inv_obj in inv_objs:
        surrounding.remove(inv_obj)
    for obj in inv_objs:
        env.step('examine ' + obj.name)
    json_inv_objs = [{'name':obj.name, 'num':obj.num} for obj in inv_objs]
    json_surr_objs = [{'name':obj.name, 'num':obj.num} for obj in surrounding]
    return json_inv_objs, json_surr_objs


def find_valid_actions(env, state, candidate_actions):
    if env.game_over() or env.victory() or env.emulator_halted():
        return []
    diff2acts = {}
    orig_score = env.get_score()
    for act in candidate_actions:
        env.set_state(state)
        if isinstance(act, defines.TemplateAction):
            obs, rew, done, info = env.step(act.action)
        else:
            obs, rew, done, info = env.step(act)
        if env.emulator_halted():
            print('Warning: Environment halted.')
            env.reset()
            continue
        if info['score'] != orig_score or done or env.world_changed():
            # Heuristic to ignore actions with side-effect of taking items
            if '(Taken)' in obs:
                continue
            diff = str(env._get_world_diff())
            if diff in diff2acts:
                if act not in diff2acts[diff]:
                    diff2acts[diff].append(act)
            else:
                diff2acts[diff] = [act]
    valid_acts = {}
    for k,v in diff2acts.items():
        valid_acts[k] = max(v, key=utl.verb_usage_count)
    env.set_state(state)
    return valid_acts


def build_dataset():
    rom = '/home/matthew/workspace/text_agents/roms/zork1.z5'
    bindings = load_bindings(rom)
    env = FrotzEnv(rom, seed=bindings['seed'])
    obs = env.reset()[0]
    walkthrough = bindings['walkthrough'].split('/')
    act_gen = TemplateActionGenerator(bindings)

    data = []
    done = False
    for act in tqdm(walkthrough):
        assert not done
        score = env.get_score()
        state = env.get_state()
        fname = pjoin('saves', str(uuid.uuid4()) + '.pkl')
        pickle.dump(state, open(fname,'wb'))

        loc_desc = env.step('look')[0]
        env.set_state(state)
        inv_desc = env.step('inventory')[0]
        env.set_state(state)

        location = env.get_player_location()
        location_json = {'name':location.name, 'num': location.num}

        surrounding_objs, inv_objs = identify_interactive_objects(env, loc_desc, inv_desc, state)
        # inv_objs, surrounding_objs = get_objs(env)

        interactive_objs = [obj[0] for obj in env.identify_interactive_objects(use_object_tree=True)]
        candidate_actions = act_gen.generate_actions(interactive_objs)
        diff2acts = find_valid_actions(env, state, candidate_actions)

        obs_new, rew, done, info = env.step(act)
        diff = str(env._get_world_diff())
        if not str(diff) in diff2acts:
            print('WalkthroughAct: {} Diff: {} Obs: {}'.format(act, diff, utl.clean(obs_new)))

        data.append({
            'rom'              : bindings['name'],
            'walkthrough_act'  : act,
            'walkthrough_diff' : diff,
            'obs'              : obs,
            'loc_desc'         : loc_desc,
            'inv_desc'         : inv_desc,
            'inv_objs'         : inv_objs,
            'location'         : location_json,
            'surrounding_objs' : surrounding_objs,
            'state'            : fname,
            'valid_acts'       : diff2acts,
            'score'            : score
        })

        obs = obs_new

    with open('data.json', 'w') as f:
        json.dump(data, f)


if __name__ == '__main__':
    build_dataset()
