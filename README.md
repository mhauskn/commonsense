# IF Walkthrough Dataset

## Dataset Organization
* ```data.json```: The main dataset file containing a list of examples.
* ```saves/```: Directory containing pickled save files, one per example.
* ```example_usage.py```: Contains example implementations of the tasks outlined below.
* ```build_dataset.py```: Code used to create the dataset.

## Example:
```json
{
    "surrounding_objs": {
        "There's nothing special about the stairs.": [
            "staircase"
        ],
        "There's nothing special about the wooden ladder.": [
            "ladder",
            "wooden",
            "rickety"
        ]
    },
    "walkthrough_act": "U",
    "inv_objs": {
        "The lamp is on.": [
            "light",
            "brass",
            "lantern"
        ],
        "There's nothing special about the clove of garlic.": [
            "clove",
            "garlic"
        ]
    },
    "rom": "zork1",
    "score": 294,
    "location": {
        "name": "Ladder Top",
        "num": 21
    },
    "inv_desc": "You are carrying:\n  A clove of garlic\n  A brass lantern (providing light)\n\n",
    "state": "saves/29644339-eddc-412f-a33f-3c6d3b09a7d1.pkl",
    "obs_desc": "Ladder Top\nThis is a very small room. In the corner is a rickety wooden ladder, leading downward. It might be safe to descend. There is also a staircase leading upward.\n\n",
    "valid_acts": {
        "(((189, 21),), (), ())": "put down clove",
        "(((164, 21),), (), ())": "put down light",
        "(((4, 20),), (), ())": "down",
        "((), (), ((164, 20),))": "put out light",
        "(((4, 16),), (), ())": "up",
        "(((210, 21),), (), ())": "throw clove at light"
    },
    "walkthrough_diff": "(((4, 16),), (), ())"
},
```

## Fields
Each example defines the following fields:
* **rom**: Name of the game that generated this example.
* **obs_desc**: Text returned by *look* command from current location.
* **inv_desc**: Text returned by *inventory* command from current step.
* **inv_objs**: Dictionary of ```{obj_description : [obj_names]}``` containing detected objects in the player's inventory.
* **surrounding_objs**: Dictionary of ```{obj_description : [obj_names]}``` containing detected objects in the player's immediate surroundings.
* **score**: Current game score at this step.
* **location**: Name and number for the world-object corresponding to the player's current location.
* **state**: Path to pickle file containing saved game state.
* **walkthrough_act**: Action taken by the walkthrough from the current state.
* **walkthrough_diff**: ```world_diff``` corresponding to taking the walkthrough action.
* **valid_acts**: list of ```world_diff : action_str```. The important part here is the world_diff since there are many action strings that can result in the same world diff.

## Possible Tasks (a partial list...)
* **Predict walkthrough actions**: Predict the ```walkthrough_act``` for a given example.
* **Predict examinable objects**: Given the observation/inventory description, attempt to predict the set of objects that are present. Ground truth given by ```surrounding_objs``` and ```inv_objs``` respectively.
* **Predict valid actions**: Given a model can we predict some/all of the valid actions? Ground truth given by world-diffs in ```valid_acts```.