# IF Walkthrough Dataset

## Dataset Organization
* ```data.json```: The main dataset file containing a list of examples.
* ```saves/```: Directory containing pickled save files, one per example.
* ```example_usage.py```: Contains example implementations of the tasks outlined below.
* ```build_dataset.py```: Code used to create the dataset.

## Example:
```json
{
    "rom": "zork1",
    "walkthrough_act": "Open window",
    "walkthrough_diff": "((), ((235, 11),), ())",
    "obs": "Behind House\nYou are behind the white house. A path leads into the forest to the east. In one corner of the house there is a small window which is slightly ajar.\n\n",
    "loc_desc": "Behind House\nYou are behind the white house. A path leads into the forest to the east. In one corner of the house there is a small window which is slightly ajar.\n\n",
    "inv_desc": "You are carrying:\n  A jewel-encrusted egg\n\n",
    "inv_objs": {
      "The jewel encrusted egg is closed.": [
        "egg"
      ]
    },
    "location": {
      "name": "Behind House",
      "num": 79
    },
    "surrounding_objs": {
      "The window is slightly ajar, but not enough to allow entry.": [
        "small",
        "window"
      ],
      "The house is a beautiful colonial house which is painted white. It is clear that the owners must have been extremely wealthy.": [
        "white",
        "house"
      ],
      "There's nothing special about the way.": [
        "path"
      ]
    },
    "state": "saves/f461488f-3085-4f5a-ac2f-bd424561e8c6.pkl",
    "valid_acts": {
      "((), ((235, 11),), ())": "open small",
      "(((86, 4),), (), ())": "take on egg",
      "(((87, 79),), (), ())": "put down egg",
      "(((4, 80),), ((80, 3),), ())": "south",
      "(((87, 79), (86, 79)), (), ())": "throw egg at small",
      "(((4, 81),), (), ())": "north",
      "(((4, 74),), ((74, 3),), ())": "east"
    },
    "prev_graph": [
      [
        "you",
        "have",
        "jewel-encrusted egg"
      ],
      [
        "North House",
        "south",
        "Forest Path"
      ],
      [
        "you",
        "in",
        "North House"
      ],
      [
        "golden clockwork canary",
        "in",
        "jewel-encrusted egg"
      ]
    ],
    "graph": [
      [
        "you",
        "have",
        "jewel-encrusted egg"
      ],
      [
        "you",
        "in",
        "Behind House"
      ],
      [
        "Behind House",
        "east",
        "North House"
      ],
      [
        "golden clockwork canary",
        "in",
        "jewel-encrusted egg"
      ]
    ],
    "graph_diff": [
      [
        "you",
        "have",
        "jewel-encrusted egg"
      ],
      [
        "you",
        "in",
        "Behind House"
      ],
      [
        "Behind House",
        "east",
        "North House"
      ],
      [
        "golden clockwork canary",
        "in",
        "jewel-encrusted egg"
      ]
    ],
    "score": 5
  }
```

## Fields
Each example defines the following fields:
* **rom**: Name of the game that generated this example.
* **obs**: Narrative text returned by the game as a result of the last action.
* **loc_desc**: Text returned by *look* command from current location.
* **inv_desc**: Text returned by *inventory* command from current step.
* **inv_objs**: Dictionary of ```{obj_description : [obj_names]}``` containing detected objects in the player's inventory.
* **surrounding_objs**: Dictionary of ```{obj_description : [obj_names]}``` containing detected objects in the player's immediate surroundings.
* **score**: Current game score at this step.
* **location**: Name and number for the world-object corresponding to the player's current location.
* **state**: Path to pickle file containing saved game state.
* **walkthrough_act**: Action taken by the walkthrough from the current state.
* **walkthrough_diff**: ```world_diff``` corresponding to taking the walkthrough action.
* **valid_acts**: list of ```world_diff : action_str```. The important part here is the world_diff since there are many action strings that can result in the same world diff.
* **prev_graph**: list of lists of ```subject, relation, object``` of knowledge graph for previous step
* **graph**: list of lists of ```subject, relation, object``` of knowledge graph for current step
* **graph_diff**: set difference between previous and current knowledge graphs

## Possible Tasks (a partial list...)
* **Predict walkthrough actions**: Predict the ```walkthrough_act``` for a given example.
* **Predict examinable objects**: Given the observation/inventory description, attempt to predict the set of objects that are present. Ground truth given by ```surrounding_objs``` and ```inv_objs``` respectively.
* **Predict valid actions**: Given a model can we predict some/all of the valid actions? Ground truth given by world-diffs in ```valid_acts```.