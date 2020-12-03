import json
from .labelling_tool import (
    LabelClass, 
    LabelClassGroup, 
    AnnoControlCheckbox, 
    AnnoControlRadioButtons, 
    AnnoControlPopupMenu)


__all__ = ['get_color_schemes', 'get_labels', 'get_anno_controls']

SECTIONS = {"colours": 'Colour Schemes', "labels":"Label Classes", "controls":"Annotation Controls"}

def get_color_schemes(cfg, section=SECTIONS["colours"]):
    colour_schemes = [
    dict(name=key, human_name=value) for key, value in cfg[section].items()
    ]
    return colour_schemes

def get_labels(cfg, section=SECTIONS["labels"]):
    "Extract labels from json"
    label_classes = []
    for group_name, group_props in cfg[section].items():
        classes = []
        for label_class, values in group_props.items():
            classes.append(LabelClass(label_class, values['name'], values['colours']))
        label_classes.append(LabelClassGroup(group_name, classes))
    return label_classes

def _add_control(name, d):
    "Check control type and setup corresnponding interface control"
    if name.lower() == 'checkbox':
        return AnnoControlCheckbox(d['id'], d['name'])
    elif name.lower() == 'radiobuttons':
        return AnnoControlRadioButtons(
            d['id'], 
            d["name"], 
            choices=[AnnoControlPopupMenu.choice(**choice) for choice in d["choices"]]
        )
    elif name.lower() == 'popup':
        groups = []
        for group in d['groups']:
            groups.append(
                AnnoControlPopupMenu.group(
                    label_text=group['label_text'], 
                    choices=[AnnoControlPopupMenu.choice(**c) for c in group['choices']]
                )
            )
        return AnnoControlPopupMenu(d['id'], d['name'], groups=groups)  

def get_anno_controls(cfg, section=SECTIONS["controls"]):
    "Get annotation controls"
    anno_controls = []
    for control_name, params in cfg["Annotation Controls"].items():
        anno_controls.append(_add_control(control_name, params))
    return anno_controls