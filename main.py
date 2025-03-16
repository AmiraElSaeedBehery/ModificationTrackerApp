import ifcopenshell
import ifcopenshell.util
import ifcopenshell.util.element
import ifcopenshell.geom
from MyFunctions import *


old_ifc_path = "HA_oldVersion.ifc"
new_ifc_path = "HA_newVersion.ifc"

old_ifc = ifcopenshell.open(old_ifc_path)
new_ifc = ifcopenshell.open(new_ifc_path)


added_elements = get_added_elements(old_ifc, new_ifc)
deleted_elements = get_deleted_elements(old_ifc, new_ifc)
modified_elements = get_modified_elements(old_ifc, new_ifc)

print(f"Added Elements: {len(added_elements)}")
print(f"Deleted Elements: {len(deleted_elements)}")
print(f"Modified Elements: {len(modified_elements)}")

save_ifc_changes_to_csv(added_elements, deleted_elements, modified_elements)

for e in added_elements:
    print(f"Added: {e.GlobalId}")