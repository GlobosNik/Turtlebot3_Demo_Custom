import argparse
import math
import os
import xml.etree.ElementTree as ET

FREE = 254
OCCUPIED = 0


def _pose(model):
    values = [float(value) for value in model.findtext('pose', '0 0 0 0 0 0').split()]
    return values[0], values[1], values[5]


def _collision_shapes(root):
    shapes = []
    for model in root.findall('.//model'):
        model_x, model_y, model_yaw = _pose(model)
        for collision in model.findall('./link/collision'):
            geometry = collision.find('geometry')
            if geometry is None:
                continue
            collision_pose = collision.findtext('pose', '0 0 0 0 0 0').split()
            local_x, local_y = float(collision_pose[0]), float(collision_pose[1])
            local_yaw = float(collision_pose[5])
            x = model_x + math.cos(model_yaw) * local_x - math.sin(model_yaw) * local_y
            y = model_y + math.sin(model_yaw) * local_x + math.cos(model_yaw) * local_y
            yaw = model_yaw + local_yaw

            cylinder = geometry.find('cylinder')
            if cylinder is not None:
                shapes.append(('cylinder', x, y, yaw, float(cylinder.findtext('radius')),
                               float(cylinder.findtext('length'))))
                continue

            box = geometry.find('box')
            if box is not None:
                size = [float(value) for value in box.findtext('size').split()]
                shapes.append(('box', x, y, yaw, size[0], size[1]))
    return shapes


def _inside(shape, x, y):
    kind, shape_x, shape_y, yaw, first, second = shape
    dx = x - shape_x
    dy = y - shape_y
    local_x = math.cos(yaw) * dx + math.sin(yaw) * dy
    local_y = -math.sin(yaw) * dx + math.cos(yaw) * dy
    if kind == 'cylinder':
        return local_x * local_x + local_y * local_y <= first * first
    return abs(local_x) <= first / 2.0 and abs(local_y) <= second / 2.0


def generate_map(world_path, output_prefix, resolution, margin):
    root = ET.parse(world_path).getroot()
    shapes = _collision_shapes(root)
    if not shapes:
        raise ValueError('No supported collision geometry was found in the SDF')

    extents = []
    for shape in shapes:
        kind, x, y, yaw, first, second = shape
        if kind == 'cylinder':
            radius_x = radius_y = first
        else:
            radius_x = abs(math.cos(yaw)) * first / 2 + abs(math.sin(yaw)) * second / 2
            radius_y = abs(math.sin(yaw)) * first / 2 + abs(math.cos(yaw)) * second / 2
        extents.append((x - radius_x, x + radius_x, y - radius_y, y + radius_y))

    min_x = math.floor((min(item[0] for item in extents) - margin) / resolution) * resolution
    max_x = math.ceil((max(item[1] for item in extents) + margin) / resolution) * resolution
    min_y = math.floor((min(item[2] for item in extents) - margin) / resolution) * resolution
    max_y = math.ceil((max(item[3] for item in extents) + margin) / resolution) * resolution
    width = int(round((max_x - min_x) / resolution))
    height = int(round((max_y - min_y) / resolution))
    pixels = bytearray([FREE] * (width * height))

    for row in range(height):
        world_y = max_y - (row + 0.5) * resolution
        for column in range(width):
            world_x = min_x + (column + 0.5) * resolution
            if any(_inside(shape, world_x, world_y) for shape in shapes):
                pixels[row * width + column] = OCCUPIED

    image_path = output_prefix + '.pgm'
    yaml_path = output_prefix + '.yaml'
    os.makedirs(os.path.dirname(os.path.abspath(output_prefix)), exist_ok=True)
    with open(image_path, 'wb') as image:
        image.write(f'P5\n{width} {height}\n255\n'.encode('ascii'))
        image.write(pixels)
    with open(yaml_path, 'w', encoding='ascii') as map_yaml:
        map_yaml.write(
            f'image: {os.path.basename(image_path)}\n'
            f'resolution: {resolution}\n'
            f'origin: [{min_x:.6f}, {min_y:.6f}, 0.0]\n'
            'negate: 0\n'
            'occupied_thresh: 0.65\n'
            'free_thresh: 0.196\n'
        )
    return yaml_path, image_path, width, height


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('world', help='Path to the Gazebo SDF world')
    parser.add_argument('-o', '--output', default='tb3_ground_truth_map',
                        help='Output prefix for .pgm and .yaml')
    parser.add_argument('--resolution', type=float, default=0.05,
                        help='Map resolution in metres per cell')
    parser.add_argument('--margin', type=float, default=1.0,
                        help='Free-space margin around the outermost obstacle')
    args = parser.parse_args()
    if args.resolution <= 0 or args.margin < 0:
        parser.error('resolution must be positive and margin must not be negative')
    yaml_path, image_path, width, height = generate_map(
        args.world, args.output, args.resolution, args.margin)
    print(f'Generated {yaml_path} and {image_path} ({width}x{height} cells)')


if __name__ == '__main__':
    main()
