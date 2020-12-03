# The MIT License (MIT)
#
# Copyright (c) 2015 University of East Anglia, Norwich, UK
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Developed by Geoffrey French in collaboration with Dr. M. Fisher and
# Dr. M. Mackiewicz.

import os
import glob
import click
import json
import uuid
import numpy as np\

from flask import Flask, render_template, request, make_response, send_from_directory
try:
    from flask_socketio import SocketIO, emit as socketio_emit
except ImportError:
    SocketIO = None
    socketio_emit = None

from .labelling_tool import (
    image_descriptor,
    PolygonLabel,
    PersistentLabelledImage,
    ensure_json_object_ids_have_prefix,
    LabelClassGroup)

from .read_cfg import *

def flask_labeller(label_classes, labelled_images, tasks=None, colour_schemes=None, anno_controls=None,
                   config=None, dextr_fn=None, use_reloader=True, debug=True, port=None):


    # Generate image IDs list
    image_ids = [str(i)   for i in range(len(labelled_images))]
    # Generate images table mapping image ID to image so we can get an image by ID
    images_table = {image_id: img   for image_id, img in zip(image_ids, labelled_images)}
    # Generate image descriptors list to hand over to the labelling tool
    # Each descriptor provides the image ID, the URL and the size
    image_descriptors = []
    for image_id, img in zip(image_ids, labelled_images):
        height, width = img.image_size
        image_descriptors.append(image_descriptor(
            image_id=image_id, url='/image/{}'.format(image_id),
            width=width, height=height
        ))


    app = Flask(__name__, static_folder='static')
    if SocketIO is not None:
        print('Using web sockets')
        socketio = SocketIO(app)
    else:
        socketio = None


    def apply_dextr_js(image, dextr_points_js):
        pixels = image.read_pixels()
        dextr_points = np.array([[p['y'], p['x']] for p in dextr_points_js])
        if dextr_fn is not None:
            print(f'dextr call: {pixels.shape=}, points={dextr_points}')
            mask = dextr_fn(pixels, dextr_points)
            regions = PolygonLabel.mask_image_to_regions_cv(mask, sort_decreasing_area=True)
            regions_js = PolygonLabel.regions_to_json(regions)
            return regions_js
        else:
            return []




    if config is None:
        config = {
            'useClassSelectorPopup': True,
            'tools': {
                'imageSelector': True,
                'labelClassSelector': True,
                'labelClassFilterInitial': None,
                'drawPolyLabel': True,
                'compositeLabel': False,
                'deleteLabel': True,
                'deleteConfig': {
                    'typePermissions': {
                        'point': True,
                        'box': True,
                        'polygon': True,
                        'composite': True,
                        'group': True,
                    }
                }
            }
        }


    @app.route('/')
    def index():
        label_classes_json = [(cls.to_json() if isinstance(cls, LabelClassGroup) else cls)
                               for cls in label_classes]
        if anno_controls is not None:
            anno_controls_json = [c.to_json() for c in anno_controls]
        else:
            anno_controls_json = []
        return render_template('labeller_page.jinja2',
                               tasks=tasks,
                               colour_schemes=colour_schemes,
                               label_class_groups=label_classes_json,
                               image_descriptors=image_descriptors,
                               initial_image_index=0,
                               anno_controls=anno_controls_json,
                               labelling_tool_config=config,
                               dextr_available=dextr_fn is not None,
                               use_websockets=socketio is not None)


    if socketio is not None:
        @socketio.on('get_labels')
        def handle_get_labels(arg_js):
            image_id = arg_js['image_id']

            image = images_table[image_id]

            labels, completed_tasks = image.get_label_data_for_tool()

            label_header = dict(image_id=image_id,
                                labels=labels,
                                completed_tasks=completed_tasks,
                                timeElapsed=0.0,
                                state='editable',
                                session_id=str(uuid.uuid4()),
            )

            socketio_emit('get_labels_reply', label_header)


        @socketio.on('set_labels')
        def handle_set_labels(arg_js):
            label_header = arg_js['label_header']

            image_id = label_header['image_id']

            image = images_table[image_id]

            image.set_label_data_from_tool(label_header['labels'], label_header['completed_tasks'])

            socketio_emit('set_labels_reply', '')


        @socketio.on('dextr')
        def handle_dextr(dextr_js):
            if 'request' in dextr_js:
                dextr_request_js = dextr_js['request']
                image_id = dextr_request_js['image_id']
                dextr_id = dextr_request_js['dextr_id']
                dextr_points = dextr_request_js['dextr_points']

                image = images_table[image_id]

                regions_js = apply_dextr_js(image, dextr_points)

                dextr_labels = dict(image_id=image_id, dextr_id=dextr_id, regions=regions_js)
                dextr_reply = dict(labels=[dextr_labels])

                socketio_emit('dextr_reply', dextr_reply)
            elif 'poll' in dextr_js:
                dextr_reply = dict(labels=[])
                socketio_emit('dextr_reply', dextr_reply)
            else:
                dextr_reply = {'error': 'unknown_command'}
                socketio_emit('dextr_reply', dextr_reply)


    else:
        @app.route('/labelling/get_labels/<image_id>')
        def get_labels(image_id):
            image = images_table[image_id]
            labels, completed_tasks = image.get_label_data_for_tool()

            label_header = {
                'image_id': image_id,
                'labels': labels,
                'completed_tasks': completed_tasks,
                'timeElapsed': 0.0,
                'state': 'editable',
                'session_id': str(uuid.uuid4()),
            }

            r = make_response(json.dumps(label_header))
            r.mimetype = 'application/json'
            return r


        @app.route('/labelling/set_labels', methods=['POST'])
        def set_labels():
            label_header = json.loads(request.form['labels'])
            image_id = label_header['image_id']

            image = images_table[image_id]

            image.set_label_data_from_tool(label_header['labels'], label_header['completed_tasks'])

            return make_response('')


        @app.route('/labelling/dextr', methods=['POST'])
        def dextr():
            dextr_js = json.loads(request.form['dextr'])
            if 'request' in dextr_js:
                dextr_request_js = dextr_js['request']
                image_id = dextr_request_js['image_id']
                dextr_id = dextr_request_js['dextr_id']
                dextr_points = dextr_request_js['dextr_points']

                image = images_table[image_id]
                regions_js = apply_dextr_js(image, dextr_points)

                dextr_labels = dict(image_id=image_id, dextr_id=dextr_id, regions=regions_js)
                dextr_reply = dict(labels=[dextr_labels])

                return make_response(json.dumps(dextr_reply))
            elif 'poll' in dextr_js:
                dextr_reply = dict(labels=[])
                return make_response(json.dumps(dextr_reply))
            else:
                return make_response(json.dumps({'error': 'unknown_command'}))


    @app.route('/image/<image_id>')
    def get_image(image_id):
        image = images_table[image_id]
        data, mimetype = image.data_and_mime_type()
        r = make_response(data)
        r.mimetype = mimetype
        return r



    if socketio is not None:
        socketio.run(app, debug=debug, port=port, use_reloader=use_reloader)
    else:
        app.run(debug=debug, port=port, use_reloader=use_reloader)

    return app


@click.command()
@click.option('--images_pat', type=str, default='', help='Image path pattern e.g. \'images/*.jpg\'')
@click.option('--labels_dir', type=click.Path(dir_okay=True, file_okay=False, writable=True))
@click.option('--readonly', is_flag=True, default=False, help='Don\'t persist changes to disk')
@click.option('--update_label_object_ids', is_flag=True, default=False, help='Update object IDs in label JSON files')
@click.option('--enable_dextr', is_flag=True, default=False)
@click.option('--dextr_weights', type=click.Path())
def run_app(images_pat, labels_dir, readonly, update_label_object_ids,
            enable_dextr, dextr_weights):


    with open('fastlabel/templates/interface_settings_clouds.json') as f:
        cfg = json.load(f)

    if enable_dextr or dextr_weights is not None:
        from dextr.model import DextrModel
        import torch

        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        if dextr_weights is not None:
            dextr_weights = os.path.expanduser(dextr_weights)
            dextr_model = torch.load(dextr_weights, map_location=device)
        else:
            dextr_model = DextrModel.pascalvoc_resunet101().to(device)

        dextr_model.eval()

        dextr_fn = lambda image, points: dextr_model.predict([image], points[None, :, :])[0] >= 0.5
    else:
        dextr_fn = None

    colour_schemes = get_color_schemes(cfg)
    label_classes = get_labels(cfg)
    anno_controls = get_anno_controls(cfg)
    tasks = get_tasks(cfg)

    if images_pat.strip() == '':
        image_paths = glob.glob('images/*.jpg') + glob.glob('images/*.png')
    else:
        image_paths = glob.glob(images_pat)

    # Load in .JPG images from the 'images' directory.
    labelled_images = PersistentLabelledImage.for_files(
        image_paths, labels_dir=labels_dir, readonly=readonly)
    print('Loaded {0} images'.format(len(labelled_images)))

    if update_label_object_ids:
        n_updated = 0
        for limg in labelled_images:
            if os.path.exists(limg.labels_path):
                label_js = json.load(open(limg.labels_path, 'r'))
                prefix = str(uuid.uuid4())
                modified = ensure_json_object_ids_have_prefix(
                    label_js, id_prefix=prefix)
                if modified:
                    with open(limg.labels_path, 'w') as f_out:
                        json.dump(label_js, f_out, indent=3)
                    n_updated += 1
        print('Updated object IDs in {} files'.format(n_updated))



    config = {
        'tools': {
            'imageSelector': True,
            'labelClassSelector': True,
            'drawPointLabel': False,
            'drawBoxLabel': True,
            'drawOrientedEllipseLabel': True,
            'drawPolyLabel': True,
            'compositeLabel': False,
            'deleteLabel': True,
            'deleteConfig': {
                'typePermissions': {
                    'point': True,
                    'box': True,
                    'polygon': True,
                    'composite': True,
                    'group': True,
                }
            }
        },
        'settings': {
            'brushWheelRate': 0.025,  # Change rate for brush radius (mouse wheel)
            'brushKeyRate': 2.0,    # Change rate for brush radius (keyboard)
        }
    }

    app = flask_labeller(label_classes, labelled_images, tasks=tasks, colour_schemes=colour_schemes,
                   anno_controls=anno_controls, config=config, dextr_fn=dextr_fn)

    return app
if __name__ == '__main__':
    run_app()