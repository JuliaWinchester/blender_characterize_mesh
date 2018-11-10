import bpy
import json

from os import path
from statistics import mean
from sys import argv

import io
from contextlib import redirect_stdout

def file_name(filepath):
	return path.split(filepath)[1]

def file_suffix(filepath):
	return path.splitext(file_name(filepath))[1]

def mesh_import_wrapper(func, filepath):
	func(filepath=filepath)

def mesh_import(filepath):
	import_func = {
		'.obj': bpy.ops.import_scene.obj,
		'.ply': bpy.ops.import_mesh.ply,
		'.stl': bpy.ops.import_mesh.stl, 
		'.wrl': bpy.ops.import_scene.x3d,
		'.x3d': bpy.ops.import_scene.x3d
		# todo: add gltf, test other mesh formats
	}

	stdout = io.StringIO()
	with redirect_stdout(stdout):
		mesh_import_wrapper(import_func[file_suffix(filepath)], filepath=filepath)
		stdout.seek(0) 
		return stdout.read()

def export_json(metadata):
	print("JSON OUTPUT:")
	print(json.dumps(metadata))

filepath = argv[-1]
 
metadata = {
	'filename': None,
	'filepath': None,
	'mimetype': None,
	'load_successful': None,
	'point_count': None, 
	'face_count': None,
	'edges_per_face': None, 
	'bounding_box_dimensions': {
		'bounding_box_x': None,
		'bounding_box_y': None,
		'bounding_box_z': None,
	},
	'centroid': {
		'centroid_x': None,
		'centroid_y': None,
		'centroid_z': None,
	},
	'has_uv_space': None, 
	'vertex_color': None
}

mime_type = {
	'.gltf': 'model/gltf+json',
	'.obj': 'text/prs.wavefront-obj',
	'.ply': 'application/ply',
	'.stl': 'application/stl',
	'.wrl': 'model/vrml',
	'.x3d': 'model/x3d+xml'
}

metadata['filename'] = path.split(filepath)[1]
metadata['filepath'] = filepath
metadata['mimetype'] = mime_type[file_suffix(filepath)]

try:
	bpy.ops.object.select_all(action='SELECT')
	bpy.ops.object.delete()
	output = mesh_import(filepath)
	if len(bpy.data.objects) == 1:
		metadata['load_successful'] = True
	else:
		metadata['load_successful'] = False # likely invalid file error, not an easy way to capture this from Blender
		metadata['load_error_message'] = output.replace("\n", "; ")
except Exception as e:
	metadata['load_successful'] = False # likely file not found error
	metadata['load_error_message'] = str(e).replace("\n", "; ")

if metadata['load_successful'] == True:
	mesh_object = bpy.data.objects[0]
	mesh = mesh_object.data

	metadata['point_count'] = len(mesh.vertices)
	metadata['face_count'] = len(mesh.polygons)

	# derive edges per face
	edges_list = [len(p.vertices) for p in mesh.polygons]
	edge_num_set = set(edges_list)
	if len(edge_num_set) != 1:
		metadata['load_successful'] = False
	else:
		metadata['edges_per_face'] = next(iter(edge_num_set))

	x_points = []
	y_points = []
	z_points = []

	for v in mesh.vertices:
		co = v.co
		x_points.append(co[0])
		y_points.append(co[1])
		z_points.append(co[2])

	# derive bounding box dimensions
	metadata['bounding_box_dimensions']['bounding_box_x'] = max(x_points) - min(x_points)
	metadata['bounding_box_dimensions']['bounding_box_y'] = max(y_points) - min(y_points)
	metadata['bounding_box_dimensions']['bounding_box_z'] = max(z_points) - min(z_points)

	# derive centroid info
	metadata['centroid']['centroid_x'] = mean(x_points)
	metadata['centroid']['centroid_y'] = mean(y_points)
	metadata['centroid']['centroid_z'] = mean(z_points)

	# UV
	if len(mesh.uv_textures) > 0:
		metadata['has_uv_space'] = True
	else:
		metadata['has_uv_space'] = False

	# Color
	if len(mesh.vertex_colors) > 0:
		metadata['vertex_color'] = True
	else:
		metadata['vertex_color'] = False

export_json(metadata)