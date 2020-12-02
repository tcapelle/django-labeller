def _jupyter_nbextension_paths():
    return [{
        'section': 'notebook',
        'src': 'static',
        'dest': 'fastlabel',
        'require': 'fastlabel/labelling_tool/extension'
    }]

from .flask_labeller import run_app