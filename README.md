# IF Walkthrough Dataset

## Dataset Organization
* ```data.json```: The main dataset file containing a list of examples.
* ```saves/```: Directory containing pickled save files, one per example.
* ```example_usage.py```: Contains example implementations of the tasks outlined below.
* ```build_dataset.py```: Code used to create the dataset.

## Example:
```json
{
    "score": 345,
    "inv_objs": {
      "The lamp is on.": [
        "brass",
        "lantern",
        "light"                                                                                                                                                                              
      ],
      "There are lots of jewels in there.": [
        "jewels",
        "trunk"
      ],
      "There's nothing special about the screwdriver.": [
        "screwdriver"
      ]
    },
    "inv_desc": "You are carrying:\n  A trunk of jewels\n  A screwdriver\n  A brass lantern (providing light)\n\n",
    "location": {
      "name": "Strange Passage",
      "num": 51
    },
    "walkthrough_diff": "(((4, 193),), (), ())",
    "walkthrough_act": "E",
    "loc_desc": "Strange Passage\nThis is a long passage. To the west is one entrance. On the east there is an old wooden door, with a large opening in it (about cyclops sized).\n\n",
    "rom": "zork1",
    "obs": "Strange Passage\n\n",
    "state": "saves/37eb6dce-d247-486b-8497-9d87a9263e57.pkl",
    "surrounding_objs": {
      "There's nothing special about the way.": [
        "passage",
        "long"
      ],
      "There are lots of jewels in there.": [
        "old"
      ]
    },
    "valid_acts": {
      "((), (), ((164, 20),))": "put out light",
      "(((101, 51),), (), ())": "put down old",
      "(((164, 51),), (), ())": "put down light",
      "(((210, 51),), (), ())": "throw screwdriver at light",
      "(((4, 185),), (), ())": "west",
      "(((4, 193),), (), ())": "east",
      "(((123, 51),), (), ())": "put down screwdriver"
    }
},
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

## Possible Tasks (a partial list...)
* **Predict walkthrough actions**: Predict the ```walkthrough_act``` for a given example.
* **Predict examinable objects**: Given the observation/inventory description, attempt to predict the set of objects that are present. Ground truth given by ```surrounding_objs``` and ```inv_objs``` respectively.
* **Predict valid actions**: Given a model can we predict some/all of the valid actions? Ground truth given by world-diffs in ```valid_acts```.