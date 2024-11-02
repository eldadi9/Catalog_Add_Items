from flask import Flask, request, render_template_string, jsonify, send_file
import pandas as pd
import random
import os
import tempfile

app = Flask(__name__)

# Persistent storage simulation
colors = {}  # stores color description to color code mapping
item_types = {}  # stores item type description to item type code mapping
model_numbers = set()  # stores all model numbers (for suggesting the next model code)
catalog = []  # stores all catalog entries

@app.route('/')
def form():
    color_options = list(colors.keys())
    item_type_options = list(item_types.keys())
    size_options_1 = [str(i) for i in range(32, 47)]
    size_options_2 = ["XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL", "5XL"]
    next_model_number = max(model_numbers, default=0) + 1
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Catalog Entry</title>
            <style>
                input, select { text-transform: capitalize; }
                .sizes-container {
                    display: flex;
                    max-width: 400px;
                }
                .size-option {
                    margin-right: 10px;
                }
                .scroll-box {
                    max-height: 200px;
                    overflow-y: scroll;
                    border: 1px solid black;
                    padding: 5px;
                    margin-right: 10px;
                }
            </style>
        </head>
        <body>
            <h1>Catalog Data Entry</h1>
            <form id="catalogForm" method="post">
                <label for="model_code">Model Code:</label>
                <input type="text" id="model_code" name="model_code" placeholder="Suggested: {{ next_model_number }}"><br><br>
                
                <label for="model_description">Model Description:</label>
                <input type="text" id="model_description" name="model_description"><br><br>
                
                <label for="color_description">Color Description:</label>
                <select id="color_description" name="color_description">
                    <option value="">Select Color</option>
                    {% for color in color_options %}
                    <option value="{{ color }}">{{ color }}</option>
                    {% endfor %}
                </select>
                <input type="text" id="new_color" name="new_color" placeholder="Enter new color">
                <button type="button" onclick="addNewColor()">Change to New Color</button><br><br>
                
                <label for="item_type_description">Item Type Description:</label>
                <select id="item_type_description" name="item_type_description">
                    <option value="">Select Item Type</option>
                    {% for item_type in item_type_options %}
                    <option value="{{ item_type }}">{{ item_type }}</option>
                    {% endfor %}
                </select>
                <input type="text" id="new_item_type" name="new_item_type" placeholder="Enter new item type">
                <button type="button" onclick="addNewItemType()">Change to New Item Type</button><br><br>
                
                <label for="size">Size:</label>
                <div class="sizes-container">
                    <div class="scroll-box">
                        <h4>Range 1 (32-46)</h4>
                        {% for size in size_options_1 %}
                        <input type="checkbox" name="size" value="{{ size }}"> {{ size }}<br>
                        {% endfor %}
                    </div>
                    <div class="scroll-box">
                        <h4>Range 2 (XS-5XL)</h4>
                        {% for size in size_options_2 %}
                        <input type="checkbox" name="size" value="{{ size }}"> {{ size }}<br>
                        {% endfor %}
                    </div>
                </div><br>

                <label for="upc">UPC:</label>
                <input type="text" id="upc" name="upc" placeholder="Enter or copy UPC"><br><br>
                <button type="button" onclick="copyItemCode()">Copy Item Code</button><br><br>

                <button type="button" onclick="saveItem()">Save</button>
                <button type="button" onclick="addNewColorEntry()">Add New Color Entry</button>
                <button type="button" onclick="saveToExcel()">Save to Excel</button>
            </form>

            <script>
                function addNewColor() {
                    var newColor = document.getElementById('new_color').value;
                    if (newColor) {
                        fetch('/add_color', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ color: newColor })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                var colorSelect = document.getElementById('color_description');
                                var newOption = document.createElement('option');
                                newOption.value = newColor;
                                newOption.textContent = newColor;
                                colorSelect.appendChild(newOption);
                            } else {
                                alert('Color already exists or invalid.');
                            }
                        });
                    }
                }

                function addNewItemType() {
                    var newItemType = document.getElementById('new_item_type').value;
                    if (newItemType) {
                        fetch('/add_item_type', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ item_type: newItemType })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                var itemTypeSelect = document.getElementById('item_type_description');
                                var newOption = document.createElement('option');
                                newOption.value = newItemType;
                                newOption.textContent = newItemType;
                                itemTypeSelect.appendChild(newOption);
                            } else {
                                alert('Item type already exists or invalid.');
                            }
                        });
                    }
                }

                function saveItem() {
                    var form = document.getElementById('catalogForm');
                    var formData = new FormData(form);
                    fetch('/save', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Item saved successfully!');
                        } else {
                            alert('Failed to save item.');
                        }
                    });
                }

                function addNewColorEntry() {
                    var modelCode = document.getElementById('model_code').value;
                    var modelDescription = document.getElementById('model_description').value;
                    var itemType = document.getElementById('item_type_description').value;

                    if (modelCode && modelDescription && itemType) {
                        window.location.href = `/?model_code=${modelCode}&model_description=${modelDescription}&item_type=${itemType}`;
                    } else {
                        alert('Please fill in Model Code, Model Description, and Item Type before adding a new color entry.');
                    }
                }

                function saveToExcel() {
                    var filePath = prompt('Please enter the file path to save the Excel file:');
                    if (filePath) {
                        fetch(`/save_to_excel?file_path=${encodeURIComponent(filePath)}`)
                        .then(response => {
                            if (response.ok) {
                                alert('Excel file saved successfully!');
                            } else {
                                alert('Failed to save Excel file.');
                            }
                        });
                    }
                }

                function copyItemCode() {
                    var modelCode = document.getElementById('model_code').value;
                    var colorDescription = document.getElementById('color_description').value;
                    var sizeElements = document.querySelectorAll('input[name="size"]:checked');
                    if (modelCode && colorDescription && sizeElements.length > 0) {
                        var itemCode = modelCode + colorDescription + sizeElements[0].value;
                        document.getElementById('upc').value = itemCode;
                    } else {
                        alert('Please fill in Model Code, Color, and select at least one size to generate an item code.');
                    }
                }
            </script>
        </body>
        </html>
    ''', color_options=color_options, item_type_options=item_type_options, size_options_1=size_options_1, size_options_2=size_options_2, next_model_number=next_model_number)

@app.route('/add_color', methods=['POST'])
def add_color():
    color = request.json['color'].strip()
    if color and color not in colors:
        color_code = random.randint(100, 999)
        while color_code in colors.values():
            color_code = random.randint(100, 999)
        colors[color] = color_code
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/add_item_type', methods=['POST'])
def add_item_type():
    item_type = request.json['item_type'].strip()
    if item_type and item_type not in item_types:
        item_type_code = random.randint(1000, 9999)
        while item_type_code in item_types.values():
            item_type_code = random.randint(1000, 9999)
        item_types[item_type] = item_type_code
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/save', methods=['POST'])
def save():
    model_code = request.form['model_code']
    model_description = request.form['model_description']
    color_description = request.form.get('new_color', '').strip() or request.form.get('color_description', '').strip()
    item_type_description = request.form.get('new_item_type', '').strip() or request.form.get('item_type_description', '').strip()
    upc = request.form['upc']
    sizes = request.form.getlist('size')

    if not sizes:
        return jsonify({'success': False, 'message': 'No sizes selected'}), 400

    # Handle color
    color_code = colors.get(color_description)
    
    # Handle item type
    item_type_code = item_types.get(item_type_description)

    # Store model number if not already stored
    if model_code.isdigit():
        model_numbers.add(int(model_code))

    for size in sizes:
        item_code = f"{model_code}{color_code}{size}"
        catalog.append({
            'Item Code': item_code,
            'Model Code': model_code,
            'Model Description': model_description,
            'Color Code': color_code,
            'Color Description': color_description,
            'Item Type Code': item_type_code,
            'Item Type Description': item_type_description,
            'Size': size,
            'UPC': upc
        })
    return jsonify({'success': True})

@app.route('/save_to_excel')
def save_to_excel():
    if not catalog:
        return jsonify({'success': False, 'message': 'No items to save.'}), 400

    file_path = request.args.get('file_path')
    if not file_path:
        return jsonify({'success': False, 'message': 'No file path provided.'}), 400

    df = pd.DataFrame(catalog)
    
    try:
        df.to_excel(file_path, index=False)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
