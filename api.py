from flask import Flask, request, jsonify
import io
import numpy as np
from rembg import remove
from PIL import Image
import requests
from webcolors import rgb_to_name, CSS3_HEX_TO_NAMES, hex_to_rgb
from scipy.spatial import KDTree
import os
app = Flask(__name__)

@app.route('/process_image', methods=['POST'])
def process_image():
    # Get image URL from the request
    image_url = request.json.get('image_url')

    # Fetch the image from the URL
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        input_img = Image.open(io.BytesIO(response.content))

        # Remove background from the image
        output_img = remove(input_img).convert("RGBA")

        # Convert the image to a numpy array
        img_array = np.array(output_img)

        # Find the non-zero rows and columns
        rows, cols = np.where(img_array[:, :, 3] != 0)
        top_row, bottom_row = rows.min(), rows.max()
        left_col, right_col = cols.min(), cols.max()

        # Crop the image
        cropped_img = output_img.crop((left_col, top_row, right_col, bottom_row))

        # Get colors of cropped image
        colors = cropped_img.getcolors(maxcolors=2**24)
        newcolors = list(colors)

        # Find the second most common color and remove it from the list of colors
        def colorextraction():
            first_most_common_color = max(newcolors, key=lambda x: x[0])
            for i in newcolors:
                if i == first_most_common_color:
                    newcolors.remove(i)
            fmc = first_most_common_color[1]
            cfmc = first_most_common_color[0]
            if fmc[0] != 0 and fmc[1] != 0 and fmc[2] != 0:
                return fmc, cfmc
            else:
                return colorextraction()

        rc = colorextraction()
        fmc = rc[0]
        cfmc = rc[1]

        # Find the second most common color and remove it from the list of colors
        second_most_common_color = max(newcolors, key=lambda x: x[0])
        for i in newcolors:
            if i == second_most_common_color:
                newcolors.remove(i)
        smc = second_most_common_color[1]
        csmc = second_most_common_color[0]

        # Return results as JSON
        result = {
            'second_most_common_color': smc,
            'second_most_common_count': csmc,
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/get_color_name', methods=['POST'])
def get_color_name():
    # Get RGB color from request
    data = request.get_json()
    rgb_tuple = tuple(data['rgb'])

    try:
        # first try to get the name of the color directly
        color_name = rgb_to_name(rgb_tuple, spec='css3')
    except ValueError:
        # if the color is not found, find the closest matching color
        css3_db = CSS3_HEX_TO_NAMES
        names = []
        rgb_values = []
        for color_hex, color_name in css3_db.items():
            
            names.append(color_name)
            rgb_values.append(hex_to_rgb(color_hex))
        kdt_db = KDTree(rgb_values)
        distance, index = kdt_db.query(rgb_tuple)
        color_name = names[index]

    # Return results as JSON
    result = {
        'color_name': color_name,
    }
    
    return jsonify(result)


if __name__ == '__main__':
     hostval='0.0.0.0'
     port1 = int(os.environ.get('PORT_APP1', 5000))
     app.run(host=hostval, port=port1)
