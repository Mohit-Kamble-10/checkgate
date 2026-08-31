"""Shared frontClassId lookup for Live vs Test record uploads."""
import copy
import json
import logging
import os

FRONT_CLASS_NOT_FOUND_ID = 9


def load_json_file(path, default=None):
    if default is None:
        default = {}
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def lookup_front_class_id(class_name, front_map):
    """Resolve inference class name to frontClassId using the given portal map."""
    if not class_name or class_name in ('Not_Found', ''):
        return FRONT_CLASS_NOT_FOUND_ID
    return front_map.get(class_name, FRONT_CLASS_NOT_FOUND_ID)


def load_front_class_maps(jsons_path, live_upload=False, test_upload=False):
    """
    Load Live and Test frontClassId maps.
    front_class_category_test.json — Test portal (IDs 28–31 for axles).
    front_class_category_live.json — Live portal (IDs 13–16 for axles).
    front_class_category.json — fallback for Test only if _test.json is missing.
    """
    front_map_live = load_json_file(jsons_path + '/front_class_category_live.json')
    front_map_test = load_json_file(jsons_path + '/front_class_category_test.json')
    if not front_map_test:
        front_map_test = load_json_file(jsons_path + '/front_class_category.json')

    if live_upload and not front_map_live:
        logging.warning(
            'front_class_category_live.json missing or empty — Live frontClassId will default to 9'
        )
    if test_upload and not front_map_test:
        logging.warning(
            'front_class_category_test.json missing or empty — Test frontClassId will default to 9'
        )
    return front_map_live, front_map_test


def build_record_payloads(request_base, final_front_class, front_map_live, front_map_test):
    """Build Live and Test record payloads; only frontClassId differs."""
    request_live = copy.deepcopy(request_base)
    request_live['frontClassId'] = lookup_front_class_id(final_front_class, front_map_live)
    request_test = copy.deepcopy(request_base)
    request_test['frontClassId'] = lookup_front_class_id(final_front_class, front_map_test)
    return request_live, request_test


def write_record_request_files(request_path, request_live_path, request_test_path,
                               request_live, request_test):
    """Persist request.json (Test copy) plus per-portal request files."""
    with open(request_path, 'w') as f:
        json.dump(request_test, f)
    with open(request_live_path, 'w') as f:
        json.dump(request_live, f)
    with open(request_test_path, 'w') as f:
        json.dump(request_test, f)
