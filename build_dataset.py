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
from jericho import defines
from glob import glob


MOVE_ACTIONS = 'north/south/west/east/northwest/southwest/northeast/southeast/up/down/enter/exit'.split('/')

with open('symtables/readable_tables.txt', 'r') as f:
    readable = [str(a).strip() for a in f]

attribues = {}
for gn in readable:
    attribues[gn] = {}

    with open('symtables/' + gn + '.out', 'r') as f:
        try:
            for line in f:
                if "attribute" in line.lower():
                    split = line.split('\t')
                    if len(split) < 2:
                        continue
                    idx, attr = int(split[0].split(' ')[1]), split[1]
                    attribues[gn][idx] = attr
        except UnicodeDecodeError:
            print("Decode error:", gn)
            continue


def tree_to_triple(cur_loc, you, sub_tree, prev_act, prev_loc, game_name):
    triples = set()

    triples.add(('you', 'in', cur_loc.name))
    if prev_act.lower() in MOVE_ACTIONS:
        triples.add((cur_loc.name, prev_act.replace(' ', '_'), prev_loc.name))

    if prev_act.lower() in defines.ABBRV_DICT.keys():
        prev_act = defines.ABBRV_DICT[prev_act.lower()]
        triples.add((cur_loc.name, prev_act.replace(' ', '_'), prev_loc.name))

    for obj in sub_tree:
        if obj.num == you.num:
            continue
        elif obj.parent == you.num:
            triples.add(('you', 'have', obj.name))
        elif obj.parent == cur_loc.num:
            triples.add((obj.name, 'in', cur_loc.name))
        else:
            cur_parent = [a.name for a in sub_tree if a.num == obj.parent]

            triples.add((obj.name, 'in', cur_parent[0]))

        if game_name in readable:
            cur_attrs = attribues[game_name]
            obj_attrs = obj.attr
            for oatr in obj_attrs:
                if oatr in cur_attrs.keys():
                    triples.add((obj.name, 'is', cur_attrs[oatr].lower()))

    return list(triples)


def graph_diff(graph1, graph2):
    graph1 = set(graph1)
    graph2 = set(graph2)
    return list((graph2 - graph1).union(graph1.intersection(graph2)))


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


def build_dataset(rom):
    print(rom)
    bindings = load_bindings(rom)
    env = FrotzEnv(rom, seed=bindings['seed'])
    walkthrough = bindings['walkthrough'].split('/')
    act_gen = TemplateActionGenerator(bindings)

    data = []
    prev_triples = []
    visited = set()

    for act in tqdm(walkthrough):
        score = env.get_score()
        state = env.get_state()
        fname = pjoin('saves', str(uuid.uuid4()) + '.pkl')
        pickle.dump(state, open(fname,'wb'))

        obs_desc = env.step('look')[0]
        env.set_state(state)
        inv_desc = env.step('inventory')[0]
        env.set_state(state)

        location = env.get_player_location()
        location_json = {'name':location.name, 'num': location.num}

        surrounding_objs, inv_objs = identify_interactive_objects(env, obs_desc, inv_desc, state)
        # inv_objs, surrounding_objs = get_objs(env)

        interactive_objs = [obj[0] for obj in env.identify_interactive_objects(use_object_tree=True)]
        candidate_actions = act_gen.generate_actions(interactive_objs)
        diff2acts = find_valid_actions(env, state, candidate_actions)

        valid_actions = diff2acts.values()
        copy_env = env.copy()

        for v in valid_actions:
            vobs, vrew, vdone, vinfo = copy_env.step(v)

            vscore = copy_env.get_score()
            vstate = copy_env.get_state()
            vfname = pjoin('saves', str(uuid.uuid4()) + '.pkl')
            pickle.dump(state, open(vfname, 'wb'))

            vobs_desc = copy_env.step('look')[0]
            copy_env.set_state(vstate)
            vinv_desc = copy_env.step('inventory')[0]
            copy_env.set_state(state)

            vlocation = copy_env.get_player_location()
            vlocation_json = {'name': vlocation.name, 'num': vlocation.num}

            vsurrounding_objs, vinv_objs = identify_interactive_objects(copy_env, vobs_desc, vinv_desc, vstate)

            vinteractive_objs = [obj[0] for obj in copy_env.identify_interactive_objects(use_object_tree=True)]
            vcandidate_actions = act_gen.generate_actions(vinteractive_objs)
            vdiff2acts = find_valid_actions(copy_env, vstate, vcandidate_actions)

            vsurrounding = utl.get_subtree(copy_env.get_player_location().child, copy_env.get_world_objects())
            vtriples = tree_to_triple(copy_env.get_player_location(), copy_env.get_player_object(), vsurrounding, v, vlocation, rom)
            vdiff = str(copy_env._get_world_diff())
            vtriple_diff = graph_diff(prev_triples, vtriples)

            if copy_env.get_world_state_hash() not in visited:
                """print({
                    'rom': bindings['name'],
                    'walkthrough_act': v,
                    'walkthrough_diff': vdiff,
                    'obs_nar' : vobs,
                    'obs_desc': vobs_desc,
                    'inv_desc': vinv_desc,
                    'inv_objs': vinv_objs,
                    'location': vlocation_json,
                    'surrounding_objs': vsurrounding_objs,
                    'state': vfname,
                    'valid_acts': vdiff2acts,
                    'prev_graph': prev_triples,
                    'graph': vtriples,
                    'graph_diff': vtriple_diff,
                    'score': vscore
                })"""
                data.append({
                    'rom': bindings['name'],
                    'walkthrough_act': v,
                    'walkthrough_diff': vdiff,
                    'obs_nar' : vobs,
                    'obs_desc': vobs_desc,
                    'inv_desc': vinv_desc,
                    'inv_objs': vinv_objs,
                    'location': vlocation_json,
                    'surrounding_objs': vsurrounding_objs,
                    'state': vfname,
                    'valid_acts': vdiff2acts,
                    'prev_graph': prev_triples,
                    'graph': vtriples,
                    'graph_diff': vtriple_diff,
                    'score': vscore
                })
            visited.add(copy_env.get_world_state_hash())
            copy_env.set_state(vstate)
        copy_env.close()

        obs, rew, done, info = env.step(act)
        surrounding = utl.get_subtree(env.get_player_location().child, env.get_world_objects())
        triples = tree_to_triple(env.get_player_location(), env.get_player_object(), surrounding, act, location, rom)
        diff = str(env._get_world_diff())
        triple_diff = graph_diff(prev_triples, triples)

        if env.get_world_state_hash() not in visited:
            """print(
                {
                'rom' : bindings['name'],
                'walkthrough_act' : act,
                'walkthrough_diff' : diff,
                'obs_nar' : obs,
                'obs_desc' : obs_desc,
                'inv_desc' : inv_desc,
                'inv_objs' : inv_objs,
                'location' : location_json,
                'surrounding_objs' : surrounding_objs,
                'state' : fname,
                'valid_acts' : diff2acts,
                'prev_graph': prev_triples,
                'graph': triples,
                'graph_diff': triple_diff,
                'score' : score
            })"""
            data.append({
                'rom' : bindings['name'],
                'walkthrough_act' : act,
                'walkthrough_diff' : diff,
                'obs_nar' : obs,
                'obs_desc' : obs_desc,
                'inv_desc' : inv_desc,
                'inv_objs' : inv_objs,
                'location' : location_json,
                'surrounding_objs' : surrounding_objs,
                'state' : fname,
                'valid_acts' : diff2acts,
                'prev_graph': prev_triples,
                'graph': triples,
                'graph_diff': triple_diff,
                'score' : score
            })
        visited.add(env.get_world_state_hash())

        prev_triples = triples
        with open(rom.split('/')[-1].split('.')[0] + '_data.json', 'w') as fi:
            json.dump(data, fi)
    print("Size:", str(len(data)))
    env.close()

    return data


if __name__ == '__main__':
    # data = build_dataset('roms/zork1.z5')
    data = []

    games = glob('roms/*')
    for game in games:
        data += build_dataset(game)

    with open('data.json', 'w') as f:
        json.dump(data, f)

    print("Total size:", len(data))
