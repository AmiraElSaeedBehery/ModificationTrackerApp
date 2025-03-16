import ifcopenshell
import ifcopenshell.util.element
import csv
import os
from collections import Counter
from datetime import datetime
import addUser

def open_ifc_file(file_path):
    """Opens an IFC file and returns the model instance."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return None
    return ifcopenshell.open(file_path)

def get_elements_by_globalid(ifc_file):
    """Returns a dictionary of IFC elements indexed by their GlobalId."""
    return {el.GlobalId: el for el in ifc_file.by_type("IfcElement")}

def get_user_who_modified(element):
    """Retrieve the user who last modified the element."""
    if element.OwnerHistory and element.OwnerHistory.LastModifiedBy:
        return element.OwnerHistory.LastModifiedBy.Name
    return "Unknown"

def get_timestamp_of_change(element):
    """Retrieve the timestamp of when the element was modified."""
    if element.OwnerHistory and element.OwnerHistory.LastModifiedDate:
        return datetime.utcfromtimestamp(element.OwnerHistory.LastModifiedDate).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    return "Unknown"

def get_added_elements(old_ifc, new_ifc):
    """Finds elements present in the new IFC file but not in the old one."""
    old_elements = set(get_elements_by_globalid(old_ifc).keys())
    new_elements = set(get_elements_by_globalid(new_ifc).keys())

    added_elements = new_elements - old_elements
    return [new_ifc.by_guid(gid) for gid in added_elements]

def get_deleted_elements(old_ifc, new_ifc):
    """Finds elements present in the old IFC file but not in the new one."""
    old_elements = set(get_elements_by_globalid(old_ifc).keys())
    new_elements = set(get_elements_by_globalid(new_ifc).keys())

    deleted_elements = old_elements - new_elements
    return [old_ifc.by_guid(gid) for gid in deleted_elements]

def get_reference_value(element):
    """Gets the 'Reference' property value from an element's property sets."""
    property_sets = ifcopenshell.util.element.get_psets(element)
    return property_sets.get("Pset_BuildingElementProxyCommon", {}).get("Reference", None)

def get_modified_elements(old_ifc, new_ifc):
    """Finds elements that exist in both files but have modified properties."""
    modified_elements = []
    old_elements = get_elements_by_globalid(old_ifc)
    new_elements = get_elements_by_globalid(new_ifc)

    common_elements = old_elements.keys() & new_elements.keys()

    for gid in common_elements:
        old_el = old_elements[gid]
        new_el = new_elements[gid]

        old_reference = get_reference_value(old_el)
        new_reference = get_reference_value(new_el)

        if old_reference != new_reference:
            modified_elements.append((new_el, old_reference, new_reference))

    return modified_elements

def save_ifc_changes_to_csv(added, deleted, modified, filename=None):
    """Saves IFC changes to a CSV file with random user tracking and timestamps."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ifc_changes_{timestamp}.csv"

    user_changes = Counter()
    element_modifications = Counter()
    timeline_data = []

    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["GlobalId", "ChangeType", "OldReference", "NewReference", "User", "Timestamp"]
        )

        for el in added:
            user = addUser.assign_random_user()  # Assign random user
            timestamp = addUser.assign_random_timestamp()  # Assign random timestamp
            writer.writerow([el.GlobalId, "Added", "", "", user, timestamp])

            user_changes[user] += 1
            element_modifications[el.GlobalId] += 1
            timeline_data.append((timestamp, "Added"))

        for el in deleted:
            user = addUser.assign_random_user()  # Assign random user
            timestamp = addUser.assign_random_timestamp()  # Assign random timestamp
            writer.writerow([el.GlobalId, "Deleted", "", "", user, timestamp])

            user_changes[user] += 1
            element_modifications[el.GlobalId] += 1
            timeline_data.append((timestamp, "Deleted"))

        for el, old_ref, new_ref in modified:
            user = addUser.assign_random_user()  # Assign random user
            timestamp = addUser.assign_random_timestamp()  # Assign random timestamp
            writer.writerow([el.GlobalId, "Modified", old_ref, new_ref, user, timestamp])

            user_changes[user] += 1
            element_modifications[el.GlobalId] += 1
            timeline_data.append((timestamp, "Modified"))

    print(f"Change log saved as {filename}")
    save_user_change_summary(user_changes)
    save_element_modifications_summary(element_modifications)
    save_timeline_data(timeline_data)

def save_user_change_summary(user_changes, filename="user_changes_summary.csv"):
    """Saves a summary of changes per user."""
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["User", "Number of Changes"])
        for user, count in user_changes.items():
            writer.writerow([user, count])

    print(f"User change summary saved as {filename}")

def save_element_modifications_summary(element_modifications, filename="element_modifications_summary.csv"):
    """Saves a summary of the most frequently modified elements."""
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["GlobalId", "Modification Count"])
        for gid, count in element_modifications.most_common(10):  # Top 10 modified elements
            writer.writerow([gid, count])

    print(f"Element modifications summary saved as {filename}")

def save_timeline_data(timeline_data, filename="modification_timeline.csv"):
    """Saves a timeline of modifications."""
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Change Type"])
        for timestamp, change_type in sorted(timeline_data):
            writer.writerow([timestamp, change_type])

    print(f"Timeline data saved as {filename}")

def main():
    old_ifc_path = "HA_oldVersion.ifc"
    new_ifc_path = "HA_newVersion.ifc"

    old_ifc = open_ifc_file(old_ifc_path)
    new_ifc = open_ifc_file(new_ifc_path)

    if not old_ifc or not new_ifc:
        print("Failed to load IFC files. Exiting...")
        return

    added_elements = get_added_elements(old_ifc, new_ifc)
    deleted_elements = get_deleted_elements(old_ifc, new_ifc)
    modified_elements = get_modified_elements(old_ifc, new_ifc)

    print(f"Added Elements: {len(added_elements)}")
    print(f"Deleted Elements: {len(deleted_elements)}")
    print(f"Modified Elements: {len(modified_elements)}")

    save_ifc_changes_to_csv(added_elements, deleted_elements, modified_elements)

if __name__ == "__main__":
    main()