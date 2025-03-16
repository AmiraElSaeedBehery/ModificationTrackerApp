import ifcopenshell
import ifcopenshell.guid
import shutil


COLORS = {
    "Added": (0.0, 1.0, 0.0),     
    "Deleted": (1.0, 0.0, 0.0), 
    "Modified": (1.0, 1.0, 0.0) 
}

def create_style(ifc_file, color_type):
    """Create a surface style for the given color type"""
    color = COLORS[color_type]
    red, green, blue = color
    
    rgb = ifc_file.create_entity(
        "IfcColourRgb", 
        Name=f"{color_type}Color", 
        Red=red, 
        Green=green, 
        Blue=blue
    )
    
    rendering = ifc_file.create_entity(
        "IfcSurfaceStyleRendering",
        SurfaceColour=rgb,
        Transparency=0.0,
        ReflectanceMethod="NOTDEFINED"
    )
    
    style = ifc_file.create_entity(
        "IfcSurfaceStyle",
        Name=f"{color_type}Style",
        Side="BOTH",
        Styles=[rendering]
    )
    
    return style

def set_element_color(ifc_file, element, color_type):
    try:
        if not element.Representation:
            print(f"⚠️ Element {element.GlobalId} has no representation")
            return False
            
        style = create_style(ifc_file, color_type)
        if hasattr(element.Representation, "Representations"):
            for rep in element.Representation.Representations:
                if hasattr(rep, "Items") and rep.Items:
                    for item in rep.Items:
                        ifc_file.create_entity(
                            "IfcStyledItem",
                            Item=item,
                            Styles=[style]
                        )
        elif hasattr(element.Representation, "Items") and element.Representation.Items:
            for item in element.Representation.Items:
                ifc_file.create_entity(
                    "IfcStyledItem",
                    Item=item,
                    Styles=[style]
                )
                
        return True
    except Exception as e:
        print(f"Error setting color: {e}")
        return False

def add_property_to_element(ifc_file, element, property_name, property_value):
    try:
        simple_property = ifc_file.create_entity(
            "IfcPropertySingleValue",
            Name=property_name,
            NominalValue=ifc_file.create_entity("IfcText", property_value)
        )
        
        property_set = ifc_file.create_entity(
            "IfcPropertySet",
            GlobalId=ifcopenshell.guid.new(),
            Name="ChangeProperties",
            HasProperties=[simple_property]
        )
        
        ifc_file.create_entity(
            "IfcRelDefinesByProperties",
            GlobalId=ifcopenshell.guid.new(),
            RelatedObjects=[element],
            RelatingPropertyDefinition=property_set
        )
        
        return True
    except Exception as e:
        print(f"Error adding property: {e}")
        return False

def process_changes(old_ifc_path, new_ifc_path, output_path):
    try:
        shutil.copy(new_ifc_path, output_path)
        old_ifc = ifcopenshell.open(old_ifc_path)
        new_ifc = ifcopenshell.open(new_ifc_path)
        colored_ifc = ifcopenshell.open(output_path)
        old_elements = {e.GlobalId: e for e in old_ifc.by_type("IfcProduct") if hasattr(e, "GlobalId")}
        new_elements = {e.GlobalId: e for e in new_ifc.by_type("IfcProduct") if hasattr(e, "GlobalId")}
        added_guids = set(new_elements.keys()) - set(old_elements.keys())
        deleted_guids = set(old_elements.keys()) - set(new_elements.keys())
        common_guids = set(old_elements.keys()) & set(new_elements.keys())
        modified_guids = []
        for guid in common_guids:
            old_element = old_elements[guid]
            new_element = new_elements[guid]
            if (hasattr(old_element, "Name") and hasattr(new_element, "Name") and 
                old_element.Name != new_element.Name):
                modified_guids.append(guid)
                
        print(f"Found {len(added_guids)} added, {len(deleted_guids)} deleted, {len(modified_guids)} modified elements")
        added_success = modified_success = deleted_success = 0
        added_fail = modified_fail = deleted_fail = 0
        print("\nColoring added elements...")
        for guid in added_guids:
            element = colored_ifc.by_guid(guid)
            if set_element_color(colored_ifc, element, "Added") and add_property_to_element(colored_ifc, element, "ChangeType", "Added"):
                added_success += 1
                print(f"✅ Colored added element: {guid}")
            else:
                added_fail += 1
                print(f"⚠️ Failed to color added element: {guid}")
        
        print("\nColoring modified elements...")
        for guid in modified_guids:
            element = colored_ifc.by_guid(guid)
            if set_element_color(colored_ifc, element, "Modified") and add_property_to_element(colored_ifc, element, "ChangeType", "Modified"):
                modified_success += 1
                print(f"✅ Colored modified element: {guid}")
            else:
                modified_fail += 1
                print(f"⚠️ Failed to color modified element: {guid}")
        
        print("\nCopying and coloring deleted elements...")
        for guid in deleted_guids:
            old_element = old_elements[guid]
            try:
                copied_element = colored_ifc.add(old_element)
                if set_element_color(colored_ifc, copied_element, "Deleted") and add_property_to_element(colored_ifc, copied_element, "ChangeType", "Deleted"):
                    deleted_success += 1
                    print(f"✅ Copied and colored deleted element: {guid}")
                else:
                    deleted_fail += 1
                    print(f"⚠️ Failed to color deleted element: {guid}")
            except Exception as e:
                deleted_fail += 1
                print(f"⚠️ Failed to copy deleted element: {guid}, Error: {e}")
        
        colored_ifc.write(output_path)
        
        print("\n----- DETAILED REPORT -----")
        print(f"Added elements: {added_success} successful, {added_fail} failed")
        print(f"Modified elements: {modified_success} successful, {modified_fail} failed")
        print(f"Deleted elements: {deleted_success} successful, {deleted_fail} failed")
        print(f"Total: {added_success + modified_success + deleted_success} successful, {added_fail + modified_fail + deleted_fail} failed")
        
        return True
    except Exception as e:
        print(f"Error processing changes: {e}")
        return False
    
if __name__ == "__main__":
    process_changes("HA_oldVersion.ifc", "HA_newVersion.ifc", "colored_model01.ifc")
