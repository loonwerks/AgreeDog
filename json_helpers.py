import os
import json
from typing import Tuple, List, Union, Iterator


def load_agree_log(counterexample_dir: str) -> Union[List, None]:
    """
    Load and parse the agree.log JSON file from the given directory.

    Args:
        counterexample_dir: Path to directory containing agree.log
    Returns:
        Parsed JSON data (usually a list of entries), or None if error.
    """
    log_path = os.path.join(counterexample_dir, 'agree.log')
    if not os.path.isfile(log_path):
        raise FileNotFoundError(f"agree.log not found in '{counterexample_dir}'")
    with open(log_path, 'r') as f:
        data = json.load(f)
    return data


def traverse_results(node: Union[dict, list]) -> Iterator[str]:
    """
    Recursively traverse a JSON structure of agree.log entries, yielding every 'result' value.
    """
    if isinstance(node, dict):
        if 'result' in node:
            yield node['result']
        for child in node.get('analyses', []):
            yield from traverse_results(child)
    elif isinstance(node, list):
        for item in node:
            yield from traverse_results(item)


def is_model_valid(data: Union[List, dict]) -> Tuple[bool, List[str]]:
    """
    Determine if the AGREE model is entirely valid.

    Args:
        data: Parsed JSON from agree.log (list or dict)
    Returns:
        Tuple(valid: bool, invalid_results: List[str])
    """
    all_results = list(traverse_results(data))
    invalids = [r for r in all_results if r != 'Valid']
    return (len(invalids) == 0, invalids)
