import ifcopenshell
import ifcopenshell.util.element
import csv

def get_added_elements(old_ifc, new_ifc):
    old_elements = {el.GlobalId for el in old_ifc.by_type("IfcElement")}
    new_elements = {el.GlobalId for el in new_ifc.by_type("IfcElement")}
    
    added_elements = new_elements - old_elements
    return [new_ifc.by_guid(gid) for gid in added_elements]

def get_deleted_elements(old_ifc, new_ifc):
    old_elements = {el.GlobalId for el in old_ifc.by_type("IfcElement")}
    new_elements = {el.GlobalId for el in new_ifc.by_type("IfcElement")}
    deleted_elements = old_elements - new_elements
    return [old_ifc.by_guid(gid) for gid in deleted_elements]


def get_reference_value(element):
    property_sets = ifcopenshell.util.element.get_psets(element)
    return property_sets.get("Pset_BuildingElementProxyCommon", {}).get("Reference", None)

def get_modified_elements(old_ifc, new_ifc):
    modified_elements = []
    old_elements = {el.GlobalId: el for el in old_ifc.by_type("IfcElement")}
    new_elements = {el.GlobalId: el for el in new_ifc.by_type("IfcElement")}
    for gid in old_elements.keys() & new_elements.keys():
        old_el = old_elements[gid]
        new_el = new_elements[gid]
        old_reference = get_reference_value(old_el)
        new_reference = get_reference_value(new_el)
        if old_reference != new_reference:
            modified_elements.append((new_el, old_reference, new_reference)) 
    return modified_elements


def save_ifc_changes_to_csv(added_elements, deleted_elements, modified_elements, filename="ifc_changes.csv"):
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["GlobalId", "ChangeType", "OldReference", "NewReference"])
        for gid in added_elements:
            writer.writerow([gid, "Added", "", ""])
        for gid in deleted_elements:
            writer.writerow([gid, "Deleted", "", ""])
        for el, old_ref, new_ref in modified_elements:
            writer.writerow([el.GlobalId, "Modified", old_ref, new_ref])
    print(f"Change log saved as {filename}")



