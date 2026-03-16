import math
import copy
import psutil

from PySide2.QtGui import QColor

result_bg = "rgb(0, 255, 255)"
normal_bg = "rgb(255, 255, 255)"

measure_unit = "Imperial"


def get_label_width():
    return 165


def get_input_width():
    return 155


def get_result_width():
    return 0


def get_text(change, current_text):
    current_value = ""

    if "new" in change:
        if change['type'] == 'change' and change['name'] == 'value':
            current_value = change['new']
    else:
        current_value = current_text

    return current_value


def is_integer(v):
    return math.isclose(v, round(v))


def float_to_str(x):
    if is_integer(x):
        return str(int(x))
    else:
        return str(x)


# tailing zero can be removed by return as int
def pretty_float(x):
    if is_integer(x):
        return int(x)
    else:
        return x

# to convert a input list or txt to float list for float value
def covert_input_to_text(inputs):
    result = ""

    if isinstance(inputs, list):
        list_length = len(inputs)

        if list_length == 1:
            result = float_to_str(inputs[0])
        else:
            for i in range(list_length - 1):
                result += float_to_str(inputs[i]) + ", "
            result += float_to_str(inputs[i + 1])
    # elif not math.isclose(inputs, 0.0):
    else: 
        result = float_to_str(inputs)

    return result


def convert_control_text(control_text):
    if not control_text:  # Check if control_text is empty or evaluates to False
        return 0

    if "," in control_text:
        # result = [float(i) for i in list(control_text.split(","))]
        result = [int(i) if is_integer(float(i)) else float(i)
                  for i in list(control_text.split(","))]
        return result
    else:
        v = float(control_text)
        return int(v) if is_integer(v) else v

def get_value_from_UI(obj, attr, ui_obj):
    if ui_obj.getText():
        setattr(obj, attr, convert_control_text(ui_obj.getText()))
        ui_obj.setTextColor("black", normal_bg)
    elif hasattr(obj, attr):
        delattr(obj, attr)

# connection dropdown change
def on_dropdown_change(obj, attr, current_value, container):
    if len(current_value) > 0 and not container.is_update:
        conn_group_before = copy.deepcopy(container.conn_group)
        setattr(obj, attr, current_value)
        container.container.main.record_changes(conn_group_before, container.conn_group, container.part_name)

# member dropdown change
def on_member_dropdown_change(obj, attr, current_value, container, member_name):
    if len(current_value) > 0 and not container.is_update:
        member_after = container.container.main.cet_steel_core.members[member_name]
        member_before = copy.deepcopy(member_after)
        setattr(obj, attr, current_value)
        container.container.main.record_member_changes(member_name, member_before, member_after)

def on_input_change(obj, attr, ui_obj, container):
    if not ui_obj.isModified():
        return
    else:
        ui_obj.setModified(False)
        conn_group_before = copy.deepcopy(container.conn_group)
        get_value_from_UI(obj, attr, ui_obj)
        container.container.main.record_changes(conn_group_before, container.conn_group, container.part_name)

def set_UI_input(obj, attr, ui_obj):
    ui_obj.setTextColor("black", normal_bg)
    if hasattr(obj, attr):
        ui_obj.setText(covert_input_to_text(getattr(obj, attr)))        
    else:
        ui_obj.setText("")


def get_conn_obj(obj, which_connection):
    if obj.part_name == "Column Transverse Stiffener":
        found = False

        if hasattr(obj.conn_group.target_member_list[obj.member_name], "setting"):
            setting = obj.conn_group.target_member_list[obj.member_name].setting
            if 'connections' in setting:
                for each in setting["connections"]:
                    if each.type == "transverse stiffener":
                        conn = each
                        found = True
                        break
        if not found:
            # todo add default connection
            conn = None
    elif obj.part_name == "Gusset":
        if hasattr(obj.conn_group, "shared_connections"): 
            setting = obj.conn_group.shared_connections["setting"]
            conn = setting["connections"]["gusset_plate"]
        else:
            conn = None
    elif obj.part_name == "Gusset To Member Conn":
        if hasattr(obj.conn_group, "shared_connections"): 
            setting = obj.conn_group.shared_connections["setting"]
            conn = setting["connections"]["web"]
        else:
            conn = None
    else:
        setting = obj.conn_group.design_member_list[obj.member_name].setting
        if obj.part_name == "Web Conn" or obj.part_name == "Brace Web Conn" or obj.part_name == "Brace":
            if hasattr(setting, "web") and "connections" in setting.web:
                conn = setting.web["connections"][which_connection]   
            else:
                conn = None    
        elif obj.part_name == "Flange Conn":
            if hasattr(setting, "flange") and "connections" in setting.flange:
                conn = setting.flange["connections"][which_connection] 
            else:
                conn = None    
        elif obj.part_name == "Beam Flange Stiffener" or obj.part_name == "Flange Filler":
            if hasattr(setting, "flange") and "connections" in setting.flange:
                conn = setting.flange["connections"][which_connection]   
            else:
                conn = None      
        elif obj.part_name == "Shear Stabilizer Plate":
            if hasattr(setting, "web") and "connections" in setting.web:
                conn = setting.web["connections"]["secondary connection"]   
            else:
                conn = None    
        else:
            print("invalid connection location" + obj.part_name + "\n")
            conn = setting.web["connections"]["web"] 
    return conn


def set_result(obj, attr, UI_obj, value):
    if not hasattr(obj, attr):
        UI_obj.setText(covert_input_to_text(value))
        UI_obj.setTextColor("black", result_bg)
        
        if hasattr(obj, attr):
            delattr(obj, attr)

def findPath(name):
    for pid in psutil.pids():
        try:
            ps = psutil.Process(pid)
            process_name = ps.name()
        except psutil.NoSuchProcess:  # Catch the error caused by the process no longer existing
            pass  # Ignore it
        else:
            if process_name == name:
                return psutil.Process(pid).exe()


def round_decimal(dec, places=4):
    return int((dec * 10**places) + 0.5) / 10.**places


def val_impr_to_metr(value):
    if measure_unit == "Imperial":
        return round_decimal(value * 25.4)
    else:
        return value

def val_metr_to_impr(value):
    if measure_unit == "Imperial":
        return round_decimal(value / 25.4)
    else:
        return value

from base64 import b64encode, b64decode

def pad(data, block_size):
    padding_length = block_size - (len(data) % block_size)
    padding = bytes([padding_length]) * padding_length
    return data + padding

def unpad(padded_data, block_size):
    padding_length = padded_data[-1]
    return padded_data[:-padding_length]

def encrypt_string(key, plaintext):
    # Generate a random initialization vector
    iv = get_random_bytes(AES.block_size)

    # Create an AES cipher object with the provided key and AES.MODE_CBC mode
    cipher = AES.new(key, AES.MODE_CBC, iv)

    # Pad the plaintext to be a multiple of the block size
    padded_plaintext = pad(plaintext.encode(), AES.block_size)

    # Encrypt the padded plaintext
    ciphertext = cipher.encrypt(padded_plaintext)

    # Concatenate the IV and ciphertext, and base64 encode the result
    encrypted_data = iv + ciphertext
    encoded_data = b64encode(encrypted_data).decode('utf-8')

    return encoded_data

def decrypt_string(key, ciphertext):
    # Base64 decode the ciphertext
    decoded_data = b64decode(ciphertext.encode('utf-8'))

    # Extract the IV from the decoded data
    iv = decoded_data[:AES.block_size]

    # Create an AES cipher object with the provided key, AES.MODE_CBC mode, and the extracted IV
    cipher = AES.new(key, AES.MODE_CBC, iv)

    # Decrypt the ciphertext (excluding the IV)
    decrypted_data = cipher.decrypt(decoded_data[AES.block_size:])

    # Unpad the decrypted data
    plaintext = unpad(decrypted_data, AES.block_size).decode('utf-8')

    return plaintext

def set_drawing_size(draw_size):
    draw_size.addItem("11 x 8.5 (Letter Landscape)")
    draw_size.addItem("11.69 x 8.27 (A4 Landscape)")
    draw_size.addItem("16.5 x 11.7 (A3 Landscape)")
    draw_size.addItem("23.45 x 16.5 (A2 Landscape)")
    draw_size.addItem("33.1 x 23.4 (A1 Landscape)")
    draw_size.addItem("8.5 x 11 (Letter Portrait)")
    draw_size.addItem("8.27 x 11.69 (A4 Portrait)")
    draw_size.addItem("11.7 x 16.5 (A3 Portrait)")
    draw_size.addItem("16.5 x 23.45 (A2 Portrait)")
    draw_size.addItem("23.4 x 33.1 (A1 Portrait)")

    draw_size.setSelection("11.69 x 8.27 (A4 Landscape)")


def read_values(obj, data, item, type = "text", default=""):
    if item in data:
        if type == "text":
            obj.setText(data[item])
        elif type == "checkbox":
            obj.setChecked(data[item])
        else: # dropdown
            obj.setSelection(data[item])
    else:
        obj.setText(default)

def set_value(cet_steel_core_setting, data, item, obj, type, default=""):
    if item in data:
        content = data[item]
        if type == 'droplist':
            obj.setSelection(content)
        elif type == 'color':
            obj.setSelectedColor(QColor(content))
        elif type == 'checkbox':
            obj.setChecked(content)
        else:
            obj.setText(content)
        cet_steel_core_setting[item] = content
    else:
        cet_steel_core_setting[item] = default